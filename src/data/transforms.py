"""Per-channel normalization for packet sequences.

Channels [IPT, DIR, SIZE] live on very different scales (ms, ±1, bytes) and
IPT/SIZE are heavy-tailed, so we log1p the positive channels then standardize
per channel using stats from *real* (non-padding) packets in the training set.

Ordering matters: morphing augments raw units (delay in ms, padding in bytes),
so normalization is always the LAST step, applied after any augmentation.
Padding slots are re-zeroed after standardization so "absent packet" stays the
zero vector.
"""
from __future__ import annotations

import torch

IPT, DIR, SIZE = 0, 1, 2


def _log_pos(x: torch.Tensor) -> torch.Tensor:
    """log1p the IPT and SIZE channels (non-negative); leave DIR untouched."""
    x = x.clone()
    x[:, :, IPT] = torch.log1p(x[:, :, IPT].clamp(min=0))
    x[:, :, SIZE] = torch.log1p(x[:, :, SIZE].clamp(min=0))
    return x


def fit_channel_stats(X: torch.Tensor):
    """Compute per-channel (mean, std) over real packets after log-transform.

    Args:
        X: (N, T, 3) raw training sequences.
    Returns:
        (mean, std): each (3,) tensors.
    """
    xl = _log_pos(X)
    mask = (X[:, :, SIZE] != 0).unsqueeze(-1)          # (N, T, 1) real-packet mask
    flat = xl[mask.expand_as(xl)].reshape(-1, 3)        # (num_real_packets, 3)
    mean = flat.mean(dim=0)
    std = flat.std(dim=0).clamp(min=1e-6)
    return mean, std


class Normalizer:
    """Standardize sequences and re-zero padding. Callable on (B, T, 3)."""

    def __init__(self, mean: torch.Tensor, std: torch.Tensor):
        self.mean = mean
        self.std = std

    def to(self, device):
        self.mean = self.mean.to(device)
        self.std = self.std.to(device)
        return self

    def __call__(self, x: torch.Tensor) -> torch.Tensor:
        mask = (x[:, :, SIZE] != 0).unsqueeze(-1)       # real packets before transform
        xl = _log_pos(x)
        xn = (xl - self.mean) / self.std
        return xn * mask                                 # padding slots back to 0
