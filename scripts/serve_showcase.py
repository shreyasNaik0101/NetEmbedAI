"""Serve the explicitly identified unfitted showcase bundle; never start capture."""

import argparse
import os

import torch
import uvicorn

from netembed.api import create_app
from netembed.bundle import Predictor

SHOWCASE_ID = "fa1f4837e4ae11c9169258ecb20338ae3c0c81c2d206231fb6fe19405b8d8549"


def validate_showcase(bundle):
    model = Predictor(bundle)
    if (
        model.identity != SHOWCASE_ID
        or model.fixed_prefix_packets != 10
        or model.meta["policy"]["fitted"]
        or model.meta["provenance"].get("fixture", True)
    ):
        raise ValueError("showcase requires the declared genuine unfitted fixed-ten bundle")
    return model


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bundle", default="experiments/spotify-ten-packet-v1/bundle")
    parser.add_argument("--port", type=int, default=8002)
    args = parser.parse_args()
    if not 1024 <= args.port <= 65535:
        parser.error("port must be in the range 1024–65535")
    validate_showcase(args.bundle)
    torch.set_num_threads(2)
    os.environ["NETEMBED_ORIGINS"] = f"http://127.0.0.1:{args.port},http://localhost:{args.port}"
    os.environ.pop("NETEMBED_EVALUATION", None)
    uvicorn.run(create_app(args.bundle), host="127.0.0.1", port=args.port)


if __name__ == "__main__":
    main()
