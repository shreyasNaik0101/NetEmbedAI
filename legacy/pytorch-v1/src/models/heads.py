"""TrafficNet: encoder + embedding head + classification head.

forward() returns (logits, embeddings) — the dual output needed for combined
cross-entropy + supervised-contrastive training. The embedding is the vector
used for contrastive loss, t-SNE, and few-shot similarity.
"""
from __future__ import annotations

import torch
import torch.nn as nn


class TrafficNet(nn.Module):
    def __init__(self, encoder: nn.Module, num_classes: int,
                 embedding_dim: int = 32, proj_hidden: int = 64, dropout: float = 0.3):
        super().__init__()
        self.encoder = encoder
        self.projection = nn.Sequential(
            nn.Linear(encoder.out_dim, proj_hidden),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(proj_hidden, embedding_dim),
        )
        self.classifier = nn.Linear(embedding_dim, num_classes)
        self.embedding_dim = embedding_dim

    def forward(self, x: torch.Tensor):
        feats = self.encoder(x)              # (B, encoder.out_dim)
        embeddings = self.projection(feats)  # (B, embedding_dim)
        logits = self.classifier(embeddings)  # (B, num_classes)
        return logits, embeddings

    @torch.no_grad()
    def embed(self, x: torch.Tensor) -> torch.Tensor:
        return self.projection(self.encoder(x))

    @property
    def num_parameters(self) -> int:
        return sum(p.numel() for p in self.parameters() if p.requires_grad)
