"""Bounded TShark metadata pipeline. Construction never starts capture."""

import asyncio
import ipaddress
import os
import re
import secrets
import time
import uuid
from copy import deepcopy
from collections import OrderedDict, deque
from dataclasses import dataclass, field
from .contract import Flow, Packet, BUDGETS
from .observation_windows import ObservationWindows, VERSION as WINDOW_VERSION
from .traffic_assessment import assess
from .service_reference import MAP_SHA256, MAP_SOURCE, attribute, merge_reference, rules, summarize
from .connection_reference import VERSION, connection_token

ADAPTER_VERSION = "tshark-prefix-ns-v3"

FIELDS = [
    "frame.time_epoch",
    "ip.src",
    "ipv6.src",
    "ip.dst",
    "ipv6.dst",
    "udp.srcport",
    "udp.dstport",
    "udp.length",
    "frame.cap_len",
    "frame.len",
    "frame.protocols",
    "quic.long.packet_type",
    "quic.version",
    "ip.frag_offset",
    "ip.flags.mf",
    "ipv6.fraghdr",
]
REFERENCE_FIELDS = [
    "tls.handshake.extensions_server_name",
    "tls.ech.client_hello_type",
    "tls.esni.encrypted_sni",
]


def tshark_path():
    return os.environ.get(
        "NETEMBED_TSHARK", "C:/Program Files/Wireshark/tshark.exe" if os.name == "nt" else "tshark"
    )


def field_args(reference=False):
    return ["-n", "-l", "-T", "fields", "-E", "separator=\t", "-E", "occurrence=f", "-E", "quote=n"] + [
        a for f in FIELDS + (REFERENCE_FIELDS if reference else []) for a in ("-e", f)
    ]


@dataclass
class Observation:
    timestamp: float
    timestamp_ns: int
    src: tuple
    dst: tuple
    size: int
    initial: bool
    reference: dict | None = None


def parse_line(line, reference=False):
    values = line.rstrip("\r\n").split("\t")
    if len(values) != len(FIELDS) + (len(REFERENCE_FIELDS) if reference else 0):
        raise ValueError("malformed field count")
    ref = attribute(values[-3], bool(values[-2] or values[-1])) if reference else None
    t, ip4s, ip6s, ip4d, ip6d, sp, dp, size, cap, wire, protocols, packet_type, version, offset, mf, frag6 = (
        values[: len(FIELDS)]
    )
    if "quic" not in protocols.split(":") or "_ws.malformed" in protocols:
        raise ValueError("not verified QUIC")
    if int(cap) != int(wire) or int(offset or 0) or mf == "1" or frag6:
        raise ValueError("truncated or fragmented datagram unsupported")
    clock = re.fullmatch(r"([0-9]{1,12})(?:\.([0-9]{1,9}))?", t)
    if clock is None:
        raise ValueError("invalid timestamp")
    # Subtract integer timestamps before conversion: epoch-sized floats lose
    # sub-microsecond gaps and can conceal nanosecond packet reordering.
    timestamp_ns = int(clock[1]) * 1000000000 + int((clock[2] or "").ljust(9, "0"))
    timestamp = timestamp_ns / 1000000000
    src = (str(ipaddress.ip_address(ip4s or ip6s)), int(sp))
    dst = (str(ipaddress.ip_address(ip4d or ip6d)), int(dp))
    if not (1 <= src[1] <= 65535 and 1 <= dst[1] <= 65535):
        raise ValueError("invalid UDP port")
    payload = int(size) - 8
    if not 1 <= payload <= 65527 or int(size) > int(wire):
        raise ValueError("invalid UDP length")
    # v1 Initial=0, v2 Initial=1. Restrict new flows to destination UDP/443.
    ver = int(version, 0) if version else None
    initial = dst[1] == 443 and (
        (ver == 1 and packet_type == "0") or (ver == 0x6B3343CF and packet_type == "1")
    )
    return Observation(timestamp, timestamp_ns, src, dst, payload, initial, ref)


@dataclass
class State:
    origin: tuple
    last_timestamp_ns: int
    touched: float
    id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
    packets: list = field(default_factory=list)
    reference: dict | None = None
    first_timestamp_ns: int | None = None
    windows: ObservationWindows | None = None


