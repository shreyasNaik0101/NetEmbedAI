import copy
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pytest

from netembed.bundle import Predictor, export_bundle, sha256, write_json
from netembed.contract import Flow, Normalizer, summary
from netembed.local_policy import calibration_guard, local_check, select_policy, frozen_policy
from netembed.paired_study import CALIBRATION_SHA, read_plan


def cases(label, index, n=3):
    result = []
    for i in range(n):
        for budget in (10, 20, 30):
            p = [0.025, 0.025, 0.025]
            p[index] = 0.95
            result.append(
                {
                    "id": f"{label}-{i}",
                    "reference": label,
                    "budget": budget,
                    "top1": ["youtube", "instagram", "spotify"][index],
                    "probabilities": p,
                }
            )
    return result


def config():
    return read_plan("configs/forest-policy-calibration-v1.json")


def test_lowest_eligible_policy_and_class_error_guard():
    cfg = config()
    labels = ["youtube", "instagram", "spotify"]
    local = cases("youtube", 0) + cases("instagram", 1)
    public = local + cases("spotify", 2, 6)
    policy, selected, curve = select_policy(local, public, labels, cfg)
    assert policy["fitted"] and policy["threshold"] == 0 and policy["min_packets"] == 10
    assert len(curve) == 101 and selected["local"]["primary"]["instagram"]["accepted"] == 3
    bad = copy.deepcopy(local)
    for r in bad:
        if r["reference"] == "instagram":
            r["top1"], r["probabilities"] = "youtube", [0.95, 0.025, 0.025]
    policy, selected, _ = select_policy(bad, public, labels, cfg)
    assert not policy["fitted"] and selected is None
    assert local_check(bad, 1.0, cfg)["eligible"] is False


def test_duplicate_and_nonfinite_cases_cannot_fit():
    cfg = config()
    rows = cases("youtube", 0) + cases("instagram", 1)
    with pytest.raises(ValueError, match="duplicated"):
        select_policy(rows + rows[:1], rows, ["youtube", "instagram", "spotify"], cfg)
    rows[0]["probabilities"][0] = float("nan")
    with pytest.raises(ValueError, match="invalid"):
        select_policy(rows, rows, ["youtube", "instagram", "spotify"], cfg)


@pytest.mark.parametrize(
    "path",
    [
        "x/forest-eval-ig-01-rows.json",
        "data/processed/v2/test.jsonl",
        "artifacts/local/browser-development/instagram-cal-03.json",
        "artifacts/local/prospective-paired-followup-v1/paired-predictions.json",
    ],
)
def test_calibration_cannot_read_final_or_previous_local_evidence(path):
    with pytest.raises(ValueError, match="excluded"):
        calibration_guard("open", (path, "r"))


def test_final_collection_requires_a_successful_policy(tmp_path):
    with pytest.raises(FileNotFoundError):
        frozen_policy(tmp_path, config())
    write_json(tmp_path / "calibration-decision.json", {"policy": {"fitted": False}})
    with pytest.raises(ValueError, match="stopped"):
        frozen_policy(tmp_path, config())


def test_fit_and_sealed_final_end_to_end_on_constructed_fixtures(tmp_path, monkeypatch):
    """Software fixture only: no real model or browser study outcomes used."""
    from sklearn.ensemble import RandomForestClassifier
    import netembed.local_policy as module

    cfg = config()
    labels = ["youtube", "instagram", "spotify"]
    flows = []
    for size in (100, 600, 1200):
        raw = np.tile([1, 1, size], (30, 1)).astype(np.float32)
        raw[0, 0] = 0
        flows.append(raw)
    rf = RandomForestClassifier(n_estimators=3, random_state=17).fit(
        [summary(x) for x in flows] * 5, [0, 1, 2] * 5
    )
    bundle = export_bundle(tmp_path / "source", rf, Normalizer.fit(flows), labels, {"fixture": True})
    cfg["candidate"] = {
        "bundle": str(bundle),
        "metadata": {"path": str(bundle / "metadata.json"), "sha256": sha256(bundle / "metadata.json")},
    }
    cfg["candidate_weight_sha256"] = sha256(bundle / "forest.json")
    monkeypatch.setattr(module, "Predictor", lambda p: Predictor(p, allow_fixture=True))
    model = module.candidate(cfg)
    root = tmp_path / "study"
    root.mkdir()
    for i, spec in enumerate(cfg["trials"]):
        raw = flows[labels.index(spec["target"])]
        rows = [
            {
                "id": f"fixture:{i}:{j}",
                "label": spec["target"],
                "packets": Flow.from_array(raw).model_dump()["packets"],
            }
            for j in range(3)
        ]
        rowpath = root / (spec["id"] + "-rows.json")
        write_json(rowpath, rows)
        start = datetime(2026, 11, 2 if i < 2 else 4, 10, i % 2, tzinfo=timezone.utc).timestamp() * 1000
        write_json(
            root / (spec["id"] + "-archive.json"),
            {
                "trial_id": spec["id"],
                "session_id": str(i),
                "status": "usable",
                "collection_role": spec["role"],
                "first_packet_ms": start,
                "last_packet_ms": start + 1000,
                "plan_sha256": CALIBRATION_SHA,
                "files": {rowpath.name: sha256(rowpath)},
            },
        )
    manifest = tmp_path / "manifest.json"
    write_json(manifest, {})
    cfg["public_manifest_sha256"] = sha256(manifest)
    public = [flows[i] for i in range(3) for _ in range(50)]
    monkeypatch.setattr(
        module,
        "read_split",
        lambda data, split: (
            public,
            np.repeat([0, 1, 2], 50),
            [f"public:{i}" for i in range(150)],
            {"labels": labels},
        )
        if split == "calibration"
        else pytest.fail("wrong split"),
    )

    class Clock(datetime):
        @classmethod
        def now(cls, tz=None):
            return datetime(2026, 11, 3, tzinfo=timezone.utc)

    monkeypatch.setattr(module, "datetime", Clock)
    original_read = Path.read_text

    def no_final(self, *args, **kwargs):
        if "-eval-" in self.name:
            pytest.fail("final data opened during fitting")
        return original_read(self, *args, **kwargs)

    with monkeypatch.context() as scope:
        scope.setattr(Path, "read_text", no_final)
        decision = module.fit(root, cfg, tmp_path)
    assert decision["policy"]["fitted"] and decision["fixture"]
    assert sha256(root / "policy-bundle/forest.json") == sha256(bundle / "forest.json")
    loaded, _ = module.frozen_policy(root, cfg)
    assert loaded.normalizer.metadata() == model.normalizer.metadata()
    for raw in flows:
        np.testing.assert_array_equal(loaded.probabilities([raw]), model.probabilities([raw]))
    assert loaded.predict(flows[0][:5])["label"] is None
    with pytest.raises(ValueError, match="after policy"):
        module.frozen_policy(root, cfg, datetime(2026, 11, 2, tzinfo=timezone.utc).timestamp() * 1000)
    report = module.evaluate(root, cfg)
    assert report["metrics"]["eligible"] and report["fixture"] and not report["default_promoted"]
    sealed = sha256(root / "final-report.json")
    with pytest.raises(FileExistsError):
        module.evaluate(root, cfg)
    with pytest.raises(FileExistsError):
        module.fit(root, cfg, tmp_path)
    assert sha256(root / "final-report.json") == sealed
