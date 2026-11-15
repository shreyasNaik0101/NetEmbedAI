"""One fixed frozen-pooling linear probe. Never starts capture or changes the app."""

import argparse
import json
import platform
import subprocess
import sys
import time
import warnings
import zipfile
from collections import Counter
from pathlib import Path

import numpy as np
import sklearn
import torch
from sklearn.exceptions import ConvergenceWarning
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from threadpoolctl import threadpool_limits

from netembed.browser_adaptation import check_roles, development, forest_weights
from netembed.bundle import sha256, write_json
from netembed.contract import BUDGETS, Flow
from netembed.data import read_split
from netembed.linear_probe import LinearProbe, PoolEncoder, WHEEL, WHEEL_SHA
from netembed.linear_probe_study import (
    bound_json,
    development_gate,
    guard_for,
    load_rows,
    prefix_training,
    read_config,
)


def note(**values):
    print(json.dumps(values), flush=True)


def run(args, cfg):
    out, upstream = Path(args.output), Path(args.upstream)
    if out.exists():
        raise FileExistsError(out)
    wheel = upstream / WHEEL
    if sha256(wheel) != WHEEL_SHA:
        raise ValueError("optional wheel changed")
    # Verify the isolated installed Python source against the pinned wheel.
    with zipfile.ZipFile(wheel) as archive:
        for name in archive.namelist():
            if name.startswith("cesnet_models/") and name.endswith(".py"):
                if (upstream / "python" / name).read_bytes() != archive.read(name):
                    raise ValueError("isolated upstream source changed")
    sys.path.insert(0, str((upstream / "python").resolve()))
    if sha256(Path(args.data) / "manifest.json") != cfg["data_manifest_sha256"]:
        raise ValueError("public data manifest changed")
    public, py, public_ids, manifest = read_split(args.data, "train")
    if len(public) != cfg["public_train_count"]:
        raise ValueError("public training count changed")
    labels = manifest["labels"]
    train_rows, train_proofs = load_rows(args.collection, "train", labels, cfg)
    local_train = [Flow(packets=r["packets"]).array() for r in train_rows]
    ly = np.array([labels.index(r["label"]) for r in train_rows])
    encoder = PoolEncoder(upstream / "30pktTCNET_256_CESNET_QUIC22_Week46_Domains.pth")
    frozen_state = {k: v.clone() for k, v in encoder.model.state_dict().items()}
    probes = [public[0][:b] for b in BUDGETS]
    first = encoder.encode(probes)
    independent = np.concatenate([encoder.encode([p]) for p in probes])
    if not np.allclose(first, independent, atol=1e-4, rtol=1e-4):
        raise ValueError("batch-dependent pooled features")
    # Record before feature extraction/fitting or any development scoring.
    out.mkdir(parents=True)
    provenance = {
        "fixture": False,
        "study": cfg,
        "config_sha256": sha256(args.config),
        "source_commit": subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
        "source_sha256": {
            p: sha256(p)
            for p in (
                "scripts/study_linear_probe.py",
                "src/netembed/linear_probe.py",
                "src/netembed/linear_probe_study.py",
                "src/netembed/pretrained_neighbors.py",
                "src/netembed/browser_adaptation.py",
                "src/netembed/data.py",
            )
        },
        "versions": {
            "python": platform.python_version(),
            "numpy": np.__version__,
            "torch": torch.__version__,
            "sklearn": sklearn.__version__,
            "cesnet_models": "0.4.1",
        },
        "training_ids": public_ids + [r["id"] for r in train_rows],
        "training_evidence": train_proofs,
        "layer_audit": {
            "dimensions": first.shape[1],
            "pool_equals_pre_refinement": True,
            "batch_vs_single_max_delta": float(np.max(np.abs(first - independent))),
            "frozen_parameters": True,
        },
    }
    write_json(out / "protocol.json", provenance)
    mass = forest_weights(len(public), ly, cfg["local_fraction"]) * (len(public) + len(ly))
    flows, targets, weights = prefix_training(public + local_train, np.concatenate([py, ly]), mass)
    start = time.perf_counter()

    def progress(done, total):
        if done % 4096 == 0 or done == total:
            note(stage="training_features", done=done, total=total)

    features = encoder.encode(flows, cfg["batch_size"], progress)
    extraction_seconds = time.perf_counter() - start
    scaler = StandardScaler().fit(features, sample_weight=weights)
    x = scaler.transform(features.astype(np.float64))
    head = LogisticRegression(**cfg["head"])
    note(stage="fit_one_linear_head", rows=len(x), dimensions=x.shape[1])
    start = time.perf_counter()
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always", ConvergenceWarning)
        head.fit(x, targets, sample_weight=weights)
    converged = not any(issubclass(w.category, ConvergenceWarning) for w in caught)
    fitting = {
        "converged": converged,
        "iterations": head.n_iter_.tolist(),
        "seconds": time.perf_counter() - start,
        "extraction_seconds": extraction_seconds,
        "warnings": [str(w.message) for w in caught],
        "training_prefix_rows": len(x),
    }
    write_json(out / "fit.json", fitting)
    if not converged:
        note(stage="stopped_nonconvergence", **fitting)
        return
    if not np.array_equal(head.classes_, np.arange(len(labels))):
        raise ValueError("head label order changed")
    model = LinearProbe(encoder, labels, scaler.mean_, scaler.scale_, head.coef_, head.intercept_, provenance)
    delta = float(np.max(np.abs(model.from_features(features[:128]) - head.predict_proba(x[:128]))))
    if delta > 1e-5:
        raise ValueError("portable head differs from sklearn")
    model.save(out / "bundle", wheel)
    loaded = LinearProbe.load(out / "bundle")
    # The fitted artifact is saved before development inputs are loaded.
    rows, selection_proofs = load_rows(args.collection, "selection", labels, cfg)
    check_roles(train_rows, rows)
    if max(
        p.get("observed_packet_range_unix_ms", p["first_packet_range_unix_ms"])[1]
        for p in train_proofs.values()
    ) >= min(p["first_packet_range_unix_ms"][0] for p in selection_proofs.values()):
        raise ValueError("local training and selection chronology overlaps")
    local = [Flow(packets=r["packets"]).array() for r in rows]
    local_y = np.array([labels.index(r["label"]) for r in rows])
    control, cy, ids, _ = read_split(args.data, "selection")
    counts, chosen = Counter(), []
    for i, label in enumerate(cy):
        if counts[int(label)] < cfg["public_control_per_class"]:
            chosen.append(i)
            counts[int(label)] += 1
    if len(chosen) != cfg["public_control_per_class"] * len(labels):
        raise ValueError("missing control class")
    control, cy, ids = [control[i] for i in chosen], cy[chosen], [ids[i] for i in chosen]
    metrics, predictions = development(loaded, control, cy, local, local_y, rows)
    write_json(out / "local-predictions.json", predictions)
    references = {k: bound_json(v) for k, v in cfg["references"].items()}
    keys = [(p["id"], p["observed_packets"], p["reference"]) for p in predictions]
    for name in ("b17", "previous_forest", "recent_forest"):
        if keys != [
            (p["id"], p["observed_packets"], p["reference"]) for p in references[name + "_predictions"]
        ]:
            raise ValueError("paired comparison case inventory differs")
    control_predictions = []
    for b in BUDGETS:
        probabilities = loaded.probabilities([raw[:b] for raw in control])
        control_predictions.extend(
            {
                "id": ident,
                "observed_packets": min(len(raw), b),
                "requested_cap": b,
                "reference": labels[int(y)],
                "top1": labels[int(p.argmax())],
                "probabilities": p.tolist(),
            }
            for raw, y, ident, p in zip(control, cy, ids, probabilities)
        )
    write_json(out / "control-predictions.json", control_predictions)
    max_delta = 0.0
    for row in predictions:
        raw = local[next(i for i, r in enumerate(rows) if r["id"] == row["id"])][: row["observed_packets"]]
        a, b = model.probabilities([raw])[0], loaded.probabilities([raw])[0]
        max_delta = max(max_delta, float(np.max(np.abs(a - b))))
        if loaded.predict(raw)["label"] is not None:
            raise ValueError("uncalibrated model must withhold")
    if max_delta != 0 or any(
        not torch.equal(v, encoder.model.state_dict()[k]) for k, v in frozen_state.items()
    ):
        raise ValueError("save/load or frozen encoder state changed")
    benchmark = cfg["benchmark"]
    raw = Flow(**bound_json(benchmark)).array()
    for _ in range(benchmark["warmup"]):
        loaded.predict(raw)
    times = []
    for _ in range(benchmark["calls"]):
        start = time.perf_counter()
        loaded.predict(raw)
        times.append((time.perf_counter() - start) * 1000)
    gate = development_gate(metrics, references, cfg)
    report = {
        "metrics": metrics,
        "fit": fitting,
        "gates": gate,
        "worthy_of_independent_validation": all(gate.values()),
        "default_promoted": False,
        "policy_fitted": False,
        "final_evaluation": False,
        "new_capture": False,
        "references": {k: references[k] for k in ("b17", "previous_forest", "recent_forest")},
        "selection_evidence": selection_proofs,
        "control_ids": ids,
        "parity": {
            "local_cases": len(predictions),
            "save_load_max_delta": max_delta,
            "sklearn_head_max_delta": delta,
            "encoder_state_unchanged": True,
        },
        "cpu": {
            "calls": len(times),
            "warmup": benchmark["warmup"],
            "threads": cfg["threads"],
            "input_sha256": benchmark["sha256"],
            "actual_packets": len(raw),
            "p50_ms": float(np.percentile(times, 50)),
            "p95_ms": float(np.percentile(times, 95)),
            "boundary": "single-flow frozen encoder, head and reply; no capture/HTTP/UI",
        },
        "checksums": {p.name: sha256(p) for p in out.glob("*.json")},
        "artifact_metadata_sha256": sha256(out / "bundle/metadata.json"),
        "limitations": [cfg["selection_limit"], cfg["public_control_limit"], cfg["paper_limits"]],
    }
    write_json(out / "report.json", report)
    note(stage="complete", metrics=metrics, gates=gate, parity=report["parity"], cpu=report["cpu"])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", default="configs/pool-linear-probe-v1.json")
    parser.add_argument("--data", default="data/processed/v2")
    parser.add_argument("--collection", default="artifacts/local/browser-development")
    parser.add_argument("--upstream", default="artifacts/local/upstream-models")
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    cfg = read_config(args.config)
    sys.addaudithook(guard_for(cfg))
    torch.set_num_threads(cfg["threads"])
    torch.use_deterministic_algorithms(True)
    torch.manual_seed(cfg["seed"])
    with threadpool_limits(limits=cfg["threads"]):
        run(args, cfg)


if __name__ == "__main__":
    main()
