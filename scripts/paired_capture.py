"""Prepare, archive and score four deliberate user-started prospective sessions."""

import argparse
import json
import subprocess
import sys
import time
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import torch
from threadpoolctl import threadpool_limits

from collect_browser import get, json_once, validate_snapshot, write_once, REPO
from netembed.browser_collection import eligible_references, observed_packet_bounds
from netembed.bundle import Predictor, sha256
from netembed.contract import Flow
from netembed.linear_probe import WHEEL, WHEEL_SHA
from netembed.netlog_stream import read_quic_reference_stream
from netembed.paired_study import (
    check_order,
    collection_status,
    read_archive,
    read_plan,
    summarize,
    support,
    validate_archive_plan,
)
from netembed.prefix_probe import PrefixProbe


def models(cfg):
    if cfg.get("workflow") == "ten_packet_policy":
        model = Predictor(cfg["source_bundle"])
        if (
            model.identity != cfg["source_artifact_id"]
            or model.fixed_prefix_packets != 10
            or model.meta["provenance"].get("fixture", True)
        ):
            raise ValueError("declared ten-packet policy source differs")
        return {"source": model}
    if cfg.get("workflow") == "ten_packet_fresh":
        from netembed.ten_fresh import frozen_models

        return frozen_models(cfg)
    if cfg.get("workflow") == "spotify_data_repair":
        model = Predictor(cfg["source_bundle"])
        if model.identity != cfg["source_artifact_id"] or model.meta["provenance"].get("fixture", True):
            raise ValueError("declared Spotify collection source differs")
        return {"source": model}
    if cfg.get("workflow") == "live_policy_validation":
        from netembed.live_policy import load_model

        return {"forest": load_model(cfg)}
    if cfg.get("workflow") == "ipv6_frozen_evaluation":
        from netembed.fresh_evaluation import frozen_models

        return frozen_models(cfg)
    if cfg.get("workflow") in ("calibrate_then_final", "family_development"):
        from netembed.local_policy import candidate

        return {"forest": candidate(cfg)}
    for spec in cfg["models"].values():
        if sha256(spec["metadata"]["path"]) != spec["metadata"]["sha256"]:
            raise ValueError("frozen candidate metadata changed")
        if Path(spec["metadata"]["path"]) != Path(spec["bundle"]) / "metadata.json":
            raise ValueError("model path differs")
    wheel = Path(cfg["models"]["prefix"]["bundle"]) / "base" / WHEEL
    if sha256(wheel) != WHEEL_SHA:
        raise ValueError("pinned optional wheel changed")
    sys.path.insert(0, str(wheel.resolve()))
    pair = {
        "prefix": PrefixProbe.load(cfg["models"]["prefix"]["bundle"]),
        "forest": Predictor(cfg["models"]["forest"]["bundle"]),
    }
    if pair["prefix"].labels != pair["forest"].labels:
        raise ValueError("candidate labels differ")
    return pair


def previous(root, cfg, trial):
    index = [s["id"] for s in cfg["trials"]].index(trial)
    reports = []
    for spec in cfg["trials"][:index]:
        report = read_archive(root, spec["id"])
        validate_archive_plan(root, spec["id"], report, cfg)
        reports.append(report)
    return reports


