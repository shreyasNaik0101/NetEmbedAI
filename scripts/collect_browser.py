"""Prepare/archive fixed development recordings. Never starts packet capture."""

import argparse
import hashlib
import json
import subprocess
import sys
import time
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse
from urllib.request import urlopen

from netembed.browser_adaptation import load_reference_trial
from netembed.browser_collection import eligible_references, read_collection_plan, stage_gate, trial_spec
from netembed.bundle import Predictor, sha256
from netembed.contract import BUDGETS

REPO = Path(__file__).resolve().parents[1]


def write_once(path, content):
    if path.exists():
        if path.read_bytes() != content:
            raise ValueError("refuse to overwrite different evidence: " + path.name)
        return
    with path.open("xb") as target:
        target.write(content)


def json_once(path, value):
    write_once(path, (json.dumps(value, indent=2, allow_nan=False) + "\n").encode())


def get(base, route):
    parsed = urlparse(base)
    if (
        parsed.scheme != "http"
        or parsed.hostname not in ("127.0.0.1", "localhost")
        or parsed.path not in ("", "/")
        or parsed.username
        or parsed.query
        or parsed.fragment
    ):
        raise ValueError("use a loopback HTTP service URL")
    with urlopen(base.rstrip("/") + route, timeout=20) as response:
        content = response.read(16 * 1024 * 1024 + 1)
    if len(content) > 16 * 1024 * 1024:
        raise ValueError("service response exceeds 16 MiB")
    return content


def prepare(args, root, path, plan):
    spec = trial_spec(plan, args.trial)
    target = root / f"{args.trial}-intent.json"
    if "followup_protocol" in plan and (root / f"{args.trial}-attempt.json").exists():
        raise ValueError("the single follow-up attempt is already bound; archive it, do not Start again")
    if target.exists():
        intent = json.loads(target.read_text())
        if (
            intent["trial_id"] != args.trial
            or intent["collection_plan_sha256"] != sha256(path)
            or intent["collection_role"] != spec["role"]
        ):
            raise ValueError("existing intent belongs to another frozen plan/role")
        print(
            json.dumps(
                {"stage": "intent_already_exists", "intent": str(target), "netlog": intent["netlog_file"]}
            )
        )
        return
    stage_gate(root, path, args.trial, time.time() * 1000)
    status = json.loads(get(args.service, "/capture/status"))
    if status["running"]:
        raise ValueError("stop capture in the app before preparing another recording")
    if status.get("session_id"):
        archived = [
            json.loads(p.read_text()).get("session_id") for p in root.glob("*-collection-summary.json")
        ]
        if status["session_id"] not in archived:
            raise ValueError("archive the current stopped session before another Start")
    model = Predictor(args.bundle)
    current = json.loads(get(args.service, "/model"))
    if current["artifact_id"] != model.identity:
        raise ValueError("audit bundle differs from the app's actual loaded model")
    if "followup_protocol" in plan:
        protocol = plan["followup_protocol"]
        if (
            model.identity != protocol["source_artifact_id"]
            or args.interface != protocol["one_additional_trial"]["interface_id"]
        ):
            raise ValueError("follow-up source model/interface differs from its declaration")
    interfaces = json.loads(get(args.service, "/capture/interfaces"))
    matches = [row for row in interfaces if row["id"] == args.interface]
    if len(matches) != 1:
        raise ValueError("selected local interface is unavailable")
    if "selected_interface_id" not in status:
        raise ValueError("restart the updated local service before this collection")
    netlog = root / f"{args.trial}-netlog.json"
    if netlog.exists():
        raise ValueError("unbound browser log already exists; preserve it and choose a declared new trial")
    ui = get(args.service, "/")
    intent = {
        "trial_id": args.trial,
        "collection_role": spec["role"],
        "collection_plan_sha256": sha256(path),
        "recorded_before_capture_utc": datetime.now(timezone.utc).isoformat(),
        "intended_activity": spec["activity"],
        "expected_artifact_id": model.identity,
        "expected_adapter": "tshark-prefix-ns-v3",
        "selected_interface_id": args.interface,
        "selected_interface_description": matches[0]["description"],
        "netlog_file": str(netlog.resolve()),
        "source_bundle": str(Path(args.bundle).resolve()),
        "previous_session_excluded": status.get("session_id"),
        "ui_index_sha256": hashlib.sha256(ui).hexdigest(),
        "capture_user_started_required": True,
        "reference_checkbox_required": True,
        "capture_duration_cap_seconds": 120,
        "keep_both_windows_visible": True,
        "labels": "independent fixed browser matcher only; never intended activity or model output",
    }
    json_once(target, intent)
    print(
        json.dumps(
            {
                "stage": "prepared_not_capturing",
                "trial": args.trial,
                "role": spec["role"],
                "activity": spec["activity"],
                "netlog": intent["netlog_file"],
                "interface": matches[0],
            }
        ),
        flush=True,
    )


