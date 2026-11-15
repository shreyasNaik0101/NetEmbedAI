"""Construct bounded offline window fixtures from public RFC payloads; never transmit."""

import argparse
import struct
from pathlib import Path

from scripts.build_encapsulation_fixture import CASES, packet, payloads


def timeline():
    # 60 datagrams before 600ms, then exact half-open boundaries in microseconds.
    # Vector 1 is server->client (135 bytes); vectors 0/2 are client->server (1200).
    times = [i * 10000 for i in range(60)] + [999999, 1000000, 1000001, 2999999, 3000000, 3100000]
    return [(micros, i % 3) for i, micros in enumerate(times)]


def build(source, through_us=3100000):
    vectors = payloads(source)
    data = bytearray(struct.pack("<IHHIIII", 0xA1B2C3D4, 2, 4, 0, 0, 65535, 1))
    for micros, index in timeline():
        if micros > through_us:
            break
        for case in range(len(CASES)):
            frame = packet(vectors[index], case, index)
            seconds, fraction = divmod(micros, 1000000)
            data += struct.pack("<IIII", 1780000000 + seconds, fraction, len(frame), len(frame)) + frame
    return bytes(data)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    path = Path(args.output)
    if path.exists():
        raise FileExistsError("choose a new path; fixtures are never overwritten")
    path.write_bytes(build(Path(__file__).resolve().parents[1] / "tests/fixtures/rfc9001.pcap"))
    print(f"Constructed offline-only protocol fixture: {path}")


if __name__ == "__main__":
    main()
