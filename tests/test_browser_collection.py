"""Constructed control/metadata fixtures only; no genuine live validation."""

import copy
import json
from datetime import datetime
from pathlib import Path
from types import SimpleNamespace

import pytest

from netembed.browser_adaptation import load_reference_trial, load_role_trial
from netembed.browser_collection import eligible_references, observed_packet_bounds, read_plan, stage_gate
from scripts import collect_browser


@pytest.fixture
def plan_path(tmp_path):
    source = Path(__file__).resolve().parents[1] / "configs/browser-collection-v3.json"
    target = tmp_path / source.name
    target.write_bytes(source.read_bytes())
    return target


@pytest.mark.parametrize("case", ["duplicate", "calibration", "existing_calibration", "role_list"])
def test_plan_refuses_role_reassignment(plan_path, case):
    plan = json.loads(plan_path.read_text())
    if case == "duplicate":
        plan["trials"][1]["id"] = plan["trials"][0]["id"]
    elif case == "calibration":
        plan["trials"][0]["id"] = "instagram-cal-02"
    elif case == "existing_calibration":
        plan["existing_training_trials"][0] = "instagram-cal-02"
    else:
        plan["train_trials"].append("instagram-dev-06")
    plan_path.write_text(json.dumps(plan))
    with pytest.raises(ValueError):
        read_plan(plan_path)


def test_new_selection_cannot_enter_training_even_with_a_valid_plan(plan_path):
    cfg = {"reference_collection_plan_filename": plan_path.name}
    with pytest.raises(ValueError, match="role cannot be interchanged"):
        load_role_trial(plan_path.parent, "instagram-dev-06", "train", ["instagram"], cfg, {})
    with pytest.raises(ValueError, match="unexpected trial role"):
        load_reference_trial(plan_path.parent, "instagram-dev-03", ["instagram"], "development")


def test_fixed_eligibility_preserves_refusals_and_ignores_model_confidence():
    def row(ident, count):
        return {
            "flow_id": ident,
            "packets": [{"iat_ms": 0, "direction": 1, "payload_bytes": 100}] * count,
            "reference": {"status": "mapped", "label": "instagram"},
            "predictions": [{"label": "whatsapp", "score": 0.99}],
        }

    reference = {"fixture": True, "flows": [row("keep", 5), row("short", 3), row("bad-size", 6)]}
    reference["flows"].append({"flow_id": "unmatched", "reference": {"status": "unmatched_connection"}})
    qc = {
        "fixture": True,
        "flows": [
            {
                "flow_id": ident,
                "socket": {"status": "unique_socket"},
                "missing_browser_prefix_packets": 0,
                "by_direction": {
                    "1": {
                        "missing_browser_prefix_packets": 0,
                        "ordered_payload_size_mismatches": int(ident == "bad-size"),
                    }
                },
            }
            for ident in ("keep", "short", "bad-size")
        ],
    }
    original = copy.deepcopy(reference)
    kept, excluded = eligible_references(reference, qc)
    assert [r["flow_id"] for r in kept] == ["keep"]
    assert [r["reason"] for r in excluded] == [
        "fewer_than_five_observed_packets",
        "within_direction_size_mismatch",
    ]
    assert reference == original
    reference["flows"][0]["predictions"] = [{"label": "instagram", "score": 0.01}]
    assert [r["flow_id"] for r in eligible_references(reference, qc)[0]] == ["keep"]
    qc["flows"].append(qc["flows"][0])
    with pytest.raises(ValueError, match="inventory"):
        eligible_references(reference, qc)


def test_archive_stops_before_reading_or_starting_capture_when_running(tmp_path, monkeypatch):
    calls = []

    def get(base, route):
        calls.append(route)
        return b'{"running": true}'

    monkeypatch.setattr(collect_browser, "get", get)
    with pytest.raises(ValueError, match="stop capture"):
        collect_browser.snapshot(
            SimpleNamespace(trial="instagram-dev-03", service="http://localhost:8001"), tmp_path, {}
        )
    assert calls == ["/capture/status"] and not list(tmp_path.iterdir())


def test_fixture_capture_is_refused():
    with pytest.raises(ValueError, match="does not match"):
        collect_browser.validate_snapshot({"fixture": True}, {}, {}, "software-fixture")


