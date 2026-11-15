"""Constructed schema fixtures, not real browser-log or service-accuracy evidence."""

import copy
import json

import pytest

from netembed.connection_reference import VERSION, connection_token, parse_endpoint
from netembed.netlog_reference import correlate, correlate_files, read_bounded


def chrome_lines(netlog):
    events = ",\n".join(json.dumps(event) for event in netlog["events"])
    return (
        '{"constants":'
        + json.dumps(netlog["constants"])
        + ',\n"events": [\n'
        + events
        + '],\n"polledData":{}\n}\n'
    )


def test_explicit_source_budget_keeps_all_selected_events_and_retained_caps(tmp_path, monkeypatch):
    from netembed import netlog_stream as stream

    _, netlog = sample()
    path = tmp_path / "browser.json"
    path.write_text(chrome_lines(netlog), encoding="utf-8")
    expected, digest, _ = stream.read_quic_reference_stream(path, include_sockets=True)
    monkeypatch.setattr(stream, "MAX_SOURCE_BYTES", 1)
    with pytest.raises(ValueError, match="source limit"):
        stream.read_quic_reference_stream(path)
    actual, other, _ = stream.read_quic_reference_stream(path, include_sockets=True, source_byte_limit=100000)
    assert actual == expected and digest == other
    monkeypatch.setattr(stream, "MAX_RETAINED_EVENTS", 1)
    with pytest.raises(ValueError, match="original event/byte"):
        stream.read_quic_reference_stream(path, source_byte_limit=100000)
    with pytest.raises(ValueError, match="budget"):
        stream.read_quic_reference_stream(path, source_byte_limit=2**31)


def test_offline_projection_roundtrips_events_and_binds_original(tmp_path, monkeypatch):
    import importlib
    from pathlib import Path
    from netembed.bundle import sha256
    from netembed.netlog_stream import read_quic_reference_stream

    monkeypatch.syspath_prepend(str(Path("scripts").resolve()))
    tool = importlib.import_module("project_netlog")
    _, netlog = sample()
    source, output = tmp_path / "source.json", tmp_path / "projection.json"
    source.write_text(chrome_lines(netlog), encoding="utf-8")
    tool.project(source, output)
    expected, _, _ = read_quic_reference_stream(source, include_sockets=True)
    actual, _, _ = read_quic_reference_stream(output, include_sockets=True)
    assert expected == actual
    proof = json.loads(output.with_suffix(".provenance.json").read_text())
    assert proof["source_sha256"] == sha256(source)
    with pytest.raises(FileExistsError):
        tool.project(source, output)


def test_expanded_offline_profile_is_explicit_and_semantically_identical(tmp_path, monkeypatch):
    from netembed import netlog_stream as stream

    evidence, netlog = sample()
    path = tmp_path / "stopped.json"
    path.write_text(chrome_lines(netlog), encoding="utf-8")
    expected, digest, _ = stream.read_quic_reference_stream(path, include_sockets=True)
    monkeypatch.setattr(stream, "MAX_RETAINED_EVENTS", 1)
    with pytest.raises(ValueError, match="original event/byte"):
        stream.read_quic_reference_stream(path)
    actual, other, details = stream.read_quic_reference_stream(path, include_sockets=True, expanded=True)
    assert actual == expected and other == digest
    assert correlate(evidence, actual) == correlate(evidence, netlog)
    assert details["limits"]["retained_events"] == 2000000
    assert details["limits"]["retained_bytes"] == 256 * 1024 * 1024
    assert details["resource_profile"] == "expanded-offline-v1"
    assert stream.MAX_SOURCE_BYTES == 256 * 1024 * 1024


def test_expanded_matcher_budget_changes_capacity_only(monkeypatch):
    import netembed.netlog_reference as module

    evidence, netlog = sample()
    expected = module.correlate(evidence, netlog)
    monkeypatch.setattr(module, "MAX_EVENTS", 1)
    with pytest.raises(ValueError, match="at most 1"):
        module.correlate(evidence, netlog)
    assert module.correlate(evidence, netlog, max_events=2000000) == expected
    with pytest.raises(ValueError, match="budget"):
        module.correlate(evidence, netlog, max_events=2000001)


