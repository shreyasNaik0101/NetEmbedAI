"""Offline Chromium NetLog-to-capture reference. Never called by inference.

Schema sources (checked 2026-10-25): Chromium net/log/net_log_event_type_list.h,
net/quic/quic_event_logger.cc and net/log/net_log_util.cc. Event enums come from
each file's constants; no hardcoded enum IDs or origin guesses from IPs/URLs.
"""

import copy
import hashlib
import json
import math
from bisect import bisect_left
from collections import Counter, defaultdict
from pathlib import Path

from .connection_reference import VERSION, connection_token, parse_endpoint
from .contract import Flow
from .service_reference import MAP_SHA256, attribute, summarize

MAX_BYTES = 64 * 1024 * 1024
MAX_EVENTS = 500000
MAX_SESSIONS = 4096
MAX_RECEIVES = 512
START_TOLERANCE_MS = 2000
RECEIVE_TOLERANCE_MS = 100
MIN_MATCHED_PACKETS = 2
MAX_CANDIDATE_SESSIONS = 16


def finite(value):
    number = float(value)
    if not math.isfinite(number):
        raise ValueError("nonfinite time")
    return number


def read_bounded(path):
    with Path(path).open("rb") as source:
        content = source.read(MAX_BYTES + 1)
    if len(content) > MAX_BYTES:
        raise ValueError("local reference input exceeds 64 MiB")
    return json.loads(content.decode("utf-8-sig")), hashlib.sha256(content).hexdigest()


def _targets(evidence):
    if not isinstance(evidence, dict):
        raise ValueError("capture evidence must be a JSON object")
    if not evidence.get("fixture") and evidence.get("source") != "user_started_capture":
        raise ValueError("capture provenance is missing; synthetic schema fixtures must be explicitly marked")
    matching = evidence.get("connection_matching") or {}
    if not isinstance(matching, dict):
        raise ValueError("invalid connection matching metadata")
    salt = matching.get("salt")
    if not evidence.get("reference_enabled") or matching.get("version") != VERSION:
        raise ValueError("requires a fresh opted-in capture export with connection matching metadata")
    connection_token(("192.0.2.1", 1), ("192.0.2.2", 443), salt)  # Validate the session key.
    flows = evidence.get("flows")
    if not isinstance(flows, list) or not 1 <= len(flows) <= 256:
        raise ValueError("expected 1..256 retained capture flows")
    result = {}
    for index, flow in enumerate(flows):
        if not isinstance(flow, dict):
            raise ValueError("invalid capture flow record")
        connection = flow.get("connection_match") or {}
        if not isinstance(connection, dict):
            raise ValueError("invalid flow matching metadata")
        token = connection.get("tuple_token", "")
        if not isinstance(token, str) or len(token) != 64:
            raise ValueError("flow lacks a valid connection token; older exports cannot be attributed")
        bytes.fromhex(token)
        try:
            first = finite(connection["first_packet_unix_ms"])
            if not 0 <= first < 1e15:
                raise ValueError("invalid first-packet time")
        except (KeyError, TypeError, ValueError):
            raise ValueError("flow lacks a valid first-packet Unix millisecond timestamp") from None
        packets = Flow(packets=flow["packets"]).packets
        elapsed, reverse = 0.0, []
        for packet in packets:
            elapsed += packet.iat_ms
            if packet.direction == -1:
                reverse.append((first + elapsed, packet.payload_bytes))
        result[index] = {"token": token, "first": first, "reverse": reverse}
    return salt, result


