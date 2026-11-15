from collections import Counter
from pathlib import Path

import numpy as np
import pytest

from netembed.spotify_weights import access_guard, choose, read_config, sample_weights
from netembed.ipv6_pilot import read_config as read_recipe


def test_fixed_protocol():
    cfg = read_config("configs/spotify-weight-study-v1.json")
    assert [a["spotify_mass"] for a in cfg["arms"]] == [0.01, 0.025, 0.05]
    assert cfg["maximum_new_fits"] == 3


@pytest.mark.parametrize("mass", [0.01, 0.025, 0.05])
def test_class_mass_not_flow_count(mass):
    labels = ["youtube"] * 144 + ["instagram"] * 104 + ["spotify"] * 68
    weights = sample_weights(56000, labels, mass)
    total = Counter()
    for label, weight in zip(labels, weights[56000:]):
        total[label] += weight
    assert weights[:56000].sum() == pytest.approx(0.75)
    assert total["spotify"] == pytest.approx(mass)
    assert total["youtube"] == pytest.approx((0.25 - mass) / 2)
    assert total["instagram"] == pytest.approx(total["youtube"])
    assert np.sum(weights) == pytest.approx(1)


@pytest.mark.parametrize("mass", [0, 0.25, -0.1, float("nan")])
def test_invalid_mass(mass):
    with pytest.raises(ValueError):
        sample_weights(10, ["youtube", "instagram", "spotify"], mass)


def test_missing_class_rejected():
    with pytest.raises(ValueError):
        sample_weights(10, ["youtube", "spotify"], 0.01)


def test_selection_requires_all_gates_and_prefers_lower_mass():
    def result(mass, passes):
        return {
            "spotify_mass": mass,
            "gates": {"retention": passes},
            "metrics": {"spotify": {"budgets": {b: {"accuracy": 1, "n": 4} for b in ["10", "20", "30"]}}},
        }

    reports = {"low": result(0.01, True), "high": result(0.05, True)}
    assert choose(reports) == "low"
    reports["low"]["gates"]["retention"] = False
    assert choose(reports) == "high"
    assert choose({"failed": result(0.01, False)}) is None


@pytest.mark.parametrize(
    "filename",
    [
        "data/processed/v2/calibration.jsonl",
        "data/processed/v2/test.jsonl",
        "artifacts/local/spotify-data-repair-v1/spotify-cal-01-rows.json",
        "artifacts/local/spotify-diagnostic-v1/spotify-01-rows.json",
        "experiments/ipv6-frozen-evaluation-v1/comparison.json",
    ],
)
def test_protected_inputs_blocked(filename):
    cfg = read_config("configs/spotify-weight-study-v1.json")
    recipe = read_recipe("configs/ipv6-realdata-pilot-v1.json")
    with pytest.raises(ValueError):
        access_guard("open", (str(Path(filename)),), cfg, recipe)


def test_permitted_training_and_development_only():
    cfg = read_config("configs/spotify-weight-study-v1.json")
    recipe = read_recipe("configs/ipv6-realdata-pilot-v1.json")
    for filename in [
        str(Path(recipe["public_data"]) / "train.jsonl"),
        str(Path(recipe["public_data"]) / "selection.jsonl"),
        "artifacts/local/spotify-data-repair-v1/spotify-train-01-rows.json",
        "artifacts/local/spotify-data-repair-v1/spotify-dev-01-rows.json",
    ]:
        access_guard("open", (filename,), cfg, recipe)
    with pytest.raises(ValueError):
        access_guard("socket.connect", (), cfg, recipe)
