"""Explicit prepare/archive/fit/final commands; serve never starts capture."""

import argparse
import json
import os
import sys
import time

import torch
from threadpoolctl import threadpool_limits

from collect_browser import write_once
import paired_capture
from netembed.paired_study import collection_status, read_plan
from netembed.bundle import sha256
from netembed.ten_policy import (
    PLAN,
    ROOT,
    candidate,
    evaluate,
    fit,
    frozen_policy,
    offline_guard,
    prerequisites,
)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    for name in ("prepare", "archive"):
        sub.add_parser(name).add_argument("trial")
    for name in ("status", "fit", "evaluate", "preflight"):
        sub.add_parser(name)
    sub.add_parser("serve").add_argument("--fitted", action="store_true")
    args = parser.parse_args()
    cfg = read_plan(PLAN)
    prerequisites(cfg)
    if args.command == "status":
        report = collection_status(ROOT, cfg, time.time() * 1000)
        if report["next_slot"] and "-final-" in report["next_slot"]["trial"]:
            try:
                frozen_policy(ROOT, cfg)
            except (OSError, ValueError, KeyError) as error:
                report["next_action"] = "awaiting_fitted_policy_or_stopped"
                report["reason"] = str(error)
        print(json.dumps(report, indent=2))
        return
    ROOT.mkdir(parents=True, exist_ok=True)
    plan_path = ROOT / PLAN.name
    write_once(plan_path, PLAN.read_bytes().replace(b"\r\n", b"\n"))
    torch.set_num_threads(cfg["threads"])
    if args.command == "preflight":
        model = candidate(cfg)
        intents = list(ROOT.parent.glob("*/*-intent.json"))
        if len(intents) > 1000:
            raise ValueError("bounded intent inventory exceeded")
        excluded = []
        eligible = []
        for path in intents:
            intent = json.loads(path.read_text())
            item = {
                "intent": str(path),
                "sha256": sha256(path),
                "role": intent.get("collection_role"),
                "artifact": intent.get("expected_artifact_id"),
            }
            if path.parent == ROOT and intent.get("collection_plan_sha256") == sha256(plan_path):
                eligible.append(item)
            else:
                excluded.append({**item, "reason": "not assigned to this frozen calibration/final protocol"})
        report = {
            "artifact_id": model.identity,
            "eligible_intents": eligible,
            "excluded_prior_intents": excluded,
            "packet_rows_read": False,
            "training_data_read": False,
            "model_fitted": False,
            "capture_started": False,
        }
        from netembed.ten_policy import write_once as write_json_once

        write_json_once(ROOT / "eligibility-preflight.json", report)
        print(
            json.dumps(
                {
                    "eligible_intents": len(eligible),
                    "excluded_prior_intents": len(excluded),
                    "result": str(ROOT / "eligibility-preflight.json"),
                    "capture_started": False,
                },
                indent=2,
            )
        )
        return
    if args.command == "serve":
        bundle = ROOT / "policy-bundle" if args.fitted else cfg["source_bundle"]
        if args.fitted:
            frozen_policy(ROOT, cfg)
        else:
            candidate(cfg)
        os.environ["NETEMBED_ORIGINS"] = "http://127.0.0.1:8002,http://localhost:8002"
        os.environ.pop("NETEMBED_EVALUATION", None)
        import uvicorn
        from netembed.api import create_app

        uvicorn.run(create_app(bundle), host="127.0.0.1", port=8002)
        return
    if args.command in ("prepare", "archive"):
        if args.trial not in [s["id"] for s in cfg["trials"]]:
            parser.error("undeclared slot")
        args.service, args.expanded_netlog = cfg["service_url"], True
        with threadpool_limits(limits=cfg["threads"]):
            {"prepare": paired_capture.prepare, "archive": paired_capture.archive}[args.command](
                args, ROOT, cfg, plan_path
            )
        return
    role = "calibration" if args.command == "fit" else "final"
    # Prerequisites were validated before the offline guard. They never become
    # fitting rows, and the guard now denies access to all older private data.
    sys.addaudithook(lambda event, values: offline_guard(event, values, ROOT, cfg, role))
    with threadpool_limits(limits=cfg["threads"]):
        print(json.dumps(fit(ROOT, cfg) if args.command == "fit" else evaluate(ROOT, cfg), indent=2))


if __name__ == "__main__":
    main()
