"""Launcher contracts; tests do not start a server or capture."""

from types import SimpleNamespace

import pytest
from scripts import serve_showcase


def model(**changes):
    value = {
        "identity": serve_showcase.SHOWCASE_ID,
        "fixed_prefix_packets": 10,
        "meta": {"policy": {"fitted": False}, "provenance": {"fixture": False}},
    }
    value.update(changes)
    return SimpleNamespace(**value)


def test_launcher_validates_profile_without_starting_capture(monkeypatch):
    expected = model()
    monkeypatch.setattr(serve_showcase, "Predictor", lambda _: expected)
    assert serve_showcase.validate_showcase("bundle") is expected


@pytest.mark.parametrize(
    "candidate",
    [
        model(identity="wrong"),
        model(fixed_prefix_packets=30),
        model(meta={"policy": {"fitted": True}, "provenance": {"fixture": False}}),
        model(meta={"policy": {"fitted": False}, "provenance": {"fixture": True}}),
    ],
)
def test_launcher_refuses_wrong_fitted_or_fixture_bundle(monkeypatch, candidate):
    monkeypatch.setattr(serve_showcase, "Predictor", lambda _: candidate)
    with pytest.raises(ValueError, match="genuine unfitted"):
        serve_showcase.validate_showcase("bundle")


def test_archive_inventory_rejects_unexpected_and_oversized_entries():
    from scripts.check_showcase_archive import validate_inventory

    invalid = SimpleNamespace(infolist=lambda: [SimpleNamespace(filename="../escape", file_size=1)])
    with pytest.raises(ValueError, match="archive members"):
        validate_inventory(invalid)