def _sessions(netlog, salt, targets, max_events=None):
    max_events = MAX_EVENTS if max_events is None else max_events
    if not 1 <= max_events <= 2000000:
        raise ValueError("invalid offline matcher event budget")
    if not isinstance(netlog, dict):
        raise ValueError("NetLog must be a JSON object")
    constants = netlog.get("constants", {})
    if not isinstance(constants, dict):
        raise ValueError("invalid NetLog constants")
    types = constants.get("logEventTypes", {})
    phases = constants.get("logEventPhase", {})
    if not isinstance(types, dict) or not isinstance(phases, dict):
        raise ValueError("invalid NetLog event/phase constants")
    if not all(name in types for name in ("QUIC_SESSION", "QUIC_SESSION_PACKET_RECEIVED")):
        raise ValueError("NetLog lacks documented QUIC event constants")
    if "PHASE_BEGIN" not in phases:
        raise ValueError("NetLog lacks phase constants")
    names = {str(value): name for name, value in types.items()}
    try:
        offset = finite(constants["timeTickOffset"])
    except (KeyError, TypeError, ValueError):
        raise ValueError("NetLog lacks a finite timeTickOffset") from None
    events = netlog.get("events")
    if not isinstance(events, list) or len(events) > max_events:
        raise ValueError(f"expected a NetLog events list with at most {max_events} entries")
    sessions = {}
    skipped = 0
    needed = defaultdict(list)
    for target in targets.values():
        for time, size in target["reverse"]:
            needed[(target["token"], size)].append(time)
    for times in needed.values():
        times.sort()
    # Pass one makes source matching independent of the JSON event order.
    for event in events:
        if not isinstance(event, dict) or names.get(str(event.get("type"))) != "QUIC_SESSION":
            continue
        if event.get("phase") != phases["PHASE_BEGIN"]:
            continue
        params = event.get("params") or {}
        try:
            if not isinstance(params, dict) or not isinstance(event.get("source"), dict):
                raise ValueError("invalid session fields")
            ident = str(event["source"]["id"])
            if ident in sessions:
                sessions[ident]["invalid"] = True
                continue
            if len(sessions) >= MAX_SESSIONS:
                raise ValueError("NetLog exceeds 4096 QUIC session limit")
            origin = params.get("host")
            valid = isinstance(origin, str) and int(params.get("port", 0)) == 443
            sessions[ident] = {
                "begin": offset + finite(event["time"]),
                "reference": attribute(origin) if valid else {"status": "origin_unavailable", "label": None},
                "packets": defaultdict(list),
                "invalid": False,
                "overflow": False,
                "tuple_token": None,
            }
        except (KeyError, TypeError, ValueError):
            if len(sessions) >= MAX_SESSIONS:
                raise ValueError("NetLog exceeds QUIC session limit") from None
            skipped += 1
    for event in events:
        if not isinstance(event, dict):
            skipped += 1
            continue
        source = event.get("source") or {}
        if not isinstance(source, dict):
            skipped += 1
            continue
        ident = str(source.get("id"))
        session = sessions.get(ident)
        if session is None:
            continue
        name = names.get(str(event.get("type")), "")
        if name in ("QUIC_CONNECTION_MIGRATION_SUCCESS", "QUIC_PORT_MIGRATION_SUCCESS"):
            session["invalid"] = True
        if name != "QUIC_SESSION_PACKET_RECEIVED":
            continue
        try:
            params = event["params"]
            if not isinstance(params, dict):
                raise ValueError("invalid receive fields")
            token = connection_token(
                parse_endpoint(params["self_address"]), parse_endpoint(params["peer_address"]), salt
            )
            if session["tuple_token"] is None:
                session["tuple_token"] = token
            elif session["tuple_token"] != token:
                session["invalid"] = True
            size = int(params["size"])
            if not 1 <= size <= 65527:
                raise ValueError("invalid packet size")
            packet = (offset + finite(event["time"]), size)
            times = needed.get((token, size), [])
            position = bisect_left(times, packet[0])
            if not any(
                abs(times[i] - packet[0]) <= RECEIVE_TOLERANCE_MS
                for i in (position - 1, position)
                if 0 <= i < len(times)
            ):
                continue
            received = session["packets"][token]
            if packet in received:
                continue  # Millisecond-indistinguishable duplicate events cannot supply extra proof.
            if len(received) >= MAX_RECEIVES:
                session["overflow"] = True
                continue
            received.append(packet)
        except (KeyError, TypeError, ValueError):
            skipped += 1
    return sessions, skipped


def _packet_matches(expected, received):
    """Conservative one-to-one size/time matches; a record cannot prove two packets."""
    pairs = sorted(
        (abs(time - other), index, other_index)
        for index, (time, size) in enumerate(expected)
        for other_index, (other, other_size) in enumerate(received)
        if size == other_size and abs(time - other) <= RECEIVE_TOLERANCE_MS
    )
    used_expected, used_received = set(), set()
    for _, index, other_index in pairs:
        if index not in used_expected and other_index not in used_received:
            used_expected.add(index)
            used_received.add(other_index)
    return len(used_expected)