def prepare(args, root, cfg, plan_path):
    if cfg.get("workflow") == "ten_packet_policy":
        from netembed.ten_policy import source_for

        cfg = source_for(root, cfg, args.trial, time.time() * 1000)
    if cfg.get("workflow") == "ten_packet_fresh":
        from netembed.ten_fresh import require_session_integrity, validate_continuation

        validate_continuation(cfg)
        require_session_integrity(root)
    if cfg.get("workflow") == "spotify_data_repair":
        from netembed.spotify_repair import source_for

        cfg = source_for(root, cfg, args.trial, time.time() * 1000)
    if cfg.get("service_url") and args.service.rstrip("/") != cfg["service_url"]:
        raise ValueError("use the declared validation service URL")
    if cfg.get("network_context") and cfg.get("workflow") not in (
        "spotify_data_repair",
        "ten_packet_fresh",
        "ten_packet_policy",
    ):
        context = cfg["network_context"]
        if sha256(context["connectivity_report"]) != context["connectivity_report_sha256"]:
            raise ValueError("declared network connectivity evidence changed")
    spec = next(s for s in cfg["trials"] if s["id"] == args.trial)
    target = root / f"{args.trial}-intent.json"
    if (root / f"{args.trial}-attempt.json").exists():
        raise ValueError("attempt already consumed; archive it, do not record a replacement")
    if target.exists():
        intent = json.loads(target.read_text())
        if intent["collection_plan_sha256"] != sha256(plan_path):
            raise ValueError("intent protocol changed")
        print(json.dumps({"stage": "already_prepared", "netlog": intent["netlog_file"]}))
        return
    check_order(cfg, args.trial, previous(root, cfg, args.trial), time.time() * 1000)
    if cfg.get("workflow") == "family_development" and spec["role"] == "selection":
        from netembed.family_collection import selection_ready

        selection_ready(root, cfg, plan_path)
    if cfg.get("workflow") == "calibrate_then_final" and spec["role"] == "final":
        from netembed.local_policy import frozen_policy

        frozen_policy(root, cfg, time.time() * 1000)
    pair = models(cfg)
    del pair
    status = json.loads(get(args.service, "/capture/status"))
    if status["running"]:
        raise ValueError("stop capture before preparation")
    current = json.loads(get(args.service, "/model"))
    if current["artifact_id"] != cfg["source_artifact_id"]:
        raise ValueError("source app model changed")
    source = Predictor(cfg["source_bundle"])
    if source.identity != current["artifact_id"]:
        raise ValueError("source audit bundle differs")
    interfaces = json.loads(get(args.service, "/capture/interfaces"))
    if not any(r["id"] == cfg["interface"] for r in interfaces):
        raise ValueError("declared Wi-Fi interface unavailable")
    if status.get("session_id"):
        # Preserve currently stopped, unassigned evidence before the user starts
        # a fresh session. Never score it as a prospective visit.
        prior = root / ("excluded-prior-" + status["session_id"])
        if not prior.exists():
            prior.mkdir()
            for name, route in (
                ("status", "/capture/status"),
                ("capture", "/capture/local-evaluation"),
                ("timing", "/capture/summary"),
            ):
                write_once(prior / (name + ".json"), get(args.service, route))
    netlog = root / f"{args.trial}-netlog.json"
    if netlog.exists():
        raise ValueError("unbound log exists; preserve it and stop")
    browser_fields = {}
    if cfg.get("scope") in ("session_acquisition_only", "fresh_evaluation_only"):
        from netembed.browser_sessions import chrome_inventory, require_closed

        require_closed(chrome_inventory())
        browser_fields = {
            "chrome_closed_before_intent": True,
            "browser_session_policy": cfg["browser_session_policy"],
        }
    intent = {
        "trial_id": args.trial,
        "collection_role": spec.get("role", "prospective_comparison"),
        "collection_plan_sha256": sha256(plan_path),
        "recorded_before_capture_utc": datetime.now(timezone.utc).isoformat(),
        "expected_artifact_id": cfg["source_artifact_id"],
        "expected_adapter": "tshark-prefix-ns-v3",
        "selected_interface_id": cfg["interface"],
        "previous_session_excluded": status.get("session_id"),
        "netlog_file": str(netlog.resolve()),
        "source_bundle": str(Path(cfg["source_bundle"]).resolve()),
        "activity": spec["activity"],
        "capture_user_started_required": True,
        **browser_fields,
        **(
            {"policy_decision_sha256": cfg["policy_decision_sha256"]}
            if cfg.get("policy_decision_sha256")
            else {}
        ),
        **(
            {
                "baseline_history_ids": [r["session_id"] for r in status["recent_sessions"]],
                "baseline_history_evictions": status["recent_sessions_evicted"],
            }
            if cfg.get("continuation") or cfg.get("workflow") == "ten_packet_policy"
            else {}
        ),
        **(
            {"network_context": cfg["network_context"], "scope": cfg["scope"]}
            if cfg.get("network_context")
            else {}
        ),
    }
    json_once(target, intent)
    print(json.dumps({"stage": "prepared_not_capturing", "intent": intent}, indent=2))


