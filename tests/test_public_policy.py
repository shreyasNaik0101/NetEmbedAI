"""Constructed policy cases, never evidence of benchmark or local accuracy."""

from copy import deepcopy

import pytest

from netembed.public_policy import fit_guard, read_config, select_policy


def cfg():
    return read_config("configs/ipv6-public-policy-v1.json")


def cases():
    result = []
    for label in ("a", "b"):
        for i in range(10):
            value = 0.8 if i < 8 else 0.4
            p = [value, 1 - value] if label == "a" else [1 - value, value]
            result.append(
                {
                    "id": f"{label}-{i}",
                    "reference": label,
                    "budget": 10,
                    "probabilities": p,
                    "top1": ("a", "b")[p.index(max(p))],
                }
            )
    return result


def test_lowest_eligible_cutoff_preserves_class_error_and_primary_coverage():
    policy, selected, curve = select_policy(cases(), ["a", "b"], cfg())
    assert len(curve) == 101 and policy["threshold"] == 0.61
    assert selected["primary"]["coverage"] == 0.8 and selected["primary"]["error"] == 0
    assert policy["validation_scope"] == "cesnet_calibration_only"
    assert policy["locally_checked_labels"] == [] and policy["min_packets"] == 10


def test_bad_class_cannot_hide_behind_good_aggregate_or_accepted_subset():
    rows = cases()
    for r in rows:
        if r["reference"] == "b":
            r.update(probabilities=[0.9, 0.1], top1="a")
    policy, selected, curve = select_policy(rows, ["a", "b"], cfg())
    assert not policy["fitted"] and selected is None and not any(r["eligible"] for r in curve)


def test_duplicate_or_inconsistent_probability_case_is_rejected():
    rows = cases()
    with pytest.raises(ValueError, match="duplicate"):
        select_policy(rows + [rows[0]], ["a", "b"], cfg())
    rows = deepcopy(rows)
    rows[0]["top1"] = "b"
    with pytest.raises(ValueError, match="invalid"):
        select_policy(rows, ["a", "b"], cfg())


@pytest.mark.parametrize(
    "event,args",
    [
        ("socket.connect", ()),
        ("socket.getaddrinfo", ()),
        ("open", ("data/processed/v2/test.jsonl",)),
        ("open", ("data/processed/v2/train.jsonl",)),
        ("open", ("data/processed/v2/selection.jsonl",)),
        ("open", ("artifacts/local/ipv6-frozen-evaluation-v1/paired-predictions.json",)),
        ("open", ("experiments/ipv6-realdata-pilot-v1/plus-real-ipv6/predictions.json",)),
        ("open", ("experiments/browser-adaptation/selection-followup-v1-seed17/development.json",)),
    ],
)
def test_policy_fit_blocks_local_evaluation_and_other_splits(event, args):
    with pytest.raises(ValueError):
        fit_guard(event, args)
    fit_guard("open", ("data/processed/v2/calibration.jsonl",))
    fit_guard("open", ("experiments/ipv6-realdata-pilot-v1/plus-real-ipv6/bundle/forest.json",))


def test_unfitted_prediction_explains_policy_without_changing_status_or_scores(bundle, raw):
    import json
    from netembed.bundle import Predictor, sha256, write_json

    metadata = json.loads((bundle / "metadata.json").read_text())
    metadata["policy"]["fitted"] = False
    write_json(bundle / "metadata.json", metadata)
    checksums = json.loads((bundle / "checksums.json").read_text())
    checksums["metadata.json"] = sha256(bundle / "metadata.json")
    write_json(bundle / "checksums.json", checksums)
    model = Predictor(bundle, allow_fixture=True)
    result = model.predict(raw)
    assert result["label"] is None and result["status"] == "insufficient_confidence"
    assert result["decision_reason"] == "policy_not_fitted" and not result["policy_fitted"]
    assert result["alternatives"] and result["policy_scope"] == "unspecified"


def test_public_export_preserves_predictions_and_records_the_actual_scope(bundle, raw, tmp_path):
    import numpy as np
    from netembed.browser_calibration import write_policy_bundle
    from netembed.bundle import Predictor

    original = Predictor(bundle, allow_fixture=True)
    policy, _, _ = select_policy(cases(), ["a", "b"], cfg())
    target = tmp_path / "public-policy"
    write_policy_bundle(bundle, target, policy, {"fixture": True}, provenance_key="public_calibration")
    fitted = Predictor(target, allow_fixture=True)
    np.testing.assert_array_equal(original.probabilities([raw]), fitted.probabilities([raw]))
    assert fitted.meta["provenance"]["public_calibration"] == {"fixture": True}
    assert "browser_calibration" not in fitted.meta["provenance"]
    assert fitted.predict(raw)["decision_reason"] == "too_few_packets"
