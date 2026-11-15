"""Fit one fixed set of checkpoint heads; preserve all earlier experiments."""

import argparse
import json
import platform
import subprocess
import sys
import time
import warnings
from collections import Counter
from pathlib import Path

import numpy as np
import sklearn
import torch
from sklearn.exceptions import ConvergenceWarning
from sklearn.linear_model import LogisticRegression
from threadpoolctl import threadpool_limits

from netembed.browser_adaptation import check_roles, forest_weights
from netembed.bundle import sha256, write_json
from netembed.contract import BUDGETS, Flow
from netembed.data import read_split
from netembed.linear_probe import LinearProbe, WHEEL, WHEEL_SHA
from netembed.linear_probe_study import bound_json, guard_for, load_rows
from netembed.prefix_probe import PrefixProbe
from netembed.prefix_probe_study import gates, read_config, summarize, validate_recovery


def note(**values):
    print(json.dumps(values), flush=True)


def score(model, flows, targets, ids, local):
    result = []
    for budget in BUDGETS:
        indices = [i for i, raw in enumerate(flows) if not local or len(raw) >= budget]
        raw = [flows[i][:budget] for i in indices]
        probabilities = model.probabilities(raw, budget)
        for i, values, x in zip(indices, probabilities, raw):
            result.append(
                {
                    "id": ids[i],
                    "reference": model.labels[int(targets[i])],
                    "observed_packets": len(x),
                    "requested_cap": budget,
                    "head_budget": budget,
                    "top1": model.labels[int(values.argmax())],
                    "probabilities": values.tolist(),
                }
            )
    return result


