# NetEmbedAI — Adversarially-Robust Encrypted Traffic Classification

Classifies encrypted (QUIC) network traffic from **per-packet sequences**, and
learns embeddings that stay **robust to adversarial traffic morphing** — the
evasion technique (jitter, padding, packet drops) that defeats most statistical
traffic classifiers.

> **One line:** a standard classifier loses ~70 macro-F1 points under adversarial
> traffic morphing; morph-augmented contrastive training cuts that loss to ~12.

This is a ground-up rebuild (PyTorch). The original TensorFlow prototype — which
treated 24 aggregate flow *statistics* as a fake sequence — is archived under
`models/`, `scripts/`, `utils/` for reference. See [ROADMAP.md](ROADMAP.md) for
the full v1→v2 rationale.

## Why the rebuild

The v1 model fed 24 aggregate flow statistics into a BiLSTM by pretending they
were a 24-step sequence — but summary statistics have no temporal order, so a
Random Forest beat the BiLSTM on real data (the classic "wrong inductive bias
for tabular data" tell). v2 fixes the input: it uses the **first 30 packets** of
each flow as a genuine sequence of `[inter-packet-time, direction, size]`, which
is real temporal structure that a causal TCN can actually exploit.

## Approach

```
first 30 packets  ->  (30, 3) sequence [IPT, DIR, SIZE]
                       -> causal TCN encoder
                       -> 32-d embedding  --(SupCon loss)-->  morph-invariant space
                       -> linear classifier
```

- **Causal TCN** encoder — parallel, low-latency, streaming-valid (no peeking at
  future packets); beats a BiLSTM at 65% of the parameters.
- **Supervised contrastive loss** on the embedding, so same-class flows cluster.
- **Traffic-morphing augmentation** (jitter / padding / drops) during training →
  the embedding learns to be invariant to morphing, so a morphed flow still
  lands with its true class.

Data: [CESNET-QUIC22](https://zenodo.org/records/10728760) via `cesnet-datazoo`,
a curated 10-app subset spanning streaming / social / messaging / cloud.

## Results (real CESNET-QUIC22, 10 classes)

| Model | Params | Clean F1 | Morphed F1 | Robustness gap |
|---|---|---|---|---|
| TCN supervised | 94k | 0.907 | 0.206 | −0.70 |
| TCN contrastive | 94k | 0.910 | 0.268 | −0.64 |
| BiLSTM supervised | 145k | 0.898 | 0.183 | −0.72 |
| **TCN contrastive + morph** | 94k | 0.880 | **0.764** | **−0.12** |

**Robustness across attack severity** (macro-F1; `results/robustness_sweep.png`):

| Severity | 0 (clean) | 0.5 | 1.0 | 2.0 | 3.0 |
|---|---|---|---|---|---|
| TCN supervised | 0.907 | 0.494 | 0.203 | 0.117 | 0.089 |
| **TCN + morph** | 0.880 | **0.830** | **0.771** | **0.498** | **0.252** |

The robust model dominates at every attack level and still holds at severity
2–3× beyond its training intensity (generalization, not memorization).

**Generalization to unseen attacks** (macro-F1 vs four attacks with *different
mechanisms* than the training augmentation — `size_normalize`, `fragment`,
`constant_timing`, `dummy_inject`). "Worst case" = the attacker's best choice
(minimum over attacks), the security-relevant metric:

| Model | clean | size_norm | fragment | const_timing | dummy_inj | **worst case** |
|---|---|---|---|---|---|---|
| TCN supervised | 0.906 | 0.185 | 0.577 | 0.182 | 0.462 | 0.182 |
| TCN + morph (timing/count) | 0.879 | 0.182 | 0.403 | 0.800 | 0.492 | 0.182 |
| **TCN + broad morph** | 0.809 | **0.706** | **0.775** | 0.638 | **0.663** | **0.638** |

This addresses the circularity of testing on the training attack family. Two
findings: (1) robustness **generalizes to unseen attacks on axes covered in
training** (the narrow morph model, trained only on timing/count jitter, hits
0.80 on the never-seen `constant_timing` attack); (2) it **fails on axes not
covered** (size flattening, fragmentation) — until those axes are added to
training. Broadening the augmentation lifts **worst-case** robustness from 0.18
to **0.64 (~3.5×)**, for a ~10-point clean-F1 cost. Robustness follows the axes
you augment — a controllable, characterized property, not a circular claim.

**Embedding separation, clean vs under attack:**

| Model | Clean sep. | Under attack | Retained |
|---|---|---|---|
| TCN supervised | 0.805 | 0.080 | 10% (brittle) |
| TCN contrastive + morph | 0.374 | 0.297 | **79% (durable)** |

The supervised model's crisp clean separation is fragile — it evaporates under
morphing. The morph model separates less on clean data but keeps 79% under
attack (and separates *better* than the baseline once attacked).

*Honest note:* robustness costs ~3 clean-F1 points (0.907 → 0.880) for ~4×
better robustness. Reported numbers are measured, not idealized.

**Few-shot via embedding prototypes** (train with one class held out, then
classify from K labeled examples, no retraining):

- **Known classes: strong** — 0.79 overall accuracy, per-class recall 0.83–0.99.
  The embedding is high-quality for metric-based classification.
- **Novel (never-trained) class: limited** — holding out YouTube, it is
  recognized at only ~0.27 recall (vs 0.10 random). The embedding is tuned to
  its training classes, not a foundation model.

This is a deliberately honest negative result: metric-based few-shot works well
*within* the trained label set, but true zero-shot generalization to an unseen
app is a real limitation — and the motivation for the self-supervised
pretraining direction listed as future work in [ROADMAP.md](ROADMAP.md).

## Reproduce

```bash
pip install torch cesnet-datazoo scikit-learn matplotlib

# 1. Download + build the curated packet-sequence subset (~2.7 GB one-time)
python -m src.data.cesnet_loader

# 2. Train (each auto-reports clean vs morphed F1)
python -m src.train.train --mode supervised  --encoder tcn
python -m src.train.train --mode contrastive --morph --encoder tcn                  # robust (timing/count)
python -m src.train.train --mode contrastive --morph --broad_aug --encoder tcn \
    --tag tcn_contrastive_broadmorph                                                # robust (all axes)

# 3. Evaluate
python -m src.eval.compare                                   # comparison table
python -m src.eval.robustness --tags tcn_supervised tcn_contrastive_morph
python -m src.eval.embeddings --tag tcn_contrastive_morph    # t-SNE + similarity
python -m src.eval.heldout_attacks                           # unseen-attack generalization
```

## Layout

```
src/
  data/    cesnet_loader.py  augment.py (morphing + broad ops)  transforms.py
  models/  tcn.py  lstm.py  heads.py
  losses/  supcon.py
  train/   train.py          # supervised / contrastive / morph / broad / hold-out
  eval/    compare.py  robustness.py  embeddings.py  fewshot.py  heldout_attacks.py
```
