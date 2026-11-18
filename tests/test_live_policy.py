"""Constructed operational/decision fixtures, never evidence of real capture."""

from copy import deepcopy
import importlib
from pathlib import Path
from types import SimpleNamespace

import pytest

from netembed.bundle import sha256
from netembed.live_policy import (
    live_stats,
    load_model,
    offline_guard,
    policy_metrics,
    score_live,
    timing_metrics,
)
from netembed.paired_study import read_plan


def config():
    return read_plan("configs/ipv6-live-policy-v1.json")


def decision(label=None):
    return {"label": label, "alternatives": [{"label": "youtube", "score": 0.8}]}


def test_missing_live_checkpoint_is_not_a_refusal_or_filled_by_correct_replay():
    points = [
        {"reference": "youtube", "live_prediction": value}
        for value in (None, decision(), decision("youtube"))
    ]
    result = live_stats(points)
    assert result["eligible_flow_checkpoints"] == 3 and result["emitted"] == 2
    assert result["missing_live_checkpoint"] == 1 and result["refused"] == 1
    assert result["end_to_end_coverage"] == pytest.approx(1 / 3)
    assert result["conditional_model_coverage"] == 0.5 and result["accepted_error"] == 0


def test_perfect_replay_cannot_pass_actual_live_acceptance_gate():
    rows = [
        {
            "budget": 10,
            "reference": label,
            "target": label,
            "live_prediction": None,
            "replay_prediction": {"alternatives": [{"label": label}]},
        }
        for label in config()["local_labels"]
    ]
    result = policy_metrics(rows, config())
    assert result["budgets"]["10"]["replay_correct_secondary"] == 2
    assert result["policy_screen_pass"] is False
    assert result["budgets"]["10"]["overall_target"]["accepted_error"] is None


def test_actual_browser_receipts_are_required_and_timing_is_separate():
    timing = {
        "timing_samples": [
            {"capture_to_parser_ms": 10.0, "queue_ms": 1.0, "pipeline_ms": 2.0, "capture_to_event_ms": 13.0}
        ],
        "capture_to_browser_receipt_ms": [],
        "drops": 0,
        "coalesced": 0,
        "receipt_tracking_evicted": {},
        "receipt_tracking_pending": {},
        "running": False,
    }
    audit = {"original_live_prediction_comparison": {"predictions": 1}}
    result = timing_metrics(timing, {"evidence_evicted": 0}, audit)
    assert not result["operational_screen_pass"]
    assert result["capture_to_browser_receipt_ms"]["p50_ms"] is None
    timing["capture_to_browser_receipt_ms"] = [20.0, 30.0]
    result = timing_metrics(timing, {"evidence_evicted": 0}, audit)
    assert result["operational_screen_pass"] and result["capture_to_browser_receipt_ms"]["p50_ms"] == 25
    timing["drops"] = 1
    assert not timing_metrics(timing, {"evidence_evicted": 0}, audit)["operational_screen_pass"]


@pytest.mark.parametrize(
    "event,args",
    [
        ("socket.connect", ()),
        ("socket.getaddrinfo", ()),
        ("open", ("data/processed/v2/calibration.jsonl",)),
        ("open", ("data/processed/v2/test.jsonl",)),
        ("open", ("artifacts/local/ipv6-frozen-evaluation-v1/paired-predictions.json",)),
        ("open", ("experiments/ipv6-public-policy-v1/decision.json",)),
        ("open", ("artifacts/local/ipv6-live-policy-v1/excluded-prior-old/capture.json",)),
    ],
)
def test_live_score_excludes_old_outcomes_and_external_data(event, args):
    cfg = config()
    with pytest.raises(ValueError):
        offline_guard(event, args, "artifacts/local/ipv6-live-policy-v1", cfg)
    offline_guard(
        "open", (cfg["source_bundle"] + "/forest.json",), "artifacts/local/ipv6-live-policy-v1", cfg
    )


def test_model_requires_exact_fitted_policy_and_weights(tmp_path, monkeypatch):
    import netembed.live_policy as module

    cfg = config()
    (tmp_path / "forest.json").write_text("fixture weights")
    cfg.update(source_bundle=str(tmp_path), source_weight_sha256=sha256(tmp_path / "forest.json"))

    class Fake:
        identity = cfg["source_artifact_id"]
        meta = {
            "kind": "forest",
            "policy": deepcopy(cfg["expected_policy"]),
            "provenance": {"fixture": False},
        }

    monkeypatch.setattr(module, "Predictor", lambda path: Fake())
    load_model(cfg)
    Fake.meta["policy"]["threshold"] = 0.1
    with pytest.raises(ValueError, match="changed"):
        load_model(cfg)


def test_expanded_profile_is_required_before_consuming_an_attempt(tmp_path, monkeypatch):
    monkeypatch.syspath_prepend(str(Path("scripts").resolve()))
    cli = importlib.import_module("paired_capture")
    monkeypatch.setattr(cli, "get", lambda *args: pytest.fail("no capture service access expected"))
    with pytest.raises(ValueError, match="expanded-netlog"):
        cli.archive(SimpleNamespace(expanded_netlog=False), tmp_path, config(), Path("unused"))
    assert not list(tmp_path.iterdir())


