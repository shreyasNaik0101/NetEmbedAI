"""Temporal Convolutional Network (TCN) encoder for packet sequences.

Standard dilated *causal* TCN (Bai, Kolter & Koltun, 2018) over per-packet
sequences of shape (B, T=30, C=3). Causal convolutions make it valid for
streaming / early classification (no peeking at future packets) and it is
fully parallel, unlike an RNN — which is why it fits the low-latency story.

Input : (B, T, C)   -> internally transposed to (B, C, T) for conv1d
Output: (B, hidden) feature vector (last-valid-timestep summary)
"""

from __future__ import annotations

import torch
import torch.nn as nn


class _Chomp1d(nn.Module):
    """Remove the right-side padding so the convolution stays causal."""

    def __init__(self, chomp_size: int):
        super().__init__()
        self.chomp_size = chomp_size

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return x[:, :, : -self.chomp_size].contiguous() if self.chomp_size > 0 else x


class _TemporalBlock(nn.Module):
    """Two dilated causal convs + residual connection."""

    def __init__(self, in_ch: int, out_ch: int, kernel_size: int, dilation: int, dropout: float):
        super().__init__()
        pad = (kernel_size - 1) * dilation
        self.net = nn.Sequential(
            nn.Conv1d(in_ch, out_ch, kernel_size, padding=pad, dilation=dilation),
            _Chomp1d(pad),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Conv1d(out_ch, out_ch, kernel_size, padding=pad, dilation=dilation),
            _Chomp1d(pad),
            nn.ReLU(),
            nn.Dropout(dropout),
        )
        # 1x1 conv to match channels for the residual when in_ch != out_ch.
        self.downsample = nn.Conv1d(in_ch, out_ch, 1) if in_ch != out_ch else None
        self.relu = nn.ReLU()

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        out = self.net(x)
        res = x if self.downsample is None else self.downsample(x)
        return self.relu(out + res)


class TCNEncoder(nn.Module):
    """Dilated causal TCN → fixed-length feature vector.

    Args:
        in_channels: input channels per timestep (3 = IPT, DIR, SIZE).
        hidden: channel width of each temporal block.
        levels: number of temporal blocks; dilation doubles each level.
        kernel_size: conv kernel width.
        dropout: dropout inside temporal blocks.
    """

    def __init__(
        self,
        in_channels: int = 3,
        hidden: int = 64,
        levels: int = 4,
        kernel_size: int = 3,
        dropout: float = 0.2,
    ):
        super().__init__()
        blocks = []
        ch_in = in_channels
        for i in range(levels):
            blocks.append(_TemporalBlock(ch_in, hidden, kernel_size, dilation=2**i, dropout=dropout))
            ch_in = hidden
        self.network = nn.Sequential(*blocks)
        self.out_dim = hidden

    def forward(self, x: torch.Tensor, lengths: torch.Tensor) -> torch.Tensor:
        if lengths.shape != (x.shape[0],) or torch.any(lengths < 1) or torch.any(lengths > x.shape[1]):
            raise ValueError("invalid sequence lengths")
        # (B, T, C) -> (B, C, T)
        x = x.transpose(1, 2)
        y = self.network(x)  # (B, hidden, T)
        return y.gather(2, (lengths - 1)[:, None, None].expand(-1, y.shape[1], 1)).squeeze(2)


class Classifier(nn.Module):
    def __init__(self, classes, hidden=64, levels=4, embedding_dim=32):
        super().__init__()
        self.encoder = TCNEncoder(hidden=hidden, levels=levels)
        self.projection = nn.Sequential(
            nn.Linear(hidden, 64), nn.ReLU(), nn.Dropout(0.3), nn.Linear(64, embedding_dim)
        )
        self.classifier = nn.Linear(embedding_dim, classes)

    def forward(self, x, lengths):
        embedding = self.projection(self.encoder(x, lengths))
        return self.classifier(embedding), embedding


def supcon(embedding, labels, temperature=0.07):
    z = nn.functional.normalize(embedding, dim=1)
    scores = z @ z.T / temperature
    diagonal = torch.eye(len(z), dtype=torch.bool, device=z.device)
    positives = (labels[:, None] == labels[None, :]) & ~diagonal
    valid = positives.any(1)
    if not valid.any():
        return embedding.sum() * 0
    scores = scores.masked_fill(diagonal, -1e9)
    logp = scores - torch.logsumexp(scores, dim=1, keepdim=True)
    return -((logp * positives).sum(1)[valid] / positives.sum(1)[valid]).mean()
