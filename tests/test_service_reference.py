import json
from types import SimpleNamespace

import pytest

from netembed.capture import Capture, FlowTable, field_args, parse_line
from netembed.service_reference import attribute, merge_reference, summarize
from test_capture import line


@pytest.mark.parametrize(
    "host,label",
    [
        ("www.youtube.com", "youtube"),
        ("R1.GOOGLEVIDEO.COM.", "youtube"),
        ("web.whatsapp.com", "whatsapp"),
        ("discord.com", None),
    ],
)
def test_reference_rules(host, label):
    assert attribute(host)["label"] == label


def test_references_refuse_ambiguous_missing_encrypted_and_unmapped():
    assert attribute("")["status"] == "unavailable"
    assert attribute("bad/host")["status"] == "unavailable"
    assert attribute("www.youtube.com.attacker.test")["status"] == "unmapped"
    assert attribute("example.com")["status"] == "unmapped"
    assert attribute("www.recaptcha.net")["status"] == "outside_supported_set"
    assert attribute("accounts.youtube.com")["status"] == "ambiguous"
    protected = attribute("www.youtube.com", protected_name_indication=True)
    assert protected["status"] == "protected_name_unverified" and protected["label"] is None
    assert "GREASE" in protected["reason"]


def test_reference_is_opt_in_and_does_not_change_packet_features():
    assert "tls.handshake.extensions_server_name" not in field_args()
    assert "tls.handshake.extensions_server_name" in field_args(True)
    states = []
    for host in ("www.youtube.com", "web.whatsapp.com"):
        observation = parse_line(line() + f"\t{host}\t\t", reference=True)
        states.append(FlowTable().ingest(observation))
    assert states[0].packets == states[1].packets
    assert states[0].reference["label"] != states[1].reference["label"]
    assert merge_reference(states[0].reference, states[1].reference)["status"] == "conflicting"


def test_evidence_is_bounded_and_contains_no_names_or_endpoints():
    capture = Capture(SimpleNamespace(identity="fixture", meta={"provenance": {"fixture": True}}))
    capture.reference_enabled = True
    for index in range(260):
        capture.emit(
            {
                "type": "packets",
                "flow_id": str(index),
                "packets": [{"iat_ms": 0, "direction": 1, "payload_bytes": 1200}],
                "reference": attribute("www.youtube.com"),
            }
        )
    evidence = capture.local_evaluation()
    assert evidence["fixture"] is True
    assert len(evidence["flows"]) == 256 and evidence["evidence_evicted"] == 4
    assert "www.youtube.com" not in json.dumps(evidence)
    assert "src" not in json.dumps(evidence) and "dst" not in json.dumps(evidence)


def test_reference_agreement_denominators_include_refusals_and_exclude_unverified():
    rows = []
    for reference, label in (("mapped", "youtube"), ("mapped", None), ("unavailable", "youtube")):
        rows.append(
            {
                "reference": {"status": reference, "label": "youtube" if reference == "mapped" else None},
                "predictions": [
                    {
                        "observed_packets": 5,
                        "label": label,
                        "alternatives": [{"label": "youtube", "score": 0.6}],
                    }
                ],
            }
        )
    result = summarize(rows)
    assert result["5"]["referenced_predictions"] == 2
    assert result["5"]["coverage"] == 0.5
    assert result["5"]["accepted_mismatches"] == 0
    assert result["10"]["coverage"] is None
