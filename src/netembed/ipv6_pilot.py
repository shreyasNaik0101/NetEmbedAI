"""One matched real-data pilot; no capture, calibration, final test or deployment."""

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
from .browser_sessions import verify_fresh
from .bundle import Predictor, export_bundle, sha256, write_json
from .contract import Flow, forest_features
from .paired_study import read_archive, read_plan, validate_archive_plan
from .size_robustness import case_metrics, guard as previous_guard, local_rows, read_public

CONFIG_SHA = "0de33a8b63290f34c1055f273a32a9a31443c47dc335dc49d7cc5a9e2fc1f6f2"


def guard(event, args):
    previous_guard(event, args)
    if event == "open" and isinstance(args[0], (str, bytes)):
        path = Path(os.fsdecode(args[0])).resolve().as_posix().lower()
        if any(
            s in path
            for s in (
                "/family-development-v1/",
                "/hotspot-family-feasibility-v1/",
                "fresh-ig-02",
                "fresh-yt-03",
                "fresh-ig-03",
            )
        ):
            raise ValueError("failed or remaining acquisition inputs excluded from pilot")


def read_config(path):
    raw = Path(path).read_bytes().replace(b"\r\n", b"\n")
    if hashlib.sha256(raw).hexdigest() != CONFIG_SHA:
        raise ValueError("fixed real-data pilot declaration changed")
    return json.loads(raw)


def validate_new_rows(rows, families, session):
    indexed = {r["id"]: r for r in families}
    if (
        len(indexed) != len(families)
        or len({r["id"] for r in rows}) != len(rows)
        or set(indexed) != {r["id"] for r in rows}
    ):
        raise ValueError("new row/family inventory duplicated or different")
    for row in rows:
        family = indexed[row["id"]]
        if (
            row["id"].split(":")[1] != session
            or family["label"] != row["label"]
            or family["packets"] != len(row["packets"])
            or family["family"] != 6
        ):
            raise ValueError("new training family/label/length/session mismatch")
        Flow(packets=row["packets"])


def new_training(cfg):
    root = Path(cfg["new_training_root"])
    collection = read_plan(cfg["new_collection_plan"])
    result, bindings, sessions = [], {}, set()
    for trial, digest in cfg["new_training_archives"].items():
        if sha256(root / (trial + "-archive.json")) != digest:
            raise ValueError("adopted acquisition receipt changed")
        archive = read_archive(root, trial)
        validate_archive_plan(root, trial, archive, collection)
        if (
            archive["status"] != "usable"
            or archive["collection_role"] != "train"
            or archive["session_id"] in sessions
        ):
            raise ValueError("requires distinct usable training acquisitions")
        sessions.add(archive["session_id"])
        intent = json.loads((root / (trial + "-intent.json")).read_text())
        proof = json.loads((root / (trial + "-browser-processes.json")).read_text())
        verify_fresh(proof["processes"], intent, archive["first_packet_ms"])
        rows = json.loads((root / (trial + "-rows.json")).read_text())
        families = json.loads((root / (trial + "-families.json")).read_text())
        validate_new_rows(rows, families, archive["session_id"])
        result.extend(
            {**r, "group_id": archive["session_id"], "acquisition_trial": trial}
            for r in rows
            if r["label"] in cfg["local_labels"]
        )
        bindings[trial] = {
            "archive_sha256": digest,
            "rows_sha256": sha256(root / (trial + "-rows.json")),
            "families_sha256": sha256(root / (trial + "-families.json")),
            "session_id": archive["session_id"],
        }
    if dict(Counter(r["label"] for r in result)) != cfg["expected_new_counts"]:
        raise ValueError("declared new training count differs")
    return result, bindings


def selection_families(cfg, rows):
    root = Path(cfg["family_audit_root"])
    if sha256(root / "report.json") != cfg["family_audit_sha256"]:
        raise ValueError("family audit changed")
    report = json.loads((root / "report.json").read_text())
    families, bindings = {}, {}
    for trial in cfg["selection_trials"]:
        path = root / (trial + ".json")
        if sha256(path) != report["trial_report_sha256"][trial]:
            raise ValueError("selection family evidence changed")
        part = json.loads(path.read_text())
        if part["role"] != "selection":
            raise ValueError("selection family role mismatch")
        for row in part["flows"]:
            if row["id"] in families:
                raise ValueError("duplicate selection family ID")
            family = int(row["family"])
            if family not in (4, 6):
                raise ValueError("selection family must be verified IPv4/IPv6")
            families[row["id"]] = family
        bindings[trial] = sha256(path)
    if set(families) != {r["id"] for r in rows}:
        raise ValueError("family metadata differs from selection inventory")
    return families, bindings


