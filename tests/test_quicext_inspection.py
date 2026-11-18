"""Inspection cannot turn weak/protected references into training labels."""

import importlib.util
import json
from pathlib import Path

import pytest


@pytest.fixture
def inspector():
    path = Path(__file__).parents[1] / "scripts" / "inspect_quicext25.py"
    spec = importlib.util.spec_from_file_location("quicext_inspector", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def row():
    return {
        "PPI": [[0, 1, 2, 0, 3], [1, -1, 1, -1, 1], [1250, 1200, 50, 45, 40]],
        "PPI_LEN": 5,
        "QUIC_SNI": "www.instagram.com",
        "PROTOCOL": 17,
        "DST_PORT": 443,
        "QUIC_CLIENT_VERSION": 1,
        "QUIC_MULTIPLEXED": 0,
        "QUIC_TLS_EXT_TYPE": [],
        "DST_IP": "must-not-be-retained",
    }


def test_bounded_inspection_excludes_names_and_does_not_create_labels(inspector):
    def rows():
        yield row()
        raise AssertionError("reader exceeded its row budget")

    report = inspector.inspect_rows(rows(), 1)
    assert report["counts"]["inspected_rows"] == 1
    assert report["training_ready"] is False
    assert report["basic_candidates_without_protected_name_by_reference"] == {"instagram": 1}
    encoded = json.dumps(report)
    assert "www.instagram.com" not in encoded and "must-not-be-retained" not in encoded


@pytest.mark.parametrize("extension", [65037, 65486])
def test_protected_reference_stays_excluded_even_when_name_matches(inspector, extension):
    sample = row()
    sample["QUIC_TLS_EXT_TYPE"] = [extension]
    report = inspector.inspect_rows([sample], 1)
    assert report["provisional_name_matches"] == {"instagram": 1}
    assert report["basic_candidates_without_protected_name_by_reference"] == {}


@pytest.mark.parametrize("fault", ["padding", "negative_time", "tcp", "multiplexed"])
def test_invalid_or_ineligible_records_cannot_become_candidates(inspector, fault):
    sample = row()
    if fault == "padding":
        sample["PPI_LEN"] = 4
    elif fault == "negative_time":
        sample["PPI"][0][1] = -1
    elif fault == "tcp":
        sample["PROTOCOL"] = 6
    else:
        sample["QUIC_MULTIPLEXED"] = 1
    report = inspector.inspect_rows([sample], 1)
    assert report["basic_candidates_without_protected_name_by_reference"] == {}
