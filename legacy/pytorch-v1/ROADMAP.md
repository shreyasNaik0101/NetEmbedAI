# NetEmbedAI — Rebuild Roadmap (Strategy B)

> **Status:** rebuild complete and merged to `main`. The old TensorFlow code has
> reached retirement and now lives in [`legacy/`](legacy/README.md), which also
> records why it was replaced. Phases 0, 2, 3, 4b and 5 are done; **Phase 1
> (tabular baseline) and the Phase 4 latency/throughput numbers are still
> outstanding** — see "Known gaps" at the end of this file.

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
- **Phase 4b (done)** — Held-out attack generalization (`src/eval/heldout_attacks.py`): evaluate against attacks with *different mechanisms* than the training augmentation (size flattening, fragmentation, constant timing, dummy injection) to defeat the circularity of testing on the training attack family. Broadening the augmentation (`--broad_aug`) lifts worst-case robustness 0.18 → 0.64 (~3.5×) for a ~10-pt clean-F1 cost. Finding: robustness follows the axes you augment.
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

## Actual structure (PyTorch)
```
src/
  data/
    cesnet_loader.py   # CESNET-QUIC22 subset -> (N,30,3) + labels
    transforms.py      # log1p + per-channel standardisation (always AFTER morphing)
    augment.py         # traffic-morphing augmentations (Phase 3 core)
  models/
    tcn.py             # causal dilated TCN encoder (primary)
    lstm.py            # LSTM / BiLSTM baseline
    heads.py           # TrafficNet: encoder + embedding + classifier
  losses/
    supcon.py          # supervised contrastive loss (ported from v1, corrected to L_out)
  train/
    train.py           # one entry point: --mode {supervised,contrastive} --morph --broad_aug
  eval/
    common.py          # shared data/model loading
    compare.py         # aggregate runs -> results/comparison.md
    robustness.py      # clean-vs-morphed severity sweep
    heldout_attacks.py # Phase 4b: attacks with unseen mechanisms
    embeddings.py      # t-SNE + intra/inter-class similarity
    fewshot.py         # held-out-class prototype similarity
demo_replay.py         # live packet-by-packet terminal demo
legacy/                # the superseded v1 TensorFlow prototype
```

The two training scripts collapsed into one `train.py` (the modes differ by a
loss term and an augmentation flag, not by a pipeline), and `eval/metrics.py`
was never written — see below.

## Known gaps

Listed rather than quietly dropped, because the honest-framing rules above apply
to the roadmap too.

| Gap | Why it matters |
|---|---|
| **Phase 1 tabular baseline never run.** No XGBoost/LightGBM on v2 flow features. | This was specified as "the honest bar the deep model must clear," and it matters more here than usual: v1's defining lesson was that Random Forest *beat* the BiLSTM. Without a v2 tree baseline, "the TCN is the right tool" is unverified on this data. |
| **No measured latency / throughput.** `eval/metrics.py` was never written; results carry parameter counts only. | Low latency is the stated reason for choosing a causal TCN over an RNN. Parameter count is a proxy, not a measurement — the claim is currently architectural rather than empirical. |
| **Phase 4 encoder comparison is one row.** Only BiLSTM was run; `--encoder lstm` never was, and the 1D-CNN and Transformer comparisons do not exist. | The architecture table promises four encoders and delivers two. |
| **`morph_f1` in `results/*.json` is unseeded.** `eval/robustness.py` re-seeds so all models face identical perturbations; `train/train.py` does not. | Each model in `comparison.md` was attacked with a different random draw. The effect is small (sweep: 0.2027 vs table: 0.2061 for `tcn_supervised` at severity 1.0) but it is the headline table. |
| **Structural morphing does not recompute inter-packet times.** `drop`, `inject` and `split` shift packets without adjusting IPT, so a survivor keeps a gap measured from a packet that is no longer there; `split` gives both fragments the full original gap, lengthening the flow. | `augment.py` justifies the padding/jitter monotonicity rule on physical-realism grounds, so the structural ops are held to that standard and miss it. The held-out `fragment` and `dummy_inject` attacks inherit the same flaw, so the evaluation cannot detect it. |
| **Broad-augmentation robustness may be capacity-limited, not a trade-off.** `--broad_aug` asks the same 94k parameters to absorb six augmentations instead of three. | The reported ~10-point clean-F1 cost is currently attributed to robustness. Re-running with `hidden=128` would separate the two explanations. |
