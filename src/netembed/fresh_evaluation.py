"""Frozen forest comparison on four new visits; no fitting or live activation."""

from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path

import numpy as np

from .browser_sessions import verify_fresh
from .bundle import Predictor, sha256, write_json
from .contract import Flow
from .family_collection import validate_rows
from .paired_study import check_order, read_archive, support, validate_archive_plan


def frozen_models(cfg):
    result = {}
    for name, spec in cfg["models"].items():
        path = Path(spec["bundle"])
        if (
            sha256(path / "metadata.json") != spec["metadata_sha256"]
            or sha256(path / "forest.json") != spec["weight_sha256"]
        ):
            raise ValueError("frozen evaluation model changed")
        model = Predictor(path)
        if model.meta["kind"] != "forest" or model.meta["policy"]["fitted"]:
            raise ValueError("requires frozen uncalibrated forest")
        result[name] = model
    if (
        set(result) != {"control", "plus-real-ipv6"}
        or result["control"].labels != result["plus-real-ipv6"].labels
    ):
        raise ValueError("evaluation model inventory/labels differ")
    return result


def offline_guard(event, args, root):
    if event in ("socket.connect", "socket.getaddrinfo"):
        raise ValueError("evaluation scoring is offline")
    if event == "open" and isinstance(args[0], (str, bytes)):
        path = Path(os.fsdecode(args[0])).resolve()
        private = Path("artifacts/local").resolve()
        experiments = Path("experiments").resolve()
        pilot = experiments / "ipv6-realdata-pilot-v1"
        bundles = [pilot / arm / "bundle" for arm in ("control", "plus-real-ipv6")]
        if (
            (path.is_relative_to(private) and not path.is_relative_to(Path(root).resolve()))
            or path.is_relative_to(Path("data").resolve())
            or any(p.startswith("excluded-prior-") for p in path.parts)
            or (path.is_relative_to(experiments) and not any(path.is_relative_to(p) for p in bundles))
        ):
            raise ValueError("training and earlier outcome data excluded from fresh evaluation")


def evaluation_coverage(rows, families, spec, cfg):
    validate_rows(families)
    index = {r["id"]: r for r in families}
    if len({r["id"] for r in rows}) != len(rows) or set(index) != {r["id"] for r in rows}:
        raise ValueError("evaluation row/family inventory differs")
    for r in rows:
        f = index[r["id"]]
        if f["label"] != r["label"] or f["packets"] != len(r["packets"]):
            raise ValueError("evaluation family label/length differs")
    n = sum(f["label"] == spec["target"] and f["family"] == 6 and f["packets"] >= 30 for f in families)
    if n < cfg["minimum_complete_target_ipv6"]:
        raise ValueError("evaluation needs one complete target IPv6 flow; preserve shortfall")
    return dict(Counter(f"{f['label']}:IPv{f['family']}" for f in families))


def summarize(records, cfg, labels):
    """Primary is target-only, each of the two visits per service equally weighted."""
    output = {}
    for arm in ("control", "plus-real-ipv6"):
        by_budget = {}
        for budget in cfg["budgets"]:
            points = [r for r in records if r["budget"] == budget]
            matrix = np.zeros((len(labels), len(labels)), dtype=int)
            for r in points:
                matrix[labels.index(r["reference"]), labels.index(r[arm]["raw_top1"])] += 1
            classes = {}
            for label in cfg["local_labels"]:
                visits = {}
                for spec in cfg["trials"]:
                    if spec["target"] != label:
                        continue
                    part = [r for r in points if r["trial"] == spec["id"] and r["reference"] == label]
                    correct = sum(r[arm]["raw_top1"] == label for r in part)
                    visits[spec["id"]] = {
                        "n": len(part),
                        "correct": correct,
                        "recall": correct / len(part) if part else None,
                    }
                values = [v["recall"] for v in visits.values()]
                classes[label] = {
                    "visits": visits,
                    "mean_visit_recall": float(np.mean(values)) if values and None not in values else None,
                }
            values = [c["mean_visit_recall"] for c in classes.values()]
            by_budget[str(budget)] = {
                "target_classes": classes,
                "target_session_balanced_macro_recall": float(np.mean(values))
                if None not in values
                else None,
                "all_local_cases": len(points),
                "all_local_correct": int(matrix.trace()),
                "all_local_confusion_matrix": matrix.tolist(),
                "confusion_label_order": labels,
                "all_local_withheld": sum(r[arm]["accepted_label"] is None for r in points),
                "family_cells": {
                    f"{label}:IPv{family}": {
                        "n": len(
                            part := [r for r in points if r["reference"] == label and r["family"] == family]
                        ),
                        "correct": sum(r[arm]["raw_top1"] == label for r in part),
                        "recall": sum(r[arm]["raw_top1"] == label for r in part) / len(part)
                        if part
                        else None,
                    }
                    for label in cfg["local_labels"]
                    for family in (4, 6)
                },
            }
        output[arm] = by_budget
    c, b = (output[a]["10"] for a in ("plus-real-ipv6", "control"))
    primary, baseline = (p["target_session_balanced_macro_recall"] for p in (c, b))
    checks = {
        "candidate_class_floor": all(
            c["target_classes"][label]["mean_visit_recall"] is not None
            and c["target_classes"][label]["mean_visit_recall"]
            >= cfg["screen"]["minimum_candidate_class_mean_visit_recall"]
            for label in cfg["local_labels"]
        ),
        "candidate_primary_no_loss": primary is not None and baseline is not None and primary >= baseline,
        "candidate_each_class_no_loss": all(
            c["target_classes"][label]["mean_visit_recall"] is not None
            and b["target_classes"][label]["mean_visit_recall"] is not None
            and c["target_classes"][label]["mean_visit_recall"]
            >= b["target_classes"][label]["mean_visit_recall"]
            for label in cfg["local_labels"]
        ),
    }
    output["primary_paired_difference"] = (
        primary - baseline if primary is not None and baseline is not None else None
    )
    output["descriptive_checks"] = checks
    output["descriptive_screen_pass"] = all(checks.values())
    return output


