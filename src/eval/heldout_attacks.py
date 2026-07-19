"""Held-out attack evaluation — fixes the circularity in the robustness claim.

The training augmentation (src/data/augment.py) uses random jitter / additive
padding / packet drops. Testing against that same family is circular ("we
studied for our own exam"). Here we define FOUR attacks with *different
mechanisms* that appear nowhere in training, and measure whether the
morph-trained model's robustness generalizes to them.

Attacks (all operate on (B, T=30, 3) raw [IPT, DIR, SIZE], respecting padding):
  1. size_normalize  - pad every packet toward the MTU (deterministic size
                       flattening; a real Tor-style defense). Unlike training's
                       small *random additive* padding.
  2. fragment        - split large packets into two half-size packets, shifting
                       the sequence. Changes structure, unlike random drops.
  3. constant_timing - replace inter-packet times with a constant (regularized
                       cadence). Unlike training's random *additive* jitter.
  4. dummy_inject    - insert dummy packets between real ones. Adds structure,
                       the opposite of dropping.

Usage:
    python -m src.eval.heldout_attacks --tags tcn_supervised tcn_contrastive tcn_contrastive_morph
"""
from __future__ import annotations

import argparse
import json
import os

import numpy as np
import torch
from sklearn.metrics import f1_score

from src.eval.common import load_data, make_normalizer, load_model, RESULTS_DIR

MTU = 1500.0
IPT, DIR, SIZE = 0, 1, 2


def _real(seq):
    """Return (real_packets (n,3) numpy, n) for one (T,3) numpy sequence."""
    m = seq[:, SIZE] != 0
    return seq[m], int(m.sum())


def _repack(packets, T=30):
    """Left-align a list/array of packets into a (T,3) array, zero-padded."""
    out = np.zeros((T, 3), dtype=np.float32)
    packets = np.asarray(packets, dtype=np.float32)[:T]
    out[: len(packets)] = packets
    return out


def size_normalize(X, severity=1.0):
    X = X.clone()
    mask = X[:, :, SIZE] != 0
    grown = X[:, :, SIZE] + severity * (MTU - X[:, :, SIZE])
    X[:, :, SIZE] = torch.where(mask, grown.clamp(max=MTU), X[:, :, SIZE])
    return X


def constant_timing(X, severity=1.0, const=10.0):
    X = X.clone()
    mask = X[:, :, SIZE] != 0
    newipt = X[:, :, IPT] * (1 - severity) + severity * const
    X[:, :, IPT] = torch.where(mask, newipt, X[:, :, IPT])
    return X


def fragment(X, severity=1.0, thresh=600.0, rng=None):
    rng = rng or np.random.RandomState(0)
    Xn = X.numpy()
    out = np.zeros_like(Xn)
    for b in range(len(Xn)):
        pk, n = _real(Xn[b])
        new = []
        for p in pk:
            if p[SIZE] > thresh and rng.random() < severity:
                half = p.copy(); half[SIZE] = p[SIZE] / 2.0
                new.append(half); new.append(half.copy())
            else:
                new.append(p)
        out[b] = _repack(new)
    return torch.tensor(out)


def dummy_inject(X, severity=1.0, max_dummies=8, rng=None):
    rng = rng or np.random.RandomState(0)
    Xn = X.numpy()
    out = np.zeros_like(Xn)
    for b in range(len(Xn)):
        pk, n = _real(Xn[b])
        k = int(round(severity * max_dummies))
        new = list(pk)
        for _ in range(k):
            pos = rng.randint(0, len(new) + 1)
            dummy = np.array([rng.uniform(0, 20),
                              rng.choice([-1.0, 1.0]),
                              rng.uniform(40, MTU)], dtype=np.float32)
            new.insert(pos, dummy)
        out[b] = _repack(new)
    return torch.tensor(out)


ATTACKS = {
    "size_normalize": size_normalize,
    "fragment": fragment,
    "constant_timing": constant_timing,
    "dummy_inject": dummy_inject,
}


@torch.no_grad()
def eval_f1(model, X, y, normalizer, batch=512):
    preds = []
    for i in range(0, len(X), batch):
        logits, _ = model(normalizer(X[i:i + batch]))
        preds.append(logits.argmax(1).cpu())
    return f1_score(y.numpy(), torch.cat(preds).numpy(), average="macro")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tags", nargs="+",
                    default=["tcn_supervised", "tcn_contrastive", "tcn_contrastive_morph"])
    ap.add_argument("--severity", type=float, default=1.0)
    ap.add_argument("--sample", type=int, default=6000, help="Test subsample for speed")
    args = ap.parse_args()

    data = load_data()
    names = data["names"]; nc = len(names)
    normalizer = make_normalizer(data["Xtr"])

    # Stratified-ish subsample for the per-sample attacks.
    rng = np.random.RandomState(0)
    idx = rng.choice(len(data["Xte"]), min(args.sample, len(data["Xte"])), replace=False)
    Xte, yte = data["Xte"][idx], data["yte"][idx]

    models = {t: load_model(t, nc)[0] for t in args.tags}

    # Clean baseline per model.
    rows = {t: {"clean": eval_f1(m, Xte, yte, normalizer)} for t, m in models.items()}

    for aname, afn in ATTACKS.items():
        Xatt = afn(Xte, severity=args.severity, rng=np.random.RandomState(1)) \
            if aname in ("fragment", "dummy_inject") else afn(Xte, severity=args.severity)
        for t, m in models.items():
            rows[t][aname] = eval_f1(m, Xatt, yte, normalizer)

    # Print table.
    cols = ["clean"] + list(ATTACKS.keys())
    hdr = f"{'model':26s} " + " ".join(f"{c[:13]:>13s}" for c in cols)
    print(hdr); print("-" * len(hdr))
    for t in args.tags:
        print(f"{t:26s} " + " ".join(f"{rows[t][c]:13.3f}" for c in cols))

    with open(os.path.join(RESULTS_DIR, "heldout_attacks.json"), "w") as f:
        json.dump({"severity": args.severity, "results": rows}, f, indent=2)
    print(f"\nsaved results/heldout_attacks.json")


if __name__ == "__main__":
    main()
