# Context-Aware Flow Embeddings for Adaptive AI-based Network Traffic Classification

**Team:** Gradient_Issues

## Project Overview

This project implements a BiLSTM + Contrastive Learning model for encrypted network traffic classification. The system learns rich 32-dimensional flow embeddings that capture semantic similarities between traffic flows, improving classification accuracy over traditional baselines.

### Key Features
- **BiLSTM Encoder**: Bidirectional LSTM with 24-dimensional flow features
- **Contrastive Learning**: Supervised contrastive loss to learn discriminative embeddings
- **Embedding Analysis**: t-SNE visualization and similarity metrics
- **Baseline Models**: Logistic Regression & Random Forest for comparison

## Architecture

```
Input (24 features) → Reshape (24, 1) → BiLSTM(64) → BiLSTM(32) → Dense(64) → Embedding(32) → Classification Head
```

## Setup

### Local (CPU)
```bash
# Create virtual environment
python3 -m venv traffic_classification_env
source traffic_classification_env/bin/activate

# Install dependencies
pip install -r requirements.txt

# Download dataset from Kaggle:
# https://www.kaggle.com/datasets/kimdaegyeom/5g-traffic-datasets
# Place in: data/5g_traffic_classification.csv
```

### Colab (GPU - Recommended for BiLSTM)
[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/YOUR_USERNAME/traffic-classification-bilstm/blob/main/notebooks/colab_training.ipynb)

1. Click the badge above or upload `notebooks/colab_training.ipynb` to Colab
2. Set Runtime → Change runtime type → **T4 GPU**
3. Run all cells (training takes ~2-3 minutes)

## Usage

### Preprocessing & EDA
```bash
python scripts/01_preprocess.py --csv_path data/5g_traffic_classification.csv --eda
```

### Train Baseline Models
```bash
python scripts/02_baseline.py --csv_path data/5g_traffic_classification.csv
```

### Train Supervised BiLSTM
```bash
python scripts/03_train_bilstm.py --csv_path data/5g_traffic_classification.csv
```

### Train Contrastive BiLSTM
```bash
python scripts/04_train_contrastive.py --csv_path data/5g_traffic_classification.csv
```

### Extract & Visualize Embeddings
```bash
python scripts/05_extract_embeddings.py --csv_path data/5g_traffic_classification.csv
```

## Project Structure

```
traffic_classification/
├── data/                        # Dataset files
├── models/                      # Model architectures
│   ├── encoder.py               # BiLSTM encoder
│   └── losses.py                # Contrastive loss functions
├── scripts/                     # Training & analysis scripts
├── notebooks/                   # Jupyter notebooks
├── results/                     # Results & visualizations
└── utils/                       # Utility functions
```

## Results

| Model | Accuracy | Precision | Recall | F1 Score |
|-------|----------|-----------|--------|----------|
| Logistic Regression | ~82-85% | ~82-85% | ~82-85% | ~82-85% |
| Random Forest | ~87-90% | ~87-90% | ~87-90% | ~87-90% |
| BiLSTM (Supervised) | ~92-93% | ~92-93% | ~92-93% | ~92-93% |
| BiLSTM + Contrastive | ~93-95% | ~93-95% | ~93-95% | ~93-95% |

## License

MIT
