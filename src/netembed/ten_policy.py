"""Role-bound, first-ten-packet acceptance policy; never starts capture."""

from datetime import datetime, timezone
import json
import os
from pathlib import Path

import numpy as np

from .browser_calibration import write_policy_bundle
from .bundle import Predictor, sha256
from .contract import Flow
from .paired_study import check_order, read_archive, validate_archive_plan
from .ten_fresh import require_session_integrity

ROOT = Path("artifacts/local/ten-packet-policy-v1")
PLAN = Path("configs/ten-packet-policy-v1.json")


def write_once(path, value):
    with Path(path).open("x", encoding="utf-8") as stream:
        json.dump(value, stream, indent=2, allow_nan=False)


def prerequisites(cfg):
    for path, digest in cfg["prerequisites"].items():
        if sha256(path) != digest:
            raise ValueError("policy prerequisite changed")
    prior = json.loads(Path(cfg["verification_report"]).read_text())
    if (
        prior["status"] != "small_fresh_raw_and_delivery_pass"
        or prior["artifact_id"] != cfg["source_artifact_id"]
    ):
        raise ValueError("frozen raw verification did not pass")


def candidate(cfg):
    model = Predictor(cfg["source_bundle"])
    if (
        model.identity != cfg["source_artifact_id"]
        or model.labels != cfg["labels"]
        or model.fixed_prefix_packets != 10
        or model.meta["policy"]["fitted"]
        or model.meta["provenance"].get("fixture", True)
        or sha256(Path(cfg["source_bundle"]) / "forest.json") != cfg["source_weight_sha256"]
    ):
        raise ValueError("frozen genuine ten-packet source differs")
    return model


def offline_guard(event, args, root, cfg, role):
    if event in ("socket.connect", "socket.getaddrinfo"):
        raise ValueError("policy fitting/evaluation is offline")
    if event != "open" or not isinstance(args[0], (str, bytes)):
        return
    path = Path(os.fsdecode(args[0])).resolve()
    if path.is_relative_to(Path("data").resolve()):
        raise ValueError("public training/calibration/test data excluded")
    if path.is_relative_to(Path("artifacts/local").resolve()):
        allowed = path.is_relative_to(Path(root).resolve()) and not any(
            name.startswith("excluded-prior-") for name in path.parts
        )
        if not allowed or (role == "calibration" and path.name.startswith("ten-policy-final-")):
            raise ValueError("old, verification or final capture excluded from fitting")
    if path.is_relative_to(Path("experiments").resolve()) and not path.is_relative_to(
        Path(cfg["source_bundle"]).resolve()
    ):
        raise ValueError("unrelated model or experiment excluded")


def frozen_policy(root, cfg, first_ms=None):
    root = Path(root)
    freeze = json.loads((root / "policy-freeze.json").read_text())
    if sha256(root / "calibration-decision.json") != freeze["decision_sha256"]:
        raise ValueError("calibration decision changed after freeze")
    decision = json.loads((root / "calibration-decision.json").read_text())
    if decision["plan_sha256"] != sha256(root / PLAN.name) or not decision["policy"]["fitted"]:
        raise ValueError("no eligible policy for this plan; final collection stopped")
    for name, digest in decision["files"].items():
        if Path(name).name != name or sha256(root / name) != digest:
            raise ValueError("calibration output changed")
    for trial, digest in decision["archives"].items():
        read_archive(root, trial)
        if sha256(root / (trial + "-archive.json")) != digest:
            raise ValueError("calibration archive changed")
    model = Predictor(root / "policy-bundle")
    base = candidate(cfg)
    if (
        model.identity != decision["policy_artifact_id"]
        or model.meta["policy"] != decision["policy"]
        or model.labels != base.labels
        or model.meta["architecture"] != base.meta["architecture"]
        or model.normalizer.metadata() != base.normalizer.metadata()
        or sha256(root / "policy-bundle/forest.json") != cfg["source_weight_sha256"]
    ):
        raise ValueError("frozen policy bundle differs")
    if (
        first_ms is not None
        and first_ms <= datetime.fromisoformat(freeze["frozen_at_utc"]).timestamp() * 1000
    ):
        raise ValueError("final session must follow policy freeze")
    return model, decision


def source_for(root, cfg, trial, now_ms):
    if Path(root).resolve() != ROOT.resolve():
        raise ValueError("use the declared policy collection root")
    prerequisites(cfg)
    require_session_integrity(root)
    spec = next(s for s in cfg["trials"] if s["id"] == trial)
    source = dict(cfg)
    if spec["role"] == "final":
        model, _ = frozen_policy(root, cfg, now_ms)
        source.update(
            source_bundle=str(Path(root) / "policy-bundle"),
            source_artifact_id=model.identity,
            policy_decision_sha256=sha256(Path(root) / "calibration-decision.json"),
        )
    else:
        candidate(cfg)
    return source


