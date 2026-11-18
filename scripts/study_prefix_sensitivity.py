"""One fixed, offline development sensitivity diagnostic; no training or capture."""

from collections import Counter
import hashlib
import json
import os
from pathlib import Path
import sys

import numpy as np
import torch
from threadpoolctl import threadpool_limits

from netembed.bundle import Predictor, sha256, write_json
from netembed.contract import Flow
from netembed.prefix_sensitivity import views

CONFIG = Path("configs/prefix-sensitivity-dev-v1.json")
CONFIG_SHA = "529288579fa82ba9424271190196ae77022783a023b4c283e156fe15c89e5a08"
OUTPUT = Path("experiments/prefix-sensitivity-dev-v1")


def guard(event, args, cfg):
    if event in ("socket.connect", "socket.getaddrinfo"):
        raise ValueError("development diagnostic is offline")
    if event != "open" or not isinstance(args[0], (str, bytes)):
        return
    path = Path(os.fsdecode(args[0])).resolve()
    if path.is_relative_to(Path("data").resolve()):
        raise ValueError("training, public calibration and final data excluded")
    if path.is_relative_to(Path("artifacts/local").resolve()) and path not in [
        Path(p).resolve() for p in cfg["inputs"]
    ]:
        raise ValueError("unrelated private, calibration or final capture excluded")
    if path.is_relative_to(Path("experiments").resolve()) and not (
        path.is_relative_to(Path(cfg["source_bundle"]).resolve())
        or path == Path(cfg["baseline_predictions"]).resolve()
        or path.is_relative_to(OUTPUT.resolve())
    ):
        raise ValueError("other experiment data excluded")


def main():
    raw = CONFIG.read_bytes().replace(b"\r\n", b"\n")
    if hashlib.sha256(raw).hexdigest() != CONFIG_SHA:
        raise ValueError("fixed diagnostic declaration changed")
    cfg = json.loads(raw)
    if OUTPUT.exists():
        raise FileExistsError("preserve existing sensitivity results")
    sys.addaudithook(lambda event, args: guard(event, args, cfg))
    torch.set_num_threads(2)
    for path, digest in cfg["inputs"].items():
        if sha256(path) != digest:
            raise ValueError("declared development input changed")
    if sha256(cfg["baseline_predictions"]) != cfg["baseline_predictions_sha256"]:
        raise ValueError("saved development baseline changed")
    model = Predictor(cfg["source_bundle"])
    if (
        model.identity != cfg["source_artifact_id"]
        or model.fixed_prefix_packets != 10
        or model.meta["policy"]["fitted"]
        or model.meta["provenance"].get("fixture", True)
        or sha256(Path(cfg["source_bundle"]) / "forest.json") != cfg["source_weight_sha256"]
    ):
        raise ValueError("frozen genuine uncalibrated model differs")
    baseline = json.loads(Path(cfg["baseline_predictions"]).read_text())
    index = {(row["domain"], row["id"]): row for row in baseline if row["domain"] in ("local", "spotify")}
    if len(index) != 21:
        raise ValueError("baseline support or identity differs")
    rows = []
    for path in cfg["inputs"]:
        p = Path(path)
        parsed = (
            [json.loads(line) for line in p.read_text().splitlines() if line.strip()]
            if p.suffix == ".jsonl"
            else json.loads(p.read_text())
        )
        domain = "spotify" if p.suffix == ".json" else "local"
        rows.extend(
            {**row, "domain": domain}
            for row in parsed
            if row["label"] in cfg["expected_counts"] and len(row["packets"]) >= 10
        )
    if (
        Counter(row["label"] for row in rows) != Counter(cfg["expected_counts"])
        or len({row["id"] for row in rows}) != 21
    ):
        raise ValueError("fixed development support differs")
    predictions = []
    with threadpool_limits(limits=2):
        for row in rows:
            inputs, swap_index = views(Flow(packets=row["packets"]).array())
            probabilities = model.probabilities(list(inputs.values()))
            old = index[(row["domain"], row["id"])]
            if (
                old["reference"] != row["label"]
                or old["observed_packets"] != 10
                or not np.allclose(probabilities[0], old["probabilities"], atol=1e-12, rtol=0)
            ):
                raise ValueError("unchanged source does not reproduce the frozen development baseline")
            for (name, arr), p in zip(inputs.items(), probabilities):
                predictions.append(
                    {
                        "id": row["id"],
                        "reference": row["label"],
                        "domain": row["domain"],
                        "view": name,
                        "top1": model.labels[int(p.argmax())],
                        "probabilities": p.tolist(),
                        "input_sha256": hashlib.sha256(arr.astype("<f4").tobytes()).hexdigest(),
                        "swap_index": swap_index if name.startswith("first_opposite") else None,
                    }
                )
    grouped = {}
    for label in cfg["expected_counts"]:
        class_rows = [r for r in predictions if r["reference"] == label]
        clean = {r["id"]: r for r in class_rows if r["view"] == "unchanged"}
        grouped[label] = {}
        for name in cfg["views"]:
            current = [r for r in class_rows if r["view"] == name]
            grouped[label][name] = {
                "n": len(current),
                "correct_top1": sum(r["top1"] == label for r in current),
                "top1_changes": sum(r["top1"] != clean[r["id"]]["top1"] for r in current),
                "max_score_shift": max(
                    float(np.max(np.abs(np.asarray(r["probabilities"]) - clean[r["id"]]["probabilities"])))
                    for r in current
                ),
                **(
                    {"swaps_applied": sum(r["swap_index"] is not None for r in current)}
                    if name.startswith("first_opposite")
                    else {}
                ),
            }
    OUTPUT.mkdir(parents=True, exist_ok=False)
    write_json(OUTPUT / "predictions.json", predictions)
    report = {
        "fixture": False,
        "status": "descriptive_development_only",
        "config_sha256": CONFIG_SHA,
        "model_id": model.identity,
        "weights_refitted": False,
        "threshold_fitted": False,
        "capture_started": False,
        "final_data_opened": False,
        "fresh_accuracy_claim": False,
        "unchanged_reproduced": 21,
        "results": grouped,
        "limits": cfg["limits"],
        "transform_sha256": sha256(Path("src/netembed/prefix_sensitivity.py")),
        "runner_sha256": sha256(Path(__file__)),
        "predictions_sha256": sha256(OUTPUT / "predictions.json"),
    }
    write_json(OUTPUT / "report.json", report)
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
