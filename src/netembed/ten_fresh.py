"""Three frozen prospective visits. No training, calibration or capture startup."""

import json
import os
from pathlib import Path

from .browser_sessions import verify_fresh
from .bundle import Predictor, sha256, write_json
from .contract import Flow
from .live_policy import percentiles, timing_metrics
from .paired_study import check_order, read_archive, support, validate_archive_plan


def validate_continuation(cfg):
    binding = cfg.get("continuation")
    if not binding:
        return
    for path_key, hash_key in [
        ("prior_review", "prior_review_sha256"),
        ("delivery_report", "delivery_report_sha256"),
    ]:
        if sha256(binding[path_key]) != binding[hash_key]:
            raise ValueError("technical continuation evidence changed")
    if json.loads(Path(binding["prior_review"]).read_text())["status"] != "session_integrity_review_required":
        raise ValueError("interrupted scope is not preserved")
    if json.loads(Path(binding["delivery_report"]).read_text())["status"] != "single_delivery_check_pass":
        raise ValueError("delivery check did not pass")


def require_session_integrity(root):
    if (Path(root) / "session-integrity-review.json").exists():
        raise ValueError(
            "interrupted/restarted session requires integrity review; no replacement capture or prospective grading"
        )


def verify_single_session(intent, status):
    """Detect restarts, including sessions evicted from the bounded history."""
    before = set(intent["baseline_history_ids"])
    after = status["recent_sessions"]
    after_ids = {entry["session_id"] for entry in after}
    evicted = status["recent_sessions_evicted"] - intent["baseline_history_evictions"]
    newly_started = after_ids - before
    if (
        evicted < 0
        or evicted > len(before - after_ids)
        or len(newly_started) != 1
        or status.get("session_id") not in newly_started
    ):
        raise ValueError("session history is ambiguous or capture was started more than once")


def frozen_models(cfg):
    pair = {}
    specs = {
        "candidate": {
            "bundle": cfg["source_bundle"],
            "artifact_id": cfg["source_artifact_id"],
            "weight_sha256": cfg["source_weight_sha256"],
        },
        "control": cfg["control"],
    }
    for name, spec in specs.items():
        model = Predictor(spec["bundle"])
        if (
            model.identity != spec["artifact_id"]
            or sha256(Path(spec["bundle"]) / "forest.json") != spec["weight_sha256"]
            or model.meta["provenance"].get("fixture", True)
        ):
            raise ValueError("frozen genuine verification model differs")
        pair[name] = model
    candidate = pair["candidate"]
    if (
        candidate.fixed_prefix_packets != 10
        or candidate.meta["policy"] != cfg["expected_policy"]
        or candidate.meta["policy"]["fitted"]
    ):
        raise ValueError("verification requires the frozen uncalibrated fixed-ten contract")
    if pair["control"].labels != candidate.labels:
        raise ValueError("verification label maps differ")
    return pair


def offline_guard(event, args, root, cfg):
    if event in ("socket.connect", "socket.getaddrinfo"):
        raise ValueError("fresh scoring is offline")
    if event != "open" or not isinstance(args[0], (str, bytes)):
        return
    p = Path(os.fsdecode(args[0])).resolve()
    if p.is_relative_to(Path("data").resolve()):
        raise ValueError("training/calibration/final public data excluded")
    if p.is_relative_to(Path("artifacts/local").resolve()) and (
        not p.is_relative_to(Path(root).resolve()) or any(x.startswith("excluded-prior-") for x in p.parts)
    ):
        raise ValueError("old or unrelated private captures excluded")
    if p.is_relative_to(Path("experiments").resolve()) and not any(
        p.is_relative_to(Path(folder).resolve())
        for folder in [cfg["source_bundle"], cfg["control"]["bundle"]]
    ):
        raise ValueError("old experiment outcomes excluded")


def primary_metrics(records, cfg):
    result = {}
    rules = cfg["rules"]
    checks = {}
    for label in cfg["local_labels"]:
        rows = [r for r in records if r["reference"] == label and r["target"] == label]
        if len(rows) < cfg["minimum_target_at_10_per_trial"]:
            raise ValueError("primary support below frozen minimum")
        candidate = sum(r["candidate"]["top1"] == label for r in rows)
        control = sum(r["control"]["top1"] == label for r in rows)
        native = [r for r in rows if r["native"] is not None]
        native_correct = sum(r["native"]["alternatives"][0]["label"] == label for r in native)
        result[label] = {
            "eligible": len(rows),
            "candidate_correct": candidate,
            "control_correct": control,
            "candidate_recall": candidate / len(rows),
            "control_recall": control / len(rows),
            "native_emitted": len(native),
            "native_missing": len(rows) - len(native),
            "native_raw_correct": native_correct,
            "native_checkpoint_coverage": len(native) / len(rows),
            "native_end_to_end_raw_recall": native_correct / len(rows),
            "accepted_labels": sum(r["native"]["label"] is not None for r in native),
        }
        checks[label + "_raw_recall"] = (
            candidate / len(rows) + 1e-12 >= rules["minimum_candidate_target_recall"]
        )
        checks[label + "_no_loss"] = candidate >= control
        checks[label + "_native_recall"] = (
            native_correct / len(rows) + 1e-12 >= rules["minimum_native_end_to_end_raw_recall"]
        )
        checks[label + "_native_coverage"] = (
            len(native) / len(rows) + 1e-12 >= rules["minimum_native_checkpoint_coverage"]
        )
    checks["spotify_raw_gain"] = (
        result["spotify"]["candidate_correct"]
        >= result["spotify"]["control_correct"] + rules["minimum_spotify_correct_gain"]
    )
    return result, checks


