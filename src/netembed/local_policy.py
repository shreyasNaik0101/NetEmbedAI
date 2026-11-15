"""Fixed local forest policy calibration and separately sealed final evaluation."""

import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

from .browser_calibration import write_policy_bundle
from .bundle import Predictor, sha256, write_json
from .contract import Flow
from .data import read_split
from .paired_study import check_order, read_archive, validate_archive_plan


def candidate(cfg):
    spec = cfg["candidate"]
    if sha256(spec["metadata"]["path"]) != spec["metadata"]["sha256"]:
        raise ValueError("frozen forest metadata changed")
    model = Predictor(spec["bundle"])
    if (
        model.identity != spec["metadata"]["sha256"]
        or model.meta["kind"] != "forest"
        or model.meta["policy"]["fitted"]
    ):
        raise ValueError("requires the declared uncalibrated forest")
    if sha256(Path(spec["bundle"]) / "forest.json") != cfg["candidate_weight_sha256"]:
        raise ValueError("forest weights changed")
    return model


def calibration_guard(event, args):
    if event == "open" and isinstance(args[0], (str, bytes)):
        path = str(args[0]).replace("\\", "/").lower()
        if any(
            s in path
            for s in (
                "-eval-",
                "browser-development",
                "prospective-paired-",
                "/test.jsonl",
                "/train.jsonl",
                "/selection.jsonl",
            )
        ):
            raise ValueError("final, training and earlier local study inputs excluded from policy fitting")
    if event in ("socket.connect", "socket.getaddrinfo"):
        raise ValueError("policy fitting is offline")


def stats(records, threshold):
    if not records:
        return {"n": 0, "accepted": 0, "errors": 0, "coverage": 0.0, "error": None}
    accepted = [r for r in records if max(r["probabilities"]) >= threshold]
    errors = sum(r["top1"] != r["reference"] for r in accepted)
    return {
        "n": len(records),
        "accepted": len(accepted),
        "errors": errors,
        "coverage": len(accepted) / len(records),
        "error": errors / len(accepted) if accepted else None,
    }


def local_check(records, threshold, cfg):
    rules = cfg["policy_rules"]
    overall = stats(records, threshold)
    classes, primary = {}, {}
    for label in cfg["local_labels"]:
        classes[label] = stats([r for r in records if r["reference"] == label], threshold)
        primary[label] = stats(
            [r for r in records if r["reference"] == label and r["budget"] == 10], threshold
        )

    def valid(s):
        return (
            s["accepted"] > 0
            and s["coverage"] >= rules["minimum_coverage"]
            and s["error"] <= rules["maximum_empirical_error"]
        )

    eligible = (
        valid(overall)
        and all(valid(s) for s in classes.values())
        and all(
            s["accepted"] >= rules["minimum_accepted_primary_per_class"] and valid(s)
            for s in primary.values()
        )
    )
    return {"overall": overall, "classes": classes, "primary": primary, "eligible": bool(eligible)}


def select_policy(local, public, labels, cfg):
    for rows in (local, public):
        if not rows or len({(r["id"], r["budget"]) for r in rows}) != len(rows):
            raise ValueError("empty or duplicated policy cases")
        for r in rows:
            p = np.asarray(r["probabilities"])
            if (
                p.shape != (len(labels),)
                or not np.isfinite(p).all()
                or (p < 0).any()
                or not np.isclose(p.sum(), 1)
                or r["reference"] not in labels
                or r["top1"] != labels[int(p.argmax())]
                or r["budget"] not in cfg["policy_rules"]["budgets"]
            ):
                raise ValueError("invalid policy probabilities/labels/budgets")
    curve = []
    rules = cfg["policy_rules"]
    for step in range(101):
        threshold = step / 100
        loc = local_check(local, threshold, cfg)
        pub = stats(public, threshold)
        per_class = {
            label: stats([r for r in public if r["reference"] == label], threshold) for label in labels
        }
        eligible = (
            loc["eligible"]
            and pub["accepted"] >= rules["minimum_accepted_public_overall"]
            and pub["error"] <= rules["maximum_empirical_error"]
            and all(
                s["accepted"] >= rules["minimum_accepted_public_per_class"]
                and s["error"] <= rules["maximum_empirical_error"]
                for s in per_class.values()
            )
        )
        curve.append(
            {
                "threshold": threshold,
                "local": loc,
                "public": pub,
                "public_classes": per_class,
                "eligible": bool(eligible),
            }
        )
    selected = next((r for r in curve if r["eligible"]), None)
    policy = {
        "version": "local-forest-policy-v1",
        "fitted": selected is not None,
        "threshold": selected["threshold"] if selected else 1.0,
        "min_packets": 10,
        "temperature": 1.0,
        "locally_checked_labels": cfg["local_labels"],
        "tie_break": "label_order",
        "note": "Empirical threshold on correlated calibration prefixes; scores are not calibrated correctness probabilities. No population risk/unknown-service guarantee.",
    }
    return policy, selected, curve


