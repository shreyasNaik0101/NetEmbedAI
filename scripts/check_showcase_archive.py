"""Check the real showcase archive without opening training or capture data."""

import argparse
import json
import os
from pathlib import Path
import sys
import tempfile
import zipfile

from netembed.bundle import Predictor, sha256
from netembed.contract import Flow

ARTIFACT_ID = "fa1f4837e4ae11c9169258ecb20338ae3c0c81c2d206231fb6fe19405b8d8549"
MEMBERS = {
    "bundle/metadata.json",
    "bundle/checksums.json",
    "bundle/forest.json",
    "DECISION.json",
    "MODEL_CARD.md",
    "NOTICE.txt",
}


def validate_inventory(archive):
    entries = archive.infolist()
    if (
        len(entries) != len(MEMBERS)
        or {entry.filename for entry in entries} != MEMBERS
        or any(entry.file_size > 50 * 1024 * 1024 for entry in entries)
    ):
        raise ValueError("unexpected or oversized archive members")


def deny_training(event, args):
    if event != "open" or not isinstance(args[0], (str, bytes)):
        return
    path = Path(os.fsdecode(args[0])).resolve()
    if any(path.is_relative_to(Path(root).resolve()) for root in ("data", "artifacts/local", "experiments")):
        raise ValueError("training data, local captures and experiment artifacts denied")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive", default="artifacts/local/showcase/netembed-ten-packet-unfitted.zip")
    args = parser.parse_args()
    archive_path = Path(args.archive)
    digest = sha256(archive_path)
    with tempfile.TemporaryDirectory(prefix="netembed-showcase-") as temp:
        with zipfile.ZipFile(archive_path) as archive:
            validate_inventory(archive)
            archive.extractall(temp)
        # Install only after reading the archive, so even its original local
        # location is unavailable to inference from the extracted bundle.
        sys.addaudithook(deny_training)
        model = Predictor(Path(temp) / "bundle")
        if (
            model.identity != ARTIFACT_ID
            or model.fixed_prefix_packets != 10
            or model.meta["policy"]["fitted"]
        ):
            raise ValueError("archive does not contain the declared unfitted showcase")
        packets = [
            {"iat_ms": 0 if i == 0 else 0.1, "direction": 1 if i % 2 == 0 else -1, "payload_bytes": 1200}
            for i in range(20)
        ]
        first = model.predict(Flow(packets=packets[:10]).array())
        extended = model.predict(Flow(packets=packets).array())
        if (
            first["label"] is not None
            or first["policy_fitted"]
            or first["model_packets"] != 10
            or extended["model_packets"] != 10
            or first["alternatives"] != extended["alternatives"]
        ):
            raise ValueError("unfitted fixed-prefix contract failed")
        print(
            json.dumps(
                {
                    "result": "pass",
                    "archive_sha256": digest,
                    "artifact_id": model.identity,
                    "fixture_input": True,
                    "training_data_read": False,
                    "live_capture": False,
                }
            )
        )


if __name__ == "__main__":
    main()
