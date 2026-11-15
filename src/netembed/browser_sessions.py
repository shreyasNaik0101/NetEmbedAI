"""Windows Chrome process-lifetime checks, outside classifier inputs."""

from datetime import datetime
import json
import math
import os
import subprocess


def chrome_inventory():
    if os.name != "nt":
        raise RuntimeError("Chrome process verification currently requires Windows")
    # Fixed read-only command. Never pass user strings or kill/launch a browser.
    command = """$ErrorActionPreference='Stop'
$records=@(Get-Process -Name chrome -ErrorAction SilentlyContinue | ForEach-Object {
    $start=$_.StartTime
    if ($null -eq $start) { throw 'Chrome start time unavailable' }
    [PSCustomObject]@{pid=$_.Id; started_unix_ms=([DateTimeOffset]$start.ToUniversalTime()).ToUnixTimeMilliseconds()}
})
ConvertTo-Json -InputObject $records -Compress
"""
    result = subprocess.run(
        ["powershell.exe", "-NoProfile", "-NonInteractive", "-Command", command],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=True,
        timeout=10,
        creationflags=subprocess.CREATE_NO_WINDOW,
    )
    rows = json.loads(result.stdout)
    validate_inventory(rows)
    return rows


def validate_inventory(rows):
    if not isinstance(rows, list) or len(rows) > 256:
        raise ValueError("invalid Chrome process inventory")
    if len({r["pid"] for r in rows}) != len(rows):
        raise ValueError("duplicate Chrome process")
    for row in rows:
        if (
            not isinstance(row["pid"], int)
            or row["pid"] <= 0
            or not math.isfinite(row["started_unix_ms"])
            or row["started_unix_ms"] <= 0
        ):
            raise ValueError("invalid Chrome process lifetime")


def require_closed(rows):
    validate_inventory(rows)
    if rows:
        raise ValueError(
            "Save your Chrome tabs, then fully exit Chrome before preparing this visit. Keep Edge open. No browser is closed automatically."
        )


def verify_fresh(rows, intent, first_packet_ms):
    validate_inventory(rows)
    if not intent.get("chrome_closed_before_intent"):
        raise ValueError("missing closed-Chrome preparation proof")
    if not rows:
        raise ValueError("Chrome lifetime proof unavailable; Chrome must remain open until archival")
    prepared = datetime.fromisoformat(intent["recorded_before_capture_utc"]).timestamp() * 1000
    if any(r["started_unix_ms"] <= prepared for r in rows):
        raise ValueError("Chrome process predates this prepared visit")
    if min(r["started_unix_ms"] for r in rows) > first_packet_ms:
        raise ValueError("current Chrome instance started after the recorded capture")
