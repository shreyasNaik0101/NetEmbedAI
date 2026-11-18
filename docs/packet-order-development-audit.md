# Packet ordering and exporter parity: development audit

This audit examines a previously exposed Spotify **selection** visit and a
separate existing PCAP prefix. It does not open the failed policy final-test
recordings, fit models or thresholds, start capture, or select an adaptation.
The existing final failure and earlier rejected timing repair remain unchanged.

## Browser versus capture ordering

The checksum-bound `spotify-dev-01` selection archive has four eligible
Spotify connections reaching ten packets. In **all four**, Chrome's recorded
socket events and packet capture disagreed somewhere within the first ten on
both merged direction sequence and merged payload-size sequence. Nevertheless,
for **all four**, ordered payload sizes agreed separately within each direction.
The same visit had 22 reported dropped viewer events and two mapped connections
excluded for missing socket prefixes. These are four correlated connections from
one previously exposed visit, not four independent visits or a population rate.

The comparison is conditioned on successful browser-origin attribution and
within-direction QC. Chrome records socket activity at a different observation
point with millisecond event times; packet capture records timestamps at its own
point. Therefore disagreement does not show which source reflects wire order or
that the live adapter is wrong. Browser labels and endpoint tokens were used only
to verify the comparison, never as model inputs. The current forest uses summary
statistics of the first ten packets, including direction-specific timing and
sizes. A different interleaving can change which packets fall inside that prefix
and how gaps are assigned, but this audit did not test whether any change would
help a model or explain an individual error.

The audit reads only the three explicitly named development archive/rows/parity
files and verifies their hashes and session binding. It blocks other private
captures, all public data, unrelated experiments and network connections. No
model predictions or final-test data are read. An independent JavaScript recount
also found 4/4 direction mismatches, 4/4 size mismatches and 4/4 within-direction
size matches. Report:
`experiments/order-parity-spotify-dev-v1/report.json`, SHA-256
`f2a5109ade09d5df1f0011e35e8e431031041816e0a750bd1333f42f674687cd`.

## Independent exporter comparison

An existing, previously isolated 30-packet PCAP prefix was reprocessed offline
using the **current** TShark adapter, then compared with the saved independent
ipfixprobe 5.8.0 result bound to those same PCAP bytes. All 30 direction and UDP
payload-size values matched, and the maximum gap difference was **0 ms**; the
first ten also matched exactly. No live interface was opened. The prefix's
ownership, network and service provenance are unconfirmed, so it is suitable
only for parser compatibility checks. One prefix cannot establish local live
accuracy, ordering at different observation points, or historical 2022 export
semantics. The two tools seeing the same PCAP also does not prove either is
equivalent to the original training export in every case.

Result: `experiments/order-parity-spotify-dev-v1/recorded-exporter-recheck.json`,
SHA-256 `7c1c33e3ce12bf17e42fa62c1d7c0962e3b93e8114b99ba9ba62b6989275783b`.
The existing independent report and source PCAP checksums are recorded within it.
The earlier constructed RFC and IPv4/IPv6 encapsulation fixtures also exercise
units, directions and sizes; they are software fixtures, not benchmark data.

## Engineering checks and decision

53 focused tests passed, including actual offline TShark fixture extraction,
existing exporter output checks, nanosecond capture handling, and a new
constructed case where opposite-direction events share the same browser
millisecond around the ten-packet boundary. It demonstrates that matching
within-direction sequences does not establish a unique merged order. Python
lint passed. The new diagnostic helpers and reports change no running capture,
model, preprocessing, confidence threshold or service default. Original
recordings and the user's pre-existing notebook change are preserved.

Nearest-millisecond timing was already evaluated with matched training and
inference, and [rejected](spotify-timing-repair-v1.md): it did not improve the
reserved Spotify development cases and harmed retained-service checks. Applying
that transformation or sorting by Chrome event order now would not be supported
by these observations. No candidate has been selected, and the final set must
not be reused for selection or fitting.

The next useful engineering question is whether a separately documented,
deliberately user-started **small paired capture** can retain the same packets
for both the current adapter and the independent exporter, with appropriate
permission and privacy controls. That would test live capture/exporter parity
on actual bytes; a browser log alone cannot establish it. Even a passing parity
check would not establish model accuracy or prove a fix. Representative,
separately assigned development and later independent evaluation data would
still be required for any classifier change.

Re-run the focused checks from `traffic_classification`:

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_order_diagnostic.py tests/test_browser_receive_parity.py tests/test_reference_parity.py tests/test_capture.py tests/test_encapsulation.py -q
.\.venv\Scripts\python.exe -m ruff check src/netembed/order_diagnostic.py scripts/audit_order_development.py scripts/audit_recorded_exporter_parity.py tests/test_order_diagnostic.py tests/test_browser_receive_parity.py
```

The audit scripts use fixed input paths and refuse to overwrite their existing
reports. PCAP and browser reference material remain private local artifacts.
