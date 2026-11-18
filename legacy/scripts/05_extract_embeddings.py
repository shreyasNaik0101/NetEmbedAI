import os
import sys
import json

import numpy as np
import matplotlib.pyplot as plt

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from scripts.preprocess import DataLoader
from models.encoder import TrafficEncoderBiLSTM
from utils.helpers import save_results


class EmbeddingAnalyzer:
    """Extract and analyze learned embeddings"""

    def __init__(self, model):
        self.model = model

    def get_embeddings(self, dataset):
        all_embeddings = []
        all_labels = []

        for x_batch, y_batch in dataset:
            _, embeddings = self.model(x_batch, training=False)
            all_embeddings.append(embeddings.numpy())
            all_labels.append(y_batch.numpy())

        embeddings = np.vstack(all_embeddings)
        labels = np.concatenate(all_labels)

        return embeddings, labels

    def plot_tsne(self, embeddings, labels, label_names, title):
        from sklearn.manifold import TSNE

        tsne = TSNE(n_components=2, perplexity=30, n_iter=1000, random_state=42)
        embeddings_2d = tsne.fit_transform(embeddings)

        plt.figure(figsize=(12, 8))
        colors = plt.cm.tab10(np.linspace(0, 1, len(label_names)))

        for i, label_name in enumerate(label_names):
            mask = labels == i
            plt.scatter(embeddings_2d[mask, 0], embeddings_2d[mask, 1],
                       c=[colors[i]], label=label_name, alpha=0.6, s=30)

        plt.xlabel('t-SNE Dimension 1')
        plt.ylabel('t-SNE Dimension 2')
        plt.title(title)
        plt.legend()
        plt.grid(alpha=0.3)
        safe_title = title.replace(' ', '_').lower()
        plt.savefig(f'results/tsne_{safe_title}.png', dpi=300, bbox_inches='tight')
        plt.close()

    def compute_similarity(self, embeddings, labels):
        embeddings = embeddings / np.linalg.norm(embeddings, axis=1, keepdims=True)

        similarity = embeddings @ embeddings.T

        intra_class_sims = []
        inter_class_sims = []

        for i in range(embeddings.shape[0]):
            same_class = labels == labels[i]
            same_class[i] = False

            if np.sum(same_class) > 0:
                intra_class_sims.append(np.mean(similarity[i, same_class]))

            diff_class = labels != labels[i]
            if np.sum(diff_class) > 0:
                inter_class_sims.append(np.mean(similarity[i, diff_class]))

        return {
            'intra_class_sim': float(np.mean(intra_class_sims)),
            'inter_class_sim': float(np.mean(inter_class_sims)),
            'intra_class_std': float(np.std(intra_class_sims)),
            'inter_class_std': float(np.std(inter_class_sims))
        }


def load_model_and_analyze(csv_path='data/5g_traffic_classification.csv',
                           weights_path='models/best_model_contrastive.weights.h5'):
    print("Loading data...")
    dataloader = DataLoader(csv_path)
    test_ds = dataloader.get_tf_dataset(*dataloader.test_data, shuffle=False)

    num_classes = len(dataloader.label_encoder.classes_)
    label_names = dataloader.label_encoder.classes_

    print(f"Loading model weights from {weights_path}...")
    model = TrafficEncoderBiLSTM(num_classes=num_classes, embedding_dim=32)
    model.load_weights(weights_path)

    analyzer = EmbeddingAnalyzer(model)

    print("Extracting embeddings...")
    embeddings, labels = analyzer.get_embeddings(test_ds)
    print(f"Embeddings shape: {embeddings.shape}")
    print(f"Labels shape: {labels.shape}")

    print("Computing t-SNE visualization...")
    analyzer.plot_tsne(embeddings, labels, label_names,
                       "Contrastive Embeddings (t-SNE)")

    print("Computing similarity metrics...")
    sim_metrics = analyzer.compute_similarity(embeddings, labels)

    print(f"\nSimilarity Metrics:")
    print(f"  Intra-class similarity: {sim_metrics['intra_class_sim']:.4f} "
          f"± {sim_metrics['intra_class_std']:.4f}")
    print(f"  Inter-class similarity: {sim_metrics['inter_class_sim']:.4f} "
          f"± {sim_metrics['inter_class_std']:.4f}")

    save_results(sim_metrics, 'results/embedding_metrics.json')
    print("\nEmbedding metrics saved to results/embedding_metrics.json")

    return sim_metrics


def final_comparison():
    """Compare all model results and generate final visualization"""
    import matplotlib.pyplot as plt

    results = {}

    base_dir = 'results'
    result_files = {
        'baseline_results.json': 'baseline',
        'bilstm_results.json': 'bilstm',
        'contrastive_results.json': 'contrastive'
    }

    for fname, key in result_files.items():
        fpath = os.path.join(base_dir, fname)
        if os.path.exists(fpath):
            with open(fpath) as f:
                data = json.load(f)
            results[key] = data

    models = []
    accuracies = []

    if 'baseline' in results:
        baseline = results['baseline']
        if 'LogisticRegression' in baseline:
            models.append('Logistic Regression')
            accuracies.append(baseline['LogisticRegression']['accuracy'])
        if 'RandomForest' in baseline:
            models.append('Random Forest')
            accuracies.append(baseline['RandomForest']['accuracy'])

    if 'bilstm' in results:
        models.append('BiLSTM (Supervised)')
        accuracies.append(results['bilstm'].get('accuracy', 0))

    if 'contrastive' in results:
        models.append('BiLSTM (Contrastive)')
        accuracies.append(results['contrastive'].get('accuracy', 0))

    if not models:
        print("No results found to compare.")
        return

    plt.figure(figsize=(10, 6))
    colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#FFA07A']
    bars = plt.bar(models, accuracies, color=colors[:len(models)])

    for bar in bars:
        height = bar.get_height()
        plt.text(bar.get_x() + bar.get_width()/2., height,
                f'{height:.3f}',
                ha='center', va='bottom', fontsize=12, fontweight='bold')

    plt.ylabel('Accuracy', fontsize=12)
    plt.title('Model Comparison: Traffic Classification', fontsize=14, fontweight='bold')
    plt.ylim([0.7, 1.0])
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()
    plt.savefig('results/10_final_comparison.png', dpi=300)
    plt.close()
    print("Final comparison saved to results/10_final_comparison.png")


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Extract and analyze embeddings')
    parser.add_argument('--csv_path', type=str,
                        default='data/5g_traffic_classification.csv',
                        help='Path to CSV dataset')
    parser.add_argument('--weights', type=str,
                        default='models/best_model_contrastive.weights.h5',
                        help='Path to model weights')
    parser.add_argument('--compare', action='store_true',
                        help='Run final model comparison')

    args = parser.parse_args()

    if args.compare:
        final_comparison()
    else:
        load_model_and_analyze(args.csv_path, args.weights)
