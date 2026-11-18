import json
from types import SimpleNamespace

import numpy as np
import pytest

from netembed.bundle import sha256, write_json
from netembed.contract import BUDGETS
from netembed.linear_probe import DIMENSIONS, LinearProbe, WHEEL
from netembed.prefix_probe import PrefixProbe, checkpoint
from netembed.prefix_probe_study import gates, read_config, summarize, validate_recovery


def flow(n):
    raw = np.tile([1, 1, 1200], (n, 1)).astype(np.float32)
    raw[0, 0] = 0
    return raw


def model():
    calls = []

    def encode(raw):
        calls.append([len(x) for x in raw])
        return np.zeros((len(raw), DIMENSIONS))

    base = LinearProbe(
        SimpleNamespace(encode=encode),
        list("abcd"),
        np.ones(DIMENSIONS),
        np.full(DIMENSIONS, 2),
        np.zeros((4, DIMENSIONS)),
        np.zeros(4),
    )
    heads = {
        b: {"coefficients": np.zeros((4, DIMENSIONS)), "intercept": np.eye(4)[i] * 5}
        for i, b in enumerate(BUDGETS)
    }
    return PrefixProbe(base, heads), calls


def test_mixed_lengths_route_heads_without_reordering_or_future_packets():
    predictor, calls = model()
    values = predictor.probabilities([flow(n) for n in (5, 30, 10, 20, 7)])
    assert values.argmax(1).tolist() == [0, 3, 1, 2, 1]
    assert calls == [[5, 30, 10, 20, 7]]
    assert all(np.array_equal(head.mean, predictor.base.mean) for head in predictor.heads.values())
    assert all(np.array_equal(head.scale, predictor.base.scale) for head in predictor.heads.values())


def test_short_flow_requested_cap_is_explicit_and_always_withheld():
    predictor, calls = model()
    assert predictor.predict(flow(7))["head_budget"] == 10
    reply = predictor.predict(flow(7), 20)
    assert reply["head_budget"] == 20 and reply["raw_top1"] == "c"
    assert reply["label"] is None and reply["status"] == "uncalibrated"
    assert predictor.predict(flow(2), 30)["status"] == "insufficient_evidence"
    assert calls == [[7], [7], [2]]
    with pytest.raises(ValueError, match="future"):
        predictor.probabilities([flow(10)], 5)
    with pytest.raises(ValueError, match="empty"):
        predictor.probabilities([])


@pytest.mark.parametrize("length,budget", [(0, None), (31, None), (6, 5), (5, 15)])
def test_invalid_checkpoint_contract(length, budget):
    with pytest.raises(ValueError):
        checkpoint(length, budget)


def test_missing_head_cannot_fall_back_to_shared_model():
    predictor, _ = model()
    with pytest.raises(ValueError, match="four"):
        PrefixProbe(predictor.base, {})


def test_artifact_checksums_and_schema(tmp_path, monkeypatch):
    predictor, _ = model()

    def fake_save(destination, wheel):
        destination.mkdir()
        for name in ("metadata.json", "head.json", "checksums.json", "encoder.pth", WHEEL):
            (destination / name).write_bytes(b"test-only")

    monkeypatch.setattr(predictor.base, "save", fake_save)
    monkeypatch.setattr(LinearProbe, "load", lambda path: predictor.base)
    bundle = tmp_path / "bundle"
    predictor.save(bundle, None)
    loaded = PrefixProbe.load(bundle)
    for b in BUDGETS:
        assert loaded.predict(flow(b)) == predictor.predict(flow(b))
    meta = json.loads((bundle / "metadata.json").read_text())
    meta["routing"] = "use shared head"
    write_json(bundle / "metadata.json", meta)
    with pytest.raises(ValueError, match="checksum"):
        PrefixProbe.load(bundle)
    checks = json.loads((bundle / "checksums.json").read_text())
    checks["metadata.json"] = sha256(bundle / "metadata.json")
    write_json(bundle / "checksums.json", checks)
    with pytest.raises(ValueError, match="unsupported"):
        PrefixProbe.load(bundle)


def test_declaration_and_parent_are_frozen(tmp_path):
    declaration, cfg = read_config("configs/prefix-linear-probe-v1.json")
    assert cfg["head"]["C"] == 1 and cfg["local_fraction"] == 0.25
    declaration["early_f1_gain_minimum"] = 0
    path = tmp_path / "changed.json"
    write_json(path, declaration)
    with pytest.raises(ValueError, match="frozen"):
        read_config(path)


def test_recovery_changes_only_iteration_cap_and_requires_unscored_attempt(tmp_path):
    original, old = read_config("configs/prefix-linear-probe-v1.json")
    declaration, cfg = read_config("configs/prefix-linear-probe-solver-recovery-v1.json")
    assert cfg == {**old, "head": {**old["head"], "max_iter": 2000}}
    failed = tmp_path / "failed"
    failed.mkdir()
    write_json(failed / "fit.json", {"5": {"converged": False, "iterations": [500]}})
    write_json(failed / "protocol.json", {"declaration": original, "inherited_config": old})
    write_json(tmp_path / "original.json", original)

    def binding(path):
        return {"path": str(path), "sha256": sha256(path)}

    declaration["numerical_recovery"].update(
        {
            "failed_directory": str(failed),
            "failed_fit": binding(failed / "fit.json"),
            "failed_protocol": binding(failed / "protocol.json"),
            "original_declaration": binding(tmp_path / "original.json"),
        }
    )
    validate_recovery(declaration, cfg)
    write_json(failed / "report.json", {"already_scored": True})
    with pytest.raises(ValueError, match="unscored"):
        validate_recovery(declaration, cfg)


def test_class_regression_still_blocks_a_large_aggregate_gain():
    declaration, cfg = read_config("configs/prefix-linear-probe-v1.json")
    shared = {
        "local_macro_f1": 0.80,
        "local_recall": {"a": 0.9, "b": 0.7},
        "budgets": {"5": {"observed_class_macro_f1": 0.6}},
    }
    candidate = {
        "local_macro_f1": 0.95,
        "local_recall": {"a": 0.85, "b": 1.0},
        "public_clean_macro_f1": 0.95,
        "budgets": {"5": {"observed_class_macro_f1": 0.9}},
    }
    reference = {"local_macro_f1": 0.78, "local_recall": {"a": 0.9, "b": 0.7}, "public_clean_macro_f1": 0.90}
    checks = gates(
        candidate,
        {k: reference for k in ("b17", "previous_forest", "recent_forest")},
        shared,
        cfg,
        declaration,
    )
    assert checks["five_packet_gain"] and checks["shared_f1_nonregression"]
    assert not checks["per_service_nonregression"] and not checks["shared_recall_nonregression"]


def test_metrics_use_available_prefixes_and_keep_public_short_flows():
    local, control = [], []
    for b in BUDGETS:
        local.extend(
            [
                {"observed_packets": b, "reference": "a", "top1": "a"},
                {"observed_packets": b, "reference": "b", "top1": "b" if b > 5 else "a"},
            ]
        )
        control.extend(
            [{"requested_cap": b, "observed_packets": 2, "reference": c, "top1": c} for c in "abc"]
        )
    metrics = summarize(local, control, list("abc"))
    assert metrics["local_recall"] == {"a": 1.0, "b": 0.75}
    assert metrics["public_clean_macro_f1"] == 1.0
    assert metrics["local_macro_f1"] == pytest.approx((1 / 3 + 3) / 4)
