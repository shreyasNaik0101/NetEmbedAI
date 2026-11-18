"""Fixed-policy live check; actual emitted decisions stay separate from replay."""

import json
import os
from pathlib import Path

import numpy as np

from .browser_sessions import verify_fresh
from .bundle import Predictor, sha256, write_json
from .contract import Flow
from .fresh_evaluation import evaluation_coverage
from .paired_study import check_order, read_archive, support, validate_archive_plan


def load_model(cfg):
    path = Path(cfg["source_bundle"])
    model = Predictor(path)
    if (
        model.identity != cfg["source_artifact_id"]
        or sha256(path / "forest.json") != cfg["source_weight_sha256"]
        or model.meta["kind"] != "forest"
        or model.meta["policy"] != cfg["expected_policy"]
        or not model.meta["policy"]["fitted"]
        or model.meta["provenance"].get("fixture", True)
    ):
        raise ValueError("frozen real public-policy model changed")
    return model


def offline_guard(event, args, root, cfg):
    if event in ("socket.connect", "socket.getaddrinfo"):
        raise ValueError("live-check scoring is offline")
    if event == "open" and isinstance(args[0], (str, bytes)):
        path = Path(os.fsdecode(args[0])).resolve()
        private, experiments = Path("artifacts/local").resolve(), Path("experiments").resolve()
        if (
            path.is_relative_to(Path("data").resolve())
            or (path.is_relative_to(private) and not path.is_relative_to(Path(root).resolve()))
            or any(part.startswith("excluded-prior-") for part in path.parts)
            or (
                path.is_relative_to(experiments)
                and not path.is_relative_to(Path(cfg["source_bundle"]).resolve())
            )
        ):
            raise ValueError("old outcomes and calibration/training data excluded from live-check scoring")


def live_stats(records):
    emitted = [r for r in records if r["live_prediction"] is not None]
    accepted = [r for r in emitted if r["live_prediction"]["label"] is not None]
    errors = sum(r["live_prediction"]["label"] != r["reference"] for r in accepted)
    raw_correct = sum(r["live_prediction"]["alternatives"][0]["label"] == r["reference"] for r in emitted)
    return {
        "eligible_flow_checkpoints": len(records),
        "emitted": len(emitted),
        "missing_live_checkpoint": len(records) - len(emitted),
        "accepted": len(accepted),
        "refused": len(emitted) - len(accepted),
        "errors": errors,
        "accepted_error": errors / len(accepted) if accepted else None,
        "end_to_end_coverage": len(accepted) / len(records) if records else 0.0,
        "conditional_model_coverage": len(accepted) / len(emitted) if emitted else None,
        "raw_correct_among_emitted": raw_correct,
    }


def policy_metrics(records, cfg):
    by_budget = {}
    for budget in cfg["budgets"]:
        points = [r for r in records if r["budget"] == budget and r["reference"] == r["target"]]
        by_budget[str(budget)] = {
            "overall_target": live_stats(points),
            "classes": {
                label: live_stats([r for r in points if r["reference"] == label])
                for label in cfg["local_labels"]
            },
            "replay_correct_secondary": sum(
                r["replay_prediction"]["alternatives"][0]["label"] == r["reference"] for r in points
            ),
        }
    rules = cfg["rules"]
    checks = {}
    for label, point in by_budget["10"]["classes"].items():
        checks[label] = (
            point["accepted"] >= rules["minimum_accepted_per_target"]
            and point["end_to_end_coverage"] >= rules["minimum_end_to_end_coverage"]
            and point["accepted_error"] is not None
            and point["accepted_error"] <= rules["maximum_empirical_accepted_error"]
        )
    return {"budgets": by_budget, "primary_class_checks": checks, "policy_screen_pass": all(checks.values())}


def percentiles(values):
    if any(not np.isfinite(v) or v < 0 for v in values):
        raise ValueError("invalid latency sample; preserve timing problem")
    return {
        "n": len(values),
        "p50_ms": float(np.percentile(values, 50)) if values else None,
        "p95_ms": float(np.percentile(values, 95)) if values else None,
    }


def timing_metrics(timing, capture, audit):
    result = {
        key: percentiles([r[key] for r in timing["timing_samples"]])
        for key in ("capture_to_parser_ms", "queue_ms", "pipeline_ms", "capture_to_event_ms")
    }
    result["capture_to_browser_receipt_ms"] = percentiles(timing["capture_to_browser_receipt_ms"])
    result["drops"] = timing["drops"]
    result["coalesced"] = timing["coalesced"]
    result["receipt_tracking_evicted"] = timing["receipt_tracking_evicted"]
    result["receipt_tracking_pending"] = timing["receipt_tracking_pending"]
    result["operational_screen_pass"] = (
        not timing["running"]
        and not timing["drops"]
        and not capture["evidence_evicted"]
        and result["pipeline_ms"]["n"] > 0
        and result["capture_to_browser_receipt_ms"]["n"] > 0
        and audit["original_live_prediction_comparison"]["predictions"] > 0
    )
    result["basis"] = (
        "All real emitted prediction events, not only correct/mapped cases. Same-host clocks; browser receipt is not paint. No hard timing bound."
    )
    return result


