"""One historical public-calibration policy fit; local outcomes stay sealed."""

from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import subprocess

import numpy as np

from .browser_calibration import write_policy_bundle
from .bundle import Predictor, sha256, write_json
from .data import read_split
from .local_policy import stats

CONFIG_SHA = "c83ac2c52b58406994b9a79762545d91cfb8d06969767a24fda972a3cc94a5cb"


def read_config(path):
    raw = Path(path).read_bytes().replace(b"\r\n", b"\n")
    if hashlib.sha256(raw).hexdigest() != CONFIG_SHA:
        raise ValueError("public-only policy declaration changed")
    return json.loads(raw)


def fit_guard(event, args, output="experiments/ipv6-public-policy-v1"):
    if event in ("socket.connect", "socket.getaddrinfo"):
        raise ValueError("public policy fitting is offline")
    if event == "open" and isinstance(args[0], (str, bytes)):
        path = Path(os.fsdecode(args[0])).resolve()
        pilot = Path("experiments/ipv6-realdata-pilot-v1").resolve()
        allowed_bundle = pilot / "plus-real-ipv6" / "bundle"
        experiments = Path("experiments").resolve()
        if (
            path.is_relative_to(Path("artifacts/local").resolve())
            or path.name in ("train.jsonl", "selection.jsonl", "test.jsonl")
            or (path.is_relative_to(pilot) and not path.is_relative_to(allowed_bundle))
            or (
                path.is_relative_to(experiments)
                and not path.is_relative_to(allowed_bundle)
                and not path.is_relative_to(Path(output).resolve())
            )
        ):
            raise ValueError("local outcomes and non-calibration splits excluded from policy fitting")


def select_policy(records, labels, cfg):
    if not records or len({(r["id"], r["budget"]) for r in records}) != len(records):
        raise ValueError("empty or duplicate calibration cases")
    for r in records:
        p = np.asarray(r["probabilities"])
        if (
            p.shape != (len(labels),)
            or not np.isfinite(p).all()
            or (p < 0).any()
            or not np.isclose(p.sum(), 1)
            or r["reference"] not in labels
            or r["top1"] != labels[int(p.argmax())]
            or r["budget"] not in cfg["budgets"]
        ):
            raise ValueError("invalid calibration probabilities/labels/budget")
    rules = cfg["rules"]

    def valid(s, minimum=1, coverage=False):
        return (
            s["accepted"] >= minimum
            and s["error"] is not None
            and s["error"] <= rules["maximum_empirical_error"]
            and (not coverage or s["coverage"] >= rules["minimum_coverage"])
        )

    primary = [r for r in records if r["budget"] == cfg["primary_budget"]]
    curve = []
    for step in range(101):
        threshold = step / 100
        pooled, early = stats(records, threshold), stats(primary, threshold)
        classes = {
            label: stats([r for r in records if r["reference"] == label], threshold) for label in labels
        }
        early_classes = {
            label: stats([r for r in primary if r["reference"] == label], threshold) for label in labels
        }
        eligible = (
            valid(pooled, coverage=True)
            and valid(early, coverage=True)
            and all(valid(s) for s in classes.values())
            and all(valid(s, rules["minimum_primary_accepted_per_class"]) for s in early_classes.values())
        )
        curve.append(
            {
                "threshold": threshold,
                "pooled": pooled,
                "primary": early,
                "classes": classes,
                "primary_classes": early_classes,
                "eligible": eligible,
            }
        )
    selected = next((r for r in curve if r["eligible"]), None)
    policy = {
        "version": "cesnet-forest-refusal-v1",
        "fitted": selected is not None,
        "threshold": selected["threshold"] if selected else 1.0,
        "min_packets": cfg["min_packets"],
        "temperature": cfg["temperature"],
        "tie_break": "label_order",
        "validation_scope": "cesnet_calibration_only",
        "locally_checked_labels": [],
        "note": "Refusal threshold fitted only on historical CESNET calibration, not local traffic. Scores are not calibrated correctness probabilities; no unknown-service guarantee.",
    }
    return policy, selected, curve


def run(config_path, output):
    cfg = read_config(config_path)
    root = Path(output)
    if root.exists():
        raise FileExistsError("preserve existing public policy run")
    model = Predictor(cfg["candidate_bundle"])
    if (
        model.identity != cfg["candidate_id"]
        or sha256(Path(cfg["candidate_bundle"]) / "forest.json") != cfg["candidate_weight_sha256"]
        or model.meta["policy"]["fitted"]
        or model.meta["provenance"].get("fixture", True)
    ):
        raise ValueError("frozen real uncalibrated candidate changed")
    if sha256(Path(cfg["public_data"]) / "manifest.json") != cfg["public_manifest_sha256"]:
        raise ValueError("public manifest changed")
    flows, targets, ids, manifest = read_split(cfg["public_data"], "calibration")
    if manifest["labels"] != model.labels:
        raise ValueError("public label order differs")
    counts, inputs, records, selected_ids = Counter(), [], [], []
    for flow, target, ident in zip(flows, targets, ids):
        label = model.labels[int(target)]
        if len(flow) < cfg["min_packets"] or counts[label] >= cfg["flows_per_class"]:
            continue
        counts[label] += 1
        selected_ids.append(ident)
        for budget in cfg["budgets"]:
            if len(flow) >= budget:
                inputs.append(flow[:budget])
                records.append(
                    {"id": ident, "reference": label, "budget": budget, "observed_packets": budget}
                )
    if any(counts[label] != cfg["flows_per_class"] for label in model.labels):
        raise ValueError("public calibration lacks declared class support")
    probabilities = np.concatenate(
        [model.probabilities(inputs[i : i + 128]) for i in range(0, len(inputs), 128)]
    )
    for row, p in zip(records, probabilities):
        row.update(probabilities=p.tolist(), top1=model.labels[int(p.argmax())])
    policy, selected, curve = select_policy(records, model.labels, cfg)
    root.mkdir(parents=True, exist_ok=False)
    write_json(root / "predictions.json", records)
    write_json(root / "curve.json", curve)
    proof = {
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "source_commit": subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
        "candidate_id": model.identity,
        "config": cfg,
        "config_sha256": CONFIG_SHA,
        "source_sha256": sha256(__file__),
        "inference_and_export_sources": {
            name: sha256(Path(__file__).with_name(name))
            for name in ("bundle.py", "contract.py", "browser_calibration.py")
        },
        "calibration_source_sha256": manifest["files"]["calibration.jsonl"],
        "selected_flow_ids": selected_ids,
        "class_counts": dict(counts),
        "prediction_sha256": sha256(root / "predictions.json"),
        "curve_sha256": sha256(root / "curve.json"),
        "local_data_read": False,
        "weights_refitted": False,
        "default_promoted": False,
        "limits": cfg["limits"],
    }
    bundle = None
    if policy["fitted"]:
        write_policy_bundle(
            cfg["candidate_bundle"], root / "bundle", policy, proof, provenance_key="public_calibration"
        )
        bundle = sha256(root / "bundle/metadata.json")
        checked = Predictor(root / "bundle")
        if not np.array_equal(checked.probabilities(inputs[:8]), probabilities[:8]):
            raise ValueError("policy export changed probability vectors")
    result = {
        **proof,
        "policy": policy,
        "selected": selected,
        "policy_artifact_id": bundle,
        "prefix_cases": len(records),
        "status": "public_policy_fitted" if selected else "public_policy_infeasible",
    }
    write_json(root / "decision.json", result)
    return result
