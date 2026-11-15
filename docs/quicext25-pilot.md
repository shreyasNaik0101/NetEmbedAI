# Newer-data training pilot — 26 October 2026

Follow-up: the [browser adaptation pilot](browser-adaptation-pilot.md) adds
independently attributed browser examples and improves later-visit development
results. Its selected forest still needs separate calibration and live final
checking. The public-data-only failures below remain unchanged.

Three real trained artifacts were produced, including a 20-epoch supervised
TCN and a same-data forest. **Neither repaired the saved local browser errors.**
The existing B17 default remains selected. No candidate was deployed, no capture
was started, and no new final-test data was opened. Further domain adaptation
needs independently attributed browser development recordings and separate
sessions for evaluation. Four mapped connections per service are a diagnostic
sample, not an adequate replacement training corpus.

## Labels and feature eligibility

The official prepared QUICEXT25 label server still timed out. An explicitly
alternative reference rule uses the published CESNET22 service map: unique
specific-service matches precede broad background fallback. Conflicting specific
matches refuse a label. The rule includes the apex of a namespace such as
`*.drive.google.com`; it is intentionally separate from the stricter live
reference matcher, which was not changed. Neither names nor endpoint identities
are prediction features.

Two audit attempts are retained. The first, strict-subdomain variant matched
166,234 original training records without a mismatch, but found only five Drive
examples in its one-million-row budget and failed the minimum-support gate.
It was not used for training. The revised namespace-apex variant checked 11,423
rows from **only the original 31 October 2022 training-day CSV**. All 3,021
mapped records agreed with the original APP label, with at least 25 mapped
examples per supported class. That passes the predeclared ≥0.99 per-class
precision check on this sample. It does not prove official QUICEXT25 APP
equivalence, complete recall, current labels or browser coverage.

The retained map is SHA-256
`90041edb9cb760265ca8fcdaaa3b1ed6138c7a4c44d3f07b2f063b75776cc5c3`.
Rule version: `quicext-reference-v2-apex-background`. The rule and audit source
hashes are recorded in `label-rule-audit-v2.json`. The source map and its
CC-BY-4.0 attribution are already packaged under `src/netembed/reference_data/`.

