import csv
import gzip
import hashlib
import io
import json
import zipfile

import pytest

from netembed.export_cesnet_csv import export


def _zip_rows(path, rows):
    content = io.StringIO(newline="")
    writer = csv.DictWriter(content, fieldnames=["ID", "TIME_FIRST", "APP", "PPI", "PPI_LEN"])
    writer.writeheader()
    writer.writerows(rows)
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr("W-2022-44/flows-20221031.csv", content.getvalue())
        archive.writestr("servicemap.csv", "Service,Tag\nExample,youtube\n")
    return hashlib.md5(path.read_bytes(), usedforsecurity=False).hexdigest()


def _row(ident, label="youtube", ppi=None, time_first="2022-10-31T12:00:00.000000"):
    return {
        "ID": ident,
        "TIME_FIRST": time_first,
        "APP": label,
        "PPI": json.dumps(ppi or [[0, 8], [1, -1], [1200, 135]]),
        "PPI_LEN": 2,
    }


def test_csv_zip_export_is_bounded_and_has_provenance(tmp_path):
    source, target = tmp_path / "source.zip", tmp_path / "flows.jsonl"
    digest = _zip_rows(
        source,
        [
            _row("one", time_first="2022-10-30T23:00:00.000000"),
            _row("two"),
            _row("three"),
            _row("four", "spotify"),
        ],
    )
    export(source, target, "CC-BY-4.0", per_class_day=2, expected_md5=digest)
    records = [json.loads(line) for line in target.read_text().splitlines()]
    assert [record["id"] for record in records] == ["one", "two", "four"]
    assert records[0]["date"] == "2022-10-31"
    assert records[0]["time_first"] == "2022-10-30T23:00:00.000000"
    assert records[0]["packets"] == [
        {"iat_ms": 0.0, "direction": 1, "payload_bytes": 1200},
        {"iat_ms": 8.0, "direction": -1, "payload_bytes": 135},
    ]
    provenance = json.loads((tmp_path / "flows.jsonl.provenance.json").read_text())
    assert provenance["archive_md5"] == digest
    assert provenance["source_sha256"] == hashlib.sha256(target.read_bytes()).hexdigest()
    assert provenance["counts_by_date"]["2022-10-31"]["youtube"] == 2
    assert provenance["official_zip_md5_matched"] is False


def test_csv_zip_rejects_checksum_and_invalid_packet_without_output(tmp_path):
    source, target = tmp_path / "source.zip", tmp_path / "flows.jsonl"
    digest = _zip_rows(source, [_row("bad", ppi=[[0, 8], [1, 0], [1200, 135]])])
    with pytest.raises(ValueError, match="MD5 mismatch"):
        export(source, target, "CC-BY-4.0", expected_md5="0" * 32)
    with pytest.raises(ValueError, match="invalid CESNET CSV record"):
        export(source, target, "CC-BY-4.0", expected_md5=digest)
    assert not target.exists()
    assert not (tmp_path / "flows.jsonl.partial").exists()


def test_csv_zip_reads_gzip_member_without_extraction(tmp_path):
    source, target = tmp_path / "source.zip", tmp_path / "flows.jsonl"
    content = io.StringIO(newline="")
    writer = csv.DictWriter(content, fieldnames=["ID", "TIME_FIRST", "APP", "PPI", "PPI_LEN"])
    writer.writeheader()
    writer.writerow(_row("nested"))
    with zipfile.ZipFile(source, "w") as archive:
        archive.writestr("W-2022-44/flows-20221031.csv.gz", gzip.compress(content.getvalue().encode()))
    digest = hashlib.md5(source.read_bytes(), usedforsecurity=False).hexdigest()
    export(source, target, "CC-BY-4.0", expected_md5=digest)
    assert json.loads(target.read_text().splitlines()[0])["id"] == "nested"
