"""Independent construction oracle versus native offline TShark + live flow builder."""

import math
import shutil
from pathlib import Path

import pytest

from netembed.capture import tshark_path
from netembed.offline import extract
from scripts.build_window_fixture import build

FIXTURES = Path(__file__).parent / "fixtures"


def oracle(horizon_ms):
    # Declare the wire fixture independently of production window accumulation.
    times = list(range(0, 600000, 10000)) + [999999, 1000000, 1000001, 2999999, 3000000, 3100000]
    rows = [
        (t, -1 if i % 3 == 1 else 1, 135 if i % 3 == 1 else 1200)
        for i, t in enumerate(times)
        if t < horizon_ms * 1000
    ]
    sizes = [size for _, _, size in rows]
    mean = sum(sizes) / len(sizes)
    bins = [[0, 0] for _ in range(horizon_ms // 100)]
    for micros, direction, _ in rows:
        bins[micros // 100000][0 if direction == 1 else 1] += 1
    return {
        "client_packets": sum(d == 1 for _, d, _ in rows),
        "server_packets": sum(d == -1 for _, d, _ in rows),
        "client_bytes": sum(s for _, d, s in rows if d == 1),
        "server_bytes": sum(s for _, d, s in rows if d == -1),
        "mean_payload_bytes": mean,
        "std_payload_bytes": math.sqrt(sum((size - mean) ** 2 for size in sizes) / len(sizes)),
        "min_payload_bytes": min(sizes),
        "max_payload_bytes": max(sizes),
        "large_payload_fraction": sum(s >= 1000 for s in sizes) / len(sizes),
        "direction_switches": sum(a[1] != b[1] for a, b in zip(rows, rows[1:])),
        "packets_by_100ms_client_server": bins,
    }


def test_window_fixture_rebuild_is_exact_and_oracle_budgets_are_explicit():
    assert (FIXTURES / "windows.pcap").read_bytes() == build(FIXTURES / "rfc9001.pcap")
    assert oracle(1000)["client_packets"] == 41 and oracle(1000)["server_packets"] == 20
    assert oracle(3000)["client_packets"] == 43 and oracle(3000)["server_packets"] == 21


@pytest.mark.parametrize("reference", [False, True])
def test_native_tshark_window_features_match_independent_wire_oracle(reference):
    if not Path(tshark_path()).exists() and not shutil.which(tshark_path()):
        pytest.skip("native TShark unavailable; offline window integration only")
    result = extract(FIXTURES / "windows.pcap", reference, observation_windows=True)
    assert result["source"] == "recorded_capture" and len(result["flows"]) == 4
    assert result["counters"]["ignored"] == result["counters"]["reordered"] == 0
    assert result["counters"]["frozen"] == 144
    for flow in result["flows"]:
        assert len(flow["packets"]) == 30
        assert [p["iat_ms"] for p in flow["packets"]] == [0] + [10] * 29
        for window in flow["observation"]["windows"]:
            assert window["state"] == "elapsed"
            for name, expected in oracle(window["horizon_ms"]).items():
                if isinstance(expected, list):
                    assert window[name] == expected
                else:
                    assert window[name] == pytest.approx(expected)
        assert flow["observation"]["service_label"] is None


def test_offline_file_end_does_not_invent_elapsed_live_windows(tmp_path):
    if not Path(tshark_path()).exists() and not shutil.which(tshark_path()):
        pytest.skip("native TShark unavailable; offline window integration only")
    path = tmp_path / "early-stop.pcap"
    path.write_bytes(build(FIXTURES / "rfc9001.pcap", through_us=390000))
    result = extract(path, observation_windows=True)
    for flow in result["flows"]:
        for window in flow["observation"]["windows"]:
            assert window["state"] == "stopped_early"
            assert window["observed_ms"] == pytest.approx(390, abs=0.001)
            assert window["client_packets"] + window["server_packets"] == 40
