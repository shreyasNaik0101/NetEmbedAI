"""Run the frozen development matrix sequentially; never open the final test."""

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path("src").resolve()))


def matching_runs(root, config, manifest_hash):
    from netembed.training import DEFAULT

    expected = {**DEFAULT, **config}
    if not expected["augmentation"]:
        expected.pop("augmentation_policy", None)
    if expected["kind"] == "forest":
        expected.pop("threads", None)  # n_jobs changes fit parallelism, not tree hyperparameters.
    matches = []
    for path in root.iterdir():
        record = path / "config.json"
        if not path.is_dir() or not record.is_file():
            continue
        details = json.loads(record.read_text())
        actual = dict(details["config"])
        if not actual["augmentation"]:
            actual.pop("augmentation_policy", None)
        if actual["kind"] == "forest":
            actual.pop("threads", None)
        if actual == expected and details["data_manifest_sha256"] == manifest_hash:
            matches.append(path)
    return sorted(matches, key=lambda path: path.name, reverse=True)


def action_for(runs):
    for run in runs:
        if (run / "result.json").is_file() and (run / "bundle" / "metadata.json").is_file():
            if (run / "selection" / "report.json").is_file():
                return "done", run
            return "evaluate", run
    for run in runs:
        if (run / "resume.pt").is_file():
            return "resume", run
    return "train", None


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", default="data/processed/v2")
    parser.add_argument("--root", default="experiments/full-real")
    parser.add_argument("--config-dir", default="experiments/configs/generated")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    from netembed.bundle import sha256

    data, root, config_dir = Path(args.data), Path(args.root), Path(args.config_dir)
    manifest_hash = sha256(data / "manifest.json")
    root.mkdir(parents=True, exist_ok=True)
    matrix = json.loads(Path("configs/matrix.json").read_text())
    matrix.sort(
        key=lambda item: (
            0 if item["kind"] == "forest" else 1 + (item["loss"] == "supcon") * 2 + item["augmentation"],
            item["seed"],
        )
    )
    env = dict(os.environ)
    env["PYTHONPATH"] = str(Path("src").resolve())
    for item in matrix:
        name = (
            f"{item['kind']}-{item['loss']}-{'aug' if item['augmentation'] else 'plain'}-{item['seed']}.json"
        )
        config_path = config_dir / name
        config = json.loads(config_path.read_text())
        runs = matching_runs(root, config, manifest_hash)
        action, run = action_for(runs)
        print(f"{name}: {action} {run or ''}", flush=True)
        if args.dry_run or action == "done":
            continue
        if action in ("train", "resume"):
            command = [
                sys.executable,
                "-m",
                "netembed.cli",
                "train",
                "--data",
                str(data),
                "--config",
                str(config_path),
                "--output",
                str(root),
            ]
            if run is not None:
                command.extend(["--resume", str(run / "resume.pt")])
            subprocess.run(command, env=env, check=True)
            finished = [
                candidate
                for candidate in matching_runs(root, config, manifest_hash)
                if (candidate / "result.json").is_file()
            ]
            if not finished:
                raise RuntimeError(f"training produced no completed run for {name}")
            run = finished[0]
        subprocess.run(
            [
                sys.executable,
                "-m",
                "netembed.cli",
                "evaluate",
                "--data",
                str(data),
                "--bundle",
                str(run / "bundle"),
                "--split",
                "selection",
                "--output",
                str(run / "selection"),
            ],
            env=env,
            check=True,
        )
        subprocess.run(
            [
                sys.executable,
                "scripts/compare_runs.py",
                "--root",
                str(root),
                "--output",
                str(root / "comparison.json"),
            ],
            env=env,
            check=True,
        )


if __name__ == "__main__":
    main()
