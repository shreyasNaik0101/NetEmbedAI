"""Software checks for comparison failures, not additional live quality data."""

import importlib.util
from pathlib import Path


spec = importlib.util.spec_from_file_location(
    "browser_receive_parity", Path(__file__).parents[1] / "scripts" / "check_browser_receive_parity.py"
)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
compare_prefix = module.compare_prefix


def test_repeated_same_millisecond_datagrams_are_not_discarded():
    result = compare_prefix([(1000.1, 1250), (1000.2, 1250)], [(1000, 1250), (1000, 1250)])
    assert result["ordered_payload_sizes_equal"]
    assert result["browser_prefix_packets"] == 2
    assert len(result["browser_minus_capture_timestamp_ms"]) == 2


def test_size_mismatch_cannot_be_repaired_by_searching_later_packets():
    result = compare_prefix([(1000, 1250), (1001, 100)], [(1000, 50), (1001, 1250), (1002, 100)])
    assert not result["ordered_payload_sizes_equal"]
    assert result["ordered_payload_size_mismatches"] == 2
    assert result["missing_browser_prefix_packets"] == 0


def test_missing_browser_packets_are_reported_even_when_sizes_so_far_agree():
    result = compare_prefix([(1000, 1250), (1001, 100)], [(1000, 1250)])
    assert not result["ordered_payload_sizes_equal"]
    assert result["missing_browser_prefix_packets"] == 1
    assert result["ordered_payload_size_mismatches"] == 0


def test_size_agreement_does_not_hide_clock_disagreement():
    result = compare_prefix([(1000, 1250)], [(1000000, 1250)])
    assert result["ordered_payload_sizes_equal"]
    assert result["maximum_absolute_timestamp_difference_ms"] == 999000


def test_merged_order_disagreement_is_not_hidden_by_within_direction_agreement():
    packets = [
        {"iat_ms": 0, "direction": 1, "payload_bytes": 1250},
        {"iat_ms": 0.1, "direction": -1, "payload_bytes": 100},
        {"iat_ms": 0.1, "direction": 1, "payload_bytes": 50},
    ]
    browser = [(1000, 0, 1, 1250), (1000, 1, 1, 50), (1001, 2, -1, 100)]
    result = module.compare_socket_prefix(packets, 1000, browser)
    assert not result["merged_direction_and_size_agree"]
    assert result["merged_direction_mismatch_indices"] == [1, 2]
    assert result["merged_payload_size_mismatch_indices"] == [1, 2]
    assert all(row["ordered_payload_sizes_equal"] for row in result["by_direction"].values())


def test_equal_browser_millisecond_preserves_ambiguity_at_ten_packet_boundary():
    # Constructed fixture only: both sources agree within each direction, but
    # swapping packets 9 and 10 changes which direction is present at ten.
    packets = [{"iat_ms": 0 if i == 0 else 0.1, "direction": 1, "payload_bytes": 100 + i} for i in range(9)]
    packets += [
        {"iat_ms": 0.1, "direction": -1, "payload_bytes": 900},
        {"iat_ms": 0.1, "direction": 1, "payload_bytes": 109},
    ]
    browser = [(1000, i, p["direction"], p["payload_bytes"]) for i, p in enumerate(packets)]
    browser[9], browser[10] = browser[10], browser[9]
    result = module.compare_socket_prefix(packets, 1000, browser)
    assert result["merged_direction_mismatch_indices"] == [9, 10]
    assert all(result["by_direction"][str(d)]["ordered_payload_sizes_equal"] for d in (1, -1))
    assert result["capture_packets"] == result["browser_prefix_packets"] == 11


def socket_sample():
    from netembed.connection_reference import connection_token

    salt = "ab" * 32
    netlog = {
        "constants": {
            "logEventTypes": {
                "UDP_CONNECT": 10,
                "UDP_LOCAL_ADDRESS": 11,
                "UDP_BYTES_SENT": 12,
                "UDP_BYTES_RECEIVED": 13,
            },
            "logEventPhase": {"PHASE_BEGIN": 1, "PHASE_END": 2},
            "logSourceType": {"UDP_SOCKET": 20},
            "timeTickOffset": 1000,
        },
        "events": [
            {
                "type": kind,
                "phase": phase,
                "source": {"id": 7, "type": 20},
                "time": str(time),
                "params": params,
            }
            for kind, phase, time, params in [
                (10, 1, 0, {"address": "198.51.100.2:443"}),
                (10, 2, 0, {"net_error": 0}),
                (11, 0, 0, {"address": "192.0.2.10:55000"}),
                (12, 0, 1, {"byte_count": 1250}),
                (13, 0, 2, {"address": "198.51.100.2:443", "byte_count": 100}),
            ]
        ],
    }
    target = {"first": 1001, "token": connection_token(("192.0.2.10", 55000), ("198.51.100.2", 443), salt)}
    return netlog, salt, target


def test_socket_identity_binds_both_ports_and_rejects_peer_change():
    netlog, salt, target = socket_sample()
    status, datagrams = module.socket_datagrams(netlog, salt, target)
    assert status["status"] == "unique_socket"
    assert [(p[2], p[3]) for p in datagrams] == [(1, 1250), (-1, 100)]
    netlog["events"][-1]["params"]["address"] = "198.51.100.2:444"
    status, datagrams = module.socket_datagrams(netlog, salt, target)
    assert status["status"] == "socket_endpoint_changed" and not datagrams


def test_chromium_success_omits_net_error_but_missing_completion_is_refused():
    netlog, salt, target = socket_sample()
    del netlog["events"][1]["params"]
    assert module.socket_datagrams(netlog, salt, target)[0]["status"] == "unique_socket"
    del netlog["events"][1]
    assert module.socket_datagrams(netlog, salt, target)[0]["status"] == "socket_connect_unverified"


def test_failed_or_malformed_socket_records_cannot_supply_partial_success():
    netlog, salt, target = socket_sample()
    netlog["events"][1]["params"]["net_error"] = -1
    assert module.socket_datagrams(netlog, salt, target)[0]["status"] == "socket_connect_unverified"
    netlog["events"][1]["params"]["net_error"] = 0
    netlog["events"][-1]["params"]["byte_count"] = -10
    status, datagrams = module.socket_datagrams(netlog, salt, target)
    assert status["status"] == "malformed_socket" and not datagrams