def load_role(root, cfg, role):
    root = Path(root)
    reports, records, bindings, ids, sessions = [], [], {}, set(), set()
    for spec in cfg["trials"]:
        if role == "calibration" and spec["role"] != role:
            break  # Do not open final archives or even their rows during fitting.
        report = read_archive(root, spec["id"])
        validate_archive_plan(root, spec["id"], report, cfg)
        if report["status"] != "usable":
            raise ValueError("unusable attempt stops calibration/final workflow")
        if report.get("collection_role") != spec["role"]:
            raise ValueError("archived calibration/final role differs from declaration")
        check_order(cfg, spec["id"], reports, report["first_packet_ms"], report["session_id"])
        reports.append(report)
        if report["session_id"] in sessions:
            raise ValueError("reused session")
        sessions.add(report["session_id"])
        if spec["role"] == role:
            rows = json.loads((root / (spec["id"] + "-rows.json")).read_text())
            bindings[spec["id"]] = sha256(root / (spec["id"] + "-archive.json"))
            for row in rows:
                if row["id"] in ids:
                    raise ValueError("duplicated flow")
                ids.add(row["id"])
                if row["label"] in cfg["local_labels"]:
                    records.append({**row, "trial": spec["id"]})
    if len(bindings) != 2:
        raise ValueError("both declared role visits required")
    return records, bindings


def predictions(model, rows, cfg):
    result = []
    for row in rows:
        raw = Flow(packets=row["packets"]).array()
        for budget in cfg["policy_rules"]["budgets"]:
            if len(raw) >= budget:
                p = model.probabilities([raw[:budget]])[0]
                result.append(
                    {
                        "id": row["id"],
                        "reference": row["label"],
                        "budget": budget,
                        "top1": model.labels[int(p.argmax())],
                        "probabilities": p.tolist(),
                    }
                )
    return result


def frozen_policy(root, cfg, first_ms=None):
    root = Path(root)
    decision = json.loads((root / "calibration-decision.json").read_text())
    if not decision["policy"]["fitted"]:
        raise ValueError("no eligible calibration policy; final collection/evaluation stopped")
    if decision["candidate_id"] != cfg["candidate"]["metadata"]["sha256"]:
        raise ValueError("candidate choice changed")
    if decision["plan"] != cfg:
        raise ValueError("calibration declaration changed")
    for name, key in (
        ("calibration-local-predictions.json", "local_prediction_sha256"),
        ("calibration-public-predictions.json", "public_prediction_sha256"),
        ("calibration-curve.json", "curve_sha256"),
    ):
        if sha256(root / name) != decision[key]:
            raise ValueError("calibration outputs changed after freeze")
    if (
        first_ms is not None
        and first_ms <= datetime.fromisoformat(decision["frozen_at_utc"]).timestamp() * 1000
    ):
        raise ValueError("final capture must start after policy freeze")
    for trial, digest in decision["calibration_archives"].items():
        read_archive(root, trial)
        if sha256(root / (trial + "-archive.json")) != digest:
            raise ValueError("calibration archive changed after freeze")
    bundle = root / "policy-bundle"
    model = Predictor(bundle)
    original = candidate(cfg)
    if (
        model.identity != decision["policy_artifact_id"]
        or model.meta["policy"] != decision["policy"]
        or sha256(bundle / "forest.json") != cfg["candidate_weight_sha256"]
        or model.normalizer.metadata() != original.normalizer.metadata()
        or model.labels != original.labels
    ):
        raise ValueError("frozen policy bundle changed")
    return model, decision


