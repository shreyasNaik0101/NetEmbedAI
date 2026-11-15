"""Prepare/serve/archive the fixed fresh check; never starts capture."""

import argparse
import json
import os
from pathlib import Path
import time
from urllib.parse import urlparse

import torch
from threadpoolctl import threadpool_limits

from collect_browser import write_once
from netembed.paired_study import collection_status, read_plan
from netembed.ten_fresh import frozen_models
import paired_capture


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan", default="configs/ten-packet-fresh-v1.json")
    parser.add_argument("--root", default="artifacts/local/ten-packet-fresh-v1")
    sub = parser.add_subparsers(dest="command", required=True)
    for cmd in ["prepare", "archive"]:
        sub.add_parser(cmd).add_argument("trial")
    for cmd in ["serve", "status", "score"]:
        sub.add_parser(cmd)
    args = parser.parse_args()
    config = Path(args.plan)
    cfg = read_plan(config)
    root = Path(args.root)
    if args.command == "status":
        print(json.dumps(collection_status(root, cfg, time.time() * 1000), indent=2))
        return
    root.mkdir(parents=True, exist_ok=True)
    plan_path = root / config.name
    write_once(plan_path, config.read_bytes().replace(b"\r\n", b"\n"))
    torch.set_num_threads(cfg["threads"])
    args.service = cfg["service_url"]
    args.expanded_netlog = True
    if args.command == "serve":
        frozen_models(cfg)
        u = urlparse(cfg["service_url"])
        if u.scheme != "http" or u.hostname != "127.0.0.1" or u.port != 8002:
            raise ValueError("requires declared localhost validation service")
        os.environ["NETEMBED_ORIGINS"] = f"http://127.0.0.1:{u.port},http://localhost:{u.port}"
        os.environ.pop("NETEMBED_EVALUATION", None)
        import uvicorn
        from netembed.api import create_app

        uvicorn.run(create_app(cfg["source_bundle"]), host=u.hostname, port=u.port)
        return
    if args.command in ["prepare", "archive"] and args.trial not in [s["id"] for s in cfg["trials"]]:
        parser.error("undeclared visit")
    with threadpool_limits(limits=cfg["threads"]):
        {"prepare": paired_capture.prepare, "archive": paired_capture.archive, "score": paired_capture.score}[
            args.command
        ](args, root, cfg, plan_path)


if __name__ == "__main__":
    main()
