import numpy as np
import tensorflow as tf


class TrafficEncoderBiLSTM(tf.keras.Model):
    """
    BiLSTM-based traffic encoder with embedding layer

    Architecture:
      Input (24) → Reshape (24, 1) → BiLSTM(64) → BiLSTM(32)
      → Dense(64) → Embedding(32) → Classification Head(num_classes)
    """

    def __init__(self, num_classes=5, embedding_dim=32):
        super(TrafficEncoderBiLSTM, self).__init__()

        self.bilstm_1 = tf.keras.layers.Bidirectional(
            tf.keras.layers.LSTM(64, return_sequences=True, dropout=0.3)
        )

        self.bilstm_2 = tf.keras.layers.Bidirectional(
            tf.keras.layers.LSTM(32, return_sequences=False, dropout=0.3)
        )

        self.dense_1 = tf.keras.layers.Dense(64, activation='relu')
        self.dropout_1 = tf.keras.layers.Dropout(0.3)

        self.embedding_layer = tf.keras.layers.Dense(
            embedding_dim,
            activation=None,
            name='embedding'
        )

        self.classifier = tf.keras.layers.Dense(
            num_classes,
            activation=None,
            name='classifier'
        )

        self.num_classes = num_classes
        self.embedding_dim = embedding_dim

    def call(self, inputs, training=False):
        x = tf.expand_dims(inputs, axis=-1)

        x = self.bilstm_1(x, training=training)
        x = self.bilstm_2(x, training=training)

        x = self.dense_1(x, training=training)
        x = self.dropout_1(x, training=training)

        embeddings = self.embedding_layer(x)
        logits = self.classifier(embeddings)

        return logits, embeddings

    def get_embedding(self, inputs, training=False):
        x = tf.expand_dims(inputs, axis=-1)
        x = self.bilstm_1(x, training=training)
        x = self.bilstm_2(x, training=training)
        x = self.dense_1(x, training=training)
        x = self.dropout_1(x, training=training)
        embeddings = self.embedding_layer(x)
        return embeddings

    @property
    def num_parameters(self):
        return sum([tf.size(w).numpy() for w in self.trainable_weights])


class Trainer:
    """Training loop with @tf.function for graph-mode speed"""

    def __init__(self, model, optimizer, loss_fn, metrics=None):
        self.model = model
        self.optimizer = optimizer
        self.loss_fn = loss_fn
        self.metrics = metrics or {}
        self.history = {
            'train_loss': [], 'val_loss': [],
            'train_acc': [], 'val_acc': []
        }

    @tf.function
    def train_step(self, x, y):
        with tf.GradientTape() as tape:
            logits, _ = self.model(x, training=True)
            loss = self.loss_fn(y, logits)

        gradients = tape.gradient(loss, self.model.trainable_weights)
        self.optimizer.apply_gradients(zip(gradients, self.model.trainable_weights))

        return loss

    @tf.function
    def val_step(self, x, y):
        logits, _ = self.model(x, training=False)
        loss = self.loss_fn(y, logits)
        preds = tf.argmax(logits, axis=1)
        acc = tf.reduce_mean(tf.cast(tf.equal(preds, y), tf.float32))
        return loss, acc

    def validate(self, val_dataset):
        val_losses = []
        val_accs = []

        for x_batch, y_batch in val_dataset:
            loss, acc = self.val_step(x_batch, y_batch)
            val_losses.append(loss.numpy())
            val_accs.append(acc.numpy())

        return np.mean(val_losses), np.mean(val_accs)

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
                self.model.save_weights('models/best_model_supervised.weights.h5')
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
