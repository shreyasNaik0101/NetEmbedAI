#!/usr/bin/env python3
"""Quick demo: classify a single network flow or batch from CSV."""
import sys, os, json, numpy as np, tensorflow as tf, pandas as pd
sys.path.append(os.path.dirname(__file__))
from scripts.preprocess import DataLoader
from models.encoder import TrafficEncoderBiLSTM

MODEL_PATH = 'models/best_model_supervised.weights.h5'  # trained locally with 91.5% on synthetic data
# MODEL_PATH = 'models/best_model_contrastive.weights.h5'  # Colab-trained on Kaggle data (78%)
CSV_PATH = 'data/5g_traffic_classification.csv'

# --- Batch demo: sample a few test rows and show predictions ---
print("Loading model + data...")
dl = DataLoader(CSV_PATH)
num_classes = len(dl.label_encoder.classes_)
class_names = dl.label_encoder.classes_

model = TrafficEncoderBiLSTM(num_classes=num_classes, embedding_dim=32)
# Pass dummy data to build all layer variables (required for subclassed models)
dummy = tf.zeros((1, 24))
model(dummy, training=False)
model.load_weights(MODEL_PATH)

# Pick 10 random test samples
X_test, y_test = dl.test_data
idxs = np.random.choice(len(X_test), 10, replace=False)
samples, true_labels = X_test[idxs], y_test[idxs]

logits, embeddings = model(samples, training=False)
preds = tf.argmax(logits, axis=1).numpy()

print(f"\n{'True':12s} {'Predicted':12s} {'Confidence':12s}")
print('-' * 36)
for i in range(10):
    conf = float(tf.nn.softmax(logits[i])[preds[i]])
    print(f'{class_names[true_labels[i]]:12s} {class_names[preds[i]]:12s} {conf:.4f}')

# --- Single flow demo: classify one custom input ---
print("\n--- Single flow prediction ---")
example_flow = np.array([[
    25.0,  # duration
    45,    # packets_forward
    8500,  # bytes_forward
    20,    # packets_backward
    3200,  # bytes_backward
    0.03,  # inter_arrival_time_mean
    0.015, # inter_arrival_time_std
    200,   # packet_size_min
    1200,  # packet_size_max
    650,   # packet_size_mean
    15.0,  # rtt
    2.5,   # jitter
    0.04,  # flow_iat_mean
    0.02,  # flow_iat_std
    0.035, # fwd_iat_mean
    0.018, # fwd_iat_std
    0.033, # bwd_iat_mean
    0.016, # bwd_iat_std
    2,     # protocol_count
    3,     # src_port_count
    2,     # dst_port_count
    3,     # syn_flags
    1,     # fin_flags
    0      # rst_flags
]])

scaled = dl.scaler.transform(example_flow)
l, e = model(scaled, training=False)
pred_class = class_names[tf.argmax(l, axis=1).numpy()[0]]
conf = float(tf.nn.softmax(l)[0][tf.argmax(l, axis=1)[0]])

print(f'Predicted: {pred_class} (confidence: {conf:.2%})')
print("\nTo customize input, edit 'example_flow' in this script.")
