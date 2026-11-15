"""Software fixtures for the retrospective pilot, never accuracy evidence."""

import copy
from pathlib import Path

import numpy as np
import pytest

from netembed.ipv6_pilot import (
    clean_assessment,
    gates,
    guard,
    read_config,
    selection_families,
    validate_new_rows,
)
from netembed.bundle import sha256, write_json


def cfg():
    return read_config("configs/ipv6-realdata-pilot-v1.json")


def test_new_declaration_adopts_only_three_usable_training_archives(tmp_path):
    c = cfg()
    assert list(c["new_training_archives"]) == ["fresh-yt-01", "fresh-ig-01", "fresh-yt-02"]
    assert sum(c["expected_new_counts"].values()) == 19 and c["seed"] == 17
    path = tmp_path / "changed.json"
    path.write_text(Path("configs/ipv6-realdata-pilot-v1.json").read_text() + " ")
    with pytest.raises(ValueError, match="declaration changed"):
        read_config(path)


def test_verified_legacy_string_family_is_reported_as_numeric_stratum(tmp_path):
    path = tmp_path / "fixture-trial.json"
    write_json(path, {"fixture": True, "role": "selection", "flows": [{"id": "a", "family": "6"}]})
    write_json(tmp_path / "report.json", {"trial_report_sha256": {"fixture-trial": sha256(path)}})
    c = {
        "family_audit_root": str(tmp_path),
        "family_audit_sha256": sha256(tmp_path / "report.json"),
        "selection_trials": ["fixture-trial"],
    }
    families, _ = selection_families(c, [{"id": "a"}])
    assert families == {"a": 6}


def test_training_rows_cannot_change_labels_families_lengths_or_session():
    rows = [
        {
            "id": "browser:fixture:one",
            "label": "youtube",
            "packets": [{"iat_ms": 0, "direction": 1, "payload_bytes": 1230}],
        }
    ]
    family = [{"id": rows[0]["id"], "label": "youtube", "family": 6, "packets": 1}]
    validate_new_rows(rows, family, "fixture")
    for key, value in (("label", "instagram"), ("family", 4), ("packets", 2)):
        altered = copy.deepcopy(family)
        altered[0][key] = value
        with pytest.raises(ValueError, match="mismatch"):
            validate_new_rows(rows, altered, "fixture")
    with pytest.raises(ValueError, match="mismatch"):
        validate_new_rows(rows, family, "other-session")
    with pytest.raises(ValueError, match="duplicated"):
        validate_new_rows(rows * 2, family * 2, "fixture")


@pytest.mark.parametrize(
    "path",
    [
        "data/processed/v2/calibration.jsonl",
        "data/./processed/v2/test.jsonl",
        "artifacts/local/forest-policy-calibration-recovery-v1/rows.json",
        "artifacts/local/family-development-v1/family-train-yt-01-rows.json",
        "artifacts/local/hotspot-family-feasibility-v1/hotspot-train-yt-01-rows.json",
        "artifacts/local/prospective-paired-followup-v1/rows.json",
        "artifacts/local/hotspot-fresh-sessions-v1/fresh-ig-02-rows.json",
    ],
)
def test_pilot_blocks_failed_remaining_calibration_and_final_inputs(path):
    with pytest.raises(ValueError, match="excluded"):
        guard("open", (path, "r", 0))


def test_public_or_local_class_regression_cannot_hide_behind_mean_gain():
    control = {
        "local": {"macro_f1": 0.8, "class_recall": {"youtube": 0.7, "instagram": 0.9}},
        "public": {"macro_f1": 0.9, "class_recall": {"youtube": 0.8, "snapchat": 0.8}},
    }
    candidate = copy.deepcopy(control)
    candidate["local"]["macro_f1"] = 0.82
    assert all(gates(candidate, control, cfg()).values())
    candidate["local"]["class_recall"]["instagram"] = 0.89
    assert not gates(candidate, control, cfg())["local_class_no_regression"]
    candidate = copy.deepcopy(control)
    candidate["local"]["macro_f1"] = 0.82
    candidate["public"]["class_recall"]["snapchat"] = 0.74
    assert not gates(candidate, control, cfg())["public_class_retention"]


def test_requested_and_actual_prefix_lengths_and_missing_family_cell_are_explicit():
    class Model:
        labels = ["youtube", "instagram"]

        def probabilities(self, arrays):
            return np.tile([0.8, 0.2], (len(arrays), 1))

    flows = [np.tile([0, 1, 1230], (n, 1)).astype(np.float32) for n in (5, 30)]
    c = {"budgets": [5, 10, 20, 30], "local_labels": Model.labels}
    report, records = clean_assessment(
        Model(), flows, np.array([0, 1]), ["a", "b"], "local", c, {"a": 4, "b": 6}
    )
    assert len(records) == 5 and report["family_cells"]["instagram:IPv4"]["10"]["recall"] is None
    _, public = clean_assessment(Model(), flows, np.array([0, 1]), ["a", "b"], "public", c)
    assert len(public) == 8
    assert next(r for r in public if r["id"] == "a" and r["requested_budget"] == 30)["observed_packets"] == 5
