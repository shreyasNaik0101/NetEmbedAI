"""Audit comparable development runs; never reads the final-test partition."""

import argparse
import hashlib
import json
import statistics
from pathlib import Path

BUDGETS = (5, 10, 20, 30)
STRESSES = ("clean", "timing", "padding", "observation_loss")
SEEDS = (17, 42, 123)
CANDIDATES = {
    "forest": ("forest", "ce", False),
    "A": ("tcn", "ce", False),
    "B": ("tcn", "ce", True),
    "C": ("tcn", "supcon", False),
    "D": ("tcn", "supcon", True),
}


def load_run(path):
    result = json.loads((path / "result.json").read_text())
    report = json.loads((path / "selection" / "report.json").read_text())
    artifact = hashlib.sha256((path / "bundle" / "metadata.json").read_bytes()).hexdigest()
    if report["split"] != "selection" or report["artifact_id"] != artifact:
        raise ValueError(f"selection/artifact mismatch: {path}")
    if report["data_manifest_sha256"] != result["data_manifest_sha256"]:
        raise ValueError(f"data manifest mismatch: {path}")
    cfg = result["config"]
    key = (cfg["kind"], cfg["loss"], cfg["augmentation"])
    candidate = next((name for name, value in CANDIDATES.items() if value == key), None)
    if candidate is None or cfg["seed"] not in SEEDS or result["fixture"]:
        raise ValueError(f"unsupported or fixture run: {path}")
    cases = report["protocols"]
    values = [cases[f"all_flows/{budget}/{stress}"]["macro_f1"] for budget in BUDGETS for stress in STRESSES]
    clean = [cases[f"all_flows/{budget}/clean"]["macro_f1"] for budget in BUDGETS]
    score = statistics.mean(values)
    if candidate != "forest" and abs(score - result["selection_score"]) > 1e-9:
        raise ValueError(f"training/evaluation selection score mismatch: {path}")
    return {
        "candidate": candidate,
        "seed": cfg["seed"],
        "run_id": result["run_id"],
        "artifact_id": artifact,
        "manifest": result["data_manifest_sha256"],
        "score": score,
        "clean": statistics.mean(clean),
        "config": cfg,
        "source_commit": result["source_commit"],
    }


def compare(root):
    runs = [
        load_run(path.parent)
        for path in sorted(Path(root).glob("*/result.json"))
        if (path.parent / "selection" / "report.json").exists()
    ]
    manifests = {run["manifest"] for run in runs}
    if len(manifests) > 1:
        raise ValueError("runs use different prepared data manifests")
    by_key = {}
    for run in runs:
        key = (run["candidate"], run["seed"])
        if key in by_key:
            raise ValueError(f"duplicate completed candidate/seed: {key}")
        by_key[key] = run
    neural = [r for r in runs if r["candidate"] != "forest"]
    for field in (
        "epochs",
        "batch_size",
        "learning_rate",
        "threads",
        "architecture",
        "patience",
        "supcon_weight",
    ):
        values = {json.dumps(r["config"][field], sort_keys=True) for r in neural}
        if len(values) > 1:
            raise ValueError(f"neural run configuration differs: {field}")
    floors = {r["config"]["clean_floor"] for r in neural if r["candidate"] != "A"}
    if len(floors) > 1 or (floors and None in floors):
        raise ValueError("comparative candidates must share one declared clean floor")
    augmentation_policies = {
        r["config"].get("augmentation_policy") for r in neural if r["candidate"] in ("B", "D")
    }
    if len(augmentation_policies) > 1 or (augmentation_policies and None in augmentation_policies):
        raise ValueError("B and D must use the same declared augmentation policy")
    summary = {}
    for name in CANDIDATES:
        subset = [by_key[(name, seed)] for seed in SEEDS if (name, seed) in by_key]
        summary[name] = {
            "seeds": {
                str(r["seed"]): {
                    k: r[k] for k in ("run_id", "artifact_id", "score", "clean", "source_commit")
                }
                for r in subset
            },
            "mean_score": statistics.mean(r["score"] for r in subset) if subset else None,
            "score_range": [min(r["score"] for r in subset), max(r["score"] for r in subset)]
            if subset
            else None,
        }
    paired = {}
    paired_clean = {}
    for left, right in (("B", "A"), ("D", "C"), ("D", "B")):
        paired[f"{left}-{right}"] = {
            str(seed): by_key[(left, seed)]["score"] - by_key[(right, seed)]["score"]
            for seed in SEEDS
            if (left, seed) in by_key and (right, seed) in by_key
        }
        paired_clean[f"{left}-{right}"] = {
            str(seed): by_key[(left, seed)]["clean"] - by_key[(right, seed)]["clean"]
            for seed in SEEDS
            if (left, seed) in by_key and (right, seed) in by_key
        }
    gains = list(paired["D-B"].values())
    clean_changes = list(paired_clean["D-B"].values())
    supcon_rule_met = (
        all(gain > 0 for gain in gains)
        and statistics.mean(gains) >= 0.01
        and all(change >= -0.01 for change in clean_changes)
        if len(gains) == len(SEEDS)
        else None
    )
    missing = [f"{name}/{seed}" for name in CANDIDATES for seed in SEEDS if (name, seed) not in by_key]
    return {
        "protocol": "all_flows/5,10,20,30 x clean,timing,padding,observation_loss",
        "data_manifest_sha256": next(iter(manifests)) if manifests else None,
        "clean_floor": next(iter(floors)) if floors else None,
        "candidates": summary,
        "paired_score_differences": paired,
        "paired_clean_differences": paired_clean,
        "supcon_rule_met": supcon_rule_met,
        "missing": missing,
        "complete": not missing,
        "note": "Development evidence only; incomplete comparisons do not establish a winner.",
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(compare(args.root), indent=2) + "\n")
