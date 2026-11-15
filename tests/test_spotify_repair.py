"""Constructed software contracts; no capture or model-quality evidence."""

from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
import pytest
from netembed.bundle import sha256, write_json
from netembed.paired_study import read_plan, check_order, support, SPOTIFY_REPAIR_SHA
from netembed.spotify_repair import source_for, stage_receipt, role_rows, status
from netembed.spotify_repair_stages import stage_guard, local_policy_checks, retention_gates
from netembed.ipv6_pilot import read_config as read_recipe


def config():
    return read_plan("configs/spotify-data-repair-v1.json")


def moment(day, hour=10):
    return datetime(2026, 11, day, hour, tzinfo=timezone.utc).timestamp() * 1000


def report(spec, first, session):
    return {
        "trial_id": spec["id"],
        "status": "usable",
        "collection_role": spec["role"],
        "plan_sha256": SPOTIFY_REPAIR_SHA,
        "session_id": session,
        "first_packet_ms": first,
        "last_packet_ms": first + 1000,
        "files": {},
    }


def test_roles_budget_and_declaration_are_fixed(tmp_path):
    cfg = config()
    assert [s["role"] for s in cfg["trials"]] == [
        "train",
        "train",
        "train",
        "selection",
        "calibration",
        "evaluation",
    ]
    assert cfg["collection"]["maximum_visits"] == 6 and cfg["minimum_target_at_10_per_trial"] == 3
    p = tmp_path / "changed.json"
    p.write_bytes(Path("configs/spotify-data-repair-v1.json").read_bytes() + b" ")
    with pytest.raises(ValueError, match="declaration changed"):
        read_plan(p)


def test_later_training_and_evaluation_dates_and_unique_sessions():
    cfg = config()
    specs = cfg["trials"]
    previous = []
    dates = [moment(8, 10), moment(8, 11), moment(9, 10), moment(9, 11), moment(9, 12), moment(10, 10)]
    for i, (spec, t) in enumerate(zip(specs, dates)):
        check_order(cfg, spec["id"], previous, t, str(i))
        previous.append(report(spec, t, str(i)))
    with pytest.raises(ValueError, match="later local"):
        check_order(cfg, specs[2]["id"], previous[:2], moment(8, 12), "new")
    with pytest.raises(ValueError, match="later local"):
        check_order(cfg, specs[5]["id"], previous[:5], moment(9, 13), "new")
    with pytest.raises(ValueError, match="reused"):
        check_order(cfg, specs[5]["id"], previous[:5], moment(10, 10), "0")
    previous[0]["status"] = "unusable_stop"
    with pytest.raises(ValueError, match="scope"):
        check_order(cfg, specs[1]["id"], previous[:1], moment(8, 11), "1")


def test_different_later_dates_are_allowed_without_forcing_same_day_slots():
    cfg = config()
    a = report(cfg["trials"][0], moment(8), "a")
    check_order(cfg, cfg["trials"][1]["id"], [a], moment(9), "b")
    b = report(cfg["trials"][1], moment(9), "b")
    with pytest.raises(ValueError, match="later local"):
        check_order(cfg, cfg["trials"][2]["id"], [a, b], moment(9, 12), "c")
    check_order(cfg, cfg["trials"][2]["id"], [a, b], moment(10), "c")


def test_minimum_support_independent_of_model_predictions():
    cfg = config()
    spec = cfg["trials"][0]
    rows = [{"label": "spotify", "packets": [{}] * n} for n in [10, 10, 30]]
    support(rows, spec, cfg)
    with pytest.raises(ValueError, match="support"):
        support(rows[:2], spec, cfg)
    with pytest.raises(ValueError, match="support"):
        support([{"label": "youtube", "packets": [{}] * 30}] * 3, spec, cfg)


@pytest.mark.parametrize("trial", ["spotify-dev-01", "spotify-cal-01", "spotify-eval-01"])
def test_later_roles_cannot_prepare_without_stage_receipts(tmp_path, trial):
    with pytest.raises(ValueError, match="awaiting"):
        source_for(tmp_path, config(), trial, moment(10))


def test_failed_stage_cannot_be_relabelled_ready(tmp_path):
    write_json(
        tmp_path / "training-stage.json",
        {"plan_sha256": SPOTIFY_REPAIR_SHA, "fixture": False, "stage": "training", "status": "failed_stop"},
    )
    with pytest.raises(ValueError, match="scope stopped"):
        stage_receipt(tmp_path, config(), "training")
    cfg = config()
    previous = []
    for i, spec in enumerate(cfg["trials"][:3]):
        t = moment(8 if i < 2 else 9, 10 + i)
        r = report(spec, t, str(i))
        write_json(tmp_path / (spec["id"] + "-archive.json"), r)
        previous.append(r)
    state = status(tmp_path, cfg, moment(10))
    assert state["next_action"] == "awaiting_stage_or_stopped"


def test_fixture_archive_cannot_enter_training(tmp_path):
    cfg = config()
    for i, spec in enumerate(cfg["trials"][:3]):
        cap = tmp_path / (spec["id"] + "-capture.json")
        write_json(cap, {"fixture": True, "source": "user_started_capture"})
        r = report(spec, moment(8 if i < 2 else 9, 10 + i), str(i))
        r["files"] = {cap.name: sha256(cap)}
        write_json(tmp_path / (spec["id"] + "-archive.json"), r)
    with pytest.raises(ValueError, match="real user"):
        role_rows(tmp_path, cfg, "train")


