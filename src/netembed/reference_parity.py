"""Read ipfixprobe PSTATS text for small offline reference fixtures."""

import re

from .contract import Flow, Packet


def parse_pstats_text(text):
    rows = re.findall(
        r"ppisizes=\(([^)]*)\),ppitimes=\(([^)]*)\),ppiflags=\([^)]*\),ppidirs=\(([^)]*)\)", text
    )
    if len(rows) != 1:
        raise ValueError("reference fixture requires exactly one PSTATS flow")
    sizes, timestamps, directions = [part.split(",") for part in rows[0]]
    if not 1 <= len(sizes) <= 30 or not len(sizes) == len(timestamps) == len(directions):
        raise ValueError("invalid reference sequence lengths")
    times_us = []
    for value in timestamps:
        seconds, micros = value.split(".", 1)
        if not seconds.isdigit() or not micros.isdigit() or not 0 <= int(micros) < 1000000:
            raise ValueError("invalid reference timestamp")
        # ipfixprobe get_text() writes sec << '.' << usec WITHOUT zero-padding.
        # Thus 100.8500 means 100 sec + 8500 usec, not the decimal 100.8500 sec.
        times_us.append(int(seconds) * 1000000 + int(micros))
    return Flow(
        packets=[
            Packet(
                iat_ms=(times_us[i] - times_us[i - 1]) / 1000 if i else 0,
                direction=int(direction),
                payload_bytes=int(size),
            )
            for i, (size, direction) in enumerate(zip(sizes, directions))
        ]
    )
