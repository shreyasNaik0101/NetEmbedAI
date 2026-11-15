import json

from fastapi.testclient import TestClient
import numpy as np
import pytest
from sklearn.ensemble import RandomForestClassifier

from netembed.api import create_app
from netembed.bundle import Predictor, export_bundle, forest_prefix, sha256, write_json
from netembed.contract import Flow, Normalizer, summary
from netembed.ten_packet import exact_ten_cohort, guard, read_config, restrict_to_ten
from netembed.ipv6_pilot import read_config as read_recipe


@pytest.fixture
def ten(tmp_path, raw):
    x = np.tile(raw, (6, 1))
    x[0, 0] = 0
    other = x.copy()
    other[:, 2] += 200
    norm = Normalizer.fit([x, other])
    forest = RandomForestClassifier(n_estimators=3, random_state=17).fit(
        [summary(a[:b]) for a in [x, other] for b in [5, 10, 20, 30]],
        [0] * 4 + [1] * 4,
    )
    source = export_bundle(tmp_path / "source", forest, norm, ["a", "b"], {"fixture": True})
    model = restrict_to_ten(source, tmp_path / "ten", {"test": True}, allow_fixture=True)
    return source, tmp_path / "ten", model, x


def test_first_ten_invariant_to_valid_future(ten, monkeypatch):
    source, _, model, raw = ten
    expected = Predictor(source, allow_fixture=True).probabilities([raw[:10]])
    changed = raw.copy()
    changed[10:, 0] = 9000
    changed[10:, 1] *= -1
    changed[10:, 2] = 65500
    monkeypatch.setattr(Normalizer, "fit", lambda _: pytest.fail("inference fit"))
    for x in [raw[:10], raw[:20], raw, changed]:
        np.testing.assert_array_equal(model.probabilities([x]), expected)
        prediction = model.predict(x)
        assert prediction["model_packets"] == 10
        assert prediction["observed_packets"] == len(x)
        assert prediction["model_observation_ms"] == float(raw[:10, 0].sum())
        assert prediction["label"] is None
    np.testing.assert_array_equal(model.probabilities([raw, changed]), np.repeat(expected, 2, axis=0))


def test_short_inputs_never_scored(ten, monkeypatch):
    _, _, model, raw = ten
    with pytest.raises(ValueError, match="at least 10"):
        model.probabilities([raw[:9]])
    monkeypatch.setattr(model, "probabilities", lambda _: pytest.fail("short flow scored"))
    result = model.predict(raw[:9])
    assert result["status"] == "insufficient_evidence"
    assert result["alternatives"] == []
    assert result["model_packets"] == 0
    assert result["model_observation_ms"] is None


def test_artifact_preserves_weights_and_fixture(ten):
    source, path, model, _ = ten
    assert sha256(source / "forest.json") == sha256(path / "forest.json")
    assert model.meta["provenance"]["fixture"] is True
    assert model.identity != Predictor(source, allow_fixture=True).identity
    with pytest.raises(ValueError, match="software-test"):
        Predictor(path)
    assert not model.meta["policy"]["fitted"]


def test_fitted_acceptance_scope_withholds_other_top_guess_without_renormalizing(ten, monkeypatch):
    _, _, model, raw = ten
    model.meta["policy"].update(fitted=True, threshold=0.5, accepted_labels=["a"])
    monkeypatch.setattr(model, "probabilities", lambda _: np.asarray([[0.1, 0.9]]))
    result = model.predict(raw[:10])
    assert result["label"] is None and result["decision_reason"] == "outside_policy_scope"
    assert result["alternatives"][0] == {"label": "b", "score": 0.9}
    monkeypatch.setattr(model, "probabilities", lambda _: np.asarray([[0.9, 0.1]]))
    assert model.predict(raw[:10])["label"] == "a"


@pytest.mark.parametrize("scope", [[], ["unknown"], ["a", "a"], "a", [None]])
def test_invalid_acceptance_scope_rejected_at_bundle_load(ten, scope):
    _, path, model, _ = ten
    meta = model.meta
    meta["policy"]["accepted_labels"] = scope
    write_json(path / "metadata.json", meta)
    write_json(path / "checksums.json", {"metadata.json": sha256(path / "metadata.json"), **meta["files"]})
    with pytest.raises(ValueError, match="accepted-label"):
        Predictor(path, allow_fixture=True)


@pytest.mark.parametrize("prefix", [True, 5, 20, 30, 10.0, "10", None])
def test_bad_architecture_rejected(prefix):
    with pytest.raises(ValueError, match="exactly 10"):
        forest_prefix({"fixed_prefix_packets": prefix})


def test_inconsistent_policy_rejected_at_load(ten):
    _, path, _, _ = ten
    meta = json.loads((path / "metadata.json").read_text())
    meta["policy"]["min_packets"] = 5
    write_json(path / "metadata.json", meta)
    write_json(path / "checksums.json", {"metadata.json": sha256(path / "metadata.json"), **meta["files"]})
    with pytest.raises(ValueError, match="policy must require"):
        Predictor(path, allow_fixture=True)


def test_api_reports_observed_and_used_without_capture(ten):
    _, path, _, raw = ten
    with TestClient(create_app(path, allow_fixture=True)) as client:
        assert client.get("/model").json()["architecture"]["fixed_prefix_packets"] == 10
        short = client.post("/predict", json=Flow.from_array(raw[:5]).model_dump()).json()
        assert short["alternatives"] == []
        results = client.post(
            "/predict-batch", json=[Flow.from_array(x).model_dump() for x in [raw[:10], raw]]
        ).json()
        assert [p["observed_packets"] for p in results] == [10, 30]
        assert [p["model_packets"] for p in results] == [10, 10]
        assert results[0]["alternatives"] == results[1]["alternatives"]
        assert not client.get("/capture/status").json()["running"]


def test_exact_support_excludes_short_without_replacement(raw):
    flows = [raw, np.tile(raw, (2, 1)), np.tile(raw, (6, 1))]
    (kept, y, ids), excluded = exact_ten_cohort(flows, [0, 1, 0], ["short", "ten", "thirty"])
    assert ids == ["ten", "thirty"] and y.tolist() == [1, 0]
    assert [len(x) for x in kept] == [10, 10]
    assert excluded == [{"id": "short", "packets": 5, "reason": "fewer_than_ten_packets"}]


@pytest.mark.parametrize(
    "path",
    [
        "data/processed/train.jsonl",
        "data/processed/calibration.jsonl",
        "data/processed/test.jsonl",
        "artifacts/local/spotify-data-repair-v1/spotify-train-01-rows.json",
        "artifacts/local/spotify-data-repair-v1/spotify-cal-01-rows.json",
        "experiments/ipv6-frozen-evaluation-v1/comparison.json",
    ],
)
def test_study_never_reads_training_calibration_final(path):
    cfg = read_config("configs/spotify-ten-packet-v1.json")
    recipe = read_recipe(cfg["recipe"])
    with pytest.raises(ValueError):
        guard("open", (path,), cfg, recipe)
