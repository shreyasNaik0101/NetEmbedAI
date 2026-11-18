"""Constructed workflow fixtures, never evidence of real model quality."""

from copy import deepcopy
from datetime import datetime, timezone
import json
from pathlib import Path

import numpy as np
import pytest

from netembed.bundle import sha256, write_json
from netembed.contract import Flow
from netembed.fresh_evaluation import (
    evaluation_coverage,
    frozen_models,
    offline_guard,
    score_evaluation,
    summarize,
)
from netembed.paired_study import IPV6_EVALUATION_SHA, read_plan


PLAN = Path("configs/ipv6-frozen-evaluation-v1.json")


def config():
    return read_plan(PLAN)


def test_declaration_locks_forest_pair_and_excludes_fitting(tmp_path):
    cfg = config()
    assert len(cfg["trials"]) == 4
    assert {s["role"] for s in cfg["trials"]} == {"evaluation"}
    assert cfg["workflow"] == "ipv6_frozen_evaluation"
    assert set(cfg["models"]) == {"control", "plus-real-ipv6"}
    changed = tmp_path / "plan.json"
    write_json(changed, {**cfg, "budgets": [10]})
    with pytest.raises(ValueError, match="changed"):
        read_plan(changed)


def test_coverage_requires_complete_target_ipv6_and_exact_family_inventory():
    cfg = config()
    spec = cfg["trials"][0]
    rows = [{"id": "fixture", "label": "youtube", "packets": [None] * 30}]
    families = [{"id": "fixture", "label": "youtube", "packets": 30, "family": 6}]
    assert evaluation_coverage(rows, families, spec, cfg) == {"youtube:IPv6": 1}
    for bad in ({"family": 4}, {"label": "instagram"}, {"packets": 29}, {"id": "other"}):
        with pytest.raises(ValueError):
            evaluation_coverage(rows, [{**families[0], **bad}], spec, cfg)
    with pytest.raises(ValueError, match="inventory"):
        evaluation_coverage(rows * 2, families, spec, cfg)


def test_frozen_model_weight_or_metadata_mutation_is_rejected(tmp_path, monkeypatch):
    import netembed.fresh_evaluation as mod

    cfg = config()
    for name, spec in cfg["models"].items():
        bundle = tmp_path / name
        bundle.mkdir()
        (bundle / "metadata.json").write_text("fixture metadata")
        (bundle / "forest.json").write_text("fixture weights")
        spec.update(
            bundle=str(bundle),
            metadata_sha256=sha256(bundle / "metadata.json"),
            weight_sha256=sha256(bundle / "forest.json"),
        )

    class Fake:
        meta = {"kind": "forest", "policy": {"fitted": False}}
        labels = ["youtube", "instagram"]

    monkeypatch.setattr(mod, "Predictor", lambda path: Fake())
    assert len(frozen_models(cfg)) == 2
    path = Path(cfg["models"]["control"]["bundle"]) / "forest.json"
    path.write_text("mutated weights")
    with pytest.raises(ValueError, match="changed"):
        frozen_models(cfg)


@pytest.mark.parametrize(
    "event,args",
    [
        ("socket.connect", ()),
        ("socket.getaddrinfo", ()),
        ("open", ("data/processed/v2/selection.jsonl",)),
        ("open", ("artifacts/local/hotspot-fresh-sessions-v1/fresh-yt-01-rows.json",)),
        ("open", ("experiments/ipv6-realdata-pilot-v1/plus-real-ipv6/predictions.json",)),
        ("open", ("artifacts/local/ipv6-frozen-evaluation-v1/excluded-prior-old/capture.json",)),
    ],
)
def test_offline_guard_blocks_prior_data_and_network(event, args):
    with pytest.raises(ValueError):
        offline_guard(event, args, "artifacts/local/ipv6-frozen-evaluation-v1")
    offline_guard(
        "open",
        ("artifacts/local/ipv6-frozen-evaluation-v1/ipv6-eval-yt-01-rows.json",),
        "artifacts/local/ipv6-frozen-evaluation-v1",
    )
    offline_guard(
        "open",
        ("experiments/ipv6-realdata-pilot-v1/plus-real-ipv6/bundle/forest.json",),
        "artifacts/local/ipv6-frozen-evaluation-v1",
    )


