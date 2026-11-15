"""Authorized offline PCAP uses the exact live parser/flow builder; never opens an interface."""

import subprocess
import threading
from .capture import FlowTable, field_args, parse_line, tshark_path

OFFLINE_TIMEOUT_SECONDS = 10


def extract(path, reference=False, observation_windows=False):
    command = [tshark_path(), "-r", str(path), *field_args(reference)]
    # Bounded output/time: small fixtures only; larger analysis should use streaming extraction.
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True)
    timed_out = threading.Event()

    def expire():
        if process.poll() is None:
            timed_out.set()
            process.kill()

    deadline = threading.Timer(OFFLINE_TIMEOUT_SECONDS, expire)
    deadline.daemon = True
    deadline.start()
    table = FlowTable(observation_windows=observation_windows)
    count = 0
    last_timestamp = 0
    try:
        for line in process.stdout:
            count += 1
            if count > 100000:
                raise ValueError("offline fixture exceeds 100000 packet limit")
            try:
                obs = parse_line(line, reference)
                last_timestamp = max(last_timestamp, obs.timestamp)
                table.ingest(obs, now=obs.timestamp)
            except ValueError:
                table.counters["ignored"] += 1
        code = process.wait(timeout=10)
        if timed_out.is_set():
            raise ValueError("offline TShark fixture extraction timed out")
        if code:
            raise ValueError("TShark failed to read capture")
    finally:
        deadline.cancel()
        deadline.join()
        if process.poll() is None:
            process.kill()
            process.wait()
        process.stdout.close()
    return {
        "source": "recorded_capture",
        "feature_parity": "parser output; reference comparison required",
        "flows": [
            {
                "schema_version": "1",
                "packets": [p.model_dump() for p in s.packets],
                **({"reference": s.reference} if reference else {}),
                **(
                    {"observation": s.windows.snapshot(last_timestamp, stopped=True)}
                    if observation_windows
                    else {}
                ),
            }
            for s in table.states.values()
        ],
        "counters": table.counters,
        **(
            {"observation_time_basis": "recorded packet timestamps; EOF is a stop, not live elapsed time"}
            if observation_windows
            else {}
        ),
    }