def clean_assessment(model, flows, y, ids, domain, cfg, families=None):
    budgets, records = {}, []
    for budget in cfg["budgets"]:
        indices = [i for i, raw in enumerate(flows) if domain == "public" or len(raw) >= budget]
        inputs = [flows[i][:budget] for i in indices]
        p = np.concatenate([model.probabilities(inputs[i : i + 128]) for i in range(0, len(inputs), 128)])
        macro = range(len(model.labels)) if domain == "public" else sorted(set(y.tolist()))
        budgets[str(budget)] = case_metrics(y[indices], p, model.labels, macro)
        for i, values, scores in zip(indices, inputs, p):
            records.append(
                {
                    "domain": domain,
                    "id": ids[i],
                    "reference": model.labels[int(y[i])],
                    "requested_budget": budget,
                    "observed_packets": len(values),
                    "top1": model.labels[int(scores.argmax())],
                    "probabilities": scores.tolist(),
                    **({"family": families[ids[i]]} if families else {}),
                }
            )
    report = {
        "budgets": budgets,
        "macro_f1": float(np.mean([r["macro_f1"] for r in budgets.values()])),
        "class_recall": {
            label: float(np.mean([r["classes"][label]["recall"] for r in budgets.values()]))
            for label in model.labels
            if any(r["classes"][label]["support"] for r in budgets.values())
        },
    }
    if families:
        report["family_cells"] = {}
        for label in cfg["local_labels"]:
            for family in (4, 6):
                cell = {}
                for budget in cfg["budgets"]:
                    rows = [
                        r
                        for r in records
                        if r["reference"] == label
                        and r["family"] == family
                        and r["requested_budget"] == budget
                    ]
                    correct = sum(r["top1"] == label for r in rows)
                    cell[str(budget)] = {
                        "n": len(rows),
                        "correct": correct,
                        "recall": correct / len(rows) if rows else None,
                    }
                report["family_cells"][f"{label}:IPv{family}"] = cell
    return report, records


def gates(candidate, control, cfg):
    rules = cfg["gates"]
    epsilon = 1e-12
    local, old = candidate["local"], control["local"]
    public, base = candidate["public"], control["public"]
    return {
        "local_f1_floor": local["macro_f1"] >= rules["minimum_local_clean_f1"],
        "local_f1_gain": local["macro_f1"] + epsilon >= old["macro_f1"] + rules["minimum_local_f1_gain"],
        "local_class_no_regression": all(
            local["class_recall"][c] + epsilon >= v for c, v in old["class_recall"].items()
        ),
        "public_f1_retention": public["macro_f1"] + epsilon
        >= base["macro_f1"] - rules["maximum_public_f1_loss"],
        "public_class_retention": all(
            public["class_recall"][c] + epsilon >= v - rules["maximum_public_class_recall_loss"]
            for c, v in base["class_recall"].items()
        ),
    }


