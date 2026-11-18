"""Software-only guards/metrics, not model-quality evidence."""

import numpy as np
import pytest

from scripts.compare_packet_rules import protected_input, rule_stats, scores


@pytest.mark.parametrize(
    "path",
    [
        r"C:\private\youtube-cal-02-netlog.json",
        "/private/instagram-cal-03-capture.json",
        "/private/youtube-cal-10-reference.json",
        "/private/instagram-dev-03-intent.json",
        "/private/youtube-eval-01-reference.json",
        "/data/test.jsonl",
        "/run/final/report.json",
    ],
)
def test_latest_or_future_trials_and_final_inputs_are_protected(path):
    assert protected_input(path)


def test_retired_selection_and_original_training_are_the_only_allowed_browser_inputs():
    assert not protected_input("/private/instagram-cal-01-calibration-rows.jsonl")
    assert not protected_input("/private/youtube-dev-02-development-rows.jsonl")
    assert not protected_input("/data/train.jsonl")


def test_no_rule_match_is_not_counted_as_correct_and_class_errors_cannot_hide():
    truth = np.array([0, 0, 0, 1, 1])
    values = ["a", "a", None, "a", None]
    report = rule_stats(truth, values, ["a", "b"])
    assert report["overall"]["matched"] == 3 and report["overall"]["errors"] == 1
    assert report["by_reference_class"]["b"]["error_among_matches"] == 1
    no_match = rule_stats(truth, [None] * len(truth), ["a", "b"])
    assert no_match["overall"]["coverage"] == 0
    assert no_match["overall"]["error_among_matches"] is None


def test_raw_local_metrics_keep_predictions_outside_the_observed_classes():
    result = scores([0, 0, 2, 2], [0, 1, 2, 1], [0, 2], 3)
    assert result["n"] == 4 and result["correct"] == 2
    assert result["macro_f1"] == pytest.approx(2 / 3)
    assert np.asarray(result["confusion"]).sum() == 4
