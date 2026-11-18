"""Run the single fixed real-data pilot; no capture or automatic activation."""

import argparse
import json
import sys

import torch
from threadpoolctl import threadpool_limits

from netembed.ipv6_pilot import guard, run


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--config", default="configs/ipv6-realdata-pilot-v1.json")
    p.add_argument("--output", default="experiments/ipv6-realdata-pilot-v1")
    args = p.parse_args()
    sys.addaudithook(guard)
    torch.set_num_threads(2)
    with threadpool_limits(limits=2):
        print(json.dumps(run(args.config, args.output), indent=2))


if __name__ == "__main__":
    main()
