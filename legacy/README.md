# legacy/ — the v1 TensorFlow prototype (superseded)

Nothing in this folder is part of the current project. It is kept because the
**reason** it was replaced is the most useful thing about it, and that reason is
worth being able to point at.

The current work is the PyTorch tree in [`../src/`](../src). See
[`../README.md`](../README.md) for what it does and
[`../ROADMAP.md`](../ROADMAP.md) for the design rationale.

## What v1 was

A BiLSTM over **24 aggregate flow statistics** (duration, packet counts, byte
volumes, IAT mean/std, flag counts), trained in TensorFlow on synthetic
gamma-distributed flows plus a Kaggle 5G traffic dataset. Six classes.
Best result: 91.5% on synthetic data, 78.5% on the real one.

## Why it was replaced

The statistics were reshaped to `(24, 1)` and fed to a recurrent model as if
they were a 24-step sequence. They are not a sequence — feature 7 does not come
"before" feature 8, so there is no temporal structure for a BiLSTM to read.

The evidence was in v1's own numbers: **Random Forest (83.2%) beat the BiLSTM
(78.5%)**. That is the standard signature of the wrong inductive bias on tabular
data. A model that cannot see packet order also cannot be asked the question the
current project is about — traffic morphing is invisible once packets have been
averaged into summary statistics.

v2 replaces the input with the real per-packet sequence (`(30, 3)` =
`[inter-packet time, direction, size]` for the first 30 packets), swaps the
BiLSTM for a causal TCN, and moves to real CESNET-QUIC22 QUIC traffic.

## Contents

| Path | What it is |
|---|---|
| `DESIGN_DOC.md` | The v1 design doc. Describes the v1 architecture and v1 numbers only — it does **not** describe the current project. |
| `models/` | v1 Keras encoder, SupCon loss, and trained `.weights.h5` checkpoints. |
| `scripts/` | v1 preprocessing, baselines, and training entry points. |
| `notebooks/` | v1 exploration, training, and Colab notebooks. |
| `utils/` | v1 helpers. |
| `data/` | The v1 Kaggle 5G traffic CSV. |
| `results/` | v1 metrics and plots (the numbered `01_`–`10_` figures). Note `contrastive_results.json` reports `accuracy: 1.0` — that is a v1 run on **synthetic** data and is not a claim about anything in v2. |
| `demo_predict.py` | v1 batch/single inference against the Keras weights. |
| `run_all.sh` | v1 pipeline runner. |
| `requirements-tensorflow.txt` | The v1 dependency set. Do not install alongside v2. |
