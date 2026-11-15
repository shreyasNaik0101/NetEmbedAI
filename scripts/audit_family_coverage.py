"""Inventory existing development IP families without fitting or starting capture."""

import json
from collections import Counter
from pathlib import Path
import sys

from diagnose_youtube_failure import guard, socket_families
from check_browser_receive_parity import socket_datagrams
from netembed.bundle import sha256, write_json
from netembed.netlog_reference import _targets
from netembed.netlog_stream import read_quic_reference_stream


def main():
    sys.addaudithook(guard)
    root = Path("artifacts/local/browser-development")
    destination = Path("experiments/family-coverage-audit-v1")
    destination.mkdir(exist_ok=True)
    meta_path = Path(
        "experiments/browser-adaptation/selection-followup-v1-seed17/forest/bundle/metadata.json"
    )
    assert sha256(meta_path) == "bd79923fabc4816cc2f15b4f150a5d3b428663c455d0fde3da6ab219eb666d62"
    provenance = json.loads(meta_path.read_text())["provenance"]
    counts, bindings = {}, {}
    for role in ("train", "selection"):
        total = Counter()
        for trial in provenance["config"][role + "_trials"]:
            proof = provenance["browser_evidence"][trial]
            paths = {
                name: root / f"{trial}-{name}.json"
                for name in ("capture", "reference", "netlog", "collection-summary")
            }
            rows_path = root / f"{trial}-development-rows.jsonl"
            assert sha256(rows_path) == proof["rows_sha256"]
            assert sha256(paths["collection-summary"]) == proof["summary_sha256"]
            receipt = json.loads(paths["collection-summary"].read_text())
            for path in paths.values():
                if path.name in receipt["evidence_sha256"]:
                    assert sha256(path) == receipt["evidence_sha256"][path.name]
            output = destination / f"{trial}.json"
            if output.exists():
                report = json.loads(output.read_text())
                assert report["rows_sha256"] == sha256(rows_path)
            else:
                capture = json.loads(paths["capture"].read_text())
                reference = json.loads(paths["reference"].read_text())
                assert reference["evidence_sha256"] == sha256(paths["capture"])
                netlog, digest, reader = read_quic_reference_stream(paths["netlog"], include_sockets=True)
                assert digest == reference["netlog_sha256"]
                salt, targets = _targets(capture)
                families = socket_families(netlog, salt)
                values = []
                for row in (json.loads(line) for line in rows_path.read_text().splitlines()):
                    if row["label"] not in ("youtube", "instagram"):
                        continue
                    ident = row["id"].split(":")[-1]
                    index = next(i for i, f in enumerate(capture["flows"]) if f["flow_id"] == ident)
                    assert row["packets"] == capture["flows"][index]["packets"]
                    target = targets[index]
                    status, packets = socket_datagrams(netlog, salt, target)
                    pair = sorted(families[target["token"]])
                    verified = (
                        status["status"] == "unique_socket"
                        and len(pair) == 1
                        and len(packets) >= len(row["packets"])
                    )
                    family = str(pair[0][0]) if verified and pair[0][0] == pair[0][1] else "unverified"
                    values.append(
                        {
                            "id": row["id"],
                            "label": row["label"],
                            "family": family,
                            "packets": len(row["packets"]),
                            "first_payload": row["packets"][0]["payload_bytes"],
                        }
                    )
                report = {
                    "trial": trial,
                    "role": role,
                    "rows_sha256": sha256(rows_path),
                    "netlog_sha256": digest,
                    "capture_sha256": sha256(paths["capture"]),
                    "reader": reader,
                    "flows": values,
                }
                write_json(output, report)
                del netlog
            total.update(f"{r['label']}:IPv{r['family']}" for r in report["flows"])
            bindings[trial] = sha256(output)
            print(
                json.dumps(
                    {
                        "trial": trial,
                        "counts": dict(Counter(f"{r['label']}:IPv{r['family']}" for r in report["flows"])),
                    }
                ),
                flush=True,
            )
        counts[role] = dict(total)
    final = destination / "report.json"
    assert not final.exists(), "preserve completed audit"
    result = {
        "counts": counts,
        "trial_report_sha256": bindings,
        "source_sha256": sha256(__file__),
        "limits": "Existing validated development exports only. Family from matched browser socket endpoints, never inferred from size or fed to a model. No addresses exported, fitting, calibration/final reads or capture startup.",
    }
    write_json(final, result)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
