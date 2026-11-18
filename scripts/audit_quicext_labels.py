"""Check an alternative reference rule against CESNET22 training-day APP labels."""

import argparse
import csv
import gzip
import hashlib
import io
import time
import zipfile
from collections import Counter
from pathlib import Path

from netembed.bundle import sha256, write_json
from netembed.data import LABELS
from netembed.quicext_data import ReferenceLabelMap, LABEL_RULE_VERSION
import netembed.quicext_data as label_module
from netembed.service_reference import MAP_SHA256


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--max-rows", type=int, default=1000000)
    args = parser.parse_args()
    if Path(args.output).exists():
        raise FileExistsError(args.output)
    if not 1 <= args.max_rows <= 1000000:
        raise ValueError("audit row budget must be 1..1000000")
    mapper = ReferenceLabelMap()
    counts, correct, statuses = Counter(), Counter(), Counter()
    mismatches, scanned, exhausted = [], 0, False
    start = time.monotonic()
    member = "cesnet-quic22/W-2022-44/1_Mon/flows-20221031.csv.gz"
    archive = Path(args.archive)
    before = archive.stat()
    with zipfile.ZipFile(archive) as source, source.open(member) as zipped:
        with gzip.GzipFile(fileobj=zipped) as compressed:
            with io.TextIOWrapper(compressed, encoding="utf-8", newline="") as text:
                reader = csv.DictReader(text)
                if not {"APP", "QUIC_SNI", "ID"}.issubset(reader.fieldnames or []):
                    raise ValueError("unexpected labelled training CSV schema")
                for row in reader:
                    scanned += 1
                    status, label = mapper.classify(row["QUIC_SNI"])
                    statuses[status] += 1
                    if label:
                        counts[label] += 1
                        correct[label] += int(label == row["APP"])
                        if label != row["APP"] and len(mismatches) < 100:
                            mismatches.append(
                                {
                                    "id_sha256": hashlib.sha256(row["ID"].encode()).hexdigest(),
                                    "reference": label,
                                    "original_app": row["APP"],
                                }
                            )
                    if all(counts[label] >= 25 for label in LABELS):
                        break
                    if scanned >= args.max_rows or time.monotonic() - start > 180:
                        exhausted = True
                        break
    after = archive.stat()
    if (before.st_size, before.st_mtime_ns) != (after.st_size, after.st_mtime_ns):
        raise ValueError("archive changed during audit")
    precision = {label: correct[label] / counts[label] if counts[label] else None for label in LABELS}
    passed = all(counts[label] >= 25 and precision[label] >= 0.99 for label in LABELS)
    write_json(
        args.output,
        {
            "member": member,
            "training_only": True,
            "rows_scanned": scanned,
            "archive_bytes": before.st_size,
            "archive_mtime_ns": before.st_mtime_ns,
            "map_sha256": MAP_SHA256,
            "label_rule_version": LABEL_RULE_VERSION,
            "label_rule_source_sha256": sha256(label_module.__file__),
            "audit_source_sha256": sha256(__file__),
            "statuses": dict(statuses),
            "predicted_counts": dict(counts),
            "correct_counts": dict(correct),
            "reference_precision_by_class": precision,
            "mismatches": mismatches,
            "passed": passed,
            "budget_exhausted": exhausted,
            "rule": "unique non-background service, background only as fallback; conflicts refuse",
            "gate": "at least 25 mapped records per supported class; >=0.99 precision each against original APP",
            "seconds": time.monotonic() - start,
            "note": "Only the first CESNET22 training day is opened. This audits a reference rule, not a trained classifier or official QUICEXT25 APP equivalence. Withheld records stay counted; recall is not claimed. Archive was previously verified in the original data provenance; this bounded member audit records size/mtime but does not rehash or fully CRC-check the entire archive.",
        },
    )


if __name__ == "__main__":
    main()
