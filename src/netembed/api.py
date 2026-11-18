"""Local single-owner inference and capture API."""

import asyncio
import json
import os
import time
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Annotated
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, ConfigDict, Field
from .bundle import Predictor
from .capture import Capture, ViewerQueue
from .contract import Flow

VIEWER_IDLE_SECONDS = 15
VIEWER_HEARTBEAT_SECONDS = 3


class Start(BaseModel):
    model_config = ConfigDict(extra="forbid")
    interface: str = Field(pattern=r"^\d{1,4}$")
    duration_seconds: int = Field(default=120, ge=10, le=600)
    reference_check: bool = False
    observation_windows: bool = False


class BodyLimit:
    def __init__(self, app, limit=262144):
        self.app, self.limit = app, limit

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            return await self.app(scope, receive, send)
        chunks, size = [], 0
        while True:
            message = await receive()
            if message["type"] == "http.disconnect":
                return
            size += len(message.get("body", b""))
            if size > self.limit:
                return await JSONResponse({"detail": "body exceeds 256 KiB"}, status_code=413)(
                    scope, receive, send
                )
            chunks.append(message)
            if not message.get("more_body", False):
                break

        async def replay():
            return chunks.pop(0) if chunks else await receive()

        await self.app(scope, replay, send)


def create_app(bundle=None, allow_fixture=False):
    allowed = os.environ.get(
        "NETEMBED_ORIGINS",
        "http://localhost:5173,http://127.0.0.1:5173,http://127.0.0.1:8000,http://localhost:8000",
    ).split(",")

    @asynccontextmanager
    async def lifespan(app):
        app.state.predictor = None
        app.state.model_error = "No model bundle configured"
        try:
            if bundle:
                app.state.predictor = Predictor(bundle, allow_fixture=allow_fixture)
                app.state.model_error = None
        except (OSError, ValueError, KeyError, RuntimeError, TypeError):
            app.state.model_error = "Bundle unavailable or invalid; inspect configured artifact"
        app.state.evaluation = {"status": "pending", "reason": "No verified report configured"}
        report_path = os.environ.get("NETEMBED_EVALUATION")
        if report_path and app.state.predictor is not None:
            try:
                report = json.loads(Path(report_path).read_text())
                if report["artifact_id"] != app.state.predictor.identity:
                    raise ValueError("report belongs to different artifact")
                app.state.evaluation = report
            except (OSError, ValueError, KeyError):
                app.state.evaluation = {
                    "status": "unavailable",
                    "reason": "Report missing, invalid or incompatible",
                }
        app.state.capture = Capture(app.state.predictor)
        app.state.inference_lock = asyncio.Lock()
        yield
        await app.state.capture.stop("service shutdown")

    app = FastAPI(title="NetEmbedAI", version="2", lifespan=lifespan)
    app.add_middleware(
        CORSMiddleware, allow_origins=allowed, allow_methods=["GET", "POST"], allow_headers=["Content-Type"]
    )
    app.add_middleware(BodyLimit)

    @app.middleware("http")
    async def local_control(request, call_next):
        origin = request.headers.get("origin")
        host = request.headers.get("host", "").split(":")[0]
        if host not in ("localhost", "127.0.0.1", "testserver") or (origin and origin not in allowed):
            return JSONResponse({"detail": "local allowed origin required"}, status_code=403)
        return await call_next(request)

    def predictor():
        if app.state.predictor is None:
            raise HTTPException(503, app.state.model_error)
        return app.state.predictor

    @app.get("/health/live")
    def live():
        return {"live": True}

    @app.get("/health/ready")
    def ready():
        predictor()
        return {"ready": True}

    @app.get("/model")
    def model():
        p = predictor()
        return {"artifact_id": p.identity, **p.meta}

    @app.post("/predict")
    async def predict(flow: Flow):
        async with app.state.inference_lock:
            return await asyncio.to_thread(predictor().predict, flow.array())

    @app.post("/predict-batch")
    async def predict_batch(flows: Annotated[list[Flow], Field(min_length=1, max_length=32)]):
        async with app.state.inference_lock:
            return await asyncio.to_thread(lambda: [predictor().predict(f.array()) for f in flows])

    @app.get("/examples")
    def examples():
        return {
            "examples": [],
            "reason": "Import a locally authorized recorded sequence; no samples redistributed",
        }

    @app.get("/evaluation")
    def evaluation():
        predictor()
        return app.state.evaluation

    @app.get("/capture/interfaces")
    async def interfaces():
        try:
            return await app.state.capture.interfaces()
        except (OSError, RuntimeError) as e:
            raise HTTPException(503, str(e)) from e

    @app.get("/capture/status")
    def status():
        return app.state.capture.status()

    @app.post("/capture/start")
    async def start(request: Start):
        try:
            return await app.state.capture.start(
                request.interface,
                request.duration_seconds,
                request.reference_check,
                **({"observation_windows": True} if request.observation_windows else {}),
            )
        except ValueError as e:
            raise HTTPException(422, str(e)) from e
        except (OSError, RuntimeError) as e:
            raise HTTPException(409, str(e)) from e

    @app.post("/capture/stop")
    async def stop():
        return await app.state.capture.stop()

    @app.get("/capture/summary")
    def session_summary():
        return app.state.capture.summary()

    @app.get("/capture/recent-sessions")
    def recent_sessions():
        c = app.state.capture
        return {
            "sessions": c.stopped_sessions(),
            "limit": c.recent_sessions.maxlen,
            "evicted": c.recent_sessions_evicted,
            "storage": "bounded memory; cleared on service exit",
        }

    @app.get("/capture/recent-sessions/{session_id}")
    def saved_session(session_id: str):
        for row in app.state.capture.recent_sessions:
            if row["session_id"] == session_id:
                return row
        raise HTTPException(404, "stopped session unavailable or evicted; no replacement data")

    @app.get("/capture/local-evaluation")
    def local_evaluation():
        return app.state.capture.local_evaluation()

    @app.get("/capture/windows")
    def window_evidence():
        return app.state.capture.window_export()

    @app.get("/capture/assessment")
    def assessment():
        return app.state.capture.assessments()

    @app.websocket("/capture/events")
    async def events(ws: WebSocket):
        if ws.headers.get("origin") not in allowed:
            await ws.close(code=1008)
            return
        c = app.state.capture
        if c.clients:
            # Completing an allowed-origin handshake exposes the reason to the
            # browser. A pre-accept rejection appears as an opaque HTTP403.
            await ws.accept()
            await ws.close(
                code=1013 if c.viewer_cleanup else 4009,
                reason="previous viewer cleanup in progress"
                if c.viewer_cleanup
                else "another app window owns the stream",
            )
            return
        q = ViewerQueue(maxsize=64)
        # Reserve ownership before the handshake yields to another connection.
        c.clients.add(q)
        try:
            await ws.accept()
        except BaseException:
            c.clients.discard(q)
            raise

        async def sender():
            next_heartbeat = time.monotonic() + VIEWER_HEARTBEAT_SECONDS
            while True:
                if time.monotonic() >= next_heartbeat:
                    # A server-driven message wakes the page's socket handler;
                    # browser interval timers may be throttled in hidden tabs.
                    await ws.send_json({"type": "heartbeat"})
                    next_heartbeat = time.monotonic() + VIEWER_HEARTBEAT_SECONDS
                    continue
                try:
                    async with asyncio.timeout(min(2, max(0.001, next_heartbeat - time.monotonic()))):
                        event = await q.get()
                except TimeoutError:
                    if time.monotonic() >= next_heartbeat:
                        continue
                    event = {"type": "status", **c.status()}
                await ws.send_json(event)

        task = asyncio.create_task(sender())
        stop_reason = "viewer disconnected"
        disconnect = {"code": None, "reason": "connection closed", "at": None}
        try:
            while True:
                message = await asyncio.wait_for(ws.receive_text(), timeout=VIEWER_IDLE_SECONDS)
                if len(message) > 1024:
                    stop_reason = "viewer message too large"
                    disconnect.update(code=1009, reason="viewer message too large")
                    await ws.close(code=1009)
                    break
                try:
                    c.acknowledge(json.loads(message))
                except (ValueError, TypeError, AttributeError):
                    pass
        except WebSocketDisconnect as error:
            disconnect.update(code=error.code, reason=(getattr(error, "reason", "") or "")[:160])
        except TimeoutError:
            stop_reason = "viewer heartbeat expired"
            disconnect.update(code=1008, reason="viewer heartbeat expired")
            await ws.close(code=1008, reason="viewer heartbeat expired")
        finally:
            c.viewer_cleanup = True

            async def cleanup_viewer():
                try:
                    task.cancel()
                    await asyncio.gather(task, return_exceptions=True)
                    if c.running:
                        disconnect["at"] = time.time()
                        c.viewer_close = disconnect
                    await c.stop(stop_reason)
                finally:
                    c.clients.discard(q)
                    c.viewer_cleanup = False

            # The websocket handler may be cancelled as its client closes.
            # Keep cleanup running so capture stops before ownership is released.
            await asyncio.shield(cleanup_viewer())

    ui = Path(__file__).resolve().parents[2] / "ui" / "dist"
    if ui.is_dir():
        app.mount("/", StaticFiles(directory=ui, html=True), name="ui")
    return app


app = create_app(os.environ.get("NETEMBED_BUNDLE"))