def test_streaming_projection_matches_full_correlation_and_preserves_migration(tmp_path):
    import hashlib
    from netembed.netlog_stream import read_quic_reference_stream

    evidence, netlog = sample()
    netlog["events"].append({"type": 123456, "source": {"id": 7}, "params": {"irrelevant": "omitted"}})
    path = tmp_path / "browser.json"
    path.write_text(chrome_lines(netlog), encoding="utf-8")
    projected, digest, reader = read_quic_reference_stream(path)
    assert digest == hashlib.sha256(path.read_bytes()).hexdigest()
    assert reader["source_events"] == 5 and reader["retained_events"] == 4
    assert correlate(evidence, projected) == correlate(evidence, netlog)
    netlog["events"].append({"type": 57, "source": {"id": 7}})
    path.write_text(chrome_lines(netlog), encoding="utf-8")
    projected, _, _ = read_quic_reference_stream(path)
    assert correlate(evidence, projected)["reference_counts"] == {"unverifiable_session": 1}


def test_streaming_socket_profile_keeps_all_udp_events_without_changing_references(tmp_path, monkeypatch):
    from netembed import netlog_stream

    evidence, netlog = sample()
    socket_events = []
    for number, name in enumerate(netlog_stream.SOCKET_TYPES, start=900):
        netlog["constants"]["logEventTypes"][name] = number
        socket_events.append({"type": number, "source": {"id": 100}, "params": {"byte_count": 1250}})
    netlog["events"].extend(socket_events)
    path = tmp_path / "sockets.json"
    path.write_text(chrome_lines(netlog), encoding="utf-8")
    default, digest, _ = netlog_stream.read_quic_reference_stream(path)
    sockets, socket_digest, stats = netlog_stream.read_quic_reference_stream(path, include_sockets=True)
    assert digest == socket_digest
    assert all(event not in default["events"] for event in socket_events)
    assert all(event in sockets["events"] for event in socket_events)
    assert correlate(evidence, sockets) == correlate(evidence, netlog)
    assert stats["version"] == "bounded-chrome-json-lines-reference-sockets-v1"
    monkeypatch.setattr(netlog_stream, "MAX_RETAINED_EVENTS", len(default["events"]))
    with pytest.raises(ValueError, match="original event/byte limits"):
        netlog_stream.read_quic_reference_stream(path, include_sockets=True)


@pytest.mark.parametrize(
    "limit",
    ["MAX_SOURCE_BYTES", "MAX_LINE_BYTES", "MAX_SOURCE_EVENTS", "MAX_RETAINED_EVENTS", "MAX_RETAINED_BYTES"],
)
def test_streaming_reader_refuses_input_or_projection_overflow(tmp_path, monkeypatch, limit):
    from netembed import netlog_stream

    _, netlog = sample()
    path = tmp_path / "browser.json"
    path.write_text(chrome_lines(netlog), encoding="utf-8")
    monkeypatch.setattr(netlog_stream, limit, 1)
    with pytest.raises(ValueError):
        netlog_stream.read_quic_reference_stream(path)


@pytest.mark.parametrize(
    "problem",
    ["missing_footer", "missing_separator", "trailing_comma", "nonobject_event", "shadowed_constants"],
)
def test_streaming_reader_validates_entire_export_including_omitted_footer(tmp_path, problem):
    from netembed.netlog_stream import read_quic_reference_stream

    _, netlog = sample()
    text = chrome_lines(netlog)
    if problem == "missing_footer":
        text = text[:-3]
    elif problem == "missing_separator":
        text = text.replace("},\n{", "}\n{", 1)
    elif problem == "trailing_comma":
        text = text.replace("}],", "},],")
    elif problem == "nonobject_event":
        netlog["events"][0] = []
        text = chrome_lines(netlog)
    else:
        text = text.replace('"polledData":{}', '"constants":{}')
    path = tmp_path / "browser.json"
    path.write_text(text, encoding="utf-8")
    with pytest.raises(ValueError):
        read_quic_reference_stream(path)


FIRST = 1700000000000
SALT = "ab" * 32
LOCAL = ("192.0.2.10", 54321)
PEER = ("198.51.100.20", 443)


