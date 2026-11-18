"""Fixed development-only linear-probe protocol and input guards."""

import hashlib
import json
import re
from collections import Counter
from pathlib import Path

import numpy as np

from .browser_adaptation import load_role_trial
from .browser_collection import read_collection_plan
from .bundle import sha256
from .contract import BUDGETS

CONFIG_SHA = "b5b88cc07317357a2c1b211c91b775075fc7892b4291d09f6921e5dd4af3db01"


def read_config(path):
    raw = Path(path).read_bytes().replace(b"\r\n", b"\n")
    if hashlib.sha256(raw).hexdigest() != CONFIG_SHA:
        raise ValueError("linear-probe protocol differs from frozen declaration")
    return json.loads(raw)


def bound_json(binding):
    if sha256(binding["path"]) != binding["sha256"]:
        raise ValueError("bound evidence changed")
    return json.loads(Path(binding["path"]).read_text())


def protected_input(path, allowed_trials):
    path = str(path).replace("\\", "/").lower()
    trials = re.findall(r"(?:instagram|youtube)-(?:cal|dev|eval)-\d+", path)
    return (
        any(trial not in allowed_trials for trial in trials)
        or any(p in path.split("/") for p in ("test.jsonl", "calibration.jsonl", "final"))
        or "/final." in path
    )


def guard_for(cfg):
    allowed = set(cfg["train_trials"] + cfg["selection_trials"])

    def guard(event, args):
        if event == "open" and isinstance(args[0], (str, bytes)):
            path = args[0].decode() if isinstance(args[0], bytes) else args[0]
            if protected_input(path, allowed):
                raise ValueError("protected calibration/final/undeclared capture excluded")
        if event in ("socket.connect", "socket.getaddrinfo"):
            raise ValueError("linear-probe study is offline")

    return guard


def load_rows(root, role, labels, cfg):
    old = bound_json(cfg["role_config"])
    bound_json(cfg["parent_data_manifest"])
    if any(old[r + "_trials"] != cfg[r + "_trials"] for r in ("train", "selection")):
        raise ValueError("declared roles changed")
    root = Path(root)
    plan = read_collection_plan(root / old["reference_collection_plan_filename"])
    rows, proofs = [], {}
    for trial in cfg[role + "_trials"]:
        binding = cfg["trial_bindings"][trial]
        if (
            sha256(root / f"{trial}-collection-summary.json") != binding["summary_sha256"]
            or sha256(root / f"{trial}-development-rows.jsonl") != binding["rows_sha256"]
        ):
            raise ValueError("declared capture changed")
        records, proof = load_role_trial(root, trial, role, labels, old, plan)
        if proof["session_id"] != binding["session_id"]:
            raise ValueError("declared session changed")
        rows.extend(r for r in records if r["label"] in cfg["local_labels"])
        proofs[trial] = proof
    if dict(Counter(r["label"] for r in rows)) != cfg[f"local_{role}_counts"]:
        raise ValueError("declared local support changed")
    if len({r["id"] for r in rows}) != len(rows) or len({p["session_id"] for p in proofs.values()}) != len(
        proofs
    ):
        raise ValueError("duplicate local IDs or sessions")
    return rows, proofs


def prefix_training(flows, targets, flow_weights):
    """Match prior training budget convention, including short truncated prefixes."""
    return (
        [raw[:b] for b in BUDGETS for raw in flows],
        np.tile(targets, len(BUDGETS)),
        np.tile(flow_weights / len(BUDGETS), len(BUDGETS)),
    )


def development_gate(metrics, references, cfg):
    forests = [references[name] for name in ("previous_forest", "recent_forest")]
    gate = cfg["gate"]
    return {
        "local_f1_floor": metrics["local_macro_f1"] >= gate["local_f1_floor"],
        "gain_over_best_fixed_forest": metrics["local_macro_f1"]
        >= max(r["local_macro_f1"] for r in forests) + gate["gain_over_best_fixed_forest"],
        "per_service_recall_floor": all(
            v >= gate["per_service_recall_floor"] for v in metrics["local_recall"].values()
        ),
        "per_service_nonregression": all(
            value >= max(r["local_recall"][label] for r in forests)
            for label, value in metrics["local_recall"].items()
        ),
        "historical_control_only": metrics["public_clean_macro_f1"]
        >= references["b17"]["public_clean_macro_f1"] - gate["historical_control_loss_vs_b17"],
    }
