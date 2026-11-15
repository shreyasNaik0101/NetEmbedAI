"""Fetch three official daily members and prepare a bounded reference-labelled pilot."""

import argparse
import hashlib
import json
import time
import urllib.request
import zlib
from collections import Counter
from datetime import datetime
from functools import lru_cache
from pathlib import Path

from netembed.bundle import sha256, write_json
from netembed.data import LABELS
from netembed.quicext_data import LABEL_RULE_VERSION, PARSER_SOURCE, ReferenceLabelMap, packet_window
from netembed.service_reference import MAP_SHA256

API = "https://zenodo.org/api/records/17249078/files/2025-05.zip/container"


def validate_protocol(protocol):
    splits = ("train", "selection", "calibration")
    if set(protocol["days"]) != set(splits):
        raise ValueError("pilot must declare exactly train/selection/calibration days")
    days = [protocol["days"][split] for split in splits]
    reserved = protocol["reserved_final_days_not_downloaded"]
    for day in days + reserved:
        if datetime.strptime(day, "%Y%m%d").strftime("%Y%m%d") != day:
            raise ValueError("invalid pilot date")
    if not days[0] < days[1] < days[2] or not reserved or min(reserved) <= days[-1]:
        raise ValueError("chronological pilot/final isolation failed")
    for split in splits:
        minimum, cap = protocol["minimum_class_counts"][split], protocol["per_class_caps"][split]
        if not 2 <= minimum <= cap <= 200:
            raise ValueError("invalid bounded pilot class budget")


def fetch_day(day, directory):
    """Never extract paths from an archive or fetch unbounded archive content."""
    if len(day) != 8 or not day.isdigit() or not day.startswith("202505"):
        raise ValueError("pilot only supports explicit May 2025 days")
    target = directory / f"{day}.parquet"
    metadata = directory / f"{day}.download.json"
    if target.exists():
        report = json.loads(metadata.read_text())
        if report["sha256"] != sha256(target):
            raise ValueError("existing day checksum mismatch")
        return target, report
    with urllib.request.urlopen(API, timeout=30) as response:
        raw = response.read(100001)
    if len(raw) > 100000:
        raise ValueError("member index exceeds cap")
    entry = next(x for x in json.loads(raw)["entries"] if x["key"] == target.name)
    if not 0 < entry["size"] <= 128 * 1024 * 1024:
        raise ValueError("daily member exceeds download budget")
    expected_url = API + "/" + target.name
    if entry["links"]["content"] != expected_url:
        raise ValueError("unexpected official member URL")
    partial = target.with_suffix(".parquet.partial")
    start, size, crc = time.monotonic(), 0, 0
    with urllib.request.urlopen(expected_url, timeout=30) as response, partial.open("xb") as output:
        while block := response.read(1024 * 1024):
            size += len(block)
            if size > entry["size"] or time.monotonic() - start > 240:
                raise ValueError("bounded download exceeded size or duration")
            output.write(block)
            crc = zlib.crc32(block, crc)
    if size != entry["size"] or crc != entry["crc"]:
        raise ValueError("official member size/CRC mismatch; partial retained")
    report = {
        "url": expected_url,
        "bytes": size,
        "crc32": f"{crc:08x}",
        "sha256": sha256(partial),
        "index_sha256": hashlib.sha256(raw).hexdigest(),
        "license": "CC-BY-4.0",
        "member_size_crc_verified": True,
        "note": "Direct official HTTPS member, not verification of full monthly ZIP MD5.",
    }
    partial.replace(target)
    write_json(metadata, report)
    print(json.dumps({"downloaded_day": day, "bytes": size}), flush=True)
    return target, report


