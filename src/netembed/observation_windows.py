"""Bounded descriptive online windows. No activity or service classifier."""

VERSION = "quic-observation-windows-v1"
HORIZONS_MS = (1000, 3000)


class ObservationWindows:
    def __init__(self, first_ns, started_monotonic):
        self.first_ns, self.started = first_ns, started_monotonic
        self.last_ns = first_ns
        self.reordered = 0
        self.late = {h: 0 for h in HORIZONS_MS}
        self.elapsed_seen = set()
        self.counts = {
            h: {
                "packets": [0, 0],
                "bytes": [0, 0],
                "large": 0,
                "switches": 0,
                "previous_direction": None,
                "size_sum_sq": 0,
                "size_min": None,
                "size_max": 0,
            }
            for h in HORIZONS_MS
        }
        self.bins = [[0, 0] for _ in range(30)]

    def add(self, timestamp_ns, direction, payload_bytes):
        if timestamp_ns < self.last_ns:
            self.reordered += 1
            return
        self.last_ns = timestamp_ns
        offset_ns = timestamp_ns - self.first_ns
        if offset_ns >= 3000000000:
            return
        channel = 0 if direction == 1 else 1
        self.bins[offset_ns // 100000000][channel] += 1
        for horizon, stats in self.counts.items():
            if offset_ns >= horizon * 1000000:
                continue
            if horizon in self.elapsed_seen:
                self.late[horizon] += 1
            stats["packets"][channel] += 1
            stats["bytes"][channel] += payload_bytes
            stats["large"] += payload_bytes >= 1000
            stats["size_sum_sq"] += payload_bytes**2
            stats["size_min"] = (
                payload_bytes if stats["size_min"] is None else min(stats["size_min"], payload_bytes)
            )
            stats["size_max"] = max(stats["size_max"], payload_bytes)
            stats["switches"] += stats["previous_direction"] not in (None, direction)
            stats["previous_direction"] = direction

    def snapshot(self, now_monotonic, stopped=False):
        elapsed_ms = max(0, (now_monotonic - self.started) * 1000)
        windows = []
        for horizon, stats in self.counts.items():
            elapsed = elapsed_ms >= horizon
            if elapsed:
                self.elapsed_seen.add(horizon)
            n, byte_total = sum(stats["packets"]), sum(stats["bytes"])
            mean = byte_total / n if n else 0
            windows.append(
                {
                    "horizon_ms": horizon,
                    "state": "elapsed" if elapsed else "stopped_early" if stopped else "observing",
                    "observed_ms": min(horizon, elapsed_ms),
                    "client_packets": stats["packets"][0],
                    "server_packets": stats["packets"][1],
                    "client_bytes": stats["bytes"][0],
                    "server_bytes": stats["bytes"][1],
                    "mean_payload_bytes": mean,
                    "std_payload_bytes": max(0, stats["size_sum_sq"] / n - mean**2) ** 0.5 if n else 0,
                    "min_payload_bytes": stats["size_min"],
                    "max_payload_bytes": stats["size_max"],
                    "large_payload_fraction": stats["large"] / n if n else 0,
                    "direction_switches": stats["switches"],
                    "packets_by_100ms_client_server": [v.copy() for v in self.bins[: horizon // 100]],
                    "late_packets_after_elapsed_snapshot": self.late[horizon],
                }
            )
        return {
            "version": VERSION,
            "first_packet_unix_ms": self.first_ns / 1000000,
            "windows": windows,
            "reordered_packets_excluded": self.reordered,
            "quality": "unverified; elapsed time is not proof of loss-free capture",
            "activity_label": None,
            "service_label": None,
        }
