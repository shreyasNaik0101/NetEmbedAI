"""Diagnostic invariants; constructed packets are not real accuracy evidence."""

import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from diagnose_youtube_failure import changed_routes, guard, replace_exact_size, socket_families
from netembed.capture import parse_line
from netembed.connection_reference import connection_token
from netembed.contract import Normalizer
from types import SimpleNamespace


@pytest.mark.parametrize(
    "path",
    [
        "data/processed/v2/train.jsonl",
        "data/./processed/v2/calibration.jsonl",
        "artifacts/local/forest-eval-yt-01-rows.json",
    ],
)
def test_diagnostic_excludes_public_and_final_reads_including_relative_paths(path):
    with pytest.raises(ValueError, match="excluded"):
        guard("open", (path, "r", 0))
    guard("open", ("artifacts/local/browser-development/youtube-dev-01-development-rows.jsonl", "r", 0))


def test_diagnostic_forbids_network_connections():
    with pytest.raises(ValueError, match="offline"):
        guard("socket.connect", ())


@pytest.mark.parametrize("ipv6,payload", [(False, 1250), (True, 1230)])
def test_parser_keeps_udp_payload_without_subtracting_ip_header_twice(ipv6, payload):
    # Equal frame lengths, different IP header and payload sizes. Fixture only.
    fields = [
        "100.123456789",
        "" if ipv6 else "192.0.2.1",
        "2001:db8::1" if ipv6 else "",
        "" if ipv6 else "198.51.100.1",
        "2001:db8::2" if ipv6 else "",
        "50000",
        "443",
        str(payload + 8),
        "1292",
        "1292",
        "eth:ipv6:udp:quic" if ipv6 else "eth:ip:udp:quic",
        "0",
        "0x00000001",
        "0",
        "0",
        "",
    ]
    obs = parse_line("\t".join(fields))
    assert obs.size == payload and obs.initial and obs.timestamp_ns == 100123456789


def test_divergence_trace_reports_actual_size_split_and_leaf_change():
    tree = {
        "left": np.array([1, -1, -1]),
        "right": np.array([2, -1, -1]),
        "feature": np.array([33, -2, -2]),
        "threshold": np.array([1241.0, -2.0, -2.0]),
    }
    model = SimpleNamespace(
        trees=[tree], normalizer=Normalizer([0, 0, 0], [1, 1, 1]), forest_feature_map="summary-v1"
    )
    raw = np.array([[0, 1, 1230], [2, -1, 1230]], dtype=np.float32)
    altered, _ = replace_exact_size(raw, 1230, 1250)
    result = changed_routes(model, raw, altered)
    assert result == {
        "trees_reaching_different_leaf": 1,
        "first_divergent_splits": [
            {
                "feature": "server.payload_bytes.max",
                "threshold": 1241.0,
                "before": 1230.0,
                "after": 1250.0,
                "trees": 1,
            }
        ],
    }
    assert changed_routes(model, raw, raw)["trees_reaching_different_leaf"] == 0


def test_size_sensitivity_preserves_original_order_times_and_other_sizes():
    raw = np.array([[0, 1, 1230], [0.001, -1, 40], [8.5, -1, 1230], [0, 1, 1250]], dtype=np.float32)
    copy = raw.copy()
    changed, count = replace_exact_size(raw, 1230, 1250)
    assert count == 2
    np.testing.assert_array_equal(raw, copy)
    np.testing.assert_array_equal(changed[:, :2], raw[:, :2])
    np.testing.assert_array_equal(changed[:, 2], [1250, 40, 1250, 1250])
    unchanged, count = replace_exact_size(raw, 1500, 1300)
    assert count == 0
    np.testing.assert_array_equal(unchanged, raw)


def test_socket_family_does_not_guess_from_packet_size_or_unrelated_socket():
    salt = "01" * 32
    netlog = {
        "constants": {
            "logEventTypes": {"UDP_LOCAL_ADDRESS": 1, "UDP_CONNECT": 2},
            "logSourceType": {"UDP_SOCKET": 3},
            "logEventPhase": {"PHASE_BEGIN": 1},
        },
        "events": [],
    }
    for ident, local, peer in (
        (4, "[2001:db8::1]:50000", "[2001:db8::2]:443"),
        (5, "192.0.2.1:50001", "198.51.100.1:443"),
    ):
        netlog["events"].extend(
            [
                {"source": {"type": 3, "id": ident}, "type": 1, "params": {"address": local}},
                {"source": {"type": 3, "id": ident}, "type": 2, "phase": 1, "params": {"address": peer}},
            ]
        )
    result = socket_families(netlog, salt)
    v6 = connection_token(("2001:db8::1", 50000), ("2001:db8::2", 443), salt)
    v4 = connection_token(("192.0.2.1", 50001), ("198.51.100.1", 443), salt)
    assert result[v6] == {(6, 6)} and result[v4] == {(4, 4)}