def run(config_path, output):
    cfg = read_config(config_path)
    out = Path(output)
    if out.exists():
        raise FileExistsError("preserve existing pilot; no tuning/retry into old output")
    ref = Predictor(cfg["reference_bundle"])
    if (
        ref.identity != cfg["reference_id"]
        or sha256(Path(cfg["reference_bundle"]) / "forest.json") != cfg["reference_weight_sha256"]
    ):
        raise ValueError("reference artifact changed")
    if sha256(Path(cfg["public_data"]) / "manifest.json") != cfg["public_manifest_sha256"]:
        raise ValueError("public manifest changed")
    rows, old_bindings = local_rows(ref, cfg)
    new, new_bindings = new_training(cfg)
    check_roles(rows["train"] + new, rows["selection"])
    if len({r["id"] for r in rows["train"] + new}) != len(rows["train"]) + len(new):
        raise ValueError("new/original training duplicates")
    families, family_bindings = selection_families(cfg, rows["selection"])
    public, py, pids, _ = read_public(cfg["public_data"], "train")
    validation, vy, vids, _ = read_public(cfg["public_data"], "selection", cfg["public_selection_per_class"])
    if len(public) != 14000:
        raise ValueError("public training count changed")
    selection = [Flow(packets=r["packets"]).array() for r in rows["selection"]]
    sy = np.array([ref.labels.index(r["label"]) for r in rows["selection"]])
    out.mkdir(parents=True, exist_ok=False)
    manifest = {
        "original_exports": old_bindings,
        "adopted_training_archives": new_bindings,
        "selection_family_metadata": family_bindings,
        "public_manifest_sha256": cfg["public_manifest_sha256"],
        "public_training_ids": pids,
        "public_selection_ids": vids,
        "original_training_ids": [r["id"] for r in rows["train"]],
        "new_training_ids": [r["id"] for r in new],
        "selection_ids": [r["id"] for r in rows["selection"]],
        "limits": cfg["limits"],
    }
    write_json(out / "data-manifest.json", manifest)
    provenance = {
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "fixture": False,
        "experimental": True,
        "config": cfg,
        "forest_seed": cfg["seed"],
        "source_commit": subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
        "source_sha256": sha256(__file__),
        "inference_sources": {n: sha256(Path(__file__).parent / n) for n in ("bundle.py", "contract.py")},
        "data_manifest_sha256": sha256(out / "data-manifest.json"),
        "license": "CESNET CC-BY-4.0 and private local training examples",
        "limits": cfg["limits"],
    }
    write_json(out / "config.json", provenance)
    reports = {}
    for arm in cfg["arms"]:
        started = time.perf_counter()
        local = rows["train"] + (new if arm == "plus-real-ipv6" else [])
        flows = public + [Flow(packets=r["packets"]).array() for r in local]
        targets = np.array([ref.labels.index(r["label"]) for r in local])
        print(
            json.dumps(
                {
                    "stage": "building_and_fitting",
                    "arm": arm,
                    "local_counts": dict(Counter(r["label"] for r in local)),
                }
            ),
            flush=True,
        )
        features = np.asarray(
            [forest_features(raw[:b], ref.normalizer, "summary-v1") for raw in flows for b in cfg["budgets"]]
        )
        weights = forest_weights(len(public) * 4, np.repeat(targets, 4), cfg["local_training_mass"])
        model = RandomForestClassifier(**cfg["forest"], random_state=cfg["seed"], n_jobs=cfg["threads"])
        model.fit(features, np.repeat(np.concatenate([py, targets]), 4), sample_weight=weights)
        bundle = export_bundle(
            out / arm / "bundle",
            model,
            ref.normalizer,
            ref.labels,
            {**provenance, "arm": arm, "local_counts": dict(Counter(r["label"] for r in local))},
            {"feature_map": "summary-v1"},
            UNCOMMITTED,
        )
        if arm == "control" and sha256(bundle / "forest.json") != cfg["reference_weight_sha256"]:
            raise ValueError("control does not reproduce original weights; stop before candidate")
        predictor = Predictor(bundle)
        expected = model.predict_proba(features[:16])
        actual = predictor.probabilities([raw[:b] for raw in flows[:4] for b in cfg["budgets"]])
        difference = float(np.max(np.abs(expected - actual)))
        if difference > 1e-12:
            raise ValueError("exported inference differs from sklearn")
        del features, model, flows
        loc, lp = clean_assessment(
            predictor, selection, sy, [r["id"] for r in rows["selection"]], "local", cfg, families
        )
        pub, pp = clean_assessment(predictor, validation, vy, vids, "public", cfg)
        report = {
            "local": loc,
            "public": pub,
            "artifact_id": predictor.identity,
            "local_training_counts": dict(Counter(r["label"] for r in local)),
            "export_maximum_difference": difference,
            "seconds": time.perf_counter() - started,
        }
        write_json(out / arm / "development.json", report)
        write_json(out / arm / "predictions.json", lp + pp)
        reports[arm] = report
        print(
            json.dumps(
                {
                    "arm": arm,
                    "local_f1": loc["macro_f1"],
                    "local_recall": loc["class_recall"],
                    "public_f1": pub["macro_f1"],
                    "seconds": report["seconds"],
                }
            ),
            flush=True,
        )
    checks = gates(reports["plus-real-ipv6"], reports["control"], cfg)
    decision = {
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "config_sha256": CONFIG_SHA,
        "config": cfg,
        "gates": checks,
        "status": "promising_for_fresh_evaluation" if all(checks.values()) else "stop_no_eligible_repair",
        "artifact_ids": {a: r["artifact_id"] for a, r in reports.items()},
        "development_sha256": {a: sha256(out / a / "development.json") for a in reports},
        "prediction_sha256": {a: sha256(out / a / "predictions.json") for a in reports},
        "config_provenance_sha256": sha256(out / "config.json"),
        "policy_fitted": False,
        "default_promoted": False,
        "limits": cfg["limits"],
    }
    write_json(out / "decision.json", decision)
    return decision