def test_new_scope_is_two_visits_no_fitting_and_scoring_waits_for_both(tmp_path, monkeypatch):
    import netembed.live_policy as module

    cfg = config()
    assert len(cfg["trials"]) == 2 and cfg["expected_policy"]["threshold"] == 0.76
    assert {s["role"] for s in cfg["trials"]} == {"live_policy_evaluation"}
    monkeypatch.setattr(module, "load_model", lambda cfg: pytest.fail("must not score incomplete cohort"))
    with pytest.raises(FileNotFoundError):
        score_live(tmp_path, cfg, Path("configs/ipv6-live-policy-v1.json"))


@pytest.mark.parametrize("emit_primary", [False, True])
def test_complete_fixture_scores_actual_emissions_not_replay(tmp_path, monkeypatch, emit_primary):
    from datetime import datetime, timezone
    import json
    from netembed.bundle import write_json
    from netembed.paired_study import LIVE_POLICY_SHA
    import netembed.live_policy as module

    cfg = config()
    cfg["fixture"] = True
    plan = Path("configs/ipv6-live-policy-v1.json")

    class Fake:
        identity = cfg["source_artifact_id"]
        meta = {"policy": cfg["expected_policy"]}

        def predict(self, raw):
            label = "youtube" if raw[0, 2] == 1200 else "instagram"
            return {
                "artifact_id": self.identity,
                "status": "classified" if len(raw) >= 10 else "insufficient_evidence",
                "label": label if len(raw) >= 10 else None,
                "alternatives": [{"label": label, "score": 0.9}],
            }

    fake = Fake()
    monkeypatch.setattr(module, "load_model", lambda cfg: fake)
    start = datetime(2026, 11, 7, tzinfo=timezone.utc).timestamp() * 1000
    from netembed.contract import Flow

    for i, spec in enumerate(cfg["trials"]):
        first, session = start + i * 10000, f"fixture-{i}"
        packets = [
            {
                "iat_ms": 0 if j == 0 else 1,
                "direction": 1 if j % 2 == 0 else -1,
                "payload_bytes": 1200 if i == 0 else 200,
            }
            for j in range(30)
        ]
        raw = Flow(packets=packets).array()
        emitted = [
            {"observed_packets": b, **fake.predict(raw[:b])} for b in ([10, 30] if emit_primary else [30])
        ]
        ident = f"browser:{session}:flow"
        values = {
            "rows": [{"id": ident, "label": spec["target"], "packets": packets}],
            "families": [{"id": ident, "label": spec["target"], "family": 6, "packets": 30}],
            "capture": {
                "fixture": False,
                "source": "user_started_capture",
                "artifact_id": fake.identity,
                "session_id": session,
                "evidence_evicted": 0,
                "flows": [{"flow_id": "flow", "packets": packets, "predictions": emitted}],
            },
            "timing": {
                "session_id": session,
                "running": False,
                "drops": 0,
                "coalesced": 0,
                "timing_samples": [
                    {
                        "capture_to_parser_ms": 1.0,
                        "queue_ms": 1.0,
                        "pipeline_ms": 1.0,
                        "capture_to_event_ms": 3.0,
                    }
                ],
                "capture_to_browser_receipt_ms": [4.0],
                "receipt_tracking_evicted": {},
                "receipt_tracking_pending": {},
            },
            "audit": {
                "session_id": session,
                "artifact_id": fake.identity,
                "original_live_prediction_comparison": {
                    "predictions": len(emitted),
                    "changed_decision_labels": 0,
                    "maximum_alternative_score_difference": 0,
                },
            },
            "intent": {
                "collection_role": "live_policy_evaluation",
                "collection_plan_sha256": sha256(plan),
                "chrome_closed_before_intent": True,
                "recorded_before_capture_utc": datetime.fromtimestamp(
                    (first - 500) / 1000, timezone.utc
                ).isoformat(),
            },
            "browser-processes": {
                "session_id": session,
                "plan_sha256": sha256(plan),
                "processes": [{"pid": i + 1, "started_unix_ms": first - 100}],
            },
        }
        for name, value in values.items():
            write_json(tmp_path / (spec["id"] + "-" + name + ".json"), value)
        write_json(
            tmp_path / (spec["id"] + "-archive.json"),
            {
                "trial_id": spec["id"],
                "status": "usable",
                "collection_role": "live_policy_evaluation",
                "session_id": session,
                "first_packet_ms": first,
                "last_packet_ms": first + 1000,
                "plan_sha256": LIVE_POLICY_SHA,
                "counts": {spec["target"]: 1},
                "reference_inventory": {},
                "files": {
                    spec["id"] + "-" + name + ".json": sha256(tmp_path / (spec["id"] + "-" + name + ".json"))
                    for name in values
                },
            },
        )
    output = score_live(tmp_path, cfg, plan)
    report = json.loads(output.read_text())
    assert report["fixture"] is True and report["operational_screen_pass"] is True
    assert report["metrics"]["policy_screen_pass"] is emit_primary
    assert report["metrics"]["budgets"]["10"]["replay_correct_secondary"] == 2
    before = sha256(output)
    with pytest.raises(ValueError, match="preserve"):
        score_live(tmp_path, cfg, plan)
    assert sha256(output) == before
