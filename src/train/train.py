"""Unified trainer for the Strategy-B rebuild.

One script covers:
  * Phase 2 — supervised TCN            (--mode supervised --encoder tcn)
  * Phase 3 — robust contrastive        (--mode contrastive --morph --encoder tcn)
  * Phase 4 — encoder ablation          (--encoder {tcn,lstm,bilstm})

Always reports BOTH clean and fully-morphed test metrics, so the robustness
gap (the headline result) falls out of every run.

Usage:
    python -m src.train.train --mode contrastive --morph --encoder tcn --epochs 40
"""
from __future__ import annotations

import argparse
import json
import os
import time

import numpy as np
import torch
from torch.utils.data import DataLoader, TensorDataset
from sklearn.metrics import accuracy_score, f1_score, classification_report

from src.models.tcn import TCNEncoder
from src.models.lstm import LSTMEncoder
from src.models.heads import TrafficNet
from src.losses.supcon import SupConLoss
from src.data.transforms import fit_channel_stats, Normalizer
from src.data.augment import MorphAugmenter

DATA = os.path.join(os.path.dirname(__file__), "..", "..", "data", "processed", "quic22_seq.npz")
RESULTS_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "results")
MODELS_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "models")


def build_encoder(name: str):
    if name == "tcn":
        return TCNEncoder(in_channels=3)
    if name == "lstm":
        return LSTMEncoder(in_channels=3, bidirectional=False)
    if name == "bilstm":
        return LSTMEncoder(in_channels=3, bidirectional=True)
    raise ValueError(name)


def load_data(path):
    d = np.load(path, allow_pickle=True)
    t = lambda a: torch.tensor(a, dtype=torch.float32)
    l = lambda a: torch.tensor(a, dtype=torch.long)
    names = [str(x) for x in d["class_names"]] if "class_names" in d else None
    return (t(d["Xtr"]), l(d["ytr"]), t(d["Xva"]), l(d["yva"]), t(d["Xte"]), l(d["yte"]), names)


def class_weights(y, num_classes, mode="sqrt_inv"):
    """Inverse-frequency class weights to counter imbalance (sqrt softens it)."""
    counts = torch.bincount(y, minlength=num_classes).float().clamp(min=1)
    w = len(y) / (num_classes * counts)
    if mode == "sqrt_inv":
        w = w.sqrt()
    return w / w.mean()


@torch.no_grad()
def _predict(model, X, normalizer, device, morph=None, batch=512):
    model.eval()
    preds = []
    for i in range(0, len(X), batch):
        xb = X[i:i + batch].to(device)
        if morph is not None:
            xb = morph.morph(xb, training=False)
        xb = normalizer(xb)
        logits, _ = model(xb)
        preds.append(logits.argmax(1).cpu())
    return torch.cat(preds).numpy()


