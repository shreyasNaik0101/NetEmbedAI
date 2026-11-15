"""Fixture parity validates timing boundaries, never trained performance."""

import numpy as np
import pytest

from netembed.benchmark_stages import benchmark_stages, convert_probabilities, forward_tcn, prepare_tcn
from netembed.bundle import Predictor


@pytest.mark.parametrize("length", [1, 5, 10, 20, 30])
def test_prepared_stage_path_matches_shared_predictor_at_every_budget(bundle, raw, length):
    predictor = Predictor(bundle, allow_fixture=True)
    flow = np.tile(raw, (6, 1))[:length]
    prepared = prepare_tcn(predictor, flow)
    actual = convert_probabilities(predictor, forward_tcn(predictor, prepared))
    np.testing.assert_allclose(actual, predictor.probabilities([flow]), atol=1e-7, rtol=0)
    assert not predictor.model.training


def test_stage_report_rejects_fixture_model_instead_of_publishing_fake_performance(bundle, raw):
    with pytest.raises(ValueError, match="real trained artifact"):
        benchmark_stages(Predictor(bundle, allow_fixture=True), raw)
