"""Embedding analysis: t-SNE visualization + intra/inter-class similarity.

Quantifies how well the learned embedding space separates traffic classes.
Contrastive (and especially morph-trained contrastive) models should show
tighter intra-class and lower inter-class similarity than a plain supervised
model.

Usage:
    python -m src.eval.embeddings --tag tcn_contrastive_morph
"""
from __future__ import annotations

import argparse
import json
import os

import numpy as np
import torch
import torch.nn.functional as F

from src.eval.common import load_data, make_normalizer, load_model, RESULTS_DIR


@torch.no_grad()
def get_embeddings(model, X, normalizer, batch=512):
    embs = []
    for i in range(0, len(X), batch):
        xb = normalizer(X[i:i + batch])
        _, e = model(xb)
        embs.append(e.cpu())
    return torch.cat(embs)


def similarity_metrics(emb, labels):
    emb = F.normalize(emb, dim=1)
    sim = emb @ emb.t()
    labels = labels.view(-1, 1)
    same = (labels == labels.t())
    eye = torch.eye(len(emb), dtype=torch.bool)
    same = same & ~eye
    diff = ~same & ~eye
    return {
        "intra_class_sim": float(sim[same].mean()),
        "inter_class_sim": float(sim[diff].mean()),
        "separation": float(sim[same].mean() - sim[diff].mean()),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tag", required=True)
    ap.add_argument("--max_points", type=int, default=4000, help="Subsample for t-SNE")
    args = ap.parse_args()

    data = load_data()
    num_classes = int(data["ytr"].max().item() + 1)
    normalizer = make_normalizer(data["Xtr"])
    model, _ = load_model(args.tag, num_classes)

    emb = get_embeddings(model, data["Xte"], normalizer)
    y = data["yte"]

    metrics = similarity_metrics(emb, y)
    print(f"intra-class sim: {metrics['intra_class_sim']:.4f}")
    print(f"inter-class sim: {metrics['inter_class_sim']:.4f}")
    print(f"separation     : {metrics['separation']:.4f}")
    with open(os.path.join(RESULTS_DIR, f"embedding_metrics_{args.tag}.json"), "w") as f:
        json.dump(metrics, f, indent=2)

    # t-SNE on a subsample.
    idx = np.random.RandomState(0).choice(len(emb), min(args.max_points, len(emb)), replace=False)
    try:
        from sklearn.manifold import TSNE
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt

        xy = TSNE(n_components=2, perplexity=30, init="pca", random_state=0).fit_transform(emb[idx].numpy())
        names = data["names"] or [str(i) for i in range(num_classes)]
        plt.figure(figsize=(10, 8))
        colors = plt.cm.tab10(np.linspace(0, 1, num_classes))
        for c in range(num_classes):
            m = y[idx].numpy() == c
            plt.scatter(xy[m, 0], xy[m, 1], s=8, alpha=0.6, color=colors[c], label=names[c])
        plt.legend(markerscale=2, fontsize=8)
        plt.title(f"t-SNE of embeddings — {args.tag}")
        plt.tight_layout()
        p = os.path.join(RESULTS_DIR, f"tsne_{args.tag}.png")
        plt.savefig(p, dpi=150)
        print(f"saved {p}")
    except Exception as e:
        print(f"t-SNE skipped: {e}")


if __name__ == "__main__":
    main()
