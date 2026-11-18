"""Write explicit, reproducible train configs from the tracked comparison matrix."""

import argparse
import json
from pathlib import Path


def materialize(matrix_path, policy_path, output):
    matrix = json.loads(Path(matrix_path).read_text())
    policy = json.loads(Path(policy_path).read_text())
    floor = policy["clean_floor"]
    if not isinstance(floor, (int, float)) or not 0 <= floor <= 1:
        raise ValueError("freeze a numeric development clean floor before comparative runs")
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    paths = []
    for item in matrix:
        cfg = {**item, "epochs": 20, "batch_size": 128, "threads": 4}
        if cfg["kind"] == "tcn":
            cfg["augmentation_policy"] = "single-edit-50-clean-v1"
            if cfg["augmentation"] or cfg["loss"] == "supcon":
                cfg["clean_floor"] = floor
        name = f"{cfg['kind']}-{cfg['loss']}-{'aug' if cfg['augmentation'] else 'plain'}-{cfg['seed']}.json"
        path = output / name
        path.write_text(json.dumps(cfg, indent=2) + "\n")
        paths.append(path)
    return paths


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--matrix", default="configs/matrix.json")
    parser.add_argument("--policy", default="configs/selection-policy.json")
    parser.add_argument("--output", default="experiments/configs/generated")
    args = parser.parse_args()
    for path in materialize(args.matrix, args.policy, args.output):
        print(path)
