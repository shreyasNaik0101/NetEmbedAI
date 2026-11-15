"""Experimental ordered-prefix retrieval. Distances are not probabilities."""

import json
from pathlib import Path

import numpy as np

from .bundle import sha256, write_json
from .contract import BUDGETS, FEATURES, validate_array

VERSION = "ordered-packet-neighbors-v1"
VARIANTS = ("ordered", "size_direction", "timing_direction", "after_eight")


def bucket(length):
    return next(b for b in BUDGETS if length <= b)


def encode(raw, length, variant="ordered"):
    if variant not in VARIANTS or length not in BUDGETS:
        raise ValueError("unknown ordered representation or budget")
    raw = validate_array(raw)[:length]
    out = np.zeros((length, 3), dtype=np.float32)
    out[: len(raw)] = raw
    out[:, 0] = np.minimum(out[:, 0], 1000) / 10
    if variant == "size_direction":
        out[:, 0] = 0
    elif variant == "timing_direction":
        out[:, 2] = 0
    elif variant == "after_eight":
        out[:8] = 0
    return out.reshape(-1)


class PacketNeighbors:
    """Fixed 1-NN, exact L1 search, stable reference-order ties, bounded memory."""

    def __init__(self, flows, targets, ids, labels, provenance=None):
        if not 1 <= len(flows) <= 50000 or len(flows) != len(targets) or len(ids) != len(flows):
            raise ValueError("invalid bounded reference inventory")
        if len(set(ids)) != len(ids) or len(set(labels)) != len(labels) or not labels:
            raise ValueError("duplicate reference identity or class")
        self.flows = [validate_array(x).copy() for x in flows]
        target_values = np.asarray(targets)
        if target_values.shape != (len(flows),) or target_values.dtype.kind not in "iu":
            raise ValueError("invalid integer reference classes")
        self.y = target_values.astype(np.int64)
        if np.any(self.y < 0) or np.any(self.y >= len(labels)):
            raise ValueError("reference class outside class map")
        self.ids, self.labels = list(ids), list(labels)
        self.provenance = provenance or {}
        self.cache = {}

    def matrix(self, length, variant):
        key = length, variant
        if key not in self.cache:
            self.cache[key] = np.stack([encode(x, length, variant) for x in self.flows])
        return self.cache[key]

    def predict(self, raw, variant="ordered"):
        raw = validate_array(raw)
        length = bucket(len(raw))
        vector = encode(raw, length, variant)
        if variant == "after_eight" and len(raw) <= 8:
            return {
                "observed_packets": len(raw),
                "reference_budget": length,
                "label": None,
                "status": "insufficient_evidence",
                "alternatives": [],
            }
        distance = np.abs(self.matrix(length, variant) - vector).sum(axis=1, dtype=np.float64)
        # References without any remaining observation cannot win after masking.
        if variant == "after_eight":
            distance[np.asarray([len(x) <= 8 for x in self.flows])] = np.inf
        finite = np.flatnonzero(np.isfinite(distance))
        if not len(finite):
            raise ValueError("no reference with usable evidence")
        nearest = int(finite[np.argmin(distance[finite])])
        alternatives = []
        for label in range(len(self.labels)):
            group = np.flatnonzero((self.y == label) & np.isfinite(distance))
            if len(group):
                index = int(group[np.argmin(distance[group])])
                alternatives.append((float(distance[index]), index, self.labels[label]))
        alternatives.sort()
        return {
            "observed_packets": len(raw),
            "reference_budget": length,
            "label": self.labels[int(self.y[nearest])],
            "status": "raw_ranking_uncalibrated" if len(raw) >= 5 else "insufficient_evidence",
            "reference_id": self.ids[nearest],
            "distance": float(distance[nearest]),
            "alternatives": [{"label": label, "distance": value} for value, _, label in alternatives[:3]],
        }

    def save(self, destination):
        destination = Path(destination)
        destination.mkdir(parents=True, exist_ok=False)
        padded = np.zeros((len(self.flows), 30, 3), dtype=np.float32)
        for i, raw in enumerate(self.flows):
            padded[i, : len(raw)] = raw
        np.savez_compressed(
            destination / "references.npz",
            packets=padded,
            lengths=np.asarray([len(x) for x in self.flows]),
            targets=self.y,
        )
        write_json(
            destination / "metadata.json",
            {
                "version": VERSION,
                "features": FEATURES,
                "labels": self.labels,
                "ids": self.ids,
                "provenance": self.provenance,
                "transform": "IPT clipped at1000ms then divided10; other channels unscaled; zero padding",
                "bucket": "smallest checkpoint >= actual length, independent of requested cap",
                "policy": {"fitted": False, "note": "Raw 1-NN ranking only; no live deployment"},
            },
        )
        write_json(
            destination / "checksums.json",
            {p: sha256(destination / p) for p in ("metadata.json", "references.npz")},
        )

    @classmethod
    def load(cls, source, allow_fixture=False):
        source = Path(source)
        checksums = json.loads((source / "checksums.json").read_text())
        if set(checksums) != {"metadata.json", "references.npz"} or any(
            sha256(source / name) != value for name, value in checksums.items()
        ):
            raise ValueError("neighbor artifact checksum mismatch")
        meta = json.loads((source / "metadata.json").read_text())
        if meta["version"] != VERSION or meta["features"] != FEATURES or meta["policy"]["fitted"]:
            raise ValueError("unsupported neighbor contract")
        if meta["provenance"].get("fixture") and not allow_fixture:
            raise ValueError("software fixture is not a benchmark artifact")
        with np.load(source / "references.npz", allow_pickle=False) as arrays:
            packets, lengths, targets = arrays["packets"], arrays["lengths"], arrays["targets"]
        if (
            packets.shape != (len(lengths), 30, 3)
            or lengths.dtype.kind not in "iu"
            or targets.dtype.kind not in "iu"
            or targets.shape != lengths.shape
            or np.any(lengths < 1)
            or np.any(lengths > 30)
        ):
            raise ValueError("invalid neighbor array layout")
        if any(np.any(raw[int(n) :] != 0) for raw, n in zip(packets, lengths)):
            raise ValueError("nonzero reference padding")
        return cls(
            [raw[: int(n)] for raw, n in zip(packets, lengths)],
            targets,
            meta["ids"],
            meta["labels"],
            meta["provenance"],
        )
