"""Saved browser/capture receive-prefix consistency, never full exporter parity."""

import argparse
from collections import defaultdict

import numpy as np

from netembed.bundle import write_json
from netembed.connection_reference import connection_token, parse_endpoint
from netembed.contract import BUDGETS, Flow
from netembed.netlog_reference import (
    START_TOLERANCE_MS,
    _packet_matches,
    _sessions,
    _targets,
    correlate,
    finite,
    read_bounded,
)


def compare_prefix(expected, received):
    """Compare the first N records without searching for convenient equal sizes.

    Preserve distinct same-millisecond datagrams. The reference matcher deliberately
    deduplicates those for attribution; this consistency check must not do so.
    """
    prefix = received[: len(expected)]
    deltas = [b[0] - a[0] for a, b in zip(expected, prefix)]
    size_mismatches = sum(a[1] != b[1] for a, b in zip(expected, prefix))
    missing = len(expected) - len(prefix)
    return {
        "capture_receive_packets": len(expected),
        "browser_prefix_packets": len(prefix),
        "missing_browser_prefix_packets": missing,
        "ordered_payload_size_mismatches": size_mismatches,
        "ordered_payload_sizes_equal": not missing and not size_mismatches,
        "browser_minus_capture_timestamp_ms": deltas,
        "maximum_absolute_timestamp_difference_ms": max(map(abs, deltas), default=None),
        "absolute_timestamp_difference_p50_p95_ms": np.percentile(np.abs(deltas), [50, 95]).tolist()
        if deltas
        else None,
    }


def socket_datagrams(netlog, salt, target):
    """Locate one complete UDP socket by exact endpoint token, never by label."""
    types = netlog["constants"]["logEventTypes"]
    phases = netlog["constants"]["logEventPhase"]
    source_type = netlog["constants"].get("logSourceType", {}).get("UDP_SOCKET")
    required = ("UDP_CONNECT", "UDP_LOCAL_ADDRESS", "UDP_BYTES_SENT", "UDP_BYTES_RECEIVED")
    if source_type is None or any(name not in types for name in required):
        return {"status": "socket_schema_unavailable"}, []
    grouped = defaultdict(list)
    for index, event in enumerate(netlog["events"]):
        if event.get("source", {}).get("type") == source_type:
            grouped[str(event["source"]["id"])].append((index, event))
    candidates = []
    for events in grouped.values():
        matched = False
        try:
            local = {
                parse_endpoint(event["params"]["address"])
                for _, event in events
                if event["type"] == types["UDP_LOCAL_ADDRESS"]
            }
            connections = [
                event
                for _, event in events
                if event["type"] == types["UDP_CONNECT"] and event["phase"] == phases["PHASE_BEGIN"]
            ]
            peers = {parse_endpoint(event["params"]["address"]) for event in connections}
            matched = any(connection_token(a, b, salt) == target["token"] for a in local for b in peers)
            if not matched:
                continue
            if len(local) != 1 or len(peers) != 1:
                candidates.append(({"status": "socket_endpoints_ambiguous"}, []))
                continue
            local = next(iter(local))
            if len(connections) != 1:
                candidates.append(({"status": "socket_reconnected"}, []))
                continue
            offset = finite(netlog["constants"]["timeTickOffset"])
            if abs(offset + finite(connections[0]["time"]) - target["first"]) > START_TOLERANCE_MS:
                continue
            ended = [
                event
                for _, event in events
                if event["type"] == types["UDP_CONNECT"] and event["phase"] == phases["PHASE_END"]
            ]
            # Chromium EndEventWithNetErrorCode omits params on success;
            # a negative result alone adds net_error. Require the END record.
            if len(ended) != 1 or ended[0].get("params", {}).get("net_error", 0) != 0:
                candidates.append(({"status": "socket_connect_unverified"}, []))
                continue
            records = []
            status = {"status": "unique_socket"}
            for index, event in events:
                if event["type"] not in (types["UDP_BYTES_SENT"], types["UDP_BYTES_RECEIVED"]):
                    continue
                params = event["params"]
                if (
                    "address" in params
                    and connection_token(local, parse_endpoint(params["address"]), salt) != target["token"]
                ):
                    status = {"status": "socket_endpoint_changed"}
                    break
                size = int(params["byte_count"])
                if not 1 <= size <= 65527:
                    raise ValueError("invalid UDP datagram size")
                records.append(
                    (
                        offset + finite(event["time"]),
                        index,
                        1 if event["type"] == types["UDP_BYTES_SENT"] else -1,
                        size,
                    )
                )
            records.sort(key=lambda packet: (packet[0], packet[1]))
            candidates.append((status, records if status["status"] == "unique_socket" else []))
        except (KeyError, TypeError, ValueError):
            # An identifiable candidate with incomplete transfer records must not
            # silently become a convenient subset of apparently matching packets.
            if matched:
                candidates.append(({"status": "malformed_socket"}, []))
    if len(candidates) != 1:
        return {"status": "ambiguous_socket" if candidates else "unmatched_socket"}, []
    return candidates[0]