def evaluate(model, X, y, normalizer, device, morph=None, batch=512):
    preds = _predict(model, X, normalizer, device, morph, batch)
    yt = y.numpy()
    return accuracy_score(yt, preds), f1_score(yt, preds, average="macro")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", choices=["supervised", "contrastive"], default="supervised")
    ap.add_argument("--encoder", choices=["tcn", "lstm", "bilstm"], default="tcn")
    ap.add_argument("--morph", action="store_true", help="Apply morph augmentation during training")
    ap.add_argument("--epochs", type=int, default=40)
    ap.add_argument("--batch_size", type=int, default=192)
    ap.add_argument("--lr", type=float, default=1e-3)
    ap.add_argument("--con_weight", type=float, default=0.5)
    ap.add_argument("--class_weight", choices=["none", "inv", "sqrt_inv"], default="sqrt_inv")
    ap.add_argument("--temperature", type=float, default=0.07)
    ap.add_argument("--patience", type=int, default=8)
    ap.add_argument("--embedding_dim", type=int, default=32)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--tag", default=None, help="Results filename tag")
    ap.add_argument("--data", default=DATA, help="Path to processed .npz")
    ap.add_argument("--holdout_class", type=int, default=None,
                    help="Global class id to exclude from train/val (for few-shot demo). "
                         "Test set keeps all classes; remaining classes are remapped for training.")
    args = ap.parse_args()

    torch.manual_seed(args.seed)
    np.random.seed(args.seed)
    device = "cuda" if torch.cuda.is_available() else "cpu"

    Xtr, ytr, Xva, yva, Xte, yte, class_names = load_data(args.data)

    if args.holdout_class is not None:
        h = args.holdout_class
        remaining = [c for c in range(int(ytr.max().item()) + 1) if c != h]
        remap = {old: new for new, old in enumerate(remaining)}

        def drop(X, y):
            keep = y != h
            X, y = X[keep], y[keep]
            y = torch.tensor([remap[int(v)] for v in y], dtype=torch.long)
            return X, y

        held_name = class_names[h] if class_names else str(h)
        Xtr, ytr = drop(Xtr, ytr)
        Xva, yva = drop(Xva, yva)
        Xte, yte = drop(Xte, yte)
        class_names = [class_names[c] for c in remaining] if class_names else None
        print(f"Hold-out: excluded class {h} ({held_name}); training on {len(remaining)} classes")

    num_classes = int(ytr.max().item() + 1)
    print(f"Loaded: train {tuple(Xtr.shape)}, val {tuple(Xva.shape)}, test {tuple(Xte.shape)}, "
          f"classes={num_classes}, device={device}")

    normalizer = Normalizer(*fit_channel_stats(Xtr)).to(device)
    morph = MorphAugmenter() if args.morph else None

    model = TrafficNet(build_encoder(args.encoder), num_classes, args.embedding_dim).to(device)
    print(f"Model: {args.encoder}, params={model.num_parameters:,}")

    opt = torch.optim.Adam(model.parameters(), lr=args.lr)
    weight = None if args.class_weight == "none" else class_weights(ytr, num_classes, args.class_weight).to(device)
    ce = torch.nn.CrossEntropyLoss(weight=weight)
    supcon = SupConLoss(args.temperature)

    loader = DataLoader(TensorDataset(Xtr, ytr), batch_size=args.batch_size, shuffle=True)

    tag = args.tag or (f"{args.encoder}_{args.mode}{'_morph' if args.morph else ''}"
                       + (f"_holdout{args.holdout_class}" if args.holdout_class is not None else ""))
    best_val, best_state, wait = -1.0, None, 0

    for epoch in range(1, args.epochs + 1):
        model.train()
        losses = []
        for xb, yb in loader:
            xb, yb = xb.to(device), yb.to(device)
            if morph is not None:
                xb = morph.morph(xb, training=True)
            xb = normalizer(xb)
            logits, emb = model(xb)
            loss = ce(logits, yb)
            if args.mode == "contrastive":
                loss = loss + args.con_weight * supcon(emb, yb)
            opt.zero_grad()
            loss.backward()
            opt.step()
            losses.append(loss.item())

        val_acc, val_f1 = evaluate(model, Xva, yva, normalizer, device)
        if val_f1 > best_val:
            best_val, best_state, wait = val_f1, {k: v.cpu().clone() for k, v in model.state_dict().items()}, 0
        else:
            wait += 1
        if epoch % 5 == 0 or epoch == 1:
            print(f"epoch {epoch:3d}  train_loss {np.mean(losses):.4f}  val_acc {val_acc:.4f}  val_f1 {val_f1:.4f}")
        if wait >= args.patience:
            print(f"early stop at epoch {epoch} (best val_f1 {best_val:.4f})")
            break

    model.load_state_dict(best_state)

    clean_acc, clean_f1 = evaluate(model, Xte, yte, normalizer, device)
    morph_eval = MorphAugmenter()
    morph_acc, morph_f1 = evaluate(model, Xte, yte, normalizer, device, morph=morph_eval)

    print(f"\n=== {tag} ===")
    print(f"clean   : acc {clean_acc:.4f}  f1 {clean_f1:.4f}")
    print(f"morphed : acc {morph_acc:.4f}  f1 {morph_f1:.4f}   (drop {clean_f1 - morph_f1:+.4f})")

    # Per-class breakdown on clean test (shows minority-class behavior).
    if class_names is not None:
        preds_clean = _predict(model, Xte, normalizer, device)
        print("\nper-class (clean):")
        print(classification_report(yte.numpy(), preds_clean,
                                    target_names=class_names, digits=3, zero_division=0))

    os.makedirs(RESULTS_DIR, exist_ok=True)
    os.makedirs(MODELS_DIR, exist_ok=True)
    results = {
        "tag": tag, "encoder": args.encoder, "mode": args.mode, "morph_train": args.morph,
        "num_classes": num_classes, "params": model.num_parameters,
        "holdout_class": args.holdout_class,
        "clean_acc": clean_acc, "clean_f1": clean_f1,
        "morph_acc": morph_acc, "morph_f1": morph_f1,
        "robustness_gap_f1": clean_f1 - morph_f1,
    }
    with open(os.path.join(RESULTS_DIR, f"{tag}.json"), "w") as f:
        json.dump(results, f, indent=2)
    torch.save(model.state_dict(), os.path.join(MODELS_DIR, f"{tag}.pt"))
    print(f"saved results/{tag}.json and models/{tag}.pt")


if __name__ == "__main__":
    main()
