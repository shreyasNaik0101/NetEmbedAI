"""One fixed matched forest timing-repair pilot; no capture or activation."""

from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import subprocess
import time

import numpy as np
from sklearn.ensemble import RandomForestClassifier

from .browser_adaptation import UNCOMMITTED, check_roles, forest_weights
from .bundle import Predictor, export_bundle, sha256, write_json
from .contract import Flow, forest_features
from .ipv6_pilot import clean_assessment, new_training, read_config as read_recipe
from .size_robustness import local_rows, read_public

CONFIG_SHA = "8cb134a30cd7fa6f0f664a059113495c7c308dbd070bd704f3a71ef6f3a5931b"


def read_config(path):
    raw = Path(path).read_bytes().replace(b"\r\n", b"\n")
    if hashlib.sha256(raw).hexdigest() != CONFIG_SHA:
        raise ValueError("fixed timing repair declaration changed")
    return json.loads(raw)


def guard(event, args, cfg, recipe, output, phase):
    if event in ("socket.connect", "socket.getaddrinfo"):
        raise ValueError("timing repair is offline")
    if event != "open" or not isinstance(args[0], (str, bytes)):
        return
    path = Path(os.fsdecode(args[0])).resolve()
    public = Path(recipe["public_data"]).resolve()
    if path.is_relative_to(Path("data").resolve()):
        if path not in [public / n for n in ("manifest.json", "train.jsonl", "selection.jsonl")]:
            raise ValueError("only public train and selection allowed")
    if path.is_relative_to(Path("artifacts/local").resolve()):
        old = Path(recipe["local_root"]).resolve()
        fresh = Path(recipe["new_training_root"]).resolve()
        diagnostic = Path(cfg["spotify_root"]).resolve()
        old_ok = path.parent == old and any(
            path.name == trial + suffix
            for trial in recipe["train_trials"] + recipe["selection_trials"]
            for suffix in ("-development-rows.jsonl", "-collection-summary.json")
        )
        new_ok = path.parent == fresh and any(
            path.name.startswith(trial + "-") for trial in recipe["new_training_archives"]
        )
        if not (old_ok or new_ok or (phase == "assessment" and path.is_relative_to(diagnostic))):
            raise ValueError("unassigned cohort or Spotify during fitting forbidden")
    if path.is_relative_to(Path("experiments").resolve()):
        allowed = [
            Path(output).resolve(),
            Path(cfg["control_bundle"]).resolve(),
            Path(recipe["reference_bundle"]).resolve(),
        ]
        if not any(path.is_relative_to(root) for root in allowed):
            raise ValueError("unrelated experiment outcomes forbidden")


def gates(candidate, control, cfg):
    rules = cfg["gates"]
    eps = 1e-12
    spotify = candidate["spotify"]["budgets"]
    checks = {
        "spotify_each_prefix_floor": all(
            spotify[b]["classes"]["spotify"]["recall"] * spotify[b]["n"] + eps >= count
            for b, count in rules["spotify_min_correct"].items()
        ),
        "spotify_primary_gain": spotify["10"]["classes"]["spotify"]["recall"] * spotify["10"]["n"] + eps
        >= control["spotify"]["budgets"]["10"]["classes"]["spotify"]["recall"]
        * control["spotify"]["budgets"]["10"]["n"]
        + rules["spotify_min_primary_gain"],
        "local_macro_f1_retention": candidate["local"]["macro_f1"] + eps >= control["local"]["macro_f1"],
        "local_each_class_prefix_retention": all(
            candidate["local"]["budgets"][b]["classes"][label]["recall"] + eps
            >= control["local"]["budgets"][b]["classes"][label]["recall"]
            for b in candidate["local"]["budgets"]
            for label in ("youtube", "instagram")
        ),
        "public_each_prefix_f1_retention": all(
            candidate["public"]["budgets"][b]["macro_f1"] + eps
            >= control["public"]["budgets"][b]["macro_f1"] - rules["public_max_macro_f1_loss_each_budget"]
            for b in candidate["public"]["budgets"]
        ),
        "public_each_class_prefix_retention": all(
            candidate["public"]["budgets"][b]["classes"][label]["recall"] + eps
            >= control["public"]["budgets"][b]["classes"][label]["recall"]
            - rules["public_max_class_recall_loss_each_budget"]
            for b in candidate["public"]["budgets"]
            for label in control["public"]["budgets"][b]["classes"]
        ),
    }
    return checks