def score_fresh(root, cfg, plan_path):
    root = Path(root)
    require_session_integrity(root)
    output = root / "comparison.json"
    if output.exists() or (root / "predictions.json").exists():
        raise FileExistsError("preserve frozen fresh score")
    models = frozen_models(cfg)
    reports, records, timings, bindings, seen = [], [], {}, {}, set()
    for spec in cfg["trials"]:
        trial = spec["id"]
        archive = read_archive(root, trial)
        validate_archive_plan(root, trial, archive, cfg)
        if archive["status"] != "usable" or archive["collection_role"] != "fresh_verification":
            raise ValueError("three usable fixed-role verification visits required")
        check_order(cfg, trial, reports, archive["first_packet_ms"], archive["session_id"])
        reports.append(archive)

        def load(name):
            p = root / (trial + "-" + name + ".json")
            if p.name not in archive["files"]:
                raise ValueError("required fresh evidence missing from archive")
            return json.loads(p.read_text())

        rows, capture, timing, audit, intent, proof = [
            load(n) for n in ["rows", "capture", "timing", "audit", "intent", "browser-processes"]
        ]
        if (
            capture["fixture"]
            or capture["source"] != "user_started_capture"
            or capture["artifact_id"] != cfg["source_artifact_id"]
            or audit["artifact_id"] != cfg["source_artifact_id"]
        ):
            raise ValueError("real frozen source required")
        if (
            any(v["session_id"] != archive["session_id"] for v in [capture, timing, audit, proof])
            or proof["plan_sha256"] != sha256(plan_path)
            or intent["collection_role"] != "fresh_verification"
            or intent["collection_plan_sha256"] != sha256(plan_path)
        ):
            raise ValueError("fresh role/session/browser binding differs")
        verify_fresh(proof["processes"], intent, archive["first_packet_ms"])
        replay = audit["original_live_prediction_comparison"]
        if replay["changed_decision_labels"] or replay["maximum_alternative_score_difference"] > 1e-6:
            raise ValueError("native source parity failed")
        support(rows, spec, cfg)
        originals = {r["flow_id"]: r for r in capture["flows"]}
        target_times = []
        for row in rows:
            if row["id"] in seen or not row["id"].startswith("browser:" + archive["session_id"] + ":"):
                raise ValueError("duplicate or wrong-session row")
            seen.add(row["id"])
            original = originals[row["id"].split(":")[-1]]
            if row["packets"] != original["packets"]:
                raise ValueError("measured packets changed")
            if row["label"] not in cfg["local_labels"] or len(row["packets"]) < 10:
                continue
            raw = Flow(packets=row["packets"]).array()[:10]
            emitted = [p for p in original["predictions"] if p["observed_packets"] == 10]
            if len(emitted) > 1:
                raise ValueError("duplicate native ten-packet checkpoint")
            native = emitted[0] if emitted else None
            expected = models["candidate"].predict(raw)
            if native:
                if (
                    native["model_packets"] != 10
                    or native["model_prefix_limit"] != 10
                    or native["artifact_id"] != cfg["source_artifact_id"]
                    or native["policy_fitted"]
                    or native["label"] is not None
                ):
                    raise ValueError("native fixed-ten unfitted contract differs")
                if (
                    native["alternatives"] != expected["alternatives"]
                    or native["status"] != expected["status"]
                ):
                    raise ValueError("native ten-packet scores do not replay")
                if row["label"] == spec["target"]:
                    target_times.append(native)
            point = {
                "trial": trial,
                "id": row["id"],
                "reference": row["label"],
                "target": spec["target"],
                "model_packets": 10,
                "native": native,
            }
            for name, model in models.items():
                probabilities = model.probabilities([raw])[0]
                point[name] = {
                    "top1": model.labels[int(probabilities.argmax())],
                    "probabilities": probabilities.tolist(),
                }
            records.append(point)
        timing_result = timing_metrics(timing, capture, audit)
        timing_result["target_native_ten_packet"] = {
            key: percentiles([p[key] for p in target_times])
            for key in ["pipeline_ms", "queue_ms", "capture_to_event_ms"]
        }
        timing_result["event_basis_note"] = (
            "All-event receipt samples include short no-score events and repeated first10 scores at later observed checkpoints. Target native10 processing/event times are separate; browser receipt is not paint."
        )
        timings[trial] = timing_result
        bindings[trial] = sha256(root / (trial + "-archive.json"))
    metrics, checks = primary_metrics(records, cfg)
    operational = all(v["operational_screen_pass"] for v in timings.values())
    write_json(root / "predictions.json", records)
    write_json(
        output,
        {
            "fixture": False,
            "status": "small_fresh_raw_and_delivery_pass"
            if all(checks.values()) and operational
            else "fresh_screen_failed_stop",
            "plan_sha256": sha256(plan_path),
            "artifact_id": cfg["source_artifact_id"],
            "metrics": metrics,
            "model_and_native_gates": checks,
            "operational_screen_pass": operational,
            "timing": timings,
            "archives": bindings,
            "reference_inventories": {r["trial_id"]: r["reference_inventory"] for r in reports},
            "prediction_sha256": sha256(root / "predictions.json"),
            "source_sha256": sha256(__file__),
            "policy_fitted": False,
            "default_promoted": False,
            "limits": cfg["limits"],
        },
    )
    return output
