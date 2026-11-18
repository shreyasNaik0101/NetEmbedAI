"""Constructed contract dictionaries; these tests are not genuine live evidence."""

from copy import deepcopy

import pytest

from netembed.observation_windows import ObservationWindows
from netembed.window_validation import validate_windows


def documents():
    intent = {
        "prepared_utc": "1970-01-01T00:00:01+00:00",
        "previous_session_excluded": None,
        "expected_interface_id": "9",
        "expected_artifact_id": "software-test",
        "expected_adapter": "tshark-prefix-ns-v3",
        "expected_window_version": "quic-observation-windows-v1",
    }
    accumulator = ObservationWindows(2000000000, 0)
    accumulator.add(2000000000, 1, 1200)
    packet = {"iat_ms": 0, "direction": 1, "payload_bytes": 1200}
    status = {
        "running": False,
        "session_id": "constructed-test",
        "selected_interface_id": "9",
        "reference_enabled": True,
        "observation_windows_enabled": True,
    }
    capture = {
        "fixture": False,
        "source": "user_started_capture",
        "session_id": status["session_id"],
        "counters": status,
        "artifact_id": "software-test",
        "adapter_version": intent["expected_adapter"],
        "flows": [
            {"flow_id": "one", "packets": [packet], "connection_match": {"first_packet_unix_ms": 2000}}
        ],
    }
    windows = {
        "fixture": False,
        "source": "user_started_capture",
        "session_id": status["session_id"],
        "version": intent["expected_window_version"],
        "running": False,
        "enabled": True,
        "flows": [{"flow_id": "one", "observation": accumulator.snapshot(4)}],
    }
    return intent, capture, windows, status


def test_valid_consistency_does_not_claim_labels_or_independent_parity():
    report = validate_windows(*documents())
    assert report["internal_consistency_passed"]
    assert report["service_accuracy"] is None and report["independent_full_window_parity"] is False


@pytest.mark.parametrize(
    "change,message",
    [
        (lambda i, c, w, s: w.update(session_id="other"), "session"),
        (lambda i, c, w, s: w.update(fixture=True), "fixture"),
        (lambda i, c, w, s: s.update(running=True), "stopped"),
        (lambda i, c, w, s: c.update(artifact_id="other"), "intended"),
        (lambda i, c, w, s: w["flows"][0]["observation"].update(service_label="youtube"), "label contract"),
        (lambda i, c, w, s: w["flows"][0]["observation"]["windows"][0].update(client_packets=2), "totals"),
        (lambda i, c, w, s: w["flows"][0]["observation"]["windows"][0].update(client_bytes=12), "prefix"),
    ],
)
def test_changed_source_and_inconsistent_counts_are_rejected(change, message):
    docs = deepcopy(documents())
    change(*docs)
    with pytest.raises(ValueError, match=message):
        validate_windows(*docs)
