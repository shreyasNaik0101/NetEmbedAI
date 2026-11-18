"""Create a local, deterministic inference archive. Never trains or publishes."""

import argparse
import hashlib
import json
import zipfile
from pathlib import Path

from netembed.bundle import Predictor


def main():
    root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser()
    parser.add_argument("--bundle", required=True)
    parser.add_argument("--decision", default=str(root / "configs/default-decision.json"))
    parser.add_argument("--model-card", default=str(root / "docs/model-card.md"))
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    bundle, output = Path(args.bundle), Path(args.output)
    checksum = output.with_suffix(output.suffix + ".sha256")
    if output.exists() or checksum.exists():
        raise FileExistsError("archive or checksum exists; choose a new output path")
    predictor = Predictor(bundle)  # Validates trusted real bundle; rejects fixtures.
    decision = Path(args.decision)
    if json.loads(decision.read_text())["artifact_id"] != predictor.identity:
        raise ValueError("frozen decision does not identify this bundle")
    model_file = "weights.pt" if predictor.meta["kind"] == "tcn" else "forest.json"
    members = {
        "bundle/" + name: (bundle / name).read_bytes()
        for name in ("metadata.json", "checksums.json", model_file)
    }
    members["DECISION.json"] = decision.read_bytes()
    members["MODEL_CARD.md"] = Path(args.model_card).read_bytes()
    members["NOTICE.txt"] = (
        "NetEmbedAI v2 local inference archive. No publication is performed.\n"
        f"Artifact identity: {predictor.identity}\n"
        "Load the bundle/ directory using the repository's Python 3.11 CPU setup.\n"
        "The archive includes saved preprocessing, labels, architecture, policy and provenance.\n"
        "No training data or resumable training checkpoint is included or required.\n"
        "Training dataset: CESNET-QUIC22 version 3 original CSV, CC-BY-4.0.\n"
        "Dataset authors: Jan Luxemburk, Karel Hynek, Tomas Cejka, Andrej Lukacovic, Pavel Siska.\n"
        "Source: https://zenodo.org/records/10728760\n"
        "Dataset license: https://creativecommons.org/licenses/by/4.0/\n"
        "Local-network recognition remains unvalidated. See MODEL_CARD.md for measured limits.\n"
    ).encode("utf-8")
    output.parent.mkdir(parents=True, exist_ok=True)
    # Stored bytes and fixed ZIP headers avoid timestamps/compressor differences.
    with zipfile.ZipFile(output, "x", compression=zipfile.ZIP_STORED) as archive:
        for name, content in sorted(members.items()):
            info = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
            info.create_system = 3
            info.external_attr = 0o644 << 16
            archive.writestr(info, content)
    digest = hashlib.sha256(output.read_bytes()).hexdigest()
    with checksum.open("x", encoding="ascii") as target:
        target.write(f"{digest}  {output.name}\n")
    print(
        json.dumps(
            {
                "archive": str(output),
                "sha256": digest,
                "artifact_id": predictor.identity,
                "bytes": output.stat().st_size,
            }
        )
    )


if __name__ == "__main__":
    main()
