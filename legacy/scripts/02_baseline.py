import os
import sys
import json

import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from scripts.preprocess import DataLoader
from utils.helpers import plot_confusion_matrix, save_results, print_metrics


def train_baselines(csv_path='data/5g_traffic_classification.csv'):
    print("Loading data...")
    dataloader = DataLoader(csv_path)

    X_train, y_train = dataloader.train_data
    X_val, y_val = dataloader.val_data
    X_test, y_test = dataloader.test_data

    label_names = dataloader.label_encoder.classes_

    results = {}
    os.makedirs('results', exist_ok=True)

    models = {
        'LogisticRegression': LogisticRegression(max_iter=1000, random_state=42),
        'RandomForest': RandomForestClassifier(n_estimators=100, random_state=42)
    }

    for name, model in models.items():
        print(f"\nTraining {name}...")
        model.fit(X_train, y_train)

        y_pred = model.predict(X_test)

        acc = accuracy_score(y_test, y_pred)
        prec = precision_score(y_test, y_pred, average='macro')
        rec = recall_score(y_test, y_pred, average='macro')
        f1 = f1_score(y_test, y_pred, average='macro')

        print(f"{name} - Accuracy: {acc:.4f}")
        print(f"{name} - Precision: {prec:.4f}")
        print(f"{name} - Recall: {rec:.4f}")
        print(f"{name} - F1 Score: {f1:.4f}")

        print(f"\nClassification Report for {name}:")
        print_metrics(y_test, y_pred, label_names)

        plot_confusion_matrix(
            y_test, y_pred, label_names,
            f'Confusion Matrix - {name}',
            f'results/03_confusion_matrix_{name}.png'
        )

        results[name] = {
            'accuracy': float(acc),
            'precision': float(prec),
            'recall': float(rec),
            'f1_score': float(f1)
        }

    save_results(results, 'results/baseline_results.json')
    print(f"\nResults saved to results/baseline_results.json")

    plot_comparison(results, label_names)

    return results


def plot_comparison(results, label_names):
    import matplotlib.pyplot as plt

    models = list(results.keys())
    accuracies = [results[m]['accuracy'] for m in models]
    f1_scores = [results[m]['f1_score'] for m in models]

    x = np.arange(len(models))
    width = 0.35

    fig, ax = plt.subplots(figsize=(10, 6))
    bars1 = ax.bar(x - width/2, accuracies, width, label='Accuracy', color='#4ECDC4')
    bars2 = ax.bar(x + width/2, f1_scores, width, label='F1 Score', color='#45B7D1')

    ax.set_ylabel('Score')
    ax.set_title('Baseline Model Comparison')
    ax.set_xticks(x)
    ax.set_xticklabels(models)
    ax.legend()
    ax.set_ylim([0, 1.0])

    for bars in [bars1, bars2]:
        for bar in bars:
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height,
                    f'{height:.3f}', ha='center', va='bottom', fontsize=10)

    plt.tight_layout()
    plt.savefig('results/05_baseline_comparison.png', dpi=300)
    plt.close()


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Train baseline models')
    parser.add_argument('--csv_path', type=str,
                        default='data/5g_traffic_classification.csv',
                        help='Path to CSV dataset')

    args = parser.parse_args()
    train_baselines(args.csv_path)
