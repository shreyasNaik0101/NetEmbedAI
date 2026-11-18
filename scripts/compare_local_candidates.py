"""Compare existing real artifacts on saved local development trials; never fit."""

import argparse
from pathlib import Path

import torch

from netembed.bundle import Predictor, sha256, write_json
from netembed.contract import BUDGETS, Flow
from netembed.netlog_reference import read_bounded
from netembed.service_reference import summarize


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--trial", nargs=3, action="append", required=True, metavar=("NAME", "EVIDENCE", "REFERENCE")
    )
    parser.add_argument("--bundle", nargs=2, action="append", required=True, metavar=("NAME", "PATH"))
    parser.add_argument("--output", required=True)
    parser.add_argument(
        "--allow-different-training-data",
        action="store_true",
        help="explicit transfer diagnostic; records separate manifests, not a matched loss comparison",
    )
    args = parser.parse_args()
    if Path(args.output).exists():
        raise FileExistsError("comparison exists; choose a new output path")
    if not 1 <= len(args.trial) <= 4 or not 1 <= len(args.bundle) <= 3:
        raise ValueError("bounded comparison requires at most four trials and three models")
    if len({x[0] for x in args.trial}) != len(args.trial) or len({x[0] for x in args.bundle}) != len(
        args.bundle
    ):
        raise ValueError("trial/model names must be unique")
    trials = {}
    for name, evidence_path, reference_path in args.trial:
        evidence, evidence_sha = read_bounded(evidence_path)
        reference, reference_sha = read_bounded(reference_path)
        if (
            evidence.get("fixture")
            or evidence.get("source") != "user_started_capture"
            or evidence["counters"]["running"]
        ):
            raise ValueError("only stopped user-started development captures are allowed")
        if (
            reference["fixture"]
            or reference["evidence_sha256"] != evidence_sha
            or reference["session_id"] != evidence["session_id"]
            or reference["artifact_id"] != evidence["artifact_id"]
        ):
            raise ValueError("reference does not bind this exact real session")
        originals = {row["flow_id"]: row for row in evidence["flows"]}
        if len(originals) != len(reference["flows"]) or set(originals) != {
            row["flow_id"] for row in reference["flows"]
        }:
            raise ValueError("reference inventory mismatch")
        for row in reference["flows"]:
            if any(row[key] != originals[row["flow_id"]][key] for key in ("packets", "predictions")):
                raise ValueError("original packets or predictions changed")
        trials[name] = {
            "session_id": evidence["session_id"],
            "adapter_version": evidence.get("adapter_version", "unversioned_pre_ns_v2"),
            "evidence_sha256": evidence_sha,
            "reference_sha256": reference_sha,
            "reference_counts": reference["reference_counts"],
            "counters": evidence["counters"],
            "evidence_evicted": evidence["evidence_evicted"],
            "rows": [row for row in reference["flows"] if row["reference"]["status"] == "mapped"],
        }
    torch.set_num_threads(2)
    models, manifests = {}, set()
    for name, path in args.bundle:
        predictor = Predictor(path)
        data_sha = predictor.meta["provenance"]["data_manifest_sha256"]
        if manifests and data_sha not in manifests and not args.allow_different_training_data:
            raise ValueError("candidates were not trained on the same data manifest")
        manifests.add(data_sha)
        per_trial = {}
        for trial_name, trial in trials.items():
            rows = []
            for row in trial["rows"]:
                raw = Flow(packets=row["packets"]).array()
                predictions = [
                    {k: v for k, v in predictor.predict(raw[:budget]).items() if k != "pipeline_ms"}
                    for budget in BUDGETS
                    if len(raw) >= budget
                ]
                rows.append(
                    {"flow_id": row["flow_id"], "reference": row["reference"], "predictions": predictions}
                )
            per_trial[trial_name] = {
                "mapped_flows": len(rows),
                "agreement_by_prefix": summarize(rows),
                "flows": rows,
            }
        models[name] = {
            "artifact_id": predictor.identity,
            "kind": predictor.meta["kind"],
            "seed": predictor.meta["provenance"].get("config", {}).get("seed"),
            "data_manifest_sha256": data_sha,
            "bundle_checksums_sha256": sha256(Path(path) / "checksums.json"),
            "policy": {k: v for k, v in predictor.meta["policy"].items() if k != "curve"},
            "trials": per_trial,
        }
        del predictor
    write_json(
        args.output,
        {
            "development_only": True,
            "data_manifest_sha256": next(iter(manifests)) if len(manifests) == 1 else None,
            "same_training_data": len(manifests) == 1,
            "trials": {
                name: {k: v for k, v in trial.items() if k != "rows"} for name, trial in trials.items()
            },
            "models": models,
            "note": "Identical saved prefix inputs within each trial. Separate training manifests are allowed only by explicit flag and then this is a transfer diagnostic, not a matched loss/augmentation comparison. Identities, seeds, manifests and saved policies are recorded. Original references, refusals and mismatches are preserved. No data fitting, threshold tuning, model selection or deployment occurs. Policies are each model's previously calibrated policies, so coverage differences do not isolate a training-loss effect. These few flows and correlated development sessions cannot establish held-out local accuracy. No final-test records or downloaded phone recordings are read.",
        },
    )


if __name__ == "__main__":
    main()
