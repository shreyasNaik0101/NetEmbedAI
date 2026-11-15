"""Bounded, streaming adapter for the original CESNET-QUIC22 Zenodo CSV ZIP."""

import csv
import gzip
import hashlib
import io
import json
import re
import zipfile
from collections import defaultdict
from contextlib import ExitStack
from datetime import date as calendar_date
from datetime import timedelta
from pathlib import Path

import numpy as np

from .bundle import sha256, write_json
from .contract import Flow, validate_array
from .data import LABELS, PERIODS

ZENODO_RECORD = "https://zenodo.org/records/10728760"
ZENODO_ZIP_MD5 = "2d52ad44ddb22645a3464634fc54bb9c"
REQUIRED_COLUMNS = {"ID", "TIME_FIRST", "APP", "PPI", "PPI_LEN"}
FLOW_NAME = re.compile(r"flows-(\d{8})\.csv(?:\.gz)?$")


def _hashes(path):
    md5 = hashlib.md5(usedforsecurity=False)
    sha = hashlib.sha256()
    with Path(path).open("rb") as source:
        for block in iter(lambda: source.read(8 * 1024 * 1024), b""):
            md5.update(block)
            sha.update(block)
    return md5.hexdigest(), sha.hexdigest()


def _parse_row(row, member, line_number):
    location = f"{member}:{line_number}"
    try:
        when = calendar_date.fromisoformat(row["TIME_FIRST"][:10]).isoformat()
        length = int(row["PPI_LEN"])
        ppi = np.asarray(json.loads(row["PPI"]), dtype=np.float32)
        if ppi.ndim != 2 or ppi.shape[0] != 3 or not 1 <= length <= 30 or ppi.shape[1] < length:
            raise ValueError("unsupported PPI shape/length")
        if np.any(ppi[:, length:] != 0):
            raise ValueError("nonzero PPI padding")
        packets = Flow.from_array(validate_array(ppi[:, :length].T)).packets
        ident = row["ID"].strip()
        if not ident:
            raise ValueError("empty flow ID")
    except (KeyError, TypeError, ValueError, json.JSONDecodeError) as error:
        raise ValueError(f"invalid CESNET CSV record at {location}: {error}") from error
    return when, ident, packets


def export(source, destination, license_id, per_class_day=200, expected_md5=ZENODO_ZIP_MD5):
    """Export selected packet-only flows; verify the full official archive first."""
    if not 1 <= per_class_day <= 10000:
        raise ValueError("per-class/day budget must be 1..10000")
    source, destination = Path(source), Path(destination)
    if destination.exists() or Path(str(destination) + ".provenance.json").exists():
        raise FileExistsError(destination)
    actual_md5, source_sha256 = _hashes(source)
    if expected_md5 and actual_md5.lower() != expected_md5.lower():
        raise ValueError(f"CESNET ZIP MD5 mismatch: {actual_md5}")
    counts = defaultdict(lambda: {label: 0 for label in LABELS})
    seen_dates = set()
    rows_scanned = 0
    partial = Path(str(destination) + ".partial")
    if partial.exists():
        raise FileExistsError(partial)
    destination.parent.mkdir(parents=True, exist_ok=True)
    try:
        with zipfile.ZipFile(source) as archive, partial.open("w", encoding="utf-8") as output:
            members = sorted(
                [info for info in archive.infolist() if FLOW_NAME.search(info.filename)],
                key=lambda info: info.filename,
            )
            if not members:
                raise ValueError("archive has no CSV flow members")
            for member in members:
                match = FLOW_NAME.search(member.filename)
                file_date = calendar_date(
                    int(match.group(1)[:4]), int(match.group(1)[4:6]), int(match.group(1)[6:])
                )
                day = file_date.isoformat()
                if not any(lo <= day <= hi for lo, hi in PERIODS.values()):
                    continue
                seen_dates.add(day)
                with ExitStack() as stack:
                    stream = stack.enter_context(archive.open(member))
                    if member.filename.lower().endswith(".gz"):
                        stream = stack.enter_context(gzip.GzipFile(fileobj=stream))
                    reader_stream = stack.enter_context(
                        io.TextIOWrapper(stream, encoding="utf-8", newline="")
                    )
                    reader = csv.DictReader(reader_stream)
                    if not reader.fieldnames or not REQUIRED_COLUMNS.issubset(reader.fieldnames):
                        raise ValueError(f"unsupported CESNET flow columns in {member.filename}")
                    for line_number, row in enumerate(reader, start=2):
                        rows_scanned += 1
                        label = row["APP"].strip()
                        if label not in LABELS:
                            continue
                        if counts[day][label] >= per_class_day:
                            continue
                        when, ident, packets = _parse_row(row, member.filename, line_number)
                        observed_date = calendar_date.fromisoformat(when)
                        if observed_date not in (file_date, file_date - timedelta(days=1)):
                            raise ValueError(f"unexpected TIME_FIRST day in {member.filename}:{line_number}")
                        record = {
                            "id": ident,
                            "date": day,
                            "time_first": row["TIME_FIRST"],
                            "label": label,
                            "schema_version": "1",
                            "packets": [packet.model_dump() for packet in packets],
                        }
                        output.write(json.dumps(record, separators=(",", ":")) + "\n")
                        counts[day][label] += 1
                        if all(counts[day][item] >= per_class_day for item in LABELS):
                            break
        if not seen_dates:
            raise ValueError("no supported flows in the configured chronological periods")
        partial.replace(destination)
        write_json(
            str(destination) + ".provenance.json",
            {
                "dataset": "CESNET-QUIC22",
                "version": "Zenodo-v3-original-CSV",
                "license": license_id,
                "exporter": "netembed-csv-v1",
                "direction_verified": True,
                "direction_source": ZENODO_RECORD,
                "source_sha256": sha256(destination),
                "archive_sha256": source_sha256,
                "archive_md5": actual_md5,
                "official_zip_md5_matched": actual_md5 == ZENODO_ZIP_MD5,
                "counts_by_date": dict(sorted(counts.items())),
                "rows_scanned": rows_scanned,
                "sampling": "first bounded records per class/day; deterministic, not population prevalence",
                "partition_date_source": "official flows-YYYYMMDD.csv.gz file date; TIME_FIRST can be previous UTC day",
                "host_session_audit": "unavailable; source flow IDs only",
            },
        )
    except Exception:
        partial.unlink(missing_ok=True)
        raise
