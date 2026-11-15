"""Hotspot acquisition fixtures: no actual capture or model-quality evidence."""

from datetime import datetime, timezone
import importlib
from pathlib import Path

import pytest

from netembed.bundle import sha256, write_json
from netembed.family_collection import freeze_training
from netembed.paired_study import HOTSPOT_SHA, collection_status, read_plan, validate_archive_plan


def test_two_visit_scope_ends_without_model_scoring_or_training_freeze(tmp_path):
    cfg = read_plan("configs/hotspot-family-feasibility-v1.json")
    assert len(cfg["trials"]) == 2 and all(s["role"] == "train" for s in cfg["trials"])
    start = datetime(2026, 11, 5, tzinfo=timezone.utc).timestamp() * 1000
    for i, spec in enumerate(cfg["trials"]):
        data = tmp_path / (spec["id"] + "-families.json")
        write_json(data, [{"fixture": True}])
        write_json(
            tmp_path / (spec["id"] + "-archive.json"),
            {
                "trial_id": spec["id"],
                "plan_sha256": HOTSPOT_SHA,
                "status": "usable",
                "session_id": str(i),
                "first_packet_ms": start + i * 10000,
                "last_packet_ms": start + i * 10000 + 1000,
                "files": {data.name: sha256(data)},
            },
        )
    status = collection_status(tmp_path, cfg, start + 30000)
    assert status["next_action"] == "feasibility_complete_no_scoring"
    assert not status["candidate_models_loaded"] and not status["candidate_scoring_run"]
    with pytest.raises(ValueError, match="feasibility scope"):
        freeze_training(tmp_path, cfg, tmp_path / "absent.json")
    assert not (tmp_path / "training-freeze.json").exists()


def test_hotspot_cannot_inherit_closed_campus_archive(tmp_path):
    cfg = read_plan("configs/hotspot-family-feasibility-v1.json")
    with pytest.raises(ValueError, match="another slot or plan"):
        validate_archive_plan(
            tmp_path,
            cfg["trials"][0]["id"],
            {"trial_id": "family-train-yt-01", "plan_sha256": "campus-plan"},
            cfg,
        )


def test_changed_network_proof_blocks_preparation_before_any_service_call(tmp_path, monkeypatch):
    monkeypatch.syspath_prepend(str(Path("scripts").resolve()))
    cli = importlib.import_module("paired_capture")
    cfg = read_plan("configs/hotspot-family-feasibility-v1.json")
    file = tmp_path / "network.json"
    write_json(file, {"fixture": True})
    cfg["network_context"]["connectivity_report"] = str(file)
    cfg["network_context"]["connectivity_report_sha256"] = "changed"
    monkeypatch.setattr(cli, "get", lambda *a: pytest.fail("service must not be called"))
    with pytest.raises(ValueError, match="connectivity evidence changed"):
        cli.prepare(None, tmp_path, cfg, tmp_path / "absent.json")