def archive(args, root, cfg, plan_path):
    if cfg.get("workflow") == "ten_packet_policy":
        from netembed.ten_policy import source_for

        cfg = source_for(root, cfg, args.trial, time.time() * 1000)
    if cfg.get("workflow") == "ten_packet_fresh":
        from netembed.ten_fresh import require_session_integrity, validate_continuation

        validate_continuation(cfg)
        require_session_integrity(root)
    if cfg.get("workflow") == "spotify_data_repair":
        cfg = {
            **cfg,
            "require_zero_drops": next(s for s in cfg["trials"] if s["id"] == args.trial)["role"]
            == "evaluation",
        }
    if cfg.get("expanded_netlog_required") and not getattr(args, "expanded_netlog", False):
        raise ValueError("this scope requires --expanded-netlog; preserve the same capture")

    def file(name):
        return root / f"{args.trial}-{name}.json"

    spec = next(s for s in cfg["trials"] if s["id"] == args.trial)
    if file("archive").exists():
        print(json.dumps(read_archive(root, args.trial)))
        return
    intent = json.loads(file("intent").read_text())
    if cfg.get("workflow") == "ten_packet_policy" and intent.get("policy_decision_sha256") != cfg.get(
        "policy_decision_sha256"
    ):
        raise ValueError("bound policy decision changed")
    if intent["collection_plan_sha256"] != sha256(plan_path) or intent["trial_id"] != args.trial:
        raise ValueError("intent changed")
    if intent.get("collection_role", "prospective_comparison") != spec.get("role", "prospective_comparison"):
        raise ValueError("pre-capture role differs from the declared slot")
    if cfg.get("network_context") and intent.get("network_context") != cfg["network_context"]:
        raise ValueError("declared network context changed")
    if not file("attempt").exists():
        status = json.loads(get(args.service, "/capture/status"))
        if (
            status["running"]
            or not status.get("session_id")
            or status["session_id"] == intent["previous_session_excluded"]
        ):
            raise ValueError("a new stopped user session is required")
        if cfg.get("continuation") or cfg.get("workflow") == "ten_packet_policy":
            from netembed.ten_fresh import verify_single_session

            try:
                verify_single_session(intent, status)
            except (ValueError, KeyError) as error:
                for name, route in (
                    ("status", "/capture/status"),
                    ("capture", "/capture/local-evaluation"),
                    ("timing", "/capture/summary"),
                ):
                    write_once(file("integrity-" + name), get(args.service, route))
                json_once(
                    root / "session-integrity-review.json",
                    {
                        "status": "session_integrity_review_required",
                        "trial_id": args.trial,
                        "reason": str(error),
                        "replacement_capture": False,
                    },
                )
                raise ValueError("capture history requires integrity review; evidence preserved") from error
        for name, route in (
            ("capture", "/capture/local-evaluation"),
            ("timing", "/capture/summary"),
            ("status", "/capture/status"),
        ):
            write_once(file(name), get(args.service, route))
        json_once(
            file("attempt"),
            {
                "session_id": status["session_id"],
                "plan_sha256": sha256(plan_path),
                "files": {file(n).name: sha256(file(n)) for n in ("capture", "timing", "status")},
            },
        )
    attempt = json.loads(file("attempt").read_text())
    if attempt["plan_sha256"] != sha256(plan_path) or any(
        sha256(root / n) != h for n, h in attempt["files"].items()
    ):
        raise ValueError("bound attempt changed")
    if not file("netlog").exists():
        raise ValueError(
            "save the stopped Chrome NetLog to the prepared filename, then archive this same attempt"
        )
    # Finalization is a precondition, not a capture-quality failure. Preserve
    # this bound attempt while waiting for a complete, stable browser log.
    read_quic_reference_stream(file("netlog"), expanded=getattr(args, "expanded_netlog", False))
    try:
        cap, timing = [json.loads(file(n).read_text()) for n in ("capture", "timing")]
        if cfg.get("workflow") == "ten_packet_policy":
            saved_status = json.loads(file("status").read_text())
            if (
                saved_status["reason"] not in ("stopped by user", "capture duration limit reached")
                or timing["receipt_tracking_pending"]["prediction"]
                or timing["receipt_tracking_evicted"]["prediction"]
            ):
                raise ValueError("uninterrupted acknowledged delivery required; no replacement")
        validate_snapshot(cap, timing, intent, attempt["session_id"])
        first, last = observed_packet_bounds(cap["flows"])
        if cfg.get("scope") in ("session_acquisition_only", "fresh_evaluation_only"):
            from netembed.browser_sessions import chrome_inventory, verify_fresh

            if not file("browser-processes").exists():
                json_once(
                    file("browser-processes"),
                    {
                        "session_id": attempt["session_id"],
                        "plan_sha256": sha256(plan_path),
                        "checked_at_utc": datetime.now(timezone.utc).isoformat(),
                        "processes": chrome_inventory(),
                    },
                )
            browser_proof = json.loads(file("browser-processes").read_text())
            if browser_proof["session_id"] != attempt["session_id"] or browser_proof["plan_sha256"] != sha256(
                plan_path
            ):
                raise ValueError("browser proof belongs to another session or plan")
            verify_fresh(browser_proof["processes"], intent, first)
        check_order(cfg, args.trial, previous(root, cfg, args.trial), first, cap["session_id"])
        if cfg.get("workflow") == "family_development" and spec["role"] == "selection":
            from netembed.family_collection import selection_ready

            selection_ready(root, cfg, plan_path)
        if cfg.get("workflow") == "calibrate_then_final" and spec["role"] == "final":
            from netembed.local_policy import frozen_policy

            frozen_policy(root, cfg, first)
        if (
            cap["counters"]["observation_windows_enabled"]
            or (cfg.get("require_zero_drops", True) and cap["counters"]["drops"])
            or cap["evidence_evicted"]
        ):
            raise ValueError("capture settings or retained evidence quality failed")
        commands = {
            "reference": [
                "-m",
                "netembed.cli",
                "attribute-netlog",
                "--evidence",
                str(file("capture")),
                "--netlog",
                str(file("netlog")),
                "--stream-netlog",
            ],
            "socket-parity": [
                str(REPO / "scripts/check_browser_receive_parity.py"),
                "--evidence",
                str(file("capture")),
                "--netlog",
                str(file("netlog")),
                "--reference",
                str(file("reference")),
                "--socket-mode",
                "--stream-netlog",
            ],
            "audit": [
                str(REPO / "scripts/audit_browser_trial.py"),
                "--evidence",
                str(file("capture")),
                "--reference",
                str(file("reference")),
                "--bundle",
                intent["source_bundle"],
            ],
        }
        for name, command in commands.items():
            if getattr(args, "expanded_netlog", False) and name in ("reference", "socket-parity"):
                command.append("--expanded-netlog")
            if not file(name).exists():
                subprocess.run(
                    [sys.executable, *command, "--output", str(file(name))], check=True, capture_output=True
                )
        ref, qc, audit = [json.loads(file(n).read_text()) for n in ("reference", "socket-parity", "audit")]
        for value in (ref, qc):
            if value["evidence_sha256"] != sha256(file("capture")) or value["netlog_sha256"] != sha256(
                file("netlog")
            ):
                raise ValueError("reference/QC inputs changed")
        if qc["reference_sha256"] != sha256(file("reference")) or audit["reference_sha256"] != sha256(
            file("reference")
        ):
            raise ValueError("reference binding changed")
        comparison = audit["original_live_prediction_comparison"]
        if comparison["changed_decision_labels"] or comparison["maximum_alternative_score_difference"] > 1e-6:
            raise ValueError("source replay failed")
        kept, excluded = eligible_references(ref, qc)
        original = {f["flow_id"]: f["packets"] for f in cap["flows"]}
        if any(r["packets"] != original[r["flow_id"]] for r in kept):
            raise ValueError("exported packet values changed")
        rows = [
            {
                "id": f"browser:{cap['session_id']}:{r['flow_id']}",
                "label": r["reference"]["label"],
                "packets": r["packets"],
            }
            for r in kept
        ]
        json_once(file("rows"), rows)
        support(rows, spec, cfg)
        family_counts = None
        if cfg.get("workflow") in ("family_development", "ipv6_frozen_evaluation", "live_policy_validation"):
            from netembed.family_collection import families_for_rows, require_coverage, require_cells

            netlog, digest, _ = read_quic_reference_stream(
                file("netlog"), include_sockets=True, expanded=getattr(args, "expanded_netlog", False)
            )
            if digest != ref["netlog_sha256"]:
                raise ValueError("family input log changed")
            families = families_for_rows(cap, netlog, rows)
            json_once(file("families"), families)
            if cfg.get("workflow") in ("ipv6_frozen_evaluation", "live_policy_validation"):
                from netembed.fresh_evaluation import evaluation_coverage

                family_counts = evaluation_coverage(rows, families, spec, cfg)
            else:
                family_counts = require_coverage(families, spec, cfg)
            if (
                cfg.get("workflow") == "family_development"
                and cfg.get("scope") not in ("feasibility_only", "session_acquisition_only")
                and args.trial == cfg["trials"][-1]["id"]
            ):
                combined = list(families)
                for earlier in cfg["trials"][4:-1]:
                    combined.extend(json.loads((root / (earlier["id"] + "-families.json")).read_text()))
                require_cells(combined, cfg)
        result = {
            "status": "usable",
            "first_packet_ms": first,
            "last_packet_ms": last,
            "counts": dict(Counter(r["label"] for r in rows)),
            "excluded": excluded,
            "reference_inventory": ref["reference_counts"],
            **({"family_counts": family_counts} if family_counts is not None else {}),
        }
    except subprocess.CalledProcessError as error:
        # A failed tool has not delivered a QC verdict. Preserve diagnostics
        # and the same bound packet attempt; never request a replacement here.
        import hashlib

        stderr = (
            (error.stderr or b"").decode(errors="replace")
            if isinstance(error.stderr, bytes)
            else (error.stderr or "")
        )
        key = hashlib.sha256(stderr.encode()).hexdigest()[:12]
        json_once(
            file("processing-error-" + key),
            {
                "trial_id": args.trial,
                "session_id": attempt["session_id"],
                "status": "processing_pending",
                "returncode": error.returncode,
                "stderr": stderr,
                "capture_sha256": sha256(file("capture")),
                "netlog_sha256": sha256(file("netlog")),
                "replacement_capture": False,
            },
        )
        raise ValueError("processing failed; same capture preserved pending tool diagnosis") from error
    except ValueError as error:
        result = {"status": "unusable_stop", "reason": str(error)}
    if cfg.get("workflow") in ("spotify_data_repair", "ten_packet_fresh") and result["status"] == "usable":
        result["quality"] = {
            "reported_drops": cap["counters"]["drops"],
            "clean_operational_screen": not cap["counters"]["drops"],
            "target_eligibility": "independent browser mapping and socket-prefix QC; prediction-independent",
            "note": "Offline QC usability is not clean live-operation validation. The operational screen requires zero drops.",
        }
    names = [p for p in root.glob(f"{args.trial}-*.json") if p != file("archive")]
    result.update(
        {
            "trial_id": args.trial,
            "collection_role": spec.get("role", "prospective_comparison"),
            "session_id": attempt["session_id"],
            "plan_sha256": sha256(plan_path),
            "files": {p.name: sha256(p) for p in names},
        }
    )
    json_once(file("archive"), result)
    if (
        cfg.get("workflow") == "family_development"
        and cfg.get("scope") not in ("feasibility_only", "session_acquisition_only")
        and args.trial == cfg["trials"][3]["id"]
        and result["status"] == "usable"
    ):
        from netembed.family_collection import freeze_training

        freeze_training(root, cfg, plan_path)
    print(json.dumps(result, indent=2))


