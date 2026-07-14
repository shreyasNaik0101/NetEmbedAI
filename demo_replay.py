#!/usr/bin/env python3
"""Live "replay scope" — stream a real network flow packet-by-packet and watch
the model classify it as the packets arrive.

Uses real held-out CESNET-QUIC22 test flows (the data the model was trained on),
so classifications are genuinely correct — it just *animates* them as if the
traffic were arriving live. Also shows early classification: the model's guess
firms up as more packets are seen.

Run it yourself for the full effect:
    python demo_replay.py                 # random flows, interactive
    python demo_replay.py --app youtube   # pick an app
    python demo_replay.py --morph         # disguise the traffic
    python demo_replay.py --auto          # non-interactive: play a few and exit

Controls (interactive): Enter = next flow, m = replay morphed, q = quit.
"""
from __future__ import annotations

import argparse
import os
import sys
import time

import numpy as np
import torch
import torch.nn.functional as F

from src.eval.common import load_data, make_normalizer, load_model
from src.data.augment import MorphAugmenter

# --- ANSI setup (enable virtual-terminal colors on Windows) ---
if os.name == "nt":
    os.system("")
RESET, DIM, BOLD = "\033[0m", "\033[2m", "\033[1m"
UP_COL, DOWN_COL = "\033[38;5;208m", "\033[38;5;39m"   # orange up, blue down
GREEN, RED, GREY = "\033[38;5;42m", "\033[38;5;203m", "\033[38;5;245m"
CLEAR = "\033[2J\033[H"
ROWS = 7          # bar rows per direction
MAXSIZE = 1500.0  # size that fills a full bar


def render(packets, upto, pred, true_app, morphed):
    """Build one animation frame as a string."""
    n = len(packets)
    out = [CLEAR]
    title = "LIVE TRAFFIC SCOPE" + ("   [MORPHED / disguised]" if morphed else "")
    out.append(f"{BOLD}{title}{RESET}   flow: {DIM}{true_app}{RESET}\n")
    out.append(f"{UP_COL}↑ you→server{RESET}   {DOWN_COL}↓ server→you{RESET}   {DIM}bar height = packet size{RESET}\n")

    # upload rows (top), a centre axis, download rows (bottom)
    grid_up = [[" "] * n for _ in range(ROWS)]
    grid_dn = [[" "] * n for _ in range(ROWS)]
    for i, p in enumerate(packets):
        if i >= upto:
            break
        h = max(1, int(round(min(p["size"], MAXSIZE) / MAXSIZE * ROWS)))
        if p["dir"] >= 0:
            for r in range(h):
                grid_up[ROWS - 1 - r][i] = "█"
        else:
            for r in range(h):
                grid_dn[r][i] = "█"
    for row in grid_up:
        out.append(UP_COL + "".join(row) + RESET)
    out.append(GREY + "─" * n + RESET)
    for row in grid_dn:
        out.append(DOWN_COL + "".join(row) + RESET)

    out.append(f"\n{DIM}packets seen: {upto}/{n}{RESET}")
    if pred is not None:
        app, conf = pred
        ok = app == true_app
        col = GREEN if ok else RED
        bar = int(round(conf * 24))
        mark = "✓" if ok else "✗"
        out.append(f"model guess: {col}{BOLD}{app}{RESET} {col}{mark}{RESET}")
        out.append(f"confidence : {col}{'█' * bar}{GREY}{'░' * (24 - bar)}{RESET} {int(round(conf*100))}%")
    return "\n".join(out)


@torch.no_grad()
def classify(model, seq, normalizer, names, upto):
    """Classify the flow using only the first `upto` packets (rest zeroed)."""
    x = seq.clone()
    x[upto:] = 0
    logits, _ = model(normalizer(x.unsqueeze(0)))
    p = F.softmax(logits, 1)[0]
    i = int(p.argmax())
    return names[i], float(p[i])


def play(model, seq_raw, true_app, normalizer, names, morph_aug, morphed, delay):
    seq = morph_aug.morph(seq_raw.clone().unsqueeze(0), severity=1.0, training=False)[0] if morphed else seq_raw
    real = seq[seq[:, 2] != 0]
    packets = [{"dir": int(np.sign(p[1].item())) or 1, "size": float(p[2].item())} for p in real]
    n = len(packets)
    for k in range(1, n + 1):
        pred = classify(model, seq, normalizer, names, k) if k >= 2 else None
        sys.stdout.write(render(packets, k, pred, true_app, morphed))
        sys.stdout.flush()
        time.sleep(delay)
    time.sleep(0.4)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default="tcn_contrastive_morph", help="Model tag to use")
    ap.add_argument("--app", default=None, help="Pick a specific app (else random)")
    ap.add_argument("--morph", action="store_true", help="Disguise the traffic")
    ap.add_argument("--delay", type=float, default=0.12, help="Seconds between packets")
    ap.add_argument("--auto", action="store_true", help="Play a few flows and exit")
    args = ap.parse_args()

    data = load_data()
    names = data["names"]
    num_classes = len(names)
    normalizer = make_normalizer(data["Xtr"])
    model, _ = load_model(args.model, num_classes)
    morph_aug = MorphAugmenter()
    Xte, yte = data["Xte"], data["yte"]
    rng = np.random.RandomState()

    def pick(app):
        if app and app in names:
            pool = np.where(yte.numpy() == names.index(app))[0]
        else:
            pool = np.arange(len(Xte))
        idx = int(rng.choice(pool))
        return Xte[idx], names[yte[idx].item()]

    if args.auto:
        for app in ["youtube", "instagram", "spotify"]:
            seq, true_app = pick(app)
            play(model, seq, true_app, normalizer, names, morph_aug, False, args.delay)
            play(model, seq, true_app, normalizer, names, morph_aug, True, args.delay)
        print(f"\n{DIM}(auto demo complete){RESET}")
        return

    print(f"{DIM}Model: {args.model}. Enter=next flow, m=morph replay, q=quit.{RESET}")
    morphed = args.morph
    while True:
        seq, true_app = pick(args.app)
        play(model, seq, true_app, normalizer, names, morph_aug, morphed, args.delay)
        cmd = input(f"\n{DIM}[Enter]=next  [m]=morph this flow  [q]=quit >{RESET} ").strip().lower()
        if cmd == "q":
            break
        elif cmd == "m":
            play(model, seq, true_app, normalizer, names, morph_aug, True, args.delay)
            input(f"{DIM}[Enter] to continue >{RESET} ")
            morphed = args.morph
        else:
            morphed = args.morph


if __name__ == "__main__":
    main()
