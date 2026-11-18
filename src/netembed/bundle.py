"""Checksummed portable inference, never imports data preparation or fits statistics."""

import hashlib
import json
import platform
import time
from pathlib import Path
import numpy as np
import torch
import sklearn
from .contract import FEATURES, Normalizer, forest_features, validate_array
from .models import Classifier


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def write_json(path, value):
    Path(path).write_text(json.dumps(value, indent=2, allow_nan=False), encoding="utf-8")


def forest_prefix(specification):
    if set(specification) - {"feature_map", "fixed_prefix_packets"}:
        raise ValueError("unknown forest architecture field")
    prefix = specification.get("fixed_prefix_packets")
    if "fixed_prefix_packets" in specification and (type(prefix) is not int or prefix != 10):
        raise ValueError("fixed forest prefix must be exactly 10 packets")
    return prefix


def export_bundle(path, model, normalizer, labels, provenance, architecture=None, policy=None):
    path = Path(path)
    kind = "tcn" if isinstance(model, Classifier) else "forest"
    if kind == "forest":
        specification = architecture or {}
        prefix = forest_prefix(specification)
        if prefix and policy and policy["min_packets"] != prefix:
            raise ValueError("fixed-prefix policy must require exactly 10 packets")
        dimension = len(
            forest_features([[0, 1, 1]], normalizer, specification.get("feature_map", "summary-v1"))
        )
        if model.n_features_in_ != dimension:
            raise ValueError("forest training features differ from exported feature map")
    path.mkdir(parents=True, exist_ok=False)
    if kind == "tcn":
        torch.save(model.state_dict(), path / "weights.pt")
        filename = "weights.pt"
    else:
        # Plain numeric JSON forest; no request-supplied pickle execution.
        trees = [
            {
                "left": t.tree_.children_left.tolist(),
                "right": t.tree_.children_right.tolist(),
                "feature": t.tree_.feature.tolist(),
                "threshold": t.tree_.threshold.tolist(),
                "value": t.tree_.value[:, 0, :].tolist(),
            }
            for t in model.estimators_
        ]
        filename = "forest.json"
        write_json(path / filename, trees)
    meta = {
        "artifact_version": 2,
        "kind": kind,
        "features": FEATURES,
        "labels": labels,
        "normalizer": normalizer.metadata(),
        "architecture": architecture or {},
        "policy": policy
        or {
            "version": "unfitted",
            "threshold": 1.0,
            "min_packets": prefix if kind == "forest" and prefix else 5,
            "fitted": False,
            "temperature": 1.0,
        },
        "provenance": provenance,
        "versions": {
            "python": platform.python_version(),
            "torch": torch.__version__,
            "numpy": np.__version__,
            "scikit_learn": sklearn.__version__,
        },
        "files": {filename: sha256(path / filename)},
    }
    write_json(path / "metadata.json", meta)
    write_json(path / "checksums.json", {"metadata.json": sha256(path / "metadata.json"), **meta["files"]})
    return path


