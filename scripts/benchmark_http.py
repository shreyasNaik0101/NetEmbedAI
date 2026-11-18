"""Measure trained-bundle loopback HTTP inference; never calls capture endpoints."""

import argparse
import json
import os
import platform
import socket
import subprocess
import sys
import time
from pathlib import Path

import numpy as np
import httpx


def free_port():
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


def benchmark(bundle, flow, calls):
    if calls < 1000:
        raise ValueError("benchmark requires at least 1000 calls")
    body = json.loads(Path(flow).read_text())
    if set(body) != {"schema_version", "packets"}:
        raise ValueError("flow must use the public prediction schema only")
    port = free_port()
    base = f"http://127.0.0.1:{port}"
    flags = subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
    process = subprocess.Popen(
        [sys.executable, "-m", "netembed.cli", "serve", "--bundle", str(bundle), "--port", str(port)],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        creationflags=flags,
    )
    try:
        with httpx.Client() as client:
            deadline = time.monotonic() + 60
            while True:
                if process.poll() is not None:
                    raise RuntimeError("local inference server exited during startup")
                try:
                    ready = client.get(base + "/health/ready", timeout=2)
                    if ready.status_code == 200:
                        break
                except httpx.RequestError:
                    pass
                if time.monotonic() > deadline:
                    raise TimeoutError("local inference server did not become ready")
                time.sleep(0.2)
            identity = client.get(base + "/model", timeout=10).json()["artifact_id"]
            times = []
            for index in range(50 + calls):
                start = time.perf_counter()
                response = client.post(base + "/predict", json=body, timeout=10)
                elapsed = (time.perf_counter() - start) * 1000
                response.raise_for_status()
                prediction = response.json()
                if prediction["artifact_id"] != identity:
                    raise ValueError("HTTP response artifact changed during benchmark")
                if index >= 50:
                    times.append(elapsed)
        return {
            "artifact_id": identity,
            "transport": "local loopback HTTP keep-alive; no browser or packet capture",
            "hardware": platform.platform() + " / " + platform.processor(),
            "warmup": 50,
            "calls": calls,
            "http_p50_ms": float(np.percentile(times, 50)),
            "http_p95_ms": float(np.percentile(times, 95)),
        }
    finally:
        if process.poll() is None:
            process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=5)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--bundle", required=True)
    parser.add_argument("--flow", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--calls", type=int, default=1000)
    args = parser.parse_args()
    result = benchmark(args.bundle, args.flow, args.calls)
    destination = Path(args.output)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(result, indent=2) + "\n")
