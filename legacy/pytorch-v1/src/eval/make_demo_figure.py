"""Generate the README demo visuals from real model predictions.

Produces:
  assets/morph_demo.png  - static "before vs after disguise" hero figure
  assets/morph_demo.gif  - animated toggle between clean and morphed

Both use real outputs from the trained baseline and robust models on a real
held-out Instagram flow, so nothing is fabricated.
"""
from __future__ import annotations

import os

import numpy as np
import torch
import torch.nn.functional as F
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation, PillowWriter

from src.eval.common import load_data, make_normalizer, load_model
from src.data.augment import MorphAugmenter

ASSETS = os.path.join(os.path.dirname(__file__), "..", "..", "assets")
UP, DOWN = "#e8833a", "#3a86d8"      # orange up (you->server), blue down (server->you)
OK, BAD = "#1d9e75", "#d64545"
BG, INK, MUT = "#ffffff", "#1a1a1a", "#6a6a6a"


def predict(model, x, normalizer, names):
    with torch.no_grad():
        logits, _ = model(normalizer(x))
        p = F.softmax(logits, 1)[0]
    i = int(p.argmax())
    return names[i], float(p[i])


def draw_bars(ax, packets):
    ax.clear()
    ax.axhline(0, color="#cccccc", lw=1, zorder=1)
    for i, p in enumerate(packets):
        up = p[1] >= 0
        h = min(p[2], 1500) / 1500 * 1.0
        ax.bar(i, h if up else -h, width=0.8, color=UP if up else DOWN, zorder=2)
    ax.set_ylim(-1.15, 1.15)
    ax.set_xlim(-1, len(packets))
    ax.axis("off")


def verdict(ax, clean_state):
    ax.clear(); ax.axis("off")


def real_packets(seq):
    real = seq[0][seq[0][:, 2] != 0]
    return [(float(p[0]), int(np.sign(p[1].item())) or 1, float(p[2])) for p in real]


def main():
    os.makedirs(ASSETS, exist_ok=True)
    data = load_data(); names = data["names"]; nc = len(names)
    normalizer = make_normalizer(data["Xtr"])
    base, _ = load_model("tcn_supervised", nc)
    robust, _ = load_model("tcn_contrastive_morph", nc)
    morph = MorphAugmenter()

    # Find an Instagram flow where morphing fools the baseline but not the robust model.
    rng = np.random.RandomState(7)
    ig = names.index("instagram")
    pool = np.where(data["yte"].numpy() == ig)[0]; rng.shuffle(pool)
    chosen = None
    for idx in pool[:80]:
        x = data["Xte"][idx:idx + 1]
        if predict(base, x, normalizer, names)[0] != "instagram":
            continue
        torch.manual_seed(idx)
        xm = morph.morph(x.clone(), severity=1.0, training=False)
        bm = predict(base, xm, normalizer, names)
        rm = predict(robust, xm, normalizer, names)
        if bm[0] != "instagram" and rm[0] == "instagram":
            chosen = (x, xm, bm, rm); break
    if chosen is None:
        raise SystemExit("no suitable example found")
    x, xm, bm, rm = chosen
    bc = predict(base, x, normalizer, names)
    rc = predict(robust, x, normalizer, names)
    pk_clean, pk_morph = real_packets(x), real_packets(xm)

    def panel(fig, gs_col, title, packets, base_pred, rob_pred):
        axb = fig.add_subplot(gs_col[0])
        draw_bars(axb, packets)
        axb.set_title(title, color=INK, fontsize=12.5, fontweight="bold",
                      pad=8, linespacing=1.4)
        axt = fig.add_subplot(gs_col[1]); axt.axis("off")
        for row, (label, pred) in enumerate([("Baseline model", base_pred),
                                             ("Robust model", rob_pred)]):
            ok = pred[0] == "instagram"
            c = OK if ok else BAD
            y = 0.62 - row * 0.42
            axt.text(0.02, y, label, color=MUT, fontsize=10, va="center")
            axt.text(0.98, y, f"{'✓' if ok else '✗'} {pred[0]}  ({pred[1]*100:.0f}%)",
                     color=c, fontsize=11, fontweight="bold", va="center", ha="right")

    def build(fig, morphed):
        fig.clear(); fig.patch.set_facecolor(BG)
        gs = fig.add_gridspec(2, 2, height_ratios=[2.2, 1], hspace=0.4, wspace=0.15,
                              left=0.04, right=0.96, top=0.74, bottom=0.12)
        fig.suptitle("Same Instagram traffic — can the model still recognize it?",
                     color=INK, fontsize=15, fontweight="bold", y=0.965)
        panel(fig, [gs[0, 0], gs[1, 0]], "Real traffic", pk_clean, bc, rc)
        rp = pk_morph if morphed else pk_clean
        rt = "Disguised traffic\n(padded + jittered — same content)" if morphed else "Real traffic"
        panel(fig, [gs[0, 1], gs[1, 1]], rt, rp,
              bm if morphed else bc, rm if morphed else rc)
        fig.text(0.5, 0.03, "each bar = one packet   ·   up = you→server, down = server→you"
                 "   ·   bar height = packet size", ha="center", color=MUT, fontsize=9)

    # Static hero: real (left) vs morphed (right).
    fig = plt.figure(figsize=(11, 4.2))
    build(fig, morphed=True)
    fig.savefig(os.path.join(ASSETS, "morph_demo.png"), dpi=130, facecolor=BG)
    print("saved assets/morph_demo.png")

    # Animated toggle: clean <-> morphed on the right panel.
    fig2 = plt.figure(figsize=(11, 4.2))
    states = [False] * 8 + [True] * 12   # hold clean, then morphed

    def update(i):
        build(fig2, morphed=states[i])
    anim = FuncAnimation(fig2, update, frames=len(states), interval=1)
    anim.save(os.path.join(ASSETS, "morph_demo.gif"), writer=PillowWriter(fps=4))
    print("saved assets/morph_demo.gif")


if __name__ == "__main__":
    main()
