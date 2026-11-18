"""Chronological preparation from audited local CESNET exports (JSONL)."""

import hashlib
import json
from collections import Counter
from pathlib import Path
import numpy as np
from .bundle import sha256, write_json
from .contract import Flow

LABELS = [
    "youtube",
    "spotify",
    "instagram",
    "tiktok",
    "snapchat",
    "whatsapp",
    "facebook-messenger",
    "discord",
    "google-drive",
    "microsoft-outlook",
]
PERIODS = {
    "train": ("2022-10-31", "2022-11-06"),
    "development": ("2022-11-07", "2022-11-13"),
    "test": ("2022-11-14", "2022-11-20"),
}


def prepare(source, output, provenance_path, limit=60000):
    provenance = json.loads(Path(provenance_path).read_text())
    for key in ("dataset", "version", "license", "exporter", "direction_verified", "source_sha256"):
        if not provenance.get(key):
            raise ValueError("missing data provenance: " + key)
    if provenance["dataset"] != "CESNET-QUIC22" or provenance["source_sha256"] != sha256(source):
        raise ValueError("dataset identity or source checksum mismatch")
    splits = {k: [] for k in ("train", "selection", "calibration", "test")}
    seen_ids, fingerprints, groups = set(), {}, {}
    rejected = 0
    for line in Path(source).open(encoding="utf-8"):
        record = json.loads(line)
        if record["label"] not in LABELS:
            continue
        date = record["date"]
        partition = next((k for k, (lo, hi) in PERIODS.items() if lo <= date <= hi), None)
        if partition is None:
            rejected += 1
            continue
        sample_id = str(record["id"])
        if sample_id in seen_ids:
            raise ValueError("duplicate sample ID")
        seen_ids.add(sample_id)
        # Retain audit metadata outside predictor input. Group assignment prevents session leakage.
        group = str(record.get("group_id", sample_id))
        if group in groups and groups[group] != partition:
            raise ValueError("group spans chronological partitions; resolve export grouping")
        groups[group] = partition
        period = partition
        if partition == "development":
            partition = (
                "calibration"
                if int(hashlib.sha256(("17:" + group).encode()).hexdigest()[:8], 16) % 4 == 0
                else "selection"
            )
        packets = record["packets"][:30]
        flow = Flow(packets=packets)
        fingerprint = hashlib.sha256(flow.array().tobytes()).hexdigest()
        feature = fingerprints.setdefault(
            fingerprint,
            {
                "periods": set(),
                "splits": set(),
                "labels": set(),
                "counts_by_label": Counter(),
                "length": len(packets),
                "rows": 0,
            },
        )
        feature["periods"].add(period)
        feature["splits"].add(partition)
        feature["labels"].add(record["label"])
        feature["counts_by_label"][record["label"]] += 1
        feature["rows"] += 1
        if len(splits[partition]) < limit:
            splits[partition].append(
                {
                    "id": sample_id,
                    "label": record["label"],
                    "date": date,
                    **({"time_first": record["time_first"]} if "time_first" in record else {}),
                    "group_id": group,
                    **flow.model_dump(),
                    "truncated": len(record["packets"]) > 30,
                }
            )
    counts = {
        k: {label: sum(r["label"] == label for r in rows) for label in LABELS} for k, rows in splits.items()
    }
    if any(n < 2 for count in counts.values() for n in count.values()):
        raise ValueError(f"insufficient class support; no silent class dropping: {counts}")
    output = Path(output)
    output.mkdir(parents=True, exist_ok=False)
    hashes = {}
    for key, rows in splits.items():
        dest = output / (key + ".jsonl")
        dest.write_text("".join(json.dumps(r) + "\n" for r in rows), encoding="utf-8")
        hashes[dest.name] = sha256(dest)
    repeated = [entry for entry in fingerprints.values() if entry["rows"] > 1]
    cross_period = [entry for entry in repeated if len(entry["periods"]) > 1]
    overlap_labels = Counter()
    for entry in cross_period:
        overlap_labels.update(entry["counts_by_label"])
    write_json(
        output / "manifest.json",
        {
            "schema": 1,
            "labels": LABELS,
            "periods": PERIODS,
            "counts": counts,
            "files": hashes,
            "source": provenance,
            "feature_collision_audit": {
                "policy": "retain unique-ID flows with recurring packet features; feature equality alone does not prove duplicate capture",
                "unique_flow_ids": len(seen_ids),
                "unique_feature_fingerprints": len(fingerprints),
                "repeated_feature_groups": len(repeated),
                "repeated_feature_rows": sum(entry["rows"] for entry in repeated),
                "cross_period_feature_groups": len(cross_period),
                "cross_period_feature_rows": sum(entry["rows"] for entry in cross_period),
                "cross_period_label_conflict_groups": sum(len(entry["labels"]) > 1 for entry in cross_period),
                "cross_period_length_groups": dict(
                    sorted(Counter(entry["length"] for entry in cross_period).items())
                ),
                "cross_period_rows_by_label": dict(sorted(overlap_labels.items())),
                "cross_split_feature_groups": sum(len(entry["splits"]) > 1 for entry in repeated),
            },
            "outside_period": rejected,
            "limit_per_partition": limit,
            "development_split": "group hash seed 17, 75% selection / 25% calibration; class support checked",
            "host_overlap": "not audited unless exporter group_id represents host/session",
        },
    )


def read_split(directory, name, allow_final=False):
    if name == "test" and not allow_final:
        raise ValueError("final test requires frozen decision and explicit final evaluation")
    directory = Path(directory)
    manifest = json.loads((directory / "manifest.json").read_text())
    path = directory / (name + ".jsonl")
    if path.name not in manifest["files"]:
        raise ValueError("requested split is not materialized; pilot final data remains reserved")
    if sha256(path) != manifest["files"][path.name]:
        raise ValueError("split checksum mismatch")
    rows = [json.loads(line) for line in path.read_text().splitlines()]
    flows = [Flow(packets=r["packets"]).array() for r in rows]
    labels = np.asarray([manifest["labels"].index(r["label"]) for r in rows])
    return flows, labels, [r["id"] for r in rows], manifest
