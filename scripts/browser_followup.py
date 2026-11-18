"""Generate fixed follow-up configs or summarize completed repetitions; never captures."""

import argparse
import json
from pathlib import Path

from netembed.browser_followup import REPO, expected_config, repetition_decision


def json_once(path, value):
    content = (json.dumps(value, indent=2, allow_nan=False) + "\n").encode()
    if path.exists():
        if path.read_bytes() != content:
            raise ValueError("refuse to overwrite different follow-up evidence")
    else:
        with path.open("xb") as target:
            target.write(content)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--protocol", default="configs/browser-selection-followup-v1.json")
    parser.add_argument("command", choices=("configs", "decision"))
    args = parser.parse_args()
    path = Path(args.protocol)
    if args.command == "configs":
        for seed in (17, 42, 123):
            target = REPO / f"configs/browser-selection-followup-v1-seed{seed}.json"
            json_once(target, expected_config(path, seed))
            print(target)
    else:
        result = repetition_decision(path)
        target = REPO / "experiments/browser-adaptation/selection-followup-v1-decision.json"
        json_once(target, result)
        print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
