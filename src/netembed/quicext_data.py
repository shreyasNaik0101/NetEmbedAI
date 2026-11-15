"""Offline reference labels for an explicitly experimental QUICEXT25 pilot.

The historical public map is audited separately. These are reference-derived
labels, not the unavailable official QUICEXT25 APP labels or predictor inputs.
"""

import csv
import io
from collections import defaultdict
from importlib.resources import files

import numpy as np

from .bundle import sha256
from .contract import Flow, validate_array
from .data import LABELS
from .service_reference import MAP_SHA256

BACKGROUND = {"google-background", "facebook-background", "default-background"}
LABEL_RULE_VERSION = "quicext-reference-v2-apex-background"
PARSER_SOURCE = "https://raw.githubusercontent.com/CESNET/ipfixprobe/0798224a3ca875402b7600f19e7610b9737aaf51/src/plugins/process/quic/src/quic_parser.hpp"


class ReferenceLabelMap:
    """Specific-service rules precede background fallback; conflicts refuse."""

    def __init__(self):
        resource = files("netembed").joinpath("reference_data/servicemap.csv")
        if sha256(resource) != MAP_SHA256:
            raise ValueError("reference-map checksum mismatch")
        self.exact, self.suffix = defaultdict(set), defaultdict(set)
        for row in csv.DictReader(io.StringIO(resource.read_text(encoding="utf-8"))):
            for raw in row["Domains"].split(","):
                pattern = raw.strip().lower()
                target = self.suffix if pattern.startswith("*.") else self.exact
                target[pattern[2:] if pattern.startswith("*.") else pattern].add(row["Tag"])

    def classify(self, host, protected=False):
        if protected:
            return "protected_name_unverified", None
        if not isinstance(host, str) or not host:
            return "unavailable", None
        try:
            name = host.rstrip(".").lower().encode("idna").decode("ascii")
            parts = name.split(".")
            if len(name) > 253 or any(
                not part or len(part) > 63 or not all(c.isalnum() or c == "-" for c in part) for part in parts
            ):
                raise ValueError("invalid hostname")
        except (ValueError, UnicodeError):
            return "unavailable", None
        # Dataset label-map namespaces may include their apex. This alternative
        # rule is audited against original APP records, never assumed equivalent
        # to the stricter live evaluation matcher.
        matches = set(self.exact.get(name, ()))
        for offset in range(len(parts)):
            matches.update(self.suffix.get(".".join(parts[offset:]), ()))
        specific = matches - BACKGROUND
        if len(specific) > 1:
            return "ambiguous", None
        if not specific:
            return ("background" if matches else "unmapped"), None
        label = next(iter(specific))
        return ("mapped", label) if label in LABELS else ("outside_supported_set", None)


def packet_window(row):
    """Match local eligibility; protocol fields qualify data, never features."""
    if row["PROTOCOL"] != 17 or row["DST_PORT"] != 443:
        raise ValueError("unsupported_transport")
    if row["QUIC_CLIENT_VERSION"] not in (1, 0x6B3343CF):
        raise ValueError("unsupported_version")
    if row["QUIC_MULTIPLEXED"] != 0:
        raise ValueError("multiplexed_connection")
    length = row["PPI_LEN"]
    ppi = np.asarray(row["PPI"], dtype=np.float64)
    if ppi.ndim != 2 or ppi.shape[0] != 3 or not 5 <= length <= 30 or ppi.shape[1] < length:
        raise ValueError("shape_or_short_window")
    if np.any(ppi[:, length:] != 0):
        raise ValueError("nonzero_padding")
    x = validate_array(ppi[:, :length].T)
    codes = row["QUIC_PACKETS"]
    # F_INITIAL=1; coalesced Initial+0RTT is also an Initial datagram.
    # The first PPI position is the first transport-payload-bearing packet.
    if x[0, 1] != 1 or x[0, 2] < 1200 or not codes or not int(codes[0]) & 1:
        raise ValueError("missing_client_initial")
    return Flow.from_array(x)
