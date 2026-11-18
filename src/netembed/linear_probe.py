"""Offline frozen global-pooling features and a portable, uncalibrated linear head."""

import json
import shutil
from pathlib import Path

import numpy as np
import torch

from .bundle import sha256, write_json
from .contract import validate_array
from .pretrained_neighbors import FrozenEncoder, UPSTREAM_VERSION, packet_batch

VERSION = "cesnet-pool-linear-probe-v1"
DIMENSIONS = 448
WEIGHT_SHA = "dc4b3333388239ac25b8c028c922965e2333cc151dd5fad951950099e86fabc4"
WHEEL_SHA = "86acb26e5c1595e2d80546bc44859e3d0daf271a20cbb7fbc829fd513a56154b"
WHEEL = "cesnet_models-0.4.1-py3-none-any.whl"
REPRESENTATION = {
    "schema": "1",
    "channels": ["iat_ms", "direction", "payload_bytes"],
    "direction": "+1 client-to-server; -1 server-to-client",
    "layout": "batch,3,30; actual prefix only, zero padding",
    "readout": "backbone_model.cnn_ppi_global_pool output, before mlp_shared",
    "dimensions": DIMENSIONS,
    "embedding_normalization": "none; training-only weighted StandardScaler in head",
    "packet_size_repair": "none; official published weights unchanged",
}


class PoolEncoder(FrozenEncoder):
    def __init__(self, weights, expected_sha256=WEIGHT_SHA):
        if expected_sha256 != WEIGHT_SHA:
            raise ValueError("only the declared official weights are supported")
        super().__init__(weights, expected_sha256)
        self.model.requires_grad_(False)
        backbone = self.model.backbone_model
        if backbone.use_mlp_flowstats or not backbone.use_mlp_shared:
            raise ValueError("unexpected official pooling architecture")

    def encode(self, flows, batch_size=128, progress=None):
        if not flows or not 1 <= batch_size <= 256:
            raise ValueError("invalid bounded embedding batch")
        if any(m.training for m in self.model.modules()):
            raise ValueError("frozen encoder must stay in evaluation mode")
        results, pooled, refinement_inputs = [], [], []
        backbone = self.model.backbone_model
        # Observe the actual upstream execution instead of reimplementing its stem.
        pool_hook = backbone.cnn_ppi_global_pool.register_forward_hook(
            lambda module, inputs, output: pooled.append(output.detach().clone())
        )
        refinement_hook = backbone.mlp_shared.register_forward_pre_hook(
            lambda module, inputs: refinement_inputs.append(inputs[0].detach().clone())
        )
        try:
            with torch.inference_mode():
                for i in range(0, len(flows), batch_size):
                    pooled.clear()
                    refinement_inputs.clear()
                    values = self.transform(packet_batch(flows[i : i + batch_size]))
                    self.model(torch.from_numpy(values))
                    if (
                        len(pooled) != 1
                        or len(refinement_inputs) != 1
                        or not torch.equal(pooled[0], refinement_inputs[0])
                        or pooled[0].shape != (len(values), DIMENSIONS)
                        or not torch.isfinite(pooled[0]).all()
                    ):
                        raise ValueError("pool output does not match pre-refinement features")
                    results.append(pooled[0].numpy())
                    if progress is not None:
                        progress(min(i + batch_size, len(flows)), len(flows))
        finally:
            pool_hook.remove()
            refinement_hook.remove()
        return np.concatenate(results)


