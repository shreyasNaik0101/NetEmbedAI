"""Build an offline synthetic PCAP from RFC 9001 A.2/A.3 vectors; never transmit."""

import re
import struct
import urllib.request
from pathlib import Path

s = urllib.request.urlopen("https://www.rfc-editor.org/rfc/rfc9001.txt", timeout=30).read().decode()
client_section = s[s.rfind("A.2.  Client Initial") : s.rfind("A.3.  Server Initial")]
server_section = s[s.rfind("A.3.  Server Initial") : s.rfind("A.4.  Retry")]


def vector(section, marker):
    tail = section.split(marker)[1]
    return bytes.fromhex("".join(re.findall(r"^   ([0-9a-f ]+)$", tail, re.M)))


client = vector(client_section, "The resulting protected packet is:")
server = vector(server_section, "The final protected packet is then:")
assert len(client) == 1200 and len(server) == 135


def checksum(raw):
    total = sum(struct.unpack("!" + "H" * (len(raw) // 2), raw))
    total = (total & 65535) + (total >> 16)
    total = (total & 65535) + (total >> 16)
    return (~total) & 65535


def datagram(payload, reverse):
    src, dst = (bytes([192, 0, 2, 1]), bytes([198, 51, 100, 1]))
    sp, dp = 50000, 443
    if reverse:
        src, dst, sp, dp = dst, src, dp, sp
    udp = struct.pack("!HHHH", sp, dp, len(payload) + 8, 0) + payload
    ip = struct.pack("!BBHHHBBH4s4s", 0x45, 0, 20 + len(udp), 1, 0, 64, 17, 0, src, dst)
    ip = ip[:10] + struct.pack("!H", checksum(ip)) + ip[12:]
    return bytes.fromhex("0200000000020200000000010800") + ip + udp


out = Path("tests/fixtures/rfc9001.pcap")
out.parent.mkdir(parents=True, exist_ok=True)
with out.open("wb") as f:
    f.write(struct.pack("<IHHIIII", 0xA1B2C3D4, 2, 4, 0, 0, 65535, 1))
    for timestamp, payload, reverse in [(0, client, False), (8500, server, True), (10000, client, False)]:
        packet = datagram(payload, reverse)
        f.write(struct.pack("<IIII", 100, timestamp, len(packet), len(packet)) + packet)
print(out)