def run(args, declaration, cfg):
    out = Path(args.output)
    if out.exists():
        raise FileExistsError(out)
    validate_recovery(declaration, cfg)
    shared_meta = bound_json(declaration["shared_metadata"])
    shared_report = bound_json(declaration["shared_report"])
    shared_predictions = bound_json(declaration["shared_predictions"])
    shared_protocol = bound_json(declaration["shared_protocol"])
    base_path = Path(declaration["shared_bundle"])
    if base_path / "metadata.json" != Path(declaration["shared_metadata"]["path"]):
        raise ValueError("shared bundle binding differs")
    wheel = base_path / WHEEL
    if sha256(wheel) != WHEEL_SHA:
        raise ValueError("pinned optional wheel changed")
    sys.path.insert(0, str(wheel.resolve()))
    base = LinearProbe.load(base_path)
    if base.provenance != shared_meta["provenance"] or base.provenance != shared_protocol:
        raise ValueError("shared preprocessing provenance differs")
    if sha256(Path(args.data) / "manifest.json") != cfg["data_manifest_sha256"]:
        raise ValueError("public manifest changed")
    public, py, pids, manifest = read_split(args.data, "train")
    if len(public) != cfg["public_train_count"] or manifest["labels"] != base.labels:
        raise ValueError("public training inventory differs")
    rows, proofs = load_rows(args.collection, "train", base.labels, cfg)
    train_ids = pids + [r["id"] for r in rows]
    if train_ids != shared_protocol["training_ids"] or proofs != shared_protocol["training_evidence"]:
        raise ValueError("paired training data differs from shared head")
    raw = public + [Flow(packets=r["packets"]).array() for r in rows]
    ly = np.array([base.labels.index(r["label"]) for r in rows])
    targets = np.concatenate([py, ly])
    weights = forest_weights(len(public), ly, cfg["local_fraction"]) * len(raw) / len(BUDGETS)
    before = {k: v.clone() for k, v in base.encoder.model.state_dict().items()}
    out.mkdir(parents=True)
    provenance = {
        "fixture": False,
        "declaration": declaration,
        "inherited_config": cfg,
        "config_sha256": sha256(args.config),
        "source_commit": subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
        "source_sha256": {
            p: sha256(p)
            for p in (
                "scripts/study_prefix_probe.py",
                "src/netembed/prefix_probe.py",
                "src/netembed/prefix_probe_study.py",
                "src/netembed/linear_probe.py",
                "src/netembed/linear_probe_study.py",
                "src/netembed/browser_adaptation.py",
            )
        },
        "versions": {
            "python": platform.python_version(),
            "numpy": np.__version__,
            "torch": torch.__version__,
            "sklearn": sklearn.__version__,
            "cesnet_models": "0.4.1",
        },
        "training_ids": train_ids,
        "training_evidence": proofs,
        "scaler_source_sha256": sha256(base_path / "head.json"),
        "training_flows_per_head": len(raw),
        "weight_sum_per_head": float(weights.sum()),
    }
    write_json(out / "protocol.json", provenance)
    heads, fits = {}, {}
    for budget in BUDGETS:
        start = time.perf_counter()

        def progress(done, total):
            if done % 4096 == 0 or done == total:
                note(stage="training_features", budget=budget, done=done, total=total)

        features = base.encoder.encode([x[:budget] for x in raw], cfg["batch_size"], progress)
        extraction = time.perf_counter() - start
        x = (features.astype(np.float64) - base.mean) / base.scale
        head = LogisticRegression(**cfg["head"])
        note(stage="fit_head", budget=budget)
        start = time.perf_counter()
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always", ConvergenceWarning)
            head.fit(x, targets, sample_weight=weights)
        converged = not any(issubclass(w.category, ConvergenceWarning) for w in caught)
        fits[str(budget)] = {
            "converged": converged,
            "iterations": head.n_iter_.tolist(),
            "fit_seconds": time.perf_counter() - start,
            "extraction_seconds": extraction,
            "warnings": [str(w.message) for w in caught],
        }
        write_json(out / "fit.json", fits)
        if not converged:
            note(stage="stopped_nonconvergence", budget=budget, fit=fits[str(budget)])
            return
        if not np.array_equal(head.classes_, np.arange(len(base.labels))):
            raise ValueError("head label order changed")
        heads[budget] = {"coefficients": head.coef_.tolist(), "intercept": head.intercept_.tolist()}
        portable = LinearProbe(base.encoder, base.labels, base.mean, base.scale, **heads[budget])
        delta = float(np.max(np.abs(portable.from_features(features[:128]) - head.predict_proba(x[:128]))))
        if delta > 1e-12:
            raise ValueError("portable checkpoint head differs from sklearn")
        fits[str(budget)]["portable_max_delta"] = delta
        write_json(out / f"head-{budget}.json", heads[budget])
        write_json(out / "fit.json", fits)
        note(stage="head_complete", budget=budget, fit=fits[str(budget)])
    model = PrefixProbe(base, heads, provenance)
    model.save(out / "bundle", wheel)
    loaded = PrefixProbe.load(out / "bundle")
    # No selection inputs or predictions are scored until every head is frozen.
    selection, selection_proofs = load_rows(args.collection, "selection", base.labels, cfg)
    check_roles(rows, selection)
    if max(
        p.get("observed_packet_range_unix_ms", p["first_packet_range_unix_ms"])[1] for p in proofs.values()
    ) >= min(p["first_packet_range_unix_ms"][0] for p in selection_proofs.values()):
        raise ValueError("local chronology overlaps")
    local = [Flow(packets=r["packets"]).array() for r in selection]
    y = np.array([base.labels.index(r["label"]) for r in selection])
    control, cy, ids, _ = read_split(args.data, "selection")
    counts, chosen = Counter(), []
    for i, label in enumerate(cy):
        if counts[int(label)] < cfg["public_control_per_class"]:
            chosen.append(i)
            counts[int(label)] += 1
    control, cy, ids = [control[i] for i in chosen], cy[chosen], [ids[i] for i in chosen]
    if ids != shared_report["control_ids"]:
        raise ValueError("paired public control differs")
    predictions = score(loaded, local, y, [r["id"] for r in selection], True)
    control_predictions = score(loaded, control, cy, ids, False)
    write_json(out / "local-predictions.json", predictions)
    write_json(out / "control-predictions.json", control_predictions)
    keys = [(r["id"], r["observed_packets"], r["reference"]) for r in predictions]
    if keys != [(r["id"], r["observed_packets"], r["reference"]) for r in shared_predictions]:
        raise ValueError("paired local cases differ")
    references = {k: bound_json(v) for k, v in cfg["references"].items()}
    for name in ("b17", "previous_forest", "recent_forest"):
        if keys != [
            (r["id"], r["observed_packets"], r["reference"]) for r in references[name + "_predictions"]
        ]:
            raise ValueError("forest comparison inventory differs")
    metrics = summarize(predictions, control_predictions, base.labels)
    checks = gates(metrics, references, shared_report["metrics"], cfg, declaration)
    # Same-batch replay checks the saved probability vectors as well as labels.
    replay = score(model, local, y, [r["id"] for r in selection], True)
    delta = max(
        float(np.max(np.abs(np.array(a["probabilities"]) - b["probabilities"])))
        for a, b in zip(replay, predictions)
    )
    if delta != 0 or any(not torch.equal(v, base.encoder.model.state_dict()[k]) for k, v in before.items()):
        raise ValueError("frozen state or artifact parity changed")
    if not np.array_equal(loaded.base.mean, base.mean) or not np.array_equal(loaded.base.scale, base.scale):
        raise ValueError("saved scaler changed")
    example = Flow(**bound_json(cfg["benchmark"])).array()
    cpu = {}
    for budget in BUDGETS:
        for _ in range(cfg["benchmark"]["warmup"]):
            loaded.predict(example[:budget], budget)
        times = []
        for _ in range(cfg["benchmark"]["calls"]):
            start = time.perf_counter()
            reply = loaded.predict(example[:budget], budget)
            times.append((time.perf_counter() - start) * 1000)
            if reply["label"] is not None:
                raise ValueError("uncalibrated head must withhold")
        cpu[str(budget)] = {
            "p50_ms": float(np.percentile(times, 50)),
            "p95_ms": float(np.percentile(times, 95)),
        }
    report = {
        "metrics": metrics,
        "fit": fits,
        "gates": checks,
        "worthy_of_independent_validation": all(checks.values()),
        "default_promoted": False,
        "new_capture": False,
        "policy_fitted": False,
        "final_evaluation": False,
        "shared_metrics": shared_report["metrics"],
        "references": {k: references[k] for k in ("b17", "previous_forest", "recent_forest")},
        "selection_evidence": selection_proofs,
        "control_ids": ids,
        "parity": {
            "local_cases": len(predictions),
            "save_load_max_delta": delta,
            "frozen_encoder_unchanged": True,
            "shared_scaler_unchanged": True,
        },
        "cpu": {
            "by_budget": cpu,
            "threads": cfg["threads"],
            "warmup": cfg["benchmark"]["warmup"],
            "calls_per_budget": cfg["benchmark"]["calls"],
            "input_sha256": cfg["benchmark"]["sha256"],
            "boundary": "single-flow encoder/head/reply; excludes capture, queue, HTTP, UI",
        },
        "checksums": {p.name: sha256(p) for p in out.glob("*.json")},
        "artifact_metadata_sha256": sha256(out / "bundle/metadata.json"),
        "limitations": [
            declaration["limits"],
            cfg["selection_limit"],
            cfg["public_control_limit"],
            cfg["paper_limits"],
        ],
    }
    write_json(out / "report.json", report)
    note(stage="complete", metrics=metrics, gates=checks, parity=report["parity"], cpu=report["cpu"])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", default="configs/prefix-linear-probe-v1.json")
    parser.add_argument("--data", default="data/processed/v2")
    parser.add_argument("--collection", default="artifacts/local/browser-development")
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    declaration, cfg = read_config(args.config)
    sys.addaudithook(guard_for(cfg))
    torch.set_num_threads(cfg["threads"])
    torch.use_deterministic_algorithms(True)
    torch.manual_seed(cfg["seed"])
    with threadpool_limits(limits=cfg["threads"]):
        run(args, declaration, cfg)


if __name__ == "__main__":
    main()
