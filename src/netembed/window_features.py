"""Versioned bounded-window features; the observation point is an explicit contract."""

import json
from decimal import Decimal
from pathlib import Path

import numpy as np

from .bundle import sha256, write_json
from .observation_windows import HORIZONS_MS, ObservationWindows

VERSION = "bounded-window-features-v1"
NAMES = [
    "log_client_packets",
    "log_server_packets",
    "log_client_bytes",
    "log_server_bytes",
    "client_packet_fraction",
    "client_byte_fraction",
    "mean_size_div1500",
    "std_size_div1500",
    "min_size_div1500",
    "max_size_div1500",
    "large_size_fraction",
    "direction_switch_fraction",
]
NAMES += [f"packet_mass_bin{i}_{d}" for i in range(30) for d in ("client", "server")]


def browser_windows(records):
    """Recorded UDP transfers, not decrypted QUIC events or live wire packets."""
    if not records:
        raise ValueError("no socket datagrams")
    anchor = records[0][0]
    first_ns = int(Decimal(str(anchor)) * 1000000)
    accumulator = ObservationWindows(first_ns, 0)
    for timestamp, _, direction, size in records:
        if direction not in (1, -1) or not 1 <= size <= 65527:
            raise ValueError("invalid socket datagram")
        ns = int(Decimal(str(timestamp)) * 1000000)
        accumulator.add(ns, direction, size)
    if accumulator.reordered:
        raise ValueError("socket transfers not ordered")
    # The caller separately verifies that the stopped log covers all three seconds.
    return {w["horizon_ms"]: w for w in accumulator.snapshot(4)["windows"]}


def features(window):
    horizon = window["horizon_ms"]
    if horizon not in HORIZONS_MS or window["state"] != "elapsed" or window["observed_ms"] != horizon:
        raise ValueError("requires an elapsed supported observation window")
    cp, sp = window["client_packets"], window["server_packets"]
    cb, sb = window["client_bytes"], window["server_bytes"]
    n, total = cp + sp, cb + sb
    if n < 1 or total < n:
        raise ValueError("missing window observations")
    bins = np.asarray(window["packets_by_100ms_client_server"], dtype=np.float64)
    if (
        bins.shape != (horizon // 100, 2)
        or not np.isfinite(bins).all()
        or (bins < 0).any()
        or (bins != np.floor(bins)).any()
        or not np.array_equal(bins.sum(axis=0), [cp, sp])
    ):
        raise ValueError("window histogram disagrees with counts")
    padded = np.zeros((30, 2))
    padded[: len(bins)] = bins / n
    scalar = [
        *np.log1p([cp, sp, cb, sb]),
        cp / n,
        cb / total,
        window["mean_payload_bytes"] / 1500,
        window["std_payload_bytes"] / 1500,
        window["min_payload_bytes"] / 1500,
        window["max_payload_bytes"] / 1500,
        window["large_payload_fraction"],
        window["direction_switches"] / max(1, n - 1),
    ]
    result = np.concatenate([scalar, padded.reshape(-1)])
    if result.shape != (len(NAMES),) or not np.isfinite(result).all():
        raise ValueError("invalid window feature values")
    return result


class WindowForest:
    def __init__(self, document):
        if (
            document["version"] != VERSION
            or document["feature_names"] != NAMES
            or document["observer"] != "browser_udp_socket"
            or document["policy"]["fitted"]
        ):
            raise ValueError("unsupported experimental window artifact")
        self.document = document
        self.labels = document["labels"]
        self.trees = document["trees"]
        if len(set(self.labels)) != len(self.labels) or len(self.labels) < 2 or not self.trees:
            raise ValueError("invalid window class map/trees")
        for tree in self.trees:
            n = len(tree["left"])
            if not all(len(tree[k]) == n for k in ("right", "feature", "threshold", "value")):
                raise ValueError("invalid window tree layout")
            for left, right, feature, threshold, value in zip(
                *(tree[k] for k in ("left", "right", "feature", "threshold", "value"))
            ):
                if (
                    not math_finite(threshold)
                    or len(value) != len(self.labels)
                    or not np.isfinite(value).all()
                    or min(value) < 0
                    or sum(value) <= 0
                    or (
                        left != -1
                        and (not 0 <= left < n or not 0 <= right < n or not 0 <= feature < len(NAMES))
                    )
                ):
                    raise ValueError("invalid window tree node")

    def predict(self, window, observer):
        if observer != self.document["observer"]:
            raise ValueError("observer mismatch; browser-to-wire transfer has not been validated")
        if window["horizon_ms"] != self.document["horizon_ms"]:
            raise ValueError("window/model observation budget differs")
        x = features(window).astype(np.float32)
        probabilities = np.zeros(len(self.labels))
        for tree in self.trees:
            node = 0
            for _ in range(len(tree["left"])):
                if tree["left"][node] == -1:
                    break
                node = (
                    tree["left"][node]
                    if x[tree["feature"][node]] <= tree["threshold"][node]
                    else tree["right"][node]
                )
            else:
                raise ValueError("cyclic window tree")
            value = np.asarray(tree["value"][node])
            probabilities += value / value.sum()
        probabilities /= len(self.trees)
        order = np.argsort(-probabilities, kind="stable")
        return {
            "label": None,
            "raw_top1": self.labels[int(order[0])],
            "status": "experimental_uncalibrated",
            "observer": observer,
            "horizon_ms": window["horizon_ms"],
            "alternatives": [{"label": self.labels[int(i)], "score": float(probabilities[i])} for i in order],
        }

    @classmethod
    def from_fitted(cls, model, labels, horizon, provenance):
        if list(model.classes_) != list(range(len(labels))) or model.n_features_in_ != len(NAMES):
            raise ValueError("window fitting classes/features differ")
        return cls(
            {
                "version": VERSION,
                "feature_names": NAMES,
                "labels": list(labels),
                "horizon_ms": horizon,
                "observer": "browser_udp_socket",
                "policy": {"fitted": False},
                "provenance": provenance,
                "trees": [
                    {
                        "left": t.tree_.children_left.tolist(),
                        "right": t.tree_.children_right.tolist(),
                        "feature": t.tree_.feature.tolist(),
                        "threshold": t.tree_.threshold.tolist(),
                        "value": t.tree_.value[:, 0, :].tolist(),
                    }
                    for t in model.estimators_
                ],
            }
        )

    def save(self, path):
        path = Path(path)
        path.mkdir(parents=True, exist_ok=False)
        write_json(path / "window-model.json", self.document)
        write_json(path / "checksums.json", {"window-model.json": sha256(path / "window-model.json")})

    @classmethod
    def load(cls, path, allow_fixture=False):
        path = Path(path)
        check = json.loads((path / "checksums.json").read_text())
        if set(check) != {"window-model.json"} or check["window-model.json"] != sha256(
            path / "window-model.json"
        ):
            raise ValueError("window artifact checksum mismatch")
        document = json.loads((path / "window-model.json").read_text())
        if document["provenance"].get("fixture") and not allow_fixture:
            raise ValueError("software fixture is not a real artifact")
        return cls(document)


def math_finite(value):
    return isinstance(value, (int, float)) and np.isfinite(value)
