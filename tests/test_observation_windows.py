import asyncio

import pytest

from netembed.capture import Capture, FlowTable, Observation
from netembed.observation_windows import ObservationWindows
from netembed.traffic_assessment import assess


def observation(milliseconds=0, port=50000):
    ns = 100000000000 + milliseconds * 1000000
    return Observation(ns / 1000000000, ns, ("192.0.2.1", port), ("198.51.100.1", 443), 1200, True)


def test_window_excludes_future_and_keeps_udp_units_and_directions():
    window = ObservationWindows(100000000000, 0)
    window.add(100000000000, 1, 1200)
    window.add(100500000000, -1, 800)
    window.add(101000000000, 1, 200)  # Boundary is excluded from the first window.
    window.add(103000000000, -1, 999)  # Excluded from both windows.
    first, third = window.snapshot(4)["windows"]
    assert first["client_bytes"] == 1200 and first["server_bytes"] == 800
    assert first["mean_payload_bytes"] == 1000 and first["std_payload_bytes"] == 200
    assert first["state"] == third["state"] == "elapsed"
    assert third["client_packets"] == 2 and third["server_packets"] == 1
    assert sum(sum(bin_) for bin_ in third["packets_by_100ms_client_server"]) == 3


def test_late_parsing_revises_counts_explicitly_and_reordering_is_not_hidden():
    window = ObservationWindows(100000000000, 0)
    window.add(100000000000, 1, 100)
    window.snapshot(1.1)
    window.add(100500000000, -1, 200)
    window.add(100400000000, 1, 400)
    result = window.snapshot(1.2)
    assert result["windows"][0]["late_packets_after_elapsed_snapshot"] == 1
    assert result["reordered_packets_excluded"] == 1
    assert result["windows"][0]["server_bytes"] == 200
    assert result["activity_label"] is None


def test_wider_window_keeps_collecting_after_the_model_prefix_freezes():
    table = FlowTable(observation_windows=True)
    state = None
    for i in range(100):
        result = table.ingest(observation(i), now=i / 1000)
        state = result or state
    assert len(state.packets) == 30 and table.counters["frozen"] == 70
    assert state.windows.snapshot(4)["windows"][1]["client_packets"] == 100
    assert len(state.windows.bins) == 30
    plain = FlowTable().ingest(observation(), now=0)
    assert plain.windows is None  # Explicit opt-in; legacy prefix remains unchanged.


def test_early_stop_and_bounded_export_cleanup_without_opening_interface():
    async def scenario():
        c = Capture(None)
        c.window_enabled = True
        c.table = FlowTable(observation_windows=True)
        c.table.ingest(observation(), now=0)
        c.window_tick(now=0.2, stopped=True)
        assert c.window_export()["source"] == "not_started"
        assert c.window_export()["flows"][0]["observation"]["windows"][0]["state"] == "stopped_early"
        c.table = FlowTable(limit=300, observation_windows=True)
        for i in range(270):
            c.table.ingest(observation(port=50000 + i), now=0)
        c.window_tick(now=4)
        assert len(c.window_evidence) == 256 and c.window_evidence_evicted == 15
        await c.stop()
        assert not c.table.states and len(c.window_evidence) == 256
        assert not c.running

    asyncio.run(scenario())


@pytest.mark.parametrize("status", ["conflicting", "ambiguous", "unavailable", "protected_name_unverified"])
def test_metadata_refusals_cannot_be_overridden_by_model_confidence(status):
    result = assess(
        {"status": status, "label": None},
        {"status": "classified", "label": "youtube", "alternatives": [{"label": "youtube", "score": 0.99}]},
    )
    assert result["identity"]["label"] is None
    assert result["packet_model"]["label"] == "youtube"
    assert result["identity_accuracy_eligible_against_name_derived_truth"] is False


def test_hybrid_conflict_keeps_both_sources_and_does_not_average_scores():
    result = assess({"status": "mapped", "label": "instagram"}, {"status": "classified", "label": "youtube"})
    assert result["identity"] == {"label": "instagram", "basis": "visible_handshake_name_map", "score": None}
    assert result["packet_model"]["label"] == "youtube"
    assert result["relationship"] == "conflicts"