class LinearProbe:
    def __init__(self, encoder, labels, mean, scale, coefficients, intercept, provenance=None):
        self.encoder, self.labels = encoder, list(labels)
        self.mean, self.scale, self.coef, self.intercept = (
            np.asarray(value, dtype=np.float64) for value in (mean, scale, coefficients, intercept)
        )
        if (
            len(labels) < 3
            or len(set(labels)) != len(labels)
            or not all(isinstance(label, str) and label for label in labels)
            or self.mean.shape != (DIMENSIONS,)
            or self.scale.shape != (DIMENSIONS,)
            or self.coef.shape != (len(labels), DIMENSIONS)
            or self.intercept.shape != (len(labels),)
            or np.any(self.scale <= 0)
            or not all(np.isfinite(a).all() for a in (self.mean, self.scale, self.coef, self.intercept))
        ):
            raise ValueError("invalid saved linear probe")
        self.provenance = provenance or {}

    def from_features(self, features):
        features = np.asarray(features, dtype=np.float64)
        if features.ndim != 2 or features.shape[1] != DIMENSIONS or not np.isfinite(features).all():
            raise ValueError("invalid pooled features")
        logits = ((features - self.mean) / self.scale) @ self.coef.T + self.intercept
        logits -= logits.max(axis=1, keepdims=True)
        probabilities = np.exp(logits)
        return probabilities / probabilities.sum(axis=1, keepdims=True)

    def probabilities(self, flows):
        return self.from_features(self.encoder.encode(flows))

    def predict(self, raw):
        raw = validate_array(raw)
        probabilities = self.probabilities([raw])[0]
        order = np.argsort(-probabilities, kind="stable")
        return {
            "label": None,
            "status": "uncalibrated" if len(raw) >= 5 else "insufficient_evidence",
            "observed_packets": len(raw),
            "raw_top1": self.labels[int(order[0])],
            "alternatives": [
                {"label": self.labels[int(i)], "uncalibrated_probability": float(probabilities[i])}
                for i in order[:3]
            ],
        }

    def save(self, destination, wheel):
        if sha256(wheel) != WHEEL_SHA or sha256(self.encoder.weights) != WEIGHT_SHA:
            raise ValueError("upstream artifact changed")
        destination = Path(destination)
        destination.mkdir(parents=True, exist_ok=False)
        shutil.copyfile(self.encoder.weights, destination / "encoder.pth")
        shutil.copyfile(wheel, destination / WHEEL)
        write_json(
            destination / "head.json",
            {
                "mean": self.mean.tolist(),
                "scale": self.scale.tolist(),
                "coefficients": self.coef.tolist(),
                "intercept": self.intercept.tolist(),
            },
        )
        write_json(
            destination / "metadata.json",
            {
                "version": VERSION,
                "labels": self.labels,
                "representation": REPRESENTATION,
                "upstream_version": UPSTREAM_VERSION,
                "weight_sha256": WEIGHT_SHA,
                "transform": self.encoder.transform.to_dict(),
                "provenance": self.provenance,
                "policy": {"fitted": False, "decision": "always withhold; raw ranking only"},
            },
        )
        files = ("metadata.json", "head.json", "encoder.pth", WHEEL)
        write_json(destination / "checksums.json", {p: sha256(destination / p) for p in files})

    @classmethod
    def load(cls, source):
        source = Path(source)
        checksums = json.loads((source / "checksums.json").read_text())
        if (
            set(checksums) != {"metadata.json", "head.json", "encoder.pth", WHEEL}
            or any(sha256(source / k) != v for k, v in checksums.items())
            or checksums["encoder.pth"] != WEIGHT_SHA
            or checksums[WHEEL] != WHEEL_SHA
        ):
            raise ValueError("linear probe checksum mismatch")
        meta = json.loads((source / "metadata.json").read_text())
        if (
            meta["version"] != VERSION
            or meta["representation"] != REPRESENTATION
            or meta["upstream_version"] != UPSTREAM_VERSION
            or meta["weight_sha256"] != WEIGHT_SHA
            or meta["policy"] != {"fitted": False, "decision": "always withhold; raw ranking only"}
            or meta["provenance"].get("fixture")
        ):
            raise ValueError("unsupported linear probe artifact")
        encoder = PoolEncoder(source / "encoder.pth")
        if meta["transform"] != encoder.transform.to_dict():
            raise ValueError("saved upstream preprocessing changed")
        head = json.loads((source / "head.json").read_text())
        return cls(encoder, meta["labels"], **head, provenance=meta["provenance"])
