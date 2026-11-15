"""Fit only the frozen browser candidate's policy on reserved calibration data."""

import copy
import json
import shutil
import subprocess
from collections import Counter
from datetime import datetime
from pathlib import Path

import numpy as np

from .browser_adaptation import check_roles, load_reference_trial
from .bundle import Predictor, sha256, write_json
from .contract import BUDGETS, Flow
from .data import read_split


def score_stats(scores, truth, threshold):
    scores, truth = np.asarray(scores), np.asarray(truth)
    keep = scores.max(1) >= threshold
    return {
        "n": len(truth),
        "accepted": int(keep.sum()),
        "coverage": float(keep.mean()),
        "error": float((scores.argmax(1)[keep] != truth[keep]).mean()) if keep.any() else None,
    }


def fit_joint_policy(local_scores, local_truth, public_scores, public_truth, required, plan):
    arrays = [np.asarray(local_scores, dtype=np.float64), np.asarray(public_scores, dtype=np.float64)]
    truths = [np.asarray(local_truth, dtype=np.int64), np.asarray(public_truth, dtype=np.int64)]
    for scores, truth in zip(arrays, truths):
        if (
            scores.ndim != 2
            or not len(scores)
            or len(scores) != len(truth)
            or not np.isfinite(scores).all()
            or (scores < 0).any()
            or not np.allclose(scores.sum(1), 1, atol=1e-6)
            or (truth < 0).any()
            or (truth >= scores.shape[1]).any()
        ):
            raise ValueError("invalid calibration probabilities or targets")
    if arrays[0].shape[1] != arrays[1].shape[1] or not required:
        raise ValueError("calibration class map mismatch")
    curve = []
    for threshold in np.linspace(0, 1, 101):
        local = score_stats(arrays[0], truths[0], threshold)
        public = score_stats(arrays[1], truths[1], threshold)
        classes = {}
        for label in required:
            chosen = truths[0] == label
            classes[str(label)] = (
                score_stats(arrays[0][chosen], truths[0][chosen], threshold)
                if chosen.any()
                else {"n": 0, "accepted": 0, "coverage": 0.0, "error": None}
            )
        eligible = (
            local["accepted"] >= plan["minimum_accepted_local_prefixes"]
            and local["error"] <= plan["maximum_empirical_error_overall"]
            and public["accepted"] >= 30
            and public["error"] <= 0.1
            and all(
                v["accepted"] >= plan["minimum_accepted_prefixes_per_local_class"]
                and v["error"] <= plan["maximum_empirical_error_per_local_class"]
                for v in classes.values()
            )
        )
        curve.append(
            {
                "threshold": float(threshold),
                "local": local,
                "public": public,
                "local_classes": classes,
                "eligible": eligible,
                "joint_coverage": (local["coverage"] + public["coverage"]) / 2,
            }
        )
    viable = [row for row in curve if row["eligible"]]
    selected = max(viable, key=lambda row: row["joint_coverage"]) if viable else None
    policy = {
        "version": "browser-joint-calibration-v1",
        "threshold": selected["threshold"] if selected else 1.0,
        "fitted": selected is not None,
        "min_packets": 5,
        "temperature": 1.0,
        "target_error": plan["maximum_empirical_error_overall"],
        "note": "Empirical calibration on correlated prefixes, not a population risk guarantee or a calibrated correctness probability. No unknown-service detection.",
    }
    return policy, selected, curve


def write_policy_bundle(source, destination, policy, proof, *, provenance_key="browser_calibration"):
    if not policy["fitted"]:
        raise ValueError("infeasible policy cannot become a calibrated bundle")
    if provenance_key not in ("browser_calibration", "public_calibration"):
        raise ValueError("unsupported policy provenance scope")
    source, destination = Path(source), Path(destination)
    checksums = json.loads((source / "checksums.json").read_text())
    if set(checksums) not in ({"metadata.json", "forest.json"}, {"metadata.json", "weights.pt"}):
        raise ValueError("unexpected source bundle inventory")
    for name, digest in checksums.items():
        if sha256(source / name) != digest:
            raise ValueError("source bundle checksum mismatch")
    metadata = json.loads((source / "metadata.json").read_text())
    metadata["policy"] = copy.deepcopy(policy)
    metadata["provenance"] = {
        **metadata["provenance"],
        provenance_key: proof,
        "uncalibrated_artifact_id": checksums["metadata.json"],
    }
    destination.mkdir(parents=True, exist_ok=False)
    for name in checksums:
        if name != "metadata.json":
            shutil.copyfile(source / name, destination / name)
    write_json(destination / "metadata.json", metadata)
    write_json(destination / "checksums.json", {name: sha256(destination / name) for name in checksums})
    return destination


def prefix_scores(predictor, flows, y, ids):
    xs, targets, records = [], [], []
    for flow, label, ident in zip(flows, y, ids):
        for budget in BUDGETS:
            if len(flow) >= budget:
                xs.append(flow[:budget])
                targets.append(int(label))
                records.append(
                    {"id": ident, "reference": predictor.labels[int(label)], "observed_packets": budget}
                )
    if not xs:
        raise ValueError("no calibration prefixes")
    scores = np.concatenate([predictor.probabilities(xs[i : i + 512]) for i in range(0, len(xs), 512)])
    for row, value in zip(records, scores):
        row.update(probabilities=value.tolist(), top1=predictor.labels[int(value.argmax())])
    return scores, np.asarray(targets), records


def collection_plan(root, name):
    if (
        Path(name).name != name
        or not name.startswith("calibration-collection-plan-")
        or not name.endswith(".json")
    ):
        raise ValueError("calibration plan must be a collection-local plan filename")
    path = Path(root) / name
    return path, json.loads(path.read_text())


