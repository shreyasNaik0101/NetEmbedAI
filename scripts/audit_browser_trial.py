"""Audit a saved browser-reference trial; never capture, fit, or change policy."""

import argparse
from pathlib import Path

import numpy as np
import torch

from netembed.bundle import Predictor, sha256, write_json
from netembed.contract import BUDGETS, Flow
from netembed.netlog_reference import read_bounded
from netembed.service_reference import summarize


def alternative_difference(original, replay):
    old = {a["label"]: a["score"] for a in original["alternatives"]}
    new = {a["label"]: a["score"] for a in replay["alternatives"]}
    if old.keys() != new.keys():
        raise ValueError("alternative inventory differs")
    return max((abs(old[k] - new[k]) for k in old), default=0.0)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("evidence", "reference", "bundle", "output"):
        parser.add_argument("--" + name, required=True)
    args = parser.parse_args()
    if Path(args.output).exists():
        raise FileExistsError("audit already exists; choose a new output path")
    evidence, evidence_sha = read_bounded(args.evidence)
    reference, reference_sha = read_bounded(args.reference)
    if evidence_sha != reference["evidence_sha256"]:
        raise ValueError("reference belongs to different capture evidence")
    if evidence["counters"]["running"]:
        raise ValueError("stop the user capture before auditing")
    if reference["fixture"] or evidence["fixture"]:
        raise ValueError("this audit requires real user-started evidence")
    torch.set_num_threads(2)
    predictor = Predictor(args.bundle)
    if not predictor.identity == evidence["artifact_id"] == reference["artifact_id"]:
        raise ValueError("artifact identities differ")
    originals = {flow["flow_id"]: flow for flow in evidence["flows"]}
    if len(originals) != len(evidence["flows"]) or len(originals) != len(reference["flows"]):
        raise ValueError("flow inventory differs")
    replay_rows, compared, max_difference, label_changes = [], 0, 0.0, 0
    matched_ids = set()
    for row in reference["flows"]:
        flow = originals[row["flow_id"]]
        if row["flow_id"] in matched_ids or any(flow[key] != row[key] for key in ("packets", "predictions")):
            raise ValueError("original packets or predictions were changed")
        matched_ids.add(row["flow_id"])
        raw = Flow(packets=flow["packets"]).array()
        predictions = {}
        for budget in BUDGETS:
            if len(raw) >= budget:
                predictions[budget] = predictor.predict(raw[:budget])
        for original in flow["predictions"]:
            replay = predictions[original["observed_packets"]]
            max_difference = max(max_difference, alternative_difference(original, replay))
            label_changes += original["label"] != replay["label"]
            compared += 1
        replay_rows.append(
            {
                "flow_id": row["flow_id"],
                "reference": row["reference"],
                "predictions": [
                    {"observed_packets": budget, **prediction} for budget, prediction in predictions.items()
                ],
            }
        )
    if label_changes or not np.isfinite(max_difference) or max_difference > 1e-6:
        raise ValueError("saved live predictions do not reproduce within 1e-6")
    write_json(
        args.output,
        {
            "session_id": evidence["session_id"],
            "artifact_id": predictor.identity,
            "evidence_sha256": evidence_sha,
            "reference_sha256": reference_sha,
            "bundle_checksums_sha256": sha256(Path(args.bundle) / "checksums.json"),
            "original_live_prediction_comparison": {
                "predictions": compared,
                "maximum_alternative_score_difference": max_difference,
                "changed_decision_labels": label_changes,
            },
            "reference_counts": reference["reference_counts"],
            "original_live_agreement_by_prefix": reference["agreement_by_prefix"],
            "offline_all_available_prefix_agreement": summarize(replay_rows),
            "offline_predictions": replay_rows,
            "note": "Diagnostic development trial, not final local accuracy. Offline replay fills available prefix checkpoints omitted by bounded live coalescing; it is not an arriving live prediction or latency measurement. All reference refusals stay in the inventory. No training data, fitting, augmentation or decision-policy changes. Inputs are bound by checksums; browser origins never enter inference.",
        },
    )


if __name__ == "__main__":
    main()
