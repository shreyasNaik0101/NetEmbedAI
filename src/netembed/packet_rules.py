"""Transparent prefix profiles and conservative interval rules; experimental only."""

import json
from pathlib import Path

import numpy as np

from .bundle import sha256, write_json
from .contract import FEATURES, validate_array

VERSION = "prefix-shape-10-v1"
RULE_VERSION = "unique-training-box-v1"
NAMES = [
    "packet_count_div30",
    "outbound_packet_fraction",
    "outbound_byte_fraction",
    "payload_fraction_ge1000",
    "direction_switch_fraction",
    "mean_payload_div1500",
    "std_payload_div1500",
    "log1p_duration_ms",
    "log1p_median_gap_ms",
    "gap_fraction_gt100ms",
]
FLOORS = np.array([1 / 30, 0.05, 0.05, 0.05, 0.05, 0.05, 0.05, 0.25, 0.25, 0.05])
BUCKETS = (5, 10, 20, 30)


def describe(raw):
    x = validate_array(raw).astype(np.float64)
    n = len(x)
    gaps = x[1:, 0]
    up = x[:, 1] == 1
    sizes = x[:, 2]
    return np.array(
        [
            n / 30,
            up.mean(),
            sizes[up].sum() / sizes.sum(),
            (sizes >= 1000).mean(),
            (x[1:, 1] != x[:-1, 1]).mean() if n > 1 else 0,
            sizes.mean() / 1500,
            sizes.std() / 1500,
            np.log1p(x[:, 0].sum()),
            np.log1p(np.median(gaps)) if n > 1 else 0,
            (gaps > 100).mean() if n > 1 else 0,
        ]
    )


def length_bucket(n):
    if not 1 <= n <= 30:
        raise ValueError("actual prefix length must be 1..30")
    return next(b for b in BUCKETS if n <= b)


def weighted_quantile(values, weights, quantile):
    values, weights = np.asarray(values), np.asarray(weights)
    if (
        values.ndim != 1
        or weights.shape != values.shape
        or not len(values)
        or not np.isfinite(values).all()
        or not np.isfinite(weights).all()
        or (weights <= 0).any()
        or not 0 <= quantile <= 1
    ):
        raise ValueError("invalid weighted training quantile")
    order = np.argsort(values, kind="stable")
    cumulative = np.cumsum(weights[order]) / weights.sum()
    index = min(int(np.searchsorted(cumulative, quantile, side="left")), len(values) - 1)
    return float(values[order[index]])


