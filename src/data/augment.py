"""Traffic-morphing augmentations — the core of Strategy B.

Simulates the three cheap real-world evasions an adversary uses to defeat a
statistical traffic classifier, operating on packet-sequence tensors of shape
(B, T=30, C=3) with channels [IPT, DIR, SIZE]:

  1. Jitter  — random timing delays added to inter-packet times (IPT).
  2. Padding — junk bytes added to packet sizes (SIZE), capped at the MTU.
  3. Drops   — packets removed from the flow; survivors shift left, tail is
               zero-padded (mirrors a real dropped/aggregated packet).

Two uses:
  * Training-time augmentation → the model learns morph-invariant embeddings,
    so a morphed flow still clusters with its true class (robustness).
  * Test-time attack simulation → measure clean-vs-morphed degradation and
    show the robust model degrades far less than the baseline (Phase 4).

Padding and jitter only ever *increase* size / time (you cannot un-send bytes
or make packets arrive earlier), which keeps the perturbation physically
realistic. Zero-padded (absent) timesteps are never morphed.
"""
from __future__ import annotations

import torch

# Channel indices within the (T, 3) layout produced by the loader.
IPT, DIR, SIZE = 0, 1, 2
DEFAULT_MTU = 1500.0  # bytes; size padding is capped here


def _packet_mask(x: torch.Tensor) -> torch.Tensor:
    """(B, T) bool mask of real (non-padding) packets. A padded slot is all-zero."""
    return x[:, :, SIZE] != 0


class MorphAugmenter:
    """Apply traffic-morphing perturbations to packet-sequence batches.

    Args:
        jitter_std:   std (in IPT units) of the half-normal timing delay.
        max_pad:      max bytes of junk padding added to a packet's size.
        drop_prob:    per-packet probability of being dropped.
        mtu:          size cap after padding.
        p:            probability of applying *each* perturbation to a sample
                      (used during training so the model also sees clean flows).
    """

    def __init__(self, jitter_std: float = 5.0, max_pad: float = 300.0,
                 drop_prob: float = 0.15, mtu: float = DEFAULT_MTU, p: float = 0.5):
        self.jitter_std = jitter_std
        self.max_pad = max_pad
        self.drop_prob = drop_prob
        self.mtu = mtu
        self.p = p

    # --- individual perturbations (also used standalone in the robustness sweep) ---

    def jitter(self, x: torch.Tensor, severity: float = 1.0) -> torch.Tensor:
        x = x.clone()
        mask = _packet_mask(x)
        delay = torch.randn_like(x[:, :, IPT]).abs() * (self.jitter_std * severity)
        x[:, :, IPT] = x[:, :, IPT] + delay * mask
        return x

    def pad(self, x: torch.Tensor, severity: float = 1.0) -> torch.Tensor:
        x = x.clone()
        mask = _packet_mask(x)
        add = torch.rand_like(x[:, :, SIZE]) * (self.max_pad * severity)
        sizes = x[:, :, SIZE] + add * mask
        x[:, :, SIZE] = torch.clamp(sizes, max=self.mtu) * mask  # keep padding slots at 0
        return x

    def drop(self, x: torch.Tensor, severity: float = 1.0) -> torch.Tensor:
        """Drop packets and left-shift survivors, zero-padding the tail."""
        B, T, C = x.shape
        out = torch.zeros_like(x)
        real = _packet_mask(x)
        keep_prob = 1.0 - min(self.drop_prob * severity, 0.95)
        keep = (torch.rand(B, T, device=x.device) < keep_prob) & real
        for b in range(B):
            kept = x[b, keep[b]]
            n = kept.shape[0]
            if n > 0:
                out[b, :n] = kept
        return out

    # --- combined morph (training augmentation / full attack) ---

    def morph(self, x: torch.Tensor, severity: float = 1.0, training: bool = True) -> torch.Tensor:
        """Apply the three perturbations. During training each is applied with
        probability ``self.p`` per batch; at test time (training=False) all are
        applied to simulate a full attack."""
        if training:
            if torch.rand(1).item() < self.p:
                x = self.jitter(x, severity)
            if torch.rand(1).item() < self.p:
                x = self.pad(x, severity)
            if torch.rand(1).item() < self.p:
                x = self.drop(x, severity)
        else:
            x = self.drop(self.pad(self.jitter(x, severity), severity), severity)
        return x
