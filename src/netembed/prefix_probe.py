"""Four fixed checkpoint heads over one frozen pooling encoder and scaler."""

import json
from pathlib import Path

import numpy as np

from .bundle import sha256, write_json
from .contract import BUDGETS, validate_array
from .linear_probe import LinearProbe, WHEEL

VERSION = "cesnet-prefix-linear-probe-v1"
ROUTING = "explicit checkpoint >= actual length; default smallest checkpoint >= actual length"


def checkpoint(length, requested=None):
    if not 1 <= length <= 30:
        raise ValueError("invalid packet count")
    if requested is not None:
        if requested not in BUDGETS or length > requested:
            raise ValueError("checkpoint would admit future packets or is unsupported")
        return requested
    return next(b for b in BUDGETS if length <= b)


class PrefixProbe:
    def __init__(self, base, heads, provenance=None):
        if set(heads) != set(BUDGETS):
            raise ValueError("exactly four checkpoint heads are required")
        self.base, self.labels = base, base.labels
        self.heads = {
            b: LinearProbe(base.encoder, base.labels, base.mean, base.scale, **head)
            for b, head in heads.items()
        }
        self.provenance = provenance or {}

    def probabilities(self, flows, budget=None):
        if not flows:
            raise ValueError("empty prefix batch")
        raw = [validate_array(x) for x in flows]
        chosen = np.array([checkpoint(len(x), budget) for x in raw])
        features = self.base.encoder.encode(raw)
        output = np.empty((len(raw), len(self.labels)), dtype=np.float64)
        for b in BUDGETS:
            indices = np.flatnonzero(chosen == b)
            if len(indices):
                output[indices] = self.heads[b].from_features(features[indices])
        return output

    def predict(self, raw, budget=None):
        raw = validate_array(raw)
        chosen = checkpoint(len(raw), budget)
        # LinearProbe retains the same always-withhold policy for each head.
        result = self.heads[chosen].predict(raw)
        return {**result, "head_budget": chosen}

    def save(self, destination, wheel):
        destination = Path(destination)
        destination.mkdir(parents=True, exist_ok=False)
        # One complete shared reference carries the encoder and training-only
        # scaler. Its old classifier is retained for provenance, never selected.
        self.base.save(destination / "base", wheel)
        write_json(
            destination / "heads.json",
            {
                str(b): {"coefficients": head.coef.tolist(), "intercept": head.intercept.tolist()}
                for b, head in self.heads.items()
            },
        )
        write_json(
            destination / "metadata.json",
            {
                "version": VERSION,
                "labels": self.labels,
                "budgets": list(BUDGETS),
                "routing": ROUTING,
                "policy": {"fitted": False, "decision": "always withhold"},
                "base_metadata_sha256": sha256(destination / "base/metadata.json"),
                "provenance": self.provenance,
            },
        )
        names = {"metadata.json", "heads.json"} | {
            "base/" + name for name in ("metadata.json", "head.json", "checksums.json", "encoder.pth", WHEEL)
        }
        write_json(destination / "checksums.json", {n: sha256(destination / n) for n in sorted(names)})

    @classmethod
    def load(cls, source):
        source = Path(source)
        checks = json.loads((source / "checksums.json").read_text())
        expected = {"metadata.json", "heads.json"} | {
            "base/" + name for name in ("metadata.json", "head.json", "checksums.json", "encoder.pth", WHEEL)
        }
        if set(checks) != expected or any(sha256(source / k) != v for k, v in checks.items()):
            raise ValueError("prefix probe checksum mismatch")
        meta = json.loads((source / "metadata.json").read_text())
        if (
            meta["version"] != VERSION
            or meta["budgets"] != list(BUDGETS)
            or meta["routing"] != ROUTING
            or meta["policy"] != {"fitted": False, "decision": "always withhold"}
            or meta["provenance"].get("fixture")
            or meta["base_metadata_sha256"] != checks["base/metadata.json"]
        ):
            raise ValueError("unsupported prefix probe artifact")
        base = LinearProbe.load(source / "base")
        if base.labels != meta["labels"]:
            raise ValueError("prefix head label order differs")
        heads = json.loads((source / "heads.json").read_text())
        if set(heads) != {str(b) for b in BUDGETS}:
            raise ValueError("exactly four checkpoint heads are required")
        return cls(base, {int(b): head for b, head in heads.items()}, meta["provenance"])
