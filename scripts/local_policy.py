"""Fit the declared forest threshold or evaluate its frozen final policy."""

import argparse
import json
import sys
from pathlib import Path

import torch
from threadpoolctl import threadpool_limits
from netembed.local_policy import calibration_guard, fit, evaluate
from netembed.paired_study import read_plan


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("command", choices=["fit", "evaluate"])
    p.add_argument("--root", default="artifacts/local/forest-policy-calibration-v1")
    p.add_argument("--data", default="data/processed/v2")
    args = p.parse_args()
    cfg = read_plan(Path(args.root) / "forest-policy-calibration-v1.json")
    if args.command == "fit":
        sys.addaudithook(calibration_guard)
    torch.set_num_threads(2)
    with threadpool_limits(limits=2):
        result = fit(args.root, cfg, args.data) if args.command == "fit" else evaluate(args.root, cfg)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
