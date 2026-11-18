"""One fixed forest feature-map experiment; never reads fresh calibration/final."""

import argparse
import json
import subprocess
import sys
import time
from collections import Counter
from pathlib import Path

import numpy as np
import torch
from sklearn.ensemble import RandomForestClassifier
from netembed.browser_adaptation import UNCOMMITTED, check_roles, development, forest_weights, load_role_trial
from netembed.bundle import Predictor, export_bundle, sha256, write_json
from netembed.contract import BUDGETS, Flow, forest_features
from netembed.data import read_split


def guard(event, args):
    if event == "open" and isinstance(args[0], (str, bytes)):
        name = str(args[0]).replace("\\", "/").lower()
        if (
            "-cal-02" in name
            or "/calibration-02/" in name
            or "/final/" in name
            or "/final." in name
            or name.endswith("/test.jsonl")
        ):
            raise AssertionError("fresh calibration and final inputs are excluded")


parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--output", required=True)
parser.add_argument("--config", default="configs/browser-ordered-forest-study.json")
parser.add_argument("--collection", default="artifacts/local/browser-development")
parser.add_argument("--data", default="data/processed/v2")
parser.add_argument("--reference-root", default="experiments/browser-adaptation")
args = parser.parse_args()
sys.addaudithook(guard)
study_path = Path(args.config)
study = json.loads(study_path.read_text())
cfg = json.loads(Path(study["reference_config"]).read_text())
assert study["train_trials"] == cfg["train_trials"] and study["selection_trials"] == cfg["selection_trials"]
assert study["forest"] == cfg["forest"] and study["local_fraction"] == cfg["local_fraction"]
assert study["seed_order"] == [17, 42, 123] and study["stop_after_seed17_if_ineligible"]
out = Path(args.output)
assert not out.exists()
out.mkdir()
collection = Path(args.collection)
plan = json.loads((collection / cfg["split_plan_filename"]).read_text())
original_root = Path(args.reference_root) / "forward-mass25-seed17"
reference = Predictor(original_root / "forest/bundle")
torch.set_num_threads(study["threads"])
rows = {}
proofs = {}
for role in ("train", "selection"):
    rows[role] = []
    for trial in study[role + "_trials"]:
        values, proof = load_role_trial(collection, trial, role, reference.labels, cfg, plan)
        rows[role].extend(values)
        proofs[trial] = proof
check_roles(rows["train"], rows["selection"])
assert proofs == reference.meta["provenance"]["browser_evidence"]
assert max(proofs[k]["first_packet_range_unix_ms"][1] for k in cfg["train_trials"]) < min(
    proofs[k]["first_packet_range_unix_ms"][0] for k in cfg["selection_trials"]
)
public, py, _, manifest = read_split(args.data, "train")
validation, vy, ids, _ = read_split(args.data, "selection")
assert (
    sha256(Path(args.data) / "manifest.json") == reference.meta["provenance"]["public_data_manifest_sha256"]
)
assert manifest["labels"] == reference.labels
counts = Counter()
selected = []
for i, label in enumerate(vy):
    if counts[int(label)] < cfg["public_selection_per_class"]:
        selected.append(i)
        counts[int(label)] += 1
