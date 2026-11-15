"""Validate archived genuine window evidence and replay its actual source model."""

import argparse
import json
from pathlib import Path

import torch

from netembed.bundle import Predictor, sha256, write_json
from netembed.contract import Flow
from netembed.window_validation import validate_windows


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default="artifacts/local/window-validation")
    parser.add_argument("--trial", default="window-engineering-01")
    parser.add_argument("--bundle", default="experiments/full-real/20261024-151720-3532794c/bundle")
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    if Path(args.trial).name != args.trial:
        raise ValueError("trial must be a local basename")
    output = Path(args.output)
    if output.exists():
        raise FileExistsError(output)
    root = Path(args.root)
    names = ("intent", "capture", "windows", "summary", "status", "assessment")
    files = {name: root / f"{args.trial}-{name}.json" for name in names}
    values = {name: json.loads(path.read_text()) for name, path in files.items()}
    report = validate_windows(values["intent"], values["capture"], values["windows"], values["status"])
    if any(values[k]["session_id"] != report["session_id"] for k in ("summary", "assessment")):
        raise ValueError("summary/assessment belongs to a different session")
    torch.set_num_threads(2)
    predictor = Predictor(args.bundle)
    if predictor.identity != values["intent"]["expected_artifact_id"]:
        raise ValueError("replay model differs from capture intent")
    count, maximum = 0, 0
    for flow in values["capture"]["flows"]:
        for saved in flow["predictions"]:
            actual = predictor.predict(Flow(packets=flow["packets"][: saved["observed_packets"]]).array())
            if (
                actual["artifact_id"] != saved["artifact_id"]
                or actual["observed_packets"] != saved["observed_packets"]
                or actual["label"] != saved["label"]
                or actual["status"] != saved["status"]
                or [a["label"] for a in actual["alternatives"]] != [a["label"] for a in saved["alternatives"]]
            ):
                raise ValueError("original prediction labels/status do not reproduce")
            maximum = max(
                maximum,
                max(
                    abs(a["score"] - b["score"])
                    for a, b in zip(actual["alternatives"], saved["alternatives"])
                ),
            )
            count += 1
    if maximum > 1e-6:
        raise ValueError("original scores do not reproduce")
    summary = values["summary"]
    report.update(
        {
            "source_prediction_replay": {"n": count, "maximum_score_difference": maximum, "tolerance": 1e-6},
            "counters": values["status"],
            "window_evidence_evicted": values["windows"]["evicted"],
            "prefix_evidence_evicted": values["capture"]["evidence_evicted"],
            "prediction_browser_receipt_ms": {
                "n": summary["browser_receipt_n"],
                "p50": summary["browser_receipt_p50_ms"],
                "p95": summary["browser_receipt_p95_ms"],
            },
            "observation_browser_receipts_measured": False,
            "browser_display_independently_inspected": False,
            "user_context": "User reports YouTube in normal Chrome, not private. Context is not per-flow truth.",
            "data_role": "engineering_only_unscored; never calibration/final or independent accuracy",
            "used_for_training": False,
            "source_sha256": {
                str(p): sha256(p) for p in (Path(__file__), Path("src/netembed/window_validation.py"))
            },
            "evidence_sha256": {path.name: sha256(path) for path in files.values()},
        }
    )
    write_json(output, report)
    print(json.dumps({k: report[k] for k in ("session_id", "horizons", "source_prediction_replay")}))


if __name__ == "__main__":
    main()
