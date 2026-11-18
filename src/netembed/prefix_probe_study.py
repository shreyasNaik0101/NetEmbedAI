"""Declaration and scoring for the single prefix-specific-head experiment."""

import hashlib
import json
from pathlib import Path

import numpy as np
from sklearn.metrics import f1_score

from .contract import BUDGETS
from .linear_probe_study import bound_json, development_gate, read_config as parent_config

CONFIG_SHA = "77bcae2b5120293b413c16f8ec0683bf959837b3d0d05ab682d2de5d71cfe8de"
RECOVERY_SHA = "5a1a34698a8438d047e6543b8a72e093c9377a9aa67a9bcf4966d01fa9ebc889"


def read_config(path):
    raw = Path(path).read_bytes().replace(b"\r\n", b"\n")
    if hashlib.sha256(raw).hexdigest() not in (CONFIG_SHA, RECOVERY_SHA):
        raise ValueError("prefix study differs from frozen declaration")
    declaration = json.loads(raw)
    cfg = parent_config(declaration["parent_config"])
    if "numerical_recovery" in declaration:
        cfg["head"] = {**cfg["head"], "max_iter": declaration["numerical_recovery"]["max_iter"]}
    return declaration, cfg


def validate_recovery(declaration, cfg):
    if "numerical_recovery" not in declaration:
        return
    recovery = declaration["numerical_recovery"]
    original = bound_json(recovery["original_declaration"])
    failed = bound_json(recovery["failed_fit"])
    protocol = bound_json(recovery["failed_protocol"])
    if (
        sorted(p.name for p in Path(recovery["failed_directory"]).iterdir())
        != recovery["expected_failed_files"]
        or set(failed) != {"5"}
        or failed["5"]["converged"]
        or failed["5"]["iterations"] != [500]
        or protocol["declaration"] != original
        or {**protocol["inherited_config"], "head": cfg["head"]} != cfg
        or {**protocol["inherited_config"]["head"], "max_iter": 2000} != cfg["head"]
    ):
        raise ValueError("numerical recovery requires the unchanged unscored stopped attempt")


def summarize(local, control, labels):
    budgets, recalls = {}, {}
    for b in BUDGETS:
        part = [r for r in local if r["observed_packets"] == b]
        public = [r for r in control if r["requested_cap"] == b]
        if not part or not public:
            raise ValueError("missing evaluation checkpoint")
        truth, pred = [r["reference"] for r in part], [r["top1"] for r in part]
        classes = {}
        for label in sorted(set(truth)):
            hits = [r["top1"] == label for r in part if r["reference"] == label]
            recall = float(np.mean(hits))
            recalls.setdefault(label, []).append(recall)
            classes[label] = {"n": len(hits), "recall": recall}
        budgets[str(b)] = {
            "n": len(part),
            "accuracy": float(np.mean([a == c for a, c in zip(truth, pred)])),
            "observed_class_macro_f1": float(
                f1_score(truth, pred, labels=sorted(set(truth)), average="macro", zero_division=0)
            ),
            "classes": classes,
            "public_clean_macro_f1": float(
                f1_score(
                    [r["reference"] for r in public],
                    [r["top1"] for r in public],
                    labels=labels,
                    average="macro",
                    zero_division=0,
                )
            ),
        }
    return {
        "budgets": budgets,
        "local_macro_f1": float(np.mean([v["observed_class_macro_f1"] for v in budgets.values()])),
        "local_recall": {label: float(np.mean(values)) for label, values in recalls.items()},
        "public_clean_macro_f1": float(np.mean([v["public_clean_macro_f1"] for v in budgets.values()])),
    }


def gates(metrics, references, shared, cfg, declaration):
    return {
        **development_gate(metrics, references, cfg),
        "shared_f1_nonregression": metrics["local_macro_f1"] >= shared["local_macro_f1"],
        "shared_recall_nonregression": all(
            value >= shared["local_recall"][label] for label, value in metrics["local_recall"].items()
        ),
        "five_packet_gain": metrics["budgets"]["5"]["observed_class_macro_f1"]
        >= shared["budgets"]["5"]["observed_class_macro_f1"] + declaration["early_f1_gain_minimum"],
    }
