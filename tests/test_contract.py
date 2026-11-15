import numpy as np
import pytest
from pydantic import ValidationError
from netembed.contract import Flow, Normalizer, validate_array, summary
from netembed.transforms import perturb


@pytest.mark.parametrize("change", ["empty", "first", "direction", "nan", "size", "fraction", "too_long"])
def test_invalid(raw, change):
    x = raw.copy()
    if change == "empty":
        x = x[:0]
    if change == "first":
        x[0, 0] = 1
    if change == "direction":
        x[0, 1] = 0
    if change == "nan":
        x[1, 0] = float("nan")
    if change == "size":
        x[0, 2] = 0
    if change == "fraction":
        x[0, 2] = 1.5
    if change == "too_long":
        x = np.tile(x, (7, 1))
    with pytest.raises(ValueError):
        validate_array(x)


def test_boundary_and_auxiliary(raw):
    f = Flow.from_array(raw)
    with pytest.raises(ValidationError):
        Flow(**f.model_dump(), label="youtube")
    assert np.array_equal(f.array(), raw)


def test_training_stats_and_padding(raw):
    norm = Normalizer.fit([raw[:1]])
    assert np.isfinite(norm.std).all()
    x, length = norm.batch([raw[:1]])
    assert length.tolist() == [1]
    assert (x[0, 1:] == 0).all()
    saved = norm.metadata()
    norm.batch([raw * [1, 1, 2]])
    assert saved == norm.metadata()


@pytest.mark.parametrize("kind", ["timing", "padding", "observation_loss"])
def test_zero_and_paired(raw, kind):
    x, _ = perturb(raw, kind, 0, 42, "a")
    np.testing.assert_array_equal(x, raw)
    strength = 0.3 if kind == "observation_loss" else 20
    a, _ = perturb(raw, kind, strength, 42, "a")
    perturb(raw, kind, strength, 42, "unrelated")
    b, _ = perturb(raw, kind, strength, 42, "a")
    np.testing.assert_array_equal(a, b)
    assert a[0, 0] == 0 and (a[:, 0] >= 0).all()


def test_loss_reconstructs_timestamps(raw):
    x, info = perturb(raw, "observation_loss", 0.5, 17, "test")
    times = np.cumsum(raw[:, 0])
    for t, size in zip(np.cumsum(x[:, 0]), x[:, 2]):
        assert t == times[np.flatnonzero(raw[:, 2] == size)[0]]
    assert len(x) + info["removed"] == len(raw)


def test_padding_never_shrinks(raw):
    raw[0, 2] = 65527
    x, _ = perturb(raw, "padding", 1000)
    assert (x[:, 2] >= raw[:, 2]).all()
    assert x[0, 2] == 65527


def test_classical_summary_prefix_only(raw):
    before = summary(raw[:3])
    raw[3:, 2] = 65527
    assert before == summary(raw[:3])
