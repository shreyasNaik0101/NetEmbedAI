"""Constructed acceptance-policy contracts; no traffic collection or quality claims."""

from copy import deepcopy
from pathlib import Path

import pytest

from netembed.ten_policy import offline_guard, select_policy, summarize, frozen_policy


def config():
    return {
        "labels": ["youtube", "instagram", "spotify", "other"],
        "local_labels": ["youtube", "instagram", "spotify"],
        "source_bundle": "experiments/spotify-ten-packet-v1/bundle",
        "minimum_target_at_10_per_trial": 3,
        "policy_rules": {
            "minimum_accepted_per_service": 2,
            "minimum_coverage": 0.5,
            "maximum_primary_error": 0,
            "maximum_overall_error": 0.1,
        },
    }


def records():
    rows = []
    labels = config()["labels"]
    for i, label in enumerate(labels[:3]):
        for j in range(3):
            scores = [0.05] * 4
            if j < 2:
                scores[i] = 0.85
            else:
                scores[i] = 0.3
                scores[(i + 1) % 3] = 0.6
            top = labels[scores.index(max(scores))]
            rows.append(
                {
                    "id": f"{label}{j}",
                    "target": label,
                    "reference": label,
                    "top1": top,
                    "probabilities": scores,
                    "native": None,
                }
            )
    return rows


def test_lowest_eligible_threshold_and_acceptance_scope():
    policy, chosen, curve = select_policy(records(), config())
    assert policy["fitted"] and policy["threshold"] == 0.61
    assert policy["accepted_labels"] == config()["local_labels"]
    assert len(curve) == 101 and chosen["eligible"]
    assert all(s["accepted"] == 2 and s["errors"] == 0 for s in chosen["primary"].values())


def test_infeasible_fit_withholds_labels_and_never_relaxes_gate():
    values = records()
    for row in values:
        if row["top1"] != row["reference"]:
            target = config()["labels"].index(row["top1"])
            row["probabilities"] = [0, 0, 0, 0]
            row["probabilities"][target] = 1
    policy, selected, _ = select_policy(values, config())
    assert not policy["fitted"] and selected is None
    assert policy["threshold"] == 1


def test_missing_native_is_not_replaced_by_offline_predictions():
    assert summarize(records(), 0.61, config())["eligible"]
    native = summarize(records(), 0.61, config(), native=True)
    assert not native["eligible"]
    assert native["overall"]["accepted"] == 0
    assert native["overall"]["accepted_error"] is None


@pytest.mark.parametrize("change", ["duplicate", "nan", "wrong_top", "wrong_length"])
def test_invalid_fitting_records_rejected(change):
    values = deepcopy(records())
    if change == "duplicate":
        values.append(values[0])
    elif change == "nan":
        values[0]["probabilities"][0] = float("nan")
    elif change == "wrong_top":
        values[0]["top1"] = "spotify"
    else:
        values[0]["probabilities"].append(0)
    with pytest.raises(ValueError):
        select_policy(values, config())


@pytest.mark.parametrize(
    "path",
    [
        "data/processed/v2/calibration.jsonl",
        "data/processed/v2/test.jsonl",
        "artifacts/local/ten-packet-fresh-continuation-v1/ten-cont-sp-01-rows.json",
        "artifacts/local/ten-packet-policy-v1/ten-policy-final-sp-01-archive.json",
        "artifacts/local/ten-packet-policy-v1/excluded-prior-old/capture.json",
        "experiments/spotify-weight-study-v1/decision.json",
    ],
)
def test_fit_guard_excludes_public_old_and_final_data(path):
    with pytest.raises(ValueError):
        offline_guard("open", (path,), Path("artifacts/local/ten-packet-policy-v1"), config(), "calibration")


def test_fit_guard_allows_only_current_calibration_and_source():
    root = Path("artifacts/local/ten-packet-policy-v1")
    for name in [
        root / "ten-policy-cal-sp-01-rows.json",
        root / "calibration-curve.json",
        Path(config()["source_bundle"]) / "forest.json",
    ]:
        offline_guard("open", (str(name),), root, config(), "calibration")
    with pytest.raises(ValueError, match="offline"):
        offline_guard("socket.connect", (), root, config(), "calibration")


def test_final_requires_a_frozen_policy_before_any_rows(tmp_path):
    with pytest.raises(FileNotFoundError):
        frozen_policy(tmp_path, config())


@pytest.mark.parametrize("problem", ["fixture", "heartbeat", "drops", "pending_receipt"])
def test_role_loader_rejects_dirty_sessions_before_reading_flow_rows(tmp_path, monkeypatch, problem):
    import json
    from datetime import datetime
    import netembed.ten_policy as policy
    from netembed.paired_study import read_plan

    cfg = read_plan("configs/ten-packet-policy-v1.json")
    trial = cfg["trials"][0]["id"]
    start = datetime.fromisoformat(cfg["declared_utc"]).timestamp() * 1000 + 1000
    report = {
        "trial_id": trial,
        "collection_role": "calibration",
        "status": "usable",
        "session_id": "constructed",
        "first_packet_ms": start,
        "last_packet_ms": start + 1000,
    }
    monkeypatch.setattr(policy, "read_archive", lambda *_: report)
    monkeypatch.setattr(policy, "validate_archive_plan", lambda *_: None)
    capture = {
        "fixture": problem == "fixture",
        "source": "user_started_capture",
        "evidence_evicted": False,
        "counters": {"drops": 1 if problem == "drops" else 0},
    }
    status = {
        "running": False,
        "reason": "viewer heartbeat expired" if problem == "heartbeat" else "stopped by user",
    }
    timing = {
        "receipt_tracking_pending": {"prediction": int(problem == "pending_receipt")},
        "receipt_tracking_evicted": {"prediction": 0},
    }
    for name, value in [("capture", capture), ("status", status), ("timing", timing)]:
        (tmp_path / (trial + "-" + name + ".json")).write_text(json.dumps(value))
    with pytest.raises(ValueError, match="uninterrupted"):
        policy.role_records(tmp_path, cfg, "calibration", None)
