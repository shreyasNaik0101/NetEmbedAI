# Instagram diagnostic trial — 26 October 2026

Follow-up: the [newer-data pilot and socket check](quicext25-pilot.md) now verify
the 41 sent payload sizes as well as the 61 received sizes, within direction.
Browser-order replay and newly trained candidates still failed to establish a
repair. The receive-only limitations below describe the original check.

The real capture worked, but the model failed this Instagram check. Four
independently attributed Instagram connections produced eight arriving model
decisions: three accepted labels, all wrong, and five withheld decisions. This
is evidence against claiming reliable local classification. No model, threshold
or normalizer was changed to conceal it. No further identical test is needed now.

## Capture and automatic stop

The user deliberately started Wi-Fi capture and Chrome NetLog recording, used
Instagram, then saved and stopped. Session
`93f3c75b28b34e96864b871051ba43a3` used adapter `tshark-prefix-ns-v2`
and the frozen augmented cross-entropy TCN, seed 17 (B17). Its artifact ID is
`18c43fe12262b81d4a3001df150a278865f3908ddd3aab934822fc0c9e5750fb`.

The saved stop reason was `duration or viewer lease expired`. Capture has a
120-second duration limit and a 10-second disconnected-viewer guard; the old
combined reason cannot distinguish which ended this session. TShark's
`78060 packets captured` line is normal shutdown output, although the old status
mistakenly displayed it as error detail. The next version filters that statistics
line and records the two guard reasons separately. Automatic stop does not erase
the retained evidence.

There were 31 retained flow windows: four Instagram references, 13 ambiguous,
five outside the supported set, eight unmatched and one unmapped. All four
Instagram references had 10–15 distinct received-packet anchors. Protected-name
refusals from passive inspection were preserved; independent browser attribution
used origin, exact connection tokens, received sizes and timing. Origins and
addresses never entered the predictor.

## Actual predictions and latency

The three accepted live errors were Facebook Messenger at score 0.8758 and
YouTube at 0.8411 and 0.9252. A score is not a probability that a label is correct.
All 71 saved predictions across the full retained inventory reproduced exactly
with the unchanged bundle: maximum alternative-score difference zero, no changed
decision labels. This rules out a live-versus-replay inference discrepancy on
these saved inputs; it does not establish correct input semantics in every case.

Offline replay fills checkpoints omitted by bounded live coalescing. On the
four Instagram references it gives 14 available 5/10/20/30-packet points, zero
Instagram top-ranked outputs, four accepted errors and ten withheld decisions.
Those additional outputs are replay evidence, not arriving live decisions.

| Measured stage, 71 events | p50 ms | p95 ms |
| --- | ---: | ---: |
| Capture to browser receipt | 271.04 | 559.81 |
| Capture to event | 261.44 | 555.37 |
| Prediction pipeline | 14.59 | 47.22 |
| Inference queue | 1.40 | 47.94 |

These are host/session observations, not paint time or a hard real-time bound.
The combined queue/pending-work drop counter was 12, with 35 coalesced updates,
zero evidence evictions and 14 active-flow expiries. The 77,020 post-prefix-cap
packets were intentionally ignored after windows froze. These counters do not
measure kernel packet loss or imply that exactly 12 network packets were lost.

All 61 retained received payload sizes on the mapped flows matched the browser
receive sequence, with zero missing records or size differences. Absolute clock
differences were p50 0.6631 ms, p95 1.3630 ms, maximum 2.8650 ms. The 41 sent
packets were not compared by this receive-only check. This is not full
bidirectional wire/exporter parity. None of the four flows contained a payload
larger than 1,250 bytes, so oversized datagrams do not explain these errors.

## Existing alternatives did not fix it

The same-data B17, plain cross-entropy A17 and forest17 artifacts were tested on
identical saved prefixes. Each keeps its original independently fitted policy.

| Candidate | YouTube top-1 correct / 14 | YouTube accepted (wrong) | Instagram top-1 correct / 14 | Instagram accepted (wrong) |
| --- | ---: | ---: | ---: | ---: |
| B17, threshold 0.67 | 10 | 1 (0) | 0 | 4 (4) |
| A17, threshold 0.64 | 9 | 3 (0) | 1 | 4 (4) |
| Forest17, threshold 0 | 9 | 14 (5) | 0 | 14 (14) |

Coverage differences cannot isolate augmentation's effect because policies
differ. These are two development sessions, four attributed flows per service
and correlated prefix decisions. The earlier YouTube session also predates the
Instagram adapter version; pooling them would not be a final study of one
adapter. None of these alternatives earned promotion. Timing-quantization
diagnostics likewise found no reliable repair.

A training-only prefix audit found class-dependent initial payload-size
distributions, while all eight mapped local YouTube/Instagram flows started at
1,250 bytes. This is a possible collection/client-context association, not proof
of causality or a justification for mapping a byte count directly to a service.
Selection, calibration and final-test records were not opened for that audit.

