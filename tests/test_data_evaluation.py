import hashlib
import json
import numpy as np
import pytest
from netembed.data import LABELS, prepare, read_split
from netembed.evaluation import evaluate, metrics


def test_final_test_guard(tmp_path):
    with pytest.raises(ValueError, match="final test"):
        read_split(tmp_path, "test")


def test_metric_regeneration():
    rows = [{"truth": 0, "scores": [0.9, 0.1]}, {"truth": 1, "scores": [0.7, 0.3]}]
    restored = json.loads(json.dumps(rows))
    report = metrics([r["truth"] for r in restored], [r["scores"] for r in restored], ["a", "b"], 0.8, True)
    assert report["accuracy"] == 0.5 and report["coverage"] == 0.5 and report["accepted_error"] == 0
    assert report["confusion"] == [[1, 0], [1, 0]]


def test_evaluation_reuses_identical_predictions_for_matched_cohort():
    class Predictor:
        labels = ["a", "b"]
        meta = {"kind": "tcn", "policy": {"threshold": 0.5, "fitted": True}}
        identity = "fixture"
        calls = 0

        def probabilities(self, flows):
            self.calls += 1
            return np.asarray([[0.9, 0.1] if x[0, 1] == 1 else [0.1, 0.9] for x in flows])

    flows = [
        np.asarray([[0 if i == 0 else 1, direction, 1200] for i in range(length)], dtype=np.float32)
        for length, direction in ((30, 1), (6, -1), (30, 1))
    ]
    predictor = Predictor()
    report, rows = evaluate(predictor, flows, np.asarray([0, 1, 0]), ["long-a", "short", "long-b"])
    assert predictor.calls == 16  # four budgets x four conditions, without a second matched-cohort pass
    assert report["protocols"]["matched_30/5/clean"]["n"] == 2
    assert report["protocols"]["all_flows/5/clean"]["n"] == 3
    matched = next(row for row in rows if row["protocol"] == "matched_30/5/clean")
    full = next(row for row in rows if row["protocol"] == "all_flows/5/clean")
    assert matched["id"] == full["id"] and matched["scores"] == full["scores"]


def test_prepare_audits_repeated_short_features_without_dropping_distinct_flows(tmp_path):
    rows = []
    serial = 0
    shared = [
        {"iat_ms": 0, "direction": 1, "payload_bytes": 1200},
        {"iat_ms": 8, "direction": -1, "payload_bytes": 135},
    ]
    for label in LABELS:
        groups = []
        for calibrated in (True, False):
            i = 0
            while len([ident for ident, is_cal in groups if is_cal == calibrated]) < 2:
                ident = f"{label}-dev-{i}"
                is_cal = int(hashlib.sha256(("17:" + ident).encode()).hexdigest()[:8], 16) % 4 == 0
                if is_cal == calibrated:
                    groups.append((ident, is_cal))
                i += 1
        for date, ids in (
            ("2022-10-31", [f"{label}-train-0", f"{label}-train-1"]),
            ("2022-11-07", [ident for ident, _ in groups]),
            ("2022-11-14", [f"{label}-test-0", f"{label}-test-1"]),
        ):
            for index, ident in enumerate(ids):
                serial += 1
                packets = (
                    shared
                    if label == "youtube" and index == 0
                    else [
                        {"iat_ms": 0, "direction": 1, "payload_bytes": 200 + serial},
                        {"iat_ms": 8, "direction": -1, "payload_bytes": 100},
                    ]
                )
                rows.append({"id": ident, "date": date, "label": label, "packets": packets})
    source = tmp_path / "flows.jsonl"
    source.write_text("".join(json.dumps(row) + "\n" for row in rows))
    provenance = tmp_path / "provenance.json"
    provenance.write_text(
        json.dumps(
            {
                "dataset": "CESNET-QUIC22",
                "version": "software-fixture",
                "license": "software-test only",
                "exporter": "software-fixture",
                "direction_verified": True,
                "source_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
                "fixture": True,
            }
        )
    )
    output = tmp_path / "prepared"
    prepare(source, output, provenance)
    manifest = json.loads((output / "manifest.json").read_text())
    audit = manifest["feature_collision_audit"]
    assert audit["cross_period_feature_groups"] == 1
    assert audit["cross_period_feature_rows"] == 3
    assert audit["cross_period_label_conflict_groups"] == 0
    assert audit["unique_flow_ids"] == len(rows)
    assert len(read_split(output, "test", allow_final=True)[0]) == 20
