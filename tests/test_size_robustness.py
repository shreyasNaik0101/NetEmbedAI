"""Constructed invariants for the new development study, not accuracy evidence."""

import copy
import json
from pathlib import Path

import numpy as np
import pytest
from sklearn.ensemble import RandomForestClassifier

from netembed.browser_adaptation import UNCOMMITTED
from netembed.bundle import Predictor, export_bundle, sha256, write_json
from netembed.contract import Normalizer, forest_features, summary
from netembed.size_robustness import (
    choose,
    gates,
    guard,
    read_config,
    read_public,
    run,
    shift_large,
    training_delta,
)


def test_relative_features_keep_counts_times_and_use_only_prefix_maximum():
    raw = np.array([[0, 1, 1250], [0.01, -1, 1000], [5, 1, 40], [20, -1, 800]], dtype=np.float32)
    norm = Normalizer([0, 0, 0], [1, 1, 1])
    before = np.asarray(summary(raw))
    after = forest_features(raw, norm, "summary-relative-size-v1")
    assert len(after) == 34
    for start in (7, 18, 29):
        np.testing.assert_allclose(after[start : start + 5], before[start : start + 5] / 1250)
        before[start : start + 5] = after[start : start + 5]
    np.testing.assert_array_equal(after, before)
    doubled = raw.copy()
    doubled[:, 2] *= 2
    np.testing.assert_allclose(after, forest_features(doubled, norm, "summary-relative-size-v1"))
    prefix = raw[:2].copy()
    expected = forest_features(prefix, norm, "summary-relative-size-v1")
    raw[2:, 2] = 60000
    np.testing.assert_array_equal(expected, forest_features(raw[:2], norm, "summary-relative-size-v1"))
    np.testing.assert_array_equal(forest_features(prefix, norm, "summary-v1"), summary(prefix))


def test_relative_forest_export_matches_training_without_data_fitting(tmp_path):
    norm = Normalizer([0, 0, 0], [1, 1, 1])
    flows = [np.array([[0, 1, 1250], [i + 1, -1, 100 + i * 80]], dtype=np.float32) for i in range(8)]
    features = [forest_features(x, norm, "summary-relative-size-v1") for x in flows]
    forest = RandomForestClassifier(n_estimators=3, max_depth=2, random_state=17).fit(
        features, [0] * 4 + [1] * 4
    )
    folder = export_bundle(
        tmp_path / "fixture",
        forest,
        norm,
        ["fixture-a", "fixture-b"],
        {"fixture": True},
        {"feature_map": "summary-relative-size-v1"},
        UNCOMMITTED,
    )
    predictor = Predictor(folder, allow_fixture=True)
    np.testing.assert_allclose(predictor.probabilities(flows), forest.predict_proba(features), atol=1e-12)
    assert predictor.predict(flows[0])["label"] is None
    # This feature map has no fitted normalization dependency.
    predictor.normalizer = Normalizer([1e6, 1e6, 1e6], [1e6, 1e6, 1e6])
    np.testing.assert_allclose(predictor.probabilities(flows), forest.predict_proba(features), atol=1e-12)


@pytest.mark.parametrize("delta", [-32, 0, 32])
def test_size_transform_preserves_units_order_and_prefix_with_bounded_clipping(delta):
    raw = np.array([[0, 1, 1250], [0.001, -1, 40], [20, -1, 1200], [2, 1, 65527]], dtype=np.float32)
    original = raw.copy()
    changed = shift_large(raw, delta)
    np.testing.assert_array_equal(raw, original)
    np.testing.assert_array_equal(changed[:, :2], raw[:, :2])
    assert changed[1, 2] == 40 and (changed[[0, 2, 3], 2] >= 1200).all()
    assert (changed[:, 2] <= 65527).all() and np.max(np.abs(changed[:, 2] - raw[:, 2])) <= 32
    np.testing.assert_array_equal(changed[:2], shift_large(raw[:2], delta))


@pytest.mark.parametrize("delta", [-33, 33, 0.5, float("nan")])
def test_size_treatment_rejects_out_of_scope_strength(delta):
    with pytest.raises(ValueError):
        shift_large(np.array([[0, 1, 1250]], dtype=np.float32), delta)


def test_augmentation_is_stateless_per_flow_and_keeps_a_fixed_manifest_across_forest_seeds():
    ids = [f"fixture-{i}" for i in range(100)]
    forward = {i: training_delta(i) for i in ids}
    backward = {i: training_delta(i) for i in reversed(ids)}
    assert forward == backward and all(-32 <= d <= 32 for d in forward.values())
    assert len(set(forward.values())) > 10 and 0 in forward.values()


@pytest.mark.parametrize(
    "path",
    [
        "data/processed/v2/calibration.jsonl",
        "data/./processed/v2/test.jsonl",
        "artifacts/local/forest-policy-calibration-recovery-v1/anything.json",
        "artifacts/local/prospective-paired-followup-v1/paired-yt-01-rows.json",
        "artifacts/local/example-eval-yt-01-rows.json",
    ],
)
def test_study_refuses_protected_inputs_even_using_relative_paths(path):
    with pytest.raises(ValueError, match="excluded"):
        guard("open", (path, "r", 0))
    guard("open", ("data/processed/v2/train.jsonl", "r", 0))


def test_public_loader_does_not_open_final_or_calibration(tmp_path):
    for role in ("calibration", "test"):
        with pytest.raises(ValueError, match="only public training/selection"):
            read_public(tmp_path / "absent", role)


def metric(f1, youtube=0.8, instagram=0.8):
    return {
        "macro_f1": f1,
        "class_recall": {"youtube": youtube, "instagram": instagram},
        "primary_class_recall": {"youtube": youtube, "instagram": instagram},
    }