class PacketRules:
    def __init__(self, document):
        if (
            document["version"] != VERSION
            or document["rule_version"] != RULE_VERSION
            or document["features"] != FEATURES
            or document["feature_names"] != NAMES
        ):
            raise ValueError("incompatible packet-rule feature contract")
        self.doc = document
        self.labels = document["labels"]
        if len(self.labels) < 2 or len(set(self.labels)) != len(self.labels):
            raise ValueError("invalid packet-rule class map")
        if set(document["profiles"]) != {str(b) for b in BUCKETS}:
            raise ValueError("missing length bucket")
        self.profiles = {}
        for key, profile in document["profiles"].items():
            arrays = {
                name: np.asarray(profile[name], dtype=np.float64) for name in ("lower", "median", "upper")
            }
            scale = np.asarray(profile["scale"], dtype=np.float64)
            active = np.asarray(profile["active"], dtype=bool)
            if (
                any(v.shape != (len(self.labels), 10) or not np.isfinite(v).all() for v in arrays.values())
                or scale.shape != (10,)
                or not np.isfinite(scale).all()
                or (scale <= 0).any()
                or active.shape != (len(self.labels),)
                or not active.any()
                or (arrays["lower"] > arrays["median"]).any()
                or (arrays["median"] > arrays["upper"]).any()
            ):
                raise ValueError("invalid saved packet-rule parameters")
            self.profiles[key] = {**arrays, "scale": scale, "active": active}

    @classmethod
    def fit(cls, flows, labels, weights, ids, class_names, minimum_flows=3, provenance=None):
        if not len(flows) == len(labels) == len(weights) == len(ids) or minimum_flows < 1:
            raise ValueError("training rows/weights/identifiers differ")
        labels, weights = np.asarray(labels, dtype=np.float64), np.asarray(weights, dtype=np.float64)
        if (
            not np.isfinite(weights).all()
            or (weights <= 0).any()
            or not np.isfinite(labels).all()
            or (labels != np.floor(labels)).any()
            or (labels < 0).any()
            or (labels >= len(class_names)).any()
        ):
            raise ValueError("invalid training classes/weights")
        labels = labels.astype(np.int64)
        identities = {}
        for ident, label in zip(ids, labels):
            if ident in identities and identities[ident] != label:
                raise ValueError("one training flow has conflicting labels")
            identities[ident] = label
        descriptors = np.asarray([describe(x) for x in flows])
        buckets = np.array([length_bucket(len(x)) for x in flows])
        profiles = {}
        for bucket in BUCKETS:
            selected = buckets == bucket
            if not selected.any():
                raise ValueError("training lacks an actual-length bucket")
            x, y, w = descriptors[selected], labels[selected], weights[selected]
            names = np.asarray(ids)[selected]
            scale = np.array(
                [
                    max(weighted_quantile(x[:, j], w, 0.75) - weighted_quantile(x[:, j], w, 0.25), FLOORS[j])
                    for j in range(10)
                ]
            )
            quantiles = np.zeros((3, len(class_names), 10))
            active, support = [], []
            for label in range(len(class_names)):
                group = y == label
                count = len(set(names[group].tolist()))
                support.append(count)
                active.append(count >= minimum_flows)
                if group.any():
                    for i, q in enumerate((0.05, 0.5, 0.95)):
                        quantiles[i, label] = [weighted_quantile(x[group, j], w[group], q) for j in range(10)]
            profiles[str(bucket)] = {
                "lower": quantiles[0].tolist(),
                "median": quantiles[1].tolist(),
                "upper": quantiles[2].tolist(),
                "scale": scale.tolist(),
                "active": active,
                "distinct_training_flow_support": support,
            }
        return cls(
            {
                "version": VERSION,
                "rule_version": RULE_VERSION,
                "features": FEATURES,
                "feature_names": NAMES,
                "labels": list(class_names),
                "profiles": profiles,
                "provenance": provenance or {},
                "minimum_training_flows": minimum_flows,
                "policy": "experimental unique training-envelope match; uncalibrated; no live deployment",
            }
        )

    def predict(self, raw):
        x = validate_array(raw)
        bucket = length_bucket(len(x))
        profile = self.profiles[str(bucket)]
        features = describe(x)
        distances = np.mean(np.abs(profile["median"] - features) / profile["scale"], axis=1)
        distances[~profile["active"]] = np.inf
        order = np.argsort(distances, kind="stable")
        inside = profile["active"] & np.all(
            (features >= profile["lower"] - 1e-12) & (features <= profile["upper"] + 1e-12), axis=1
        )
        matches = np.flatnonzero(inside)
        answer = self.labels[int(matches[0])] if len(x) >= 5 and len(matches) == 1 else None
        return {
            "observed_packets": len(x),
            "length_bucket": bucket,
            "nearest_label": self.labels[int(order[0])],
            "rule_label": answer,
            "matching_profiles": [self.labels[int(i)] for i in matches],
            "status": "insufficient_evidence"
            if len(x) < 5
            else "heuristic_match_uncalibrated"
            if answer
            else "no_unique_profile_match",
            "alternatives": [
                {"label": self.labels[int(i)], "distance": float(distances[i])}
                for i in order
                if profile["active"][i]
            ][:3],
        }

    def save(self, destination):
        destination = Path(destination)
        destination.mkdir(parents=True, exist_ok=False)
        write_json(destination / "rules.json", self.doc)
        write_json(destination / "checksums.json", {"rules.json": sha256(destination / "rules.json")})

    @classmethod
    def load(cls, source, allow_fixture=False):
        source = Path(source)
        checksums = json.loads((source / "checksums.json").read_text())
        if set(checksums) != {"rules.json"} or sha256(source / "rules.json") != checksums["rules.json"]:
            raise ValueError("packet-rule checksum mismatch")
        document = json.loads((source / "rules.json").read_text())
        if document["provenance"].get("fixture") and not allow_fixture:
            raise ValueError("software fixture is not a benchmark artifact")
        return cls(document)
