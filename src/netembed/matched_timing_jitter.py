"""Deterministic abstract gap jitter and fixed matched development gates."""

import hashlib
import numpy as np

from .contract import validate_array


def assignment(flow_id, seed=70017):
    digest = hashlib.sha256(f"{seed}:{flow_id}".encode()).digest()
    return (-0.1, 0.0, 0.1)[int.from_bytes(digest[:8], "big") % 3]


def jitter(flow, delta):
    if delta not in (-0.1, 0.0, 0.1):
        raise ValueError("undeclared abstract gap offset")
    raw = validate_array(flow).copy()
    raw[1:, 0] = np.clip(raw[1:, 0] + np.float32(delta), 0, 3600000)
    return raw


def gates(control, candidate, labels):
    local = ["youtube", "instagram", "spotify"]
    views = ["unchanged", "gap_plus_0_1_ms", "gap_minus_0_1_ms"]
    clean = all(
        candidate["local"]["unchanged"]["classes"][label]["correct"]
        >= control["local"]["unchanged"]["classes"][label]["correct"]
        for label in local
    )
    stress = all(
        candidate["local"][view]["classes"][label]["correct"]
        >= control["local"][view]["classes"][label]["correct"]
        for view in views[1:]
        for label in local
    )
    gain = sum(candidate["local"][view]["correct"] - control["local"][view]["correct"] for view in views[1:])
    public_old, public_new = control["public"]["unchanged"], candidate["public"]["unchanged"]
    return {
        "local_clean_no_service_loss": clean,
        "local_each_stress_no_service_loss": stress,
        "local_stress_gain_at_least_two": gain >= 2,
        "public_macro_f1_retained": public_new["macro_f1"] + 1e-12 >= public_old["macro_f1"] - 0.02,
        "public_each_class_recall_retained": all(
            public_new["classes"][label]["recall"] + 1e-12 >= public_old["classes"][label]["recall"] - 0.05
            for label in labels
        ),
    }