def summarize(records, threshold, cfg, native=False):
    def stats(rows):
        accepted = []
        for row in rows:
            if native:
                label = row["native"]["label"] if row["native"] else None
            else:
                label = (
                    row["top1"]
                    if row["top1"] in cfg["local_labels"] and max(row["probabilities"]) >= threshold
                    else None
                )
            if label is not None:
                accepted.append(label == row["reference"])
        return {
            "n": len(rows),
            "accepted": len(accepted),
            "errors": len(accepted) - sum(accepted),
            "coverage": len(accepted) / len(rows) if rows else 0,
            "accepted_error": 1 - sum(accepted) / len(accepted) if accepted else None,
        }

    primary = {
        label: stats([r for r in records if r["target"] == label and r["reference"] == label])
        for label in cfg["local_labels"]
    }
    overall = stats(records)
    rules = cfg["policy_rules"]
    eligible = all(
        s["n"] >= cfg["minimum_target_at_10_per_trial"]
        and s["accepted"] >= rules["minimum_accepted_per_service"]
        and s["coverage"] >= rules["minimum_coverage"]
        and s["accepted_error"] is not None
        and s["accepted_error"] <= rules["maximum_primary_error"]
        for s in primary.values()
    )
    eligible = (
        eligible
        and overall["accepted_error"] is not None
        and overall["accepted_error"] <= rules["maximum_overall_error"]
    )
    return {"primary": primary, "overall": overall, "eligible": bool(eligible)}


def select_policy(records, cfg):
    if not records or len({r["id"] for r in records}) != len(records):
        raise ValueError("empty or duplicated calibration flows")
    for row in records:
        scores = np.asarray(row["probabilities"])
        if (
            scores.shape != (len(cfg["labels"]),)
            or not np.isfinite(scores).all()
            or (scores < 0).any()
            or not np.isclose(scores.sum(), 1)
            or row["reference"] not in cfg["labels"]
            or row["top1"] != cfg["labels"][int(scores.argmax())]
        ):
            raise ValueError("invalid calibration scores or labels")
    curve = [{"threshold": step / 100, **summarize(records, step / 100, cfg)} for step in range(101)]
    selected = next((point for point in curve if point["eligible"]), None)
    policy = {
        "version": "ten-packet-local-acceptance-v1",
        "fitted": selected is not None,
        "threshold": selected["threshold"] if selected else 1.0,
        "min_packets": 10,
        "temperature": 1.0,
        "tie_break": "label_order",
        "accepted_labels": cfg["local_labels"],
        "locally_checked_labels": cfg["local_labels"],
        "validation_scope": "three_service_local_calibration_only",
        "note": "Empirical acceptance threshold on correlated local flows; model scores are not correctness probabilities. No unknown-service or network-transfer guarantee.",
    }
    return policy, selected, curve


