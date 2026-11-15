"""Fixed training/development/calibration/evaluation executors; no capture startup."""

from collections import Counter
import json
import os
from pathlib import Path
import sys
import time
import subprocess
import numpy as np
import torch
from sklearn.ensemble import RandomForestClassifier
from threadpoolctl import threadpool_limits

from .browser_adaptation import UNCOMMITTED, check_roles, forest_weights
from .browser_calibration import write_policy_bundle
from .bundle import Predictor, export_bundle, sha256, write_json
from .contract import Flow, forest_features
from .data import read_split
from .ipv6_pilot import read_config as read_recipe, new_training, clean_assessment
from .size_robustness import local_rows, read_public
from .local_policy import stats
from .public_policy import select_policy
from .live_policy import timing_metrics
from .paired_study import SPOTIFY_REPAIR_SHA
from .spotify_repair import role_rows, stage_receipt, write_stage

OUTPUT = Path("experiments/spotify-data-repair-v1")


def stage_guard(event, args, command, root, cfg, recipe):
    if event in ("socket.connect", "socket.getaddrinfo"):
        raise ValueError("study stage is offline")
    if event != "open" or not isinstance(args[0], (str, bytes)):
        return
    p = Path(os.fsdecode(args[0])).resolve()
    allowed_splits = {
        "fit": ["train.jsonl"],
        "assess": ["selection.jsonl"],
        "calibrate": ["calibration.jsonl"],
        "evaluate": [],
    }[command]
    public = Path(recipe["public_data"]).resolve()
    if p.is_relative_to(Path("data").resolve()) and p not in [
        public / n for n in ["manifest.json"] + allowed_splits
    ]:
        raise ValueError("wrong public split for stage")
    if p.is_relative_to(Path("artifacts/local").resolve()):
        current = Path(root).resolve()
        role = {"fit": "train", "assess": "selection", "calibrate": "calibration", "evaluate": "evaluation"}[
            command
        ]
        slots = [s["id"] for s in cfg["trials"] if s["role"] == role]
        previous = {
            "fit": ["train"],
            "assess": ["train", "selection"],
            "calibrate": ["train", "selection", "calibration"],
            "evaluate": ["train", "selection", "calibration", "evaluation"],
        }[command]
        previous_ids = [s["id"] for s in cfg["trials"] if s["role"] in previous]
        stage_names = {
            "fit": ["training"],
            "assess": ["training", "development"],
            "calibrate": ["training", "development", "calibration"],
            "evaluate": ["training", "development", "calibration"],
        }[command]
        current_ok = p.parent == current and (
            p.name in [s + "-stage.json" for s in stage_names]
            or p.name == Path("configs/spotify-data-repair-v1.json").name
            or any(p.name.startswith(t + "-") for t in slots)
            or any(p.name == t + "-archive.json" for t in previous_ids)
        )
        old = Path(recipe["local_root"]).resolve()
        old_roles = (
            recipe["train_trials"] + recipe["selection_trials"]
            if command == "fit"
            else recipe["selection_trials"]
            if command == "assess"
            else []
        )
        old_ok = p.parent == old and any(
            p.name == t + s
            for t in old_roles
            for s in ["-development-rows.jsonl", "-collection-summary.json"]
        )
        fresh = Path(recipe["new_training_root"]).resolve()
        fresh_ok = (
            command == "fit"
            and p.parent == fresh
            and any(p.name.startswith(t + "-") for t in recipe["new_training_archives"])
        )
        if not (current_ok or old_ok or fresh_ok):
            raise ValueError("wrong private cohort/role for stage")
    if p.is_relative_to(Path("experiments").resolve()):
        allowed = [
            Path(recipe["reference_bundle"]).resolve(),
            Path(cfg["source_bundle"]).resolve(),
        ]
        stages = {
            "fit": ["training"],
            "assess": ["training", "development"],
            "calibrate": ["training", "development", "calibration"],
            "evaluate": ["training", "development", "calibration", "evaluation"],
        }[command]
        allowed.extend((OUTPUT / stage).resolve() for stage in stages)
        if not any(p.is_relative_to(a) for a in allowed):
            raise ValueError("unrelated experiment excluded")


