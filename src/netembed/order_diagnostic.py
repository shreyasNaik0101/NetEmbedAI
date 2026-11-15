"""Summarize saved bidirectional comparisons; no scoring, fitting or capture."""


def summarize(rows, parity, session_id, budget=10):
    if type(budget) is not int or budget < 1:
        raise ValueError("positive integer prefix required")
    index = {}
    for entry in parity["flows"]:
        fid = entry["flow_id"]
        if fid in index:
            raise ValueError("duplicate comparison flow")
        index[fid] = entry
    if parity["session_id"] != session_id:
        raise ValueError("parity session differs")
    result = {
        "eligible": 0,
        "first_prefix_direction_mismatch": 0,
        "first_prefix_size_mismatch": 0,
        "full_prefix_direction_mismatch": 0,
        "full_prefix_size_mismatch": 0,
        "both_directions_size_equal": 0,
    }
    seen = set()
    for row in rows:
        if row["label"] != "spotify" or len(row["packets"]) < budget:
            continue
        prefix = "browser:" + session_id + ":"
        if not row["id"].startswith(prefix) or row["id"] in seen:
            raise ValueError("duplicate or wrong-session flow")
        seen.add(row["id"])
        entry = index[row["id"][len(prefix) :]]
        if (
            entry["socket"]["status"] != "unique_socket"
            or entry["missing_browser_prefix_packets"]
            or entry["capture_packets"] != len(row["packets"])
            or entry["browser_prefix_packets"] < budget
        ):
            raise ValueError("incomplete socket comparison")
        direction, sizes = (
            entry["merged_direction_mismatch_indices"],
            entry["merged_payload_size_mismatch_indices"],
        )
        if any(type(i) is not int or i < 0 or i >= len(row["packets"]) for i in direction + sizes):
            raise ValueError("invalid mismatch index")
        result["eligible"] += 1
        result["first_prefix_direction_mismatch"] += int(any(i < budget for i in direction))
        result["first_prefix_size_mismatch"] += int(any(i < budget for i in sizes))
        result["full_prefix_direction_mismatch"] += int(bool(direction))
        result["full_prefix_size_mismatch"] += int(bool(sizes))
        result["both_directions_size_equal"] += int(
            all(entry["by_direction"][str(d)]["ordered_payload_sizes_equal"] for d in (1, -1))
        )
    return result
