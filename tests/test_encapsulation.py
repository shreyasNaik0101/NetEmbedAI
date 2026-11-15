"""Different link/network headers must yield the same transport-payload features."""

import importlib.util
import shutil
import struct
from pathlib import Path

import pytest

from netembed.capture import tshark_path
from netembed.offline import extract

ROOT = Path(__file__).parents[1]
spec = importlib.util.spec_from_file_location(
    "encapsulation_fixture", ROOT / "scripts/build_encapsulation_fixture.py"
)
builder = importlib.util.module_from_spec(spec)
spec.loader.exec_module(builder)


def test_fixture_is_reproducible_and_headers_are_not_a_constant_offset():
    fixture = ROOT / "tests/fixtures/encapsulation.pcap"
    assert fixture.read_bytes() == builder.build(ROOT / "tests/fixtures/rfc9001.pcap")
    payload = builder.payloads(ROOT / "tests/fixtures/rfc9001.pcap")
    # Hand-derived overheads: Ethernet/VLAN + variable IP header + eight UDP bytes.
    assert [len(builder.packet(p, 1, i)) - len(p) for i, p in enumerate(payload)] == [42, 50, 58]
    assert [len(builder.packet(p, 3, i)) - len(p) for i, p in enumerate(payload)] == [62, 74, 86]


@pytest.mark.parametrize("case", range(4))
def test_constructed_ipv4_and_ipv6_headers_and_udp_checksums_are_valid(case):
    for index, payload in enumerate(builder.payloads(ROOT / "tests/fixtures/rfc9001.pcap")):
        frame = builder.packet(payload, case, index)
        vlan_bytes = 4 * index if case in (1, 3) else 0
        ip = frame[14 + vlan_bytes :]
        if case < 2:
            length = (ip[0] & 15) * 4
            assert builder.checksum(ip[:length]) == 0
            assert struct.unpack_from("!H", ip, 2)[0] == len(ip)
            udp = ip[length:]
            pseudo = ip[12:20] + struct.pack("!BBH", 0, 17, len(udp))
        else:
            extensions = 8 * index if case == 3 else 0
            assert struct.unpack_from("!H", ip, 4)[0] == len(ip) - 40
            udp = ip[40 + extensions :]
            pseudo = ip[8:40] + struct.pack("!I3xB", len(udp), 17)
        assert struct.unpack_from("!H", udp, 4)[0] == len(payload) + 8
        assert builder.checksum(pseudo + udp) == 0


@pytest.mark.parametrize("reference", [False, True])
def test_real_tshark_preserves_payload_units_and_direction_across_all_headers(reference):
    if not Path(tshark_path()).exists() and not shutil.which(tshark_path()):
        pytest.skip("native TShark unavailable; offline integration only")
    result = extract(ROOT / "tests/fixtures/encapsulation.pcap", reference)
    assert len(result["flows"]) == 4 and result["counters"]["ignored"] == 0
    for flow in result["flows"]:
        assert [(p["iat_ms"], p["direction"], p["payload_bytes"]) for p in flow["packets"]] == [
            (0, 1, 1200),
            (8.5, -1, 135),
            (1.5, 1, 1200),
        ]
