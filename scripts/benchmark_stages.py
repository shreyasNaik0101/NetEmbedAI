"""Bounded real-artifact stage benchmark. Never opens a capture interface."""

import argparse
import subprocess
from pathlib import Path

import torch
from threadpoolctl import threadpool_limits

from netembed.benchmark_stages import benchmark_stages
from netembed.bundle import Predictor, sha256, write_json
from netembed.contract import Flow


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bundle", required=True)
    parser.add_argument("--flow", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--threads", type=int, default=2, choices=(1, 2, 4))
    args = parser.parse_args()
    output = Path(args.output)
    if output.exists():
        raise FileExistsError(output)
    predictor = Predictor(args.bundle)
    flow = Flow.model_validate_json(Path(args.flow).read_text()).array()
    torch.set_num_threads(args.threads)
    with threadpool_limits(limits=args.threads):
        report = benchmark_stages(predictor, flow)
    report.update(
        flow_sha256=sha256(args.flow),
        source_commit=subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
        source_sha256={str(p): sha256(p) for p in (Path(__file__), Path("src/netembed/benchmark_stages.py"))},
        new_capture=False,
    )
    write_json(output, report)
    print(f"Saved stage timing report: {output}")


if __name__ == "__main__":
    main()
