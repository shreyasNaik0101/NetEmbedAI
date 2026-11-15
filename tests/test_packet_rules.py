"""Constructed packet/rule fixtures; never benchmark or live validation evidence."""

import copy

import numpy as np
import pytest

from netembed.bundle import Predictor
from netembed.packet_rules import PacketRules, describe, length_bucket, weighted_quantile


def fixture_training(identical=False):
    flows, labels, ids = [], [], []
    for label in (0, 1):
        for flow in range(3):
            for budget in (5, 10, 20, 30):
                x = np.zeros((budget, 3), dtype=np.float32)
                x[1:, 0] = 1 if label == 0 or identical else 20
                x[:, 1] = 1
                x[:, 2] = 100 + flow if label == 0 or identical else 1400 + flow
                flows.append(x)
                labels.append(label)
                ids.append(f"software-fixture:{label}:{flow}")
    return flows, labels, np.ones(len(flows)), ids


def fitted(identical=False):
    flows, y, weights, ids = fixture_training(identical)
    return PacketRules.fit(
        flows, y, weights, ids, ["fixture-a", "fixture-b"], provenance={"fixture": True}
    ), flows


def test_descriptor_units_direction_and_zero_duration():
    raw = np.array([[0, 1, 1000], [2, -1, 500], [198, 1, 100]], dtype=np.float32)
    result = describe(raw)
    np.testing.assert_allclose(
        result[[0, 1, 2, 3, 4, 7, 8, 9]],
        [3 / 30, 2 / 3, 1100 / 1600, 1 / 3, 1, np.log1p(200), np.log1p(100), 0.5],
    )
    assert np.isfinite(describe([[0, 1, 1250]])).all()


def test_training_weighted_quantile_and_invalid_weight():
    assert weighted_quantile([1, 10, 20], [1, 8, 1], 0.5) == 10
    assert weighted_quantile([1, 10], [1, 1], 0.5) == 1
    with pytest.raises(ValueError):
        weighted_quantile([1], [0], 0.5)


def test_unique_rule_match_and_overlapping_rules_abstain():
    rules, flows = fitted()
    assert rules.predict(flows[0])["rule_label"] == "fixture-a"
    ambiguous, flows = fitted(identical=True)
    reply = ambiguous.predict(flows[0])
    assert reply["rule_label"] is None and len(reply["matching_profiles"]) == 2
    assert reply["nearest_label"] == "fixture-a"  # Saved class order breaks a tie.
    assert reply["status"] == "no_unique_profile_match"
    assert rules.predict(flows[0][:1])["status"] == "insufficient_evidence"


def test_observed_length_not_requested_cap_selects_profile_and_future_is_unread():
    assert [length_bucket(n) for n in (1, 3, 5, 6, 16, 20, 23, 30)] == [5, 5, 5, 10, 20, 20, 30, 30]
    rules, flows = fitted()
    full = flows[3].copy()
    first = rules.predict(full[:5])
    full[5:, :] = [9000, -1, 65000]
    assert rules.predict(full[:5]) == first
    assert rules.predict(full[:3])["length_bucket"] == 5


def test_distinct_flow_support_does_not_count_repeated_prefixes_as_new_flows():
    flows, y, weights, _ = fixture_training()
    ids = [f"software-fixture:{label}" for label in y]
    with pytest.raises(ValueError, match="saved packet-rule parameters"):
        PacketRules.fit(flows, y, weights, ids, ["fixture-a", "fixture-b"], provenance={"fixture": True})


def test_saved_rules_reproduce_without_any_fit_or_dataset_access(tmp_path, monkeypatch):
    rules, flows = fitted()
    before = copy.deepcopy(rules.doc)
    reply = rules.predict(flows[0])
    rules.save(tmp_path / "rules")
    monkeypatch.setattr(PacketRules, "fit", lambda *a, **k: pytest.fail("inference fitted data"))
    with pytest.raises(ValueError, match="software fixture"):
        PacketRules.load(tmp_path / "rules")
    loaded = PacketRules.load(tmp_path / "rules", allow_fixture=True)
    assert loaded.predict(flows[0]) == reply and rules.doc == before
    assert all("distance" in r and "score" not in r for r in reply["alternatives"])
    with pytest.raises(ValueError, match="bundle file inventory"):
        Predictor(tmp_path / "rules", allow_fixture=True)
    with (tmp_path / "rules/rules.json").open("ab") as target:
        target.write(b" ")
    with pytest.raises(ValueError, match="checksum"):
        PacketRules.load(tmp_path / "rules", allow_fixture=True)


def test_saved_units_and_nonfinite_parameters_are_refused():
    rules, _ = fitted()
    bad = copy.deepcopy(rules.doc)
    bad["features"]["direction"] = "0/1"
    with pytest.raises(ValueError, match="feature contract"):
        PacketRules(bad)
    bad = copy.deepcopy(rules.doc)
    bad["profiles"]["5"]["scale"][0] = 0
    with pytest.raises(ValueError, match="saved packet-rule parameters"):
        PacketRules(bad)
