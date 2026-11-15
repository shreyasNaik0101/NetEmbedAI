"""Fixed matched forest pilot; no network, capture, calibration or promotion."""

import argparse
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
from sklearn.metrics import f1_score
from threadpoolctl import threadpool_limits

from netembed.browser_adaptation import check_roles
from netembed.bundle import Predictor, export_bundle, sha256, write_json
from netembed.contract import Flow, forest_features
from netembed.ipv6_pilot import new_training, read_config as read_recipe
from netembed.matched_timing_jitter import assignment, gates, jitter
from netembed.paired_study import read_plan
from netembed.prefix_sensitivity import views
from netembed.size_robustness import local_rows, read_public
from netembed.spotify_repair import role_rows, stage_receipt
from netembed.spotify_repair_stages import local_rows_selection
from netembed.spotify_weights import access_guard, sample_weights
from netembed.ten_packet import exact_ten_cohort

CONFIG = Path("configs/timing-jitter-matched-v1.json")
CONFIG_SHA = "0a446675f24664cf236aca8eb9823bd5c310ec93854b7a6c1351b13b5c201cc5"


def guard(event, args, cfg, recipe, output=None):
    if event == "open" and isinstance(args[0], (str, bytes)):
        path = Path(os.fsdecode(args[0])).resolve()
        if (
            path.is_relative_to(Path(cfg["source_bundle"]).resolve())
            or path == Path(cfg["baseline_predictions"]).resolve()
            or (output is not None and path.is_relative_to(Path(output).resolve()))
        ):
            return
    access_guard(event, args, cfg, recipe)


def load_data(cfg, recipe, previous, source):
    stage_receipt(cfg["previous_root"], previous, "training")
    reference = Predictor(recipe["reference_bundle"])
    original, old_bindings = local_rows(reference, recipe)
    adopted, adopted_bindings = new_training(recipe)
    spotify, spotify_bindings = role_rows(cfg["previous_root"], previous, "train")
    spotify_dev, dev_bindings = role_rows(cfg["previous_root"], previous, "selection")
    retained, retained_bindings = local_rows_selection(reference, recipe)
    train = original["train"] + adopted + spotify
    check_roles(train, retained + spotify_dev)
    if len(train) != 79 or len(spotify) != 17 or len(spotify_dev) != 4 or len(retained) != 17:
        raise ValueError("role-bound local inventory differs")
    if len({r["id"] for r in train}) != len(train):
        raise ValueError("duplicate local training rows")
    public, targets, ids, _ = read_public(recipe["public_data"], "train")
    validation, vy, vids, _ = read_public(recipe["public_data"], "selection", 50)
    if (
        sha256(Path(recipe["public_data"]) / "manifest.json") != recipe["public_manifest_sha256"]
        or len(public) != 14000
    ):
        raise ValueError("public training inventory changed")
    path = Path(cfg["previous_training_manifest"])
    if sha256(path) != cfg["previous_training_manifest_sha256"]:
        raise ValueError("prior training manifest changed")
    previous_manifest = json.loads(path.read_text())
    if (
        ids != previous_manifest["public_training_ids"]
        or [r["id"] for r in spotify] != previous_manifest["new_spotify_training_ids"]
        or [r["id"] for r in train[:62]] != previous_manifest["old_local_training_ids"]
    ):
        raise ValueError("training examples differ from prior model")
    local_dev = retained + spotify_dev
    local_x = [Flow(packets=r["packets"]).array() for r in local_dev]
    public_exact, excluded = exact_ten_cohort(validation, vy, vids)
    if (
        len(public_exact[0]) != 452
        or len(excluded) != 48
        or len(local_x) != 21
        or any(len(x) < 10 for x in local_x)
    ):
        raise ValueError("fixed ten-packet development inventory differs")
    cohorts = {
        "public": public_exact,
        "local": (
            [x[:10] for x in local_x],
            np.asarray([source.labels.index(r["label"]) for r in local_dev]),
            [r["id"] for r in local_dev],
        ),
    }
    manifest = {
        "public_training_ids": ids,
        "local_training_ids": [r["id"] for r in train],
        "selection_ids": {name: cohort[2] for name, cohort in cohorts.items()},
        "public_short_excluded": excluded,
        "old_exports": old_bindings,
        "adopted_archives": adopted_bindings,
        "spotify_training": spotify_bindings,
        "spotify_selection": dev_bindings,
        "retained_selection": retained_bindings,
    }
    return public, targets, ids, train, cohorts, manifest


