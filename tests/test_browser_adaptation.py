import copy

import numpy as np
import pytest
import torch

from netembed.browser_adaptation import (
    UNCOMMITTED,
    check_roles,
    forest_weights,
    passes_guard,
    train_epoch,
    load_role_trial,
)
from netembed.bundle import Predictor, export_bundle


def test_whole_session_isolation_even_with_distinct_flow_ids():
    with pytest.raises(ValueError, match="crosses train"):
        check_roles([{"id": "a", "group_id": "same-session"}], [{"id": "b", "group_id": "same-session"}])
    check_roles([{"id": "a", "group_id": "one"}], [{"id": "b", "group_id": "two"}])


def test_domain_weights_preserve_mass_and_balance_local_classes():
    targets = np.array([0, 0, 0, 2])
    weights = forest_weights(100, targets, 0.25)
    assert weights[:100].sum() == pytest.approx(0.75)
    assert weights[100:][targets == 0].sum() == pytest.approx(0.125)
    assert weights[100:][targets == 2].sum() == pytest.approx(0.125)
    assert weights.sum() == pytest.approx(1)


def test_forward_quality_floor_cannot_be_hidden_by_easy_class():
    base = {
        "local_macro_f1": 0.2,
        "public_clean_macro_f1": 0.8,
        "local_recall": {"youtube": 0.7, "instagram": 0.1},
    }
    cfg = {
        "local_macro_f1_gain_minimum": 0.1,
        "public_clean_loss_limit": 0.02,
        "local_quality_floor": 0.75,
        "local_class_recall_floor": 0.65,
    }
    candidate = {
        "local_macro_f1": 0.8,
        "public_clean_macro_f1": 0.8,
        "local_recall": {"youtube": 1.0, "instagram": 0.5},
    }
    assert not passes_guard(candidate, base, cfg)
    candidate["local_recall"]["instagram"] = 0.8
    assert passes_guard(candidate, base, cfg)
    candidate["local_macro_f1"] = 0.7
    assert not passes_guard(candidate, base, cfg)


def test_retired_calibration_cannot_silently_enter_training(tmp_path):
    with pytest.raises(ValueError, match="selection-only"):
        load_role_trial(tmp_path, "instagram-cal-01", "train", ["instagram"], {}, {})


@pytest.mark.parametrize("failure", ["forgetting", "local_regression", "no_improvement"])
def test_local_gain_cannot_hide_global_or_class_regression(failure):
    base = {
        "local_macro_f1": 0.4,
        "public_clean_macro_f1": 0.9,
        "local_recall": {"youtube": 0.8, "instagram": 0.0},
    }
    candidate = {
        "local_macro_f1": 0.8,
        "public_clean_macro_f1": 0.89,
        "local_recall": {"youtube": 0.9, "instagram": 0.8},
    }
    cfg = {"local_macro_f1_gain_minimum": 0.1, "public_clean_loss_limit": 0.02}
    assert passes_guard(candidate, base, cfg)
    if failure == "forgetting":
        candidate["public_clean_macro_f1"] = 0.7
    elif failure == "local_regression":
        candidate["local_recall"]["youtube"] = 0.7
    else:
        candidate["local_macro_f1"] = 0.45
    assert not passes_guard(candidate, base, cfg)


def test_warm_start_changes_copy_reuses_statistics_and_stays_uncommitted(bundle, raw, tmp_path, monkeypatch):
    torch.set_num_threads(1)
    base = Predictor(bundle, allow_fixture=True)
    before = base.probabilities([raw]).copy()
    statistics = copy.deepcopy(base.normalizer.metadata())
    model = copy.deepcopy(base.model)
    monkeypatch.setattr(type(base.normalizer), "fit", lambda *a: pytest.fail("must not fit normalization"))
    optimizer = torch.optim.Adam(model.parameters(), lr=0.001)
    cfg = {"batch_size": 4, "local_fraction": 0.5, "steps_per_epoch": 1}
    train_epoch(
        model,
        base.normalizer,
        [raw, raw],
        np.array([0, 1]),
        [raw, raw],
        np.array([0, 1]),
        optimizer,
        np.random.default_rng(17),
        cfg,
    )
    np.testing.assert_array_equal(before, base.probabilities([raw]))
    assert base.normalizer.metadata() == statistics
    assert any(
        not torch.equal(value, base.model.state_dict()[name]) for name, value in model.state_dict().items()
    )
    path = export_bundle(
        tmp_path / "adapted",
        model,
        base.normalizer,
        base.labels,
        {"fixture": True},
        base.meta["architecture"],
        UNCOMMITTED,
    )
    adapted = Predictor(path, allow_fixture=True)
    assert adapted.normalizer.metadata() == statistics
    assert adapted.predict(raw)["label"] is None
    assert adapted.meta["policy"]["fitted"] is False