def candidate_spec(bundle):
    model = Predictor(bundle)
    return {
        "bundle": str(bundle),
        "artifact_id": model.identity,
        "weight_sha256": sha256(Path(bundle) / "forest.json"),
    }


def emit_stage(root, cfg, stage, checks, candidate, folder):
    files = [p for p in folder.rglob("*") if p.is_file()]
    return write_stage(
        root, cfg, stage, "passed" if all(checks.values()) else "failed_stop", checks, candidate, files
    )


def fit(root, cfg, recipe):
    new, bindings = role_rows(root, cfg, "train")
    if sum(len(r["packets"]) >= 10 for r in new) < 9 or sum(len(r["packets"]) >= 30 for r in new) < 3:
        raise ValueError("training support below declaration")
    out = OUTPUT / "training"
    if out.exists():
        raise FileExistsError("preserve training execution; no replacement fits")
    old = Predictor(recipe["reference_bundle"])
    reference = Predictor(cfg["source_bundle"])
    if (
        reference.identity != cfg["source_artifact_id"]
        or sha256(Path(cfg["source_bundle"]) / "forest.json") != cfg["source_weight_sha256"]
    ):
        raise ValueError("control changed")
    if old.normalizer.metadata() != reference.normalizer.metadata() or old.labels != reference.labels:
        raise ValueError("saved preprocessing changed")
    original, old_bindings = local_rows(old, recipe)
    adopted, adopted_bindings = new_training(recipe)
    local = original["train"] + adopted
    check_roles(local + new, original["selection"])
    if {r["group_id"] for r in local} & {r["group_id"] for r in new}:
        raise ValueError("old/new training session overlaps")
    public, py, pids, manifest = read_public(recipe["public_data"], "train")
    if (
        len(public) != 14000
        or len(local) != 62
        or sha256(Path(recipe["public_data"]) / "manifest.json") != recipe["public_manifest_sha256"]
    ):
        raise ValueError("frozen training inventory differs")
    out.mkdir(parents=True)
    data = {
        "public_training_ids": pids,
        "old_local_training_ids": [r["id"] for r in local],
        "new_spotify_training_ids": [r["id"] for r in new],
        "new_archives": bindings,
        "old_exports": old_bindings,
        "adopted": adopted_bindings,
    }
    write_json(out / "data-manifest.json", data)
    models = {}
    for arm in cfg["training"]["arms"]:
        started = time.perf_counter()
        local_arm = local + (new if arm == "plus_spotify" else [])
        raw = public + [Flow(packets=r["packets"]).array() for r in local_arm]
        ly = np.asarray([reference.labels.index(r["label"]) for r in local_arm])
        features = np.asarray(
            [forest_features(x[:b], reference.normalizer, "summary-v1") for x in raw for b in cfg["budgets"]]
        )
        weights = forest_weights(len(public) * 4, np.repeat(ly, 4), cfg["training"]["local_training_mass"])
        model = RandomForestClassifier(**cfg["training"]["forest"], random_state=17, n_jobs=2)
        model.fit(features, np.repeat(np.concatenate([py, ly]), 4), sample_weight=weights)
        bundle = export_bundle(
            out / arm / "bundle",
            model,
            reference.normalizer,
            reference.labels,
            {
                "fixture": False,
                "experimental": True,
                "study_plan_sha256": SPOTIFY_REPAIR_SHA,
                "data_manifest_sha256": sha256(out / "data-manifest.json"),
                "arm": arm,
                "training_counts": dict(Counter(r["label"] for r in local_arm)),
                "source_sha256": sha256(__file__),
                "source_commit": subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
                "public_manifest_sha256": recipe["public_manifest_sha256"],
                "source_artifact_id": reference.identity,
                "license": "CESNET CC-BY-4.0 and private user-authorized local training",
            },
            {"feature_map": "summary-v1"},
            UNCOMMITTED,
        )
        if arm == "control" and sha256(bundle / "forest.json") != cfg["source_weight_sha256"]:
            raise ValueError("control failed exact reproduction; stop before candidate")
        checked = Predictor(bundle)
        probe = [x[:b] for x in raw[:4] + raw[-4:] for b in cfg["budgets"]]
        expected = model.predict_proba(
            np.asarray([forest_features(x, reference.normalizer, "summary-v1") for x in probe])
        )
        if not np.allclose(checked.probabilities(probe), expected, rtol=0, atol=1e-12):
            raise ValueError("portable export parity failed")
        models[arm] = {**candidate_spec(bundle), "seconds": time.perf_counter() - started}
        write_json(out / (arm + "-fit.json"), models[arm])
        print(json.dumps({"stage": "fit_complete", "arm": arm, **models[arm]}), flush=True)
    write_json(out / "models.json", models)
    return emit_stage(
        root,
        cfg,
        "training",
        {"control_reproduced": True, "candidate_export_verified": True},
        models["plus_spotify"],
        out,
    )


