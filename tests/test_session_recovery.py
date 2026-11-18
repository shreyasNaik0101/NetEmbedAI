"""Constructed lifecycle tests, never real capture or model-quality evidence."""

import asyncio
from types import SimpleNamespace

from fastapi.testclient import TestClient
from starlette.websockets import WebSocketDisconnect
import pytest

from netembed.api import create_app
from netembed.capture import Capture


def populate(capture, session):
    capture.session_id = session
    capture.running = True
    capture.started_at = 1.0
    capture.reference_enabled = True
    capture.emit(
        {
            "type": "packets",
            "flow_id": "fixture-flow",
            "packets": [{"iat_ms": 0, "direction": 1, "payload_bytes": 100}],
            "reference": {"status": "unavailable", "label": None},
        }
    )
    capture.events.append({"pipeline_ms": 1, "queue_ms": 2})
    capture.delivery.append(4.0)


def test_stopped_snapshots_survive_new_sessions_are_independent_and_bounded():
    async def run():
        c = Capture(SimpleNamespace(identity="fixture", meta={"provenance": {"fixture": True}}))
        for i in range(4):
            populate(c, str(i))
            c.viewer_close = {"code": 1008, "reason": "viewer heartbeat expired"}
            await c.stop("viewer heartbeat expired")
            assert len(c.recent_sessions) == min(3, i + 1)
            await c.stop("duplicate stop")
            assert len(c.recent_sessions) == min(3, i + 1)
            c.evidence["fixture-flow"]["packets"][0]["payload_bytes"] = 999
            c.evidence.clear()
            c.events.clear()
            c.delivery.clear()
        assert c.recent_sessions_evicted == 1
        assert [r["session_id"] for r in c.recent_sessions] == ["1", "2", "3"]
        for row in c.recent_sessions:
            assert row["capture"]["fixture"] is True
            assert row["capture"]["flows"][0]["packets"][0]["payload_bytes"] == 100
            assert row["timing"]["browser_receipt_p50_ms"] == 4
            assert row["timing"]["timing_samples"] == [{"pipeline_ms": 1, "queue_ms": 2}]
            assert row["status"]["reason"] == "viewer heartbeat expired"
            assert row["status"]["viewer_close"]["code"] == 1008
        assert c.stopped_sessions()[0]["retained_packets"] == 1

    asyncio.run(run())


def test_recovery_endpoints_are_read_only_and_do_not_start_capture(bundle):
    with TestClient(create_app(bundle, allow_fixture=True)) as client:
        assert client.get("/capture/recent-sessions").json()["sessions"] == []
        capture = client.app.state.capture
        populate(capture, "software-fixture")
        result = client.post("/capture/stop", json={})
        assert result.status_code == 200
        recent = client.get("/capture/recent-sessions").json()
        assert recent["limit"] == 3 and len(recent["sessions"]) == 1
        saved = client.get("/capture/recent-sessions/software-fixture").json()
        assert saved["session_id"] == "software-fixture"
        assert saved["capture"]["fixture"] is True
        assert not saved["status"]["running"]
        assert client.get("/capture/recent-sessions/missing").status_code == 404
        assert not client.get("/capture/status").json()["running"]


def test_heartbeat_expiry_is_distinct_and_preserved(bundle, monkeypatch):
    import netembed.api as api

    monkeypatch.setattr(api, "VIEWER_IDLE_SECONDS", 0.01)
    with TestClient(create_app(bundle, allow_fixture=True)) as client:
        populate(client.app.state.capture, "expired-fixture")
        with client.websocket_connect("/capture/events", headers={"Origin": "http://localhost:5173"}) as ws:
            with pytest.raises(WebSocketDisconnect) as error:
                while True:
                    ws.receive_json()
            assert error.value.code == 1008
        saved = client.get("/capture/recent-sessions/expired-fixture").json()
        assert saved["status"]["reason"] == "viewer heartbeat expired"
        assert saved["status"]["viewer_close"]["code"] == 1008
        assert not client.get("/capture/status").json()["running"]


@pytest.mark.parametrize("_iteration", range(8))
def test_server_heartbeat_keeps_timerless_viewer_alive_and_releases_on_close(monkeypatch, _iteration):
    import time
    import netembed.api as api

    monkeypatch.setattr(api, "VIEWER_IDLE_SECONDS", 0.15)
    monkeypatch.setattr(api, "VIEWER_HEARTBEAT_SECONDS", 0.02)
    with TestClient(create_app()) as client:
        with client.websocket_connect("/capture/events", headers={"Origin": "http://localhost:5173"}) as ws:
            deadline = time.monotonic() + 0.35
            replies = 0
            while time.monotonic() < deadline:
                message = ws.receive_json()
                if message["type"] == "heartbeat":
                    ws.send_json({"type": "heartbeat"})
                    replies += 1
            assert replies >= 3
            assert client.get("/capture/status").json()["viewer_connected"]
            assert not client.get("/capture/status").json()["running"]
        # Closing the client starts server cleanup asynchronously. Wait for
        # ownership to be released before asking a new viewer to connect.
        deadline = time.monotonic() + 2
        while client.get("/capture/status").json()["viewer_connected"]:
            assert time.monotonic() < deadline, "viewer ownership was not released"
            time.sleep(0.01)
        with client.websocket_connect("/capture/events", headers={"Origin": "http://localhost:5173"}) as ws:
            # A queued status is legitimate after the previous viewer's stop.
            # Ownership release must not depend on which message arrives first.
            while ws.receive_json()["type"] != "heartbeat":
                pass


def test_unresponsive_viewer_expires_despite_server_heartbeats(bundle, monkeypatch):
    import netembed.api as api

    monkeypatch.setattr(api, "VIEWER_IDLE_SECONDS", 0.08)
    monkeypatch.setattr(api, "VIEWER_HEARTBEAT_SECONDS", 0.01)
    with TestClient(create_app(bundle, allow_fixture=True)) as client:
        populate(client.app.state.capture, "unresponsive-fixture")
        with client.websocket_connect("/capture/events", headers={"Origin": "http://localhost:5173"}) as ws:
            with pytest.raises(WebSocketDisconnect) as error:
                while True:
                    ws.receive_json()
            assert error.value.code == 1008
        assert not client.get("/capture/status").json()["running"]
        saved = client.get("/capture/recent-sessions/unresponsive-fixture").json()
        assert saved["status"]["reason"] == "viewer heartbeat expired"
