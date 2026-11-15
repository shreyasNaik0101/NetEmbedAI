"""Descriptive saved-parity audit of one declared, previously exposed development visit."""

import json
import os
from pathlib import Path
import sys

from netembed.bundle import sha256
from netembed.order_diagnostic import summarize

ROOT = Path("artifacts/local/spotify-data-repair-v1")
TRIAL = "spotify-dev-01"
ARCHIVE_SHA = "2c6641e357febaff4597f549020a8eb995b16e379be593f686413c499298ee66"
PLAN_SHA = "f4853905ca5bcb0b17bdda8ce92935737a0fa98ceb00c03a24fad33604a6f50e"
INPUTS = [ROOT / (TRIAL + "-" + n + ".json") for n in ("archive", "rows", "socket-parity")]
OUTPUT = Path("experiments/order-parity-spotify-dev-v1/report.json")


def guard(event, args):
    if event in ("socket.connect", "socket.getaddrinfo"):
        raise ValueError("diagnostic is offline")
    if event != "open" or not isinstance(args[0], (str, bytes)):
        return
    path = Path(os.fsdecode(args[0])).resolve()
    if path.is_relative_to(Path("data").resolve()):
        raise ValueError("public data excluded")
    if path.is_relative_to(Path("artifacts/local").resolve()) and path not in [p.resolve() for p in INPUTS]:
        raise ValueError("unrelated private or final data excluded")
    if path.is_relative_to(Path("experiments").resolve()) and path != OUTPUT.resolve():
        raise ValueError("other experiment data excluded")


def main():
    if OUTPUT.exists():
        raise FileExistsError("preserve existing diagnostic report")
    sys.addaudithook(guard)
    if sha256(INPUTS[0]) != ARCHIVE_SHA:
        raise ValueError("development archive changed")
    archive = json.loads(INPUTS[0].read_text())
    if (
        archive["status"] != "usable"
        or archive["collection_role"] != "selection"
        or archive["trial_id"] != TRIAL
        or archive["plan_sha256"] != PLAN_SHA
    ):
        raise ValueError("wrong development role or plan")
    for path in INPUTS[1:]:
        if sha256(path) != archive["files"][path.name]:
            raise ValueError("development input changed")
    rows, parity = (json.loads(p.read_text()) for p in INPUTS[1:])
    if (
        parity["session_id"] != archive["session_id"]
        or parity["evidence_sha256"] != archive["files"][TRIAL + "-capture.json"]
    ):
        raise ValueError("comparison does not bind the archived session")
    result = summarize(rows, parity, archive["session_id"])
    if result["eligible"] != 4:
        raise ValueError("declared development support changed")
    report = {
        "fixture": False,
        "role": "previously exposed selection diagnostic",
        "prefix": 10,
        "counts": result,
        "archive_sha256": ARCHIVE_SHA,
        "inputs": {p.name: sha256(p) for p in INPUTS[1:]},
        "source_sha256": sha256(Path(__file__)),
        "reported_event_drops": archive["quality"]["reported_drops"],
        "excluded_connections": len(archive["excluded"]),
        "model_predictions_read": False,
        "final_data_opened": False,
        "model_fit": False,
        "capture_started": False,
        "limits": "Four correlated eligible Spotify flows from one previously exposed visit, conditioned on browser-origin attribution and within-direction QC. Chrome socket events are userspace observations and millisecond-resolution timestamps, not wire-order ground truth or an independent reconstruction of 2022 CESNET export. Full-prefix includes the first10. No repair or causal claim.",
    }
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT.open("x", encoding="utf-8") as stream:
        json.dump(report, stream, indent=2)
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