def score(args, root, cfg, plan_path):
    if cfg.get("workflow") == "ten_packet_fresh":
        from netembed.ten_fresh import offline_guard, score_fresh, validate_continuation

        validate_continuation(cfg)
        sys.addaudithook(lambda event, values: offline_guard(event, values, root, cfg))
        print(score_fresh(root, cfg, plan_path))
        return
    if cfg.get("workflow") == "spotify_data_repair":
        raise ValueError("use scripts/spotify_data_repair.py for role-bound stage commands")
    if cfg.get("workflow") == "live_policy_validation":
        from netembed.live_policy import offline_guard, score_live

        sys.addaudithook(lambda event, values: offline_guard(event, values, root, cfg))
        print(score_live(root, cfg, plan_path))
        return
    if cfg.get("workflow") == "ipv6_frozen_evaluation":
        from netembed.fresh_evaluation import offline_guard, score_evaluation

        sys.addaudithook(lambda event, values: offline_guard(event, values, root))
        print(score_evaluation(root, cfg, plan_path))
        return
    if cfg.get("workflow") == "family_development":
        raise ValueError(
            "family development requires its future bound trainer/scorer; generic paired scoring is disabled"
        )
    if cfg.get("workflow") == "calibrate_then_final":
        raise ValueError("use scripts/local_policy.py fit or evaluate for the calibration workflow")
    reports = [read_archive(root, s["id"]) for s in cfg["trials"]]
    rows_by_trial = {}
    for i, (spec, report) in enumerate(zip(cfg["trials"], reports)):
        validate_archive_plan(root, spec["id"], report, cfg)
        if report["status"] != "usable":
            raise ValueError("four usable declared visits required; preserve any shortfall")
        check_order(cfg, spec["id"], reports[:i], report["first_packet_ms"], report["session_id"])
        rows = json.loads((root / f"{spec['id']}-rows.json").read_text())
        support(rows, spec, cfg)
        rows_by_trial[spec["id"]] = rows
    output = root / "comparison.json"
    if output.exists():
        raise ValueError("comparison already frozen; preserve it")
    pair = models(cfg)
    records = []
    for spec in cfg["trials"]:
        for row in rows_by_trial[spec["id"]]:
            if row["label"] not in cfg["local_labels"]:
                continue
            raw = Flow(packets=row["packets"]).array()
            for b in cfg["budgets"]:
                if len(raw) < b:
                    continue
                record = {"trial": spec["id"], "id": row["id"], "reference": row["label"], "budget": b}
                for name, model in pair.items():
                    probabilities = (
                        model.probabilities([raw[:b]], b)[0]
                        if name == "prefix"
                        else model.probabilities([raw[:b]])[0]
                    )
                    reply = model.predict(raw[:b], b) if name == "prefix" else model.predict(raw[:b])
                    record[name] = {
                        "raw_top1": model.labels[int(np.argmax(probabilities))],
                        "probabilities": probabilities.tolist(),
                        "accepted_label": reply["label"],
                        "status": reply["status"],
                    }
                records.append(record)
    json_once(root / "paired-predictions.json", records)
    json_once(
        output,
        {
            "fixture": bool(cfg.get("fixture", False)),
            "metrics": summarize(records, cfg),
            "plan_sha256": sha256(plan_path),
            "archives": {s["id"]: sha256(root / f"{s['id']}-archive.json") for s in cfg["trials"]},
            "prediction_sha256": sha256(root / "paired-predictions.json"),
            "technical_continuation_sha256": sha256(root / "paired-yt-01-continuation.json")
            if (root / "paired-yt-01-continuation.json").exists()
            else None,
            "models": cfg["models"],
            "default_promoted": False,
            "policy_fitted": False,
            "limits": cfg["limits"],
        },
    )
    print(output)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--root", default="artifacts/local/prospective-paired-v1")
    p.add_argument("--plan", default="configs/prospective-paired-v1.json")
    p.add_argument("--service")
    p.add_argument(
        "--expanded-netlog", action="store_true", help="explicit bounded expanded offline log profile"
    )
    sub = p.add_subparsers(dest="command", required=True)
    for name in ("prepare", "archive"):
        sub.add_parser(name).add_argument("trial")
    sub.add_parser("score")
    sub.add_parser("status")
    args = p.parse_args()
    cfg = read_plan(args.plan)
    args.service = args.service or cfg.get("service_url", "http://127.0.0.1:8001")
    if args.command in ("prepare", "archive") and args.trial not in [s["id"] for s in cfg["trials"]]:
        p.error("trial is not declared by this plan")
    root = Path(args.root)
    if args.command == "status":
        print(json.dumps(collection_status(root, cfg, time.time() * 1000), indent=2))
        return
    root.mkdir(parents=True, exist_ok=True)
    plan_path = root / Path(args.plan).name
    write_once(plan_path, Path(args.plan).read_bytes().replace(b"\r\n", b"\n"))
    torch.set_num_threads(2)
    with threadpool_limits(limits=2):
        {"prepare": prepare, "archive": archive, "score": score}[args.command](args, root, cfg, plan_path)


if __name__ == "__main__":
    main()
