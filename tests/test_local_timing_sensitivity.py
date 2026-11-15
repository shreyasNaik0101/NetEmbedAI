"""Semantic regression checks for exploratory timing hypotheses, not accuracy."""

import importlib.util
from pathlib import Path

import numpy as np
import pytest


spec = importlib.util.spec_from_file_location(
    "local_shift", Path(__file__).parents[1] / "scripts" / "diagnose_local_shift.py"
)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def test_absolute_timestamp_floor_is_distinct_from_flooring_each_gap():
    raw = np.array([[0, 1, 1250], [0.6, -1, 100], [0.6, 1, 200]], dtype=np.float32)
    before = raw.copy()
    result = module.timing_variants(raw, 1000.8)
    np.testing.assert_array_equal(result["floor_gap"][:, 0], [0, 0, 0])
    np.testing.assert_array_equal(result["floor_timestamp"][:, 0], [0, 1, 1])
    np.testing.assert_array_equal(raw, before)
    for variant in result.values():
        np.testing.assert_array_equal(variant[:, 1:], raw[:, 1:])
        assert variant[0, 0] == 0


def test_absolute_clock_phase_changes_timestamp_floor_but_not_gap_floor():
    raw = np.array([[0, 1, 1250], [0.4, -1, 100]], dtype=np.float32)
    a, b = module.timing_variants(raw, 1000.1), module.timing_variants(raw, 1000.9)
    assert a["floor_timestamp"][1, 0] == 0 and b["floor_timestamp"][1, 0] == 1
    np.testing.assert_array_equal(a["floor_gap"], b["floor_gap"])


def test_nonfinite_clock_is_rejected():
    with pytest.raises(ValueError, match="nonfinite"):
        module.timing_variants(np.array([[0, 1, 1250]]), float("nan"))
