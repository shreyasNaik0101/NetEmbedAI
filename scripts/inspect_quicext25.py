"""Inspect a bounded local QUICEXT25 sample; never train or create APP labels."""

import argparse
from collections import Counter, defaultdict
from functools import lru_cache
from itertools import islice
from pathlib import Path

import numpy as np

from netembed.bundle import sha256, write_json
from netembed.contract import validate_array
from netembed.service_reference import MAP_SHA256, attribute

COLUMNS = (
    "PPI",
    "PPI_LEN",
    "QUIC_SNI",
    "PROTOCOL",
    "DST_PORT",
    "QUIC_CLIENT_VERSION",
    "QUIC_MULTIPLEXED",
    "QUIC_TLS_EXT_TYPE",
)


def inspect_rows(rows, limit):
    """Aggregate references without retaining names, endpoints or packet rows."""
    if not 1 <= limit <= 262144:
        raise ValueError("inspection row limit must be 1..262144")
    counts, statuses, failures = Counter(), Counter(), Counter()
    names, protected_names, candidates = Counter(), Counter(), Counter()
    sizes = defaultdict(Counter)
    mapped = lru_cache(maxsize=8192)(attribute)
    for row in islice(rows, limit):
        counts["inspected_rows"] += 1
        reference = mapped(row["QUIC_SNI"])
        statuses[reference["status"]] += 1
        protected = bool({65037, 65486} & set(row["QUIC_TLS_EXT_TYPE"] or []))
        counts["protected_name_indications"] += int(protected)
        label = reference.get("label")
        if label:
            names[label] += 1
            protected_names[label] += int(protected)
        try:
            length = row["PPI_LEN"]
            ppi = np.asarray(row["PPI"], dtype=np.float64)
            if ppi.ndim != 2 or ppi.shape[0] != 3 or not 1 <= length <= 30 or ppi.shape[1] < length:
                raise ValueError("shape/length")
            if np.any(ppi[:, length:] != 0):
                raise ValueError("nonzero padding")
            x = validate_array(ppi[:, :length].T)
        except (ValueError, TypeError):
            failures["invalid_packet_contract"] += 1
            continue
        counts["valid_packet_contract"] += 1
        basic = (
            row["PROTOCOL"] == 17
            and row["DST_PORT"] == 443
            and row["QUIC_CLIENT_VERSION"] in (1, 0x6B3343CF)
            and row["QUIC_MULTIPLEXED"] == 0
            and x[0, 1] == 1
            and x[0, 2] >= 1200
            and length >= 5
        )
        counts["basic_candidates_only"] += int(basic)
        if label and basic:
            sizes[label][int(x[0, 2])] += 1
            if not protected:
                candidates[label] += 1
    mapped.cache_clear()
    return {
        "counts": dict(counts),
        "invalid_contract_counts": dict(failures),
        "historical_map_statuses": dict(statuses),
        "provisional_name_matches": dict(names),
        "protected_indications_in_name_matches": dict(protected_names),
        "basic_candidates_without_protected_name_by_reference": dict(candidates),
        "initial_payload_histograms_basic_candidates": {k: dict(sorted(v.items())) for k, v in sizes.items()},
        "historical_reference_map_sha256": MAP_SHA256,
        "training_ready": False,
        "note": "Development schema inspection only. References use the historical CESNET22 map, not verified QUICEXT25 APP labels. ECH/ESNI may be GREASE; those indications stay excluded from candidate references. Basic candidates are not proven client Initials. No export, fitting, inference or final-test access. A first-row sample is not population prevalence. Names and addresses are absent from this aggregate output.",
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", required=True)
    parser.add_argument("--expected-sha256", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--max-rows", type=int, default=16384)
    args = parser.parse_args()
    if Path(args.output).exists():
        raise FileExistsError("inspection exists; choose a new output path")
    source = Path(args.source)
    if source.stat().st_size > 256 * 1024 * 1024:
        raise ValueError("inspection file exceeds 256 MiB limit")
    digest = sha256(source)
    if digest != args.expected_sha256:
        raise ValueError("source checksum mismatch")
    import pyarrow
    import pyarrow.parquet as pq

    with pq.ParquetFile(source) as parquet:
        if not set(COLUMNS).issubset(parquet.schema_arrow.names):
            raise ValueError("unsupported inspection schema")
        rows = (
            row
            for batch in parquet.iter_batches(batch_size=512, columns=list(COLUMNS), use_threads=False)
            for row in batch.to_pylist()
        )
        report = inspect_rows(rows, args.max_rows)
        report.update(
            source_sha256=digest,
            source_rows=parquet.metadata.num_rows,
            source_has_app_column="APP" in parquet.schema_arrow.names,
            pyarrow_version=pyarrow.__version__,
            row_limit=args.max_rows,
        )
    write_json(args.output, report)


if __name__ == "__main__":
    main()
