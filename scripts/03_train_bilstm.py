import os
import sys
import json

import numpy as np
import tensorflow as tf
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from scripts.preprocess import DataLoader
from models.encoder import TrafficEncoderBiLSTM, Trainer
from utils.helpers import plot_training_curves, plot_confusion_matrix, save_results, print_metrics


def train_supervised(csv_path='data/5g_traffic_classification.csv', epochs=100, patience=15, batch_size=32):
    print("Loading data...")
    dataloader = DataLoader(csv_path)

    train_ds = dataloader.get_tf_dataset(*dataloader.train_data, shuffle=True, batch_size=batch_size)
    val_ds = dataloader.get_tf_dataset(*dataloader.val_data, shuffle=False, batch_size=batch_size)
    test_ds = dataloader.get_tf_dataset(*dataloader.test_data, shuffle=False, batch_size=batch_size)

    num_classes = len(dataloader.label_encoder.classes_)
    label_names = dataloader.label_encoder.classes_

    print(f"Number of classes: {num_classes}")
    print(f"Classes: {list(label_names)}")

    model = TrafficEncoderBiLSTM(num_classes=num_classes, embedding_dim=32)

    optimizer = tf.keras.optimizers.Adam(learning_rate=0.001)
    loss_fn = tf.keras.losses.SparseCategoricalCrossentropy(from_logits=True)

    trainer = Trainer(model, optimizer, loss_fn)
    print(f"Model parameters: {model.num_parameters:,}")
    print(f"Training BiLSTM (supervised)...")
    history = trainer.fit(train_ds, val_ds, epochs=epochs, patience=patience)

    print("\nEvaluating on test set...")
    test_loss, test_acc = trainer.validate(test_ds)
    print(f"Test Loss: {test_loss:.4f}")
    print(f"Test Accuracy: {test_acc:.4f}")

    y_pred = []
    y_true = []
    for x_batch, y_batch in test_ds:
        logits, _ = model(x_batch, training=False)
        preds = tf.argmax(logits, axis=1).numpy()
        y_pred.extend(preds)
        y_true.extend(y_batch.numpy())

    y_pred = np.array(y_pred)
    y_true = np.array(y_true)

    precision = precision_score(y_true, y_pred, average='macro')
    recall = recall_score(y_true, y_pred, average='macro')
    f1 = f1_score(y_true, y_pred, average='macro')

    print(f"\nTest Metrics:")
    print(f"Accuracy:  {test_acc:.4f}")
    print(f"Precision: {precision:.4f}")
    print(f"Recall:    {recall:.4f}")
    print(f"F1 Score:  {f1:.4f}")

    print("\nClassification Report:")
    print_metrics(y_true, y_pred, label_names)

    os.makedirs('results', exist_ok=True)

    results = {
        'model': 'BiLSTM (Supervised)',
        'accuracy': float(test_acc),
        'precision': float(precision),
        'recall': float(recall),
        'f1_score': float(f1),
        'loss': float(test_loss),
        'num_parameters': int(model.num_parameters),
        'embedding_dim': 32
    }

    save_results(results, 'results/bilstm_results.json')

    try:
        plot_training_curves(
            history, 'BiLSTM Supervised',
            'results/06_bilstm_training_curves.png'
        )
        plot_confusion_matrix(
            y_true, y_pred, label_names,
            'Confusion Matrix - BiLSTM Supervised',
            'results/07_bilstm_confusion_matrix.png'
        )
    except Exception as e:
        print(f"Warning: Plotting failed: {e}")

    print(f"\nResults saved to results/bilstm_results.json")
    return results


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Train supervised BiLSTM')
    parser.add_argument('--csv_path', type=str,
                        default='data/5g_traffic_classification.csv',
                        help='Path to CSV dataset')
    parser.add_argument('--epochs', type=int, default=100,
                        help='Maximum epochs')
    parser.add_argument('--patience', type=int, default=15,
                        help='Early stopping patience')
    parser.add_argument('--batch_size', type=int, default=32,
                        help='Batch size')

    args = parser.parse_args()
    train_supervised(args.csv_path, args.epochs, args.patience, args.batch_size)
