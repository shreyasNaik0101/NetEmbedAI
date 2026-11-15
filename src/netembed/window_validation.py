"""Offline internal-consistency checks for deliberately started window trials."""

import math
from collections import Counter
from datetime import datetime

from .contract import Flow
from .observation_windows import HORIZONS_MS, VERSION


def validate_windows(intent, capture, observations, status):
    if (
        capture.get("fixture")
        or observations.get("fixture")
        or capture["source"] != "user_started_capture"
        or observations["source"] != "user_started_capture"
    ):
        raise ValueError("requires genuine capture, not fixture/replay")
    session = status["session_id"]
    if (
        not session
        or session == intent["previous_session_excluded"]
        or capture["session_id"] != session
        or observations["session_id"] != session
        or capture["counters"]["session_id"] != session
    ):
        raise ValueError("capture/window session binding changed")
    if (
        status["running"]
        or observations["running"]
        or capture["counters"]["running"]
        or status["selected_interface_id"] != intent["expected_interface_id"]
        or capture["counters"].get("selected_interface_id") != intent["expected_interface_id"]
        or capture["artifact_id"] != intent["expected_artifact_id"]
        or capture["adapter_version"] != intent["expected_adapter"]
        or not status["reference_enabled"]
        or not status["observation_windows_enabled"]
        or not observations["enabled"]
    ):
        raise ValueError("requires stopped capture with intended model/interface/options")
    if observations["version"] != VERSION or observations["version"] != intent["expected_window_version"]:
        raise ValueError("unsupported window version")
    source = {f["flow_id"]: f for f in capture["flows"]}
    rows = observations["flows"]
    ids = [r["flow_id"] for r in rows]
    if (
        len(source) != len(capture["flows"])
        or len(ids) != len(set(ids))
        or len(ids) > 256
        or any(ident not in source for ident in ids)
    ):
        raise ValueError("window/prefix inventory differs")
    since = datetime.fromisoformat(intent["prepared_utc"]).timestamp() * 1000
    results, late_flows = [], set()
    for row in rows:
        obs, original = row["observation"], source[row["flow_id"]]
        if (
            obs["version"] != VERSION
            or obs["first_packet_unix_ms"] <= since
            or obs["first_packet_unix_ms"] != original["connection_match"]["first_packet_unix_ms"]
            or obs["activity_label"] is not None
            or obs["service_label"] is not None
        ):
            raise ValueError("window origin/label contract changed")
        windows = obs["windows"]
        if [w["horizon_ms"] for w in windows] != list(HORIZONS_MS):
            raise ValueError("window horizons changed")
        packets = Flow(packets=original["packets"]).packets
        elapsed, times = 0, []
        for p in packets:
            elapsed += p.iat_ms
            times.append(elapsed)
        for window in windows:
            horizon = window["horizon_ms"]
            bins = window["packets_by_100ms_client_server"]
            if len(bins) != horizon // 100 or any(
                len(pair) != 2 or any(type(v) is not int or v < 0 for v in pair) for pair in bins
            ):
                raise ValueError("invalid directional histogram")
            for direction, key, column in ((1, "client", 0), (-1, "server", 1)):
                count, byte_count = window[key + "_packets"], window[key + "_bytes"]
                if (
                    type(count) is not int
                    or type(byte_count) is not int
                    or count < 0
                    or byte_count < 0
                    or count != sum(pair[column] for pair in bins)
                ):
                    raise ValueError("directional window totals disagree")
                # Lower-bound consistency only, NOT independent full-window parity.
                prefix = [
                    p for p, t in zip(packets, times) if t < horizon - 1e-6 and p.direction == direction
                ]
                if count < len(prefix) or byte_count < sum(p.payload_bytes for p in prefix):
                    raise ValueError("window is missing retained prefix observations")
            n = window["client_packets"] + window["server_packets"]
            byte_total = window["client_bytes"] + window["server_bytes"]
            if (
                not n
                or not math.isfinite(window["mean_payload_bytes"])
                or not math.isclose(window["mean_payload_bytes"], byte_total / n, rel_tol=1e-9)
                or not window["min_payload_bytes"]
                <= window["mean_payload_bytes"]
                <= window["max_payload_bytes"]
                or not 0 <= window["large_payload_fraction"] <= 1
                or not 1 <= window["min_payload_bytes"] <= window["max_payload_bytes"] <= 65527
                or not n <= byte_total <= n * 65527
                or not math.isfinite(window["std_payload_bytes"])
                or window["std_payload_bytes"] < 0
                or not 0 <= window["direction_switches"] < n
                or window["state"] not in ("elapsed", "observing", "stopped_early")
                or not 0 <= window["observed_ms"] <= horizon
                or (window["state"] == "elapsed" and window["observed_ms"] != horizon)
            ):
                raise ValueError("window aggregate/state contract changed")
            late = window["late_packets_after_elapsed_snapshot"]
            if type(late) is not int or not 0 <= late <= n:
                raise ValueError("invalid late-observation counter")
            if late:
                late_flows.add(row["flow_id"])
            results.append(
                {
                    "flow_id": row["flow_id"],
                    "horizon_ms": horizon,
                    "state": window["state"],
                    "packets": n,
                    "bytes": byte_total,
                    "model_prefix_packets": len(packets),
                    "late_revisions": late,
                }
            )
        first, last = windows
        if first["packets_by_100ms_client_server"] != last["packets_by_100ms_client_server"][:10]:
            raise ValueError("nested horizon histograms disagree")
        if any(
            first[k] > last[k] for k in ("client_packets", "server_packets", "client_bytes", "server_bytes")
        ):
            raise ValueError("cumulative horizons regress")
    return {
        "session_id": session,
        "capture_flow_count": len(source),
        "window_flow_count": len(rows),
        "missing_window_flow_ids": sorted(set(source) - set(ids)),
        "states": dict(Counter(r["state"] for r in results)),
        "horizons": {
            str(h): {
                "flow_count": sum(r["horizon_ms"] == h for r in results),
                "packet_sum": sum(r["packets"] for r in results if r["horizon_ms"] == h),
                "maximum_packets_one_flow": max(
                    (r["packets"] for r in results if r["horizon_ms"] == h), default=0
                ),
                "flows_exceeding_model_prefix": sum(
                    r["horizon_ms"] == h and r["packets"] > r["model_prefix_packets"] for r in results
                ),
                "late_packet_revisions": sum(r["late_revisions"] for r in results if r["horizon_ms"] == h),
            }
            for h in HORIZONS_MS
        },
        "late_revision_flow_ids": sorted(late_flows),
        "reordered_observations_excluded": sum(r["observation"]["reordered_packets_excluded"] for r in rows),
        "internal_consistency_passed": True,
        "independent_full_window_parity": False,
        "service_accuracy": None,
        "activity_accuracy": None,
        "note": "Actual capture and internal prefix/count checks only. No independent labels or on-wire reference; no accuracy or loss-free guarantee.",
    }
