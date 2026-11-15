"""User-started bounded PCAP, followed by offline same-bytes exporter comparison."""

import argparse
import json
import os
import re
import signal
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

from netembed.bundle import sha256
from netembed.capture import FlowTable, field_args, parse_line, tshark_path

ROOT = Path("artifacts/local/paired-exporter-check-v1")
IMAGE = "netembed-ipfixprobe-parity:local"
IMAGE_ID = "sha256:c673a8e1b05c9678d33dcd851c0f7a9ba572f4ec2f263419a3da1d23e813f196"
MAX_BYTES = 5 * 1024 * 1024


def write_once(path, payload):
    with Path(path).open("x", encoding="utf-8") as stream:
        json.dump(payload, stream, indent=2)


def candidate_stream(lines):
    """Choose first QUIC flow reaching ten valid ordered packets, never by label."""
    table = FlowTable()
    streams = {}
    for line in lines:
        fields = line.rstrip("\r\n").split("\t")
        if len(fields) != 17 or not re.fullmatch(r"\d+", fields[-1]):
            continue
        try:
            obs = parse_line("\t".join(fields[:-1]))
            state = table.ingest(obs, now=obs.timestamp)
        except (ValueError, OverflowError):
            continue
        if state is None:
            continue
        stream = int(fields[-1])
        old = streams.setdefault(state.id, stream)
        if old != stream:
            raise ValueError("one capture flow maps to multiple UDP streams")
        if len(state.packets) == 10:
            return stream
    raise ValueError("no verified QUIC connection reached ten ordered packets; preserve this recording")


def select(source, destination):
    source, destination = Path(source), Path(destination)
    if not source.is_file() or source.stat().st_size > MAX_BYTES:
        raise ValueError("input missing or larger than the bounded capture limit")
    if destination.exists() or source.resolve() == destination.resolve():
        raise FileExistsError("selection output exists or would overwrite source")
    if source.resolve() == (ROOT / "capture.pcap").resolve():
        receipt = json.loads((ROOT / "capture-receipt.json").read_text())
        if receipt["fixture"] or sha256(source) != receipt["raw_sha256"]:
            raise ValueError("capture receipt does not match the original PCAP")
    command = [tshark_path(), "-r", str(source), *field_args(), "-e", "udp.stream"]
    result = subprocess.run(command, check=True, capture_output=True, text=True, timeout=30)
    lines = result.stdout.splitlines()
    if len(lines) > 12000:
        raise ValueError("capture exceeds the declared packet count")
    stream = candidate_stream(lines)
    destination.parent.mkdir(parents=True, exist_ok=True)
    # Reserve the output name before invoking TShark, preserving prior evidence.
    with destination.open("xb"):
        pass
    subprocess.run(
        [
            tshark_path(),
            "-r",
            str(source),
            "-Y",
            f"udp.stream == {stream}",
            "-F",
            "pcap",
            "-w",
            str(destination),
        ],
        check=True,
        capture_output=True,
        timeout=30,
    )
    if destination.stat().st_size > MAX_BYTES:
        raise ValueError("selected recording exceeds the bounded input limit")
    return {
        "stream": stream,
        "source_sha256": sha256(source),
        "selected_sha256": sha256(destination),
        "selection": "first verified QUIC flow to reach ten valid in-order packets; no model, hostname or label",
    }


