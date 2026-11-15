import json
from pathlib import Path
import numpy as np
import pytest
from netembed.bundle import Predictor, sha256, write_json
from netembed.contract import Flow
from netembed.training import augment_one, train


def fixture_data(tmp_path, raw):
    data = tmp_path / "data"
    data.mkdir()
    hashes = {}
    for partition in ["train", "selection", "calibration"]:
        rows = []
        for i in range(8):
            x = raw.copy()
            x[:, 2] += i * 10
            rows.append(
                {
                    "id": f"{partition}-{i}",
                    "label": ["fixture-a", "fixture-b"][i % 2],
                    **Flow.from_array(x).model_dump(),
                }
            )
        path = data / (partition + ".jsonl")
        path.write_text("".join(json.dumps(r) + "\n" for r in rows))
        hashes[path.name] = sha256(path)
    write_json(
        data / "manifest.json",
        {
            "labels": ["fixture-a", "fixture-b"],
            "files": hashes,
            "source": {"fixture": True, "license": "software tests only"},
        },
    )
    return data


def test_tiny_supervised_training_and_resume_are_fixture_only(tmp_path, raw):
    data = fixture_data(tmp_path, raw)
    cfg = {
        "epochs": 1,
        "threads": 1,
        "batch_size": 4,
        "architecture": {"hidden": 4, "levels": 1, "embedding_dim": 4},
    }
    run = Path(train(data, tmp_path / "runs", cfg))
    assert not (data / "test.jsonl").exists()  # trainer succeeds with final test entirely absent
    p = Predictor(run / "bundle", allow_fixture=True)
    assert p.meta["provenance"]["fixture"] is True
    assert len(p.predict(raw)["alternatives"]) == 2
    with pytest.raises(ValueError, match="software-test"):
        Predictor(run / "bundle")
    resumed = Path(train(data, tmp_path / "runs", cfg, resume=run / "resume.pt"))
    q = Predictor(resumed / "bundle", allow_fixture=True)
    assert p.predict(raw)["alternatives"] == q.predict(raw)["alternatives"]


def test_clean_floor_does_not_stop_before_first_eligible_epoch(tmp_path, raw, monkeypatch):
    data = fixture_data(tmp_path, raw)
    monkeypatch.setattr("netembed.training.f1_score", lambda *args, **kwargs: 0.0)
    cfg = {
        "augmentation": True,
        "clean_floor": 0.5,
        "epochs": 3,
        "patience": 1,
        "threads": 1,
        "batch_size": 4,
        "architecture": {"hidden": 4, "levels": 1, "embedding_dim": 4},
    }
    with pytest.raises(ValueError, match="no epoch meets"):
        train(data, tmp_path / "runs", cfg)
    failure = json.loads(next((tmp_path / "runs").glob("*/failure.json")).read_text())
    assert failure["epochs_completed"] == 3


def test_augmented_candidate_requires_predeclared_floor(tmp_path):
    with pytest.raises(ValueError, match="clean_floor"):
        train(tmp_path, tmp_path, {"augmentation": True})


def test_augmentation_choices_are_paired_and_include_clean(raw):
    choices = {}
    for ident in (f"flow-{i}" for i in range(120)):
        first, kind = augment_one(raw, ident, 4, 2017)
        second, repeated_kind = augment_one(raw, ident, 4, 2017)
        assert kind == repeated_kind and np.array_equal(first, second)
        choices[ident] = (kind, first)
    assert {kind for kind, _ in choices.values()} == {"clean", "timing", "padding", "observation_loss"}
    for ident in reversed(list(choices)):
        transformed, kind = augment_one(raw, ident, 4, 2017)
        assert kind == choices[ident][0] and np.array_equal(transformed, choices[ident][1])
        if kind == "clean":
            assert np.array_equal(transformed, raw)
        elif kind == "timing":
            assert np.array_equal(transformed[:, 2], raw[:, 2])
        elif kind == "padding":
            assert np.array_equal(transformed[:, 0], raw[:, 0])
