# Design Doc: Context-Aware Flow Embeddings for Encrypted Traffic Classification

## 1. Overview / Problem Statement

**Problem:** Encrypted network traffic hides application identity from traditional DPI (deep packet inspection). Network operators cannot distinguish YouTube from Netflix, or VoIP from Gaming, using port/protocol analysis alone. ML-based classification offers a solution, but most approaches use simple feature vectors (statistical flow metrics) with shallow classifiers, missing temporal patterns in flow dynamics.

**Current pain points:**
- Port-based classification is obsolete (80%+ traffic is encrypted)
- DPI fails on encrypted payloads (TLS 1.3, QUIC)
- Existing ML approaches treat flow features as flat vectors, losing sequential structure

## 2. Motivation / Goals

**Why:** Accurate traffic classification enables QoS prioritization, bandwidth allocation, anomaly detection, and network slicing in 5G networks — without decrypting user data.

**Success metrics:**
- Classification accuracy >85% on 5G network traffic (target), achieved 78.5% on real Kaggle data, 91.5% on synthetic
- Contrastive learning outperforms standard supervised BiLSTM by ≥5%
- Embedding space shows clear class separation (validated via t-SNE)

## 3. Requirements

**Functional:**
- Accept 24 statistical flow features as input (duration, packet counts, byte volumes, IAT statistics, flags)
- Classify traffic into 6 application classes (YouTube, Netflix, Gaming, Browsing, Streaming, VoIP)
- Generate 32-dimensional flow embeddings for downstream tasks (clustering, retrieval, few-shot)
- Support batch inference on pre-recorded PCAP-derived CSVs

**Non-functional:**
- Single forward pass <10ms on CPU, <1ms on GPU
- Model size <10MB for edge deployment (actual: ~1.5M params, ~6MB)
- Training completes in under 5 minutes on T4 GPU

## 4. Constraints & Assumptions

**Constraints:**
- No GPU available on local development machines (CPU-only training is 60× slower)
- Kaggle API rate-limited; dataset download may fail — synthetic fallback required
- Windows environment; TensorFlow GPU unsupported natively after v2.11

**Assumptions:**
- 24 flow-level features are sufficient for classification (no raw packet bytes)
- Training and inference distributions match (same feature engineering pipeline)
- 100K labeled samples provide adequate coverage for 6 classes

## 5. Proposed Design

### Architecture

```
Input (24 features)
  → Reshape (24, 1)        # treat as 24-step 1D sequence
  → BiLSTM(64, return_seq) # bidirectional forward/backward
  → BiLSTM(32)             # summarize to single vector
  → Dense(64, ReLU)        # non-linear projection
  → Dropout(0.3)           # regularization
  → Dense(32)              # embedding layer (contrastive target)
  → Dense(num_classes)     # classification head
```

Two training regimes:
1. **Supervised**: Cross-entropy loss on logits
2. **Contrastive**: Combined loss = CE(logits) + SupConLoss(embeddings, labels) with temperature=0.07

### Components

| Component | File | Role |
|---|---|---|
| `TrafficEncoderBiLSTM` | `models/encoder.py` | Keras subclassed model; forward pass returns (logits, embeddings) |
| `Trainer` | `models/encoder.py` | Custom training loop with `@tf.function` train/val steps, early stopping, best-weight checkpointing |
| `ContrastiveTrainer` | inherited from `Trainer` | Overrides train/val steps to handle combined loss |
| `SupConLoss` | `models/losses.py` | Supervised contrastive loss (normalized temperature-scaled cross-entropy) |
| `CombinedLoss` | `models/losses.py` | Weighted sum of CE + SupConLoss |
| `DataLoader` | `scripts/preprocess.py` | CSV ingestion, label encoding, stratified split, StandardScaler, TF.data pipelines |
| `demo_predict.py` | root | Single/batch inference on saved weights |

### Data Flow

```
CSV → DataLoader → StandardScaler → stratified split (70/15/15)
  → TF.data pipeline (shuffle, batch 64, prefetch)
  → BiLSTM model → logits (CE loss) + embeddings (SupCon loss)
  → backprop → early stopping → save best_model_*.weights.h5
  → evaluation → classification report + t-SNE embedding visualization
```

## 6. Alternatives Considered

| Approach | Why Rejected |
|---|---|
| MLP (fully connected) | Fast on CPU but loses sequential structure; used temporarily as speed benchmark |
| 1D-CNN | Fixed receptive field; can't capture long-range temporal dependencies like BiLSTM |
| Transformer encoder | Overkill for 24-step sequence; higher parameter count, slower convergence |
| Random Forest / Logistic Regression | Strong baselines (~95% on synthetic) but no learned embeddings for downstream tasks |
| model.compile().fit() | Cannot handle dual-output (logits + embeddings) for contrastive loss; requires custom training loop |

## 7. Risks & Mitigations

| Risk | Impact | Mitigation |
|---|---|---|
| Real Kaggle dataset unavailable | Can't test on real-world data | Synthetic data generator produces realistic gamma-distributed flows as fallback |
| CPU training too slow | Blocks development | Reduced epochs (20) for local iteration; Colab T4 GPU for full 100-epoch runs |
| Contrastive training converges to degenerate solutions | Collapsed embeddings | SupConLoss with temperature scaling; L2 normalization before similarity computation |
| Feature column ordering mismatch between train/inference | Random predictions | DataLoader enforces consistent column order; scaler fitted once and exported |

## 8. Rollout Plan

**Phase 1 — Local prototyping (done):**
- Build synthetic dataset (100K rows, 6 classes)
- Implement BiLSTM + Trainer class
- Train 20 epochs on CPU, validate 91.5% accuracy
- Push to GitHub

**Phase 2 — GPU training (done):**
- Deploy Colab notebook with Kaggle dataset download + synthetic fallback
- Train 100 epochs on T4: 72.6% supervised, 78.5% contrastive
- Generate t-SNE embedding visualization

**Phase 3 — Inference & demo (done):**
- `demo_predict.py` script for single/batch classification
- Resume bullets for Amazon ML summer school application

**Backward compatibility:** N/A (greenfield project)

## 9. Testing & Validation

| Test | Method | Result |
|---|---|---|
| Classification accuracy | Hold-out test set (15%) | Supervised: 72.6%, Contrastive: 78.5% (Kaggle) |
| Baseline comparison | Logistic Regression, Random Forest | LR: 74.1%, RF: 83.2% (synthetic: ~95%) |
| Embedding quality | t-SNE visualization | Clear class clustering (contrastive > supervised) |
| Confidence calibration | Softmax probability output | Correct predictions average 85-100% confidence |

## 10. Open Questions

- Would raw packet-byte input (via 1D-CNN or Transformer) outperform flow-level statistics?
- How does the model generalize to unseen applications (zero-shot via embedding similarity)?
- Can the model be distilled to a smaller footprint for edge deployment (ONNX, TFLite)?
- Does temperature annealing in SupConLoss improve separation further?
