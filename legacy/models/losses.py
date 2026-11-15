import tensorflow as tf


class SupConLoss(tf.keras.losses.Loss):
    """
    Supervised Contrastive Loss
    Paper: "Supervised Contrastive Learning" (Khosla et al., ICML 2020)
    Reference: https://arxiv.org/abs/2004.11362
    """

    def __init__(self, temperature=0.07, reduction='mean'):
        super(SupConLoss, self).__init__(reduction=reduction)
        self.temperature = temperature

    def call(self, embeddings, labels):
        embeddings = tf.math.l2_normalize(embeddings, axis=1)

        batch_size = tf.shape(embeddings)[0]

        similarity_matrix = tf.matmul(embeddings, embeddings, transpose_b=True)
        similarity_matrix = similarity_matrix / self.temperature

        labels_expanded = tf.expand_dims(labels, axis=1)
        labels_mask = tf.equal(labels_expanded, tf.expand_dims(labels, axis=0))

        mask_self = tf.eye(batch_size, dtype=tf.bool)
        labels_mask = tf.logical_and(labels_mask, ~mask_self)

        logits_max = tf.reduce_max(similarity_matrix, axis=1, keepdims=True)
        logits = similarity_matrix - logits_max

        log_neg = tf.reduce_logsumexp(logits, axis=1)

        log_pos = tf.math.log(
            tf.reduce_sum(
                tf.exp(logits) * tf.cast(labels_mask, tf.float32), axis=1
            ) + 1e-6
        )

        loss = -log_pos + log_neg

        return tf.reduce_mean(loss)


class CombinedLoss(tf.keras.losses.Loss):
    """Combined Cross-Entropy + Contrastive Loss"""

    def __init__(self, ce_weight=1.0, con_weight=0.5, temperature=0.07):
        super(CombinedLoss, self).__init__()
        self.ce_weight = ce_weight
        self.con_weight = con_weight
        self.ce_loss = tf.keras.losses.SparseCategoricalCrossentropy(from_logits=True)
        self.con_loss = SupConLoss(temperature=temperature)

    def call(self, y_true, logits_and_embeddings):
        logits, embeddings = logits_and_embeddings

        ce_loss = self.ce_loss(y_true, logits)
        con_loss = self.con_loss(embeddings, y_true)

        total_loss = self.ce_weight * ce_loss + self.con_weight * con_loss

        return total_loss