class FlowTable:
    def __init__(self, limit=256, idle_seconds=65, observation_windows=False):
        self.limit, self.idle_seconds = limit, idle_seconds
        self.observation_windows = observation_windows
        self.states = OrderedDict()
        self.counters = {"ignored": 0, "evicted": 0, "frozen": 0, "reordered": 0}

    def ingest(self, obs, now=None):
        now = time.monotonic() if now is None else now
        for key in list(self.states):
            if now - self.states[key].touched > self.idle_seconds:
                del self.states[key]
                self.counters["evicted"] += 1
        key = tuple(sorted((obs.src, obs.dst)))
        state = self.states.get(key)
        if state is None:
            if not obs.initial:
                self.counters["ignored"] += 1
                return None
            if len(self.states) >= self.limit:
                self.states.popitem(last=False)
                self.counters["evicted"] += 1
            state = State(obs.src, obs.timestamp_ns, now, first_timestamp_ns=obs.timestamp_ns)
            if self.observation_windows:
                state.windows = ObservationWindows(obs.timestamp_ns, now)
            self.states[key] = state
        self.states.move_to_end(key)
        state.touched = now
        state.reference = merge_reference(state.reference, obs.reference)
        if state.windows is not None:
            state.windows.add(obs.timestamp_ns, 1 if obs.src == state.origin else -1, obs.size)
        if len(state.packets) >= 30:
            self.counters["frozen"] += 1
            return None
        if obs.timestamp_ns < state.last_timestamp_ns:
            self.counters["reordered"] += 1
            return None
        packet = Packet(
            iat_ms=(obs.timestamp_ns - state.last_timestamp_ns) / 1000000 if state.packets else 0,
            direction=1 if obs.src == state.origin else -1,
            payload_bytes=obs.size,
        )
        state.last_timestamp_ns = obs.timestamp_ns
        state.packets.append(packet)
        return state


class ViewerQueue:
    """Bounded single-viewer queue; cumulative packet snapshots can supersede."""

    def __init__(self, maxsize=64):
        if maxsize < 1:
            raise ValueError("viewer capacity must be positive")
        self.maxsize = maxsize
        self.items = deque()
        self.ready = asyncio.Event()

    def qsize(self):
        return len(self.items)

    def empty(self):
        return not self.items

    def full(self):
        return len(self.items) >= self.maxsize

    def put_nowait(self, event):
        if self.full():
            raise asyncio.QueueFull
        self.items.append(event)
        self.ready.set()

    def get_nowait(self):
        if not self.items:
            raise asyncio.QueueEmpty
        event = self.items.popleft()
        if not self.items:
            self.ready.clear()
        return event

    async def get(self):
        while True:
            try:
                return self.get_nowait()
            except asyncio.QueueEmpty:
                await self.ready.wait()

    def offer(self, event):
        kind = event.get("type")
        if kind == "packets":
            for i, old in enumerate(self.items):
                if old.get("type") == "packets" and old.get("flow_id") == event.get("flow_id"):
                    self.items[i] = event
                    return True, None
        dropped = None
        if self.full():
            packet_index = next((i for i, old in enumerate(self.items) if old.get("type") == "packets"), None)
            if packet_index is not None:
                dropped = self.items[packet_index].get("type")
                del self.items[packet_index]
            elif kind != "prediction":
                return False, kind or "other"
            else:
                # Prefer a status/window event over an actual model checkpoint.
                low_index = next(
                    (i for i, old in enumerate(self.items) if old.get("type") != "prediction"), 0
                )
                dropped = self.items[low_index].get("type", "other")
                del self.items[low_index]
        self.put_nowait(event)
        return False, dropped


