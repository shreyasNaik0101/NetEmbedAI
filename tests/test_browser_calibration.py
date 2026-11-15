"""Constructed software fixtures; no calibration-quality or live evidence."""

import json

import numpy as np
import pytest

from netembed.browser_adaptation import load_reference_trial, load_trial
from netembed.browser_calibration import collection_plan, fit_joint_policy, write_policy_bundle
from netembed.bundle import Predictor, sha256


PLAN = {
    "minimum_accepted_local_prefixes": 30,
    "minimum_accepted_prefixes_per_local_class": 5,
    "maximum_empirical_error_overall": 0.1,
    "maximum_empirical_error_per_local_class": 0.1,
}


def test_explicit_new_plan_preserves_previous_candidate_plan(tmp_path):
    old = tmp_path / "calibration-collection-plan-v1.json"
    new = tmp_path / "calibration-collection-plan-v2.json"
    old.write_text('{"candidate_artifact_id": "old"}')
    new.write_text('{"candidate_artifact_id": "replacement"}')
    old_hash = sha256(old)
    path, plan = collection_plan(tmp_path, new.name)
    assert path == new and plan["candidate_artifact_id"] == "replacement"
    assert sha256(old) == old_hash


@pytest.mark.parametrize(
    "name",
    ["../calibration-collection-plan-v1.json", "other.json", "nested/calibration-collection-plan-v1.json"],
)
def test_plan_cannot_escape_collection_or_use_an_unrelated_file(tmp_path, name):
    with pytest.raises(ValueError, match="collection-local"):
        collection_plan(tmp_path, name)


def perfect(truth, confidence=0.95):
    result = np.full((len(truth), 2), 1 - confidence)
    result[np.arange(len(truth)), truth] = confidence
    return result


def test_joint_policy_checks_each_class_even_when_total_error_is_allowed():
    truth = np.repeat([0, 1], 20)
    scores = perfect(truth, 0.9)
    scores[:4] = [0.45, 0.55]  # 10% overall, but 20% error for class zero.
    public_truth = np.repeat([0, 1], 50)
    policy, selected, _ = fit_joint_policy(scores, truth, perfect(public_truth), public_truth, [0, 1], PLAN)
    assert policy["fitted"] and policy["threshold"] == pytest.approx(0.56)
    assert selected["local"]["accepted"] == 36
    assert selected["local_classes"]["0"]["error"] == 0


def test_local_errors_cannot_be_diluted_by_many_public_records():
    truth = np.repeat([0, 1], 20)
    scores = perfect(truth)
    scores[:20] = [0.01, 0.99]
    public_truth = np.repeat([0, 1], 1000)
    policy, _, _ = fit_joint_policy(scores, truth, perfect(public_truth), public_truth, [0, 1], PLAN)
    assert policy["fitted"] is False


@pytest.mark.parametrize("truth", [np.repeat([0, 1], 10), np.zeros(40, dtype=int)])
def test_insufficient_prefixes_or_service_support_stays_uncommitted(truth):
    public_truth = np.repeat([0, 1], 50)
    policy, selected, _ = fit_joint_policy(
        perfect(truth), truth, perfect(public_truth), public_truth, [0, 1], PLAN
    )
    assert not policy["fitted"] and selected is None and policy["threshold"] == 1


def test_historical_control_cannot_be_ignored():
    truth = np.repeat([0, 1], 20)
    bad_public = perfect(1 - truth, 0.99)
    policy, _, _ = fit_joint_policy(perfect(truth), truth, bad_public, truth, [0, 1], PLAN)
    assert not policy["fitted"]


@pytest.mark.parametrize(
    "trial,stage",
    [
        ("instagram-dev-01", "calibration"),
        ("instagram-cal-01", "development"),
        ("instagram-eval-01", "calibration"),
    ],
)
def test_recording_roles_cannot_be_interchanged(tmp_path, trial, stage):
    with pytest.raises(ValueError, match="trial role"):
        load_reference_trial(tmp_path, trial, ["youtube", "instagram"], stage)
    if "cal" in trial:
        with pytest.raises(ValueError):
            load_trial(tmp_path, trial, ["youtube", "instagram"])


def test_policy_export_keeps_weights_normalizer_and_source_unchanged(bundle, raw, tmp_path):
    source = Predictor(bundle, allow_fixture=True)
    before = json.loads((bundle / "metadata.json").read_text())
    weights = sha256(bundle / "weights.pt")
    policy = {
        "version": "software-fixture",
        "threshold": 0.9,
        "fitted": True,
        "min_packets": 5,
        "temperature": 1.0,
    }
    target = write_policy_bundle(bundle, tmp_path / "calibrated", policy, {"fixture": True})
    after = Predictor(target, allow_fixture=True)
    assert sha256(target / "weights.pt") == weights == sha256(bundle / "weights.pt")
    assert after.normalizer.metadata() == source.normalizer.metadata()
    np.testing.assert_array_equal(after.probabilities([raw]), source.probabilities([raw]))
    assert json.loads((bundle / "metadata.json").read_text()) == before
    with pytest.raises(ValueError, match="infeasible"):
        write_policy_bundle(bundle, tmp_path / "unsafe", {**policy, "fitted": False}, {})
