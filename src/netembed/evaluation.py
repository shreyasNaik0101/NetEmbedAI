"""Predictions are the source of reports; no stored historical metrics are imported."""

import time
import platform
import numpy as np
import torch
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix, f1_score
from .contract import BUDGETS
from .transforms import perturb

STRESS = {"clean": None, "timing": 5.0, "padding": 128, "observation_loss": 0.1}


def metrics(y, probabilities, labels, threshold=1.0, fitted=False):
    scores = np.asarray(probabilities)
    y = np.asarray(y)
    predicted = scores.argmax(1)
    accepted = scores.max(1) >= threshold if fitted else np.zeros(len(y), dtype=bool)
    return {
        "n": len(y),
        "accuracy": accuracy_score(y, predicted),
        "macro_f1": f1_score(y, predicted, labels=list(range(len(labels))), average="macro", zero_division=0),
        "classes": classification_report(
            y,
            predicted,
            labels=list(range(len(labels))),
            target_names=labels,
            output_dict=True,
            zero_division=0,
        ),
        "confusion": confusion_matrix(y, predicted, labels=list(range(len(labels)))).tolist(),
        "coverage": float(accepted.mean()),
        "accepted_error": float((predicted[accepted] != y[accepted]).mean()) if accepted.any() else None,
    }


def evaluate(predictor, flows, y, ids):
    rows, reports = [], {}
    cohorts = [
        ("matched_30", [i for i, x in enumerate(flows) if len(x) >= 30]),
        ("all_flows", list(range(len(flows)))),
    ]
    for budget in BUDGETS:
        for kind, severity in STRESS.items():
            inputs, overhead = [], []
            for x, ident in zip(flows, ids):
                x = x[:budget]
                if severity is not None:
                    x, info = perturb(x, kind, severity, 2026, ident)
                else:
                    info = {}
                inputs.append(x)
                overhead.append(info)
            batch_size = 128 if predictor.meta["kind"] == "tcn" else 4096
            probs = np.concatenate(
                [
                    predictor.probabilities(inputs[j : j + batch_size])
                    for j in range(0, len(inputs), batch_size)
                ]
            )
            policy = predictor.meta["policy"]
            for cohort, indices in cohorts:
                if not indices:
                    continue
                key = f"{cohort}/{budget}/{kind}"
                reports[key] = metrics(
                    y[indices], probs[indices], predictor.labels, policy["threshold"], policy["fitted"]
                )
                for i in indices:
                    rows.append(
                        {
                            "protocol": key,
                            "id": ids[i],
                            "truth": int(y[i]),
                            "scores": probs[i].tolist(),
                            "observed": len(inputs[i]),
                            "overhead": overhead[i],
                        }
                    )
    return {"artifact_id": predictor.identity, "protocols": reports, "stress_seed": 2026}, rows


def fit_policy(predictor, flows, y, target_error=0.1):
    # Policy population is uniform checkpoints, same mixture as training.
    xs, ys = [], []
    for x, label in zip(flows, y):
        for budget in BUDGETS:
            if len(x) >= budget:
                xs.append(x[:budget])
                ys.append(label)
    if not xs:
        raise ValueError("no calibration prefixes")
    batch_size = 128 if predictor.meta["kind"] == "tcn" else 4096
    scores = np.concatenate(
        [predictor.probabilities(xs[j : j + batch_size]) for j in range(0, len(xs), batch_size)]
    )
    truth = np.asarray(ys)
    curve = []
    for threshold in np.linspace(0, 1, 101):
        keep = scores.max(1) >= threshold
        error = float((scores.argmax(1)[keep] != truth[keep]).mean()) if keep.any() else None
        curve.append(
            {
                "threshold": float(threshold),
                "coverage": float(keep.mean()),
                "error": error,
                "accepted": int(keep.sum()),
            }
        )
    viable = [r for r in curve if r["accepted"] >= 30 and r["error"] <= target_error]
    chosen = max(viable, key=lambda r: r["coverage"]) if viable else None
    return {
        "version": "calibration-coverage-v1",
        "threshold": chosen["threshold"] if chosen else 1.0,
        "min_packets": 5,
        "temperature": 1.0,
        "fitted": chosen is not None,
        "target_error": target_error,
        "curve": curve,
        "note": "empirical calibration subset; not a correctness guarantee",
    }


def benchmark(predictor, flow, calls=1000):
    if calls < 1000:
        raise ValueError("benchmark requires at least 1000 calls")
    for _ in range(50):
        predictor.predict(flow)
    times = []
    for _ in range(calls):
        start = time.perf_counter()
        predictor.predict(flow)
        times.append((time.perf_counter() - start) * 1000)
    batches = []
    for _ in range(100):
        start = time.perf_counter()
        predictor.probabilities([flow] * 32)
        batches.append(time.perf_counter() - start)
    return {
        "artifact_id": predictor.identity,
        "fixture": predictor.meta["provenance"].get("fixture", False),
        "hardware": platform.platform() + " / " + platform.processor(),
        "torch": torch.__version__,
        "threads": torch.get_num_threads(),
        "warmup": 50,
        "calls": calls,
        "pipeline_p50_ms": float(np.percentile(times, 50)),
        "pipeline_p95_ms": float(np.percentile(times, 95)),
        "batch32_flows_per_second": float(32 / np.mean(batches)),
        "http_and_capture_latency": "not measured by this command",
    }
