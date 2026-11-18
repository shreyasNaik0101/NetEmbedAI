# First genuine observation-window trial — 28 October 2026

The user deliberately started Wi-Fi capture with experimental windows and the
separate reference option enabled, then reported using YouTube in **normal
Chrome**, not a private window. Normal Chrome is valid for this functional
check. Pre-existing pooled connections can be skipped when their beginnings
are absent, but thirty-three eligible new QUIC flow windows were recorded.
The chosen site does not label every connection on the laptop.

The stopped session is `a7ea6358ab04493b9cc8a078d79f58c8`, interface 9,
prefix adapter `tshark-prefix-ns-v3`, window version
`quic-observation-windows-v1`, with the unchanged B17 artifact
`18c43fe12262b81d4a3001df150a278865f3908ddd3aab934822fc0c9e5750fb`.
The pre-capture intent fixed an engineering-only, unscored role and a
one-recording cap. It does not replace the frozen browser development cycle.

## Actual retained observations

| Observation horizon | Retained flows | Packet observations summed over flows | Largest single-flow count | Flows exceeding their model prefix |
| --- | ---: | ---: | ---: | ---: |
| First 1 second | 33 | 3,808 | 1,700 | 15 |
| First 3 seconds | 33 | 3,856 | 1,700 | 15 |

These are nested windows over the same connections: the rows must not be added
as independent traffic. Both horizons elapsed for all 33 retained windows.
No window flow is missing from the retained prefix inventory. The collector
therefore demonstrably continued beyond the model's thirty-packet cap during
genuine user-started capture. This is functional evidence, not classification
accuracy or proof that more packets carry a unique service identity.

All directional histogram counts equal the corresponding packet totals; means
match directional byte totals. Window counts/bytes include at least every
retained prefix observation within each horizon, with matching flow IDs and
first-packet timestamps. One-second histograms are the nested initial bins of
the three-second histograms. These are **internal consistency checks**, not an
independent on-wire exporter comparison or a guarantee that capture lost no packets.

There were **nineteen late packet revisions across three one-second windows**:
packets inside the event-time interval were parsed after an elapsed snapshot.
The final snapshots include them and preserve the revision counters. No such
revisions occurred in the three-second windows. No reordered observations were
recorded. An elapsed snapshot must therefore not be treated as immutable or as
proof of complete delivery; this limitation stays in the evidence.

Capture stopped at its two-minute duration limit, with zero recorded combined
viewer/inference queue drops, 31 coalesced checkpoints, no evidence eviction,
zero backlog and no reported process error. Ten idle flow-table entries were
evicted; that counter is distinct from losing retained evidence. 14,335 later
packet observations hit the model's prefix freeze. No TShark process remained
when checked after Stop.

All **86 saved B17 predictions reproduce exactly**, with zero score difference
and unchanged labels/status at two Torch threads. Capture-to-browser receipt
p50/p95 for these prediction events is **320.69/546.28 ms** over 86 receipts.
These measurements do not measure window-event receipt, browser paint time or
hard real-time bounds.

## What remains unverified

All 33 passive references are `protected_name_unverified`. This may include
ECH GREASE; it does not prove that all names were encrypted. No Chrome NetLog
was requested for this unscored test, so no independent per-flow service labels
exist here. Service/activity accuracy stays null. These rows are not used for
training, threshold fitting, calibration or final evaluation.

The screen's observation-event rendering has software tests, but this trial
does not record observation-event acknowledgements. Independent screen
inspection encountered **“Computer Use app approval timed out”**. Browser
display verification remains pending a user report or visual access; genuine
server collection must not be renamed independently verified live UI delivery.
No additional capture is needed merely to preserve these server-side findings.

The next model-evidence requirement is matched, independently labelled
longer-window development/evaluation data and its fixed feature/quality protocol.
This test cannot be retrospectively called a YouTube accuracy test or an
untouched final test. Existing prefix-only recordings cannot supply missing
later on-wire observations. No improved model or completed release follows.

## Artifacts and reproduction

Raw endpoint responses, intent and verification stay private under
`artifacts/local/window-validation/`. They were archived before any next Start;
different evidence is not overwritten. Files contain packet metadata and
session matching tokens, not application payloads or raw hostnames/addresses.

| `window-engineering-01-…` file | SHA-256 |
| --- | --- |
| `intent.json` | `2ba0be1ee96d5d76a890d0639ad9bdb1281323dfba2e62eeb4930662ffa05e26` |
| `capture.json` | `5a70265796dc489dc5ccbe2a10d6d704e8ec0c2594b29cb0dcc6a7ba7e39ecfa` |
| `windows.json` | `02edc545f22b729aac2feca71c8f0b2bf02037f0415c1968c0390d86436bb234` |
| `summary.json` | `8c08e3d084cc60ced410e4dcd8948ad41a8a9f6e1746074d6e594400c3915470` |
| `assessment.json` | `7fd449d062fbc4a72dc7c5953d7373cd9323269a9d6d7d27f4395edacff5edd4` |
| `status.json` | `1d8eed1709453e98568cb0309ee86641675b1f3dbda1e61ccb06a8d8fb0343ee` |
| `verification.json` | `b02176294bc5a63602869312e67e732df418e9bc37fba46803d490bb279efc34` |

From `traffic_classification`, use a new verification output filename:

```powershell
.venv/Scripts/python.exe scripts/validate_window_trial.py --output artifacts/local/window-validation/window-engineering-01-reverification.json
.venv/Scripts/python.exe -m pytest -q
.venv/Scripts/python.exe -m ruff check src/netembed scripts tests
.venv/Scripts/python.exe -m ruff format --check src/netembed scripts tests
```

The validator binds session, model, interface, versions, options, chronology and
histograms, rejects fixtures/replay and invalid counts, and replays the actual
source bundle without fitting. **256 Python tests passed**, with one existing
Starlette/AnyIO deprecation warning; Ruff lint/format passed for 87 active files.
No UI source changed in this archival step, so its preceding ten-test/build
checkpoint is retained rather than claimed as newly rerun. No test started
capture. The app remains stopped with B17 unchanged.
