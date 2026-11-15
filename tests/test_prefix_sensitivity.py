"""Synthetic transformation semantics, not physical network claims."""

import numpy as np
import pytest
from netembed.prefix_sensitivity import views


def sample():
    return np.array(
        [[0 if i == 0 else 0.5, 1 if i < 4 else -1, 100 + i] for i in range(12)], dtype=np.float32
    )


def test_fixed_prefix_bounds_immutability_and_swap_preserves_pairs_and_duration():
    raw = sample()
    original = raw.copy()
    result, index = views(raw)
    np.testing.assert_array_equal(raw, original)
    assert index == 4 and all(len(x) == 10 for x in result.values())
    for name in ["gap_plus_0_1_ms", "gap_minus_0_1_ms"]:
        assert result[name][0, 0] == 0
        assert np.max(np.abs(result[name][:, 0] - raw[:10, 0])) <= 0.10001
        np.testing.assert_array_equal(result[name][:, 1:], raw[:10, 1:])
    swapped = result["first_opposite_direction_swap_within_1_ms"]
    np.testing.assert_array_equal(swapped[:, 0], raw[:10, 0])
    np.testing.assert_array_equal(swapped[3, 1:], raw[4, 1:])
    np.testing.assert_array_equal(swapped[4, 1:], raw[3, 1:])
    altered_future = raw.copy()
    altered_future[10:, 2] += 500
    for key, value in views(altered_future)[0].items():
        np.testing.assert_array_equal(value, result[key])


def test_no_eligible_swap_is_unchanged_and_short_inputs_fail():
    raw = sample()
    raw[:, 1] = 1
    result, index = views(raw)
    assert index is None
    np.testing.assert_array_equal(result["unchanged"], result["first_opposite_direction_swap_within_1_ms"])
    with pytest.raises(ValueError, match="ten"):
        views(raw[:9])


def test_clipping_prevents_negative_and_excessive_gaps():
    raw = sample()
    raw[1, 0] = 0
    raw[2, 0] = 3600000
    result, _ = views(raw)
    assert result["gap_minus_0_1_ms"][1, 0] == 0
    assert result["gap_plus_0_1_ms"][2, 0] == 3600000


@pytest.mark.parametrize(
    "path",
    [
        "data/processed/v2/train.jsonl",
        "data/processed/v2/test.jsonl",
        "artifacts/local/ten-packet-policy-v1/final-predictions.json",
        "artifacts/local/ten-packet-policy-v1/ten-policy-cal-yt-01-rows.json",
        "experiments/ipv6-frozen-evaluation-v1/comparison.json",
    ],
)
def test_offline_study_guard_denies_protected_inputs(path):
    import json
    from pathlib import Path
    from scripts.study_prefix_sensitivity import guard

    cfg = json.loads(Path("configs/prefix-sensitivity-dev-v1.json").read_text())
    with pytest.raises(ValueError):
        guard("open", (path,), cfg)
    with pytest.raises(ValueError, match="offline"):
        guard("socket.connect", (), cfg)
