"""Vary Ethernet/IP headers around existing RFC vectors; never transmit packets."""

import argparse
import hashlib
import ipaddress
import struct
from pathlib import Path

SOURCE_SHA256 = "5eb614d13006a7c6dc06732b71de01b447795db6cb1e03fc2c7717f257c09e1c"
CASES = ("ipv4_plain", "ipv4_vlan_options", "ipv6_plain", "ipv6_vlan_extensions")


def checksum(data):
    if len(data) % 2:
        data += b"\0"
    total = sum(struct.unpack("!" + "H" * (len(data) // 2), data))
    while total >> 16:
        total = (total & 65535) + (total >> 16)
    return (~total) & 65535


def payloads(source):
    data = Path(source).read_bytes()
    if hashlib.sha256(data).hexdigest() != SOURCE_SHA256:
        raise ValueError("RFC source fixture checksum mismatch")
    offset, result = 24, []
    while offset < len(data):
        _, _, captured, _ = struct.unpack_from("<IIII", data, offset)
        packet = data[offset + 16 : offset + 16 + captured]
        ip_header = (packet[14] & 15) * 4
        result.append(packet[14 + ip_header + 8 :])
        offset += 16 + captured
    if [len(p) for p in result] != [1200, 135, 1200]:
        raise ValueError("unexpected RFC payload sequence")
    return result


def packet(payload, case_index, packet_index):
    ipv6 = case_index >= 2
    varied = case_index in (1, 3)
    reverse = packet_index == 1
    client = ipaddress.ip_address("2001:db8::1" if ipv6 else "192.0.2.1").packed
    server = ipaddress.ip_address("2001:db8::2" if ipv6 else "198.51.100.1").packed
    src, dst = (server, client) if reverse else (client, server)
    sport, dport = (443, 50000 + case_index) if reverse else (50000 + case_index, 443)
    udp = struct.pack("!HHHH", sport, dport, len(payload) + 8, 0) + payload
    pseudo = (
        src + dst + (struct.pack("!I3xB", len(udp), 17) if ipv6 else struct.pack("!BBH", 0, 17, len(udp)))
    )
    udp = udp[:6] + struct.pack("!H", checksum(pseudo + udp) or 65535) + udp[8:]
    if ipv6:
        extension_bytes = 8 * packet_index if varied else 0
        extensions = (
            bytes([17, extension_bytes // 8 - 1]) + bytes(extension_bytes - 2) if extension_bytes else b""
        )
        ip = struct.pack(
            "!IHBB16s16s", 6 << 28, len(extensions) + len(udp), 0 if extensions else 17, 64, src, dst
        )
        ip += extensions
    else:
        options = b"\x01" * (4 * packet_index if varied else 0)
        ip = (
            struct.pack(
                "!BBHHHBBH4s4s",
                0x45 + len(options) // 4,
                0,
                20 + len(options) + len(udp),
                packet_index,
                0,
                64,
                17,
                0,
                src,
                dst,
            )
            + options
        )
        ip = ip[:10] + struct.pack("!H", checksum(ip)) + ip[12:]
    ethernet = bytes.fromhex("020000000002020000000001")
    if varied and packet_index == 1:
        ethernet += struct.pack("!HH", 0x8100, 1)
    elif varied and packet_index == 2:
        ethernet += struct.pack("!HHHH", 0x88A8, 2, 0x8100, 3)
    ethernet += struct.pack("!H", 0x86DD if ipv6 else 0x0800)
    return ethernet + ip + udp


def build(source):
    vectors = payloads(source)
    data = bytearray(struct.pack("<IHHIIII", 0xA1B2C3D4, 2, 4, 0, 0, 65535, 1))
    for case in range(len(CASES)):
        for index, (micros, vector) in enumerate(zip((0, 8500, 10000), vectors)):
            frame = packet(vector, case, index)
            data += struct.pack("<IIII", 1780000000 + case, micros, len(frame), len(frame)) + frame
    return bytes(data)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    destination = Path(args.output)
    if destination.exists():
        raise FileExistsError("choose a new output path; fixtures are never overwritten")
    source = Path(__file__).resolve().parents[1] / "tests/fixtures/rfc9001.pcap"
    destination.write_bytes(build(source))
    print(f"Constructed offline fixture: {destination}")


if __name__ == "__main__":
    main()