def retention_gates(candidate, control, cfg):
    rules = cfg["development_gates"]
    eps = 1e-12
    sp = candidate["spotify"]["budgets"]
    old = control["spotify"]["budgets"]
    return {
        "spotify_each_prefix": all(
            sp[b]["classes"]["spotify"]["recall"] + eps >= rules["spotify_min_raw_recall_each_10_20_30"]
            for b in ["10", "20", "30"]
        ),
        "spotify_primary_gain": sp["10"]["accuracy"] * sp["10"]["n"] + eps
        >= old["10"]["accuracy"] * old["10"]["n"] + rules["spotify_min_primary_correct_gain"],
        "local_f1_retention": candidate["local"]["macro_f1"] + eps >= control["local"]["macro_f1"],
        "local_each_class_prefix": all(
            candidate["local"]["budgets"][b]["classes"][label]["recall"] + eps
            >= control["local"]["budgets"][b]["classes"][label]["recall"]
            for b in sp
            for label in ["youtube", "instagram"]
        ),
        "public_each_prefix_f1": all(
            candidate["public"]["budgets"][b]["macro_f1"] + eps
            >= control["public"]["budgets"][b]["macro_f1"] - rules["public_max_macro_f1_loss_each_prefix"]
            for b in sp
        ),
        "public_each_class_prefix": all(
            candidate["public"]["budgets"][b]["classes"][label]["recall"] + eps
            >= control["public"]["budgets"][b]["classes"][label]["recall"]
            - rules["public_max_class_recall_loss_each_prefix"]
            for b in sp
            for label in control["public"]["budgets"][b]["classes"]
        ),
    }


def assess(root, cfg, recipe):
    training = stage_receipt(root, cfg, "training")
    new, bindings = role_rows(root, cfg, "selection")
    out = OUTPUT / "development"
    if out.exists():
        raise FileExistsError("preserve development result")
    models = json.loads((OUTPUT / "training/models.json").read_text())
    old = Predictor(recipe["reference_bundle"])
    original, _ = local_rows_selection(old, recipe)
    public, py, pids, _ = read_public(recipe["public_data"], "selection", 50)
    domains = {"spotify": (new, "local"), "local": (original, "local")}
    reports = {}
    out.mkdir(parents=True)
    for arm, spec in models.items():
        model = Predictor(spec["bundle"])
        result = {}
        predictions = []
        for domain, (rows, mode) in domains.items():
            raw = [Flow(packets=r["packets"]).array() for r in rows]
            y = np.asarray([model.labels.index(r["label"]) for r in rows])
            result[domain], cases = clean_assessment(model, raw, y, [r["id"] for r in rows], mode, recipe)
            predictions.extend({**r, "domain": domain} for r in cases)
        result["public"], cases = clean_assessment(model, public, py, pids, "public", recipe)
        predictions.extend(cases)
        reports[arm] = result
        write_json(out / (arm + "-metrics.json"), result)
        write_json(out / (arm + "-predictions.json"), predictions)
    checks = retention_gates(reports["plus_spotify"], reports["control"], cfg)
    write_json(
        out / "decision.json",
        {
            "gates": checks,
            "plan_sha256": SPOTIFY_REPAIR_SHA,
            "selection_archives": bindings,
            "limits": "reused retention and one prospective Spotify development visit; no final evaluation",
        },
    )
    return emit_stage(root, cfg, "development", checks, training["candidate"], out)


