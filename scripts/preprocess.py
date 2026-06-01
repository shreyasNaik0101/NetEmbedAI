import os
import sys

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder, StandardScaler
import tensorflow as tf

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))


class DataLoader:
    """
    Load and preprocess 5G traffic data

    Args:
        csv_path: Path to CSV file
        test_size: Test set proportion (15%)
        val_size: Validation set proportion (15%)
    """

    def __init__(self, csv_path, test_size=0.15, val_size=0.15):
        self.df = pd.read_csv(csv_path)

        self.feature_cols = [
            'duration', 'packets_forward', 'bytes_forward',
            'packets_backward', 'bytes_backward',
            'inter_arrival_time_mean', 'inter_arrival_time_std',
            'packet_size_min', 'packet_size_max', 'packet_size_mean',
            'rtt', 'jitter',
            'flow_iat_mean', 'flow_iat_std',
            'fwd_iat_mean', 'fwd_iat_std',
            'bwd_iat_mean', 'bwd_iat_std',
            'protocol_count', 'src_port_count', 'dst_port_count',
            'syn_flags', 'fin_flags', 'rst_flags'
        ]

        self.label_col = 'label'

        self.df = self.df.dropna(subset=self.feature_cols + [self.label_col])

        self.label_encoder = LabelEncoder()
        self.df['label_encoded'] = self.label_encoder.fit_transform(self.df[self.label_col])

        train_df, test_df = train_test_split(
            self.df, test_size=test_size,
            stratify=self.df['label_encoded'],
            random_state=42
        )

        val_size_adjusted = val_size / (1 - test_size)
        train_df, val_df = train_test_split(
            train_df, test_size=val_size_adjusted,
            stratify=train_df['label_encoded'],
            random_state=42
        )

        self.scaler = StandardScaler()
        X_train = self.scaler.fit_transform(train_df[self.feature_cols])
        X_val = self.scaler.transform(val_df[self.feature_cols])
        X_test = self.scaler.transform(test_df[self.feature_cols])

        y_train = train_df['label_encoded'].values
        y_val = val_df['label_encoded'].values
        y_test = test_df['label_encoded'].values

        self.train_data = (X_train, y_train)
        self.val_data = (X_val, y_val)
        self.test_data = (X_test, y_test)

    def get_tf_dataset(self, X, y, batch_size=32, shuffle=True):
        dataset = tf.data.Dataset.from_tensor_slices((X, y))
        if shuffle:
            dataset = dataset.shuffle(buffer_size=1000)
        dataset = dataset.batch(batch_size)
        dataset = dataset.prefetch(tf.data.AUTOTUNE)
        return dataset


def plot_eda(dataloader):
    """Generate EDA visualizations"""

    os.makedirs('results', exist_ok=True)

    plt.figure(figsize=(12, 4))

    plt.subplot(1, 2, 1)
    class_counts = dataloader.df['label'].value_counts()
    plt.bar(class_counts.index, class_counts.values)
    plt.title('Traffic Type Distribution')
    plt.xlabel('Traffic Type')
    plt.ylabel('Count')
    plt.xticks(rotation=45)

    plt.subplot(1, 2, 2)
    dataloader.df['duration'].hist(bins=50)
    plt.title('Flow Duration Distribution')
    plt.xlabel('Duration (seconds)')
    plt.ylabel('Frequency')

    plt.tight_layout()
    plt.savefig('results/01_class_distribution.png', dpi=300)
    plt.close()

    print("Feature Statistics:")
    print(dataloader.df[dataloader.feature_cols].describe())

    plt.figure(figsize=(10, 8))
    corr = dataloader.df[dataloader.feature_cols].corr()
    sns.heatmap(corr, cmap='coolwarm', center=0)
    plt.title('Feature Correlation Matrix')
    plt.savefig('results/02_feature_correlations.png', dpi=300, bbox_inches='tight')
    plt.close()


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Preprocess 5G traffic data')
    parser.add_argument('--csv_path', type=str,
                        default='data/5g_traffic_classification.csv',
                        help='Path to CSV dataset')
    parser.add_argument('--eda', action='store_true',
                        help='Generate EDA visualizations')

    args = parser.parse_args()

    print(f"Loading data from {args.csv_path}...")
    loader = DataLoader(args.csv_path)

    print(f"Dataset shape: {loader.df.shape}")
    print(f"Number of classes: {len(loader.label_encoder.classes_)}")
    print(f"Classes: {list(loader.label_encoder.classes_)}")
    print(f"Train size: {len(loader.train_data[0])}")
    print(f"Val size: {len(loader.val_data[0])}")
    print(f"Test size: {len(loader.test_data[0])}")
    print(f"Feature dimensions: {len(loader.feature_cols)}")

    if args.eda:
        print("Generating EDA visualizations...")
        plot_eda(loader)

    print("Preprocessing complete.")
