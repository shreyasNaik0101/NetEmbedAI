"""Constructed software fixtures only; no benchmark or live quality evidence."""

import numpy as np
import pytest
from sklearn.ensemble import RandomForestClassifier

from netembed.bundle import Predictor, export_bundle
from netembed.contract import Normalizer, forest_features, summary


def examples():
    a = np.array([[0, 1, 1250], [1, -1, 100], [3, 1, 200], [2, -1, 150]], dtype=np.float32)
    return a, a[[0, 2, 1, 3]]


def test_ordered_map_distinguishes_equal_summaries_and_masks_padding():
    a, b = examples()
    norm = Normalizer.fit([a])
    old = forest_features(a, norm)
    np.testing.assert_array_equal(old, summary(b))
    ordered = forest_features(a, norm, "summary-ordered-v1")
    assert len(ordered) == 154 and not np.array_equal(ordered, forest_features(b, norm, "summary-ordered-v1"))
    np.testing.assert_array_equal(ordered[:34], old)
    np.testing.assert_array_equal(ordered[34:124].reshape(30, 3)[4:], 0)
    np.testing.assert_array_equal(ordered[-30:], [1] * 4 + [0] * 26)


def test_ordered_bundle_roundtrip_uses_saved_preprocessing(tmp_path, monkeypatch):
    a, b = examples()
    norm = Normalizer.fit([a])
    flows = [a, b, a[:2], b[:2]]
    features = [forest_features(x, norm, "summary-ordered-v1") for x in flows]
    forest = RandomForestClassifier(n_estimators=5, random_state=17).fit(features, [0, 1, 0, 1])
    path = export_bundle(
        tmp_path / "ordered",
        forest,
        norm,
        ["a", "b"],
        {"fixture": True},
        {"feature_map": "summary-ordered-v1"},
    )
    monkeypatch.setattr(Normalizer, "fit", lambda _: pytest.fail("inference fitted preprocessing"))
    loaded = Predictor(path, allow_fixture=True)
    np.testing.assert_allclose(loaded.probabilities(flows), forest.predict_proba(features), atol=1e-12)
    with pytest.raises(ValueError, match="differ from exported"):
        export_bundle(tmp_path / "wrong-map", forest, norm, ["a", "b"], {"fixture": True})
    assert not (tmp_path / "wrong-map").exists()


def test_unknown_feature_map_refused_before_export(tmp_path):
    a, b = examples()
    norm = Normalizer.fit([a])
    forest = RandomForestClassifier(n_estimators=2, random_state=17).fit([summary(a), summary(b)], [0, 1])
    with pytest.raises(ValueError, match="unknown forest feature map"):
        export_bundle(
            tmp_path / "unknown", forest, norm, ["a", "b"], {"fixture": True}, {"feature_map": "guess"}
        )
    assert not (tmp_path / "unknown").exists()