def assess(model, cohorts, view_names):
    results, predictions = {}, []
    labels = model.labels
    for domain, (flows, targets, ids) in cohorts.items():
        results[domain] = {}
        for view in view_names:
            arrays = [views(raw)[0][view] for raw in flows]
            probabilities = np.concatenate(
                [model.probabilities(arrays[i : i + 128]) for i in range(0, len(arrays), 128)]
            )
            predicted = probabilities.argmax(axis=1)
            classes = {}
            for index, label in enumerate(labels):
                mask = targets == index
                count = int(mask.sum())
                correct = int((predicted[mask] == index).sum())
                classes[label] = {"n": count, "correct": correct, "recall": correct / count if count else 0.0}
            macro_labels = (
                list(range(len(labels)))
                if domain == "public"
                else [labels.index(x) for x in ("youtube", "instagram", "spotify")]
            )
            results[domain][view] = {
                "n": len(ids),
                "correct": int((predicted == targets).sum()),
                "macro_f1": float(
                    f1_score(targets, predicted, labels=macro_labels, average="macro", zero_division=0)
                ),
                "classes": classes,
            }
            for ident, target, p in zip(ids, targets, probabilities):
                predictions.append(
                    {
                        "domain": domain,
                        "id": ident,
                        "reference": labels[int(target)],
                        "view": view,
                        "top1": labels[int(p.argmax())],
                        "probabilities": p.tolist(),
                    }
                )
    return results, predictions


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--recover-sandbox-failure", action="store_true")
    args = parser.parse_args()
    raw_cfg = CONFIG.read_bytes().replace(b"\r\n", b"\n")
    if hashlib.sha256(raw_cfg).hexdigest() != CONFIG_SHA:
        raise ValueError("fixed matched protocol changed")
    cfg = json.loads(raw_cfg)
    previous, recipe = read_plan(cfg["previous_plan"]), read_recipe(cfg["training_recipe"])
    original_out = Path(cfg["output"])
    out = (
        Path("experiments/timing-jitter-matched-v1-execution-recovery")
        if args.recover_sandbox_failure
        else original_out
    )
    if out.exists():
        raise FileExistsError("preserve existing study; no repeated or extra fits")
    if args.recover_sandbox_failure:
        expected_names = {"protocol.json", "data-manifest.json", "augmentation-manifest.json"}
        if {p.name for p in original_out.iterdir()} != expected_names:
            raise ValueError("previous attempt is not the pre-fit-only sandbox failure")
        if (
            json.loads((original_out / "protocol.json").read_text()) != cfg
            or sha256(original_out / "data-manifest.json")
            != "b4792438ebc8b112528b301750a7f2bee2642e21ee79b5bf86f5fc45e6b9cd0b"
            or sha256(original_out / "augmentation-manifest.json")
            != "b96f4994b0e98ef956843a10d3c8a5ca14994135730f5eb0f7e6ae47cdcb7e4a"
        ):
            raise ValueError("previous pre-fit data or protocol changed")
    sys.addaudithook(lambda event, values: guard(event, values, cfg, recipe, out))
    torch.set_num_threads(cfg["threads"])
    source = Predictor(cfg["source_bundle"])
    if (
        source.identity != cfg["source_artifact_id"]
        or source.fixed_prefix_packets != 10
        or source.meta["policy"]["fitted"]
        or source.meta["provenance"].get("fixture", True)
        or sha256(Path(cfg["source_bundle"]) / "forest.json") != cfg["source_weight_sha256"]
        or sha256(cfg["baseline_predictions"]) != cfg["baseline_predictions_sha256"]
    ):
        raise ValueError("frozen source or baseline changed")
    print("Loading role-bound training and exposed selection data; final inputs blocked.", flush=True)
    public, py, pids, train, cohorts, manifest = load_data(cfg, recipe, previous, source)
    original = public + [Flow(packets=r["packets"]).array() for r in train]
    identifiers = pids + [r["id"] for r in train]
    deltas = [assignment(ident, cfg["augmentation"]["seed"]) for ident in identifiers]
    if len(set(identifiers)) != len(identifiers):
        raise ValueError("duplicate training flow identifiers")
    local_labels = np.repeat([r["label"] for r in train], len(cfg["training_budgets"]))
    targets = np.repeat(
        np.concatenate([py, [source.labels.index(r["label"]) for r in train]]), len(cfg["training_budgets"])
    )
    weights = sample_weights(len(public) * len(cfg["training_budgets"]), local_labels, cfg["spotify_mass"])
    out.mkdir(parents=True, exist_ok=False)
    write_json(out / "protocol.json", cfg)
    write_json(out / "data-manifest.json", manifest)
    write_json(
        out / "augmentation-manifest.json",
        {
            "seed": cfg["augmentation"]["seed"],
            "assignments": [{"id": ident, "delta_ms": delta} for ident, delta in zip(identifiers, deltas)],
            "counts": {str(d): deltas.count(d) for d in (-0.1, 0.0, 0.1)},
        },
    )
    if args.recover_sandbox_failure:
        if (
            sha256(out / "data-manifest.json")
            != "b4792438ebc8b112528b301750a7f2bee2642e21ee79b5bf86f5fc45e6b9cd0b"
            or sha256(out / "augmentation-manifest.json")
            != "b96f4994b0e98ef956843a10d3c8a5ca14994135730f5eb0f7e6ae47cdcb7e4a"
        ):
            raise ValueError("recovery inputs differ; stop before any fit")
        write_json(
            out / "recovery.json",
            {
                "previous_status": "Windows worker-pool permission denied before any tree fit",
                "previous_runner_sha256": "b63d4b8286e00d6439ab787f218b9de49bc5192b7baebfa188f81b4f306e067c",
                "data_manifest_sha256": sha256(out / "data-manifest.json"),
                "augmentation_manifest_sha256": sha256(out / "augmentation-manifest.json"),
                "changed_recipe_or_data": False,
            },
        )
    print("Building matched control and jitter feature matrices.", flush=True)
    features = {}
    for arm in ("control", "jitter"):
        features[arm] = np.asarray(
            [
                forest_features(
                    (raw if arm == "control" else jitter(raw, delta))[:budget],
                    source.normalizer,
                    "summary-v1",
                )
                for raw, delta in zip(original, deltas)
                for budget in cfg["training_budgets"]
            ]
        )
    if features["control"].shape != features["jitter"].shape or len(targets) != len(weights):
        raise ValueError("matched training inventories differ")
    baseline = json.loads(Path(cfg["baseline_predictions"]).read_text())
    expected = {(r["domain"], r["id"]): r for r in baseline}
    outcomes = {}
    with threadpool_limits(limits=cfg["threads"]):
        for seed in cfg["forest_seeds"]:
            results = {}
            for arm in ("control", "jitter"):
                started = time.perf_counter()
                print(f"Fitting seed {seed}: {arm}.", flush=True)
                estimator = RandomForestClassifier(**cfg["forest"], random_state=seed, n_jobs=cfg["threads"])
                estimator.fit(features[arm], targets, sample_weight=weights)
                folder = out / f"seed{seed}" / arm
                bundle = export_bundle(
                    folder / "bundle",
                    estimator,
                    source.normalizer,
                    source.labels,
                    {
                        "fixture": False,
                        "experimental": True,
                        "config_sha256": CONFIG_SHA,
                        "runner_sha256": sha256(Path(__file__)),
                        "augmentation_source_sha256": sha256(Path("src/netembed/matched_timing_jitter.py")),
                        "data_manifest_sha256": sha256(out / "data-manifest.json"),
                        "augmentation_manifest_sha256": sha256(out / "augmentation-manifest.json"),
                        "seed": seed,
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
                        "note": "No inherited confidence policy.",
                    },
                )
                model = Predictor(bundle)
                weight_hash = sha256(bundle / "forest.json")
                if seed == 17 and arm == "control" and weight_hash != cfg["source_weight_sha256"]:
                    raise ValueError("seed17 control weights differ; stop before candidate fitting")
                probe = [x[:10] for x in original[:4] + original[-4:] if len(x) >= 10]
                sklearn_probs = estimator.predict_proba(
                    np.asarray([forest_features(x, source.normalizer, "summary-v1") for x in probe])
                )
                parity = float(np.max(np.abs(sklearn_probs - model.probabilities(probe))))
                if parity > 1e-12:
                    raise ValueError("portable model parity failed")
                metrics, predictions = assess(model, cohorts, cfg["views"])
                if seed == 17 and arm == "control":
                    for p in predictions:
                        if p["view"] != "unchanged":
                            continue
                        domain = (
                            "spotify"
                            if p["domain"] == "local" and p["reference"] == "spotify"
                            else p["domain"]
                        )
                        prior = expected[(domain, p["id"])]
                        if prior["reference"] != p["reference"] or not np.allclose(
                            prior["probabilities"], p["probabilities"], atol=1e-12, rtol=0
                        ):
                            raise ValueError(
                                "control baseline predictions differ; stop before candidate fitting"
                            )
                write_json(folder / "predictions.json", predictions)
                results[arm] = {
                    "metrics": metrics,
                    "artifact_id": model.identity,
                    "weights_sha256": weight_hash,
                    "prediction_sha256": sha256(folder / "predictions.json"),
                    "sklearn_export_max_abs_difference": parity,
                    "fit_export_assess_seconds": time.perf_counter() - started,
                }
                write_json(folder / "metrics.json", results[arm])
            checks = gates(results["control"]["metrics"], results["jitter"]["metrics"], source.labels)
            outcomes[str(seed)] = {
                "gates": checks,
                "passed": all(checks.values()),
                "metrics_sha256": {
                    arm: sha256(out / f"seed{seed}" / arm / "metrics.json") for arm in results
                },
            }
            write_json(out / f"seed{seed}" / "result.json", outcomes[str(seed)])
            print(json.dumps({"seed": seed, "gates": checks}), flush=True)
            if not outcomes[str(seed)]["passed"]:
                break
    passed = len(outcomes) == len(cfg["forest_seeds"]) and all(row["passed"] for row in outcomes.values())
    decision = {
        "status": "development_candidate_only" if passed else "stop_no_validated_candidate",
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "config_sha256": CONFIG_SHA,
        "seeds": outcomes,
        "threshold_fitted": False,
        "default_promoted": False,
        "final_data_opened": False,
        "capture_started": False,
        "training_data_manifest_sha256": sha256(out / "data-manifest.json"),
        "augmentation_manifest_sha256": sha256(out / "augmentation-manifest.json"),
        "limits": cfg["limits"],
    }
    write_json(out / "decision.json", decision)
    print(json.dumps(decision, indent=2), flush=True)


if __name__ == "__main__":
    main()
