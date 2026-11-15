"""Robustness sweep — the Strategy-B headline figure.

For each given model, sweep traffic-morphing severity from 0 (clean) upward and
measure macro-F1 at each level. Overlaying a morph-trained model against a plain
baseline shows the robust model's F1 degrading far more slowly under attack.

Usage:
    python -m src.eval.robustness --tags tcn_supervised tcn_contrastive_morph
"""
from __future__ import annotations

import argparse
import json
import os

import numpy as np
import torch
from sklearn.metrics import f1_score

from src.data.augment import MorphAugmenter
from src.eval.common import load_data, make_normalizer, load_model, RESULTS_DIR


@torch.no_grad()
def f1_at_severity(model, X, y, normalizer, severity, seed=0, batch=512):
    torch.manual_seed(seed)  # reproducible perturbations across models
    morph = MorphAugmenter()
    preds = []
    for i in range(0, len(X), batch):
        xb = X[i:i + batch]
        if severity > 0:
            xb = morph.morph(xb, severity=severity, training=False)
        xb = normalizer(xb)
        logits, _ = model(xb)
        preds.append(logits.argmax(1).cpu())
    preds = torch.cat(preds).numpy()
    return f1_score(y.numpy(), preds, average="macro")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tags", nargs="+", required=True, help="Model tags to compare")
    ap.add_argument("--severities", nargs="+", type=float,
                    default=[0.0, 0.5, 1.0, 1.5, 2.0, 3.0])
    args = ap.parse_args()

    data = load_data()
    num_classes = int(data["ytr"].max().item() + 1)
    normalizer = make_normalizer(data["Xtr"])

    curves = {}
    for tag in args.tags:
        model, _ = load_model(tag, num_classes)
        curve = [f1_at_severity(model, data["Xte"], data["yte"], normalizer, s)
                 for s in args.severities]
        curves[tag] = curve
        print(f"{tag:32s} " + "  ".join(f"{s}:{f:.3f}" for s, f in zip(args.severities, curve)))

    out = {"severities": args.severities, "curves": curves}
    with open(os.path.join(RESULTS_DIR, "robustness_sweep.json"), "w") as f:
        json.dump(out, f, indent=2)

    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        plt.figure(figsize=(8, 5))
        for tag, curve in curves.items():
            plt.plot(args.severities, curve, marker="o", label=tag)
        plt.xlabel("Traffic-morphing severity")
        plt.ylabel("Macro-F1")
        plt.title("Robustness to adversarial traffic morphing")
        plt.grid(alpha=0.3)
        plt.legend()
        plt.tight_layout()
        p = os.path.join(RESULTS_DIR, "robustness_sweep.png")
        plt.savefig(p, dpi=150)
        print(f"saved {p}")
    except Exception as e:
        print(f"plot skipped: {e}")


if __name__ == "__main__":
    main()
