"""Offline fixture/recording-prefix parity. Never captures or builds/pulls images."""

import argparse
import hashlib
import subprocess
from pathlib import Path

import numpy as np

from netembed.bundle import sha256, write_json
from netembed.capture import ADAPTER_VERSION
from netembed.contract import Flow
from netembed.offline import extract
from netembed.reference_parity import parse_pstats_text

PCAP_SHA256 = "5eb614d13006a7c6dc06732b71de01b447795db6cb1e03fc2c7717f257c09e1c"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--image", required=True, help="explicit trusted locally built reference image")
    parser.add_argument("--output", required=True)
    parser.add_argument(
        "--pcap",
        help="optional small existing authorized recording prefix; source must be described separately",
    )
    parser.add_argument(
        "--source-description", default="unconfirmed existing recording; not a verified user-started trial"
    )
    parser.add_argument(
        "--constructed", action="store_true", help="mark an explicitly supplied constructed PCAP as a fixture"
    )
    args = parser.parse_args()
    fixture = (
        Path(args.pcap).resolve()
        if args.pcap
        else Path(__file__).resolve().parents[1] / "tests/fixtures/rfc9001.pcap"
    )
    if fixture.stat().st_size > 16 * 1024 * 1024:
        raise ValueError("use a small recorded prefix (at most 16 MiB), not a full recording")
    pcap_sha = sha256(fixture)
    if not args.pcap and pcap_sha != PCAP_SHA256:
        raise ValueError("offline RFC fixture checksum mismatch")
    out = Path(args.output)
    if out.exists():
        raise FileExistsError(out)
    stdout = out.with_suffix(".stdout.txt")
    if stdout.exists():
        raise FileExistsError(stdout)
    out.parent.mkdir(parents=True, exist_ok=True)
    image_id = subprocess.run(
        ["docker", "image", "inspect", args.image, "--format", "{{.Id}}"],
        capture_output=True,
        text=True,
        timeout=15,
        check=True,
    ).stdout.strip()
    base = [
        "docker",
        "run",
        "--pull=never",
        "--rm",
        "--network",
        "none",
        "--cap-drop",
        "ALL",
        "--security-opt",
        "no-new-privileges",
        "--memory",
        "512m",
        "--cpus",
        "1",
        "--user",
        "65534:65534",
        "--read-only",
        "--tmpfs",
        "/tmp:rw,noexec,nosuid,size=16m",
    ]
    command = [
        *base,
        "--mount",
        f"type=bind,source={fixture.as_posix()},target=/fixtures/input.pcap,readonly",
        args.image,
        "-i",
        "pcap;file=/fixtures/input.pcap",
        "-p",
        "pstats",
        "-o",
        "text",
    ]
    process = subprocess.run(command, capture_output=True, timeout=30, check=True)
    stdout.write_bytes(process.stdout)
    reference = parse_pstats_text(process.stdout.decode("utf-8"))
    actual = extract(fixture)
    if len(actual["flows"]) != 1:
        raise ValueError("adapter did not produce exactly one reference flow")
    adapter = Flow.model_validate(actual["flows"][0])
    version = subprocess.run(
        [*base, args.image, "-V"], capture_output=True, text=True, timeout=15, check=True
    ).stdout.strip()
    same = bool(np.allclose(reference.array(), adapter.array(), atol=1e-7, rtol=0))
    write_json(
        out,
        {
            "source": "constructed_offline_pcap"
            if args.constructed
            else "existing_recorded_pcap_prefix"
            if args.pcap
            else "constructed_rfc9001_protocol_fixture",
            "source_description": args.source_description
            if args.pcap
            else "constructed RFC 9001 protocol fixture",
            "fixture": args.constructed or not bool(args.pcap),
            "pcap_sha256": pcap_sha,
            "reference_tool": "CESNET ipfixprobe PSTATS",
            "reference_version": version,
            "docker_image_id": image_id,
            "reference_stdout_sha256": hashlib.sha256(process.stdout).hexdigest(),
            "reference_text_timestamp_format": "integer seconds dot integer microseconds; microseconds are not zero-padded",
            "reference_features": reference.model_dump(),
            "adapter_features": adapter.model_dump(),
            "raw_features_match": same,
            "absolute_tolerance": 1e-7,
            "adapter_counters": actual["counters"],
            "adapter_version": ADAPTER_VERSION,
            "raw_iat_exact": len(reference.packets) == len(adapter.packets)
            and all(a.iat_ms == b.iat_ms for a, b in zip(reference.packets, adapter.packets)),
            "maximum_raw_iat_error_ms": max(
                abs(a.iat_ms - b.iat_ms) for a, b in zip(reference.packets, adapter.packets)
            ),
            "adapter_source_sha256": sha256(Path(__file__).resolve().parents[1] / "src/netembed/capture.py"),
            "note": "Independent current exporter comparison on the explicit offline PCAP. Recording origins require separate provenance; filenames do not label connections or prove user-started collection. No trained-model, local-quality or historical 2022 CSV quantization claim follows. The container mounts only this file, never a capture interface.",
        },
    )
    print(f"raw_features_match={same}; reference_version={version}; report={out}")
    if not same:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
