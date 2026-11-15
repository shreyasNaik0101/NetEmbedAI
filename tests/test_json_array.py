import json

import pytest

from netembed.json_array import iter_json_array


@pytest.mark.parametrize("chunk", [1, 7, 64, 1024])
def test_array_reader_preserves_items_across_chunk_boundaries(tmp_path, chunk):
    values = [{"value": [[1.25, 0.75]], "left": [-1], "name": 'escaped \\" value'}, {"nodes": [0] * 100}]
    path = tmp_path / "trees.json"
    path.write_text(json.dumps(values, indent=2))
    assert list(iter_json_array(path, chunk_chars=chunk)) == values


@pytest.mark.parametrize("text", ["", "{}", "[{}", "[{},]", "[{} {}]", "[{}] garbage"])
def test_bad_model_array_cannot_supply_partial_success(tmp_path, text):
    path = tmp_path / "trees.json"
    path.write_text(text)
    with pytest.raises(ValueError):
        list(iter_json_array(path, chunk_chars=1))


def test_chunk_ending_halfway_through_number_cannot_change_its_value(tmp_path):
    path = tmp_path / "trees.json"
    path.write_text("[1e3,-2.5e-2,3]")
    assert list(iter_json_array(path, chunk_chars=1)) == [1000, -0.025, 3]


def test_item_memory_bound_and_empty_array(tmp_path):
    path = tmp_path / "trees.json"
    path.write_text('[{"nodes":[' + ",".join(["0"] * 100) + "]}]")
    with pytest.raises(ValueError, match="bounded"):
        list(iter_json_array(path, max_item_chars=30, chunk_chars=7))
    path.write_text(" [ ] \n")
    assert list(iter_json_array(path, chunk_chars=1)) == []
