"""Bounded projection of Chrome's JSON-lines export for origin attribution only.

Every input event is parsed. Selection depends only on event type; connection,
hostname, time, labels and model output never choose which events to retain.
"""

import hashlib
import json
import re
from pathlib import Path

MAX_SOURCE_BYTES = 256 * 1024 * 1024
MAX_LINE_BYTES = 2 * 1024 * 1024
MAX_SOURCE_EVENTS = 2000000
MAX_RETAINED_BYTES = 64 * 1024 * 1024
MAX_RETAINED_EVENTS = 500000
KEPT_TYPES = (
    "QUIC_SESSION",
    "QUIC_SESSION_PACKET_RECEIVED",
    "QUIC_CONNECTION_MIGRATION_SUCCESS",
    "QUIC_PORT_MIGRATION_SUCCESS",
)
SOCKET_TYPES = ("UDP_CONNECT", "UDP_LOCAL_ADDRESS", "UDP_BYTES_SENT", "UDP_BYTES_RECEIVED")


def read_quic_reference_stream(
    path, include_sockets=False, *, source_byte_limit=None, source_event_limit=None, expanded=False
):
    source_byte_limit = (
        (1024 * 1024 * 1024 if expanded else MAX_SOURCE_BYTES)
        if source_byte_limit is None
        else source_byte_limit
    )
    source_event_limit = (
        (8000000 if expanded else MAX_SOURCE_EVENTS) if source_event_limit is None else source_event_limit
    )
    retained_event_limit = 2000000 if expanded else MAX_RETAINED_EVENTS
    retained_byte_limit = 256 * 1024 * 1024 if expanded else MAX_RETAINED_BYTES
    if not 1 <= source_byte_limit <= 1024 * 1024 * 1024 or not 1 <= source_event_limit <= 8000000:
        raise ValueError("invalid offline NetLog source budget")
    path = Path(path)
    before = path.stat()
    if before.st_size > source_byte_limit:
        raise ValueError("streaming NetLog exceeds source limit (default 256 MiB)")
    digest, consumed, lines = hashlib.sha256(), 0, 0
    with path.open("rb") as source:

        def line():
            nonlocal consumed, lines
            value = source.readline(MAX_LINE_BYTES + 1)
            lines += bool(value)
            if lines > source_event_limit + 8:
                raise ValueError("streaming NetLog exceeds line count limit")
            if len(value) > MAX_LINE_BYTES:
                raise ValueError("streaming NetLog line exceeds 2 MiB")
            consumed += len(value)
            if consumed > source_byte_limit:
                raise ValueError("streaming NetLog exceeds source limit")
            digest.update(value)
            return value

        header = line().decode("utf-8-sig").strip()
        if not header.endswith(","):
            raise ValueError("streaming reader requires Chrome's constants-first JSON-lines export")
        constants_root = json.loads(header[:-1] + "}")
        if set(constants_root) != {"constants"} or not isinstance(constants_root["constants"], dict):
            raise ValueError("invalid constants-first NetLog header")
        if not re.fullmatch(rb'\s*"events"\s*:\s*\[\s*', line()):
            raise ValueError("expected a standalone NetLog events array header")
        constants = constants_root["constants"]
        types = constants.get("logEventTypes", {})
        if not isinstance(types, dict):
            raise ValueError("invalid event enum table")
        kept_types = KEPT_TYPES + SOCKET_TYPES if include_sockets else KEPT_TYPES
        retained_ids = {types[name] for name in kept_types if name in types}
        events, scanned, retained_bytes = [], 0, len(header.encode("utf-8"))
        previous_comma, have_event = False, False
        while True:
            raw = line()
            if not raw:
                raise ValueError("unterminated NetLog events array")
            value = raw.strip()
            if not value:
                continue
            closing = value.endswith(b"],") or value.endswith(b"]")
            footer_follows = closing and value.endswith(b"],")
            if closing:
                value = value[:-2] if footer_follows else value[:-1]
                value = value.strip()
            comma = value.endswith(b",")
            body = value[:-1] if comma else value
            if body:
                if have_event and not previous_comma:
                    raise ValueError("missing NetLog event separator")
                event = json.loads(body)
                if not isinstance(event, dict):
                    raise ValueError("NetLog events must be JSON objects")
                scanned += 1
                if scanned > source_event_limit:
                    raise ValueError("streaming NetLog exceeds source event limit")
                if event.get("type") in retained_ids:
                    retained_bytes += len(body)
                    if len(events) >= retained_event_limit or retained_bytes > retained_byte_limit:
                        raise ValueError("QUIC reference projection exceeds original event/byte limits")
                    events.append(event)
                previous_comma, have_event = comma, True
            if closing:
                if previous_comma:
                    raise ValueError("trailing comma in NetLog events array")
                break
        footer = bytearray()
        while value := line():
            footer += value
            if len(footer) > MAX_LINE_BYTES:
                raise ValueError("NetLog footer exceeds 2 MiB")
        if footer_follows:
            footer_fields = json.loads(b"{" + footer)
            if not isinstance(footer_fields, dict) or {"events", "constants"} & footer_fields.keys():
                raise ValueError("NetLog footer shadows reference inputs")
        else:
            if bytes(footer).strip() != b"}":
                raise ValueError("invalid NetLog closing object")
            footer_fields = {}
    after = path.stat()
    if (before.st_size, before.st_mtime_ns) != (after.st_size, after.st_mtime_ns):
        raise ValueError("NetLog changed while reading; stop browser logging first")
    return (
        {"constants": constants, "events": events},
        digest.hexdigest(),
        {
            "version": "bounded-chrome-json-lines-reference-sockets-v1"
            if include_sockets
            else "bounded-chrome-json-lines-reference-v1",
            "source_bytes": consumed,
            "source_events": scanned,
            "resource_profile": "expanded-offline-v1" if expanded else "normal",
            "limits": {
                "source_bytes": source_byte_limit,
                "source_events": source_event_limit,
                "retained_bytes": retained_byte_limit,
                "retained_events": retained_event_limit,
            },
            "retained_events": len(events),
            "retained_encoded_bytes": retained_bytes,
            "retained_event_names": list(kept_types),
            "omitted_footer_fields": sorted(footer_fields),
            "selection": "event type only; every selected QUIC-reference and optional UDP-socket event retained",
            "note": "Full original file parsed and SHA-256 bound. No prediction, origin, connection or time filtering. Optional UDP socket event types are retained for parity checks only. Matching gates are unchanged; the explicit resource profile and limits above apply.",
        },
    )