Export accepts UDP/443, supported QUIC client versions, no multiplexing, a
5–30-packet valid PPI, first direction +1 and an Initial-bearing first datagram.
It rejects ECH/ESNI indications, including possible GREASE, for these reference
labels. Initial flag 1 is documented in the
[collector source snapshot from May 2025](https://raw.githubusercontent.com/CESNET/ipfixprobe/0798224a3ca875402b7600f19e7610b9737aaf51/src/plugins/process/quic/src/quic_parser.hpp).
The exact deployed collector build is not given in the dataset record, so the
snapshot is supporting evidence rather than proof of that build's identity.
Coalesced Initial+0RTT datagrams remain eligible. Size alone never establishes
Initial eligibility.

## Data and frozen budgets

Three daily members were downloaded through the
[official record's member API](https://zenodo.org/api/records/17249078/files/2025-05.zip/container).
Each matched its official size and CRC; SHA-256 values are below. Their combined
size is 122,586,041 bytes. The complete monthly ZIP was not downloaded or
MD5-verified. This remains reference-labelled development data from the
[official CC-BY-4.0 corpus](https://zenodo.org/records/17249078), not synthetic data.

The protocol was saved before inspecting the later days. Sampling takes the
first eligible records per class in source-file order, capped at 200 for training
and 100 for each later partition. This is not a prevalence sample. Low pilot
support was declared in advance: five records per training class and two per
selection/calibration class. Those tiny minima enable a pipeline pilot; they
do not justify a release or a strong class-quality estimate.

| Class | Train: 1 May | Selection: 2 May | Calibration: 3 May |
| --- | ---: | ---: | ---: |
| YouTube | 200 | 100 | 100 |
| Spotify | 200 | 100 | 100 |
| Instagram | 200 | 100 | 100 |
| TikTok | 5 | 8 | 10 |
| Snapchat | 200 | 100 | 100 |
| WhatsApp | 200 | 100 | 100 |
| Messenger | 29 | 24 | 17 |
| Discord | 200 | 100 | 100 |
| Drive | 110 | 100 | 93 |
| Outlook | 46 | 81 | 29 |
| Total | 1,390 | 813 | 749 |

Partitions use the official daily member dates. Available original connection
IDs and destination identifiers are hashed for grouping; no group crosses
partitions. Client host identities are unavailable, so host independence is
not established. No identical packet-feature sequence crosses these three
partitions. All 2,952 selected rows were checked back against their original
Parquet rows: packet values, reference labels and group hashes matched exactly.

Input validation was added while the initial preparation process was running;
packet extraction and label functions were unchanged. The separate finalized-
source verification records this fact rather than claiming the running process
executed newly added validation. The two reserved final days, 8 and 9 May, were
not downloaded; `test.jsonl` is absent. Preparation refuses class dropping,
cross-partition connection reuse and changed source/audit hashes. Training fits
normalization only on its training partition, and policy only on calibration.

## Actual model evidence

Training source commit: `88b5983b5ea0555e915ed2330dd513836d03d3f0`.
All runs use seed 17, two CPU threads, the existing architecture and the existing
four prefix budgets. No augmentation, SupCon, hyperparameter search, local-log
fitting or threshold adjustment was performed.

| Run | Model | Fit time seconds | Selected epoch | Selection mean over 16 cases |
| --- | --- | ---: | ---: | ---: |
| `20261026-111626-fc56d0e5` | Two-epoch CE pilot | 51.25 | 2 | 0.12097 |
| `20261026-111720-9993a200` | Forest | 15.66 | — | 0.65586 |
| `20261026-111853-25db8dac` | Twenty-epoch CE | 356.71 | 20 | 0.52327 |

Fit times exclude some subsequent export/policy/report work and are not inference
latencies. The longer CE budget was declared after observing undertraining in
the two-epoch pilot, before replaying these candidates on local evidence.
The 20-epoch model's clean selection macro-F1 at 5/10/20/30 packets was
0.47971/0.63157/0.62946/0.60309. The forest's was
0.83464/0.86507/0.89686/0.91329. These estimates measure agreement with the
alternative reference labels on a small, biased sample. They are not CESNET22
final-test figures or trustworthy estimates of browser quality.

Saved local replay uses the same four attributed flows and 14 available prefix
points per service for every model. These are offline development predictions,
not new live events. The new candidates and B17 have different training data,
label provenance and calibrated policies; this comparison cannot isolate an
augmentation or loss effect.

| Model | YouTube top-1 correct / 14 | Accepted (wrong) | Instagram top-1 correct / 14 | Accepted (wrong) |
| --- | ---: | ---: | ---: | ---: |
| Existing B17 | 10 | 1 (0) | 0 | 4 (4) |
| New CE, 20 epochs | 3 | 1 (1) | 1 | 0 (0) |
| New forest | 0 | 4 (4) | 2 | 4 (4) |

Withholding every Instagram label is not a successful classifier. No candidate
earned promotion. One seed, correlated prefixes, very small class counts and
two local development sessions do not support model-selection or release claims.
The original one-time CESNET22 final report's checksum is unchanged.

## Additional Instagram socket check

The bounded reader now optionally retains all UDP connect, address, sent and
received event types for socket-mode diagnostics. It parses and hashes the
entire original 165 MB log; no origin, label, time or connection filter selects
retained events. It retained 269,405 events / 47,043,457 encoded bytes under the
original projection caps. The default attribution profile still omits sockets.

All four Instagram flows matched unique sockets. Within each direction, all
**41 sent and 61 received payload sizes matched in order**, with no missing
prefix packets. Merging directions using browser userspace clocks produced
19 direction-position and 29 size-position differences over 102 packet points.
Browser event times are not an on-wire ordering/timing reference. Replaying the
browser socket ordering with the unchanged B17 still ranked Instagram first
at zero of 14 points; its two accepted decisions were both wrong. This check
does not establish complete historical-exporter or wire-timing parity, and
changing to browser order is not an adopted inference repair.

## Artifacts and reproduction

All private evidence below is under `artifacts/local/quicext25-schema/` and
remains ignored. Bundles are complete, with saved preprocessing, labels,
weights, architecture, versions, policy and provenance, under
`experiments/quicext25-pilot/<run>/bundle/`.

| Artifact | SHA-256 |
| --- | --- |
| 1 May source Parquet | `22592795db66ca4b7d8fe5efbfee12612d03c74dcc52339538703822a1216631` |
| 2 May source Parquet | `1667c0230799231dee18851210f0b00b5fd9e9c011d03af1a94cbb92ea32c3bc` |
| 3 May source Parquet | `f0559a2c199325009101b51741ac41ab27cdc3dfda097c4293e5b638fded0147` |
| Prepared `manifest.json` | `a695170a106e8ba2f2a8891a5777b434c5329b244cfc13fae5027fdc7edf8a9c` |
| `label-rule-audit-v2.json` | `4718a7f0a5c2c7053976c6337e8dfdf53b1d6c51d5d3614828cece2de7817824` |
| CE20 `metadata.json` / artifact ID | `24304049ac571626d84c93ca41d7f789eea23f6670cc1c765af293dbfe76f540` |
| CE20 `weights.pt` | `e1d03bf9162be22c56dc2e83b680f9b5ec3d9b279c9225eb89fe210283482132` |
| Forest `metadata.json` / artifact ID | `fe533881f339f02760c28fb161e51ce07c755e345ea97924253838748cebeeed` |
| Forest `forest.json` | `1130087fb1778aed896e0ac2e39ddaadd4a4bb642b927f7a15dd46bc908bbabf` |
| `pilot-transfer-comparison.json` | `cd6650cb578961108bd7116101c31b15ba85c9ff57d9ece09b65fcd2378cac75` |
| `instagram-socket-parity.json` | `af5407453a5437d2668bcaa26d58f34346902cd8b89eb5093b6f74a9e7e0201c` |
| `pilot-result-summary.json` | `3c02d446d504f740c40aa71106f2eef9093e90ebd7608aca0e4b7ec22179419d` |

Run from `traffic_classification`, using fresh output paths:

```powershell
.venv/Scripts/python.exe -m pip install -e '.[dev,data,parquet]'
.venv/Scripts/python.exe scripts/audit_quicext_labels.py --archive C:/Users/shrey/Downloads/cesnet-quic22.zip --output artifacts/local/quicext25-audit-repeat.json
.venv/Scripts/python.exe scripts/prepare_quicext_pilot.py --protocol configs/quicext25-pilot.json --label-audit artifacts/local/quicext25-audit-repeat.json --downloads artifacts/local/quicext25-schema --output data/processed/quicext25-pilot-repeat
.venv/Scripts/netembed.exe train --data data/processed/quicext25-pilot-repeat --config configs/quicext25-ce20.json --output experiments/quicext25-repeat
```

The audit must be rerun if source byte hashes change. Existing downloads are
verified against their retained download metadata; incomplete files remain
explicit `.partial` files. The pilot forest config uses the protocol's
`pilot_training` values with `kind=forest` and the same seed. Actual flat configs
are also saved beside the local evidence. Use the emitted run's `bundle` with
`netembed evaluate --data ... --bundle ... --output ... --split selection`.

The local transfer report uses `scripts/compare_local_candidates.py` with its
explicit `--allow-different-training-data` flag, the existing YouTube/Instagram
capture and reference pairs, and these three bundle paths. Socket reproduction:

```powershell
.venv/Scripts/python.exe scripts/check_browser_receive_parity.py --stream-netlog --socket-mode --socket-replay-bundle experiments/full-real/20261024-151720-3532794c/bundle --evidence artifacts/local/capture-instagram-01.json --netlog artifacts/local/chrome-netlog-instagram-01.json --reference artifacts/local/reference-instagram-01.json --output artifacts/local/instagram-socket-repeat.json
.venv/Scripts/python.exe -m pytest -q
```

No final evaluation or default switch is part of these reproduction commands.
No experiment, data download or capture is left running after the reported work.

Final local verification: **163 Python tests passed**, including native offline
TShark checks and the Parquet fixture; no tests skipped. Ruff lint and formatting
passed for all 59 active Python files, and `pip check` passed. The one existing
Starlette/AnyIO deprecation warning remains. Hosted CI has not run on this
unpublished branch. UI code did not change in this stage; its earlier seven
tests and production build are separate evidence. The idle service still loads
the original B17 artifact with capture off.