class Capture:
    def __init__(self, predictor, queue_size=64):
        self.predictor = predictor
        self.process = None
        self.tasks = []
        self.lock = asyncio.Lock()
        self.table = FlowTable()
        self.pending = OrderedDict()
        self.wake = asyncio.Event()
        self.queue_size = queue_size
        self.clients = set()
        self.viewer_cleanup = False
        self.errors = deque(maxlen=8)
        self.session_id = None
        self.sequence = 0
        self.drops = 0
        self.coalesced = 0
        self.packet_updates_coalesced = 0
        self.inference_queue_drops = 0
        self.viewer_event_drops = {k: 0 for k in ("packets", "prediction", "status", "observation", "other")}
        self.running = False
        self.last_client = time.monotonic()
        self.reason = "idle"
        self.events = deque(maxlen=1000)
        self.delivery_pending = OrderedDict()
        self.delivery = deque(maxlen=1000)
        self.observation_delivery_pending = OrderedDict()
        self.observation_delivery = deque(maxlen=1000)
        self.receipt_tracking_evicted = {"prediction": 0, "observation": 0}
        self.reference_enabled = False
        self.evidence = OrderedDict()
        self.evidence_evicted = 0
        self.match_salt = None
        self.selected_interface_id = None
        self.window_enabled = False
        self.window_evidence = OrderedDict()
        self.window_evidence_evicted = 0
        self.recent_sessions = deque(maxlen=3)
        self.recent_sessions_evicted = 0
        self.started_at = self.stopped_at = None
        self.viewer_close = None

    def stopped_sessions(self):
        return [
            {
                "session_id": row["session_id"],
                "reason": row["status"]["reason"],
                "connections": len(row["capture"]["flows"]),
                "retained_packets": sum(len(f["packets"]) for f in row["capture"]["flows"]),
                "started_at": row["status"]["started_at"],
                "stopped_at": row["status"]["stopped_at"],
            }
            for row in reversed(self.recent_sessions)
        ]

    def retain_stopped_session(self):
        if not self.session_id or any(row["session_id"] == self.session_id for row in self.recent_sessions):
            return
        if len(self.recent_sessions) == self.recent_sessions.maxlen:
            self.recent_sessions_evicted += 1
        self.recent_sessions.append(
            deepcopy(
                {
                    "session_id": self.session_id,
                    "capture": self.local_evaluation(),
                    "timing": self.summary(),
                    "status": self.status(),
                }
            )
        )

    def summary(self):
        samples = list(self.delivery)
        window_samples = list(self.observation_delivery)
        # Import locally to keep capture construction lightweight.
        import numpy as np

        return {
            **self.status(),
            "timing_samples": list(self.events),
            "capture_to_browser_receipt_ms": samples,
            "browser_receipt_n": len(samples),
            "browser_receipt_p50_ms": float(np.percentile(samples, 50)) if samples else None,
            "browser_receipt_p95_ms": float(np.percentile(samples, 95)) if samples else None,
            "observation_emit_to_browser_receipt_ms": window_samples,
            "observation_receipt_n": len(window_samples),
            "observation_receipt_p50_ms": float(np.percentile(window_samples, 50))
            if window_samples
            else None,
            "observation_receipt_p95_ms": float(np.percentile(window_samples, 95))
            if window_samples
            else None,
            "receipt_tracking_evicted": dict(self.receipt_tracking_evicted),
            "receipt_tracking_pending": {
                "prediction": len(self.delivery_pending),
                "observation": len(self.observation_delivery_pending),
            },
            "receipt_timing_basis": "same-host wall clocks; prediction from checkpoint packet, observation from server emission; neither measures paint",
            "quality": "unverified; trial context is not a per-flow label",
        }

    async def interfaces(self):
        p = await asyncio.create_subprocess_exec(
            tshark_path(), "-D", stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
        )
        try:
            out, err = await asyncio.wait_for(p.communicate(), 10)
        except TimeoutError:
            p.kill()
            await p.wait()
            raise RuntimeError("interface listing timed out")
        if p.returncode:
            raise RuntimeError("TShark interface listing failed; check Npcap/permissions")
        return [
            {"id": m[1], "description": m[2]}
            for line in out.decode(errors="replace").splitlines()
            if (m := re.match(r"^(\d+)\. (.+)$", line))
        ]

    def status(self):
        return {
            "running": self.running,
            "viewer_connected": bool(self.clients),
            "viewer_cleanup": self.viewer_cleanup,
            "reason": self.reason,
            "started_at": self.started_at,
            "stopped_at": self.stopped_at,
            "viewer_close": self.viewer_close,
            "recent_sessions": self.stopped_sessions(),
            "recent_sessions_evicted": self.recent_sessions_evicted,
            "session_id": self.session_id,
            "source": "capture",
            "adapter_version": ADAPTER_VERSION,
            "selected_interface_id": self.selected_interface_id,
            "active_flows": len(self.table.states),
            "backlog": len(self.pending),
            "drops": self.drops,
            "coalesced": self.coalesced,
            "packet_updates_coalesced": self.packet_updates_coalesced,
            "inference_queue_drops": self.inference_queue_drops,
            "viewer_event_drops": dict(self.viewer_event_drops),
            "reference_enabled": self.reference_enabled,
            "observation_windows_enabled": self.window_enabled,
            **self.table.counters,
            "stderr_lines": len(self.errors),
            "error_detail": self.errors[-1].strip() if self.errors and not self.running else None,
        }

    def emit(self, event):
        self.sequence += 1
        event = {
            "schema_version": "1",
            "source": "capture",
            "adapter_version": ADAPTER_VERSION,
            "session_id": self.session_id,
            "sequence": self.sequence,
            "emitted_at": time.time(),
            **event,
        }
        if event.get("type") == "prediction":
            self.delivery_pending[self.sequence] = event["capture_timestamp"]
            if len(self.delivery_pending) > 64:
                self.delivery_pending.popitem(last=False)
                self.receipt_tracking_evicted["prediction"] += 1
        elif event.get("type") == "observation":
            self.observation_delivery_pending[self.sequence] = event["emitted_at"]
            if len(self.observation_delivery_pending) > 64:
                self.observation_delivery_pending.popitem(last=False)
                self.receipt_tracking_evicted["observation"] += 1
        if self.reference_enabled and event.get("type") in ("packets", "prediction"):
            ident = event["flow_id"]
            if ident not in self.evidence:
                if len(self.evidence) >= 256:
                    self.evidence.popitem(last=False)
                    self.evidence_evicted += 1
                self.evidence[ident] = {"flow_id": ident, "packets": [], "predictions": {}}
            record = self.evidence[ident]
            self.evidence.move_to_end(ident)
            record["reference"] = merge_reference(record.get("reference"), event.get("reference")) or {
                "status": "unavailable",
                "label": None,
            }
            if event["type"] == "packets":
                record["packets"] = event["packets"]
                if event.get("connection_match"):
                    record["connection_match"] = event["connection_match"]
            else:
                record["predictions"][event["observed_packets"]] = {
                    k: event[k]
                    for k in ("observed_packets", "label", "status", "alternatives", "artifact_id")
                }
                # Preserve the actual model budget and checkpoint timing, not
                # just its score. Fixed-ten events may observe 20/30 packets.
                record["predictions"][event["observed_packets"]].update(
                    {
                        k: event[k]
                        for k in (
                            "model_packets",
                            "model_prefix_limit",
                            "model_observation_ms",
                            "observation_ms",
                            "policy_version",
                            "policy_fitted",
                            "policy_scope",
                            "decision_reason",
                            "pipeline_ms",
                            "queue_ms",
                            "capture_to_parser_ms",
                            "capture_to_event_ms",
                            "capture_timestamp",
                            "emitted_at",
                            "sequence",
                        )
                        if k in event
                    }
                )
        for q in self.clients:
            if isinstance(q, ViewerQueue):
                coalesced, dropped = q.offer(event)
                self.packet_updates_coalesced += int(coalesced)
            else:
                dropped = q.get_nowait().get("type", "other") if q.full() else None
                q.put_nowait(event)
            if dropped is not None:
                self.drops += 1
                self.viewer_event_drops[dropped if dropped in self.viewer_event_drops else "other"] += 1

    def acknowledge(self, message):
        """Receipt in the WebSocket handler, never animation or browser paint."""
        if (
            not isinstance(message, dict)
            or not self.session_id
            or message.get("session_id") != self.session_id
        ):
            return False
        kind, sequence, received = (
            message.get("event_type"),
            message.get("sequence"),
            message.get("received_at"),
        )
        if (
            kind not in ("prediction", "observation")
            or type(sequence) is not int
            or type(received) not in (int, float)
            or not 0 <= received <= 1e13
        ):
            return False
        pending, samples = (
            (self.delivery_pending, self.delivery)
            if kind == "prediction"
            else (self.observation_delivery_pending, self.observation_delivery)
        )
        anchor = pending.get(sequence)
        if anchor is None or not anchor <= received <= anchor + 600:
            return False
        del pending[sequence]
        samples.append((received - anchor) * 1000)
        return True

    def local_evaluation(self):
        flows = [
            {**record, "predictions": list(record["predictions"].values())}
            for record in self.evidence.values()
        ]
        return {
            "schema_version": "1",
            "source": "user_started_capture",
            "adapter_version": ADAPTER_VERSION,
            "fixture": bool(self.predictor and self.predictor.meta.get("provenance", {}).get("fixture")),
            "session_id": self.session_id,
            "reference_enabled": self.reference_enabled,
            "connection_matching": (
                {"version": VERSION, "salt": self.match_salt} if self.reference_enabled else None
            ),
            "artifact_id": self.predictor.identity if self.predictor else None,
            "reference_policy": {
                "method": "visible handshake SNI mapped separately; never predictor input",
                "source": MAP_SOURCE,
                "map_sha256": MAP_SHA256,
            },
            "flows": flows,
            "agreement_by_prefix": summarize(flows),
            "evidence_evicted": self.evidence_evicted,
            "counters": self.status(),
            "note": "Agreement with a historical hostname map, not app ground truth. Missing/encrypted names stay unverified. Retained flows only; exports omit payloads, hostnames and addresses. Transient grouping addresses clear on Stop. Expires on next Start or service exit.",
        }

    def window_tick(self, now=None, stopped=False):
        if not self.window_enabled:
            return
        now = time.monotonic() if now is None else now
        for state in self.table.states.values():
            window = state.windows.snapshot(now, stopped)
            row = {"flow_id": state.id, "observation": window, "reference": state.reference}
            if row == self.window_evidence.get(state.id):
                continue
            if state.id not in self.window_evidence and len(self.window_evidence) >= 256:
                self.window_evidence.popitem(last=False)
                self.window_evidence_evicted += 1
            self.window_evidence[state.id] = row
            self.emit({"type": "observation", **row})

    def window_export(self):
        return {
            "version": WINDOW_VERSION,
            "session_id": self.session_id,
            "source": "user_started_capture" if self.session_id else "not_started",
            "fixture": bool(self.predictor and self.predictor.meta["provenance"].get("fixture")),
            "enabled": self.window_enabled,
            "running": self.running,
            "flows": list(self.window_evidence.values()),
            "evicted": self.window_evidence_evicted,
            "note": "Descriptive windows only. No activity/service model or independent quality validation. Raw names, addresses and payload content omitted.",
        }

    def assessments(self):
        return {
            "session_id": self.session_id,
            "source": "separate_metadata_and_packet_estimate",
            "flows": [
                {
                    "flow_id": row["flow_id"],
                    **assess(row.get("reference"), next(reversed(row["predictions"].values()), None)),
                }
                for row in self.evidence.values()
            ],
        }

    async def start(self, interface, duration, reference=False, observation_windows=False):
        async with self.lock:
            if self.running:
                raise RuntimeError("capture already running")
            if self.predictor is None:
                raise RuntimeError("trained model unavailable")
            if self.predictor.meta["provenance"].get("fixture"):
                raise RuntimeError("fixture models cannot run live capture")
            if not self.clients:
                raise RuntimeError("connect event stream before starting capture")
            if interface not in [x["id"] for x in await self.interfaces()]:
                raise ValueError("select a current local interface")
            if reference:
                rules()  # Validate the separate reference resource before opening an interface.
            self.reference_enabled = reference
            self.selected_interface_id = interface
            self.match_salt = secrets.token_hex(32) if reference else None
            self.evidence.clear()
            self.evidence_evicted = 0
            self.window_enabled = observation_windows
            self.window_evidence.clear()
            self.window_evidence_evicted = 0
            self.table = FlowTable(observation_windows=observation_windows)
            self.pending.clear()
            self.errors.clear()
            self.events.clear()
            self.delivery.clear()
            self.delivery_pending.clear()
            self.observation_delivery_pending.clear()
            self.observation_delivery.clear()
            self.receipt_tracking_evicted = {"prediction": 0, "observation": 0}
            self.last_client = time.monotonic()
            self.sequence = self.drops = self.coalesced = 0
            self.packet_updates_coalesced = self.inference_queue_drops = 0
            self.viewer_event_drops = dict.fromkeys(self.viewer_event_drops, 0)
            self.session_id = uuid.uuid4().hex
            self.started_at, self.stopped_at = time.time(), None
            self.viewer_close = None
            self.process = await asyncio.create_subprocess_exec(
                tshark_path(),
                "-i",
                interface,
                "-f",
                "udp port 443",
                "-a",
                f"duration:{duration}",
                *field_args(reference),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                limit=65536,
            )
            self.running, self.reason = True, "capturing"
            self.tasks = [
                asyncio.create_task(self.read()),
                asyncio.create_task(self.drain()),
                asyncio.create_task(self.worker()),
                asyncio.create_task(self.guard(duration)),
            ]
            return self.status()

    async def read(self):
        try:
            while self.running:
                line = await self.process.stdout.readline()
                if not line:
                    break
                parsed_at, received = time.time(), time.perf_counter()
                try:
                    obs = parse_line(line.decode(errors="replace"), self.reference_enabled)
                    state = self.table.ingest(obs)
                except (ValueError, OverflowError):
                    self.table.counters["ignored"] += 1
                    continue
                if state is None:
                    continue
                flow = Flow(packets=list(state.packets))
                self.emit(
                    {
                        "type": "packets",
                        "flow_id": state.id,
                        "packets": flow.model_dump()["packets"],
                        "observed_packets": len(flow.packets),
                        "reference": state.reference,
                        "connection_match": (
                            {
                                "tuple_token": connection_token(obs.src, obs.dst, self.match_salt),
                                "first_packet_unix_ms": state.first_timestamp_ns / 1000000,
                            }
                            if self.reference_enabled
                            else None
                        ),
                        "capture_timestamp": obs.timestamp,
                        "parsed_at": parsed_at,
                        "capture_to_parser_ms": (parsed_at - obs.timestamp) * 1000,
                    }
                )
                if len(state.packets) in BUDGETS:
                    checkpoint = (state.id, len(state.packets))
                    if checkpoint in self.pending:
                        self.coalesced += 1
                    elif len(self.pending) >= self.queue_size:
                        self.pending.popitem(last=False)
                        self.drops += 1
                        self.inference_queue_drops += 1
                    self.pending[checkpoint] = (flow, received, parsed_at, obs.timestamp, state.reference)
                    self.wake.set()
        finally:
            if self.running:
                asyncio.create_task(self.stop("capture process exited"))

    async def drain(self):
        while line := await self.process.stderr.readline():
            message = line.decode(errors="replace").strip()
            if message.startswith("Capturing on ") or re.fullmatch(r"\d+ packets? captured", message):
                continue
            if message:
                self.errors.append(message[:512])

    async def worker(self):
        while self.running:
            await self.wake.wait()
            while self.pending and self.running:
                (flow_id, _), (flow, received, parsed_at, captured_at, reference) = self.pending.popitem(
                    last=False
                )
                queued_ms = (time.perf_counter() - received) * 1000
                try:
                    result = await asyncio.to_thread(self.predictor.predict, flow.array())
                except Exception:
                    self.reason = "inference failed"
                    asyncio.create_task(self.stop(self.reason))
                    return
                if self.running:
                    timing = {
                        "queue_ms": queued_ms,
                        "capture_to_parser_ms": (parsed_at - captured_at) * 1000,
                        "capture_to_event_ms": (time.time() - captured_at) * 1000,
                    }
                    self.events.append({**timing, "pipeline_ms": result["pipeline_ms"]})
                    self.emit(
                        {
                            "type": "prediction",
                            "flow_id": flow_id,
                            "capture_timestamp": captured_at,
                            "reference": reference,
                            "packets": flow.model_dump()["packets"],
                            **result,
                            **timing,
                        }
                    )
            self.wake.clear()

    async def guard(self, duration):
        deadline = time.monotonic() + duration
        while self.running:
            await asyncio.sleep(1)
            self.window_tick()
            if self.clients:
                self.last_client = time.monotonic()
            if time.monotonic() >= deadline:
                asyncio.create_task(self.stop("capture duration limit reached"))
                return
            if time.monotonic() - self.last_client > 10:
                asyncio.create_task(self.stop("viewer disconnected"))
                return

    async def stop(self, reason="stopped by user"):
        async with self.lock:
            if (
                not self.running
                and not self.tasks
                and not self.pending
                and not self.table.states
                and (self.process is None or self.process.returncode is not None)
            ):
                return self.status()
            self.running = False
            self.reason = reason
            if self.process and self.process.returncode is None:
                if os.name == "nt":
                    killer = await asyncio.create_subprocess_exec(
                        "taskkill",
                        "/PID",
                        str(self.process.pid),
                        "/T",
                        "/F",
                        stdout=asyncio.subprocess.DEVNULL,
                        stderr=asyncio.subprocess.DEVNULL,
                    )
                    await killer.wait()
                else:
                    self.process.terminate()
                try:
                    await asyncio.wait_for(self.process.wait(), 3)
                except TimeoutError:
                    self.process.kill()
                    await self.process.wait()
            for task in self.tasks:
                if task is not asyncio.current_task():
                    task.cancel()
            await asyncio.gather(
                *(t for t in self.tasks if t is not asyncio.current_task()), return_exceptions=True
            )
            self.tasks.clear()
            self.pending.clear()
            self.window_tick(stopped=True)
            self.table.states.clear()
            self.stopped_at = time.time()
            self.emit({"type": "status", **self.status()})
            self.retain_stopped_session()
            return self.status()