def export_day(path, day, cap):
    import pyarrow.parquet as pq

    light = [
        "QUIC_SNI",
        "QUIC_TLS_EXT_TYPE",
        "PROTOCOL",
        "DST_PORT",
        "QUIC_CLIENT_VERSION",
        "QUIC_MULTIPLEXED",
        "PPI_LEN",
        "QUIC_OCCID",
        "QUIC_OSCID",
        "DST_IP",
    ]
    heavy = ["PPI", "QUIC_PACKETS"]
    counts, statuses, rejected, records = Counter(), Counter(), Counter(), []
    mapper = lru_cache(maxsize=8192)(ReferenceLabelMap().classify)
    digest, position = sha256(path), 0
    with pq.ParquetFile(path) as source:
        for batch in source.iter_batches(batch_size=1024, columns=light + heavy, use_threads=False):
            # Decode packet arrays only for records still needed under the cap.
            metadata = batch.select(light).to_pylist()
            for offset, row in enumerate(metadata):
                index = position + offset
                protected = bool({65037, 65486} & set(row["QUIC_TLS_EXT_TYPE"] or []))
                status, label = mapper(row["QUIC_SNI"], protected)
                statuses[status] += 1
                if not label or counts[label] >= cap:
                    continue
                for name in heavy:
                    row[name] = batch.column(batch.schema.get_field_index(name))[offset].as_py()
                try:
                    flow = packet_window(row)
                except ValueError as error:
                    rejected[str(error)] += 1
                    continue
                ident = f"{digest}:{index}"
                connection = [row["QUIC_OCCID"] or "", row["QUIC_OSCID"] or ""]
                # No name, address or CID is retained in model inputs/JSONL.
                key = json.dumps([row["DST_IP"], connection], sort_keys=True) if any(connection) else ident
                group = hashlib.sha256(key.encode()).hexdigest()
                records.append(
                    {"id": ident, "group_id": group, "date": day, "label": label, **flow.model_dump()}
                )
                counts[label] += 1
            position += len(batch)
    return records, {
        "rows_scanned": position,
        "counts": dict(counts),
        "reference_statuses": dict(statuses),
        "eligibility_rejections": dict(rejected),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--protocol", required=True)
    parser.add_argument("--label-audit", required=True)
    parser.add_argument("--downloads", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    protocol = json.loads(Path(args.protocol).read_text())
    validate_protocol(protocol)
    audit = json.loads(Path(args.label_audit).read_text())
    if (
        not audit["passed"]
        or audit["label_rule_version"] != LABEL_RULE_VERSION
        or audit["map_sha256"] != MAP_SHA256
    ):
        raise ValueError("label-rule audit gate failed")
    import netembed.quicext_data as label_module

    if audit["label_rule_source_sha256"] != sha256(label_module.__file__):
        raise ValueError("label rule changed after audit")
    if protocol["label_rule_version"] != LABEL_RULE_VERSION:
        raise ValueError("protocol label rule mismatch")
    output, downloads = Path(args.output), Path(args.downloads)
    if output.exists():
        raise FileExistsError(output)
    downloads.mkdir(parents=True, exist_ok=True)
    output.mkdir(parents=True)
    # Persist the complete frozen intent before fetching or inspecting later days.
    write_json(output / "protocol.json", protocol)
    split_rows, reports, groups, files_by_split = {}, {}, {}, {}
    for split in ("train", "selection", "calibration"):
        day = protocol["days"][split]
        path, report = fetch_day(day, downloads)
        rows, stats = export_day(path, day, protocol["per_class_caps"][split])
        counts = Counter(row["label"] for row in rows)
        reports[split] = {"download": report, **stats}
        write_json(output / "preparation-progress.json", reports)
        if any(counts[label] < protocol["minimum_class_counts"][split] for label in LABELS):
            raise ValueError(f"insufficient pilot support; no silent class dropping: {split} {dict(counts)}")
        for row in rows:
            previous = groups.setdefault(row["group_id"], split)
            if previous != split:
                raise ValueError("connection group spans chronological pilot partitions")
        split_rows[split] = rows
        print(json.dumps({"prepared_split": split, "counts": dict(counts)}), flush=True)
    for split, rows in split_rows.items():
        path = output / f"{split}.jsonl"
        path.write_text("".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8")
        files_by_split[path.name] = sha256(path)
    write_json(
        output / "manifest.json",
        {
            "schema": 1,
            "labels": LABELS,
            "periods": protocol["days"],
            "counts": {
                k: {label: sum(r["label"] == label for r in rows) for label in LABELS}
                for k, rows in split_rows.items()
            },
            "files": files_by_split,
            "source": {
                "dataset": protocol["dataset"],
                "version": "experimental-reference-pilot-v1",
                "fixture": False,
                "license": "CC-BY-4.0",
                "label_rule_version": LABEL_RULE_VERSION,
                "map_sha256": MAP_SHA256,
                "audit_sha256": sha256(args.label_audit),
                "protocol_sha256": sha256(args.protocol),
                "exporter_source_sha256": sha256(__file__),
                "quic_packet_flag_source": PARSER_SOURCE,
                "sources": reports,
                "note": "Alternative reference labels audited on CESNET22 training records, not official QUICEXT25 APP labels. Small deterministic imbalanced pilot, no release/default promotion or prevalence claims.",
            },
            "reserved_final_days_not_downloaded": protocol["reserved_final_days_not_downloaded"],
            "final_test_materialized": False,
            "host_overlap": "client host identifiers unavailable; available connection IDs audited across splits",
        },
    )


if __name__ == "__main__":
    main()
