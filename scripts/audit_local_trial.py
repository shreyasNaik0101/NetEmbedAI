"""Explore opted-in local metadata; no accuracy claim and no adapter/model changes."""

import argparse
import json
from pathlib import Path

import numpy as np
import torch

from netembed.bundle import Predictor, sha256, write_json
from netembed.contract import BUDGETS, Flow
from netembed.data import read_split


def feature_stats(flows):
    x = np.concatenate(flows)
    return {
        "flows": len(flows),
        "packets": len(x),
        "quantiles": [0, 50, 90, 99, 100],
        "iat_ms": np.percentile(x[:, 0], [0, 50, 90, 99, 100]).tolist(),
        "payload_bytes": np.percentile(x[:, 2], [0, 50, 90, 99, 100]).tolist(),
        "noninteger_iat_fraction": float(np.mean(x[:, 0] != np.floor(x[:, 0]))),
        "payload_above_1500_packets": int(np.sum(x[:, 2] > 1500)),
        "forward_packet_fraction": float(np.mean(x[:, 1] == 1)),
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--evidence", required=True)
    parser.add_argument("--data", required=True)
    parser.add_argument("--bundle", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    torch.set_num_threads(2)
    source = Path(args.evidence)
    evidence = json.loads(source.read_text(encoding="utf-8-sig"))
    if not evidence.get("reference_enabled") or not 1 <= len(evidence["flows"]) <= 256:
        raise ValueError("requires an opted-in bounded local trial export")
    predictor = Predictor(args.bundle)
    if evidence["artifact_id"] != predictor.identity:
        raise ValueError("trial and audit artifact identities differ")
    local = [Flow(packets=row["packets"]).array() for row in evidence["flows"]]
    training, _, _, _ = read_split(args.data, "train")  # Never opens selection/calibration/final test.
    rows = []
    for observed, raw in zip(evidence["flows"], local):
        predictions = {}
        for budget in BUDGETS:
            if len(raw) < budget:
                continue
            predictions[str(budget)] = {}
            for method in ("unchanged", "floor_ms", "nearest_ms"):
                x = raw[:budget].copy()
                if method == "floor_ms":
                    x[:, 0] = np.floor(x[:, 0])
                elif method == "nearest_ms":
                    x[:, 0] = np.rint(x[:, 0])
                result = predictor.predict(x)
                predictions[str(budget)][method] = {k: result[k] for k in ("status", "label", "alternatives")}
        rows.append(
            {"flow_id": observed["flow_id"], "reference": observed["reference"], "predictions": predictions}
        )
    write_json(
        args.output,
        {
            "artifact_id": predictor.identity,
            "evidence_sha256": sha256(source),
            "data_manifest_sha256": sha256(Path(args.data) / "manifest.json"),
            "data_read": "train only",
            "local_stats": feature_stats(local),
            "training_stats": feature_stats(training),
            "sensitivity": rows,
            "note": "Exploratory feature/score sensitivity only. Floor and nearest-millisecond rules are not validated exporter semantics and are not deployed. No per-flow labels, local accuracy or causal performance improvement is inferred.",
        },
    )


if __name__ == "__main__":
    main()
