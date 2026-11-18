"""Frozen fresh-session comparison contracts; no training or capture startup."""

import hashlib
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

import numpy as np

from .bundle import sha256


def collection_status(root, cfg, now_ms):
    """Read and verify collection progress without loading any candidate model."""
    root = Path(root)
    slots, reports, next_slot = [], [], None
    for spec in cfg["trials"]:
        trial = spec["id"]
        item = {"trial": trial, "target": spec["target"], "day": spec["day"]}
        if (root / f"{trial}-archive.json").exists():
            try:
                report = read_archive(root, trial)
                validate_archive_plan(root, trial, report, cfg)
                if report["status"] == "usable":
                    check_order(cfg, trial, reports, report["first_packet_ms"], report["session_id"])
                item.update({"state": report["status"], "counts": report.get("counts", {})})
                reports.append(report)
            except (ValueError, KeyError, OSError) as error:
                item.update({"state": "integrity_error", "reason": str(error)})
        else:
            state = "not_prepared"
            if (root / f"{trial}-intent.json").exists():
                state = "prepared"
            if (root / f"{trial}-attempt.json").exists():
                state = "bound_attempt_waiting_archive"
            item["state"] = state
        if next_slot is None and item["state"] != "usable":
            next_slot = item.copy()
        slots.append(item)
    next_date, action = None, "complete_set_ready_for_explicit_scoring"
    if next_slot:
        action = next_slot["state"]
        if action == "not_prepared":
            try:
                check_order(cfg, next_slot["trial"], reports, now_ms)
                action = "ready_to_prepare"
            except ValueError as error:
                action = "blocked_by_schedule_or_prior_slot"
                next_slot["reason"] = str(error)
                if reports and next_slot["day"] > cfg["trials"][0]["day"]:
                    day = datetime.fromisoformat(local_date(reports[0]["first_packet_ms"], cfg)).date()
                    next_date = (day + timedelta(days=1)).isoformat()
    if (
        cfg.get("workflow") == "calibrate_then_final"
        and next_slot
        and next_slot["trial"] in [s["id"] for s in cfg["trials"] if s.get("role") == "final"]
    ):
        decision_path = root / "calibration-decision.json"
        if not decision_path.exists():
            action = "awaiting_calibration_policy"
        elif not json.loads(decision_path.read_text())["policy"]["fitted"]:
            action = "calibration_failed_stop"
    if cfg.get("workflow") == "family_development" and next_slot:
        spec = next(s for s in cfg["trials"] if s["id"] == next_slot["trial"])
        if spec["role"] == "selection" and action not in ("unusable_stop", "integrity_error"):
            if not (root / "training-freeze.json").exists() or not (root / "trained-seed17.json").exists():
                action = "awaiting_frozen_training_and_bound_seed17"
    if cfg.get("scope") == "feasibility_only" and next_slot is None:
        action = "feasibility_complete_no_scoring"
    if cfg.get("scope") == "session_acquisition_only" and next_slot is None:
        action = "session_acquisition_complete_no_scoring"
    if cfg.get("workflow") == "ten_packet_policy" and (root / "final-report.json").exists():
        try:
            report = json.loads((root / "final-report.json").read_text())
            if report["status"] not in ("final_failed_stop", "small_local_accepted_screen_pass"):
                raise ValueError("unrecognized final report status")
            if (
                sha256(root / "final-predictions.json") != report["predictions_sha256"]
                or sha256(root / "calibration-decision.json") != report["decision_sha256"]
                or any(
                    Path(trial).name != trial or sha256(root / (trial + "-archive.json")) != digest
                    for trial, digest in report["archives"].items()
                )
            ):
                raise ValueError("final report inputs changed")
            action = report["status"]
        except (OSError, ValueError, KeyError, TypeError):
            action = "final_report_integrity_error"
    if (
        cfg.get("workflow") in ("ten_packet_fresh", "ten_packet_policy")
        and (root / "session-integrity-review.json").exists()
    ):
        action = "session_integrity_review_required"
        if next_slot:
            next_slot["reason"] = "interrupted/restarted session; no replacement or prospective grading"
    return {
        "root": str(root),
        "slots": slots,
        "usable_visits": sum(s["state"] == "usable" for s in slots),
        "next_slot": next_slot,
        "next_action": action,
        "earliest_next_local_date": next_date,
        "candidate_models_loaded": False,
        "candidate_scoring_run": False,
        "saved_comparison_exists": (root / "comparison.json").exists(),
    }


