"""Offline four-head artifact inference; never starts capture."""

import argparse
import json
import sys
from pathlib import Path

import torch
from threadpoolctl import threadpool_limits

from netembed.bundle import sha256
from netembed.contract import Flow
from netembed.linear_probe import WHEEL, WHEEL_SHA
from netembed.prefix_probe import PrefixProbe


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bundle", required=True)
    parser.add_argument("--flow", required=True)
    parser.add_argument("--budget", type=int, choices=[5, 10, 20, 30])
    args = parser.parse_args()
    wheel = Path(args.bundle) / "base" / WHEEL
    if sha256(wheel) != WHEEL_SHA:
        raise ValueError("pinned optional wheel changed")
    sys.path.insert(0, str(wheel.resolve()))
    torch.set_num_threads(2)
    with threadpool_limits(limits=2):
        model = PrefixProbe.load(args.bundle)
        raw = Flow(**json.loads(Path(args.flow).read_text())).array()
        # An explicit cap truncates before inference; the model itself rejects
        # over-budget arrays so accidental future-packet access cannot be hidden.
        if args.budget is not None:
            raw = raw[: args.budget]
        print(json.dumps(model.predict(raw, args.budget), indent=2))


if __name__ == "__main__":
    main()
