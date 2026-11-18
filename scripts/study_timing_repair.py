"""Run the fixed matched timing repair; never start capture or activate artifacts."""

import argparse
import json
import torch
from threadpoolctl import threadpool_limits
from netembed.timing_repair import run


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--config", default="configs/spotify-timing-repair-v1.json")
    p.add_argument("--output", default="experiments/spotify-timing-repair-v1")
    args = p.parse_args()
    torch.set_num_threads(2)
    with threadpool_limits(limits=2):
        print(json.dumps(run(args.config, args.output), indent=2))


if __name__ == "__main__":
    main()
