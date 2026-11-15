"""Opt-in evaluation side channel. Nothing in this module determines predictions."""

import csv
import hashlib
import io
from functools import lru_cache
from importlib.resources import files

from .data import LABELS

MAP_SOURCE = "https://zenodo.org/records/10728760"
MAP_SHA256 = "90041edb9cb760265ca8fcdaaa3b1ed6138c7a4c44d3f07b2f063b75776cc5c3"


@lru_cache(maxsize=1)
def rules():
    content = files("netembed").joinpath("reference_data/servicemap.csv").read_bytes()
    if hashlib.sha256(content).hexdigest() != MAP_SHA256:
        raise ValueError("evaluation service-map checksum mismatch")
    return tuple(
        (pattern.strip().lower(), row["Tag"])
        for row in csv.DictReader(io.StringIO(content.decode("utf-8")))
        for pattern in row["Domains"].split(",")
    )


def attribute(host, protected_name_indication=False):
    """Conservative hostname-map reference; discard the name after mapping.

    A wildcard requires a preceding label. Exact labels and suffix boundaries
    matter; ambiguous matches and observed ECH/ESNI never produce a reference.
    """
    if protected_name_indication:
        return {
            "status": "protected_name_unverified",
            "label": None,
            "reason": "ECH/ESNI indication observed. ECH may be GREASE; this does not prove encryption or establish the actual service name.",
        }
    if not host:
        return {"status": "unavailable", "label": None}
    try:
        name = host.rstrip(".").lower().encode("idna").decode("ascii")
        if len(name) > 253 or any(
            not part or len(part) > 63 or not all(c.isalnum() or c == "-" for c in part)
            for part in name.split(".")
        ):
            raise ValueError("invalid hostname")
    except (UnicodeError, ValueError):
        return {"status": "unavailable", "label": None}
    matches = {
        tag
        for pattern, tag in rules()
        if pattern.startswith("*.") and name.endswith(pattern[1:]) and name != pattern[2:]
    }
    matches.update(tag for pattern, tag in rules() if not pattern.startswith("*.") and name == pattern)
    if len(matches) > 1:
        return {"status": "ambiguous", "label": None}
    if not matches:
        return {"status": "unmapped", "label": None}
    label = next(iter(matches))
    if label not in LABELS:
        return {"status": "outside_supported_set", "label": None}
    return {"status": "mapped", "label": label}


def merge_reference(previous, observed):
    if observed is None or observed["status"] == "unavailable":
        return previous
    if previous is None or previous["status"] == "unavailable":
        return observed
    if previous != observed:
        return {"status": "conflicting", "label": None}
    return previous


def summarize(flows):
    """Report agreement only for explicitly mapped references and retained rows."""
    result = {}
    for budget in (5, 10, 20, 30):
        rows = [
            (flow["reference"]["label"], prediction)
            for flow in flows
            if flow.get("reference", {}).get("status") == "mapped"
            for prediction in flow.get("predictions", [])
            if prediction["observed_packets"] == budget
        ]
        accepted = [(label, prediction) for label, prediction in rows if prediction["label"] is not None]
        result[str(budget)] = {
            "referenced_predictions": len(rows),
            "accepted": len(accepted),
            "accepted_mismatches": sum(label != p["label"] for label, p in accepted),
            "coverage": len(accepted) / len(rows) if rows else None,
            "top1_reference_agreement": (
                sum(bool(p["alternatives"]) and label == p["alternatives"][0]["label"] for label, p in rows)
                / len(rows)
                if rows
                else None
            ),
        }
    return result
