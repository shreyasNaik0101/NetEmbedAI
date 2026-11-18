"""Offline research artifact inference using only the bundle and one raw flow."""

import argparse
import json
import sys
from pathlib import Path

import torch
from threadpoolctl import threadpool_limits

from netembed.bundle import sha256
from netembed.contract import Flow
from netembed.linear_probe import LinearProbe, WHEEL, WHEEL_SHA


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bundle", required=True)
    parser.add_argument("--flow", required=True)
    args = parser.parse_args()
    wheel = Path(args.bundle) / WHEEL
    if sha256(wheel) != WHEEL_SHA:
        raise ValueError("pinned optional wheel changed")
    # The pure-Python wheel is directly importable; no install or network is needed.
    sys.path.insert(0, str(wheel.resolve()))
    torch.set_num_threads(2)
    with threadpool_limits(limits=2):
        model = LinearProbe.load(args.bundle)
        flow = Flow(**json.loads(Path(args.flow).read_text()))
        print(json.dumps(model.predict(flow.array()), indent=2))


if __name__ == "__main__":
    main()
