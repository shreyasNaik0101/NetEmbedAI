"""Run one bounded declared stage; never starts capture or fits a confidence policy."""

import argparse
import json
import sys

import torch
from threadpoolctl import threadpool_limits

from netembed.size_robustness import finish, guard, run


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    stage = parser.add_mutually_exclusive_group(required=True)
    stage.add_argument("--seed", type=int, choices=(17, 42, 123))
    stage.add_argument("--decision", action="store_true")
    parser.add_argument("--config", default="configs/size-robustness-v1.json")
    parser.add_argument("--output", default="experiments/size-robustness-v1")
    args = parser.parse_args()
    sys.addaudithook(guard)
    torch.set_num_threads(2)
    with threadpool_limits(limits=2):
        result = (
            finish(args.config, args.output) if args.decision else run(args.seed, args.config, args.output)
        )
        print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
