"""One fixed training-only packet-rule comparison. No capture or deployment."""

import argparse
import json
import platform
import re
import subprocess
import sys
import time
from collections import Counter
from pathlib import Path

import numpy as np
import sklearn
import torch
from sklearn.metrics import accuracy_score, confusion_matrix, f1_score

from netembed.browser_adaptation import check_roles, forest_weights, load_role_trial
from netembed.bundle import Predictor, sha256, write_json
from netembed.contract import BUDGETS, Flow
from netembed.data import read_split
from netembed.packet_rules import FLOORS, NAMES, VERSION, PacketRules


def protected_input(path):
    path = str(path).replace("\\", "/").lower()
    trial = re.search(r"(?:instagram|youtube)-(cal|dev|eval)-(\d\d)(?:[^0-9]|$)", path)
    protected_trial = trial and (
        trial[1] == "eval"
        or (trial[1] == "cal" and int(trial[2]) != 1)
        or (trial[1] == "dev" and int(trial[2]) > 2)
    )
    return bool(
        protected_trial
        or "/calibration-02/" in path
        or "/final/" in path
        or "/final." in path
        or path.endswith("/test.jsonl")
    )


def audit_guard(event, args):
    if event == "open" and isinstance(args[0], (str, bytes)) and protected_input(args[0]):
        raise ValueError("newer calibration, prospective recordings and final inputs are excluded")


def scores(truth, predictions, observed_classes, n_classes):
    truth, predictions = np.asarray(truth), np.asarray(predictions)
    return {
        "n": len(truth),
        "correct": int((truth == predictions).sum()),
        "accuracy": float(accuracy_score(truth, predictions)),
        "macro_f1": float(
            f1_score(truth, predictions, labels=observed_classes, average="macro", zero_division=0)
        ),
        "recall": {str(i): float((predictions[truth == i] == i).mean()) for i in observed_classes},
        "confusion": confusion_matrix(truth, predictions, labels=list(range(n_classes))).tolist(),
    }


def rule_stats(truth, predictions, labels):
    def part(indices):
        accepted = [i for i in indices if predictions[i] is not None]
        errors = sum(predictions[i] != labels[int(truth[i])] for i in accepted)
        return {
            "available": len(indices),
            "matched": len(accepted),
            "errors": errors,
            "coverage": len(accepted) / len(indices) if len(indices) else None,
            "error_among_matches": errors / len(accepted) if accepted else None,
        }

    return {
        "overall": part(range(len(truth))),
        "by_reference_class": {
            labels[int(label)]: part(np.flatnonzero(truth == label)) for label in np.unique(truth)
        },
    }


