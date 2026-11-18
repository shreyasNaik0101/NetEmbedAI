"""Raw schema 1: milliseconds, client/server signs, UDP payload bytes."""

from typing import Literal
import numpy as np
from pydantic import BaseModel, ConfigDict, Field, model_validator

SCHEMA = "1"
BUDGETS = (5, 10, 20, 30)
FEATURES = {
    "schema": SCHEMA,
    "channels": ["iat_ms", "direction", "payload_bytes"],
    "direction": "+1 client-to-server; -1 server-to-client",
    "readout": "last-valid-v2",
    "transform": "log1p-iat-size-standardize-v1",
    "max_packets": 30,
}


class Packet(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)
    iat_ms: float = Field(ge=0, le=3600000)
    direction: Literal[-1, 1]
    payload_bytes: int = Field(strict=True, ge=1, le=65527)


class Flow(BaseModel):
    model_config = ConfigDict(extra="forbid")
    schema_version: Literal["1"] = "1"
    packets: list[Packet] = Field(min_length=1, max_length=30)

    @model_validator(mode="after")
    def first_zero(self):
        if self.packets[0].iat_ms != 0:
            raise ValueError("first observed iat_ms must be zero")
        return self

    def array(self):
        return np.asarray([[p.iat_ms, p.direction, p.payload_bytes] for p in self.packets], dtype=np.float32)

    @classmethod
    def from_array(cls, x):
        x = validate_array(x)
        return cls(packets=[Packet(iat_ms=float(t), direction=int(d), payload_bytes=int(s)) for t, d, s in x])


def validate_array(x):
    x = np.asarray(x, dtype=np.float32)
    if x.ndim != 2 or x.shape[1] != 3 or not 1 <= len(x) <= 30:
        raise ValueError("expected 1..30 packets with three channels")
    if (
        not np.isfinite(x).all()
        or ((x[:, 0] < 0) | (x[:, 0] > 3600000)).any()
        or x[0, 0] != 0
        or not np.isin(x[:, 1], [-1, 1]).all()
        or (x[:, 2] < 1).any()
        or (x[:, 2] > 65527).any()
        or (x[:, 2] != np.floor(x[:, 2])).any()
    ):
        raise ValueError("invalid raw packet feature values")
    return x


def log_features(x):
    x = x.copy()
    x[:, (0, 2)] = np.log1p(x[:, (0, 2)])
    return x


class Normalizer:
    def __init__(self, mean, std):
        self.mean, self.std = np.asarray(mean, dtype=np.float32), np.asarray(std, dtype=np.float32)
        if (
            self.mean.shape != (3,)
            or self.std.shape != (3,)
            or not np.isfinite(self.mean).all()
            or not np.isfinite(self.std).all()
            or (self.std <= 0).any()
        ):
            raise ValueError("invalid saved normalizer")

    @classmethod
    def fit(cls, training_flows):
        flat = np.concatenate([log_features(validate_array(x)) for x in training_flows])
        return cls(flat.mean(0), np.maximum(flat.std(0), 1e-6))

    def batch(self, flows):
        out = np.zeros((len(flows), 30, 3), np.float32)
        lengths = []
        for i, raw in enumerate(flows):
            x = validate_array(raw)
            out[i, : len(x)] = (log_features(x) - self.mean) / self.std
            lengths.append(len(x))
        return out, np.asarray(lengths, np.int64)

    def metadata(self):
        return {"mean": self.mean.tolist(), "std": self.std.tolist()}


def summary(x):
    x = validate_array(x)
    features = [len(x)]
    for direction in (None, 1, -1):
        part = x if direction is None else x[x[:, 1] == direction]
        features.append(len(part))
        for col in (0, 2):
            v = part[:, col]
            features.extend(
                [float(f(v)) if len(v) else 0.0 for f in (np.sum, np.mean, np.std, np.min, np.max)]
            )
    return features


def forest_features(raw, normalizer, feature_map="summary-v1"):
    """Versioned maps using only the observed prefix; no extra input channels."""
    if feature_map not in (
        "summary-v1",
        "summary-ordered-v1",
        "summary-relative-size-v1",
        "summary-nearest-ms-v1",
    ):
        raise ValueError("unknown forest feature map")
    raw = validate_array(raw)
    if feature_map == "summary-nearest-ms-v1":
        raw = raw.copy()
        raw[:, 0] = np.rint(raw[:, 0])
    aggregate = np.asarray(summary(raw), dtype=np.float64)
    if feature_map == "summary-relative-size-v1":
        # Scale only payload statistics by the maximum in this observed prefix.
        # Packet inputs remain integer UDP bytes; counts/gaps keep their units.
        # No later packet, data-fitted statistic or endpoint identity is used.
        for start in (7, 18, 29):
            aggregate[start : start + 5] /= float(raw[:, 2].max())
        return aggregate
    if feature_map in ("summary-v1", "summary-nearest-ms-v1"):
        return aggregate
    padded, _ = normalizer.batch([raw])
    mask = (np.arange(30) < len(raw)).astype(np.float64)
    return np.concatenate([aggregate, padded.reshape(-1), mask])
