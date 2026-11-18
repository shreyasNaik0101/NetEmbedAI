"""Constructed augmentation/guard checks; not evidence of traffic or quality."""

import numpy as np
import pytest
from netembed.matched_timing_jitter import assignment, jitter, gates


def test_jitter_is_bounded_immutable_and_prefix_consistent():
    raw = np.array(
        [[0 if i == 0 else 0.05, 1 if i % 2 else -1, 200 + i] for i in range(30)], dtype=np.float32
    )
    original = raw.copy()
    for delta in [-0.1, 0, 0.1]:
        changed = jitter(raw, delta)
        np.testing.assert_array_equal(raw, original)
        assert changed[0, 0] == 0 and (changed[:, 0] >= 0).all()
        assert np.max(np.abs(changed[:, 0] - raw[:, 0])) <= 0.10001
        np.testing.assert_array_equal(changed[:, 1:], raw[:, 1:])
        for length in (5, 10, 20, 30):
            np.testing.assert_array_equal(jitter(raw[:length], delta), changed[:length])
    with pytest.raises(ValueError):
        jitter(raw, 0.2)


def test_assignment_is_stable_and_uses_only_declared_values():
    ids = [f"flow-{i}" for i in range(100)]
    values = {key: assignment(key) for key in ids}
    assert values == {key: assignment(key) for key in reversed(ids)}
    assert set(values.values()) == {-0.1, 0.0, 0.1}


def test_retention_gates_reject_class_loss_even_with_improved_total():
    labels = ["youtube", "instagram", "spotify"]

    def report(n):
        return {
            "correct": n * 3,
            "macro_f1": 1.0,
            "classes": {label: {"correct": n, "recall": 1.0} for label in labels},
        }

    control = {
        d: {v: report(2) for v in ["unchanged", "gap_plus_0_1_ms", "gap_minus_0_1_ms"]}
        for d in ["local", "public"]
    }
    import copy

    candidate = copy.deepcopy(control)
    candidate["local"]["gap_plus_0_1_ms"]["correct"] += 3
    candidate["local"]["gap_plus_0_1_ms"]["classes"]["spotify"]["correct"] -= 1
    result = gates(control, candidate, labels)
    assert result["local_stress_gain_at_least_two"]
    assert not result["local_each_stress_no_service_loss"]


@pytest.mark.parametrize(
    "path",
    [
        "data/processed/v2/test.jsonl",
        "data/processed/v2/calibration.jsonl",
        "artifacts/local/ten-packet-policy-v1/final-predictions.json",
        "artifacts/local/spotify-data-repair-v1/spotify-eval-01-rows.json",
    ],
)
def test_matched_study_blocks_final_and_calibration_inputs(path):
    import json
    from pathlib import Path
    from scripts.study_matched_timing_jitter import guard

    cfg = json.loads(Path("configs/timing-jitter-matched-v1.json").read_text())
    recipe = json.loads(Path(cfg["training_recipe"]).read_text())
    with pytest.raises(ValueError):
        guard("open", (path,), cfg, recipe)
    with pytest.raises(ValueError, match="offline"):
        guard("socket.connect", (), cfg, recipe)
