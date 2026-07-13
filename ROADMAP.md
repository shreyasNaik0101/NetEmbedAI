# NetEmbedAI — Rebuild Roadmap (Strategy B)

> **Status:** active rebuild on branch `strategy-b-rebuild`. The old TensorFlow
> code (`models/`, `scripts/`, `utils/`, `demo_predict.py`) is kept untouched as
> a reference/"v1" and will be retired once the rebuild reaches parity.

## The one-line pitch

> A modern encrypted-traffic classifier whose contrastively-learned embeddings
> stay **robust to adversarial traffic morphing**, benchmarked for real-time
> throughput, and able to recognize unseen apps from a handful of packets.

## What changed from v1 and why

| v1 (original) | Rebuild | Reason |
|---|---|---|
| 24 aggregate flow **statistics** treated as a fake 24-step sequence | First-30 **per-packet** sequence `[size, IAT, direction]` | A BiLSTM/TCN needs a *real* temporal sequence; summary stats have no order. RF beat the BiLSTM in v1 — the classic "wrong inductive bias for tabular data" tell. |
| Synthetic gamma-distributed data (91.5%) + weak Kaggle run (78.5%) | **CESNET-QUIC22** real per-packet data via `cesnet-datazoo` | Credible, modern (QUIC), and ships packet sequences pre-extracted — no PCAP parsing. |
| BiLSTM (offline only) | **TCN** primary encoder (causal, streaming-friendly, fast), with LSTM/1D-CNN/Transformer as comparisons | TCN is parallelizable and low-latency — supports the throughput story. |
| Plain SupCon on clean traffic | **Adversarial-robust SupCon**: augment with jitter / padding / drops so morphed traffic still clusters with its true class | **This is the headline contribution (Strategy B).** |
| TensorFlow | **PyTorch** | Native fit with CESNET libraries; standard for research. |
| F1 only | F1 **+ latency + packets/sec** | "Impact" needs throughput, not just accuracy. |

## Scope — locked

### In scope
- **Phase 0** — Data: `cesnet-datazoo` loader → bounded CESNET-QUIC22 subset → `(N, 30, 3)` tensors + labels. Verify load, inspect class balance.
- **Phase 1** — Tabular baseline: XGBoost/LightGBM on flow-level features (honest bar the deep model must clear).
- **Phase 2** — TCN encoder → embedding head + classifier. Plain supervised first.
- **Phase 3 (headline)** — Traffic-morphing augmentation pipeline (jitter, size padding, packet drops) + supervised contrastive loss → morph-invariant embeddings.
- **Phase 4** — Architecture + robustness comparison table: TCN vs LSTM vs 1D-CNN vs small Transformer, each with F1 **and** params/latency/throughput, **and** clean-vs-morphed degradation.
- **Phase 5** — Few-shot recognition of a held-out class via embedding similarity (no retraining).
- **Packaging** — CLI / Docker demo: classify flows + flag morphed ones.

### Explicitly out of scope (list as "future work" — naming these reads as mature)
- eBPF/XDP in-kernel capture (separate systems discipline; and you don't run a NN in eBPF anyway — it extracts metadata, inference is userspace).
- SSM / Mamba encoders (overkill at 30 timesteps).
- Self-supervised foundation-model pretraining + MAML meta-learning (PhD-scale compute).
- Live 10 Gbps line-rate claims (benchmark honestly on available hardware instead).

## Honest framing rules
- Report **measured** numbers, not padded ranges.
- These are **researched** areas (ET-BERT, nPrint, TCN classifiers, robust-ML). We claim "strong modern engineering + one novel-flavored robustness contribution," not "disrupting the field."
- Keep throughput claims to what we can actually demonstrate.

## Target structure (PyTorch)
```
src/
  data/
    cesnet_loader.py   # CESNET-QUIC22 subset -> (N,30,3) + labels
    augment.py         # traffic-morphing augmentations (Phase 3 core)
  models/
    tcn.py             # TCN encoder (primary)
    lstm.py            # LSTM baseline
    heads.py           # embedding + classifier heads
  losses/
    supcon.py          # supervised contrastive loss (ported from v1)
  train/
    train_supervised.py
    train_contrastive.py
  eval/
    metrics.py         # F1, latency, throughput
    robustness.py      # clean-vs-morphed degradation
    fewshot.py         # held-out-class similarity
ROADMAP.md
```
