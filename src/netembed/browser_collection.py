"""Fixed development roles and feature-only eligibility; never starts capture."""

import json
import re
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path

from .bundle import sha256
from .contract import Flow


def read_plan(path):
    plan = json.loads(Path(path).read_text())
    if plan.get("version") != 3:
        raise ValueError("invalid bounded development plan")
    trials = plan["trials"]
    ids = [row["id"] for row in trials]
    if plan["version"] != 3 or len(ids) != len(set(ids)) or not 1 <= len(ids) <= 6:
        raise ValueError("invalid bounded development plan")
    prior_training, saw_selection = set(), False
    for row in trials:
        if not re.fullmatch(r"(?:instagram|youtube)-dev-0[3-6]", row["id"]) or row["role"] not in (
            "train",
            "selection",
        ):
            raise ValueError("development plan cannot assign calibration/final records")
        if row.get("later_date_than") and row["later_date_than"] not in prior_training:
            raise ValueError("later-date activity must refer to earlier training")
        if row["role"] == "selection":
            saw_selection = True
        elif saw_selection:
            raise ValueError("training cannot follow reserved selection")
        else:
            prior_training.add(row["id"])
    existing = plan["existing_training_trials"]
    if len(existing) != len(set(existing)) or any(
        not re.fullmatch(r"(?:instagram|youtube)-dev-0[12]", name) for name in existing
    ):
        raise ValueError("only original development records may enter existing training")
    expected_train = existing + [r["id"] for r in trials if r["role"] == "train"]
    expected_selection = [r["id"] for r in trials if r["role"] == "selection"]
    if plan["train_trials"] != expected_train or plan["selection_trials"] != expected_selection:
        raise ValueError("development role lists disagree")
    if set(plan["protected_trial_ids"]) & set(expected_train + expected_selection):
        raise ValueError("protected recordings cannot enter new development")
    if plan["eligibility"] != "mapped-valid-prefix-v1":
        raise ValueError("unknown reference eligibility rule")
    return plan


def trial_spec(plan, trial):
    matches = [row for row in plan["trials"] if row["id"] == trial]
    if len(matches) != 1:
        raise ValueError("trial is not reserved by this development plan")
    return matches[0]


def read_collection_plan(path):
    """Dispatch the separately declared extension without loosening v3."""
    if json.loads(Path(path).read_text()).get("kind") == "prospective_selection_followup_protocol":
        from .browser_followup import read_followup

        return read_followup(path)
    return read_plan(path)


def observed_packet_bounds(flows):
    """Bounds of actual retained input packets, including each flow's gaps."""
    if not flows:
        raise ValueError("no retained packet times")
    starts, ends = [], []
    for flow in flows:
        packets = Flow(packets=flow["packets"]).packets
        first = float(flow["connection_match"]["first_packet_unix_ms"])
        starts.append(first)
        ends.append(first + sum(packet.iat_ms for packet in packets))
    return [min(starts), max(ends)]


def eligible_references(reference, parity):
    """No activity name, model label or confidence participates in filtering."""
    checked = {row["flow_id"]: row for row in parity["flows"]}
    mapped = [row for row in reference["flows"] if row["reference"]["status"] == "mapped"]
    if len(checked) != len(parity["flows"]) or set(checked) != {r["flow_id"] for r in mapped}:
        raise ValueError("feature-check inventory differs from mapped references")
    kept, excluded = [], []
    for row in mapped:
        raw = Flow(packets=row["packets"])
        qc = checked[row["flow_id"]]
        reason = (
            "fewer_than_five_observed_packets"
            if len(raw.packets) < 5
            else "socket_not_unique"
            if qc["socket"]["status"] != "unique_socket"
            else "missing_socket_prefix"
            if qc["missing_browser_prefix_packets"]
            or any(v["missing_browser_prefix_packets"] for v in qc["by_direction"].values())
            else "within_direction_size_mismatch"
            if any(v["ordered_payload_size_mismatches"] for v in qc["by_direction"].values())
            else None
        )
        if reason:
            excluded.append({"flow_id": row["flow_id"], "reason": reason})
        else:
            kept.append(row)
    return kept, excluded


def stage_gate(root, plan_path, trial, now_ms):
    """Verify prerequisites from archived evidence, never from model accuracy."""
    from .browser_adaptation import load_reference_trial

    root, plan_path = Path(root), Path(plan_path)
    plan = read_collection_plan(plan_path)
    if "followup_protocol" in plan:
        from .browser_followup import stage_gate as followup_gate

        return followup_gate(root, plan_path, plan, trial, now_ms)
    spec = trial_spec(plan, trial)
    index = [r["id"] for r in plan["trials"]].index(trial)
    prior = plan["trials"][:index]
    missing = [r["id"] for r in prior if not (root / f"{r['id']}-collection-summary.json").exists()]
    if missing:
        raise ValueError("archive earlier recordings first: " + ", ".join(missing))
    if spec.get("later_date_than"):
        name = spec["later_date_than"]
        _, proof = load_reference_trial(root, name, plan["labels"], "development", plan_path)
        zone = timezone(timedelta(minutes=plan["local_utc_offset_minutes"]))
        earlier = datetime.fromtimestamp(proof["first_packet_range_unix_ms"][0] / 1000, zone).date()
        if datetime.fromtimestamp(now_ms / 1000, zone).date() <= earlier:
            raise ValueError("this training activity is reserved for a later local date")
    if spec["role"] == "train":
        return
    records, proofs = [], {}
    for name in plan["train_trials"]:
        bound = plan_path if name in [r["id"] for r in plan["trials"]] else None
        values, proof = load_reference_trial(root, name, plan["labels"], "development", bound)
        records.extend(values)
        proofs[name] = proof
    counts = Counter(row["label"] for row in records)
    if any(counts[label] < minimum for label, minimum in plan["minimum_training_connections"].items()):
        raise ValueError("training reference coverage below fixed targets: " + json.dumps(dict(counts)))
    new_instagram = [
        r["id"] for r in plan["trials"] if r["role"] == "train" and r["id"].startswith("instagram-")
    ]
    times = [proofs[name]["first_packet_range_unix_ms"][0] for name in new_instagram]
    zone = timezone(timedelta(minutes=plan["local_utc_offset_minutes"]))
    dates = {datetime.fromtimestamp(t / 1000, zone).date() for t in times}
    if len(dates) < plan["minimum_new_instagram_training_dates"]:
        raise ValueError("new Instagram training must cover the reserved number of dates")
    latest = max(
        p.get("observed_packet_range_unix_ms", p["first_packet_range_unix_ms"])[1] for p in proofs.values()
    )
    if now_ms < latest + plan["selection_gap_minutes"] * 60000:
        raise ValueError("selection must start after the fixed post-training time gap")


def bound_plan(root, filename):
    if Path(filename).name != filename:
        raise ValueError("collection plan must be a local filename")
    path = Path(root) / filename
    return path, read_plan(path), sha256(path)