def role_records(root, cfg, role, model):
    root = Path(root)
    reports, records, bindings, seen = [], [], {}, set()
    for spec in cfg["trials"]:
        if role == "calibration" and spec["role"] != role:
            break  # Do not even open final archives during fitting.
        report = read_archive(root, spec["id"])
        validate_archive_plan(root, spec["id"], report, cfg)
        if report["status"] != "usable" or report["collection_role"] != spec["role"]:
            raise ValueError("usable role-bound archives required; no replacements")
        check_order(cfg, spec["id"], reports, report["first_packet_ms"], report["session_id"])
        reports.append(report)
        if spec["role"] != role:
            continue
        if role == "final":
            frozen_policy(root, cfg, report["first_packet_ms"])
        trial = spec["id"]
        cap = json.loads((root / (trial + "-capture.json")).read_text())
        status = json.loads((root / (trial + "-status.json")).read_text())
        timing = json.loads((root / (trial + "-timing.json")).read_text())
        if (
            cap["fixture"]
            or cap["source"] != "user_started_capture"
            or cap["evidence_evicted"]
            or cap["counters"]["drops"]
            or status["running"]
            or status["reason"] not in ("stopped by user", "capture duration limit reached")
            or timing["receipt_tracking_pending"]["prediction"]
            or timing["receipt_tracking_evicted"]["prediction"]
        ):
            raise ValueError("uninterrupted zero-drop delivery required; scope stopped")
        originals = {r["flow_id"]: r for r in cap["flows"]}
        rows = json.loads((root / (trial + "-rows.json")).read_text())
        for row in rows:
            if row["id"] in seen or not row["id"].startswith("browser:" + report["session_id"] + ":"):
                raise ValueError("duplicated or wrong-session row")
            seen.add(row["id"])
            original = originals[row["id"].split(":")[-1]]
            if row["packets"] != original["packets"]:
                raise ValueError("reference packets differ")
            if len(row["packets"]) < 10:
                continue
            raw = Flow(packets=row["packets"]).array()[:10]
            scores = model.probabilities([raw])[0]
            native = [r for r in original["predictions"] if r["observed_packets"] == 10]
            if len(native) > 1:
                raise ValueError("duplicate native checkpoint")
            actual = native[0] if native else None
            expected = model.predict(raw)
            if actual and any(
                actual[key] != expected[key]
                for key in (
                    "artifact_id",
                    "alternatives",
                    "status",
                    "label",
                    "model_packets",
                    "policy_fitted",
                )
            ):
                raise ValueError("native ten-packet inference does not replay")
            records.append(
                {
                    "id": row["id"],
                    "trial": trial,
                    "target": spec["target"],
                    "reference": row["label"],
                    "top1": model.labels[int(scores.argmax())],
                    "probabilities": scores.tolist(),
                    "native": actual,
                }
            )
        bindings[trial] = sha256(root / (trial + "-archive.json"))
    if len(bindings) != 3:
        raise ValueError("all three declared visits for this role required")
    for label in cfg["local_labels"]:
        primary = [r for r in records if r["target"] == label and r["reference"] == label]
        if (
            len(primary) < cfg["minimum_target_at_10_per_trial"]
            or sum(r["native"] is not None for r in primary) / len(primary) < cfg["minimum_native_coverage"]
        ):
            raise ValueError("primary support or native checkpoint coverage failed")
    return records, bindings


def fit(root, cfg):
    root = Path(root)
    require_session_integrity(root)
    if (root / "calibration-decision.json").exists() or (root / "calibration-predictions.json").exists():
        raise FileExistsError("calibration already attempted; preserve its result")
    model = candidate(cfg)
    records, bindings = role_records(root, cfg, "calibration", model)
    policy, selected, curve = select_policy(records, cfg)
    write_once(root / "calibration-predictions.json", records)
    write_once(root / "calibration-curve.json", curve)
    proof = {
        "source_artifact_id": model.identity,
        "plan_sha256": sha256(root / PLAN.name),
        "archives": bindings,
        "weights_refitted": False,
        "normalization_refitted": False,
    }
    artifact = None
    if policy["fitted"]:
        write_policy_bundle(cfg["source_bundle"], root / "policy-bundle", policy, proof)
        artifact = Predictor(root / "policy-bundle").identity
    decision = {
        **proof,
        "fixture": False,
        "policy": policy,
        "selected": selected,
        "policy_artifact_id": artifact,
        "source_sha256": sha256(__file__),
        "files": {
            name: sha256(root / name) for name in ["calibration-predictions.json", "calibration-curve.json"]
        },
        "status": "policy_frozen_for_final_only" if policy["fitted"] else "calibration_failed_stop",
        "default_promoted": False,
    }
    write_once(root / "calibration-decision.json", decision)
    write_once(
        root / "policy-freeze.json",
        {
            "decision_sha256": sha256(root / "calibration-decision.json"),
            "frozen_at_utc": datetime.now(timezone.utc).isoformat(),
        },
    )
    return decision


def evaluate(root, cfg):
    root = Path(root)
    require_session_integrity(root)
    if (root / "final-report.json").exists() or (root / "final-predictions.json").exists():
        raise FileExistsError("final evaluation already attempted")
    model, decision = frozen_policy(root, cfg)
    records, bindings = role_records(root, cfg, "final", model)
    offline = summarize(records, decision["policy"]["threshold"], cfg)
    native = summarize(records, decision["policy"]["threshold"], cfg, native=True)
    report = {
        "fixture": False,
        "status": "small_local_accepted_screen_pass"
        if offline["eligible"] and native["eligible"]
        else "final_failed_stop",
        "offline": offline,
        "native": native,
        "policy_artifact_id": model.identity,
        "decision_sha256": sha256(root / "calibration-decision.json"),
        "archives": bindings,
        "default_promoted": False,
        "limits": cfg["limits"],
    }
    write_once(root / "final-predictions.json", records)
    report["predictions_sha256"] = sha256(root / "final-predictions.json")
    write_once(root / "final-report.json", report)
    return report
