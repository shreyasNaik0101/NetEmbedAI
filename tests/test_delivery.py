"""Software event fixtures only. No capture interface or latency claim."""

from copy import deepcopy

import pytest
from fastapi.testclient import TestClient

from netembed.api import create_app
from netembed.capture import Capture


def capture(monkeypatch):
    monkeypatch.setattr("netembed.capture.time.time", lambda: 100)
    c = Capture(None)
    c.session_id = "software-session"
    c.emit({"type": "prediction", "capture_timestamp": 99.5})
    c.emit({"type": "observation"})
    return c


def ack(kind="observation", sequence=2, received_at=100.025):
    return {
        "session_id": "software-session",
        "event_type": kind,
        "sequence": sequence,
        "received_at": received_at,
    }


def test_receipt_channels_have_distinct_anchors_and_duplicates_do_not_count(monkeypatch):
    c = capture(monkeypatch)
    assert c.acknowledge(ack())
    assert c.acknowledge(ack("prediction", 1))
    assert list(c.observation_delivery) == pytest.approx([25])
    assert list(c.delivery) == pytest.approx([525])
    assert not c.acknowledge(ack())
    assert len(c.observation_delivery) == 1


@pytest.mark.parametrize(
    "change",
    [
        {"session_id": "previous-session"},
        {"session_id": None},
        {"event_type": "prediction"},
        {"event_type": "packets"},
        {"sequence": True},
        {"sequence": 2.0},
        {"sequence": []},
        {"received_at": float("nan")},
        {"received_at": float("inf")},
        {"received_at": "100.025"},
        {"received_at": True},
        {"received_at": 99},
        {"received_at": 701},
        {"received_at": 10**1000},
    ],
)
def test_invalid_receipt_does_not_consume_pending_evidence(monkeypatch, change):
    c = capture(monkeypatch)
    value = ack()
    value.update(change)
    assert not c.acknowledge(value)
    assert c.acknowledge(ack())
    assert len(c.observation_delivery) == 1 and not c.delivery


def test_receipt_tracking_is_bounded_and_counts_pending_eviction(monkeypatch):
    c = capture(monkeypatch)
    assert c.acknowledge(ack())
    for _ in range(1100):
        c.emit({"type": "observation"})
        assert c.acknowledge(ack(sequence=c.sequence))
    assert len(c.observation_delivery) == 1000
    for _ in range(70):
        c.emit({"type": "observation"})
    assert len(c.observation_delivery_pending) == 64
    assert c.receipt_tracking_evicted["observation"] == 6
    assert c.delivery_pending == {1: 99.5}


def test_websocket_receipts_reach_separate_summary_fields_without_capture():
    app = create_app()
    with TestClient(app) as client:
        assert client.get("/capture/summary").json()["observation_receipt_p95_ms"] is None
        with client.websocket_connect("/capture/events", headers={"origin": "http://localhost:5173"}) as ws:
            c = app.state.capture
            c.session_id = "software-session"
            client.portal.call(c.emit, {"type": "observation", "fixture": True})
            event = ws.receive_json()
            receipt = ack(sequence=event["sequence"], received_at=event["emitted_at"] + 0.025)
            wrong = deepcopy(receipt)
            wrong["session_id"] = "previous-session"
            ws.send_json(wrong)
            ws.send_json(receipt)
            for _ in range(30):
                summary = client.get("/capture/summary").json()
                if summary["observation_receipt_n"]:
                    break
            assert summary["observation_receipt_n"] == 1
            assert summary["observation_receipt_p95_ms"] == pytest.approx(25, abs=0.001)
            assert summary["browser_receipt_n"] == 0
            assert not summary["running"]
