"""Portable commands. No command implicitly trains or starts packet capture."""

import argparse
import json
import os
from pathlib import Path
import torch
from .bundle import Predictor, sha256, write_json
from .contract import Flow


def main():
    p = argparse.ArgumentParser(prog="netembed")
    commands = p.add_subparsers(dest="command", required=True)
    serve = commands.add_parser("serve")
    serve.add_argument("--bundle")
    serve.add_argument("--port", type=int, default=8000)
    for name in ("predict", "benchmark"):
        sub = commands.add_parser(name)
        sub.add_argument("--bundle", required=True)
        sub.add_argument("--flow", required=True)
        if name == "benchmark":
            sub.add_argument("--output", required=True)
    exporter = commands.add_parser("export-cesnet")
    exporter.add_argument("--source", required=True)
    exporter.add_argument("--output", required=True)
    exporter.add_argument("--license", required=True)
    exporter.add_argument("--per-class-day", type=int, default=200)
    csv_exporter = commands.add_parser("export-cesnet-csv")
    csv_exporter.add_argument("--source", required=True)
    csv_exporter.add_argument("--output", required=True)
    csv_exporter.add_argument("--license", required=True)
    csv_exporter.add_argument("--per-class-day", type=int, default=200)
    csv_exporter.add_argument("--expected-md5", default="2d52ad44ddb22645a3464634fc54bb9c")
    prep = commands.add_parser("prepare")
    prep.add_argument("--source", required=True)
    prep.add_argument("--provenance", required=True)
    prep.add_argument("--output", required=True)
    prep.add_argument("--limit", type=int, default=60000)
    train = commands.add_parser("train")
    train.add_argument("--data", required=True)
    train.add_argument("--config", required=True)
    train.add_argument("--output", default="experiments")
    train.add_argument("--resume")
    evaluate = commands.add_parser("evaluate")
    evaluate.add_argument("--data", required=True)
    evaluate.add_argument("--bundle", required=True)
    evaluate.add_argument("--output", required=True)
    evaluate.add_argument("--split", choices=["selection", "test"], default="selection")
    evaluate.add_argument("--decision", help="frozen decision JSON required for final test")
    offline = commands.add_parser("capture-file")
    offline.add_argument("--pcap", required=True)
    offline.add_argument("--output", required=True)
    offline.add_argument("--reference-check", action="store_true")
    offline.add_argument(
        "--observation-windows",
        action="store_true",
        help="offline descriptive windows, not live capture or predictions",
    )
    netlog = commands.add_parser("attribute-netlog")
    netlog.add_argument("--evidence", required=True)
    netlog.add_argument("--netlog", required=True)
    netlog.add_argument("--output", required=True)
    netlog.add_argument(
        "--expanded-netlog", action="store_true", help="explicit bounded expanded offline log profile"
    )
    netlog.add_argument(
        "--stream-netlog",
        action="store_true",
        help="bounded Chrome JSON-lines attribution for large stopped logs",
    )
    a = p.parse_args()
    torch.set_num_threads(int(os.environ.get("NETEMBED_THREADS", "4")))
    if a.command == "serve":
        import uvicorn
        from .api import create_app

        uvicorn.run(create_app(a.bundle), host="127.0.0.1", port=a.port)
    elif a.command == "export-cesnet":
        from .export_cesnet import export

        export(a.source, a.output, a.license, a.per_class_day)
    elif a.command == "export-cesnet-csv":
        from .export_cesnet_csv import export

        export(a.source, a.output, a.license, a.per_class_day, a.expected_md5)
    elif a.command == "prepare":
        from .data import prepare

        prepare(a.source, a.output, a.provenance, a.limit)
    elif a.command == "train":
        from .training import train

        print(train(a.data, a.output, json.loads(Path(a.config).read_text()), a.resume))
    elif a.command in ("predict", "benchmark"):
        predictor = Predictor(a.bundle)
        raw = Flow.model_validate_json(Path(a.flow).read_text()).array()
        if a.command == "predict":
            print(json.dumps(predictor.predict(raw), indent=2))
        else:
            from .evaluation import benchmark

            write_json(a.output, benchmark(predictor, raw))
    elif a.command == "evaluate":
        from .data import read_split
        from .evaluation import evaluate

        predictor = Predictor(a.bundle)
        if a.split == "test":
            if not a.decision:
                p.error("final test requires --decision frozen using development evidence")
            decision = json.loads(Path(a.decision).read_text())
            if (
                decision["artifact_id"] != predictor.identity
                or not decision.get("rationale")
                or decision["data_manifest_sha256"] != sha256(Path(a.data) / "manifest.json")
                or not decision.get("development_runs")
            ):
                p.error("frozen decision does not match artifact/data or lacks development evidence")
        flows, y, ids, manifest = read_split(a.data, a.split, allow_final=a.split == "test")
        report, rows = evaluate(predictor, flows, y, ids)
        report.update(split=a.split, data_manifest_sha256=sha256(Path(a.data) / "manifest.json"))
        out = Path(a.output)
        out.mkdir(parents=True, exist_ok=False)
        predictions = out / "predictions.jsonl"
        predictions.write_text("".join(json.dumps(r) + "\n" for r in rows))
        report["predictions_sha256"] = sha256(predictions)
        write_json(out / "report.json", report)
    elif a.command == "capture-file":
        from .offline import extract

        write_json(a.output, extract(a.pcap, a.reference_check, a.observation_windows))
    elif a.command == "attribute-netlog":
        from .netlog_reference import correlate_files

        correlate_files(
            a.evidence, a.netlog, a.output, stream_netlog=a.stream_netlog, expanded_netlog=a.expanded_netlog
        )


if __name__ == "__main__":
    main()
