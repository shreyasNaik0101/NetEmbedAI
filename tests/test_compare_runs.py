import hashlib
import json

import pytest

from scripts.compare_runs import compare, load_run


def run_fixture(root, name, seed, manifest="same", split="selection"):
    path = root / name
    (path / "bundle").mkdir(parents=True, exist_ok=True)
    (path / "selection").mkdir(exist_ok=True)
    metadata = b"{}"
    (path / "bundle" / "metadata.json").write_bytes(metadata)
    result = {
        "config": {"kind": "forest", "loss": "ce", "augmentation": False, "seed": seed},
        "fixture": False,
        "run_id": name,
        "data_manifest_sha256": manifest,
        "source_commit": "example",
    }
    (path / "result.json").write_text(json.dumps(result))
    cases = {
        f"all_flows/{budget}/{stress}": {"macro_f1": 0.5}
        for budget in (5, 10, 20, 30)
        for stress in ("clean", "timing", "padding", "observation_loss")
    }
    report = {
        "split": split,
        "artifact_id": hashlib.sha256(metadata).hexdigest(),
        "data_manifest_sha256": manifest,
        "protocols": cases,
    }
    (path / "selection" / "report.json").write_text(json.dumps(report))
    return path


def test_comparison_rejects_final_test_and_mixed_data(tmp_path):
    path = run_fixture(tmp_path, "one", 17, split="test")
    with pytest.raises(ValueError, match="selection/artifact mismatch"):
        load_run(path)
    run_fixture(tmp_path, "one", 17)
    run_fixture(tmp_path, "two", 42, manifest="different")
    with pytest.raises(ValueError, match="different prepared data"):
        compare(tmp_path)
