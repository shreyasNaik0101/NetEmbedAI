import numpy as np
import pytest
import torch
from netembed.bundle import export_bundle
from netembed.contract import Normalizer
from netembed.models import Classifier


@pytest.fixture
def raw():
    return np.asarray([[0, 1, 1200], [2, -1, 900], [3, 1, 100], [5, -1, 1000], [1, 1, 80]], dtype=np.float32)


@pytest.fixture
def bundle(tmp_path, raw):
    torch.set_num_threads(1)
    torch.manual_seed(17)
    model = Classifier(2, hidden=8, levels=2, embedding_dim=4).eval()
    return export_bundle(
        tmp_path / "fixture",
        model,
        Normalizer.fit([raw]),
        ["fixture-a", "fixture-b"],
        {"fixture": True, "license": "software-test only"},
        {"hidden": 8, "levels": 2, "embedding_dim": 4},
    )