def benchmark(predict, raw, warmup, calls):
    for _ in range(warmup):
        predict(raw)
    times = []
    for _ in range(calls):
        started = time.perf_counter()
        predict(raw)
        times.append((time.perf_counter() - started) * 1000)
    return {
        "calls": calls,
        "warmup": warmup,
        "p50_ms": float(np.percentile(times, 50)),
        "p95_ms": float(np.percentile(times, 95)),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", default="configs/packet-rule-study.json")
    parser.add_argument("--data", default="data/processed/v2")
    parser.add_argument("--collection", default="artifacts/local/browser-development")
    parser.add_argument("--reference-root", default="experiments/browser-adaptation")
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    sys.addaudithook(audit_guard)
    out = Path(args.output)
    if out.exists():
        raise FileExistsError(out)
    study = json.loads(Path(args.config).read_text())
    if (
        study["feature_version"] != VERSION
        or study["features"] != NAMES
        or not np.array_equal(study["scale_floors"], FLOORS)
        or study["profile_quantiles"] != [0.05, 0.5, 0.95]
        or study["length_buckets"] != list(BUDGETS)
    ):
        raise ValueError("study config differs from implemented rule")
    torch.set_num_threads(study["threads"])
    cfg = json.loads(Path(study["reference_config"]).read_text())
    root = Path(args.collection)
    plan_path = root / cfg["split_plan_filename"]
    plan = json.loads(plan_path.read_text())
    reference_run = Path(args.reference_root) / study["reference_run"]
    models = {
        "tcn": Predictor(reference_run / study["tcn_candidate"] / "bundle"),
        "forest": Predictor(reference_run / study["forest_candidate"] / "bundle"),
    }
    labels = models["forest"].labels
    if models["tcn"].labels != labels:
        raise ValueError("paired model label order differs")
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
        raise ValueError("local train/selection chronology overlaps")
    if any(proofs != model.meta["provenance"]["browser_evidence"] for model in models.values()):
        raise ValueError("rule and model local training/selection cohorts differ")
    public, py, public_ids, manifest = read_split(args.data, "train")
    control, cy, control_ids, _ = read_split(args.data, "selection")
    manifest_sha = sha256(Path(args.data) / "manifest.json")
    if manifest["labels"] != labels or any(
        model.meta["provenance"]["public_data_manifest_sha256"] != manifest_sha for model in models.values()
    ):
        raise ValueError("public training data/labels differ from paired models")
    counts, chosen = Counter(), []
    for i, label in enumerate(cy):
        if counts[int(label)] < cfg["public_selection_per_class"]:
            counts[int(label)] += 1
            chosen.append(i)
    if any(
        [control_ids[i] for i in chosen] != model.meta["provenance"]["public_selection_ids"]
        for model in models.values()
    ):
        raise ValueError("historical retention cohort changed")
    control, cy, control_ids = [control[i] for i in chosen], cy[chosen], [control_ids[i] for i in chosen]
    local = {role: [Flow(packets=row["packets"]).array() for row in values] for role, values in rows.items()}
    ly = {role: np.array([labels.index(row["label"]) for row in values]) for role, values in rows.items()}
    out.mkdir(parents=True)
    provenance = {
        "fixture": False,
        "study": study,
        "study_sha256": sha256(args.config),
        "source_commit": subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
        "source_sha256": {p: sha256(p) for p in (__file__, "src/netembed/packet_rules.py")},
        "versions": {
            "python": platform.python_version(),
            "numpy": np.__version__,
            "torch": torch.__version__,
            "scikit_learn": sklearn.__version__,
        },
        "public_manifest_sha256": manifest_sha,
        "browser_evidence": proofs,
        "browser_plan_sha256": sha256(plan_path),
        "paired_model_ids": {name: m.identity for name, m in models.items()},
        "local_training_connections": len(rows["train"]),
        "local_selection_connections": len(rows["selection"]),
        "selection_groups": sorted({r["group_id"] for r in rows["selection"]}),
        "historical_selection_ids": control_ids,
        "new_calibration_and_final_used": False,
    }
    write_json(out / "protocol.json", provenance)
    print(
        json.dumps(
            {
                "stage": "cohorts_verified",
                "local_train": len(rows["train"]),
                "local_selection": len(rows["selection"]),
            }
        ),
        flush=True,
    )
    training_flows = [x[:b] for x in public + local["train"] for b in BUDGETS]
    training_y = np.repeat(np.concatenate([py, ly["train"]]), len(BUDGETS))
    training_ids = np.repeat(public_ids + [r["id"] for r in rows["train"]], len(BUDGETS)).tolist()
    weights = forest_weights(
        len(public) * len(BUDGETS), np.repeat(ly["train"], len(BUDGETS)), cfg["local_fraction"]
    )
    started = time.perf_counter()
    rule = PacketRules.fit(
        training_flows,
        training_y,
        weights,
        training_ids,
        labels,
        study["minimum_distinct_training_flows_per_class_bucket"],
        provenance,
    )
    fit_seconds = time.perf_counter() - started
    rule.save(out / "rules")
    loaded = PacketRules.load(out / "rules")
    masses = np.bincount(training_y, weights=weights, minlength=len(labels))
    majority = int(np.flatnonzero(np.isclose(masses, masses.max(), atol=1e-12, rtol=0))[0])
    report = {
        "raw_metrics": {},
        "rule_metrics": {},
        "profile_artifact_id": sha256(out / "rules/rules.json"),
        "class_map": labels,
        "training_majority_label": labels[majority],
        "fit_seconds": fit_seconds,
        "paired_model_ids": provenance["paired_model_ids"],
        "policy_fitted": False,
        "default_promoted": False,
        "final_evaluation": False,
        "new_capture": False,
        "profile_support": {
            key: {"active": value["active"], "distinct_flows": value["distinct_training_flow_support"]}
            for key, value in rule.doc["profiles"].items()
        },
    }
    local_records = None
    for cohort, flows, truth, ids in (
        ("local_development", local["selection"], ly["selection"], [r["id"] for r in rows["selection"]]),
        ("historical_public_control", control, cy, control_ids),
    ):
        observed = sorted(set(truth.tolist())) if cohort == "local_development" else list(range(len(labels)))
        budget_metrics, budget_rules, records = {}, {}, []
        for budget in BUDGETS:
            indices = [
                i for i, raw in enumerate(flows) if cohort != "local_development" or len(raw) >= budget
            ]
            xs = [flows[i][:budget] for i in indices]
            y = truth[indices]
            replies = [loaded.predict(x) for x in xs]
            if any(reply != rule.predict(x) for reply, x in zip(replies, xs)):
                raise ValueError("saved rule inference differs from fitted rule")
            predicted = {
                "signature_nearest": [labels.index(r["nearest_label"]) for r in replies],
                "training_majority": [majority] * len(xs),
            }
            probabilities = {}
            for name, model in models.items():
                probabilities[name] = np.concatenate(
                    [model.probabilities(xs[i : i + 128]) for i in range(0, len(xs), 128)]
                )
                predicted[name] = probabilities[name].argmax(1).tolist()
            budget_metrics[str(budget)] = {
                name: scores(y, values, observed, len(labels)) for name, values in predicted.items()
            }
            budget_rules[str(budget)] = rule_stats(y, [r["rule_label"] for r in replies], labels)
            for j, index in enumerate(indices):
                records.append(
                    {
                        "id": ids[index],
                        "reference": labels[int(y[j])],
                        "requested_cap": budget,
                        "actual_packets": len(xs[j]),
                        "signature": replies[j],
                        "raw_model_top1": {
                            name: labels[int(values[j])] for name, values in predicted.items()
                        },
                        "model_probabilities": {
                            name: value[j].tolist() for name, value in probabilities.items()
                        },
                    }
                )
        write_json(out / f"{cohort}-predictions.json", records)
        report["raw_metrics"][cohort] = {
            "budgets": budget_metrics,
            "mean_budget_macro_f1": {
                name: float(np.mean([b[name]["macro_f1"] for b in budget_metrics.values()]))
                for name in predicted
            },
            "correct_across_available_caps": {
                name: sum(b[name]["correct"] for b in budget_metrics.values()) for name in predicted
            },
            "available_caps": sum(b["training_majority"]["n"] for b in budget_metrics.values()),
        }
        report["rule_metrics"][cohort] = {
            "budgets": budget_rules,
            "combined": rule_stats(
                np.array([labels.index(r["reference"]) for r in records]),
                [r["signature"]["rule_label"] for r in records],
                labels,
            ),
        }
        for name, candidate in (("tcn", study["tcn_candidate"]), ("forest", study["forest_candidate"])):
            old_metric = json.loads((reference_run / candidate / "development.json").read_text())
            key = "local_macro_f1" if cohort == "local_development" else "public_clean_macro_f1"
            if abs(report["raw_metrics"][cohort]["mean_budget_macro_f1"][name] - old_metric[key]) > 1e-12:
                raise ValueError("paired quality metric does not reproduce")
        if cohort == "local_development":
            local_records = records
        print(
            json.dumps(
                {
                    "stage": cohort,
                    "raw_f1": report["raw_metrics"][cohort]["mean_budget_macro_f1"],
                    "rules": report["rule_metrics"][cohort]["combined"]["overall"],
                }
            ),
            flush=True,
        )
    replay = {}
    for name, candidate in (("tcn", study["tcn_candidate"]), ("forest", study["forest_candidate"])):
        saved = json.loads((reference_run / candidate / "predictions.json").read_text())
        original = {(r["id"], r["observed_packets"]): r for r in saved}
        deltas = []
        if len(original) != len(local_records):
            raise ValueError("paired saved local prediction inventory differs")
        for row in local_records:
            old = original[row["id"], row["requested_cap"]]
            if old["reference"] != row["reference"] or old["top1"] != row["raw_model_top1"][name]:
                raise ValueError("paired local labels/predictions changed")
            deltas.append(
                float(np.max(np.abs(np.array(old["probabilities"]) - row["model_probabilities"][name])))
            )
        if max(deltas) > 1e-7:
            raise ValueError("paired saved model probabilities differ")
        replay[name] = {"comparisons": len(deltas), "maximum_probability_difference": max(deltas)}
    report["paired_prediction_replay"] = replay
    local_raw = report["raw_metrics"]["local_development"]
    public_raw = report["raw_metrics"]["historical_public_control"]
    gates = study["further_validation_gates"]
    recalls_pass = all(
        np.mean([b["signature_nearest"]["recall"][str(i)] for b in local_raw["budgets"].values()])
        >= np.mean([b["forest"]["recall"][str(i)] for b in local_raw["budgets"].values()])
        for i in sorted(set(ly["selection"].tolist()))
    )
    nearest_pass = (
        local_raw["mean_budget_macro_f1"]["signature_nearest"]
        >= local_raw["mean_budget_macro_f1"]["forest"] - gates["local_f1_comparability_margin_to_forest"]
        and public_raw["mean_budget_macro_f1"]["signature_nearest"]
        >= public_raw["mean_budget_macro_f1"]["forest"] - gates["maximum_historical_public_f1_loss_to_forest"]
        and recalls_pass
    )
    matched = report["rule_metrics"]["local_development"]["combined"]
    rule_pass = (
        matched["overall"]["matched"] >= gates["minimum_rule_matches_local"]
        and matched["overall"]["error_among_matches"]
        <= gates["maximum_error_among_rule_matches_overall_and_per_local_class"]
        and all(
            v["matched"] >= gates["minimum_rule_matches_per_local_class"]
            and v["error_among_matches"]
            <= gates["maximum_error_among_rule_matches_overall_and_per_local_class"]
            for v in matched["by_reference_class"].values()
        )
    )
    report["development_decision"] = {
        "nearest_signature_comparable": bool(nearest_pass),
        "per_local_class_recall_nonregression": bool(recalls_pass),
        "unique_rules_meet_support_error_gate": bool(rule_pass),
        "worth_independent_validation_under_frozen_gates": bool(nearest_pass and rule_pass),
        "default_promoted": False,
        "note": "Development decision only. Even a pass would require a new independent validation cycle; neither profile distances nor interval matches are calibrated correctness probabilities.",
    }
    durations = {}
    for budget in BUDGETS:
        values = [
            float(Flow(packets=r["packets"][:budget]).array()[:, 0].astype(np.float64).sum() / 1000)
            for r in rows["train"] + rows["selection"]
            if len(r["packets"]) >= budget
        ]
        durations[str(budget)] = {
            "n": len(values),
            "median_seconds": float(np.median(values)),
            "under_three_seconds": sum(t < 3 for t in values),
            "at_least_fifteen_seconds": sum(t >= 15 for t in values),
        }
    report["internship_activity_rules_availability"] = {
        "prefix_durations": durations,
        "activity_accuracy": None,
        "reason": "Only service references exist. Activity truth, full-flow IP-size/rate windows and RTP/STUN/DNS/ASN/name inputs are outside this packet-only study. No activity-to-app labels or zero-filled missing structural evidence.",
    }
    raw = Flow(**json.loads(Path(study["benchmark_input"]).read_text())).array()
    report["cpu"] = {
        "input_sha256": sha256(study["benchmark_input"]),
        "actual_packets": len(raw),
        "hardware": platform.platform() + " / " + platform.processor(),
        "torch": torch.__version__,
        "threads": torch.get_num_threads(),
        "calls": {},
    }
    for name, predict in {
        "packet_rules": loaded.predict,
        **{name: m.predict for name, m in models.items()},
    }.items():
        report["cpu"]["calls"][name] = benchmark(
            predict, raw, study["benchmark_warmup"], study["benchmark_calls"]
        )
        print(json.dumps({"stage": "cpu", "name": name, **report["cpu"]["calls"][name]}), flush=True)
    report["provenance"] = {
        "protocol_sha256": sha256(out / "protocol.json"),
        "prediction_sha256": {
            name: sha256(out / f"{name}-predictions.json")
            for name in ("local_development", "historical_public_control")
        },
    }
    report["limits"] = (
        "Post-failure development comparison, not independent validation. Local prefixes are correlated within14 connections/two selection visits. Historical public data is retention only. Raw nearest rank is distinct from unique-rule matches; distances are not probabilities and no error-calibrated policy was fit. Same training pool, feature budgets and global domain weights, different training-only feature transforms/fit procedures. CPU excludes capture/HTTP/UI. No app service change or heuristic release promotion."
    )
    write_json(out / "report.json", report)
    print(str(out), flush=True)


if __name__ == "__main__":
    main()
