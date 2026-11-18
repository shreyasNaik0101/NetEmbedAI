"""Calibrate the frozen candidate offline; never trains, captures or deploys."""

import argparse
import torch
from netembed.browser_calibration import run


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("data", "collection", "bundle", "decision", "output"):
        parser.add_argument("--" + name, required=True)
    parser.add_argument("--additional-trial", action="append", default=[])
    parser.add_argument("--previous-report")
    parser.add_argument("--plan-name", default="calibration-collection-plan-v1.json")
    args = parser.parse_args()
    torch.set_num_threads(2)
    print(
        run(
            args.data,
            args.collection,
            args.bundle,
            args.decision,
            args.output,
            args.additional_trial,
            args.previous_report,
            args.plan_name,
        )
    )


if __name__ == "__main__":
    main()