def correlate(evidence, netlog, max_events=None):
    salt, targets = _targets(evidence)
    sessions, skipped = _sessions(netlog, salt, targets, max_events=max_events)
    by_token = defaultdict(list)
    for session in sessions.values():
        for token in session["packets"]:
            by_token[token].append(session)
    report_rows = []
    for index, flow in enumerate(evidence["flows"]):
        target = targets[index]
        candidates = []
        possible = [
            s for s in by_token[target["token"]] if abs(target["first"] - s["begin"]) <= START_TOLERANCE_MS
        ]
        for session in possible[:MAX_CANDIDATE_SESSIONS]:
            matches = _packet_matches(target["reverse"], session["packets"].get(target["token"], []))
            if matches >= MIN_MATCHED_PACKETS:
                candidates.append((session, matches))
        if len(possible) > MAX_CANDIDATE_SESSIONS or len(candidates) > 1:
            reference = {"status": "ambiguous_connection", "label": None}
        elif not candidates:
            reference = {"status": "unmatched_connection", "label": None}
        elif candidates[0][0]["invalid"] or candidates[0][0]["overflow"]:
            reference = {"status": "unverifiable_session", "label": None}
        else:
            reference = dict(candidates[0][0]["reference"])
        report_rows.append(
            {
                "flow_id": flow["flow_id"],
                "packets": copy.deepcopy(flow["packets"]),
                "predictions": copy.deepcopy(flow.get("predictions", [])),
                "passive_reference": copy.deepcopy(flow.get("reference")),
                "reference": {**reference, "method": "browser_netlog_origin"},
                "matching_candidates": len(possible)
                if len(possible) > MAX_CANDIDATE_SESSIONS
                else len(candidates),
                "candidate_limit_exceeded": len(possible) > MAX_CANDIDATE_SESSIONS,
                "matched_receive_packets": candidates[0][1] if len(candidates) == 1 else None,
            }
        )
    return {
        "schema_version": "1",
        "session_id": evidence.get("session_id"),
        "artifact_id": evidence.get("artifact_id"),
        "fixture": bool(evidence.get("fixture")),
        "method": "Chromium QUIC session origin, exact session-salted tuple and packet-size/time correlation",
        "matching_policy": {
            "version": VERSION,
            "start_tolerance_ms": START_TOLERANCE_MS,
            "receive_tolerance_ms": RECEIVE_TOLERANCE_MS,
            "minimum_receive_matches": MIN_MATCHED_PACKETS,
            "maximum_candidate_sessions": MAX_CANDIDATE_SESSIONS,
            "maximum_receive_records_per_session_tuple": MAX_RECEIVES,
            "packet_size_rule": "exact UDP-payload byte count equality",
        },
        "service_map_sha256": MAP_SHA256,
        "flows": report_rows,
        "reference_counts": dict(Counter(row["reference"]["status"] for row in report_rows)),
        "retained_capture_flows": len(report_rows),
        "browser_quic_sessions": len(sessions),
        "agreement_by_prefix": summarize(report_rows),
        "agreement_by_service": {
            label: summarize([row for row in report_rows if row["reference"].get("label") == label])
            for label in sorted(
                {
                    row["reference"]["label"]
                    for row in report_rows
                    if row["reference"].get("status") == "mapped"
                }
            )
        },
        "unusable_netlog_events": skipped,
        "evidence_evicted": evidence.get("evidence_evicted", 0),
        "note": "Browser session-origin reference, not tab or message identity. Connection pooling, capture point and clock changes can prevent reliable attribution. Original predictions are preserved. Unmatched/ambiguous rows stay in the denominator inventory; agreement uses only retained mapped references. No raw hostnames, endpoints or matching keys are copied into this report.",
    }


def correlate_files(evidence_path, netlog_path, output, stream_netlog=False, expanded_netlog=False):
    if Path(output).exists():
        raise FileExistsError("reference report already exists; choose a new output path")
    evidence, evidence_sha = read_bounded(evidence_path)
    reader = None
    if stream_netlog:
        from .netlog_stream import read_quic_reference_stream

        netlog, netlog_sha, reader = read_quic_reference_stream(netlog_path, expanded=expanded_netlog)
    else:
        netlog, netlog_sha = read_bounded(netlog_path)
    report = correlate(evidence, netlog, max_events=2000000 if expanded_netlog else None)
    report.update(evidence_sha256=evidence_sha, netlog_sha256=netlog_sha)
    if reader:
        report["netlog_reader"] = reader
    from .bundle import write_json

    write_json(output, report)