def capture(interface):
    if not re.fullmatch(r"\d{1,4}", interface):
        raise ValueError("interface must be a TShark interface number")
    ROOT.mkdir(parents=True, exist_ok=False)
    raw = ROOT / "capture.pcap"
    write_once(
        ROOT / "intent.json",
        {
            "interface": interface,
            "declared_utc": datetime.now(timezone.utc).isoformat(),
            "duration_cap_seconds": 30,
            "packet_cap": 12000,
            "size_cap_kib": 4096,
            "filter": "udp port 443",
            "started_by": "explicit local command",
            "privacy": "PCAP contains raw packets and potentially payloads, addresses and other sensitive metadata; keep private.",
        },
    )
    print(
        "Starting UDP/443 capture for at most 30 seconds. Wait 5 seconds, then open your chosen site.",
        flush=True,
    )
    process = subprocess.Popen(
        [
            tshark_path(),
            "-i",
            interface,
            "-f",
            "udp port 443",
            "-a",
            "duration:30",
            "-a",
            "filesize:4096",
            "-c",
            "12000",
            "-F",
            "pcap",
            "-w",
            str(raw),
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
        text=True,
        start_new_session=os.name != "nt",
    )
    try:
        process.communicate(timeout=45)
    except subprocess.TimeoutExpired as error:
        try:
            if os.name == "nt":
                subprocess.run(
                    ["taskkill", "/PID", str(process.pid), "/T", "/F"],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    timeout=10,
                    check=False,
                )
            else:
                try:
                    os.killpg(process.pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
        finally:
            if process.poll() is None:
                process.kill()
            process.communicate()
        raise RuntimeError("capture exceeded its timeout and was stopped; preserve this attempt") from error
    if process.returncode or not raw.is_file() or raw.stat().st_size > MAX_BYTES:
        raise RuntimeError("capture did not complete cleanly; preserve this attempt for diagnosis")
    write_once(
        ROOT / "capture-receipt.json",
        {
            "stopped_utc": datetime.now(timezone.utc).isoformat(),
            "raw_bytes": raw.stat().st_size,
            "raw_sha256": sha256(raw),
            "exit_code": process.returncode,
            "fixture": False,
        },
    )
    print("Capture stopped. Run the offline select command next.")


def compare(source, output, fixture):
    if output.exists() or output.with_suffix(".stdout.txt").exists():
        raise FileExistsError("comparison output exists")
    selection = json.loads(source.with_suffix(".selection.json").read_text())
    if sha256(source) != selection["selected_sha256"]:
        raise ValueError("selected PCAP changed after selection")
    if not fixture:
        if (
            source.resolve() != (ROOT / "selected.pcap").resolve()
            or output.resolve() != (ROOT / "parity.json").resolve()
        ):
            raise ValueError("real recording comparison requires the declared local paths")
        receipt = json.loads((ROOT / "capture-receipt.json").read_text())
        if (
            receipt["fixture"]
            or sha256(ROOT / "capture.pcap") != receipt["raw_sha256"]
            or selection["source_sha256"] != receipt["raw_sha256"]
        ):
            raise ValueError("selected PCAP is not bound to the user-started capture")
    result = subprocess.run(
        ["docker", "image", "inspect", IMAGE, "--format", "{{.Id}}"],
        check=True,
        capture_output=True,
        text=True,
        timeout=15,
    )
    if result.stdout.strip() != IMAGE_ID:
        raise ValueError("local reference image identity changed")
    subprocess.run(
        [
            sys.executable,
            "scripts/check_ipfixprobe_fixture.py",
            "--image",
            IMAGE,
            "--pcap",
            str(source),
            "--source-description",
            "constructed offline fixture"
            if fixture
            else "deliberate local bounded capture; service not asserted",
            "--output",
            str(output),
            *(["--constructed"] if fixture else []),
        ],
        check=True,
        timeout=100,
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("capture").add_argument("--interface", required=True)
    choose = sub.add_parser("select")
    choose.add_argument("--input", type=Path, default=ROOT / "capture.pcap")
    choose.add_argument("--output", type=Path, default=ROOT / "selected.pcap")
    check = sub.add_parser("compare")
    check.add_argument("--input", type=Path, default=ROOT / "selected.pcap")
    check.add_argument("--output", type=Path, default=ROOT / "parity.json")
    check.add_argument("--fixture", action="store_true")
    args = parser.parse_args()
    if args.command == "capture":
        capture(args.interface)
    elif args.command == "select":
        receipt = select(args.input, args.output)
        write_once(args.output.with_suffix(".selection.json"), receipt)
        print(json.dumps(receipt, indent=2))
    else:
        compare(args.input, args.output, args.fixture)


if __name__ == "__main__":
    main()