def local_rows_selection(reference, recipe):
    result = []
    bindings = {}
    for trial in recipe["selection_trials"]:
        proof = reference.meta["provenance"]["browser_evidence"][trial]
        path = Path(recipe["local_root"]) / (trial + "-development-rows.jsonl")
        if sha256(path) != proof["rows_sha256"]:
            raise ValueError("old selection changed")
        result.extend(
            r
            for r in [json.loads(line) for line in path.read_text().splitlines()]
            if r["label"] in ["youtube", "instagram"]
        )
        bindings[str(path)] = sha256(path)
    return result, bindings


def probability_cases(model, rows, budgets, domain):
    result = []
    inputs = []
    for row in rows:
        raw = row.get("array")
        if raw is None:
            raw = Flow(packets=row["packets"]).array()
        for b in budgets:
            if len(raw) >= b:
                result.append({"id": row["id"], "reference": row["label"], "budget": b, "domain": domain})
                inputs.append(raw[:b])
    values = np.concatenate([model.probabilities(inputs[i : i + 128]) for i in range(0, len(inputs), 128)])
    for case, p in zip(result, values):
        case.update(probabilities=p.tolist(), top1=model.labels[int(p.argmax())])
    return result


def local_policy_checks(points, threshold, cfg):
    early = [r for r in points if r["budget"] == 10]
    primary = stats(early, threshold)
    pooled = stats(points, threshold)
    rules = cfg["calibration"]
    return (
        primary["accepted"] >= rules["spotify_min_primary_accepted"]
        and primary["coverage"] >= rules["spotify_min_primary_coverage"]
        and primary["error"] == 0
        and pooled["accepted"] >= 2
        and pooled["error"] == 0
    )


def calibrate(root, cfg, recipe):
    dev = stage_receipt(root, cfg, "development")
    rows, bindings = role_rows(root, cfg, "calibration")
    out = OUTPUT / "calibration"
    if out.exists():
        raise FileExistsError("preserve one calibration fit")
    model = Predictor(dev["candidate"]["bundle"])
    raw, y, ids, manifest = read_split(recipe["public_data"], "calibration")
    counts = Counter()
    selected = []
    for x, target, ident in zip(raw, y, ids):
        label = model.labels[int(target)]
        if len(x) >= 10 and counts[label] < 50:
            selected.append({"id": ident, "label": label, "array": x})
            counts[label] += 1
    if any(counts[label] != 50 for label in model.labels):
        raise ValueError("public calibration lacks frozen support")
    public = probability_cases(model, selected, [10, 20, 30], "public")
    local = probability_cases(model, rows, [10, 20, 30], "spotify")
    policy_cfg = {
        "budgets": [10, 20, 30],
        "primary_budget": 10,
        "min_packets": 10,
        "temperature": 1,
        "rules": {
            "maximum_empirical_error": 0.1,
            "minimum_coverage": 0.5,
            "minimum_primary_accepted_per_class": 5,
        },
    }
    _, _, curve = select_policy(public, model.labels, policy_cfg)
    for point in curve:
        point["spotify_eligible"] = local_policy_checks(local, point["threshold"], cfg)
    chosen = next((p for p in curve if p["eligible"] and p["spotify_eligible"]), None)
    out.mkdir(parents=True)
    write_json(out / "predictions.json", public + local)
    write_json(out / "curve.json", curve)
    policy = {
        "version": "spotify-data-repair-refusal-v1",
        "fitted": chosen is not None,
        "threshold": chosen["threshold"] if chosen else 1,
        "min_packets": 10,
        "temperature": 1,
        "tie_break": "label_order",
        "validation_scope": "public_and_local_spotify_calibration",
        "locally_checked_labels": ["spotify"] if chosen else [],
        "note": "Empirical fitting checks on historical public and one local Spotify calibration session; scores are not correctness probabilities or unknown-service detection.",
    }
    proof = {
        "study_plan_sha256": SPOTIFY_REPAIR_SHA,
        "calibration_archives": bindings,
        "curve_sha256": sha256(out / "curve.json"),
        "predictions_sha256": sha256(out / "predictions.json"),
        "policy": policy,
        "selected": chosen,
    }
    write_json(out / "decision.json", proof)
    candidate = dev["candidate"]
    if chosen:
        bundle = write_policy_bundle(candidate["bundle"], out / "bundle", policy, proof)
        candidate = candidate_spec(bundle)
        if candidate["weight_sha256"] != dev["candidate"]["weight_sha256"]:
            raise ValueError("calibration changed weights")
    return emit_stage(
        root, cfg, "calibration", {"public_and_spotify_policy_feasible": chosen is not None}, candidate, out
    )


