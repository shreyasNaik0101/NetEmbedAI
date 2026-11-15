import numpy as np
import pytest

from netembed.pretrained_neighbors import FrozenEncoder, FrozenNeighbors, packet_batch


def test_upstream_layout_keeps_channels_and_padding_separate(raw):
    result = packet_batch([raw, raw[:2]])
    assert result.shape == (2, 3, 30)
    np.testing.assert_array_equal(result[0, :, :5], raw.T)
    np.testing.assert_array_equal(result[1, :, 2:], 0)
    np.testing.assert_array_equal(result[0, 1, :5], raw[:, 1])


def test_no_random_weight_or_network_fallback(tmp_path):
    with pytest.raises(ValueError, match="missing or changed"):
        FrozenEncoder(tmp_path / "absent.pth", "0" * 64)
    path = tmp_path / "bad.pth"
    path.write_bytes(b"damaged")
    with pytest.raises(ValueError, match="missing or changed"):
        FrozenEncoder(path, "0" * 64)


def test_cosine_retrieval_and_ties_are_not_probabilities(raw):
    a, b = np.eye(256, dtype=np.float32)[:2]

    class Encoder:
        def encode(self, flows):
            assert len(flows) == 1 and len(flows[0]) == len(raw)
            return a[None]

    model = FrozenNeighbors(
        Encoder(),
        {n: np.stack([a, a, b]) for n in (5, 10, 20, 30)},
        [1, 0, 0],
        ["first", "second", "third"],
        ["a", "b"],
    )
    reply = model.predict(raw)
    assert reply["label"] == reply["alternatives"][0]["label"] == "b"
    assert reply["status"] == "raw_ranking_uncalibrated"
    assert "score" not in reply["alternatives"][0]
    assert reply["reference_id"] == "first"


def test_bad_or_nonunit_reference_embeddings_are_rejected():
    with pytest.raises(ValueError, match="normalized"):
        FrozenNeighbors(None, {n: np.zeros((1, 256)) for n in (5, 10, 20, 30)}, [0], ["one"], ["a"])
