"""Prepare/archive the fixed six-visit Spotify study. Capture remains user-started."""

import argparse
from copy import deepcopy
import json
import os
from pathlib import Path
import time
from urllib.parse import urlparse

from collect_browser import write_once
from netembed.paired_study import read_plan
from netembed.spotify_repair import source_for, status
import paired_capture


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--plan", default="configs/spotify-data-repair-v1.json")
    p.add_argument("--root", default="artifacts/local/spotify-data-repair-v1")
    sub = p.add_subparsers(dest="command", required=True)
    for name in ["prepare", "archive", "serve"]:
        sub.add_parser(name).add_argument("trial")
    sub.add_parser("status")
    for name in ["fit", "assess", "calibrate", "evaluate"]:
        sub.add_parser(name)
    args = p.parse_args()
    cfg = read_plan(args.plan)
    root = Path(args.root)
    if args.command == "status":
        print(json.dumps(status(root, cfg, time.time() * 1000), indent=2))
        return
    root.mkdir(parents=True, exist_ok=True)
    plan_path = root / Path(args.plan).name
    write_once(plan_path, Path(args.plan).read_bytes().replace(b"\r\n", b"\n"))
    if args.command in ["fit", "assess", "calibrate", "evaluate"]:
        from netembed.spotify_repair_stages import execute

        print(json.dumps(execute(args.command, root, cfg), indent=2))
        return
    if args.trial not in [s["id"] for s in cfg["trials"]]:
        p.error("undeclared trial")
    if args.command == "archive":
        # Intent already binds its exact source bundle; source_for must not
        # require reopening a browser or recreating the stage decision.
        effective = deepcopy(cfg)
        spec = next(s for s in cfg["trials"] if s["id"] == args.trial)
        effective["require_zero_drops"] = spec["role"] == "evaluation"
    else:
        effective = source_for(root, cfg, args.trial, time.time() * 1000)
    args.service = cfg["service_url"]
    args.expanded_netlog = True
    if args.command == "serve":
        import torch
        import uvicorn
        from netembed.api import create_app

        u = urlparse(args.service)
        os.environ["NETEMBED_ORIGINS"] = f"http://127.0.0.1:{u.port},http://localhost:{u.port}"
        os.environ.pop("NETEMBED_EVALUATION", None)
        torch.set_num_threads(2)
        uvicorn.run(create_app(effective["source_bundle"]), host="127.0.0.1", port=u.port)
        return
    if args.command == "prepare":
        paired_capture.prepare(args, root, effective, plan_path)
    else:
        paired_capture.archive(args, root, effective, plan_path)


if __name__ == "__main__":
    main()