def sample(local=LOCAL, peer=PEER):
    def address(pair):
        return f"[{pair[0]}]:{pair[1]}" if ":" in pair[0] else f"{pair[0]}:{pair[1]}"

    evidence = {
        "fixture": True,
        "source": "software_schema_fixture",
        "session_id": "capture-fixture",
        "artifact_id": "model-fixture",
        "reference_enabled": True,
        "connection_matching": {"version": VERSION, "salt": SALT},
        "flows": [
            {
                "flow_id": "opaque-flow",
                "connection_match": {
                    "tuple_token": connection_token(local, peer, SALT),
                    "first_packet_unix_ms": FIRST,
                },
                "packets": [
                    {"iat_ms": gap, "direction": direction, "payload_bytes": size}
                    for gap, direction, size in [
                        (0, 1, 1250),
                        (10, -1, 40),
                        (1, -1, 1250),
                        (2, 1, 100),
                        (3, -1, 1000),
                    ]
                ],
                "reference": {"status": "protected_name_unverified", "label": None},
                "predictions": [
                    {
                        "observed_packets": 5,
                        "status": "classified",
                        "label": "whatsapp",
                        "alternatives": [{"label": "whatsapp", "score": 0.9}],
                        "artifact_id": "model-fixture",
                    }
                ],
            }
        ],
    }
    netlog = {
        "constants": {
            "timeTickOffset": str(FIRST - 1000),
            "logEventTypes": {
                "QUIC_SESSION": 713,
                "QUIC_SESSION_PACKET_RECEIVED": 991,
                "QUIC_CONNECTION_MIGRATION_MODE": 55,
                "QUIC_CONNECTION_MIGRATION_SUCCESS": 57,
            },
            "logEventPhase": {"PHASE_BEGIN": 1, "PHASE_END": 2, "PHASE_NONE": 0},
        },
        "events": [
            {
                "type": 713,
                "phase": 1,
                "source": {"id": 7},
                "time": "990",
                "params": {"host": "r1.googlevideo.com", "port": 443},
            },
            *[
                {
                    "type": 991,
                    "phase": 0,
                    "source": {"id": 7},
                    "time": str(time),
                    "params": {"self_address": address(local), "peer_address": address(peer), "size": size},
                }
                for time, size in [(1010, 40), (1011, 1250), (1016, 1000)]
            ],
        ],
    }
    return evidence, netlog


def test_exact_reference_correlation_preserves_conflicting_model_output_and_omits_pii():
    evidence, netlog = sample()
    before = copy.deepcopy(evidence)
    result = correlate(evidence, netlog)
    row = result["flows"][0]
    assert row["reference"]["label"] == "youtube" and row["matched_receive_packets"] == 3
    assert row["predictions"] == evidence["flows"][0]["predictions"]
    assert row["predictions"][0]["label"] == "whatsapp"
    assert result["agreement_by_prefix"]["5"]["accepted_mismatches"] == 1
    assert result["agreement_by_service"]["youtube"]["5"]["accepted_mismatches"] == 1
    assert result["agreement_by_prefix"]["5"]["top1_reference_agreement"] == 0
    assert evidence == before
    text = json.dumps(result)
    for private in ("r1.googlevideo.com", LOCAL[0], PEER[0], SALT):
        assert private not in text


def test_origin_is_not_guessed_from_tuple_when_netlog_redacts_it():
    evidence, netlog = sample()
    netlog["events"][0]["params"].pop("host")
    result = correlate(evidence, netlog)
    assert result["reference_counts"] == {"origin_unavailable": 1}
    assert result["agreement_by_service"] == {}


def test_begin_time_gate_and_finite_clock_offset_are_required():
    evidence, netlog = sample()
    netlog["events"][0]["time"] = "10000"
    assert correlate(evidence, netlog)["reference_counts"] == {"unmatched_connection": 1}
    netlog["constants"]["timeTickOffset"] = "nan"
    with pytest.raises(ValueError, match="finite timeTickOffset"):
        correlate(evidence, netlog)


def test_candidate_limit_stays_ambiguous_instead_of_selecting_a_convenient_session():
    evidence, netlog = sample()
    template = copy.deepcopy(netlog["events"])
    for ident in range(8, 24):
        extra = copy.deepcopy(template)
        for event in extra:
            event["source"]["id"] = ident
        netlog["events"].extend(extra)
    result = correlate(evidence, netlog)
    assert result["reference_counts"] == {"ambiguous_connection": 1}
    assert result["flows"][0]["candidate_limit_exceeded"]


