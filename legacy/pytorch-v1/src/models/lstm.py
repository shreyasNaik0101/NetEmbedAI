"""LSTM / BiLSTM encoder for packet sequences (baseline comparison).

Unidirectional LSTM is the streaming-valid baseline (causal); BiLSTM is offered
for the Phase-4 ablation ("BiLSTM buys +X% offline but can't stream").

Input : (B, T, C)
Output: (B, hidden * num_directions) feature vector (last hidden state).
"""
from __future__ import annotations

import torch
import torch.nn as nn


class LSTMEncoder(nn.Module):
    def __init__(self, in_channels: int = 3, hidden: int = 64, layers: int = 2,
                 bidirectional: bool = False, dropout: float = 0.2):
        super().__init__()
        self.lstm = nn.LSTM(
            input_size=in_channels,
            hidden_size=hidden,
            num_layers=layers,
            batch_first=True,
            dropout=dropout if layers > 1 else 0.0,
            bidirectional=bidirectional,
        )
        self.bidirectional = bidirectional
        self.out_dim = hidden * (2 if bidirectional else 1)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        out, _ = self.lstm(x)        # (B, T, hidden*dirs)
        return out[:, -1, :]         # last timestep
