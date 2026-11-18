import copy
from datetime import datetime, timezone

import pytest

from netembed.bundle import sha256, write_json
from netembed.paired_study import check_order, read_archive, read_plan, summarize, support


@pytest.mark.parametrize(
    "plan,constant",
    [
        ("prospective-paired-v1", "CONFIG_SHA"),
        ("prospective-paired-followup-v1", "FOLLOWUP_SHA"),
        ("forest-policy-calibration-v1", "CALIBRATION_SHA"),
        ("family-development-v1", "FAMILY_SHA"),
        ("hotspot-family-feasibility-v1", "HOTSPOT_SHA"),
        ("hotspot-fresh-sessions-v1", "FRESH_SHA"),
        ("ipv6-frozen-evaluation-v1", "IPV6_EVALUATION_SHA"),
        ("ipv6-live-policy-v1", "LIVE_POLICY_SHA"),
        ("spotify-data-repair-v1", "SPOTIFY_REPAIR_SHA"),
        ("ten-packet-fresh-v1", "TEN_FRESH_SHA"),
        ("ten-packet-fresh-continuation-v1", "TEN_CONTINUATION_SHA"),
        ("ten-packet-policy-v1", "TEN_POLICY_SHA"),
    ],
)
def test_frozen_plan_bytes_match_archive_binding(plan, constant):
    from netembed import paired_study

    assert sha256(f"configs/{plan}.json") == getattr(paired_study, constant)


def test_status_checks_evidence_and_date_without_loading_models(tmp_path):
    from netembed.paired_study import CONFIG_SHA, collection_status

    cfg = read_plan("configs/prospective-paired-v1.json")
    for i, spec in enumerate(cfg["trials"][:2]):
        rowfile = tmp_path / f"{spec['id']}-rows.json"
        write_json(rowfile, [])
        write_json(
            tmp_path / f"{spec['id']}-archive.json",
            {
                "trial_id": spec["id"],
                "plan_sha256": CONFIG_SHA,
                "status": "usable",
                "session_id": str(i),
                "first_packet_ms": ms(2) + i * 10000,
                "last_packet_ms": ms(2) + i * 10000 + 1000,
                "files": {rowfile.name: sha256(rowfile)},
                "counts": {spec["target"]: 3},
            },
        )
    status = collection_status(tmp_path, cfg, ms(2) + 30000)
    assert status["usable_visits"] == 2
    assert status["earliest_next_local_date"] == "2026-11-03"
    assert status["next_action"] == "blocked_by_schedule_or_prior_slot"
    assert status["candidate_models_loaded"] is False and status["candidate_scoring_run"] is False
    assert collection_status(tmp_path, cfg, ms(3))["next_action"] == "ready_to_prepare"
    write_json(tmp_path / "paired-yt-01-rows.json", ["changed"])
    status = collection_status(tmp_path, cfg, ms(3))
    assert status["slots"][1]["state"] == "integrity_error"
    assert status["next_action"] == "integrity_error"