def run(config_path, output):
    cfg = read_config(config_path)
    recipe = read_recipe(cfg["training_recipe"])
    recipe_bytes = Path(cfg["training_recipe"]).read_bytes().replace(b"\r\n", b"\n")
    if hashlib.sha256(recipe_bytes).hexdigest() != cfg["training_recipe_sha256"]:
        raise ValueError("original training recipe changed")
    out = Path(output)
    if out.exists():
        raise FileExistsError("preserve fixed experiment output")
    phase = ["fitting"]
    import sys

    sys.addaudithook(lambda e, a: guard(e, a, cfg, recipe, out, phase[0]))
    reference = Predictor(cfg["control_bundle"])
    old = Predictor(recipe["reference_bundle"])
    if (
        reference.identity != cfg["control_id"]
        or sha256(Path(cfg["control_bundle"]) / "forest.json") != cfg["control_weights_sha256"]
    ):
        raise ValueError("current control artifact changed")
    if reference.normalizer.metadata() != old.normalizer.metadata() or reference.labels != old.labels:
        raise ValueError("normalizer/labels differ")
    if sha256(Path(recipe["public_data"]) / "manifest.json") != recipe["public_manifest_sha256"]:
        raise ValueError("public manifest changed")
    rows, old_bindings = local_rows(old, recipe)
    new, new_bindings = new_training(recipe)
    local_training = rows["train"] + new
    check_roles(local_training, rows["selection"])
    public, py, pids, manifest = read_public(recipe["public_data"], "train")
    validation, vy, vids, _ = read_public(
        recipe["public_data"], "selection", cfg["public_selection_per_class"]
    )
    if (
        len(public) != 14000
        or len(local_training) != 62
        or len(rows["selection"]) != 17
        or manifest["labels"] != reference.labels
    ):
        raise ValueError("fixed data counts or labels differ")
    flows = public + [Flow(packets=r["packets"]).array() for r in local_training]
    ids = pids + [r["id"] for r in local_training]
    if len(set(ids)) != len(ids):
        raise ValueError("duplicate training IDs")
    targets = np.array([reference.labels.index(r["label"]) for r in local_training])
    weights = forest_weights(len(public) * 4, np.repeat(targets, 4), recipe["local_training_mass"])
    y = np.repeat(np.concatenate([py, targets]), 4)
    out.mkdir(parents=True, exist_ok=False)
    write_json(
        out / "data-manifest.json",
        {
            "public_manifest_sha256": recipe["public_manifest_sha256"],
            "public_training_ids": pids,
            "public_selection_ids": vids,
            "local_training_ids": [r["id"] for r in local_training],
            "local_selection_ids": [r["id"] for r in rows["selection"]],
            "original_exports": old_bindings,
            "new_training_exports": new_bindings,
            "local_training_counts": dict(Counter(r["label"] for r in local_training)),
            "limits": cfg["scope"],
        },
    )
    provenance = {
        "fixture": False,
        "experimental": True,
        "config": cfg,
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "source_commit": subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
        "source_sha256": sha256(__file__),
        "contract_sha256": sha256(Path(__file__).parent / "contract.py"),
        "data_manifest_sha256": sha256(out / "data-manifest.json"),
        "license": "CESNET CC-BY-4.0 and private local training",
        "limits": cfg["scope"],
    }
    write_json(out / "config.json", provenance)
    artifacts = {}
    # Both fits finish before Spotify inputs are opened. Each arm uses identical weights/rows.
    for arm, feature_map in cfg["arms"].items():
        started = time.perf_counter()
        print(json.dumps({"stage": "fitting", "arm": arm, "feature_map": feature_map}), flush=True)
        features = np.asarray(
            [
                forest_features(raw[:b], reference.normalizer, feature_map)
                for raw in flows
                for b in cfg["budgets"]
            ]
        )
        model = RandomForestClassifier(**cfg["forest"], random_state=cfg["seed"], n_jobs=cfg["threads"])
        model.fit(features, y, sample_weight=weights)
        bundle = export_bundle(
            out / arm / "bundle",
            model,
            reference.normalizer,
            reference.labels,
            {**provenance, "arm": arm},
            {"feature_map": feature_map},
            UNCOMMITTED,
        )
        weight_sha = sha256(bundle / "forest.json")
        if arm == "control" and weight_sha != cfg["control_weights_sha256"]:
            raise ValueError("control does not reproduce current weights; stop before treatment")
        predictor = Predictor(bundle)
        probe = [raw[:b] for raw in flows[:4] for b in cfg["budgets"]]
        difference = float(
            np.max(np.abs(model.predict_proba(features[:16]) - predictor.probabilities(probe)))
        )
        if difference > 1e-12:
            raise ValueError("portable train/inference preprocessing parity failed")
        artifacts[arm] = {
            "bundle": str(bundle),
            "artifact_id": predictor.identity,
            "weight_sha256": weight_sha,
            "export_maximum_difference": difference,
            "fit_and_export_seconds": time.perf_counter() - started,
        }
        del features, model, predictor
        print(json.dumps({"stage": "fit_verified", "arm": arm, **artifacts[arm]}), flush=True)
    phase[0] = "assessment"
    diag_root = Path(cfg["spotify_root"])
    if sha256(diag_root / "spotify-01-report.json") != cfg["spotify_report_sha256"]:
        raise ValueError("Spotify diagnostic changed")
    diagnostic = json.loads((diag_root / "spotify-01-report.json").read_text())
    for name, digest in diagnostic["files"].items():
        if sha256(diag_root / name) != digest:
            raise ValueError("Spotify evidence binding changed")
    points = json.loads((diag_root / "spotify-01-predictions.json").read_text())
    spotify_ids = {r["flow_id"] for r in points if r["reference"] == "spotify"}
    capture = json.loads((diag_root / "spotify-01-capture.json").read_text())
    spotify = [f for f in capture["flows"] if f["flow_id"] in spotify_ids]
    if len(spotify) != 5:
        raise ValueError("Spotify inventory differs")
    if any(r["id"].split(":")[-1] in spotify_ids for r in local_training + rows["selection"]):
        raise ValueError("Spotify evidence entered training or retention cohort")
    domains = {
        "local": (
            [Flow(packets=r["packets"]).array() for r in rows["selection"]],
            np.array([reference.labels.index(r["label"]) for r in rows["selection"]]),
            [r["id"] for r in rows["selection"]],
            "local",
        ),
        "public": (validation, vy, vids, "public"),
        "spotify": (
            [Flow(packets=r["packets"]).array() for r in spotify],
            np.full(5, reference.labels.index("spotify")),
            [r["flow_id"] for r in spotify],
            "local",
        ),
    }
    reports = {}
    for arm in cfg["arms"]:
        predictor = Predictor(artifacts[arm]["bundle"])
        report, predictions = {}, []
        for domain, (inputs, truth, names, mode) in domains.items():
            report[domain], cases = clean_assessment(predictor, inputs, truth, names, mode, recipe)
            predictions.extend({**r, "domain": domain} for r in cases)
        report.update(artifacts[arm])
        write_json(out / arm / "development.json", report)
        write_json(out / arm / "predictions.json", predictions)
        reports[arm] = report
    checks = gates(reports["nearest_ms"], reports["control"], cfg)
    decision = {
        "status": "development_candidate_only" if all(checks.values()) else "stop_repair_rejected",
        "config_sha256": CONFIG_SHA,
        "gates": checks,
        "artifacts": artifacts,
        "development_sha256": {a: sha256(out / a / "development.json") for a in reports},
        "prediction_sha256": {a: sha256(out / a / "predictions.json") for a in reports},
        "data_manifest_sha256": sha256(out / "data-manifest.json"),
        "diagnostic_report_sha256": cfg["spotify_report_sha256"],
        "source_quality_drops": capture["counters"]["drops"],
        "policy_fitted": False,
        "default_promoted": False,
        "spotify_diagnostic_never_used_for_fitting": True,
        "limits": cfg["scope"],
    }
    write_json(out / "decision.json", decision)
    return decision