CONFIG_SHA = "42a885ede594ce523bc3f2b35d223b4806683ffa6fd94dd5c21dea8322821d7f"
FOLLOWUP_SHA = "c8aed9b2c6fe1138e574b8e6af8a8c9d7ddbb3ba62b57359922e829b37f6f289"
CALIBRATION_SHA = "3f8cc1029137439d2a3a82563ea1c6b462019a4d03587dbc3777dc1499f1d693"
FAMILY_SHA = "24a45e295b63e4ffce390e5a5d9b7f51a7dc968b31c6df3fa1f63e5459e7af17"
HOTSPOT_SHA = "8742c0a5b24be8edf9912428689dcdfc4a332e96d3c1d2fe1f5e7587a4f01a70"
FRESH_SHA = "8d457350c09f8dfeaac13d30f792bd073f4ab41490d4dca8c737b01c285e8a2d"
IPV6_EVALUATION_SHA = "dd0723d1dbefc777a586133a71de74a8f2478b2f427ee5d3ff349f02a913e616"
LIVE_POLICY_SHA = "c2f040c50b540cf083451953d27d50dd42e96845afebd6a9113080127ecdf695"
SPOTIFY_REPAIR_SHA = "f4853905ca5bcb0b17bdda8ce92935737a0fa98ceb00c03a24fad33604a6f50e"
TEN_FRESH_SHA = "5d69cabd395e168a1c06bbebd9f9a7de16d5e82434c203acf7406536c71f8cac"
TEN_CONTINUATION_SHA = "c59b34bc3073ce68a0e5ee28d0a5eb069a2c56e898ab65eee72e5f50a1e6a9ca"
TEN_POLICY_SHA = "f81457112c67e119878533e6d1c3425ea9fa643480bb20985ec65f75a35ebe0c"


def validate_archive_plan(root, trial, report, cfg):
    binding = cfg.get("inherited_archives", {}).get(trial)
    expected = {
        "prospective-paired-followup-v1": FOLLOWUP_SHA,
        "forest-policy-calibration-v1": CALIBRATION_SHA,
        "family-development-v1": FAMILY_SHA,
        "hotspot-family-feasibility-v1": HOTSPOT_SHA,
        "hotspot-fresh-sessions-v1": FRESH_SHA,
        "ipv6-frozen-evaluation-v1": IPV6_EVALUATION_SHA,
        "ipv6-live-policy-v1": LIVE_POLICY_SHA,
        "spotify-data-repair-v1": SPOTIFY_REPAIR_SHA,
        "ten-packet-fresh-v1": TEN_FRESH_SHA,
        "ten-packet-fresh-continuation-v1": TEN_CONTINUATION_SHA,
        "ten-packet-policy-v1": TEN_POLICY_SHA,
    }.get(cfg["version"], CONFIG_SHA)
    if binding:
        if sha256(Path(root) / f"{trial}-archive.json") != binding["archive_sha256"]:
            raise ValueError("inherited archive changed")
        expected = binding["plan_sha256"]
    if report["trial_id"] != trial or report["plan_sha256"] != expected:
        raise ValueError("archive belongs to another slot or plan")


def read_plan(path):
    raw = Path(path).read_bytes().replace(b"\r\n", b"\n")
    if hashlib.sha256(raw).hexdigest() not in (
        CONFIG_SHA,
        FOLLOWUP_SHA,
        CALIBRATION_SHA,
        FAMILY_SHA,
        HOTSPOT_SHA,
        FRESH_SHA,
        IPV6_EVALUATION_SHA,
        LIVE_POLICY_SHA,
        SPOTIFY_REPAIR_SHA,
        TEN_FRESH_SHA,
        TEN_CONTINUATION_SHA,
        TEN_POLICY_SHA,
    ):
        raise ValueError("prospective paired declaration changed")
    return json.loads(raw)