def reports():
    return {
        "local": {"clean": metric(0.8), "stress": metric(0.6)},
        "public": {"clean": metric(0.8), "stress": metric(0.7)},
    }


def test_mean_improvement_cannot_hide_local_or_public_class_regression():
    cfg = read_config(Path(__file__).parents[1] / "configs/size-robustness-v1.json")
    control = reports()
    candidate = copy.deepcopy(control)
    candidate["local"]["stress"]["macro_f1"] = 0.7
    assert all(gates(candidate, control, cfg).values())
    candidate["local"]["clean"]["class_recall"]["instagram"] = 0.79
    assert not gates(candidate, control, cfg)["local_clean_classes"]
    candidate = copy.deepcopy(control)
    candidate["local"]["stress"]["macro_f1"] = 0.7
    candidate["public"]["clean"]["class_recall"]["youtube"] = 0.74
    assert not gates(candidate, control, cfg)["public_clean_classes"]
    candidate["local"]["stress"]["primary_class_recall"]["youtube"] = 0.6
    assert not gates(candidate, control, cfg)["local_primary_stress_floor"]


def test_choice_is_seed17_only_with_fixed_simple_tie_preference_and_no_rescue(tmp_path):
    path = Path(__file__).parents[1] / "configs/size-robustness-v1.json"
    cfg = read_config(path)
    values = {name: reports() for name in ("clean", "size-jitter", "relative-size")}
    assert choose(values, cfg) is None
    values["size-jitter"]["local"]["stress"]["macro_f1"] = 0.7
    values["relative-size"]["local"]["stress"]["macro_f1"] = 0.695
    assert choose(values, cfg) == "relative-size"
    (tmp_path / "seed17").mkdir()
    (tmp_path / "seed17/result.json").write_text(json.dumps({"config": cfg, "chosen": None}))
    with pytest.raises(ValueError, match="no repetitions"):
        run(42, path, tmp_path)


def saved_fixture_run(root, seed, cfg, values, chosen):
    """Explicit fixture exports exercise evidence verification, never real claims."""
    folder = root / f"seed{seed}"
    folder.mkdir()
    write_json(folder / "data-manifest.json", {"fixture": True})
    write_json(folder / "training-augmentation-manifest.json", {"fixture": True})
    write_json(
        folder / "config.json",
        {
            "data_manifest_sha256": sha256(folder / "data-manifest.json"),
            "augmentation_manifest_sha256": sha256(folder / "training-augmentation-manifest.json"),
        },
    )
    norm = Normalizer([0, 0, 0], [1, 1, 1])
    forest = RandomForestClassifier(n_estimators=1, random_state=17).fit([[0] * 34, [1] * 34], [0, 1])
    identities, development, predictions = {}, {}, {}
    for arm, report in values.items():
        bundle = export_bundle(
            folder / arm / "bundle",
            forest,
            norm,
            ["fixture-a", "fixture-b"],
            {"fixture": True},
            {},
            UNCOMMITTED,
        )
        write_json(folder / arm / "development.json", report)
        write_json(folder / arm / "predictions.json", {"fixture": True})
        identities[arm] = sha256(bundle / "metadata.json")
        development[arm] = sha256(folder / arm / "development.json")
        predictions[arm] = sha256(folder / arm / "predictions.json")
    write_json(
        folder / "result.json",
        {
            "config": cfg,
            "forest_seed": seed,
            "chosen": chosen,
            "artifact_ids": identities,
            "config_sha256": sha256(folder / "config.json"),
            "development_sha256": development,
            "prediction_sha256": predictions,
            "gates": {a: gates(v, values["clean"], cfg) for a, v in values.items() if a != "clean"},
        },
    )


def test_failed_first_stage_is_sealed_without_reading_repetitions_or_benchmark(tmp_path, monkeypatch):
    import netembed.size_robustness as study

    path = Path(__file__).parents[1] / "configs/size-robustness-v1.json"
    cfg = read_config(path)
    values = {name: reports() for name in ("clean", "size-jitter", "relative-size")}
    saved_fixture_run(tmp_path, 17, cfg, values, None)
    monkeypatch.setattr(study, "Predictor", lambda p: Predictor(p, allow_fixture=True))
    result = study.finish(path, tmp_path)
    assert result["status"] == "stop_no_validated_candidate" and result["development_candidate"] is None
    assert set(result["eligible_by_seed"]) == {"17"} and not (tmp_path / "benchmark.json").exists()
    with pytest.raises(FileExistsError):
        study.finish(path, tmp_path)


def test_good_later_seed_cannot_rescue_failed_repetition(tmp_path, monkeypatch):
    import netembed.size_robustness as study

    path = Path(__file__).parents[1] / "configs/size-robustness-v1.json"
    cfg = read_config(path)
    for seed in (17, 42, 123):
        arms = ("clean", "size-jitter", "relative-size") if seed == 17 else ("clean", "relative-size")
        values = {name: reports() for name in arms}
        for arm in arms:
            if arm != "clean":
                values[arm]["local"]["stress"]["macro_f1"] = 0.7
        if seed == 42:
            values["relative-size"]["local"]["clean"]["class_recall"]["instagram"] = 0.7
        saved_fixture_run(tmp_path, seed, cfg, values, "relative-size")
    monkeypatch.setattr(study, "Predictor", lambda p: Predictor(p, allow_fixture=True))
    result = study.finish(path, tmp_path)
    assert result["eligible_by_seed"] == {"17": True, "42": False, "123": True}
    assert not result["eligible_all_three_seeds"] and result["development_candidate"] is None