def archive_fixture(root, cfg, spec, index):
    start = datetime(2026, 11, 6, tzinfo=timezone.utc).timestamp() * 1000
    start += (spec["day"] - 1) * 86400000 + index * 10000
    trial, session = spec["id"], str(index)
    raw = np.tile([1, 1, 1200 if spec["target"] == "youtube" else 200], (30, 1))
    raw[0, 0] = 0
    rows = [
        {
            "id": f"browser:{session}:fixture",
            "label": spec["target"],
            "packets": Flow.from_array(raw).model_dump()["packets"],
        }
    ]
    values = {
        "rows": rows,
        "families": [{"id": rows[0]["id"], "label": spec["target"], "packets": 30, "family": 6}],
        "intent": {
            "collection_role": "evaluation",
            "collection_plan_sha256": sha256(PLAN),
            "chrome_closed_before_intent": True,
            "recorded_before_capture_utc": datetime.fromtimestamp(
                (start - 1000) / 1000, timezone.utc
            ).isoformat(),
        },
        "browser-processes": {
            "session_id": session,
            "plan_sha256": sha256(PLAN),
            "processes": [{"pid": 100 + index, "started_unix_ms": start - 500}],
        },
    }
    for name, value in values.items():
        write_json(root / f"{trial}-{name}.json", value)
    write_json(
        root / f"{trial}-archive.json",
        {
            "trial_id": trial,
            "collection_role": "evaluation",
            "status": "usable",
            "session_id": session,
            "plan_sha256": IPV6_EVALUATION_SHA,
            "first_packet_ms": start,
            "last_packet_ms": start + 1000,
            "files": {f"{trial}-{name}.json": sha256(root / f"{trial}-{name}.json") for name in values},
        },
    )


def test_score_waits_for_all_visits_pairs_actual_prefixes_and_preserves_outputs(tmp_path, monkeypatch):
    import netembed.fresh_evaluation as mod

    cfg, calls = config(), {"control": [], "plus-real-ipv6": []}

    class Fake:
        labels = ["youtube", "instagram"]

        def __init__(self, name):
            self.name = name

        def probabilities(self, batch):
            raw = batch[0]
            calls[self.name].append(raw.copy())
            correct = self.name == "plus-real-ipv6" and raw[0, 2] == 200
            return np.array([[0.1, 0.9] if correct else [0.9, 0.1]])

        def predict(self, raw):
            return {"label": None, "status": "uncalibrated"}

    monkeypatch.setattr(mod, "frozen_models", lambda cfg: {arm: Fake(arm) for arm in calls})
    for i, spec in enumerate(cfg["trials"][:3]):
        archive_fixture(tmp_path, cfg, spec, i)
    with pytest.raises(FileNotFoundError):
        score_evaluation(tmp_path, cfg, PLAN)
    assert not any(calls.values()) and not (tmp_path / "paired-predictions.json").exists()
    archive_fixture(tmp_path, cfg, cfg["trials"][3], 3)
    output = score_evaluation(tmp_path, cfg, PLAN)
    result = json.loads(output.read_text())
    assert result["status"] == "promising_fresh_screen"
    assert result["metrics"]["primary_paired_difference"] == 0.5
    assert result["default_promoted"] is result["policy_fitted"] is False
    assert len(calls["control"]) == len(calls["plus-real-ipv6"]) == 16
    for a, b in zip(*calls.values()):
        np.testing.assert_array_equal(a, b)
    digest = sha256(output)
    with pytest.raises(ValueError, match="preserve"):
        score_evaluation(tmp_path, cfg, PLAN)
    assert sha256(output) == digest


def test_target_visit_balancing_ignores_incidental_volume_and_exposes_class_loss():
    cfg = config()
    rows = []
    for i, spec in enumerate(cfg["trials"]):
        for _ in range(50 if i == 0 else 1):
            label = spec["target"]
            rows.append(
                {
                    "trial": spec["id"],
                    "reference": label,
                    "family": 6,
                    "budget": 10,
                    "control": {"raw_top1": label, "accepted_label": None},
                    "plus-real-ipv6": {"raw_top1": "youtube", "accepted_label": None},
                }
            )
    incidental = deepcopy(rows[0])
    incidental["trial"] = cfg["trials"][1]["id"]
    rows += [incidental] * 100
    result = summarize(rows, cfg, ["youtube", "instagram"])
    assert result["control"]["10"]["target_session_balanced_macro_recall"] == 1
    assert result["plus-real-ipv6"]["10"]["target_session_balanced_macro_recall"] == 0.5
    assert result["descriptive_screen_pass"] is False
    assert result["plus-real-ipv6"]["10"]["family_cells"]["instagram:IPv4"]["recall"] is None
