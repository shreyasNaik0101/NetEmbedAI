"""Constructed protocol tests; never capture or establish genuine model quality."""

from copy import deepcopy
from datetime import datetime
import importlib
from pathlib import Path

import pytest

from netembed.paired_study import check_order, read_plan, support
from netembed.ten_fresh import (
    offline_guard,
    primary_metrics,
    require_session_integrity,
    score_fresh,
    verify_single_session,
)
from netembed.paired_study import collection_status
from netembed.capture import Capture


def config():
    return read_plan("configs/ten-packet-fresh-v1.json")


def records():
    result = []
    for label in ["youtube", "instagram", "spotify"]:
        for i in range(3):
            result.append(
                {
                    "id": label + str(i),
                    "reference": label,
                    "target": label,
                    "candidate": {"top1": label},
                    "control": {"top1": label if label != "spotify" else "youtube"},
                    "native": {"alternatives": [{"label": label, "score": 0.7}], "label": None},
                }
            )
    return result


def test_frozen_three_visits_exact_budget_and_no_thirty_requirement():
    cfg = config()
    assert cfg["budgets"] == [10]
    assert [s["target"] for s in cfg["trials"]] == ["youtube", "instagram", "spotify"]
    support([{"label": "youtube", "packets": [{}] * 10}] * 3, cfg["trials"][0], cfg)
    with pytest.raises(ValueError, match="insufficient"):
        support([{"label": "youtube", "packets": [{}] * 10}] * 2, cfg["trials"][0], cfg)


def test_dates_may_advance_but_session_overlap_and_unusable_stop():
    cfg = config()
    start = datetime.fromisoformat(cfg["declared_utc"]).timestamp() * 1000 + 10000
    prior = {
        "trial_id": cfg["trials"][0]["id"],
        "status": "usable",
        "session_id": "one",
        "first_packet_ms": start,
        "last_packet_ms": start + 1000,
    }
    check_order(cfg, cfg["trials"][1]["id"], [prior], start + 86400000, "two")
    with pytest.raises(ValueError, match="reused"):
        check_order(cfg, cfg["trials"][1]["id"], [prior], start + 2000, "one")
    with pytest.raises(ValueError, match="overlapping"):
        check_order(cfg, cfg["trials"][1]["id"], [prior], start + 500, "two")
    with pytest.raises(ValueError, match="unusable"):
        check_order(cfg, cfg["trials"][1]["id"], [{**prior, "status": "unusable_stop"}], start + 2000, "two")


def test_native_missing_is_not_filled_by_perfect_replay():
    rows = records()
    metrics, gates = primary_metrics(rows, config())
    assert all(gates.values()) and metrics["spotify"]["accepted_labels"] == 0
    rows[-1]["native"] = None
    metrics, gates = primary_metrics(rows, config())
    assert gates["spotify_raw_recall"] and gates["spotify_raw_gain"]
    assert not gates["spotify_native_recall"] and not gates["spotify_native_coverage"]
    assert metrics["spotify"]["native_missing"] == 1


def test_incidental_rows_do_not_inflate_target_support_or_quality():
    rows = records()
    wrong = deepcopy(rows[0])
    wrong.update(target="instagram", candidate={"top1": "spotify"}, native=None)
    metrics, gates = primary_metrics(rows + [wrong], config())
    assert metrics["youtube"]["eligible"] == 3 and all(gates.values())
    rows[0]["candidate"]["top1"] = "spotify"
    _, gates = primary_metrics(rows, config())
    assert not gates["youtube_no_loss"] and not gates["youtube_raw_recall"]


@pytest.mark.parametrize(
    "filename",
    [
        "data/train.jsonl",
        "data/calibration.jsonl",
        "data/test.jsonl",
        "artifacts/local/spotify-data-repair-v1/spotify-dev-01-rows.json",
        "artifacts/local/ten-packet-fresh-v1/excluded-prior-old/capture.json",
        "experiments/spotify-weight-study-v1/decision.json",
    ],
)
def test_scoring_blocks_old_outcomes_and_fitting_inputs(filename):
    with pytest.raises(ValueError):
        offline_guard("open", (filename,), Path("artifacts/local/ten-packet-fresh-v1"), config())


def test_audit_compares_empty_short_input_alternatives(monkeypatch):
    monkeypatch.syspath_prepend(str(Path("scripts").resolve()))
    audit = importlib.import_module("audit_browser_trial")
    assert audit.alternative_difference({"alternatives": []}, {"alternatives": []}) == 0
    with pytest.raises(ValueError, match="inventory"):
        audit.alternative_difference({"alternatives": []}, {"alternatives": [{"label": "x", "score": 1}]})
    assert audit.alternative_difference(
        {"alternatives": [{"label": "x", "score": 0.5}]}, {"alternatives": [{"label": "x", "score": 0.6}]}
    ) == pytest.approx(0.1)


def test_capture_retains_fixed_budget_and_real_event_timing_fields():
    capture = Capture(None)
    capture.reference_enabled = True
    capture.session_id = "software-fixture"
    event = {
        "type": "prediction",
        "flow_id": "fixture",
        "observed_packets": 20,
        "artifact_id": "fixture",
        "label": None,
        "status": "insufficient_confidence",
        "alternatives": [{"label": "spotify", "score": 0.7}],
        "model_packets": 10,
        "model_prefix_limit": 10,
        "model_observation_ms": 3.0,
        "policy_fitted": False,
        "decision_reason": "policy_not_fitted",
        "pipeline_ms": 1.25,
        "queue_ms": 0.5,
        "capture_to_event_ms": 12.0,
        "capture_to_parser_ms": 9.0,
        "capture_timestamp": 100.0,
    }
    capture.emit(event)
    saved = capture.evidence["fixture"]["predictions"][20]
    for key in [
        "model_packets",
        "model_prefix_limit",
        "model_observation_ms",
        "policy_fitted",
        "pipeline_ms",
        "queue_ms",
        "capture_to_event_ms",
        "capture_to_parser_ms",
        "capture_timestamp",
    ]:
        assert saved[key] == event[key]
    assert saved["observed_packets"] == 20
    assert saved["sequence"] > 0 and saved["emitted_at"] > 0


def test_restarted_attempt_blocks_grading_before_models_or_new_capture(tmp_path):
    require_session_integrity(tmp_path)
    (tmp_path / "session-integrity-review.json").write_text("{}")
    with pytest.raises(ValueError, match="integrity review"):
        score_fresh(tmp_path, config(), Path("configs/ten-packet-fresh-v1.json"))
    report = collection_status(tmp_path, config(), 0)
    assert report["next_action"] == "session_integrity_review_required"


def test_session_history_rejects_restarts_and_lost_new_sessions():
    intent = {"baseline_history_ids": ["old1", "old2", "old3"], "baseline_history_evictions": 0}
    status = {
        "session_id": "new",
        "recent_sessions_evicted": 1,
        "recent_sessions": [{"session_id": x} for x in ["old2", "old3", "new"]],
    }
    verify_single_session(intent, status)
    status["recent_sessions"] = [{"session_id": x} for x in ["old3", "another", "new"]]
    status["recent_sessions_evicted"] = 2
    with pytest.raises(ValueError, match="more than once"):
        verify_single_session(intent, status)
    status["recent_sessions_evicted"] = 4
    status["recent_sessions"] = [{"session_id": x} for x in ["old3", "old2", "new"]]
    with pytest.raises(ValueError, match="more than once"):
        verify_single_session(intent, status)
