"""Fixed, exploratory timing/model comparisons on saved development references."""

import argparse
from pathlib import Path

import numpy as np
import torch

from netembed.bundle import Predictor, sha256, write_json
from netembed.contract import BUDGETS, Flow, validate_array
from netembed.data import read_split
from netembed.netlog_reference import finite, read_bounded
from netembed.service_reference import summarize


def timing_variants(raw, first_packet_unix_ms):
    raw = validate_array(raw)
    first = finite(first_packet_unix_ms)
    variants = {name: raw.copy() for name in ("unchanged", "floor_gap", "nearest_gap", "floor_timestamp")}
    variants["floor_gap"][:, 0] = np.floor(raw[:, 0])
    variants["nearest_gap"][:, 0] = np.rint(raw[:, 0])
    times = np.floor(first + np.cumsum(raw[:, 0], dtype=np.float64))
    variants["floor_timestamp"][1:, 0] = np.diff(times)
    return variants


def cohort_stats(flows):
    if not flows:
        return {"flows": 0}
    packets = np.concatenate(flows)
    return {
        "flows": len(flows),
        "packets": len(packets),
        "percentiles": [0, 25, 50, 75, 90, 100],
        "iat_ms": np.percentile(packets[:, 0], [0, 25, 50, 75, 90, 100]).tolist(),
        "payload_bytes": np.percentile(packets[:, 2], [0, 25, 50, 75, 90, 100]).tolist(),
        "forward_packet_fraction": float(np.mean(packets[:, 1] == 1)),
        "zero_iat_fraction": float(np.mean(packets[:, 0] == 0)),
        "noninteger_iat_fraction": float(np.mean(packets[:, 0] != np.floor(packets[:, 0]))),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("evidence", "reference", "data", "output"):
        parser.add_argument("--" + name, required=True)
    parser.add_argument("--bundle", nargs=2, action="append", required=True, metavar=("NAME", "PATH"))
    args = parser.parse_args()
    if Path(args.output).exists():
        raise FileExistsError("diagnostic exists; choose a new output path")
    if not 1 <= len(args.bundle) <= 3 or len({name for name, _ in args.bundle}) != len(args.bundle):
        raise ValueError("requires 1..3 uniquely named bundles for bounded comparison")
    evidence, evidence_sha = read_bounded(args.evidence)
    reference, reference_sha = read_bounded(args.reference)
    if reference["evidence_sha256"] != evidence_sha:
        raise ValueError("reference is bound to different evidence")
    if evidence["fixture"] or reference["fixture"] or evidence["counters"]["running"]:
        raise ValueError("requires real, stopped user-started capture evidence")
    originals = {row["flow_id"]: row for row in evidence["flows"]}
    if (
        len(originals) != len(reference["flows"])
        or len(originals) != len(evidence["flows"])
        or set(originals) != {row["flow_id"] for row in reference["flows"]}
        or reference["artifact_id"] != evidence["artifact_id"]
    ):
        raise ValueError("flow inventory mismatch")
    selected = []
    for row in reference["flows"]:
        original = originals[row["flow_id"]]
        if any(row[key] != original[key] for key in ("packets", "predictions")):
            raise ValueError("reference changed original packets or predictions")
        if row["reference"]["status"] == "mapped":
            selected.append((row, original))
    if not selected:
        raise ValueError("no defensible mapped references; do not infer labels from trial context")
    torch.set_num_threads(2)
    training, labels, _, manifest = read_split(args.data, "train")
    manifest_sha = sha256(Path(args.data) / "manifest.json")
    results = {}
    for name, path in args.bundle:
        metadata, _ = read_bounded(Path(path) / "metadata.json")
        if metadata["kind"] != "tcn":
            raise ValueError("this memory-bounded diagnostic accepts compact TCNs only")
        predictor = Predictor(path)
        if predictor.meta["provenance"]["data_manifest_sha256"] != manifest_sha:
            raise ValueError("model and training-data manifest differ")
        by_variant = {variant: [] for variant in ("unchanged", "floor_gap", "nearest_gap", "floor_timestamp")}
        for row, original in selected:
            raw = Flow(packets=original["packets"]).array()
            first = original["connection_match"]["first_packet_unix_ms"]
            for variant, altered in timing_variants(raw, first).items():
                predictions = []
                for budget in BUDGETS:
                    if len(altered) < budget:
                        continue
                    result = predictor.predict(altered[:budget])
                    predictions.append({k: v for k, v in result.items() if k != "pipeline_ms"})
                by_variant[variant].append(
                    {"flow_id": row["flow_id"], "reference": row["reference"], "predictions": predictions}
                )
        baseline = [p for row in by_variant["unchanged"] for p in row["predictions"]]
        results[name] = {
            "artifact_id": predictor.identity,
            "bundle_checksums_sha256": sha256(Path(path) / "checksums.json"),
            "policy": predictor.meta["policy"],
            "variants": {
                variant: {
                    "agreement_by_prefix": summarize(rows),
                    "changed_top1_from_unchanged": sum(
                        p["alternatives"][0]["label"] != b["alternatives"][0]["label"]
                        for p, b in zip([p for row in rows for p in row["predictions"]], baseline)
                    ),
                    "changed_decisions_from_unchanged": sum(
                        p["label"] != b["label"]
                        for p, b in zip([p for row in rows for p in row["predictions"]], baseline)
                    ),
                    "flows": rows,
                }
                for variant, rows in by_variant.items()
            },
        }
        del predictor
    stats = {}
    for label in sorted({row["reference"]["label"] for row, _ in selected}):
        local = [
            Flow(packets=row["packets"]).array() for row, _ in selected if row["reference"]["label"] == label
        ]
        same_class = [x for x, y in zip(training, labels) if manifest["labels"][y] == label]
        stats[label] = {
            str(budget): {
                "local": cohort_stats([x[:budget] for x in local if len(x) >= budget]),
                "training": cohort_stats([x[:budget] for x in same_class if len(x) >= budget]),
            }
            for budget in BUDGETS
        }
    write_json(
        args.output,
        {
            "session_id": evidence["session_id"],
            "evidence_sha256": evidence_sha,
            "reference_sha256": reference_sha,
            "data_manifest_sha256": manifest_sha,
            "data_read": "train only; selection/calibration/final-test records are not opened",
            "reference_inventory": reference["reference_counts"],
            "mapped_development_flows": len(selected),
            "models": results,
            "same_service_prefix_feature_stats": stats,
            "note": "Exploratory development sensitivity, not local final evaluation or causal evidence. Fixed hypotheses are unchanged gaps, flooring each gap, nearest-integer gaps, and flooring absolute timestamps before differencing. Absolute timestamps are reconstructed from saved metadata; exact historical exporter quantization remains unverified. Original predictions, model weights, normalizers, labels and decision policies are unchanged. No candidate is selected or deployed from these few flows. Origin labels are independent references, never predictor inputs. No capture or training is started.",
        },
    )


if __name__ == "__main__":
    main()