def local_date(ms, cfg):
    zone = timezone(timedelta(minutes=cfg["offset_minutes"]))
    return datetime.fromtimestamp(ms / 1000, zone).date().isoformat()


def check_order(cfg, trial, previous, first_ms, session=None):
    if cfg.get("workflow") in ("spotify_data_repair", "ten_packet_fresh", "ten_packet_policy"):
        from .spotify_repair import check_schedule

        return check_schedule(cfg, trial, previous, first_ms, session)
    specs = cfg["trials"]
    index = next((i for i, s in enumerate(specs) if s["id"] == trial), None)
    if index is None or len(previous) != index:
        raise ValueError("archive the declared preceding slots first")
    declaration = (
        cfg.get("followup_declared_utc", cfg["declared_utc"])
        if trial not in cfg.get("inherited_archives", {})
        else cfg["declared_utc"]
    )
    if first_ms <= datetime.fromisoformat(declaration).timestamp() * 1000:
        raise ValueError("capture predates declaration")
    for spec, report in zip(specs, previous):
        if report["trial_id"] != spec["id"] or report["status"] != "usable":
            raise ValueError("unusable or mismatched prior attempt stops study")
        if session is not None and report["session_id"] == session:
            raise ValueError("duplicate session")
        if first_ms <= report["last_packet_ms"]:
            raise ValueError("overlapping sessions")
        today = local_date(first_ms, cfg)
        day = local_date(report["first_packet_ms"], cfg)
        if (spec["day"] == specs[index]["day"] and today != day) or (
            spec["day"] < specs[index]["day"] and today <= day
        ):
            raise ValueError("recordings must follow the declared two-date schedule")


def support(rows, spec, cfg):
    for budget, key in ((10, "minimum_target_at_10_per_trial"), (30, "minimum_target_at_30_per_trial")):
        n = sum(r["label"] == spec["target"] and len(r["packets"]) >= budget for r in rows)
        if n < cfg[key]:
            raise ValueError(f"insufficient independent {spec['target']} support at {budget} packets: {n}")


def read_archive(root, trial):
    root = Path(root)
    report = json.loads((root / f"{trial}-archive.json").read_text())
    for name, digest in report["files"].items():
        if Path(name).name != name or sha256(root / name) != digest:
            raise ValueError("archived evidence changed")
    return report


def summarize(records, cfg):
    """Visits, not repeated prefixes, get equal primary weight within each class."""
    result = {}
    for model in ("prefix", "forest"):
        by_budget = {}
        for budget in cfg["budgets"]:
            part = [r for r in records if r["budget"] == budget]
            classes = {}
            for label in cfg["local_labels"]:
                visits = {}
                for spec in cfg["trials"]:
                    group = [r for r in part if r["trial"] == spec["id"] and r["reference"] == label]
                    if group:
                        visits[spec["id"]] = {
                            "n": len(group),
                            "correct": sum(r[model]["raw_top1"] == label for r in group),
                            "recall": float(np.mean([r[model]["raw_top1"] == label for r in group])),
                        }
                classes[label] = {
                    "visits": visits,
                    "mean_visit_recall": float(np.mean([v["recall"] for v in visits.values()]))
                    if visits
                    else None,
                }
            values = [v["mean_visit_recall"] for v in classes.values()]
            by_budget[str(budget)] = {
                "classes": classes,
                "session_balanced_macro_recall": float(np.mean(values))
                if all(v is not None for v in values)
                else None,
                "cases": len(part),
                "correct": sum(r[model]["raw_top1"] == r["reference"] for r in part),
                "withheld": sum(r[model]["accepted_label"] is None for r in part),
            }
        result[model] = by_budget
    primary = result["prefix"]["10"]["session_balanced_macro_recall"]
    baseline = result["forest"]["10"]["session_balanced_macro_recall"]
    result["descriptive_screen_pass"] = (
        primary is not None
        and baseline is not None
        and primary >= baseline
        and all(
            v["mean_visit_recall"] is not None and v["mean_visit_recall"] >= cfg["minimum_class_recall"]
            for v in result["prefix"]["10"]["classes"].values()
        )
    )
    result["primary_paired_difference"] = (
        primary - baseline if primary is not None and baseline is not None else None
    )
    return result