def evaluate(root, cfg, recipe):
    policy = stage_receipt(root, cfg, "calibration")
    rows, bindings = role_rows(root, cfg, "evaluation")
    out = OUTPUT / "evaluation"
    if out.exists():
        raise FileExistsError("preserve final evaluation")
    spec = next(s for s in cfg["trials"] if s["role"] == "evaluation")
    prefix = Path(root) / spec["id"]
    cap = json.loads(Path(str(prefix) + "-capture.json").read_text())
    timing = json.loads(Path(str(prefix) + "-timing.json").read_text())
    audit = json.loads(Path(str(prefix) + "-audit.json").read_text())
    if cap["artifact_id"] != policy["candidate"]["artifact_id"]:
        raise ValueError("final live model differs from frozen policy")
    originals = {r["flow_id"]: r for r in cap["flows"]}
    records = []
    for row in rows:
        original = originals[row["id"].split(":")[-1]]
        for b in cfg["budgets"]:
            if len(row["packets"]) >= b:
                native = next((p for p in original["predictions"] if p["observed_packets"] == b), None)
                records.append(
                    {"id": row["id"], "budget": b, "reference": "spotify", "live_prediction": native}
                )
    from .live_policy import live_stats

    metrics = {str(b): live_stats([r for r in records if r["budget"] == b]) for b in cfg["budgets"]}
    early = metrics["10"]
    t = timing_metrics(timing, cap, audit)
    rules = cfg["evaluation"]
    checks = {
        "minimum_accepted": early["accepted"] >= rules["min_accepted_spotify"],
        "coverage": early["end_to_end_coverage"] >= rules["min_end_to_end_coverage"],
        "accepted_error": early["accepted_error"] is not None
        and early["accepted_error"] <= rules["max_accepted_error"],
        "raw_recall_end_to_end": early["raw_correct_among_emitted"] / early["eligible_flow_checkpoints"]
        >= rules["min_raw_recall"],
        "native_operational": t["operational_screen_pass"],
    }
    out.mkdir(parents=True)
    write_json(out / "predictions.json", records)
    report = {
        "status": "small_spotify_live_screen_pass" if all(checks.values()) else "final_failed_stop",
        "gates": checks,
        "metrics": metrics,
        "timing": t,
        "plan_sha256": SPOTIFY_REPAIR_SHA,
        "artifact_id": cap["artifact_id"],
        "archives": bindings,
        "policy_stage_sha256": sha256(Path(root) / "calibration-stage.json"),
        "default_promoted": False,
        "limits": "Single final Spotify visit, not population accuracy, fresh YT/IG validation or broad release. Missing live checkpoints not filled by replay.",
    }
    write_json(out / "report.json", report)
    return report


def execute(command, root, cfg):
    recipe = read_recipe(cfg["training_recipe"])
    sys.addaudithook(lambda e, a: stage_guard(e, a, command, root, cfg, recipe))
    if sha256(Path(recipe["public_data"]) / "manifest.json") != recipe["public_manifest_sha256"]:
        raise ValueError("frozen public manifest changed")
    torch.set_num_threads(2)
    with threadpool_limits(limits=2):
        return {"fit": fit, "assess": assess, "calibrate": calibrate, "evaluate": evaluate}[command](
            root, cfg, recipe
        )
