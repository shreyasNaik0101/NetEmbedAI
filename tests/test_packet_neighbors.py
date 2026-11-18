import numpy as np
import pytest

from netembed.packet_neighbors import PacketNeighbors, encode
from netembed.packet_study import protected_input, summarize


def sequence(sizes):
    return np.array(
        [[0 if i == 0 else 1, 1 if i % 2 == 0 else -1, size] for i, size in enumerate(sizes)],
        dtype=np.float32,
    )


def test_order_distinguishes_identical_size_summaries():
    a, b = sequence([100, 200, 300, 400, 500]), sequence([500, 400, 300, 200, 100])
    model = PacketNeighbors([a, b], [0, 1], ["a", "b"], ["one", "two"])
    assert model.predict(a)["label"] == "one"
    assert model.predict(b)["label"] == "two"


def test_reference_future_cannot_affect_five_packet_distance():
    a = sequence([100] * 30)
    changed = a.copy()
    changed[5:, 2] = 65000
    left = PacketNeighbors([a], [0], ["a"], ["one"])
    right = PacketNeighbors([changed], [0], ["a"], ["one"])
    assert left.predict(a[:5]) == right.predict(a[:5])


def test_short_input_is_not_repeated_into_future_positions():
    x = sequence([100, 200])
    result = encode(x, 5).reshape(5, 3)
    assert np.all(result[2:] == 0)
    assert result[1, 0] == pytest.approx(0.1)
    x[1, 0] = 90000
    assert encode(x, 5)[3] == 100


def test_after_eight_cannot_invent_a_five_packet_answer():
    model = PacketNeighbors(
        [sequence([100] * 5), sequence([100] * 10)], [0, 1], ["short", "long"], ["one", "two"]
    )
    assert model.predict(sequence([100] * 5), "after_eight")["label"] is None
    assert model.predict(sequence([100] * 10), "after_eight")["label"] == "two"


def test_serialization_is_standalone_and_detects_corruption(tmp_path):
    a = sequence([100] * 10)
    model = PacketNeighbors([a], [0], ["a"], ["one"], {"fixture": True})
    model.save(tmp_path / "saved")
    with pytest.raises(ValueError, match="fixture"):
        PacketNeighbors.load(tmp_path / "saved")
    loaded = PacketNeighbors.load(tmp_path / "saved", allow_fixture=True)
    for n in (5, 9, 10):
        assert model.predict(a[:n]) == loaded.predict(a[:n])
    (tmp_path / "saved/references.npz").write_bytes(b"damaged")
    with pytest.raises(ValueError, match="checksum"):
        PacketNeighbors.load(tmp_path / "saved", allow_fixture=True)


def test_tie_is_reference_order_and_ids_must_be_unique():
    a = sequence([100] * 5)
    model = PacketNeighbors([a, a], [1, 0], ["first", "second"], ["one", "two"])
    assert model.predict(a)["label"] == "two"
    assert model.predict(a)["alternatives"][0]["label"] == "two"
    with pytest.raises(ValueError, match="duplicate"):
        PacketNeighbors([a, a], [0, 1], ["same", "same"], ["one", "two"])


def test_partial_ablation_does_not_get_a_comparable_mean():
    records = [{"requested_cap": 5, "reference": "one", "prediction": {"label": None}}]
    result = summarize(records, ["one", "two"])
    assert result["mean_budget_macro_f1"] is None
    assert result["ranked"] == 0 and result["available"] == 1


@pytest.mark.parametrize(
    "path",
    [
        "/x/youtube-cal-02-netlog.json",
        "/x/instagram-dev-03-capture.json",
        "/x/youtube-eval-01.json",
        "/data/test.jsonl",
        "/run/final/report.json",
    ],
)
def test_protected_inputs_remain_out_of_diagnostic(path):
    assert protected_input(path)
