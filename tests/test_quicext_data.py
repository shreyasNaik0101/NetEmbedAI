import pytest

from netembed.quicext_data import ReferenceLabelMap, packet_window


def sample():
    return {
        "PROTOCOL": 17,
        "DST_PORT": 443,
        "QUIC_CLIENT_VERSION": 1,
        "QUIC_MULTIPLEXED": 0,
        "PPI_LEN": 5,
        "PPI": [[0, 1, 0, 2, 1], [1, -1, -1, 1, -1], [1250, 1200, 50, 60, 40]],
        "QUIC_PACKETS": [129, 133, 128, 128, 128],
    }


def test_background_fallback_does_not_override_specific_service():
    labels = ReferenceLabelMap()
    assert labels.classify("www.messenger.com") == ("mapped", "facebook-messenger")
    assert labels.classify("x.drive.google.com") == ("mapped", "google-drive")
    assert labels.classify("accounts.youtube.com") == ("ambiguous", None)
    assert labels.classify("unlisted.google.com") == ("background", None)


def test_label_boundaries_and_protection():
    labels = ReferenceLabelMap()
    assert labels.classify("www.instagram.com") == ("mapped", "instagram")
    assert labels.classify("www.instagram.com.evil.example") == ("unmapped", None)
    assert labels.classify("instagram.com") == ("mapped", "instagram")
    assert labels.classify("drive.google.com") == ("mapped", "google-drive")
    assert labels.classify("www.instagram.com", protected=True) == ("protected_name_unverified", None)


def test_only_packet_features_are_exported():
    row = sample()
    row.update(QUIC_SNI="www.instagram.com", DST_IP="excluded", QUIC_USER_AGENT="excluded")
    flow = packet_window(row)
    assert set(flow.model_dump()) == {"schema_version", "packets"}
    assert flow.packets[0].payload_bytes == 1250


@pytest.mark.parametrize("code", [129, 131])
def test_initial_and_coalesced_initial_are_eligible(code):
    row = sample()
    row["QUIC_PACKETS"][0] = code
    assert len(packet_window(row).packets) == 5


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("PROTOCOL", 6),
        ("DST_PORT", 80),
        ("QUIC_CLIENT_VERSION", 99),
        ("QUIC_MULTIPLEXED", 1),
        ("QUIC_PACKETS", [128, 129, 133]),
        ("QUIC_PACKETS", []),
        ("PPI_LEN", 4),
    ],
)
def test_unsupported_and_midflow_records_refuse(field, value):
    row = sample()
    row[field] = value
    with pytest.raises(ValueError):
        packet_window(row)