def fit(root, cfg, data):
    root = Path(root)
    if (root / "calibration-decision.json").exists() or (root / "policy-bundle").exists():
        raise FileExistsError("preserve existing calibration output")
    model = candidate(cfg)
    rows, bindings = load_role(root, cfg, "calibration")
    local = predictions(model, rows, cfg)
    if sha256(Path(data) / "manifest.json") != cfg["public_manifest_sha256"]:
        raise ValueError("public calibration manifest changed")
    flows, y, ids, manifest = read_split(data, "calibration")
    if manifest["labels"] != model.labels:
        raise ValueError("public label order differs")
    counts, public_rows = {}, []
    for raw, target, ident in zip(flows, y, ids):
        label = model.labels[int(target)]
        if len(raw) >= 10 and counts.get(label, 0) < cfg["policy_rules"]["public_flows_per_class"]:
            public_rows.append(
                {"id": ident, "label": label, "packets": Flow.from_array(raw).model_dump()["packets"]}
            )
            counts[label] = counts.get(label, 0) + 1
    if any(counts.get(label) != cfg["policy_rules"]["public_flows_per_class"] for label in model.labels):
        raise ValueError("insufficient public calibration support")
    public = predictions(model, public_rows, cfg)
    policy, selected, curve = select_policy(local, public, model.labels, cfg)
    write_json(root / "calibration-local-predictions.json", local)
    write_json(root / "calibration-public-predictions.json", public)
    write_json(root / "calibration-curve.json", curve)
    proof = {
        "candidate_id": model.identity,
        "plan": cfg,
        "calibration_archives": bindings,
        "fixture": bool(model.meta["provenance"].get("fixture", False)),
        "source_commit": subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
        "source_sha256": sha256(__file__),
        "local_prediction_sha256": sha256(root / "calibration-local-predictions.json"),
        "public_prediction_sha256": sha256(root / "calibration-public-predictions.json"),
        "curve_sha256": sha256(root / "calibration-curve.json"),
        "public_control": "historical retrospective diagnostic only",
    }
    artifact = None
    if policy["fitted"]:
        write_policy_bundle(cfg["candidate"]["bundle"], root / "policy-bundle", policy, proof)
        artifact = sha256(root / "policy-bundle/metadata.json")
    decision = {
        **proof,
        "policy": policy,
        "selected": selected,
        "policy_artifact_id": artifact,
        "frozen_at_utc": datetime.now(timezone.utc).isoformat(),
        "default_promoted": False,
    }
    write_json(root / "calibration-decision.json", decision)
    return decision


def evaluate(root, cfg):
    root = Path(root)
    if (root / "final-report.json").exists():
        raise FileExistsError("final evaluation already frozen")
    model, decision = frozen_policy(root, cfg)
    rows, bindings = load_role(root, cfg, "final")
    for spec in cfg["trials"]:
        if spec["role"] == "final":
            report = read_archive(root, spec["id"])
            frozen_policy(root, cfg, report["first_packet_ms"])
    values = predictions(model, rows, cfg)
    result = local_check(values, decision["policy"]["threshold"], cfg)
    write_json(root / "final-predictions.json", values)
    report = {
        "policy_artifact_id": model.identity,
        "threshold": decision["policy"]["threshold"],
        "fixture": decision["fixture"],
        "metrics": result,
        "final_archives": bindings,
        "calibration_decision_sha256": sha256(root / "calibration-decision.json"),
        "prediction_sha256": sha256(root / "final-predictions.json"),
        "default_promoted": False,
        "limits": cfg["limits"],
    }
    write_json(root / "final-report.json", report)
    return report
