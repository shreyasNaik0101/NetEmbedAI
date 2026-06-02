import json
import os
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.metrics import confusion_matrix, classification_report


def save_results(results, filepath):
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, 'w') as f:
        json.dump(results, f, indent=2)


def load_results(filepath):
    with open(filepath, 'r') as f:
        return json.load(f)


def plot_confusion_matrix(y_true, y_pred, label_names, title, save_path):
    cm = confusion_matrix(y_true, y_pred)
    plt.figure(figsize=(10, 8))
    sns.heatmap(cm, annot=True, fmt='d', cmap='Blues',
                xticklabels=label_names, yticklabels=label_names)
    plt.title(title)
    plt.ylabel('True Label')
    plt.xlabel('Predicted Label')
    plt.tight_layout()
    plt.savefig(save_path, dpi=300, bbox_inches='tight')
    plt.close()


def plot_training_curves(history, title, save_path):
    if 'train_loss' in history:
        train_loss = history['train_loss']
        val_loss = history['val_loss']
        train_acc = history.get('train_acc', None)
        val_acc = history.get('val_acc', None)
    else:
        train_loss = history['loss']
        val_loss = history['val_loss']
        train_acc = history.get('accuracy', None)
        val_acc = history.get('val_accuracy', None)

    epochs = range(1, len(train_loss) + 1)

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))

    ax1.plot(epochs, train_loss, label='Train Loss')
    ax1.plot(epochs, val_loss, label='Val Loss')
    ax1.set_xlabel('Epochs')
    ax1.set_ylabel('Loss')
    ax1.set_title(f'{title} - Loss')
    ax1.legend()
    ax1.grid(alpha=0.3)

    if val_acc is not None:
        ax2.plot(epochs, val_acc, label='Val Accuracy', color='green')
        if train_acc is not None:
            ax2.plot(epochs, train_acc, label='Train Accuracy', color='blue', alpha=0.7)
        ax2.set_xlabel('Epochs')
        ax2.set_ylabel('Accuracy')
        ax2.set_title(f'{title} - Accuracy')
        ax2.legend()
        ax2.grid(alpha=0.3)

    plt.tight_layout()
    plt.savefig(save_path, dpi=300, bbox_inches='tight')
    plt.close()


def print_metrics(y_true, y_pred, label_names):
    print(classification_report(y_true, y_pred, target_names=label_names))
