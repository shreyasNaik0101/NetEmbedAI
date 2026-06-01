#!/bin/bash
# Full pipeline runner

set -e

echo "=========================================="
echo "  5G Traffic Classification Pipeline"
echo "  Team: Gradient_Issues"
echo "=========================================="

DATA_PATH=${1:-"data/5g_traffic_classification.csv"}

echo ""
echo "=== Phase 1: Preprocessing & EDA ==="
python scripts/01_preprocess.py --csv_path "$DATA_PATH" --eda

echo ""
echo "=== Phase 2: Baseline Models ==="
python scripts/02_baseline.py --csv_path "$DATA_PATH"

echo ""
echo "=== Phase 3: Supervised BiLSTM ==="
python scripts/03_train_bilstm.py --csv_path "$DATA_PATH"

echo ""
echo "=== Phase 4: Contrastive BiLSTM ==="
python scripts/04_train_contrastive.py --csv_path "$DATA_PATH"

echo ""
echo "=== Phase 5: Embedding Analysis ==="
python scripts/05_extract_embeddings.py --csv_path "$DATA_PATH"
python scripts/05_extract_embeddings.py --csv_path "$DATA_PATH" --compare

echo ""
echo "=========================================="
echo "  Pipeline Complete!"
echo "=========================================="
