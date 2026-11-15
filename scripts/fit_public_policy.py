"""Fit one declared public-only refusal policy; no local data or capture."""

import argparse
import json
import sys

import torch
from threadpoolctl import threadpool_limits

from netembed.public_policy import fit_guard, run


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", default="configs/ipv6-public-policy-v1.json")
    parser.add_argument("--output", default="experiments/ipv6-public-policy-v1")
    args = parser.parse_args()
    sys.addaudithook(lambda event, values: fit_guard(event, values, args.output))
    torch.set_num_threads(2)
    with threadpool_limits(limits=2):
        report = run(args.config, args.output)
    print(
        json.dumps(
            {k: report[k] for k in ("status", "policy", "policy_artifact_id", "prefix_cases")}, indent=2
        )
    )


if __name__ == "__main__":
    main()
