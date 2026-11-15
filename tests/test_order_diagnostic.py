"""Synthetic comparison contracts, not captured traffic or model evidence."""

from copy import deepcopy
import pytest
from netembed.order_diagnostic import summarize


def sample():
    rows = [{"id": "browser:session:one", "label": "spotify", "packets": [{}] * 30}]
    entry = {
        "flow_id": "one",
        "socket": {"status": "unique_socket"},
        "capture_packets": 30,
        "browser_prefix_packets": 30,
        "missing_browser_prefix_packets": 0,
        "merged_direction_mismatch_indices": [9, 20],
        "merged_payload_size_mismatch_indices": [10],
        "by_direction": {str(d): {"ordered_payload_sizes_equal": True} for d in (1, -1)},
    }
    return rows, {"session_id": "session", "flows": [entry]}


def test_prefix_boundary_and_within_direction_are_separate():
    rows, parity = sample()
    result = summarize(rows, parity, "session")
    assert result == {
        "eligible": 1,
        "first_prefix_direction_mismatch": 1,
        "first_prefix_size_mismatch": 0,
        "full_prefix_direction_mismatch": 1,
        "full_prefix_size_mismatch": 1,
        "both_directions_size_equal": 1,
    }


@pytest.mark.parametrize("problem", ["duplicate", "missing", "out_of_range", "wrong_session"])
def test_bad_comparison_is_not_silently_counted(problem):
    rows, parity = sample()
    if problem == "duplicate":
        parity["flows"].append(deepcopy(parity["flows"][0]))
    elif problem == "missing":
        parity["flows"][0]["missing_browser_prefix_packets"] = 1
    elif problem == "out_of_range":
        parity["flows"][0]["merged_direction_mismatch_indices"] = [30]
    else:
        parity["session_id"] = "another"
    with pytest.raises(ValueError):
        summarize(rows, parity, "session")