## Engineering changes and remaining gate

The 165 MB Chrome log exceeded the default 64 MiB JSON limit. An explicit
`attribute-netlog --stream-netlog` option now reads Chrome's line-oriented export
with bounded raw size, line size, event count and retained-reference size. It
keeps all relevant QUIC session, receive and successful-migration events by
event type, without selecting an origin, time range or prediction. The actual
913,145 source events became 125,765 retained events (24,439,690 encoded bytes).
Reprocessing the earlier YouTube log with this reader produced an identical
reference report apart from reader metadata. UDP socket-view checks require
the full reader because the projection deliberately omits socket records.

Forest JSON loading now decodes one numeric tree at a time rather than building
the entire nested JSON object in memory. File identity and prediction arithmetic
remain unchanged. Regression tests include chunk boundaries and malformed data.

The flow idle timeout was corrected from 30 to 65 seconds to match the
[CESNET collection description](https://pmc.ncbi.nlm.nih.gov/articles/PMC9851865/).
Adapter `tshark-prefix-ns-v3` records this prospective grouping change; replaying
all 31 saved Instagram windows under the corrected rule leaves their metadata
unchanged. This correction does not repair these classification errors. Fresh
real-live validation of v3 remains pending; this v2 session is not relabeled.

Verification after these changes: **137 Python tests, seven UI tests, production
UI build, Ruff lint/format and UI formatting passed locally**. This validates
software contracts, not local model quality. Hosted CI remains unrun on this
unpublished branch. The frozen CESNET default and held-out results remain intact.

The open release gate is reliable local service classification. Further work
needs independently attributed current development data and separate held-out
sessions, followed by a frozen adaptation and evaluation protocol. Downloaded
phone recordings with unknown provenance remain excluded. No retraining,
dataset download or automatic capture was started during this investigation.

## Local evidence and reproduction

These private files remain ignored under `artifacts/local/`; browser logs can
contain browsing metadata and are not committed. SHA-256 values:

| File | SHA-256 |
| --- | --- |
| `capture-instagram-01.json` | `9dcb377febd38ac5af6f1d20bb5ec385eb6bfd2ab825cae02b68181b0ba0af1f` |
| `chrome-netlog-instagram-01.json` | `79fa3611cdb1ed050d161630d9ccb50b9e3ed2ee424ce440fed8a929a6f6ba87` |
| `reference-instagram-01.json` | `355dd5ec124eb53d0feed0af7a5ba56fe25d6e746c5e54fee501cdb6d78a6c87` |
| `timing-instagram-01.json` | `3ef3439b4b75f55e49ccdf0a2cfcc26b3d9270ff77fa573c2a4bbe6f4a3da935` |
| `audit-instagram-01.json` | `de342c3a54f44b5523ab4828e1e001a3a31b06fa78b64e4dacb34314df1dda7d` |
| `browser-receive-parity-instagram-01.json` | `2a24655ba9ae4234e230c357c5508246565a8a793849eb8eb2cf31e248b616f4` |
| `timing-model-diagnostic-instagram-01.json` | `f3ed228b0fb521c5f15ee4635f41dedad219e18a3fcae513afe08cc3fbe11bea` |
| `local-candidate-comparison-01-v2.json` | `23b0f6b5821253d470b1a85d31f2347743b9716222ac5c5923290db731cf169d` |
| `training-prefix-eligibility-audit.json` | `907d64f921315eadb70e1e1986f3861e67041a0422a8cb5941992c595c5f7b24` |

Run from `traffic_classification` in PowerShell, choosing new output paths:

```powershell
.venv/Scripts/netembed.exe attribute-netlog --stream-netlog --evidence artifacts/local/capture-instagram-01.json --netlog artifacts/local/chrome-netlog-instagram-01.json --output artifacts/local/reference-instagram-repeat.json
.venv/Scripts/python.exe scripts/audit_browser_trial.py --evidence artifacts/local/capture-instagram-01.json --reference artifacts/local/reference-instagram-01.json --bundle experiments/full-real/20261024-151720-3532794c/bundle --output artifacts/local/audit-instagram-repeat.json
.venv/Scripts/python.exe scripts/compare_local_candidates.py --trial youtube artifacts/local/capture-youtube-01.json artifacts/local/reference-youtube-01.json --trial instagram artifacts/local/capture-instagram-01.json artifacts/local/reference-instagram-01.json --bundle B17 experiments/full-real/20261024-151720-3532794c/bundle --bundle A17 experiments/full-real/20261024-132801-9bc6963a/bundle --bundle forest17 experiments/full-real/20261024-125543-76c2fadb/bundle --output artifacts/local/comparison-repeat.json
```

Commands refuse existing outputs. They do not start capture, fit models or
access the final-test data. A fresh checkout needs the separately retained
private inputs and real bundles to reproduce this local trial; software tests
alone cannot recreate it.
