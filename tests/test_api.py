from fastapi.testclient import TestClient
from netembed.api import create_app
from netembed.bundle import Predictor
from netembed.contract import Flow


def test_missing_model_and_no_capture():
    with TestClient(create_app()) as client:
        assert client.get("/health/live").status_code == 200
        assert client.get("/health/ready").status_code == 503
        assert client.get("/capture/status").json()["running"] is False
        assert client.post("/capture/start", json={"interface": "1"}).status_code == 409
        assert client.post("/capture/stop", json={}).status_code == 200
        summary = client.get("/capture/summary").json()
        assert summary["browser_receipt_n"] == 0
        assert summary["browser_receipt_p95_ms"] is None
        evidence = client.get("/capture/local-evaluation").json()
        assert evidence["reference_enabled"] is False and evidence["flows"] == []


def test_api_parity_and_validation(bundle, raw):
    body = Flow.from_array(raw).model_dump()
    with TestClient(create_app(bundle, allow_fixture=True)) as client:
        assert client.get("/health/ready").status_code == 200
        actual = client.post("/predict", json=body).json()
        expected = Predictor(bundle, allow_fixture=True).predict(raw)
        assert actual["alternatives"] == expected["alternatives"]
        assert client.post("/predict-batch", json=[body] * 2).status_code == 200
        assert client.post("/predict-batch", json=[body] * 33).status_code == 422
        assert client.post("/predict", json={"packets": []}).status_code == 422
        assert client.post("/predict", json={**body, "label": "youtube"}).status_code == 422
        assert client.post("/predict", json={**body, "reference": "youtube"}).status_code == 422
        assert client.post("/predict", json={"packets": body["packets"] * 7}).status_code == 422
        assert client.post("/predict", content="x" * 262145).status_code == 413
        assert (
            client.post(
                "/capture/start", json={"interface": "1"}, headers={"Origin": "https://evil.example"}
            ).status_code
            == 403
        )


def test_fixture_cannot_capture(bundle):
    with TestClient(create_app(bundle, allow_fixture=True)) as client:
        r = client.post("/capture/start", json={"interface": "1"})
        assert r.status_code == 409 and "fixture" in r.text


def test_windows_and_assessment_are_idle_until_explicit_capture():
    app = create_app()
    calls = []

    async def start(interface, duration, reference=False, observation_windows=False):
        calls.append((interface, reference, observation_windows))
        return {"running": False}

    with TestClient(app) as client:
        assert client.get("/capture/windows").json()["source"] == "not_started"
        assert client.get("/capture/assessment").json()["flows"] == []
        app.state.capture.start = start
        response = client.post("/capture/start", json={"interface": "9", "observation_windows": True})
        assert response.status_code == 200
    assert calls == [("9", False, True)]


def test_reference_collection_is_explicit_start_option():
    app = create_app()
    calls = []

    async def start(interface, duration, reference=False):
        calls.append((interface, duration, reference))
        return {"running": False}  # Contract stub; no process or interface access.

    with TestClient(app) as client:
        app.state.capture.start = start
        assert client.post("/capture/start", json={"interface": "9"}).status_code == 200
        assert (
            client.post("/capture/start", json={"interface": "9", "reference_check": True}).status_code == 200
        )
    assert calls == [("9", 120, False), ("9", 120, True)]


def test_idle_viewer_expires_and_releases_ownership(monkeypatch):
    import pytest
    from starlette.websockets import WebSocketDisconnect
    import netembed.api as api

    monkeypatch.setattr(api, "VIEWER_IDLE_SECONDS", 0.05)
    app = create_app()
    with TestClient(app) as client:
        for _ in range(2):
            with client.websocket_connect(
                "/capture/events", headers={"Origin": "http://localhost:5173"}
            ) as ws:
                with pytest.raises(WebSocketDisconnect):
                    ws.receive_json()
        assert client.get("/capture/status").json()["session_id"] is None


def test_second_viewer_cannot_take_ownership():
    import pytest
    from starlette.websockets import WebSocketDisconnect

    app = create_app()
    with TestClient(app) as client:
        with client.websocket_connect(
            "/capture/events", headers={"Origin": "http://localhost:5173"}
        ) as first:
            first.send_json({"type": "heartbeat"})
            with pytest.raises(WebSocketDisconnect):
                with client.websocket_connect(
                    "/capture/events", headers={"Origin": "http://localhost:5173"}
                ) as second:
                    try:
                        second.receive_json()
                    except WebSocketDisconnect as error:
                        assert error.code == 4009
                        raise
            assert first.receive_json()["running"] is False