def compare_socket_prefix(packets, first_packet_unix_ms, received):
    elapsed, expected = 0.0, []
    for packet in packets:
        elapsed += packet["iat_ms"]
        expected.append((first_packet_unix_ms + elapsed, packet["direction"], packet["payload_bytes"]))
    prefix = received[: len(expected)]
    direction_mismatches = [i for i, (a, b) in enumerate(zip(expected, prefix)) if a[1] != b[2]]
    size_mismatches = [i for i, (a, b) in enumerate(zip(expected, prefix)) if a[2] != b[3]]
    return {
        "capture_packets": len(expected),
        "browser_prefix_packets": len(prefix),
        "missing_browser_prefix_packets": len(expected) - len(prefix),
        "merged_direction_mismatch_indices": direction_mismatches,
        "merged_payload_size_mismatch_indices": size_mismatches,
        "merged_direction_and_size_agree": len(expected) == len(prefix)
        and not direction_mismatches
        and not size_mismatches,
        "by_direction": {
            str(direction): compare_prefix(
                [(time, size) for time, d, size in expected if d == direction],
                [(time, size) for time, _, d, size in received if d == direction],
            )
            for direction in (1, -1)
        },
    }


def check(
    evidence_path,
    netlog_path,
    reference_path,
    socket_mode=False,
    replay_bundle=None,
    stream_netlog=False,
    expanded_netlog=False,
):
    evidence, evidence_sha = read_bounded(evidence_path)
    reader = None
    if stream_netlog:
        from netembed.netlog_stream import read_quic_reference_stream

        netlog, netlog_sha, reader = read_quic_reference_stream(
            netlog_path, include_sockets=socket_mode, expanded=expanded_netlog
        )
    else:
        netlog, netlog_sha = read_bounded(netlog_path)
    reference, reference_sha = read_bounded(reference_path)
    if evidence_sha != reference["evidence_sha256"] or netlog_sha != reference["netlog_sha256"]:
        raise ValueError("reference does not bind these exact input files")
    if evidence["fixture"] or reference["fixture"] or evidence["counters"]["running"]:
        raise ValueError("requires an actual stopped user-started capture")
    fresh = correlate(evidence, netlog, max_events=2000000 if expanded_netlog else None)
    if fresh["flows"] != reference["flows"]:
        raise ValueError("saved reference does not reproduce with the fixed matcher")
    salt, targets = _targets(evidence)
    sessions, _ = _sessions(netlog, salt, targets, max_events=2000000 if expanded_netlog else None)
    receive_type = netlog["constants"]["logEventTypes"]["QUIC_SESSION_PACKET_RECEIVED"]
    offset = finite(netlog["constants"]["timeTickOffset"])
    predictor = None
    if replay_bundle:
        if not socket_mode:
            raise ValueError("socket replay requires socket mode")
        import torch
        from netembed.bundle import Predictor

        torch.set_num_threads(2)
        predictor = Predictor(replay_bundle)
        if predictor.identity != evidence["artifact_id"]:
            raise ValueError("socket diagnostic must use the unchanged capture artifact")
    rows = []
    for index, row in enumerate(reference["flows"]):
        if row["reference"]["status"] != "mapped":
            continue
        target = targets[index]
        candidates = [
            (ident, session)
            for ident, session in sessions.items()
            if abs(target["first"] - session["begin"]) <= START_TOLERANCE_MS
            and _packet_matches(target["reverse"], session["packets"].get(target["token"], [])) >= 2
        ]
        if len(candidates) != 1 or candidates[0][1]["invalid"] or candidates[0][1]["overflow"]:
            raise ValueError("mapped connection is no longer uniquely verifiable")
        ident = candidates[0][0]
        if socket_mode:
            socket_status, datagrams = socket_datagrams(netlog, salt, target)
            result = {
                "flow_id": row["flow_id"],
                "reference": row["reference"],
                "socket": socket_status,
                **compare_socket_prefix(row["packets"], target["first"], datagrams),
            }
            if (
                predictor is not None
                and socket_status["status"] == "unique_socket"
                and len(datagrams) >= len(row["packets"])
            ):
                prefix = datagrams[: len(row["packets"])]
                browser = Flow.from_array(
                    np.array(
                        [
                            [time - prefix[i - 1][0] if i else 0, direction, size]
                            for i, (time, _, direction, size) in enumerate(prefix)
                        ]
                    )
                ).array()
                capture = Flow(packets=row["packets"]).array()
                for name, raw in (
                    ("capture_prefix_predictions", capture),
                    ("recorded_socket_predictions", browser),
                ):
                    result[name] = [
                        {k: v for k, v in predictor.predict(raw[:budget]).items() if k != "pipeline_ms"}
                        for budget in BUDGETS
                        if len(raw) >= budget
                    ]
                result["replay_status"] = "complete_recorded_prefix"
            elif predictor is not None:
                result["replay_status"] = "unavailable_or_incomplete_socket_prefix"
            rows.append(result)
            continue
        received = []
        for event in netlog["events"]:
            if event.get("type") != receive_type or str(event.get("source", {}).get("id")) != ident:
                continue
            params = event["params"]
            token = connection_token(
                parse_endpoint(params["self_address"]), parse_endpoint(params["peer_address"]), salt
            )
            if token != target["token"]:
                raise ValueError("received endpoint pair changed")
            received.append((offset + finite(event["time"]), int(params["size"])))
        # Stable timestamp order retains file order for indistinguishable times.
        received.sort(key=lambda packet: packet[0])
        rows.append(
            {
                "flow_id": row["flow_id"],
                "reference": row["reference"],
                "uncompared_client_to_server_packets": len(row["packets"]) - len(target["reverse"]),
                **compare_prefix(target["reverse"], received),
            }
        )
    if socket_mode:
        from netembed.service_reference import summarize

        return {
            "session_id": evidence["session_id"],
            "artifact_id": evidence["artifact_id"],
            "evidence_sha256": evidence_sha,
            "netlog_sha256": netlog_sha,
            "reference_sha256": reference_sha,
            "reference_inventory": reference["reference_counts"],
            **({"netlog_reader": reader} if reader else {}),
            "compared_flows": len(rows),
            "flows": rows,
            "recorded_replay_agreement": {
                name: summarize(
                    [{"reference": row["reference"], "predictions": row.get(name, [])} for row in rows]
                )
                for name in ("capture_prefix_predictions", "recorded_socket_predictions")
            }
            if predictor
            else None,
            "note": "Diagnostic comparison of browser UDP socket-transfer event times with capture times, conditioned on mapped QUIC-origin references. Within-direction size agreement does not erase merged direction/size order mismatches. Socket event time is a userspace observation point, not a reference for on-wire order, complete ipfixprobe parity or historical quantization. Optional socket replay is explicitly offline metadata replay, not arriving live inference or a selected adaptation. No payload logging, capture, model fitting, feature adaptation or deployment. No model inputs come from endpoint identities.",
        }
    deltas = [d for row in rows for d in row["browser_minus_capture_timestamp_ms"]]
    return {
        "session_id": evidence["session_id"],
        "artifact_id": evidence["artifact_id"],
        "evidence_sha256": evidence_sha,
        "netlog_sha256": netlog_sha,
        "reference_sha256": reference_sha,
        "reference_inventory": reference["reference_counts"],
        "compared_flows": len(rows),
        "compared_receive_packets": sum(row["browser_prefix_packets"] for row in rows),
        "missing_browser_prefix_packets": sum(row["missing_browser_prefix_packets"] for row in rows),
        "ordered_payload_size_mismatches": sum(row["ordered_payload_size_mismatches"] for row in rows),
        **({"netlog_reader": reader} if reader else {}),
        "uncompared_client_to_server_packets": sum(
            row["uncompared_client_to_server_packets"] for row in rows
        ),
        "maximum_absolute_timestamp_difference_ms": max(map(abs, deltas), default=None),
        "absolute_timestamp_difference_p50_p95_ms": np.percentile(np.abs(deltas), [50, 95]).tolist()
        if deltas
        else None,
        "flows": rows,
        "note": "Receive-prefix consistency on uniquely mapped browser-origin references only. Attribution used size/time anchors, so this is conditioned on successful correlation, not unbiased quality or full independent exporter parity. All first N receive events are compared in stable timestamp/file order, including equal-millisecond records and size mismatches; none are filtered by captured size. Browser timestamps are millisecond event times at a different observation point. Client-to-server packets, bidirectional gaps, historical exporter quantization and unreferenced sessions are not validated. No model or preprocessing changes; no capture started.",
    }


def main():
    from pathlib import Path

    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("evidence", "netlog", "reference", "output"):
        parser.add_argument("--" + name, required=True)
    parser.add_argument(
        "--socket-mode", action="store_true", help="Compare actual UDP socket datagrams in both directions"
    )
    parser.add_argument(
        "--socket-replay-bundle", help="Optionally replay socket metadata with the exact capture artifact"
    )
    parser.add_argument(
        "--stream-netlog",
        action="store_true",
        help="bounded QUIC reference/optional socket projection for large Chrome logs",
    )
    parser.add_argument(
        "--expanded-netlog", action="store_true", help="explicit bounded expanded offline profile"
    )
    args = parser.parse_args()
    if Path(args.output).exists():
        raise FileExistsError("parity report already exists; choose a new output path")
    write_json(
        args.output,
        check(
            args.evidence,
            args.netlog,
            args.reference,
            args.socket_mode,
            args.socket_replay_bundle,
            args.stream_netlog,
            args.expanded_netlog,
        ),
    )


if __name__ == "__main__":
    main()