def run(
    data,
    collection,
    bundle,
    decision_path,
    destination,
    additional=(),
    previous_report=None,
    plan_name="calibration-collection-plan-v1.json",
):
    root, out = Path(collection), Path(destination)
    if out.exists():
        raise FileExistsError(out)
    plan_path, plan = collection_plan(root, plan_name)
    decision = json.loads(Path(decision_path).read_text())
    predictor = Predictor(bundle)
    if (
        sha256(decision_path) != plan["candidate_decision_sha256"]
        or predictor.identity != decision["uncalibrated_artifact_id"]
        or predictor.identity != plan["candidate_artifact_id"]
        or predictor.meta["files"] != decision["model_files_sha256"]
        or predictor.normalizer.metadata() != decision["normalizer"]
        or predictor.meta["policy"]["fitted"]
    ):
        raise ValueError("candidate weights/normalizer/choice changed before calibration")
    if additional:
        if not previous_report or not set(additional).issubset(
            plan["additional_trials_only_if_support_insufficient"]
        ):
            raise ValueError("additional calibration requires prior infeasible report and reserved trials")
        previous = json.loads(Path(previous_report).read_text())
        if (
            previous["policy"]["fitted"]
            or previous["uncalibrated_artifact_id"] != predictor.identity
            or previous["provenance"]["plan_sha256"] != sha256(plan_path)
        ):
            raise ValueError("policy already frozen or prior candidate differs")
    trials = list(plan["first_trials"]) + list(additional)
    if len(set(trials)) != len(trials):
        raise ValueError("duplicate calibration trial")
    missing = [name for name in trials if not (root / f"{name}-collection-summary.json").exists()]
    if missing:
        raise ValueError("missing separate calibration recordings: " + ", ".join(missing))
    records, proofs, sessions = [], {}, set()
    original_groups = {v["session_id"] for v in predictor.meta["provenance"]["browser_evidence"].values()}
    frozen_time = 1000 * datetime.fromisoformat(decision["frozen_at_utc"]).timestamp()
    for name in trials:
        intent = json.loads((root / f"{name}-intent.json").read_text())
        if intent["calibration_target_artifact_id"] != predictor.identity or intent[
            "calibration_plan_sha256"
        ] != sha256(plan_path):
            raise ValueError("calibration intent does not bind frozen candidate/plan")
        rows, proof = load_reference_trial(root, name, predictor.labels, "calibration")
        if (
            proof["session_id"] in original_groups | sessions
            or proof["first_packet_range_unix_ms"][0] <= frozen_time
        ):
            raise ValueError("calibration reuses development session or predates candidate freeze")
        sessions.add(proof["session_id"])
        records.extend(rows)
        proofs[name] = proof
    check_roles([{"id": "reserved", "group_id": group} for group in original_groups], records)
    labels = ["youtube", "instagram"]
    targeted = [row for row in records if row["label"] in labels]
    required = [predictor.labels.index(label) for label in labels]
    local_scores, local_y, local_predictions = prefix_scores(
        predictor,
        [Flow(packets=row["packets"]).array() for row in targeted],
        [predictor.labels.index(row["label"]) for row in targeted],
        [row["id"] for row in targeted],
    )
    public, y, ids, manifest = read_split(data, "calibration")
    if sha256(Path(data) / "manifest.json") != predictor.meta["provenance"]["public_data_manifest_sha256"]:
        raise ValueError("historical calibration data manifest mismatch")
    counts, selected = Counter(), []
    for index, label in enumerate(y):
        if counts[int(label)] < 50:
            selected.append(index)
            counts[int(label)] += 1
    if any(counts[i] != 50 for i in range(len(predictor.labels))) or manifest["labels"] != predictor.labels:
        raise ValueError("historical calibration class support mismatch")
    public_scores, public_y, public_predictions = prefix_scores(
        predictor, [public[i] for i in selected], y[selected], [ids[i] for i in selected]
    )
    policy, selected_policy, curve = fit_joint_policy(
        local_scores, local_y, public_scores, public_y, required, plan
    )
    out.mkdir(parents=True)
    proof = {
        "plan": plan,
        "plan_sha256": sha256(plan_path),
        "candidate_decision_sha256": sha256(decision_path),
        "calibration_sources": proofs,
        "calibration_code_sha256": sha256(__file__),
        "calibration_source_commit": subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
        "historical_public_manifest_sha256": sha256(Path(data) / "manifest.json"),
        "historical_public_calibration_ids": [ids[i] for i in selected],
        "local_flow_counts": dict(Counter(row["label"] for row in targeted)),
        "selected_policy_statistics": selected_policy,
        "class_map": predictor.labels,
        "unscored_other_supported_flow_counts": dict(
            Counter(row["label"] for row in records if row["label"] not in labels)
        ),
        "note": "Weights and normalization unchanged. Threshold fit on separate calibration only. Historical public data is a retention control, not a forward test; local coverage limited to YouTube/Instagram.",
    }
    report = {
        "uncalibrated_artifact_id": predictor.identity,
        "policy": policy,
        "selected": selected_policy,
        "curve": curve,
        "provenance": proof,
        "weights_refitted": False,
        "final_evaluation": False,
        "local_available_prefixes": len(local_y),
        "historical_public_prefixes": len(public_y),
    }
    write_json(out / "local-predictions.json", local_predictions)
    write_json(out / "historical-predictions.json", public_predictions)
    proof["prediction_sha256"] = {
        name: sha256(out / name) for name in ("local-predictions.json", "historical-predictions.json")
    }
    if policy["fitted"]:
        result = write_policy_bundle(bundle, out / "bundle", policy, proof)
        report["calibrated_artifact_id"] = sha256(result / "metadata.json")
        report["weights_sha256"] = predictor.meta["files"]
    write_json(out / "report.json", report)
    return str(out)
