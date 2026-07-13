"""Few-shot recognition via embedding prototypes — Phase 5 (Strategy C, light).

Tests whether the learned embedding space can recognize traffic classes from
only K labeled examples, WITHOUT retraining. Most compelling when run on a model
that was trained with a class held out (see train.py --holdout_class): if that
novel class is still recognized from a handful of packets, the embedding
generalizes to unseen apps.

Protocol (prototypical, N-way K-shot):
  * embed the whole test set once,
  * per episode: sample K support embeddings per class -> class prototype (mean),
    classify the remaining query embeddings by nearest prototype (cosine),
  * average accuracy / per-class recall over many episodes.

Usage:
    python -m src.eval.fewshot --tag tcn_contrastive_morph_holdout7 --shots 5 10 20
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
def embed_all(model, X, normalizer, batch=512):
    out = []
    for i in range(0, len(X), batch):
        _, e = model(normalizer(X[i:i + batch]))
        out.append(e.cpu())
    return F.normalize(torch.cat(out), dim=1)


def few_shot_episode(emb, y, num_classes, k, rng):
    """One N-way K-shot episode. Returns (accuracy, per_class_correct, per_class_total)."""
    support_idx, query_idx = [], []
    for c in range(num_classes):
        idx = np.where(y == c)[0]
        rng.shuffle(idx)
        support_idx.append(idx[:k])
        query_idx.append(idx[k:])
    protos = torch.stack([emb[si].mean(0) for si in support_idx])   # (C, D)
    protos = F.normalize(protos, dim=1)

    q = np.concatenate(query_idx)
    sims = emb[q] @ protos.t()                                       # cosine (already normed)
    preds = sims.argmax(1).numpy()
    truth = y[q]

    correct = np.zeros(num_classes); total = np.zeros(num_classes)
    for c in range(num_classes):
        m = truth == c
        total[c] = m.sum()
        correct[c] = (preds[m] == c).sum()
    return (preds == truth).mean(), correct, total


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tag", required=True)
    ap.add_argument("--shots", nargs="+", type=int, default=[5, 10, 20])
    ap.add_argument("--episodes", type=int, default=200)
    args = ap.parse_args()

    data = load_data()
    num_classes = int(data["yte"].max().item() + 1)     # all 10 classes in the test set
    normalizer = make_normalizer(data["Xtr"])
    # The classifier head was trained on fewer classes if a class was held out;
    # few-shot uses embeddings only, so the head size just needs to load cleanly.
    model, _ = load_model(args.tag, _train_classes(args.tag, num_classes))

    emb = embed_all(model, data["Xte"], normalizer)
    y = data["yte"].numpy()
    names = data["names"] or [str(i) for i in range(num_classes)]
    novel = _holdout(args.tag)

    report = {}
    for k in args.shots:
        rng = np.random.RandomState(0)
        accs, corr, tot = [], np.zeros(num_classes), np.zeros(num_classes)
        for _ in range(args.episodes):
            a, c, t = few_shot_episode(emb, y, num_classes, k, rng)
            accs.append(a); corr += c; tot += t
        recall = corr / np.clip(tot, 1, None)
        report[k] = {"overall_acc": float(np.mean(accs)),
                     "per_class_recall": {names[i]: float(recall[i]) for i in range(num_classes)}}
        print(f"\n{k}-shot: overall acc {np.mean(accs):.3f}")
        for i in range(num_classes):
            tag_novel = "  <-- NOVEL (never trained)" if novel is not None and i == novel else ""
            print(f"  {names[i]:22s} recall {recall[i]:.3f}{tag_novel}")

    with open(os.path.join(RESULTS_DIR, f"fewshot_{args.tag}.json"), "w") as f:
        json.dump({"novel_class": novel, "shots": report}, f, indent=2)
    print(f"\nsaved results/fewshot_{args.tag}.json")


def _holdout(tag):
    """Read holdout_class from the run's results json, if any."""
    p = os.path.join(RESULTS_DIR, f"{tag}.json")
    if os.path.exists(p):
        with open(p) as f:
            return json.load(f).get("holdout_class")
    return None


def _train_classes(tag, num_classes):
    """Number of classes the model's classifier head was trained with."""
    return num_classes - 1 if _holdout(tag) is not None else num_classes


if __name__ == "__main__":
    main()
