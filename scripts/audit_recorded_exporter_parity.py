"""Offline current-adapter check against an existing ipfixprobe report; no capture."""

import json
from pathlib import Path

from netembed.bundle import sha256
from netembed.offline import extract

ROOT = Path("artifacts/local/ipfixprobe-recorded")
PCAP = ROOT / "recorded-prefix.pcap"
REFERENCE = ROOT / "final-parity.json"
OUTPUT = Path("experiments/order-parity-spotify-dev-v1/recorded-exporter-recheck.json")
PCAP_SHA = "43ddbef754660921dd23eac69e8605b732ee8643e31b2e188331a161b5b4fb67"
REFERENCE_SHA = "8bca523221639185a2911313a483bfd21a3a662ddce800daaa3160eba9e6acf2"


def main():
    if OUTPUT.exists():
        raise FileExistsError("preserve existing report")
    if sha256(PCAP) != PCAP_SHA or sha256(REFERENCE) != REFERENCE_SHA:
        raise ValueError("recorded prefix or exporter report changed")
    reference = json.loads(REFERENCE.read_text())
    if reference["pcap_sha256"] != PCAP_SHA or reference["reference_version"] != "5.8.0":
        raise ValueError("independent exporter binding differs")
    extracted = extract(PCAP)
    if len(extracted["flows"]) != 1:
        raise ValueError("expected exactly one offline captured connection")
    expected = reference["reference_features"]["packets"]
    actual = extracted["flows"][0]["packets"]
    if len(expected) != 30 or len(actual) != 30:
        raise ValueError("expected exactly thirty prefix packets")
    differences = [abs(a["iat_ms"] - b["iat_ms"]) for a, b in zip(expected, actual)]
    result = {
        "source": "previously recorded pcap prefix; provenance unconfirmed",
        "reference": "saved independent ipfixprobe 5.8.0 output on the same pcap",
        "pcap_sha256": PCAP_SHA,
        "reference_report_sha256": REFERENCE_SHA,
        "adapter_source_sha256": sha256(Path("src/netembed/capture.py")),
        "source_sha256": sha256(Path(__file__)),
        "packet_count": len(actual),
        "first_ten_direction_equal": all(
            a["direction"] == b["direction"] for a, b in zip(expected[:10], actual[:10])
        ),
        "first_ten_payload_size_equal": all(
            a["payload_bytes"] == b["payload_bytes"] for a, b in zip(expected[:10], actual[:10])
        ),
        "all_direction_equal": all(a["direction"] == b["direction"] for a, b in zip(expected, actual)),
        "all_payload_size_equal": all(
            a["payload_bytes"] == b["payload_bytes"] for a, b in zip(expected, actual)
        ),
        "first_ten_max_iat_difference_ms": max(differences[:10]),
        "all_max_iat_difference_ms": max(differences),
        "adapter_counters": extracted["counters"],
        "model_fit": False,
        "model_scored": False,
        "live_capture": False,
        "limits": "One existing prefix of uncertain ownership and network provenance. Current adapter and a saved current exporter output observe the same recorded packets. No service identity, live app quality, browser socket ordering, 2022 exporter equivalence or model improvement is established.",
    }
    with OUTPUT.open("x", encoding="utf-8") as stream:
        json.dump(result, stream, indent=2)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
