"""Constructed family/role fixtures, never live quality evidence."""

from datetime import datetime, timezone

import pytest

from netembed.bundle import sha256, write_json
from netembed.connection_reference import connection_token
from netembed.family_collection import (
    families_for_rows,
    freeze_training,
    require_cells,
    require_coverage,
    selection_ready,
)
from netembed.paired_study import FAMILY_SHA, check_order, read_plan, collection_status


def config():
    return read_plan("configs/family-development-v1.json")


def rows(label="youtube", family=6):
    return [
        {"id": f"{label}-{family}-{i}", "label": label, "family": family, "packets": 30 if i == 0 else 10}
        for i in range(3)
    ]


def test_training_ipv4_cannot_satisfy_ipv6_gate_and_scores_have_no_role():
    cfg = config()
    spec = cfg["trials"][0]
    with pytest.raises(ValueError, match="shortfall"):
        require_coverage(rows(family=4), spec, cfg)
    values = rows() + rows(family=4)
    for r in values:
        r["prediction"] = "wrong"
        r["confidence"] = 0
    assert require_coverage(values, spec, cfg) == {"youtube:IPv6": 3, "youtube:IPv4": 3}
    assert len(values) == 6


def test_selection_needs_every_cell_and_complete_prefix():
    cfg = config()
    values = [r for label in cfg["local_labels"] for family in (4, 6) for r in rows(label, family)]
    require_cells(values, cfg)
    with pytest.raises(ValueError, match="cell shortfall"):
        require_cells([r for r in values if not (r["label"] == "instagram" and r["family"] == 4)], cfg)
    values[0]["packets"] = 20
    with pytest.raises(ValueError, match="at30"):
        require_cells(values, cfg)


def test_family_is_matched_by_token_not_size():
    salt = "01" * 32
    token = connection_token(("2001:db8::1", 50000), ("2001:db8::2", 443), salt)
    packets = [{"iat_ms": 0, "direction": 1, "payload_bytes": 1250}]
    capture = {
        "fixture": True,
        "reference_enabled": True,
        "connection_matching": {"version": "tuple-hmac-sha256-v1", "salt": salt},
        "flows": [
            {
                "flow_id": "one",
                "packets": packets,
                "connection_match": {"tuple_token": token, "first_packet_unix_ms": 1000},
            }
        ],
    }
    netlog = {
        "constants": {
            "logEventTypes": {"UDP_LOCAL_ADDRESS": 1, "UDP_CONNECT": 2},
            "logSourceType": {"UDP_SOCKET": 3},
            "logEventPhase": {"PHASE_BEGIN": 1},
        },
        "events": [
            {"source": {"type": 3, "id": 1}, "type": 1, "params": {"address": "[2001:db8::1]:50000"}},
            {
                "source": {"type": 3, "id": 1},
                "type": 2,
                "phase": 1,
                "params": {"address": "[2001:db8::2]:443"},
            },
        ],
    }
    r = [{"id": "browser:session:one", "label": "youtube", "packets": packets}]
    assert families_for_rows(capture, netlog, r)[0]["family"] == 6
    netlog["events"] = []
    with pytest.raises(ValueError, match="unavailable"):
        families_for_rows(capture, netlog, r)


def archives(tmp_path):
    cfg = config()
    plan = tmp_path / "family-development-v1.json"
    from pathlib import Path

    plan.write_bytes(Path("configs/family-development-v1.json").read_bytes().replace(b"\r\n", b"\n"))
    start = datetime(2026, 11, 5, tzinfo=timezone.utc).timestamp() * 1000
    reports = []
    for i, spec in enumerate(cfg["trials"][:4]):
        file = tmp_path / (spec["id"] + "-families.json")
        write_json(file, rows(spec["target"]))
        first = start + (i // 2) * 86400000 + (i % 2) * 10000
        report = {
            "trial_id": spec["id"],
            "status": "usable",
            "collection_role": "train",
            "plan_sha256": FAMILY_SHA,
            "session_id": str(i),
            "first_packet_ms": first,
            "last_packet_ms": first + 1000,
            "files": {file.name: sha256(file)},
        }
        write_json(tmp_path / (spec["id"] + "-archive.json"), report)
        reports.append(report)
    return cfg, plan, reports


def test_freeze_preserves_inputs_and_selection_waits_for_fit(tmp_path):
    cfg, plan, reports = archives(tmp_path)
    freeze = freeze_training(tmp_path, cfg, plan)
    assert freeze_training(tmp_path, cfg, plan) == freeze
    with pytest.raises(ValueError, match="bound seed17"):
        selection_ready(tmp_path, cfg, plan)
    status = collection_status(tmp_path, cfg, reports[-1]["last_packet_ms"] + 86400000)
    assert status["next_action"] == "awaiting_frozen_training_and_bound_seed17"
    assert not status["candidate_models_loaded"]
    write_json(tmp_path / (cfg["trials"][0]["id"] + "-families.json"), [])
    with pytest.raises(ValueError, match="changed"):
        freeze_training(tmp_path, cfg, plan)


def test_four_date_order_and_session_reuse(tmp_path):
    cfg, _, previous = archives(tmp_path)
    trial = cfg["trials"][4]["id"]
    with pytest.raises(ValueError, match="duplicate session"):
        check_order(cfg, trial, previous, previous[-1]["last_packet_ms"] + 86400000, "0")
    with pytest.raises(ValueError, match="schedule"):
        check_order(cfg, trial, previous, previous[-1]["last_packet_ms"] + 2000, "fresh")
    check_order(cfg, trial, previous, previous[-1]["last_packet_ms"] + 86400000, "fresh")


def test_family_protocol_digest_cannot_change(tmp_path):
    from pathlib import Path

    target = tmp_path / "changed.json"
    target.write_text(Path("configs/family-development-v1.json").read_text() + " ")
    with pytest.raises(ValueError, match="changed"):
        read_plan(target)


def test_duplicate_flow_cannot_inflate_family_support():
    cfg = config()
    values = rows()
    values[1]["id"] = values[0]["id"]
    with pytest.raises(ValueError, match="duplicate"):
        require_coverage(values, cfg["trials"][0], cfg)
    with pytest.raises(ValueError, match="duplicate"):
        require_cells(values, cfg)


def test_freeze_rejects_reused_session_even_if_hashes_are_valid(tmp_path):
    cfg, plan, previous = archives(tmp_path)
    previous[1]["session_id"] = previous[0]["session_id"]
    write_json(tmp_path / (cfg["trials"][1]["id"] + "-archive.json"), previous[1])
    with pytest.raises(ValueError, match="duplicate session"):
        freeze_training(tmp_path, cfg, plan)