def score_live(root, cfg, plan_path):
    root = Path(root)
    output = root / "live-policy-report.json"
    if output.exists() or (root / "live-policy-predictions.json").exists():
        raise ValueError("live result already started/frozen; preserve it")
    reports, cohorts, timing_reports, bindings = [], [], {}, {}
    for spec in cfg["trials"]:
        trial = spec["id"]
        archive = read_archive(root, trial)
        validate_archive_plan(root, trial, archive, cfg)
        if archive["status"] != "usable" or archive["collection_role"] != "live_policy_evaluation":
            raise ValueError("both usable live-policy visits required")
        check_order(cfg, trial, reports, archive["first_packet_ms"], archive["session_id"])
        reports.append(archive)

        def load(name):
            path = root / f"{trial}-{name}.json"
            if path.name not in archive["files"]:
                raise ValueError("required live evidence not bound to archive")
            return json.loads(path.read_text())

        rows, families, capture, timing, audit, intent, proof = (
            load(name)
            for name in ("rows", "families", "capture", "timing", "audit", "intent", "browser-processes")
        )
        if (
            capture["fixture"]
            or capture["source"] != "user_started_capture"
            or capture["artifact_id"] != cfg["source_artifact_id"]
            or audit["artifact_id"] != cfg["source_artifact_id"]
            or any(value["session_id"] != archive["session_id"] for value in (capture, timing, audit))
            or proof["session_id"] != archive["session_id"]
            or proof["plan_sha256"] != sha256(plan_path)
            or intent["collection_role"] != "live_policy_evaluation"
            or intent["collection_plan_sha256"] != sha256(plan_path)
        ):
            raise ValueError("live capture/model/role/browser binding differs")
        verify_fresh(proof["processes"], intent, archive["first_packet_ms"])
        replay = audit["original_live_prediction_comparison"]
        if replay["changed_decision_labels"] or replay["maximum_alternative_score_difference"] > 1e-6:
            raise ValueError("source live inference does not reproduce")
        support(rows, spec, cfg)
        evaluation_coverage(rows, families, spec, cfg)
        originals = {r["flow_id"]: r for r in capture["flows"]}
        for row in rows:
            if not row["id"].startswith(f"browser:{archive['session_id']}:"):
                raise ValueError("row belongs to another capture session")
            original = originals[row["id"].split(":")[-1]]
            if row["packets"] != original["packets"]:
                raise ValueError("live measured packet values changed")
            cohorts.append((spec, row, original))
        timing_reports[trial] = timing_metrics(timing, capture, audit)
        bindings[trial] = sha256(root / (trial + "-archive.json"))
    model = load_model(cfg)
    records, seen = [], set()
    for spec, row, original in cohorts:
        if row["id"] in seen:
            raise ValueError("duplicate live flow across visits")
        seen.add(row["id"])
        if row["label"] not in cfg["local_labels"]:
            continue
        raw = Flow(packets=row["packets"]).array()
        emitted = {p["observed_packets"]: p for p in original["predictions"]}
        for budget in cfg["budgets"]:
            if len(raw) < budget:
                continue
            replay = model.predict(raw[:budget])
            native = emitted.get(budget)
            if native:
                for key in ("label", "status", "alternatives", "artifact_id"):
                    if native[key] != replay[key]:
                        raise ValueError("native prediction changed on replay")
            records.append(
                {
                    "trial": spec["id"],
                    "id": row["id"],
                    "reference": row["label"],
                    "target": spec["target"],
                    "budget": budget,
                    "packet_observation_ms": float(raw[:budget, 0].sum()),
                    "live_prediction": native,
                    "replay_prediction": replay,
                }
            )
    metrics = policy_metrics(records, cfg)
    operational = all(p["operational_screen_pass"] for p in timing_reports.values())
    write_json(root / "live-policy-predictions.json", records)
    write_json(
        output,
        {
            "artifact_id": model.identity,
            "policy": model.meta["policy"],
            "plan_sha256": sha256(plan_path),
            "archives": bindings,
            "metrics": metrics,
            "timing": timing_reports,
            "reference_inventories": {r["trial_id"]: r["reference_inventory"] for r in reports},
            "mapped_counts": {r["trial_id"]: r["counts"] for r in reports},
            "operational_screen_pass": operational,
            "status": "descriptive_live_screen_pass"
            if operational and metrics["policy_screen_pass"]
            else "stop_live_screen_failed",
            "prediction_sha256": sha256(root / "live-policy-predictions.json"),
            "source_sha256": sha256(__file__),
            "fixture": bool(cfg.get("fixture", False)),
            "weights_or_policy_refitted": False,
            "default_promoted": False,
            "limits": cfg["limits"],
        },
    )
    return output
