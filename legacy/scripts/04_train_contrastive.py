import os
import sys
import json

import numpy as np
import tensorflow as tf
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from scripts.preprocess import DataLoader
from models.encoder import TrafficEncoderBiLSTM, Trainer
from models.losses import CombinedLoss
from utils.helpers import plot_training_curves, plot_confusion_matrix, save_results, print_metrics


class ContrastiveTrainer(Trainer):
    """Trainer that handles combined CE + contrastive loss"""

    @tf.function
    def train_step(self, x, y):
        with tf.GradientTape() as tape:
            logits, embeddings = self.model(x, training=True)
            loss = self.loss_fn(y, (logits, embeddings))

        gradients = tape.gradient(loss, self.model.trainable_weights)
        self.optimizer.apply_gradients(zip(gradients, self.model.trainable_weights))

        return loss

    @tf.function
    def val_step(self, x, y):
        logits, embeddings = self.model(x, training=False)
        loss = self.loss_fn(y, (logits, embeddings))
        preds = tf.argmax(logits, axis=1)
        acc = tf.reduce_mean(tf.cast(tf.equal(preds, y), tf.float32))
        return loss, acc

    def fit(self, train_dataset, val_dataset, epochs=100, patience=15):
        best_val_loss = float('inf')
        patience_counter = 0
        best_epoch = 0

        for epoch in range(epochs):
            train_losses = []
            for x_batch, y_batch in train_dataset:
                loss = self.train_step(x_batch, y_batch)
                train_losses.append(loss.numpy())

            val_loss, val_acc = self.validate(val_dataset)
            train_loss = np.mean(train_losses)

            if val_loss < best_val_loss:
                best_val_loss = val_loss
                patience_counter = 0
                best_epoch = epoch
                self.model.save_weights('models/best_model_contrastive.weights.h5')
            else:
                patience_counter += 1

            self.history['train_loss'].append(train_loss)
            self.history['val_loss'].append(val_loss)
            self.history['val_acc'].append(val_acc)

            if (epoch + 1) % 10 == 0:
                print(f"Epoch {epoch+1}/{epochs} - "
                      f"Loss: {train_loss:.4f}, Val Loss: {val_loss:.4f}, "
                      f"Val Acc: {val_acc:.4f}")

            if patience_counter >= patience:
                print(f"Early stopping at epoch {epoch+1} (best: {best_epoch+1})")
                break

        return self.history


def train_contrastive(csv_path='data/5g_traffic_classification.csv',
                      epochs=100, patience=15, batch_size=32,
                      ce_weight=1.0, con_weight=0.5, temperature=0.07):
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
    combined_loss = CombinedLoss(
        ce_weight=ce_weight,
        con_weight=con_weight,
        temperature=temperature
    )

    trainer = ContrastiveTrainer(model, optimizer, combined_loss)
    print(f"Model parameters: {model.num_parameters:,}")
    print(f"CE weight: {ce_weight}, Con weight: {con_weight}, Temperature: {temperature}")
    print("Training BiLSTM with Contrastive Learning...")
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
        'model': 'BiLSTM + Contrastive Learning',
        'accuracy': float(test_acc),
        'precision': float(precision),
        'recall': float(recall),
        'f1_score': float(f1),
        'loss': float(test_loss),
        'num_parameters': int(model.num_parameters),
        'embedding_dim': 32,
        'ce_weight': ce_weight,
        'con_weight': con_weight,
        'temperature': temperature
    }

    save_results(results, 'results/contrastive_results.json')

    try:
        plot_training_curves(
            history, 'BiLSTM Contrastive',
            'results/08_contrastive_training_curves.png'
        )
        plot_confusion_matrix(
            y_true, y_pred, label_names,
            'Confusion Matrix - BiLSTM Contrastive',
            'results/09_contrastive_confusion_matrix.png'
        )
    except Exception as e:
        print(f"Warning: Plotting failed: {e}")

    print(f"\nResults saved to results/contrastive_results.json")
    return results


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Train BiLSTM with contrastive learning')
    parser.add_argument('--csv_path', type=str,
                        default='data/5g_traffic_classification.csv',
                        help='Path to CSV dataset')
    parser.add_argument('--epochs', type=int, default=100,
                        help='Maximum epochs')
    parser.add_argument('--patience', type=int, default=15,
                        help='Early stopping patience')
    parser.add_argument('--batch_size', type=int, default=32,
                        help='Batch size')
    parser.add_argument('--ce_weight', type=float, default=1.0,
                        help='Cross-entropy loss weight')
    parser.add_argument('--con_weight', type=float, default=0.5,
                        help='Contrastive loss weight')
    parser.add_argument('--temperature', type=float, default=0.07,
                        help='Contrastive temperature')

    args = parser.parse_args()
    train_contrastive(
        args.csv_path, args.epochs, args.patience, args.batch_size,
        args.ce_weight, args.con_weight, args.temperature
    )
