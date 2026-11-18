"""Shared helpers for evaluation scripts: load processed data and trained models."""
from __future__ import annotations

import json
import os

import numpy as np
import torch

from src.models.tcn import TCNEncoder
from src.models.lstm import LSTMEncoder
from src.models.heads import TrafficNet
from src.data.transforms import fit_channel_stats, Normalizer

ROOT = os.path.join(os.path.dirname(__file__), "..", "..")
DATA = os.path.join(ROOT, "data", "processed", "quic22_seq.npz")
RESULTS_DIR = os.path.join(ROOT, "results")
MODELS_DIR = os.path.join(ROOT, "models")


def build_encoder(name: str):
    if name == "tcn":
        return TCNEncoder(in_channels=3)
    if name == "lstm":
        return LSTMEncoder(in_channels=3, bidirectional=False)
    if name == "bilstm":
        return LSTMEncoder(in_channels=3, bidirectional=True)
    raise ValueError(name)


def load_data(path=DATA):
    d = np.load(path, allow_pickle=True)
    t = lambda a: torch.tensor(a, dtype=torch.float32)
    l = lambda a: torch.tensor(a, dtype=torch.long)
    names = [str(x) for x in d["class_names"]] if "class_names" in d else None
    return dict(Xtr=t(d["Xtr"]), ytr=l(d["ytr"]), Xva=t(d["Xva"]), yva=l(d["yva"]),
                Xte=t(d["Xte"]), yte=l(d["yte"]), names=names)


def make_normalizer(Xtr, device="cpu"):
    return Normalizer(*fit_channel_stats(Xtr)).to(device)


def load_model(tag: str, num_classes: int, device="cpu", embedding_dim: int = 32):
    """Rebuild a TrafficNet from results/{tag}.json config + models/{tag}.pt weights."""
    with open(os.path.join(RESULTS_DIR, f"{tag}.json")) as f:
        cfg = json.load(f)
    model = TrafficNet(build_encoder(cfg["encoder"]), num_classes, embedding_dim).to(device)
    model.load_state_dict(torch.load(os.path.join(MODELS_DIR, f"{tag}.pt"), map_location=device))
    model.eval()
    return model, cfg
