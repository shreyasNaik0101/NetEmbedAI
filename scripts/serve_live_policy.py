"""Launch the explicitly selected validation profile; never start capture."""

import argparse
import os
from urllib.parse import urlparse

import torch

from netembed.live_policy import load_model
from netembed.paired_study import read_plan


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan", default="configs/ipv6-live-policy-v1.json")
    args = parser.parse_args()
    cfg = read_plan(args.plan)
    load_model(cfg)
    url = urlparse(cfg["service_url"])
    if url.hostname != "127.0.0.1" or url.scheme != "http" or not url.port:
        raise ValueError("validation service must be explicit localhost")
    os.environ["NETEMBED_ORIGINS"] = f"http://127.0.0.1:{url.port},http://localhost:{url.port}"
    os.environ.pop("NETEMBED_EVALUATION", None)
    torch.set_num_threads(cfg["threads"])
    import uvicorn
    from netembed.api import create_app

    uvicorn.run(create_app(cfg["source_bundle"]), host="127.0.0.1", port=url.port)


if __name__ == "__main__":
    main()
