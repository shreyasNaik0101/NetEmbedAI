"""Complete the already-declared seed123 pair after a premature seed42 stop."""

from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import sys
import time

import numpy as np
import torch
from sklearn.ensemble import RandomForestClassifier
from threadpoolctl import threadpool_limits

from netembed.bundle import Predictor, export_bundle, sha256, write_json
from netembed.contract import Flow, forest_features
from netembed.ipv6_pilot import read_config as read_recipe
from netembed.matched_timing_jitter import assignment, gates, jitter
from netembed.paired_study import read_plan
from netembed.spotify_weights import sample_weights
from study_matched_timing_jitter import CONFIG, CONFIG_SHA, assess, guard, load_data

PREVIOUS = Path("experiments/timing-jitter-matched-v1-execution-recovery")
PREVIOUS_DECISION_SHA = "2f870812203b41fca33e852f47ff67d58b6545b686e770bf6b78b9078f0aefa1"
RUNNER_SHA = "8ed35518035c96b53163a5cfefff7c9ea8d70ffc670a04ac482efa1e3bb9d07d"
OUT = Path("experiments/timing-jitter-matched-v1-seed123-continuation")


def main():
    raw = CONFIG.read_bytes().replace(b"\r\n", b"\n")
    if (
        hashlib.sha256(raw).hexdigest() != CONFIG_SHA
        or sha256(Path("scripts/study_matched_timing_jitter.py")) != RUNNER_SHA
    ):
        raise ValueError("fixed original protocol or runner changed")
    cfg = json.loads(raw)
    previous = read_plan(cfg["previous_plan"])
    recipe = read_recipe(cfg["training_recipe"])
    if OUT.exists():
        raise FileExistsError("preserve existing continuation; no repeat")
    if sha256(PREVIOUS / "decision.json") != PREVIOUS_DECISION_SHA:
        raise ValueError("prior decision changed")
    decision = json.loads((PREVIOUS / "decision.json").read_text())
    if (
        cfg["forest_seeds"] != [17, 42, 123]
        or not decision["seeds"]["17"]["passed"]
        or decision["seeds"]["42"]["passed"]
        or set(decision["seeds"]) != {"17", "42"}
    ):
        raise ValueError("not the known premature stop before declared seed123")
    for seed, row in decision["seeds"].items():
        for arm, digest in row["metrics_sha256"].items():
            if sha256(PREVIOUS / f"seed{seed}" / arm / "metrics.json") != digest:
                raise ValueError("prior seed evidence changed")

    def bounded_guard(event, values):
        if event == "open" and isinstance(values[0], (str, bytes)):
            path = Path(os.fsdecode(values[0])).resolve()
            if path.is_relative_to(OUT.resolve()):
                return
        guard(event, values, cfg, recipe, OUT)

    sys.addaudithook(bounded_guard)
    torch.set_num_threads(cfg["threads"])
    source = Predictor(cfg["source_bundle"])
    if (
        source.identity != cfg["source_artifact_id"]
        or source.fixed_prefix_packets != 10
        or source.meta["policy"]["fitted"]
        or source.meta["provenance"].get("fixture", True)
        or sha256(Path(cfg["source_bundle"]) / "forest.json") != cfg["source_weight_sha256"]
    ):
        raise ValueError("source model differs")
    print("Completing predeclared seed123 with the same role-bound data; final inputs blocked.", flush=True)
    public, py, pids, train, cohorts, manifest = load_data(cfg, recipe, previous, source)
    original = public + [Flow(packets=r["packets"]).array() for r in train]
    identifiers = pids + [r["id"] for r in train]
    deltas = [assignment(ident, cfg["augmentation"]["seed"]) for ident in identifiers]
    if len(set(identifiers)) != len(identifiers):
        raise ValueError("duplicate training identity")
    local_labels = np.repeat([r["label"] for r in train], len(cfg["training_budgets"]))
    targets = np.repeat(
        np.concatenate([py, [source.labels.index(r["label"]) for r in train]]), len(cfg["training_budgets"])
    )
    weights = sample_weights(len(public) * len(cfg["training_budgets"]), local_labels, cfg["spotify_mass"])
    OUT.mkdir(parents=True, exist_ok=False)
    write_json(OUT / "data-manifest.json", manifest)
    write_json(
        OUT / "augmentation-manifest.json",
        {
            "seed": cfg["augmentation"]["seed"],
            "assignments": [{"id": ident, "delta_ms": delta} for ident, delta in zip(identifiers, deltas)],
            "counts": {str(d): deltas.count(d) for d in (-0.1, 0.0, 0.1)},
        },
    )
    if (
        sha256(OUT / "data-manifest.json") != decision["training_data_manifest_sha256"]
        or sha256(OUT / "augmentation-manifest.json") != decision["augmentation_manifest_sha256"]
    ):
        raise ValueError("continuation data/augmentation changed; stop before fitting")
    print("Building the same two feature matrices for seed123.", flush=True)
    features = {
        arm: np.asarray(
            [
                forest_features(
                    (raw if arm == "control" else jitter(raw, delta))[:b], source.normalizer, "summary-v1"
                )
                for raw, delta in zip(original, deltas)
                for b in cfg["training_budgets"]
            ]
        )
        for arm in ("control", "jitter")
    }
    if features["control"].shape != features["jitter"].shape or len(targets) != len(weights):
        raise ValueError("matched training inventories differ")
    results = {}
    with threadpool_limits(limits=cfg["threads"]):
        for arm in ("control", "jitter"):
            started = time.perf_counter()
            print(f"Fitting predeclared seed123: {arm}.", flush=True)
            estimator = RandomForestClassifier(**cfg["forest"], random_state=123, n_jobs=cfg["threads"])
            estimator.fit(features[arm], targets, sample_weight=weights)
            folder = OUT / arm
            bundle = export_bundle(
                folder / "bundle",
                estimator,
                source.normalizer,
                source.labels,
                {
                    "fixture": False,
                    "experimental": True,
                    "config_sha256": CONFIG_SHA,
                    "prior_decision_sha256": PREVIOUS_DECISION_SHA,
                    "runner_sha256": sha256(Path(__file__)),
                    "augmentation_source_sha256": sha256(Path("src/netembed/matched_timing_jitter.py")),
                    "data_manifest_sha256": sha256(OUT / "data-manifest.json"),
                    "augmentation_manifest_sha256": sha256(OUT / "augmentation-manifest.json"),
                    "seed": 123,
                    "arm": arm,
                    "limits": cfg["limits"],
                },
                {"feature_map": "summary-v1", "fixed_prefix_packets": 10},
                {
                    "version": "matched-jitter-unfitted-v1",
                    "fitted": False,
                    "threshold": 1.0,
                    "min_packets": 10,
                    "temperature": 1.0,
                    "tie_break": "label_order",
                },
            )
            model = Predictor(bundle)
            probe = [x[:10] for x in original[:4] + original[-4:] if len(x) >= 10]
            expected = estimator.predict_proba(
                np.asarray([forest_features(x, source.normalizer, "summary-v1") for x in probe])
            )
            parity = float(np.max(np.abs(expected - model.probabilities(probe))))
            if parity > 1e-12:
                raise ValueError("portable model parity failed")
            metrics, predictions = assess(model, cohorts, cfg["views"])
            write_json(folder / "predictions.json", predictions)
            results[arm] = {
                "metrics": metrics,
                "artifact_id": model.identity,
                "weights_sha256": sha256(bundle / "forest.json"),
                "prediction_sha256": sha256(folder / "predictions.json"),
                "sklearn_export_max_abs_difference": parity,
                "fit_export_assess_seconds": time.perf_counter() - started,
            }
            write_json(folder / "metrics.json", results[arm])
    checks = gates(results["control"]["metrics"], results["jitter"]["metrics"], source.labels)
    result = {
        "status": "stop_no_validated_candidate",
        "seed123_gates": checks,
        "seed123_passed": all(checks.values()),
        "prior_seed17_passed": True,
        "prior_seed42_passed": False,
        "previous_decision_sha256": PREVIOUS_DECISION_SHA,
        "config_sha256": CONFIG_SHA,
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "default_promoted": False,
        "threshold_fitted": False,
        "final_data_opened": False,
        "capture_started": False,
        "metrics_sha256": {arm: sha256(OUT / arm / "metrics.json") for arm in results},
        "limits": cfg["limits"],
        "reason": "Seed42 failed; all predeclared seeds must pass. Seed123 cannot rescue that failure.",
    }
    write_json(OUT / "decision.json", result)
    print(json.dumps(result, indent=2), flush=True)


if __name__ == "__main__":
    main()