class Predictor:
    def __init__(self, path, allow_fixture=False):
        path = Path(path)
        checksums = json.loads((path / "checksums.json").read_text())
        if set(checksums) not in ({"metadata.json", "weights.pt"}, {"metadata.json", "forest.json"}):
            raise ValueError("invalid bundle file inventory")
        for name, digest in checksums.items():
            if sha256(path / name) != digest:
                raise ValueError("bundle checksum mismatch: " + name)
        self.meta = json.loads((path / "metadata.json").read_text())
        m = self.meta
        if m["artifact_version"] != 2 or m["features"] != FEATURES:
            raise ValueError("incompatible feature/readout version; retrain old weights")
        if m["kind"] not in ("tcn", "forest"):
            raise ValueError("unknown predictor type")
        if m["provenance"].get("fixture", False) and not allow_fixture:
            raise ValueError("software-test artifact is not a real demo model")
        self.labels = m["labels"]
        if len(self.labels) < 2 or len(set(self.labels)) != len(self.labels):
            raise ValueError("invalid class map")
        self.normalizer = Normalizer(**m["normalizer"])
        policy = m["policy"]
        accepted_labels = policy.get("accepted_labels", self.labels)
        if (
            not isinstance(accepted_labels, list)
            or not accepted_labels
            or any(not isinstance(label, str) or label not in self.labels for label in accepted_labels)
            or len(set(accepted_labels)) != len(accepted_labels)
        ):
            raise ValueError("invalid accepted-label policy scope")
        if (
            not 0 <= policy["threshold"] <= 1
            or not 1 <= policy["min_packets"] <= 30
            or not np.isfinite(policy["temperature"])
            or policy["temperature"] <= 0
        ):
            raise ValueError("invalid decision policy")
        self.identity = checksums["metadata.json"]
        self.fixed_prefix_packets = None
        if m["kind"] == "tcn":
            self.model = Classifier(len(self.labels), **m["architecture"])
            self.model.load_state_dict(torch.load(path / "weights.pt", map_location="cpu", weights_only=True))
            self.model.eval()
        else:
            from .json_array import iter_json_array

            self.fixed_prefix_packets = forest_prefix(m["architecture"])
            if self.fixed_prefix_packets and policy["min_packets"] != self.fixed_prefix_packets:
                raise ValueError("fixed-prefix policy must require exactly 10 packets")
            self.forest_feature_map = m["architecture"].get("feature_map", "summary-v1")
            dimension = len(forest_features([[0, 1, 1]], self.normalizer, self.forest_feature_map))
            self.trees = []
            for t in iter_json_array(path / "forest.json"):
                if len(t["value"][0]) != len(self.labels):
                    raise ValueError("forest class map mismatch")
                if any(feature >= dimension or feature < -2 for feature in t["feature"]):
                    raise ValueError("forest split outside declared feature map")
                self.trees.append(
                    {
                        "left": np.asarray(t["left"], dtype=np.int32),
                        "right": np.asarray(t["right"], dtype=np.int32),
                        "feature": np.asarray(t["feature"], dtype=np.int32),
                        "threshold": np.asarray(t["threshold"], dtype=np.float64),
                        "value": np.asarray(t["value"], dtype=np.float64),
                    }
                )
            if not self.trees:
                raise ValueError("forest class map mismatch")

    def probabilities(self, flows):
        flows = [validate_array(x) for x in flows]
        prefix = getattr(self, "fixed_prefix_packets", None)
        if prefix:
            if any(len(x) < prefix for x in flows):
                raise ValueError("fixed-prefix scoring requires at least 10 observed packets")
            flows = [x[:prefix] for x in flows]
        if self.meta["kind"] == "tcn":
            x, lengths = self.normalizer.batch(flows)
            with torch.inference_mode():
                logits, _ = self.model(torch.from_numpy(x), torch.from_numpy(lengths))
                return torch.softmax(logits / self.meta["policy"]["temperature"], 1).numpy()
        features = np.asarray([forest_features(x, self.normalizer, self.forest_feature_map) for x in flows])
        result = np.zeros((len(flows), len(self.labels)))
        if len(flows) == 1:
            # Live inference routes one flow. Avoid allocating numpy index/mask
            # arrays at every branch while preserving tree and summation order.
            for tree in self.trees:
                node = 0
                for _ in range(len(tree["left"])):
                    if tree["left"][node] == -1:
                        break
                    node = int(
                        tree["left"][node]
                        if features[0, tree["feature"][node]] <= tree["threshold"][node]
                        else tree["right"][node]
                    )
                else:
                    raise ValueError("cyclic or invalid forest tree")
                value = tree["value"][node]
                result[0] += value / value.sum()
            return result / len(self.trees)
        for tree in self.trees:
            nodes = np.zeros(len(flows), dtype=np.int32)
            for _ in range(len(tree["left"])):
                moving = tree["left"][nodes] != -1
                if not moving.any():
                    break
                rows = np.flatnonzero(moving)
                current = nodes[rows]
                nodes[rows] = np.where(
                    features[rows, tree["feature"][current]] <= tree["threshold"][current],
                    tree["left"][current],
                    tree["right"][current],
                )
            else:
                raise ValueError("cyclic or invalid forest tree")
            value = tree["value"][nodes]
            result += value / value.sum(axis=1, keepdims=True)
        return result / len(self.trees)

    def predict(self, raw):
        start = time.perf_counter()
        raw = validate_array(raw)
        policy = self.meta["policy"]
        short = self.fixed_prefix_packets is not None and len(raw) < self.fixed_prefix_packets
        scores = np.empty(0) if short else self.probabilities([raw])[0]
        indices = (
            np.argsort(-scores, kind="stable")[:3]
            if policy.get("tie_break") == "label_order"
            else np.argsort(-scores)[:3]
        )
        status = (
            "insufficient_evidence"
            if len(raw) < policy["min_packets"]
            else "insufficient_confidence"
            if not policy["fitted"]
            or scores[indices[0]] < policy["threshold"]
            or self.labels[indices[0]] not in policy.get("accepted_labels", self.labels)
            else "classified"
        )
        return {
            "artifact_id": self.identity,
            "artifact_version": 2,
            "status": status,
            "label": self.labels[indices[0]] if status == "classified" else None,
            "alternatives": [{"label": self.labels[i], "score": float(scores[i])} for i in indices],
            "observed_packets": len(raw),
            "policy_version": policy["version"],
            "policy_fitted": policy["fitted"],
            "policy_scope": policy.get("validation_scope", "unspecified"),
            "decision_reason": (
                "too_few_packets"
                if status == "insufficient_evidence"
                else "policy_not_fitted"
                if not policy["fitted"]
                else "outside_policy_scope"
                if self.labels[indices[0]] not in policy.get("accepted_labels", self.labels)
                else "below_threshold"
                if status == "insufficient_confidence"
                else "accepted_by_policy"
            ),
            "observation_ms": float(np.asarray(raw)[:, 0].sum()),
            "pipeline_ms": (time.perf_counter() - start) * 1000,
            **(
                {
                    "model_packets": 0 if short else self.fixed_prefix_packets,
                    "model_prefix_limit": self.fixed_prefix_packets,
                    "model_observation_ms": None
                    if short
                    else float(raw[: self.fixed_prefix_packets, 0].sum()),
                }
                if self.fixed_prefix_packets
                else {}
            ),
        }