def validate_snapshot(cap, timing, intent, session_id):
    if (
        cap["fixture"]
        or cap["source"] != "user_started_capture"
        or cap["counters"]["running"]
        or not cap["reference_enabled"]
        or cap["adapter_version"] != intent["expected_adapter"]
        or cap["artifact_id"] != intent["expected_artifact_id"]
        or cap["session_id"] != timing["session_id"]
        or cap["session_id"] != session_id
        or cap["session_id"] == intent["previous_session_excluded"]
        or cap["counters"].get("selected_interface_id") != intent["selected_interface_id"]
    ):
        raise ValueError("stopped capture does not match the pre-capture intent")
    if not cap["flows"]:
        raise ValueError("no retained QUIC flows; do not fabricate a development recording")
    first = min(row["connection_match"]["first_packet_unix_ms"] for row in cap["flows"])
    if first <= datetime.fromisoformat(intent["recorded_before_capture_utc"]).timestamp() * 1000:
        raise ValueError("capture predates the frozen intent")


def snapshot(args, root, intent):
    cap_path, timing_path = [root / f"{args.trial}-{name}.json" for name in ("capture", "timing")]
    if cap_path.exists() and timing_path.exists():
        cap, timing = json.loads(cap_path.read_text()), json.loads(timing_path.read_text())
        validate_snapshot(cap, timing, intent, cap["session_id"])
        return
    status = json.loads(get(args.service, "/capture/status"))
    if status["running"]:
        raise ValueError("stop capture in the app before archiving")
    cap_bytes, timing_bytes = (
        get(args.service, "/capture/local-evaluation"),
        get(args.service, "/capture/summary"),
    )
    cap, timing = json.loads(cap_bytes), json.loads(timing_bytes)
    validate_snapshot(cap, timing, intent, status["session_id"])
    write_once(cap_path, cap_bytes)
    write_once(timing_path, timing_bytes)


def followup_snapshot(args, root, intent, plan, path):
    """Bind the first stopped attempt before eligibility checks; no replacement."""
    from netembed.browser_followup import stage_gate as followup_gate

    attempt_path = root / f"{args.trial}-attempt.json"
    paths = {name: root / f"{args.trial}-attempt-{name}.json" for name in ("capture", "timing", "status")}
    if not attempt_path.exists():
        status_bytes = get(args.service, "/capture/status")
        status = json.loads(status_bytes)
        if status["running"]:
            raise ValueError("stop capture before binding the follow-up attempt")
        if not status.get("session_id") or status["session_id"] == intent["previous_session_excluded"]:
            raise ValueError("no new user-started follow-up attempt to archive")
        cap_bytes = get(args.service, "/capture/local-evaluation")
        timing_bytes = get(args.service, "/capture/summary")
        for name, value in (("capture", cap_bytes), ("timing", timing_bytes), ("status", status_bytes)):
            write_once(paths[name], value)
        json_once(
            attempt_path,
            {
                "trial_id": args.trial,
                "session_id": status["session_id"],
                "protocol_sha256": sha256(path),
                "files_sha256": {p.name: sha256(p) for p in paths.values()},
                "note": "Single attempt consumed before eligibility checks; never replace with another session.",
            },
        )
    attempt = json.loads(attempt_path.read_text())
    if attempt["trial_id"] != args.trial or attempt["protocol_sha256"] != sha256(path):
        raise ValueError("bound follow-up attempt belongs to another protocol")
    expected = {p.name for p in paths.values()}
    if set(attempt["files_sha256"]) != expected or any(
        sha256(root / name) != digest for name, digest in attempt["files_sha256"].items()
    ):
        raise ValueError("bound follow-up attempt evidence changed")
    cap, timing = [json.loads(paths[name].read_text()) for name in ("capture", "timing")]
    try:
        validate_snapshot(cap, timing, intent, attempt["session_id"])
        first = min(f["connection_match"]["first_packet_unix_ms"] for f in cap["flows"])
        state = followup_gate(root, path, plan, args.trial, first)
        if cap["session_id"] in state["sessions"]:
            raise ValueError("follow-up attempt reuses a parent session")
        if cap["counters"].get("observation_windows_enabled") is not False:
            raise ValueError("follow-up requires longer-window statistics off")
    except ValueError as error:
        json_once(
            root / f"{args.trial}-followup-outcome.json",
            {
                "trial_id": args.trial,
                "session_id": attempt["session_id"],
                "status": "unusable_attempt_stop",
                "reason": str(error),
                "attempt_sha256": sha256(attempt_path),
                "training_started": False,
            },
        )
        raise
    for name in ("capture", "timing"):
        write_once(root / f"{args.trial}-{name}.json", paths[name].read_bytes())


