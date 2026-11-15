"""Software fixtures only; never model-quality evidence or live capture."""

import copy
import numpy as np
import pytest
from sklearn.ensemble import RandomForestClassifier
from netembed.bundle import Predictor, export_bundle
from netembed.contract import Normalizer, forest_features
from netembed.timing_repair import read_config, guard, gates


def test_rounding_map_is_prefix_local_and_does_not_mutate_input():
    raw = np.array(
        [[0, 1, 1200], [0.5, -1, 90], [1.5, 1, 1230], [2.5, -1, 40], [0.8, 1, 50]], dtype=np.float32
    )
    before = raw.copy()
    rounded = raw.copy()
    rounded[:, 0] = [0, 0, 2, 2, 1]
    normalizer = Normalizer.fit([raw])
    for b in [1, 3, 5]:
        actual = forest_features(raw[:b], normalizer, "summary-nearest-ms-v1")
        expected = forest_features(rounded[:b], normalizer, "summary-v1")
        np.testing.assert_array_equal(actual, expected)
    np.testing.assert_array_equal(raw, before)
    with pytest.raises(ValueError, match="unknown forest"):
        forest_features(raw, normalizer, "summary-unknown-ms")


def test_rounding_artifact_matches_training_features_without_training_data(tmp_path):
    arrays = [
        np.array(
            [[0, 1, 1200], [v, -1, 100], [v + 0.5, 1, 60], [0.3, -1, 50], [0.2, 1, 70]],
            dtype=np.float32,
        )
        for v in [0.1, 0.9, 2.1, 5.7]
    ]
    normalizer = Normalizer.fit(arrays)
    features = np.asarray([forest_features(x, normalizer, "summary-nearest-ms-v1") for x in arrays])
    model = RandomForestClassifier(n_estimators=3, max_depth=2, random_state=17).fit(features, [0, 0, 1, 1])
    path = export_bundle(
        tmp_path / "fixture",
        model,
        normalizer,
        ["fixture-a", "fixture-b"],
        {"fixture": True},
        {"feature_map": "summary-nearest-ms-v1"},
    )
    predictor = Predictor(path, allow_fixture=True)
    np.testing.assert_allclose(
        predictor.probabilities(arrays), model.predict_proba(features), rtol=0, atol=1e-12
    )
    assert predictor.meta["architecture"]["feature_map"] == "summary-nearest-ms-v1"
    for x in arrays:
        assert predictor.predict(x)["decision_reason"] == "policy_not_fitted"


def test_fixed_protocol_rejects_changed_bytes(tmp_path):
    cfg = read_config("configs/spotify-timing-repair-v1.json")
    assert cfg["seed"] == 17 and len(cfg["arms"]) == 2
    from pathlib import Path

    path = tmp_path / "changed.json"
    path.write_bytes(Path("configs/spotify-timing-repair-v1.json").read_bytes() + b" ")
    with pytest.raises(ValueError, match="declaration changed"):
        read_config(path)


def guard_config():
    cfg = read_config("configs/spotify-timing-repair-v1.json")
    from netembed.ipv6_pilot import read_config as recipe

    return cfg, recipe(cfg["training_recipe"])


@pytest.mark.parametrize(
    "path",
    [
        "data/processed/v2/test.jsonl",
        "data/processed/v2/calibration.jsonl",
        "artifacts/local/ipv6-frozen-evaluation-v1/ipv6-eval-yt-01-capture.json",
        "artifacts/local/ipv6-live-policy-v1/live-yt-01-capture.json",
        "artifacts/local/forest-policy-calibration-recovery-v1/rows.json",
        "artifacts/local/hotspot-fresh-sessions-v1/fresh-ig-02-rows.json",
        "artifacts/local/spotify-diagnostic-v1/spotify-01-capture.json",
        "experiments/spotify-frozen-comparison-v1/report.json",
    ],
)
def test_protected_or_diagnostic_during_fitting_is_blocked(path):
    cfg, recipe = guard_config()
    with pytest.raises(ValueError):
        guard("open", (path, "r", 0), cfg, recipe, "experiments/spotify-timing-repair-v1", "fitting")


def test_diagnostic_access_only_after_fitting_and_network_forbidden():
    cfg, recipe = guard_config()
    guard(
        "open",
        ("artifacts/local/spotify-diagnostic-v1/spotify-01-capture.json", "r", 0),
        cfg,
        recipe,
        "experiments/spotify-timing-repair-v1",
        "assessment",
    )
    with pytest.raises(ValueError, match="offline"):
        guard("socket.connect", (), cfg, recipe, "experiments/spotify-timing-repair-v1", "assessment")


def fixture_metrics(spotify_correct):
    return {
        "spotify": {
            "budgets": {
                str(b): {"n": n, "classes": {"spotify": {"recall": c / n}}}
                for b, n, c in zip([10, 20, 30], [5, 5, 3], spotify_correct)
            }
        },
        "local": {
            "macro_f1": 0.9,
            "budgets": {
                str(b): {"classes": {"youtube": {"recall": 0.9}, "instagram": {"recall": 1.0}}}
                for b in [5, 10, 20, 30]
            },
        },
        "public": {
            "budgets": {
                str(b): {"macro_f1": 0.9, "classes": {"youtube": {"recall": 0.9}, "spotify": {"recall": 0.8}}}
                for b in [5, 10, 20, 30]
            }
        },
    }


def test_primary_gain_cannot_hide_later_spotify_or_retention_failures():
    cfg, _ = guard_config()
    control = fixture_metrics([0, 0, 0])
    candidate = fixture_metrics([4, 3, 2])
    assert all(gates(candidate, control, cfg).values())
    later = fixture_metrics([4, 0, 0])
    assert not gates(later, control, cfg)["spotify_each_prefix_floor"]
    altered = copy.deepcopy(candidate)
    altered["local"]["budgets"]["5"]["classes"]["instagram"]["recall"] = 0.99
    assert not gates(altered, control, cfg)["local_each_class_prefix_retention"]
    altered = copy.deepcopy(candidate)
    altered["public"]["budgets"]["20"]["classes"]["spotify"]["recall"] = 0.74
    assert not gates(altered, control, cfg)["public_each_class_prefix_retention"]
