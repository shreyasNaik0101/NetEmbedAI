"""Fixed legacy development cohort for isolated diagnostics, never final data."""

import json
import re
from collections import Counter
from pathlib import Path

import numpy as np
from sklearn.metrics import confusion_matrix, f1_score

from .browser_adaptation import check_roles, load_role_trial
from .bundle import Predictor, sha256
from .contract import BUDGETS, Flow
from .data import read_split


def protected_input(path):
    path = str(path).replace("\\", "/").lower()
    trial = re.search(r"(?:instagram|youtube)-(cal|dev|eval)-(\d\d)(?:[^0-9]|$)", path)
    return bool(
        (
            trial
            and (
                trial[1] == "eval"
                or (trial[1] == "cal" and int(trial[2]) != 1)
                or (trial[1] == "dev" and int(trial[2]) > 2)
            )
        )
        or "/calibration-02/" in path
        or "/final/" in path
        or "/final." in path
        or path.endswith("/test.jsonl")
    )


def audit_guard(event, args):
    if event == "open" and isinstance(args[0], (str, bytes)) and protected_input(args[0]):
        raise ValueError("protected calibration, prospective collection and final input excluded")


def cohorts(data, collection, reference_root):
    cfg = json.loads(Path("configs/browser-forward-mass25.json").read_text())
    root = Path(collection)
    plan_path = root / cfg["split_plan_filename"]
    plan = json.loads(plan_path.read_text())
    run = Path(reference_root) / "forward-mass25-seed17"
    models = {"tcn": Predictor(run / "tcn-epoch-5/bundle"), "forest": Predictor(run / "forest/bundle")}
    labels = models["forest"].labels
    rows, proofs = {}, {}
    for role in ("train", "selection"):
        rows[role] = []
        for trial in cfg[role + "_trials"]:
            values, proof = load_role_trial(root, trial, role, labels, cfg, plan)
            rows[role].extend(values)
            proofs[trial] = proof
    check_roles(rows["train"], rows["selection"])
    if max(proofs[k]["first_packet_range_unix_ms"][1] for k in cfg["train_trials"]) >= min(
        proofs[k]["first_packet_range_unix_ms"][0] for k in cfg["selection_trials"]
    ):
        raise ValueError("local chronology overlaps")
    if any(
        model.labels != labels or proofs != model.meta["provenance"]["browser_evidence"]
        for model in models.values()
    ):
        raise ValueError("paired local cohort differs")
    public, py, public_ids, manifest = read_split(data, "train")
    control, cy, ids, _ = read_split(data, "selection")
    manifest_sha = sha256(Path(data) / "manifest.json")
    if manifest["labels"] != labels or any(
        model.meta["provenance"]["public_data_manifest_sha256"] != manifest_sha for model in models.values()
    ):
        raise ValueError("public training identity differs")
    count, chosen = Counter(), []
    for i, label in enumerate(cy):
        if count[int(label)] < 50:
            count[int(label)] += 1
            chosen.append(i)
    if any(
        [ids[i] for i in chosen] != model.meta["provenance"]["public_selection_ids"]
        for model in models.values()
    ):
        raise ValueError("historical control cohort differs")
    return {
        "labels": labels,
        "models": models,
        "train": public + [Flow(packets=r["packets"]).array() for r in rows["train"]],
        "train_y": np.concatenate([py, [labels.index(r["label"]) for r in rows["train"]]]),
        "train_ids": public_ids + [r["id"] for r in rows["train"]],
        "local": [Flow(packets=r["packets"]).array() for r in rows["selection"]],
        "local_y": np.array([labels.index(r["label"]) for r in rows["selection"]]),
        "local_ids": [r["id"] for r in rows["selection"]],
        "control": [control[i] for i in chosen],
        "control_y": cy[chosen],
        "control_ids": [ids[i] for i in chosen],
        "provenance": {
            "browser_evidence": proofs,
            "public_manifest_sha256": manifest_sha,
            "public_control_ids": [ids[i] for i in chosen],
            "browser_plan_sha256": sha256(plan_path),
            "paired_model_ids": {k: v.identity for k, v in models.items()},
            "local_train_connections": len(rows["train"]),
            "local_selection_connections": len(rows["selection"]),
            "selection_groups": sorted({r["group_id"] for r in rows["selection"]}),
        },
    }


def summarize(records, labels):
    metrics = {}
    for budget in BUDGETS:
        part = [r for r in records if r["requested_cap"] == budget]
        valid = [r for r in part if r["prediction"]["label"] is not None]
        observed = sorted({labels.index(r["reference"]) for r in part})
        truth = [labels.index(r["reference"]) for r in valid]
        predicted = [labels.index(r["prediction"]["label"]) for r in valid]
        metrics[str(budget)] = {
            "available": len(part),
            "ranked": len(valid),
            "correct": sum(a == b for a, b in zip(truth, predicted)),
            "macro_f1_on_ranked": float(
                f1_score(truth, predicted, labels=observed, average="macro", zero_division=0)
            )
            if valid
            else None,
            "recall_on_ranked": {
                labels[i]: float(np.mean(np.array(predicted)[np.array(truth) == i] == i))
                if i in truth
                else None
                for i in observed
            },
            "confusion_on_ranked": confusion_matrix(
                truth, predicted, labels=list(range(len(labels)))
            ).tolist(),
        }
    complete = all(m["ranked"] == m["available"] and m["ranked"] for m in metrics.values())
    return {
        "budgets": metrics,
        "correct": sum(m["correct"] for m in metrics.values()),
        "available": len(records),
        "ranked": sum(m["ranked"] for m in metrics.values()),
        "mean_budget_macro_f1": float(np.mean([m["macro_f1_on_ranked"] for m in metrics.values()]))
        if complete
        else None,
    }
