import h5py
import numpy as np
import pytest
from netembed.export_cesnet import export


def test_hdf5_export_schema_and_provenance(tmp_path):
    source = tmp_path / "source.h5"
    app = h5py.enum_dtype({"youtube": 0, "spotify": 1}, basetype="i2")
    dtype = np.dtype([("APP", app), ("PPI", "f4", (3, 30)), ("PPI_LEN", "i2")])
    rows = np.zeros(4, dtype=dtype)
    for i in range(4):
        rows[i]["APP"] = i % 2
        rows[i]["PPI_LEN"] = 2
        rows[i]["PPI"][:, 0] = [0, 1, 1200 + i]
        rows[i]["PPI"][:, 1] = [8, -1, 100 + i]
    with h5py.File(source, "w") as f:
        f.create_dataset("flows/D20221031", data=rows)
    target = tmp_path / "export.jsonl"
    export(source, target, "software-test only", 2)
    assert len(target.read_text().splitlines()) == 4
    assert (tmp_path / "export.jsonl.provenance.json").exists()
    with pytest.raises(FileExistsError):
        export(source, target, "software-test only", 2)


def test_truncated_hdf5_fails_without_output(tmp_path):
    source = tmp_path / "broken.h5"
    source.write_bytes(b"not an hdf5 file")
    with pytest.raises(OSError):
        export(source, tmp_path / "out.jsonl", "software-test only")
    assert not (tmp_path / "out.jsonl").exists()
