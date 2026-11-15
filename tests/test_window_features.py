"""Constructed software fixtures only, not network accuracy observations."""

from copy import deepcopy

import numpy as np
import pytest
from sklearn.ensemble import RandomForestClassifier

from netembed.bundle import Predictor
from netembed.window_features import NAMES, WindowForest, browser_windows, features
from scripts.study_browser_windows import guard


def records(count=5, size=1200):
    return [(1000000 + i * 100, i, 1 if i % 2 == 0 else -1, size) for i in range(count)]


def test_half_open_browser_windows_do_not_read_future_traffic():
    rows = [
        (1000000, 0, 1, 1200),
        (1000999, 1, -1, 800),
        (1001000, 2, 1, 100),
        (1002999, 3, -1, 400),
        (1003000, 4, -1, 65527),
    ]
    windows = browser_windows(rows)
    assert windows[1000]["client_packets"] + windows[1000]["server_packets"] == 2
    assert windows[3000]["client_packets"] + windows[3000]["server_packets"] == 4
    other = rows[:-1] + [(1003000, 4, 1, 1), (2000000, 5, 1, 60000)]
    for horizon in (1000, 3000):
        np.testing.assert_array_equal(features(windows[horizon]), features(browser_windows(other)[horizon]))


def test_directional_bin_mass_padding_and_label_independence():
    window = browser_windows(records())[1000]
    x = features(window)
    assert len(x) == len(NAMES) == 72
    assert x[12:].sum() == pytest.approx(1)
    assert not x[32:].any()  # First-second input does not borrow later bins.
    changed = deepcopy(window)
    changed.update(label="answer", hostname="answer", process_name="answer")
    np.testing.assert_array_equal(features(changed), x)
    changed["state"] = "observing"
    with pytest.raises(ValueError, match="elapsed"):
        features(changed)


def test_window_forest_numeric_export_parity_and_observer_budget_guards(tmp_path):
    windows = [browser_windows(records(3 + i, 100 if i < 8 else 1200))[1000] for i in range(16)]
    x = np.asarray([features(w) for w in windows])
    y = np.array([0] * 8 + [1] * 8)
    forest = RandomForestClassifier(n_estimators=4, max_depth=3, random_state=17).fit(x, y)
    exported = WindowForest.from_fitted(forest, ["fixture-a", "fixture-b"], 1000, {"fixture": True})
    exported.save(tmp_path / "model")
    with pytest.raises(ValueError, match="fixture"):
        WindowForest.load(tmp_path / "model")
    model = WindowForest.load(tmp_path / "model", allow_fixture=True)
    for window, expected in zip(windows, forest.predict_proba(x)):
        reply = model.predict(window, "browser_udp_socket")
        actual = [
            next(a["score"] for a in reply["alternatives"] if a["label"] == label) for label in model.labels
        ]
        np.testing.assert_allclose(actual, expected, atol=1e-12)
        assert reply["label"] is None
    with pytest.raises(ValueError, match="observer mismatch"):
        model.predict(windows[0], "tshark")
    with pytest.raises(ValueError, match="budget"):
        model.predict(browser_windows(records())[3000], "browser_udp_socket")
    with pytest.raises(ValueError, match="inventory"):
        Predictor(tmp_path / "model", allow_fixture=True)


@pytest.mark.parametrize(
    "path",
    [
        "/data/instagram-cal-02-netlog.json",
        "/data/youtube-dev-03-netlog.json",
        "/data/window-validation/window-engineering-01-capture.json",
        "/data/test.jsonl",
        "/run/final/report.json",
    ],
)
def test_window_study_excludes_protected_and_unscored_inputs(path):
    with pytest.raises(ValueError, match="excluded"):
        guard("open", (path,))