def test_full_paired_scorer_uses_identical_prefixes_and_freezes_fixture_report(tmp_path, monkeypatch):
    """Constructed software fixture only; no real candidate or fresh capture is scored."""
    import importlib
    import json
    from pathlib import Path
    from types import SimpleNamespace
    import numpy as np
    from netembed.contract import Flow

    monkeypatch.syspath_prepend(str(Path("scripts").resolve()))
    cli = importlib.import_module("paired_capture")
    plan = Path("configs/prospective-paired-v1.json")
    cfg = read_plan(plan)
    cfg["fixture"] = True
    calls = {"prefix": [], "forest": []}

    class FakeModel:
        labels = ["youtube", "instagram", "spotify"]

        def __init__(self, name):
            self.name = name

        def probabilities(self, flows, budget=None):
            assert len(flows) == 1
            raw = flows[0]
            if self.name == "prefix":
                assert budget == len(raw)
            else:
                assert budget is None
            calls[self.name].append(raw.copy())
            return np.array([[0.7, 0.2, 0.1]])

        def predict(self, raw, budget=None):
            return {"label": None, "status": "uncalibrated"}

    monkeypatch.setattr(cli, "models", lambda cfg: {name: FakeModel(name) for name in calls})
    for i, spec in enumerate(cfg["trials"]):
        raw = np.tile([1, 1, 1200], (30, 1))
        raw[0, 0] = 0
        packets = Flow.from_array(raw).model_dump()["packets"]
        rows = [{"id": f"fixture-{i}-{j}", "label": spec["target"], "packets": packets} for j in range(3)]
        file = tmp_path / f"{spec['id']}-rows.json"
        write_json(file, rows)
        start = ms(2 + i // 2) + (i % 2) * 10000
        write_json(
            tmp_path / f"{spec['id']}-archive.json",
            {
                "trial_id": spec["id"],
                "session_id": str(i),
                "status": "usable",
                "plan_sha256": sha256(plan),
                "first_packet_ms": start,
                "last_packet_ms": start + 1000,
                "files": {file.name: sha256(file)},
            },
        )
    monkeypatch.setattr(cli, "get", lambda *args: pytest.fail("scoring must not access capture service"))
    cli.score(SimpleNamespace(), tmp_path, cfg, plan)
    result = json.loads((tmp_path / "comparison.json").read_text())
    assert result["fixture"] is True and result["policy_fitted"] is False
    assert result["default_promoted"] is False
    assert result["metrics"]["primary_paired_difference"] == 0
    assert len(calls["prefix"]) == len(calls["forest"]) == 48
    for left, right in zip(calls["prefix"], calls["forest"]):
        np.testing.assert_array_equal(left, right)
    before = sha256(tmp_path / "comparison.json")
    with pytest.raises(ValueError, match="already frozen"):
        cli.score(SimpleNamespace(), tmp_path, cfg, plan)
    assert sha256(tmp_path / "comparison.json") == before


def ms(day):
    return datetime(2026, 11, day, 10, tzinfo=timezone.utc).timestamp() * 1000


def test_followup_preserves_inherited_archives_and_new_capture_date(tmp_path):
    from netembed.paired_study import validate_archive_plan

    cfg = read_plan("configs/prospective-paired-followup-v1.json")
    assert len(cfg["inherited_archives"]) == 2
    assert cfg["followup_scope"]["maximum_new_sessions"] == 2
    report = {
        "trial_id": "paired-ig-01",
        "plan_sha256": cfg["inherited_archives"]["paired-ig-01"]["plan_sha256"],
    }
    path = tmp_path / "paired-ig-01-archive.json"
    write_json(path, report)
    cfg["inherited_archives"]["paired-ig-01"]["archive_sha256"] = sha256(path)
    validate_archive_plan(tmp_path, "paired-ig-01", report, cfg)
    write_json(path, {**report, "changed": True})
    with pytest.raises(ValueError, match="inherited"):
        validate_archive_plan(tmp_path, "paired-ig-01", report, cfg)


def test_two_date_order_and_duplicate_sessions():
    cfg = read_plan("configs/prospective-paired-v1.json")
    first = {
        "trial_id": "paired-ig-01",
        "status": "usable",
        "session_id": "a",
        "first_packet_ms": ms(2),
        "last_packet_ms": ms(2) + 1000,
    }
    check_order(cfg, "paired-yt-01", [first], ms(2) + 10000, "b")
    with pytest.raises(ValueError, match="two-date"):
        check_order(cfg, "paired-yt-01", [first], ms(3), "b")
    with pytest.raises(ValueError, match="duplicate"):
        check_order(cfg, "paired-yt-01", [first], ms(2) + 10000, "a")
    second = {**first, "trial_id": "paired-yt-01", "session_id": "b"}
    with pytest.raises(ValueError, match="two-date"):
        check_order(cfg, "paired-yt-02", [first, second], ms(2) + 20000, "c")
    check_order(cfg, "paired-yt-02", [first, second], ms(3), "c")
    first["status"] = "unusable_stop"
    with pytest.raises(ValueError, match="stops"):
        check_order(cfg, "paired-yt-01", [first], ms(2) + 10000, "b")


def test_support_does_not_depend_on_model_predictions():
    cfg = read_plan("configs/prospective-paired-v1.json")
    spec = cfg["trials"][0]
    rows = [{"label": "instagram", "packets": [None] * n} for n in (10, 10, 30)]
    support(rows, spec, cfg)
    rows[2]["packets"] = [None] * 20
    with pytest.raises(ValueError, match="support"):
        support(rows, spec, cfg)


def test_freeze_and_archive_tampering(tmp_path):
    cfg = read_plan("configs/prospective-paired-v1.json")
    cfg["minimum_class_recall"] = 0
    write_json(tmp_path / "changed.json", cfg)
    with pytest.raises(ValueError, match="changed"):
        read_plan(tmp_path / "changed.json")
    write_json(tmp_path / "rows.json", [])
    write_json(tmp_path / "trial-archive.json", {"files": {"rows.json": sha256(tmp_path / "rows.json")}})
    read_archive(tmp_path, "trial")
    write_json(tmp_path / "rows.json", ["changed"])
    with pytest.raises(ValueError, match="changed"):
        read_archive(tmp_path, "trial")


def test_session_balancing_does_not_reward_large_visits():
    cfg = read_plan("configs/prospective-paired-v1.json")
    records = []
    for trial, label, n, correct in (
        ("paired-ig-01", "instagram", 20, True),
        ("paired-ig-02", "instagram", 1, False),
        ("paired-yt-01", "youtube", 2, True),
        ("paired-yt-02", "youtube", 2, True),
    ):
        for b in cfg["budgets"]:
            for _ in range(n):
                reply = {"raw_top1": label if correct else "spotify", "accepted_label": None}
                records.append(
                    {
                        "trial": trial,
                        "reference": label,
                        "budget": b,
                        "prefix": reply,
                        "forest": copy.deepcopy(reply),
                    }
                )
    result = summarize(records, cfg)
    assert result["prefix"]["10"]["session_balanced_macro_recall"] == 0.75
    assert result["primary_paired_difference"] == 0
    assert result["descriptive_screen_pass"] is False


def test_scorer_refuses_incomplete_capture_set_before_loading_models(tmp_path, monkeypatch):
    from pathlib import Path
    import importlib
    from types import SimpleNamespace

    monkeypatch.syspath_prepend(str(Path("scripts").resolve()))
    cli = importlib.import_module("paired_capture")
    monkeypatch.setattr(cli, "models", lambda cfg: pytest.fail("must not load/score candidates yet"))
    cfg = read_plan("configs/prospective-paired-v1.json")
    with pytest.raises(FileNotFoundError):
        cli.score(SimpleNamespace(), tmp_path, cfg, Path("configs/prospective-paired-v1.json"))


def test_unfinished_netlog_keeps_bound_capture_pending(tmp_path, monkeypatch):
    import importlib
    from pathlib import Path
    from types import SimpleNamespace

    monkeypatch.syspath_prepend(str(Path("scripts").resolve()))
    cli = importlib.import_module("paired_capture")
    plan_path = Path("configs/prospective-paired-v1.json")
    cfg = read_plan(plan_path)
    trial = "paired-ig-01"
    write_json(
        tmp_path / f"{trial}-intent.json", {"trial_id": trial, "collection_plan_sha256": sha256(plan_path)}
    )
    write_json(tmp_path / f"{trial}-attempt.json", {"plan_sha256": sha256(plan_path), "files": {}})
    attempt_hash = sha256(tmp_path / f"{trial}-attempt.json")
    (tmp_path / f"{trial}-netlog.json").write_text('{"constants":{},\n"events": [\n')
    monkeypatch.setattr(cli, "get", lambda *args: pytest.fail("must retain existing bound session"))
    with pytest.raises(ValueError, match="unterminated"):
        cli.archive(SimpleNamespace(trial=trial), tmp_path, cfg, plan_path)
    assert not (tmp_path / f"{trial}-archive.json").exists()
    assert sha256(tmp_path / f"{trial}-attempt.json") == attempt_hash


def test_processing_failure_is_pending_not_an_unusable_capture(tmp_path, monkeypatch):
    import importlib
    import subprocess
    from pathlib import Path
    from types import SimpleNamespace

    monkeypatch.syspath_prepend(str(Path("scripts").resolve()))
    cli = importlib.import_module("paired_capture")
    plan = Path("configs/prospective-paired-v1.json")
    cfg = read_plan(plan)
    trial = "paired-ig-01"
    write_json(
        tmp_path / f"{trial}-intent.json",
        {"trial_id": trial, "collection_plan_sha256": sha256(plan), "source_bundle": "fixture"},
    )
    write_json(
        tmp_path / f"{trial}-attempt.json",
        {"session_id": "fixture", "plan_sha256": sha256(plan), "files": {}},
    )
    write_json(
        tmp_path / f"{trial}-capture.json",
        {
            "session_id": "fixture",
            "flows": [],
            "counters": {"observation_windows_enabled": False, "drops": 0},
            "evidence_evicted": 0,
        },
    )
    write_json(tmp_path / f"{trial}-timing.json", {})
    write_json(tmp_path / f"{trial}-netlog.json", {})
    monkeypatch.setattr(cli, "read_quic_reference_stream", lambda *a, **k: None)
    monkeypatch.setattr(cli, "validate_snapshot", lambda *a: None)
    monkeypatch.setattr(cli, "observed_packet_bounds", lambda *a: (1, 2))
    monkeypatch.setattr(cli, "check_order", lambda *a: None)
    monkeypatch.setattr(cli, "previous", lambda *a: [])

    def failure(*a, **k):
        raise subprocess.CalledProcessError(1, ["fixture-tool"], stderr=b"fixture resource failure")

    monkeypatch.setattr(cli.subprocess, "run", failure)
    with pytest.raises(ValueError, match="same capture preserved"):
        cli.archive(SimpleNamespace(trial=trial), tmp_path, cfg, plan)
    assert not (tmp_path / f"{trial}-archive.json").exists()
    assert len(list(tmp_path.glob(f"{trial}-processing-error-*.json"))) == 1


def test_completed_policy_reports_failure_not_ready_for_rescoring(tmp_path):
    import json
    from netembed.paired_study import collection_status
    from netembed.bundle import sha256

    cfg = {"trials": [], "workflow": "ten_packet_policy"}
    (tmp_path / "final-predictions.json").write_text("[]")
    (tmp_path / "calibration-decision.json").write_text("{}")
    report = {
        "status": "final_failed_stop",
        "predictions_sha256": sha256(tmp_path / "final-predictions.json"),
        "decision_sha256": sha256(tmp_path / "calibration-decision.json"),
        "archives": {},
    }
    (tmp_path / "final-report.json").write_text(json.dumps(report))
    assert collection_status(tmp_path, cfg, 0)["next_action"] == "final_failed_stop"
    (tmp_path / "final-predictions.json").write_text("[1]")
    assert collection_status(tmp_path, cfg, 0)["next_action"] == "final_report_integrity_error"
    (tmp_path / "final-report.json").write_text(json.dumps({"status": "unknown"}))
    assert collection_status(tmp_path, cfg, 0)["next_action"] == "final_report_integrity_error"
