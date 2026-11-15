"""Constructed process/visit fixtures, never model-quality evidence."""

from datetime import datetime, timezone
import importlib
from pathlib import Path
from types import SimpleNamespace
import json
import os

import pytest

from netembed.browser_sessions import chrome_inventory, require_closed, verify_fresh, validate_inventory
from netembed.bundle import sha256, write_json
from netembed.family_collection import require_coverage, freeze_training
from netembed.paired_study import FRESH_SHA, check_order, collection_status, read_plan


def config():
    return read_plan("configs/hotspot-fresh-sessions-v1.json")


@pytest.mark.skipif(os.name != "nt", reason="native Windows process query; no browser control")
def test_native_windows_process_query_returns_verifiable_lifetimes():
    validate_inventory(chrome_inventory())


def test_fresh_lifetime_requires_restart_before_capture_and_live_proof():
    intent = {"chrome_closed_before_intent": True, "recorded_before_capture_utc": "2026-11-04T13:00:00+00:00"}
    prepared = datetime.fromisoformat(intent["recorded_before_capture_utc"]).timestamp() * 1000
    root = {"pid": 10, "started_unix_ms": prepared + 1000}
    child = {"pid": 11, "started_unix_ms": prepared + 15000}
    verify_fresh([root, child], intent, prepared + 10000)
    for processes, expected in (
        ([{**root, "started_unix_ms": prepared - 1}], "predates"),
        ([child], "after the recorded"),
        ([], "remain open"),
    ):
        with pytest.raises(ValueError, match=expected):
            verify_fresh(processes, intent, prepared + 10000)
    with pytest.raises(ValueError, match="missing closed"):
        verify_fresh([root], {}, prepared + 10000)


def test_open_browser_and_invalid_process_inventory_block_proof():
    require_closed([])
    with pytest.raises(ValueError, match="fully exit Chrome"):
        require_closed([{"pid": 1, "started_unix_ms": 1000}])
    with pytest.raises(ValueError, match="duplicate"):
        validate_inventory([{"pid": 1, "started_unix_ms": 1000}] * 2)
    with pytest.raises(ValueError, match="invalid"):
        validate_inventory([{"pid": 1, "started_unix_ms": float("nan")}])


def test_complete_ipv6_flow_meets_new_rule_without_rewriting_old_minimum():
    values = [{"id": "fixture:one", "label": "youtube", "family": 6, "packets": 30}]
    cfg = config()
    assert require_coverage(values, cfg["trials"][0], cfg) == {"youtube:IPv6": 1}
    old = read_plan("configs/hotspot-family-feasibility-v1.json")
    with pytest.raises(ValueError, match="shortfall"):
        require_coverage(values, old["trials"][0], old)
    values[0]["family"] = 4
    with pytest.raises(ValueError, match="shortfall"):
        require_coverage(values, cfg["trials"][0], cfg)
    values[0]["family"] = 6
    values[0]["packets"] = 29
    with pytest.raises(ValueError, match="at30"):
        require_coverage(values, cfg["trials"][0], cfg)


def test_distinct_sessions_and_dates_finish_without_training_or_scoring(tmp_path):
    cfg = config()
    previous = []
    start = datetime(2026, 11, 5, tzinfo=timezone.utc).timestamp() * 1000
    for i, spec in enumerate(cfg["trials"]):
        first = start + (spec["day"] - 1) * 86400000 + i * 10000
        check_order(cfg, spec["id"], previous, first, str(i))
        file = tmp_path / (spec["id"] + "-fixture.json")
        write_json(file, {"fixture": True})
        report = {
            "trial_id": spec["id"],
            "status": "usable",
            "plan_sha256": FRESH_SHA,
            "session_id": str(i),
            "first_packet_ms": first,
            "last_packet_ms": first + 1000,
            "files": {file.name: sha256(file)},
        }
        write_json(tmp_path / (spec["id"] + "-archive.json"), report)
        previous.append(report)
    assert (
        collection_status(tmp_path, cfg, start + 3 * 86400000)["next_action"]
        == "session_acquisition_complete_no_scoring"
    )
    with pytest.raises(ValueError, match="feasibility scope"):
        freeze_training(tmp_path, cfg, tmp_path / "no-plan.json")


@pytest.mark.parametrize(
    "plan_path",
    [
        "configs/hotspot-fresh-sessions-v1.json",
        "configs/ipv6-frozen-evaluation-v1.json",
        "configs/ipv6-live-policy-v1.json",
        "configs/spotify-data-repair-v1.json",
        "configs/ten-packet-fresh-v1.json",
    ],
)
@pytest.mark.parametrize("browser_open", [True, False])
def test_preparation_checks_chrome_without_starting_capture(tmp_path, monkeypatch, plan_path, browser_open):
    monkeypatch.syspath_prepend(str(Path("scripts").resolve()))
    cli = importlib.import_module("paired_capture")
    import netembed.browser_sessions as sessions

    cfg = read_plan(plan_path)
    # This fixture exercises preparation, not private network-report files.
    cfg.pop("network_context", None)
    declared = datetime.fromisoformat(cfg["declared_utc"]).timestamp()
    monkeypatch.setattr(cli.time, "time", lambda: declared + 60)
    spec = cfg["trials"][0]
    monkeypatch.setattr(cli, "models", lambda cfg: {})

    class Source:
        identity = cfg["source_artifact_id"]

    monkeypatch.setattr(cli, "Predictor", lambda path: Source())

    def get(base, route):
        return json.dumps(
            {
                "/capture/status": {"running": False},
                "/model": {"artifact_id": Source.identity},
                "/capture/interfaces": [{"id": cfg["interface"]}],
            }[route]
        ).encode()

    monkeypatch.setattr(cli, "get", get)
    monkeypatch.setattr(
        sessions, "chrome_inventory", lambda: [{"pid": 7, "started_unix_ms": 1000}] if browser_open else []
    )
    args = SimpleNamespace(trial=spec["id"], service=cfg.get("service_url", "http://127.0.0.1:8001"))
    path = tmp_path / (spec["id"] + "-intent.json")
    if browser_open:
        with pytest.raises(ValueError, match="fully exit"):
            cli.prepare(args, tmp_path, cfg, Path(plan_path))
        assert not path.exists()
    else:
        cli.prepare(args, tmp_path, cfg, Path(plan_path))
        assert json.loads(path.read_text())["chrome_closed_before_intent"] is True
