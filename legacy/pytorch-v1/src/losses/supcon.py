"""Supervised Contrastive Loss (Khosla et al., ICML 2020).

Ported from the v1 TensorFlow implementation and corrected to the standard
"L_out" formulation from the paper (mean over positives of the log-softmax),
which is the variant the authors recommend.

Reference: https://arxiv.org/abs/2004.11362
"""
import torch
import torch.nn as nn
import torch.nn.functional as F


class SupConLoss(nn.Module):
    """Supervised contrastive loss over a batch of embeddings.

    Args:
        temperature: softmax temperature (paper default 0.07).
    """

    def __init__(self, temperature: float = 0.07):
        super().__init__()
        self.temperature = temperature

    def forward(self, embeddings: torch.Tensor, labels: torch.Tensor) -> torch.Tensor:
        """
        Args:
            embeddings: (B, D) float tensor. L2-normalized internally.
            labels:     (B,)  int tensor of class ids.
        Returns:
            scalar loss.
        """
        device = embeddings.device
        batch_size = embeddings.shape[0]

        embeddings = F.normalize(embeddings, dim=1)

        # (B, B) cosine-similarity logits scaled by temperature.
        logits = embeddings @ embeddings.t() / self.temperature

        # Numerical stability: subtract per-row max (detached).
        logits = logits - logits.max(dim=1, keepdim=True).values.detach()

        # Positive mask: same label, excluding the diagonal (self).
        labels = labels.view(-1, 1)
        pos_mask = torch.eq(labels, labels.t()).float().to(device)
        self_mask = torch.eye(batch_size, device=device)
        pos_mask = pos_mask - self_mask  # remove self-pairs

        # Denominator over all pairs except self (log-sum-exp of the row).
        exp_logits = torch.exp(logits) * (1 - self_mask)
        log_prob = logits - torch.log(exp_logits.sum(dim=1, keepdim=True) + 1e-12)

        # Mean log-prob over the positives for each anchor.
        pos_counts = pos_mask.sum(dim=1)
        # Anchors with no positive in the batch contribute 0 (avoid div-by-zero).
        valid = pos_counts > 0
        mean_log_prob_pos = (pos_mask * log_prob).sum(dim=1)[valid] / pos_counts[valid]

        if mean_log_prob_pos.numel() == 0:
            return torch.zeros([], device=device, requires_grad=True)

        return -mean_log_prob_pos.mean()
