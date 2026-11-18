"""Strict local HDF5 exporter. Does not download, fit, or infer service labels."""

import json
from pathlib import Path
import h5py
import numpy as np
from .bundle import sha256, write_json
from .contract import Flow, validate_array
from .data import LABELS, PERIODS


def export(source, destination, license_id, per_class_day=200):
    if per_class_day < 1 or per_class_day > 10000:
        raise ValueError("per-class/day budget must be 1..10000")
    destination = Path(destination)
    if destination.exists():
        raise FileExistsError(destination)
    source_hash = sha256(source)
    counts = {}
    # Open first: a truncated HDF5 fails before any output file is created.
    with h5py.File(source, "r") as database:
        if "flows" not in database:
            raise ValueError("expected CESNET /flows/DYYYYMMDD layout")
        destination.parent.mkdir(parents=True, exist_ok=True)
        with destination.open("w", encoding="utf-8") as output:
            for name in sorted(database["flows"]):
                compact = name.removeprefix("D")
                if len(compact) != 8 or not compact.isdigit():
                    continue
                date = compact[:4] + "-" + compact[4:6] + "-" + compact[6:]
                if not any(lo <= date <= hi for lo, hi in PERIODS.values()):
                    continue
                table = database["flows"][name]
                if not set(("APP", "PPI", "PPI_LEN")).issubset(table.dtype.names or ()):
                    raise ValueError("unsupported HDF5 fields; inspect exporter version")
                enum = h5py.check_enum_dtype(table.dtype.fields["APP"][0])
                if not enum:
                    raise ValueError("APP enum absent; explicit audited service map required")
                label_map = {int(v): k.decode() if isinstance(k, bytes) else k for k, v in enum.items()}
                day_counts = {label: 0 for label in LABELS}
                for start in range(0, len(table), 4096):
                    for offset, row in enumerate(table[start : start + 4096]):
                        label = label_map[int(row["APP"])]
                        if label not in LABELS or day_counts[label] >= per_class_day:
                            continue
                        length = int(row["PPI_LEN"])
                        ppi = np.asarray(row["PPI"])
                        if (
                            ppi.ndim != 2
                            or ppi.shape[0] not in (3, 4)
                            or ppi.shape[1] != 30
                            or not 1 <= length <= 30
                        ):
                            raise ValueError("unsupported PPI shape/length")
                        x = validate_array(ppi[:3, :length].T)
                        if np.any(ppi[:3, length:] != 0):
                            raise ValueError("nonzero padding in source")
                        ident = f"{source_hash[:16]}:{name}:{start + offset}"
                        record = {
                            "id": ident,
                            "date": date,
                            "label": label,
                            **Flow.from_array(x).model_dump(),
                        }
                        output.write(json.dumps(record) + "\n")
                        day_counts[label] += 1
                    if all(n >= per_class_day for n in day_counts.values()):
                        break
                counts[date] = day_counts
    write_json(
        str(destination) + ".provenance.json",
        {
            "dataset": "CESNET-QUIC22",
            "version": "XS-local-HDF5",
            "license": license_id,
            "exporter": "netembed-hdf5-v1",
            "direction_verified": True,
            "direction_source": "https://zenodo.org/records/10728760",
            "source_sha256": sha256(destination),
            "hdf5_sha256": source_hash,
            "h5py": h5py.__version__,
            "counts_by_date": counts,
            "sampling": "first bounded records per class/day; deterministic, not population prevalence",
            "host_session_audit": "unavailable; source row IDs only",
        },
    )