assert [ids[i] for i in selected] == reference.meta["provenance"]["public_selection_ids"]
validation, vy = [validation[i] for i in selected], vy[selected]
local = {role: [Flow(packets=row["packets"]).array() for row in values] for role, values in rows.items()}
ly = {
    role: np.array([reference.labels.index(row["label"]) for row in values]) for role, values in rows.items()
}
assert len(local["train"]) == 17 and len(local["selection"]) == 14
(out / "data-manifest.json").write_bytes((original_root / "data-manifest.json").read_bytes())
write_json(
    out / "protocol.json",
    {
        "study": study,
        "study_sha256": sha256(study_path),
        "input_proofs": proofs,
        "source_commit": subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
        "source_sha256": {
            name: sha256(name) for name in (__file__, "src/netembed/contract.py", "src/netembed/bundle.py")
        },
        "training_flows": len(public) + len(local["train"]),
        "local_train": dict(Counter(r["label"] for r in rows["train"])),
        "local_selection": dict(Counter(r["label"] for r in rows["selection"])),
    },
)
started = time.perf_counter()
features = np.asarray(
    [
        forest_features(x[:b], reference.normalizer, study["feature_map"])
        for x in public + local["train"]
        for b in BUDGETS
    ],
    dtype=np.float32,
)
targets = np.repeat(np.concatenate([py, ly["train"]]), len(BUDGETS))
weights = forest_weights(
    len(public) * len(BUDGETS), np.repeat(ly["train"], len(BUDGETS)), study["local_fraction"]
)
print(
    json.dumps(
        {"stage": "features_ready", "shape": features.shape, "elapsed_s": time.perf_counter() - started}
    ),
    flush=True,
)
results = []
for seed in study["seed_order"]:
    seed_root = out / f"seed-{seed}"
    old_root = Path(args.reference_root) / f"forward-mass25-seed{seed}"
    baseline = json.loads((old_root / "forest/development.json").read_text())
    forest = RandomForestClassifier(**study["forest"], random_state=seed, n_jobs=study["threads"])
    forest.fit(features, targets, sample_weight=weights)
    provenance = {
        **reference.meta["provenance"],
        "candidate": "forest-ordered-prefix",
        "config": study,
        "source_commit": json.loads((out / "protocol.json").read_text())["source_commit"],
        "seeds": {"forest": seed},
        "data_manifest_sha256": sha256(out / "data-manifest.json"),
        "ordered_study_protocol_sha256": sha256(out / "protocol.json"),
        "source_sha256": json.loads((out / "protocol.json").read_text())["source_sha256"],
        "note": "Experimental same-data feature-map change; old development selection already used. New calibration/final inputs excluded by Python open audit guard. No deployment, confidence fitting or future accuracy claim.",
    }
    bundle = export_bundle(
        seed_root / "bundle",
        forest,
        reference.normalizer,
        reference.labels,
        provenance,
        {"feature_map": study["feature_map"]},
        UNCOMMITTED,
    )
    predictor = Predictor(bundle)
    queries = [x[:b] for x in local["selection"] for b in BUDGETS if len(x) >= b]
    a = predictor.probabilities(queries)
    b = forest.predict_proba(
        [forest_features(x, reference.normalizer, study["feature_map"]) for x in queries]
    )
    delta = float(np.max(np.abs(a - b)))
    assert delta <= 1e-12
    metric, predictions = development(
        predictor, validation, vy, local["selection"], ly["selection"], rows["selection"]
    )
    eligible = (
        metric["local_macro_f1"]
        >= baseline["local_macro_f1"] + study["minimum_local_f1_gain_over_paired_summary_forest"]
        and metric["public_clean_macro_f1"]
        >= baseline["public_clean_macro_f1"]
        - study["maximum_historical_clean_loss_over_paired_summary_forest"]
        and all(value >= baseline["local_recall"][label] for label, value in metric["local_recall"].items())
    )
    result = {
        "seed": seed,
        "artifact_id": predictor.identity,
        "development": metric,
        "paired_summary_development": baseline,
        "passes_preregistered_development_gates": eligible,
        "sklearn_export_max_difference": delta,
        "total_elapsed_s": time.perf_counter() - started,
        "policy_fitted": False,
        "default_promoted": False,
    }
    write_json(seed_root / "development.json", result)
    write_json(seed_root / "predictions.json", predictions)
    results.append(result)
    print(json.dumps(result), flush=True)
    if seed == 17 and not eligible:
        break
write_json(
    out / "result.json",
    {
        "results": results,
        "study_sha256": sha256(study_path),
        "status": "development gates passed; requires a new independent validation cycle"
        if len(results) == 3 and all(r["passes_preregistered_development_gates"] for r in results)
        else "stopped; no validated replacement",
        "no_new_calibration_or_final_reads": True,
        "new_training_family": False,
        "default_promoted": False,
        "limits": "Post-failure development only, not independent accuracy. Same raw packet channels/budgets, forest params, weighting, splits and training-only normalizer. Expanding features also changes sqrt feature sampling; no isolated causal claim for order alone. No further sweep or capture requested.",
    },
)
