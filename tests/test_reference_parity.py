import pytest
import json
from pathlib import Path

from netembed.bundle import sha256

from netembed.reference_parity import parse_pstats_text


def test_committed_reference_binds_real_exporter_output_to_the_protocol_fixture():
    fixtures = Path(__file__).parent / "fixtures"
    report = json.loads((fixtures / "rfc9001.ipfixprobe-reference.json").read_text())
    output = fixtures / "rfc9001.ipfixprobe.stdout.txt"
    assert report["fixture"] is True and report["reference_version"] == "5.8.0"
    assert report["pcap_sha256"] == sha256(fixtures / "rfc9001.pcap")
    assert report["reference_stdout_sha256"] == sha256(output)
    assert parse_pstats_text(output.read_text()).model_dump() == report["reference_features"]


def test_pstats_unpadded_microseconds_are_not_decimal_seconds():
    text = "ppisizes=(1200,135,1200),ppitimes=(100.0,100.8500,100.10000),ppiflags=(0,0,0),ppidirs=(1,-1,1)"
    flow = parse_pstats_text(text)
    assert [p.iat_ms for p in flow.packets] == [0, 8.5, 1.5]
    assert [p.payload_bytes for p in flow.packets] == [1200, 135, 1200]
    assert [p.direction for p in flow.packets] == [1, -1, 1]


@pytest.mark.parametrize(
    "text",
    [
        "",
        "ppisizes=(1),ppitimes=(1.1000000),ppiflags=(0),ppidirs=(1)",
        "ppisizes=(1,2),ppitimes=(2.0,1.0),ppiflags=(0,0),ppidirs=(1,-1)",
        "ppisizes=(1),ppitimes=(1.0),ppiflags=(0),ppidirs=(0)",
    ],
)
def test_incompatible_reference_output_is_rejected(text):
    with pytest.raises(ValueError):
        parse_pstats_text(text)
