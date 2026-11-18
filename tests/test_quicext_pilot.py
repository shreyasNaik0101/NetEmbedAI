import importlib.util
import json
from pathlib import Path

import pytest

from netembed.data import read_split


@pytest.fixture
def pilot():
    path = Path(__file__).parents[1] / "scripts" / "prepare_quicext_pilot.py"
    spec = importlib.util.spec_from_file_location("quicext_pilot", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.mark.parametrize("fault", ["same_day", "reverse", "reserved_overlap", "excessive_budget"])
def test_protocol_rejects_leakage_and_unbounded_budgets(pilot, fault):
    path = Path(__file__).parents[1] / "configs" / "quicext25-pilot.json"
    protocol = json.loads(path.read_text())
    if fault == "same_day":
        protocol["days"]["selection"] = protocol["days"]["train"]
    elif fault == "reverse":
        protocol["days"]["train"] = "20250504"
    elif fault == "reserved_overlap":
        protocol["reserved_final_days_not_downloaded"] = ["20250502"]
    else:
        protocol["per_class_caps"]["train"] = 100000
    with pytest.raises(ValueError):
        pilot.validate_protocol(protocol)


def test_no_pilot_final_data_is_inferred_or_opened(tmp_path):
    (tmp_path / "manifest.json").write_text(json.dumps({"files": {}}))
    with pytest.raises(ValueError, match="not materialized"):
        read_split(tmp_path, "test", allow_final=True)


def test_export_preserves_units_excludes_protected_and_redacts(pilot, tmp_path):
    pa = pytest.importorskip("pyarrow")
    pq = pytest.importorskip("pyarrow.parquet")
    common = {
        "PROTOCOL": 17,
        "DST_PORT": 443,
        "QUIC_CLIENT_VERSION": 1,
        "QUIC_MULTIPLEXED": 0,
        "PPI_LEN": 5,
        "PPI": [[0, 0, 2, 1, 0], [1, -1, 1, -1, 1], [1250, 1200, 45, 50, 30]],
        "QUIC_PACKETS": [129, 133, 128, 128, 128],
        "QUIC_OCCID": "client",
        "QUIC_OSCID": "server",
        "DST_IP": "private-destination",
    }
    source = [
        {**common, "QUIC_SNI": "www.instagram.com", "QUIC_TLS_EXT_TYPE": []},
        {**common, "QUIC_SNI": "www.instagram.com", "QUIC_TLS_EXT_TYPE": [65037]},
        {**common, "QUIC_SNI": "drive.google.com", "QUIC_TLS_EXT_TYPE": [], "QUIC_OSCID": "another"},
    ]
    path = tmp_path / "day.parquet"
    pq.write_table(pa.Table.from_pylist(source), path)
    rows, report = pilot.export_day(path, "20250501", cap=5)
    assert [r["label"] for r in rows] == ["instagram", "google-drive"]
    assert report["reference_statuses"]["protected_name_unverified"] == 1
    assert rows[0]["packets"][2] == {"iat_ms": 2.0, "direction": 1, "payload_bytes": 45}
    assert rows[0]["group_id"] != rows[1]["group_id"]
    encoded = json.dumps(rows)
    for excluded in ("www.instagram.com", "drive.google.com", "private-destination", '"client"', '"server"'):
        assert excluded not in encoded
