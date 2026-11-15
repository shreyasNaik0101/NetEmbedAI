"""CPU timing boundaries for the existing TCN predictor; no fitting or model changes."""

import os
import platform
import time

import numpy as np
import torch

from .contract import validate_array


def prepare_tcn(predictor, raw):
    if predictor.meta["kind"] != "tcn":
        raise ValueError("stage benchmark supports the existing CPU TCN only")
    x, lengths = predictor.normalizer.batch([validate_array(raw)])
    return torch.from_numpy(x), torch.from_numpy(lengths)


def forward_tcn(predictor, prepared):
    with torch.inference_mode():
        return predictor.model(*prepared)[0]


def convert_probabilities(predictor, logits):
    with torch.inference_mode():
        return torch.softmax(logits / predictor.meta["policy"]["temperature"], 1).numpy()


def benchmark_stages(predictor, raw, calls=1000):
    if predictor.meta["provenance"].get("fixture"):
        raise ValueError("real trained artifact required for a performance report")
    if not 1000 <= calls <= 5000:
        raise ValueError("stage benchmark requires 1000..5000 calls")
    prepared = prepare_tcn(predictor, raw)
    logits = forward_tcn(predictor, prepared)
    prepared_scores = convert_probabilities(predictor, logits)
    delta = float(np.max(np.abs(prepared_scores - predictor.probabilities([raw]))))
    if delta > 1e-7:
        raise ValueError("benchmark path differs from shared predictor probabilities")
    callbacks = {
        "preprocessing": lambda: prepare_tcn(predictor, raw),
        "model_forward": lambda: forward_tcn(predictor, prepared),
        "probability_conversion": lambda: convert_probabilities(predictor, logits),
        "full_predictor": lambda: predictor.predict(raw),
    }
    stages = {}
    for name, callback in callbacks.items():
        for _ in range(50):
            callback()
        samples = []
        for _ in range(calls):
            start = time.perf_counter()
            callback()
            samples.append((time.perf_counter() - start) * 1000)
        stages[name] = {
            "p50_ms": float(np.percentile(samples, 50)),
            "p95_ms": float(np.percentile(samples, 95)),
        }
    return {
        "artifact_id": predictor.identity,
        "fixture": False,
        "hardware": {
            "os": platform.platform(),
            "processor": platform.processor(),
            "logical_cpus": os.cpu_count(),
        },
        "versions": {
            "python": platform.python_version(),
            "torch": torch.__version__,
            "numpy": np.__version__,
        },
        "torch_threads": torch.get_num_threads(),
        "packets": len(raw),
        "warmup_per_stage": 50,
        "calls_per_stage": calls,
        "probability_parity_maximum_delta": delta,
        "stage_order": list(callbacks),
        "stages": stages,
        "boundaries": {
            "preprocessing": "raw-array validation, saved normalization, padding and NumPy-to-CPU-tensor views",
            "model_forward": "CPU TCN forward including its existing embedding/classifier outputs; inference mode; prepared tensors reused",
            "probability_conversion": "saved temperature, softmax and NumPy view; existing logits reused",
            "full_predictor": "unmodified Predictor.predict including preprocessing, forward, probabilities, decision policy and response dictionary",
        },
        "limits": "Sequential isolated stage measurements on one recorded input. Percentiles are not additive. Excludes loading, API/Pydantic/JSON/HTTP, capture, observation wait and browser receipt/paint. Host-load dependent; not a throughput or hard-real-time guarantee.",
    }