@pytest.mark.parametrize(
    "url", ["https://example.com", "http://example.com", "http://localhost/other", "http://user@localhost"]
)
def test_collection_client_does_not_send_metadata_to_remote_urls(url, monkeypatch):
    monkeypatch.setattr(collect_browser, "urlopen", lambda *a, **k: pytest.fail("unexpected network request"))
    with pytest.raises(ValueError, match="loopback"):
        collect_browser.get(url, "/capture/status")


def test_partial_archival_is_idempotent_and_never_overwrites(tmp_path):
    path = tmp_path / "fixture-evidence.json"
    content = b'{"fixture":true}'
    collect_browser.write_once(path, content)
    collect_browser.write_once(path, content)
    with pytest.raises(ValueError, match="overwrite"):
        collect_browser.write_once(path, b"changed")
    assert path.read_bytes() == content


def fake_stage_inputs(plan_path, monkeypatch, instagram_per_new_trial=5):
    import netembed.browser_adaptation as adaptation

    plan = read_plan(plan_path)
    first = datetime.fromisoformat("2026-10-27T12:00:00+00:00").timestamp() * 1000
    for spec in plan["trials"][:4]:
        (plan_path.parent / f"{spec['id']}-collection-summary.json").write_text('{"fixture":true}')

    def load(root, name, labels, stage, bound=None):
        label = name.split("-")[0]
        n = (
            instagram_per_new_trial
            if name in ("instagram-dev-03", "instagram-dev-04", "instagram-dev-05")
            else 3
            if label == "instagram" and name.endswith("01")
            else 2
            if label == "instagram"
            else 6
        )
        start = first + (86400000 if name == "instagram-dev-05" else 0)
        return [{"label": label, "fixture": True}] * n, {"first_packet_range_unix_ms": [start, start + 1000]}

    monkeypatch.setattr(adaptation, "load_reference_trial", load)
    return first


def test_preparation_blocks_the_later_date_activity_too_early(plan_path, monkeypatch):
    first = fake_stage_inputs(plan_path, monkeypatch)
    with pytest.raises(ValueError, match="later local date"):
        stage_gate(plan_path.parent, plan_path, "instagram-dev-05", first + 10000)
    stage_gate(plan_path.parent, plan_path, "instagram-dev-05", first + 86400000)


def test_selection_waits_for_training_gap_and_class_coverage(plan_path, monkeypatch):
    first = fake_stage_inputs(plan_path, monkeypatch)
    with pytest.raises(ValueError, match="post-training time gap"):
        stage_gate(plan_path.parent, plan_path, "instagram-dev-06", first + 86400000 + 2000)
    stage_gate(plan_path.parent, plan_path, "instagram-dev-06", first + 86400000 + 3602000)
    fake_stage_inputs(plan_path, monkeypatch, instagram_per_new_trial=4)
    with pytest.raises(ValueError, match="coverage below"):
        stage_gate(plan_path.parent, plan_path, "instagram-dev-06", first + 3 * 86400000)


def test_later_trial_is_not_prepared_before_archiving_the_first(plan_path):
    with pytest.raises(ValueError, match="archive earlier recordings"):
        stage_gate(plan_path.parent, plan_path, "instagram-dev-04", 0)


def test_observed_bounds_include_a_longer_prefix_from_an_earlier_connection():
    def flow(start, gaps):
        return {
            "connection_match": {"first_packet_unix_ms": start},
            "packets": [{"iat_ms": gap, "direction": 1, "payload_bytes": 100} for gap in gaps],
        }

    # Constructed metadata fixture: the latest-starting connection ends first.
    assert observed_packet_bounds([flow(1000, [0, 2000, 4000]), flow(5000, [0, 10])]) == [1000, 7000]


def test_selection_gap_starts_after_last_retained_packet_not_connection_start(plan_path, monkeypatch):
    import netembed.browser_adaptation as adaptation

    first = fake_stage_inputs(plan_path, monkeypatch)
    previous = adaptation.load_reference_trial

    def with_observed_end(*args, **kwargs):
        rows, proof = previous(*args, **kwargs)
        start = proof["first_packet_range_unix_ms"][0]
        proof["observed_packet_range_unix_ms"] = [start, start + 90000]
        return rows, proof

    monkeypatch.setattr(adaptation, "load_reference_trial", with_observed_end)
    latest_start = first + 86400000
    with pytest.raises(ValueError, match="post-training time gap"):
        stage_gate(plan_path.parent, plan_path, "instagram-dev-06", latest_start + 3601000)
    stage_gate(plan_path.parent, plan_path, "instagram-dev-06", latest_start + 3691000)
