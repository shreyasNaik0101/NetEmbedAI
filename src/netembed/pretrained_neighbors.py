"""Offline CESNET 30pktTCNET transfer with a frozen encoder and exact retrieval."""

import importlib.metadata
import json
import shutil
from pathlib import Path

import numpy as np
import torch

from .bundle import sha256, write_json
from .contract import BUDGETS, FEATURES, validate_array
from .packet_neighbors import bucket

VERSION = "cesnet-frozen-neighbors-v1"
UPSTREAM_VERSION = "0.4.1"


def packet_batch(flows):
    """Upstream source expects (batch, channels, 30), not our (batch, 30, 3)."""
    batch = np.zeros((len(flows), 3, 30), dtype=np.float32)
    for i, raw in enumerate(flows):
        raw = validate_array(raw)
        batch[i, :, : len(raw)] = raw.T
    return batch


class FrozenEncoder:
    def __init__(self, weights, expected_sha256):
        weights = Path(weights)
        if not weights.is_file() or sha256(weights) != expected_sha256:
            raise ValueError("missing or changed official encoder weights")
        if importlib.metadata.version("cesnet-models") != UPSTREAM_VERSION:
            raise ValueError("use the pinned optional cesnet-models version")
        from cesnet_models.models import Model_30pktTCNET_256_Weights, model_30pktTCNET_256

        self.model = model_30pktTCNET_256(weights=None)
        state = torch.load(weights, map_location="cpu", weights_only=True)
        # Official loader removes its pretraining-only classifier head too.
        state.pop("arcface_module.W", None)
        self.model.load_state_dict(state, strict=True)
        self.model.eval()
        self.transform = Model_30pktTCNET_256_Weights.DEFAULT.transforms["ppi_transform"]
        self.weights, self.weights_sha256 = weights, expected_sha256

    def encode(self, flows, batch_size=128, progress=None):
        if not flows or not 1 <= batch_size <= 256:
            raise ValueError("invalid bounded embedding batch")
        results = []
        with torch.inference_mode():
            for i in range(0, len(flows), batch_size):
                # Only actual supplied prefix values enter the upstream transform.
                values = self.transform(packet_batch(flows[i : i + batch_size]))
                vectors = self.model(torch.from_numpy(values)).numpy()
                if (
                    vectors.shape != (len(values), 256)
                    or not np.isfinite(vectors).all()
                    or not np.allclose(np.linalg.norm(vectors, axis=1), 1, atol=1e-4)
                ):
                    raise ValueError("invalid official encoder output")
                results.append(vectors)
                if progress is not None:
                    progress(min(i + batch_size, len(flows)), len(flows))
        return np.concatenate(results)


class FrozenNeighbors:
    def __init__(self, encoder, banks, targets, ids, labels, provenance=None):
        self.encoder, self.banks = encoder, banks
        self.y = np.asarray(targets)
        if (
            self.y.dtype.kind not in "iu"
            or self.y.shape != (len(ids),)
            or not 1 <= len(ids) <= 50000
            or len(set(ids)) != len(ids)
            or len(set(labels)) != len(labels)
            or not labels
            or np.any(self.y < 0)
            or np.any(self.y >= len(labels))
        ):
            raise ValueError("invalid frozen-embedding reference inventory")
        if set(banks) != set(BUDGETS) or any(
            bank.shape != (len(ids), 256)
            or not np.isfinite(bank).all()
            or not np.allclose(np.linalg.norm(bank, axis=1), 1, atol=1e-4)
            for bank in banks.values()
        ):
            raise ValueError("invalid normalized embedding banks")
        self.ids, self.labels = list(ids), list(labels)
        self.provenance = provenance or {}

    def predict(self, raw):
        raw = validate_array(raw)
        length = bucket(len(raw))
        query = self.encoder.encode([raw])[0]
        similarities = self.banks[length] @ query
        nearest = int(np.argmax(similarities))
        alternatives = []
        for label in range(len(self.labels)):
            group = np.flatnonzero(self.y == label)
            if len(group):
                index = int(group[np.argmax(similarities[group])])
                alternatives.append((-float(similarities[index]), index, self.labels[label]))
        alternatives.sort()
        return {
            "observed_packets": len(raw),
            "reference_budget": length,
            "label": self.labels[int(self.y[nearest])],
            "reference_id": self.ids[nearest],
            "status": "raw_ranking_uncalibrated" if len(raw) >= 5 else "insufficient_evidence",
            "alternatives": [
                {"label": name, "cosine_similarity": -score} for score, _, name in alternatives[:3]
            ],
        }

    def save(self, destination, wheel):
        destination = Path(destination)
        destination.mkdir(parents=True, exist_ok=False)
        shutil.copyfile(self.encoder.weights, destination / "encoder.pth")
        shutil.copyfile(wheel, destination / "cesnet_models-0.4.1-py3-none-any.whl")
        np.savez_compressed(
            destination / "banks.npz",
            targets=self.y,
            **{f"budget{b}": bank for b, bank in self.banks.items()},
        )
        write_json(
            destination / "metadata.json",
            {
                "version": VERSION,
                "features": FEATURES,
                "upstream_version": UPSTREAM_VERSION,
                "weight_sha256": self.encoder.weights_sha256,
                "ids": self.ids,
                "labels": self.labels,
                "provenance": self.provenance,
                "policy": {"fitted": False},
                "pretraining_period": "W-2022-46; overlaps original public final-test week; not independent there",
                "transform": "upstream saved clipping, no scaling; [IPT_ms,DIR,UDP_payload_bytes] channels-first; zero padding",
                "retrieval": "cosine 1-NN; smallest reference budget >= actual input length; reference-order ties",
            },
        )
        files = ("metadata.json", "encoder.pth", "cesnet_models-0.4.1-py3-none-any.whl", "banks.npz")
        write_json(destination / "checksums.json", {p: sha256(destination / p) for p in files})

    @classmethod
    def load(cls, source):
        source = Path(source)
        checksums = json.loads((source / "checksums.json").read_text())
        expected = {"metadata.json", "encoder.pth", "cesnet_models-0.4.1-py3-none-any.whl", "banks.npz"}
        if set(checksums) != expected or any(sha256(source / k) != v for k, v in checksums.items()):
            raise ValueError("frozen-embedding artifact checksum mismatch")
        meta = json.loads((source / "metadata.json").read_text())
        if (
            meta["version"] != VERSION
            or meta["features"] != FEATURES
            or meta["policy"]["fitted"]
            or meta["upstream_version"] != UPSTREAM_VERSION
            or meta["provenance"].get("fixture")
        ):
            raise ValueError("unsupported frozen-embedding artifact")
        encoder = FrozenEncoder(source / "encoder.pth", meta["weight_sha256"])
        with np.load(source / "banks.npz", allow_pickle=False) as arrays:
            targets = arrays["targets"]
            banks = {b: arrays[f"budget{b}"] for b in BUDGETS}
        return cls(encoder, banks, targets, meta["ids"], meta["labels"], meta["provenance"])