@pytest.mark.parametrize(
    "change",
    ["wrong_port", "wrong_ip", "wrong_clock", "wrong_size", "missing_size", "one_packet", "different_source"],
)
def test_tuple_time_size_source_and_minimum_evidence_are_all_required(change):
    evidence, netlog = sample()
    if change == "one_packet":
        netlog["events"] = netlog["events"][:2]
    else:
        for event in netlog["events"][1:]:
            if change == "wrong_port":
                event["params"]["self_address"] = "192.0.2.10:54322"
            elif change == "wrong_ip":
                event["params"]["peer_address"] = "198.51.100.21:443"
            elif change == "wrong_clock":
                event["time"] = str(int(event["time"]) + 5000)
            elif change == "wrong_size":
                event["params"]["size"] = 999
            elif change == "missing_size":
                event["params"].pop("size")
            elif change == "different_source":
                event["source"]["id"] = 8
    assert correlate(evidence, netlog)["flows"][0]["reference"]["status"] == "unmatched_connection"


def test_duplicate_events_cannot_supply_two_packet_matches():
    evidence, netlog = sample()
    netlog["events"] = [netlog["events"][0], netlog["events"][1], copy.deepcopy(netlog["events"][1])]
    assert correlate(evidence, netlog)["reference_counts"] == {"unmatched_connection": 1}


def test_ambiguous_sessions_are_not_selected_by_expected_label():
    evidence, netlog = sample()
    duplicate = copy.deepcopy(netlog["events"])
    for event in duplicate:
        event["source"]["id"] = 8
    duplicate[0]["params"]["host"] = "web.whatsapp.com"
    netlog["events"].extend(duplicate)
    result = correlate(evidence, netlog)
    assert result["reference_counts"] == {"ambiguous_connection": 1}
    assert result["agreement_by_prefix"]["5"]["referenced_predictions"] == 0


def test_migration_mode_is_not_migration_but_success_or_changed_tuple_refuses_reference():
    evidence, netlog = sample()
    netlog["events"].append({"type": 55, "source": {"id": 7}})
    assert correlate(evidence, netlog)["reference_counts"] == {"mapped": 1}
    netlog["events"].append({"type": 57, "source": {"id": 7}})
    assert correlate(evidence, netlog)["reference_counts"] == {"unverifiable_session": 1}
    netlog["events"].pop()
    other = copy.deepcopy(netlog["events"][1])
    other["params"]["self_address"] = "192.0.2.10:54322"
    netlog["events"].append(other)
    assert correlate(evidence, netlog)["reference_counts"] == {"unverifiable_session": 1}


@pytest.mark.parametrize(
    "local,peer", [(("2001:db8::1", 54321), ("2001:db8::2", 443)), (("::ffff:192.0.2.10", 54321), PEER)]
)
def test_ipv6_and_ipv4_mapped_endpoints(local, peer):
    evidence, netlog = sample(local, peer)
    assert correlate(evidence, netlog)["reference_counts"] == {"mapped": 1}
    assert connection_token(LOCAL, PEER, SALT) == connection_token(PEER, LOCAL, SALT)
    assert connection_token(LOCAL, PEER, SALT) != connection_token(LOCAL, PEER, "cd" * 32)
    assert parse_endpoint("[2001:db8::1]:443") == ("2001:db8::1", 443)


def test_event_order_does_not_link_receives_to_the_wrong_source():
    evidence, netlog = sample()
    netlog["events"].reverse()
    assert correlate(evidence, netlog)["reference_counts"] == {"mapped": 1}


def test_old_exports_and_unsupported_netlog_are_refused():
    evidence, netlog = sample()
    old = copy.deepcopy(evidence)
    old.pop("connection_matching")
    with pytest.raises(ValueError, match="fresh opted-in"):
        correlate(old, netlog)
    netlog["constants"].pop("logEventTypes")
    with pytest.raises(ValueError, match="QUIC event constants"):
        correlate(evidence, netlog)


def test_files_hash_both_inputs_and_refuse_overwrite_or_oversized_input(tmp_path, monkeypatch):
    import netembed.netlog_reference as module

    evidence, netlog = sample()
    capture, browser, output = (tmp_path / name for name in ("capture.json", "browser.json", "report.json"))
    capture.write_text(json.dumps(evidence))
    browser.write_text(json.dumps(netlog))
    correlate_files(capture, browser, output)
    result = json.loads(output.read_text())
    assert len(result["evidence_sha256"]) == len(result["netlog_sha256"]) == 64
    with pytest.raises(FileExistsError):
        correlate_files(capture, browser, output)
    monkeypatch.setattr(module, "MAX_BYTES", 16)
    with pytest.raises(ValueError, match="64 MiB"):
        read_bounded(browser)