def score_evaluation(root, cfg, plan_path):
    root = Path(root)
    if (root / "comparison.json").exists() or (root / "paired-predictions.json").exists():
        raise ValueError("evaluation already started/frozen; preserve outputs")
    reports, cohort, used_ids = [], [], set()
    for spec in cfg["trials"]:
        trial = spec["id"]
        report = read_archive(root, trial)
        validate_archive_plan(root, trial, report, cfg)
        if report["status"] != "usable" or report["collection_role"] != "evaluation":
            raise ValueError("all four usable evaluation visits required before scoring")
        check_order(cfg, trial, reports, report["first_packet_ms"], report["session_id"])
        reports.append(report)

        def load(name):
            path = root / f"{trial}-{name}.json"
            if path.name not in report["files"]:
                raise ValueError("evaluation archive missing required evidence")
            return json.loads(path.read_text())

        rows, families, intent, proof = (load(n) for n in ("rows", "families", "intent", "browser-processes"))
        if (
            intent["collection_role"] != "evaluation"
            or intent["collection_plan_sha256"] != sha256(plan_path)
            or proof["plan_sha256"] != sha256(plan_path)
            or proof["session_id"] != report["session_id"]
        ):
            raise ValueError("evaluation intent/browser binding differs")
        verify_fresh(proof["processes"], intent, report["first_packet_ms"])
        support(rows, spec, cfg)
        evaluation_coverage(rows, families, spec, cfg)
        family_index = {r["id"]: r["family"] for r in families}
        for row in rows:
            if row["id"] in used_ids or not row["id"].startswith(f"browser:{report['session_id']}:"):
                raise ValueError("evaluation flow duplicate/session differs")
            used_ids.add(row["id"])
            raw = Flow(packets=row["packets"]).array()
            if row["label"] in cfg["local_labels"]:
                cohort.append((spec, row, raw, family_index[row["id"]]))
    pair = frozen_models(cfg)
    records = []
    for spec, row, raw, family in cohort:
        for budget in cfg["budgets"]:
            if len(raw) < budget:
                continue
            prefix = raw[:budget]
            entry = {
                "trial": spec["id"],
                "id": row["id"],
                "reference": row["label"],
                "target": spec["target"],
                "family": family,
                "budget": budget,
                "observed_packets": len(prefix),
                "prefix_sha256": hashlib.sha256(np.asarray(prefix, dtype="<f4").tobytes()).hexdigest(),
            }
            for arm, model in pair.items():
                probabilities = model.probabilities([prefix])[0]
                reply = model.predict(prefix)
                if reply["label"] is not None:
                    raise ValueError("uncalibrated evaluation must withhold accepted labels")
                entry[arm] = {
                    "raw_top1": model.labels[int(np.argmax(probabilities))],
                    "probabilities": probabilities.tolist(),
                    "accepted_label": None,
                    "status": reply["status"],
                }
            records.append(entry)
    labels = pair["control"].labels
    metrics = summarize(records, cfg, labels)
    write_json(root / "paired-predictions.json", records)
    write_json(
        root / "comparison.json",
        {
            "created_utc": datetime.now(timezone.utc).isoformat(),
            "plan_sha256": sha256(plan_path),
            "archives": {s["id"]: sha256(root / (s["id"] + "-archive.json")) for s in cfg["trials"]},
            "prediction_sha256": sha256(root / "paired-predictions.json"),
            "models": cfg["models"],
            "source_sha256": sha256(__file__),
            "metrics": metrics,
            "status": "promising_fresh_screen"
            if metrics["descriptive_screen_pass"]
            else "stop_failed_fresh_screen",
            "default_promoted": False,
            "policy_fitted": False,
            "limits": cfg["limits"],
        },
    )
    return root / "comparison.json"
