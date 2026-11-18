"""Deterministic raw-unit perturbations; padding is abstract feature corruption."""

import hashlib
import numpy as np
from .contract import validate_array


def perturb(raw, kind, strength, seed=17, sample_id=""):
    x = validate_array(raw).copy()
    if not np.isfinite(strength) or strength < 0:
        raise ValueError("strength must be finite and nonnegative")
    if kind not in ("timing", "padding", "observation_loss"):
        raise ValueError("unknown stress family")
    if strength == 0:
        return x, {
            "kind": kind,
            "strength": strength,
            "seed": seed,
            "removed": 0,
            "first_observation_offset_ms": 0.0,
            "byte_delta": 0.0,
            "duration_delta_ms": 0.0,
        }
    key = hashlib.sha256(f"{seed}:{sample_id}:{kind}".encode()).digest()
    rng = np.random.default_rng(int.from_bytes(key[:8], "big"))
    before_bytes, before_duration = float(x[:, 2].sum()), float(x[:, 0].sum())
    removed, offset = 0, 0.0
    if kind == "timing":
        # Cumulative nonnegative extra delay; derive IPT from absolute times.
        times = np.cumsum(x[:, 0]) + np.cumsum(rng.uniform(0, strength, len(x)))
        times -= times[0]
        x[:, 0] = np.diff(times, prepend=0)
    elif kind == "padding":
        x[:, 2] = np.minimum(65527, x[:, 2] + int(strength))
    elif kind == "observation_loss":
        if strength > 1:
            raise ValueError("loss probability must be <= 1")
        keep = rng.random(len(x)) >= strength
        keep[0] = True  # keep origin; never create an empty flow
        times = np.cumsum(x[:, 0])[keep]
        removed = int((~keep).sum())
        x = x[keep]
        x[:, 0] = np.diff(times, prepend=times[0])
    else:
        raise ValueError("unknown stress family")
    return x, {
        "kind": kind,
        "strength": strength,
        "seed": seed,
        "removed": removed,
        "first_observation_offset_ms": offset,
        "byte_delta": float(x[:, 2].sum()) - before_bytes,
        "duration_delta_ms": float(x[:, 0].sum()) - before_duration,
    }
