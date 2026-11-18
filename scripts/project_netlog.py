"""Explicit bounded offline projection; no origin, time or model filtering."""

import argparse
import json
from pathlib import Path

from netembed.bundle import sha256, write_json
from netembed.netlog_stream import read_quic_reference_stream


def project(source, destination, expanded=False):
    destination = Path(destination)
    if destination.exists() or destination.with_suffix(".provenance.json").exists():
        raise FileExistsError(destination)
    values, digest, details = read_quic_reference_stream(
        source,
        include_sockets=True,
        source_byte_limit=1024 * 1024 * 1024,
        source_event_limit=8000000,
        expanded=expanded,
    )
    with destination.open("x", encoding="utf-8", newline="\n") as out:
        out.write(json.dumps({"constants": values["constants"]})[:-1] + ',\n"events": [\n')
        for i, event in enumerate(values["events"]):
            out.write(json.dumps(event) + ("," if i + 1 < len(values["events"]) else "") + "\n")
        out.write("]\n}\n")
    # Re-read with ordinary limits and compare the retained semantic inventory.
    checked, _, _ = read_quic_reference_stream(destination, include_sockets=True, expanded=expanded)
    if checked != values:
        raise ValueError("projected event inventory changed")
    proof = {
        "source_path": str(Path(source).resolve()),
        "source_sha256": digest,
        "projection_sha256": sha256(destination),
        "reader": details,
        "source_byte_limit": 1024 * 1024 * 1024,
        "source_event_limit": 8000000,
        "retained_caps_unchanged": not expanded,
        "resource_profile": "expanded-offline-v1" if expanded else "normal",
        "model_scoring": False,
    }
    write_json(destination.with_suffix(".provenance.json"), proof)
    print(json.dumps(proof, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source")
    parser.add_argument("destination")
    parser.add_argument(
        "--expanded-netlog",
        action="store_true",
        help="explicit bounded 1GiB/8M source, 256MiB/2M retained offline profile",
    )
    args = parser.parse_args()
    project(args.source, args.destination, args.expanded_netlog)