def archive(args, root, path, plan):
    spec = trial_spec(plan, args.trial)

    def prefix(name):
        return root / f"{args.trial}-{name}.json"

    intent = json.loads(prefix("intent").read_text())
    if (
        intent["trial_id"] != args.trial
        or intent["collection_plan_sha256"] != sha256(path)
        or intent["collection_role"] != spec["role"]
    ):
        raise ValueError("intent role or plan changed")
    if prefix("collection-summary").exists():
        rows, proof = load_reference_trial(root, args.trial, plan["labels"], "development", path)
        print(json.dumps({"stage": "already_archived", "counts": proof["counts"], "rows": len(rows)}))
        return
    if "followup_protocol" in plan:
        followup_snapshot(args, root, intent, plan, path)
    else:
        snapshot(args, root, intent)
    print(json.dumps({"stage": "stopped_evidence_saved", "trial": args.trial}), flush=True)
    common = ["--evidence", str(prefix("capture")), "--netlog", str(prefix("netlog"))]
    commands = [
        ("reference", ["-m", "netembed.cli", "attribute-netlog", *common, "--stream-netlog"]),
        (
            "socket-parity",
            [
                str(REPO / "scripts/check_browser_receive_parity.py"),
                *common,
                "--reference",
                str(prefix("reference")),
                "--socket-mode",
                "--stream-netlog",
            ],
        ),
        (
            "audit",
            [
                str(REPO / "scripts/audit_browser_trial.py"),
                "--evidence",
                str(prefix("capture")),
                "--reference",
                str(prefix("reference")),
                "--bundle",
                intent["source_bundle"],
            ],
        ),
    ]
    for name, command in commands:
        if not prefix(name).exists():
            subprocess.run([sys.executable, *command, "--output", str(prefix(name))], check=True)
        print(json.dumps({"stage": name, "trial": args.trial}), flush=True)
    cap, ref, qc, audit, timing = [
        json.loads(prefix(name).read_text())
        for name in ("capture", "reference", "socket-parity", "audit", "timing")
    ]
    if (
        ref["evidence_sha256"] != sha256(prefix("capture"))
        or qc["evidence_sha256"] != sha256(prefix("capture"))
        or ref["netlog_sha256"] != sha256(prefix("netlog"))
        or qc["netlog_sha256"] != sha256(prefix("netlog"))
        or qc["reference_sha256"] != sha256(prefix("reference"))
        or audit["reference_sha256"] != sha256(prefix("reference"))
    ):
        raise ValueError("archive source hashes disagree")
    comparison = audit["original_live_prediction_comparison"]
    if comparison["changed_decision_labels"] or comparison["maximum_alternative_score_difference"] > 1e-6:
        raise ValueError("source model predictions did not reproduce")
    eligible, excluded = eligible_references(ref, qc)
    first = min(r["connection_match"]["first_packet_unix_ms"] for r in cap["flows"])
    day = datetime.fromtimestamp(first / 1000, timezone.utc).date().isoformat()
    rows = [
        {
            "id": f"browser:{cap['session_id']}:{r['flow_id']}",
            "group_id": cap["session_id"],
            "date": day,
            "label": r["reference"]["label"],
            "schema_version": "1",
            "packets": r["packets"],
        }
        for r in eligible
    ]
    rows_path = root / f"{args.trial}-development-rows.jsonl"
    write_once(rows_path, "".join(json.dumps(r) + "\n" for r in rows).encode())
    files = [
        prefix(name)
        for name in ("intent", "capture", "netlog", "reference", "socket-parity", "audit", "timing")
    ]
    files += [rows_path, path]
    if "followup_protocol" in plan:
        files += [prefix("attempt")]
        files += [prefix("attempt-" + name) for name in ("capture", "timing", "status")]
    report = {
        "trial_id": args.trial,
        "session_id": cap["session_id"],
        "collection_role": spec["role"],
        "collection_plan_sha256": sha256(path),
        "reference_inventory": ref["reference_counts"],
        "eligible_reference_counts": dict(Counter(r["label"] for r in rows)),
        "excluded_mapped_flows": excluded,
        "available_prefix_points": sum(len(r["packets"]) >= b for r in rows for b in BUDGETS),
        "source_prediction_replay": comparison,
        "counters": cap["counters"],
        "evidence_evicted": cap["evidence_evicted"],
        "browser_receipt_ms": {
            "n": timing["browser_receipt_n"],
            "p50": timing["browser_receipt_p50_ms"],
            "p95": timing["browser_receipt_p95_ms"],
        },
        "evidence_sha256": {p.name: sha256(p) for p in files},
        "used_for_training": False,
        "final_evaluation": False,
        "note": "Development only. Every refusal/exclusion retained, eligibility independent of activity and predictions. Within-direction parity is not merged wire-order truth. Archival never starts capture, trains or fits confidence.",
    }
    json_once(prefix("collection-summary"), report)
    load_reference_trial(root, args.trial, plan["labels"], "development", path)
    print(
        json.dumps(
            {
                "stage": "archived",
                "trial": args.trial,
                "counts": report["eligible_reference_counts"],
                "excluded": excluded,
                "prefix_points": report["available_prefix_points"],
            }
        ),
        flush=True,
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--collection", default="artifacts/local/browser-development")
    parser.add_argument("--plan", default="configs/browser-collection-v3.json")
    parser.add_argument("--service", default="http://127.0.0.1:8001")
    parser.add_argument("--bundle", default="experiments/full-real/20261024-151720-3532794c/bundle")
    parser.add_argument("--interface", default="9")
    sub = parser.add_subparsers(dest="command", required=True)
    for name in ("prepare", "archive"):
        sub.add_parser(name).add_argument("trial")
    sub.add_parser("status")
    args = parser.parse_args()
    root, source = Path(args.collection), Path(args.plan)
    plan = read_collection_plan(source)
    path = root / source.name
    if args.command == "status":
        if path.exists():
            plan = read_collection_plan(path)
        print(
            json.dumps(
                {
                    "trials": [
                        {**r, "archived": (root / f"{r['id']}-collection-summary.json").exists()}
                        for r in plan["trials"]
                    ]
                }
            )
        )
        return
    root.mkdir(parents=True, exist_ok=True)
    if "followup_protocol" in plan:
        parent_name = Path(plan["followup_protocol"]["parent_plan"]["path"]).name
        parent_target = root / parent_name
        expected_parent = plan["followup_protocol"]["parent_plan"]["sha256"]
        if parent_target.exists():
            if sha256(parent_target) != expected_parent:
                raise ValueError("frozen private parent plan changed")
        else:
            parent_bytes = (source.parent / parent_name).read_bytes().replace(b"\r\n", b"\n")
            if hashlib.sha256(parent_bytes).hexdigest() != expected_parent:
                raise ValueError("parent config does not reproduce the frozen parent bytes")
            write_once(parent_target, parent_bytes)
    write_once(path, source.read_bytes())
    if args.command == "prepare":
        prepare(args, root, path, plan)
    else:
        archive(args, root, path, plan)


if __name__ == "__main__":
    main()