@pytest.mark.parametrize(
    "command,path",
    [
        ("fit", "data/processed/v2/test.jsonl"),
        ("fit", "data/processed/v2/selection.jsonl"),
        ("fit", "artifacts/local/spotify-data-repair-v1/spotify-dev-01-rows.json"),
        ("fit", "artifacts/local/spotify-diagnostic-v1/spotify-01-capture.json"),
        ("assess", "artifacts/local/spotify-data-repair-v1/spotify-cal-01-rows.json"),
        ("calibrate", "artifacts/local/spotify-data-repair-v1/spotify-eval-01-netlog.json"),
        ("calibrate", "data/processed/v2/selection.jsonl"),
        ("evaluate", "data/processed/v2/train.jsonl"),
        ("fit", "artifacts/local/ipv6-frozen-evaluation-v1/ipv6-eval-yt-01-rows.json"),
    ],
)
def test_stage_guards_reject_leakage(command, path):
    cfg = config()
    recipe = read_recipe(cfg["training_recipe"])
    with pytest.raises(ValueError):
        stage_guard(
            "open", (path, "r", 0), command, Path("artifacts/local/spotify-data-repair-v1"), cfg, recipe
        )


def test_training_only_access_and_offline_guards():
    cfg = config()
    recipe = read_recipe(cfg["training_recipe"])
    root = Path("artifacts/local/spotify-data-repair-v1")
    stage_guard("open", (str(root / "spotify-train-01-rows.json"), "r", 0), "fit", root, cfg, recipe)
    with pytest.raises(ValueError, match="offline"):
        stage_guard("socket.connect", (), "fit", root, cfg, recipe)


def test_calibration_requires_actual_local_correct_accepts():
    cfg = config()
    records = [
        {"id": str(i), "reference": "spotify", "top1": "spotify", "budget": 10, "probabilities": [0.1, 0.9]}
        for i in range(3)
    ]
    assert local_policy_checks(records, 0.8, cfg)
    assert not local_policy_checks(records, 0.95, cfg)
    wrong = deepcopy(records)
    wrong[0]["top1"] = "youtube"
    assert not local_policy_checks(wrong, 0.8, cfg)


def metrics():
    budget = {
        str(b): {
            "n": 3,
            "accuracy": 1,
            "macro_f1": 0.9,
            "classes": {"spotify": {"recall": 1}, "youtube": {"recall": 0.9}, "instagram": {"recall": 0.9}},
        }
        for b in [5, 10, 20, 30]
    }
    return {
        "spotify": {"budgets": deepcopy(budget)},
        "local": {"macro_f1": 0.9, "budgets": deepcopy(budget)},
        "public": {"budgets": deepcopy(budget)},
    }


def test_development_cannot_trade_other_classes_or_late_prefixes_for_gain():
    cfg = config()
    candidate = metrics()
    control = metrics()
    for v in control["spotify"]["budgets"].values():
        v["accuracy"] = 0
        v["classes"]["spotify"]["recall"] = 0
    assert all(retention_gates(candidate, control, cfg).values())
    candidate["spotify"]["budgets"]["30"]["classes"]["spotify"]["recall"] = 0
    assert not retention_gates(candidate, control, cfg)["spotify_each_prefix"]
    candidate = metrics()
    candidate["local"]["budgets"]["10"]["classes"]["instagram"]["recall"] = 0.8
    assert not retention_gates(candidate, control, cfg)["local_each_class_prefix"]


@pytest.mark.parametrize(
    "command,path",
    [
        ("fit", "artifacts/local/spotify-data-repair-v1/calibration-stage.json"),
        ("fit", "experiments/spotify-data-repair-v1/evaluation/report.json"),
        ("calibrate", "experiments/spotify-data-repair-v1/evaluation/predictions.json"),
    ],
)
def test_future_stage_outcomes_are_also_blocked(command, path):
    cfg = config()
    recipe = read_recipe(cfg["training_recipe"])
    with pytest.raises(ValueError):
        stage_guard(
            "open", (path, "r", 0), command, Path("artifacts/local/spotify-data-repair-v1"), cfg, recipe
        )


def test_public_feasibility_cannot_override_wrong_local_calibration():
    from netembed.public_policy import select_policy

    cfg = config()
    labels = ["youtube", "spotify"]
    public = []
    for label in labels:
        for i in range(5):
            public.append(
                {
                    "id": label + str(i),
                    "budget": 10,
                    "reference": label,
                    "top1": label,
                    "probabilities": [0.9, 0.1] if label == "youtube" else [0.1, 0.9],
                }
            )
    rules = {
        "budgets": [10, 20, 30],
        "primary_budget": 10,
        "min_packets": 10,
        "temperature": 1,
        "rules": {
            "maximum_empirical_error": 0.1,
            "minimum_coverage": 0.5,
            "minimum_primary_accepted_per_class": 5,
        },
    }
    _, _, curve = select_policy(public, labels, rules)
    local = [
        {"id": str(i), "reference": "spotify", "budget": 10, "top1": "spotify", "probabilities": [0.2, 0.8]}
        for i in range(2)
    ]
    local.append(
        {"id": "wrong", "reference": "spotify", "budget": 10, "top1": "youtube", "probabilities": [0.7, 0.3]}
    )
    chosen = next(p for p in curve if p["eligible"] and local_policy_checks(local, p["threshold"], cfg))
    assert chosen["threshold"] == 0.71
    local[0].update(top1="youtube", probabilities=[0.95, 0.05])
    assert not any(p["eligible"] and local_policy_checks(local, p["threshold"], cfg) for p in curve)
