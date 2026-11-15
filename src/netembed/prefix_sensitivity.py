"""Abstract fixed-prefix sensitivity transformations, not network simulations."""

import numpy as np
from .contract import validate_array


def views(flow):
    source = validate_array(flow)
    if len(source) < 10:
        raise ValueError("requires at least ten packets")
    source = source[:10].copy()
    plus, minus, swapped = source.copy(), source.copy(), source.copy()
    plus[1:, 0] = np.minimum(3600000, source[1:, 0] + np.float32(0.1))
    minus[1:, 0] = np.maximum(0, source[1:, 0] - np.float32(0.1))
    swap_index = None
    for i in range(2, 10):
        if source[i, 0] <= 1.0 and source[i - 1, 1] != source[i, 1]:
            swapped[[i - 1, i], 1:] = swapped[[i, i - 1], 1:]
            swap_index = i
            break
    return {
        "unchanged": source,
        "gap_plus_0_1_ms": plus,
        "gap_minus_0_1_ms": minus,
        "first_opposite_direction_swap_within_1_ms": swapped,
    }, swap_index
