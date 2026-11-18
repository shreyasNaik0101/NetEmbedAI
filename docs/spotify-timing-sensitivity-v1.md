# Spotify timing sensitivity — 6 November 2026

A fixed offline comparison found that integer timing helps the older local forest rank Spotify at ten packets, but does not provide a reliable accepted Spotify classifier. B17 and the current demo forest do not recover at that prefix.

## Fixed comparison

Exactly the same five previously verified Spotify connections, three frozen models and 5/10/20/30-packet budgets were evaluated with four predefined variants:

- Unchanged observed gaps.
- Floor each inter-arrival gap to whole milliseconds.
- Round each gap to the nearest millisecond (ties to even).
- Floor reconstructed absolute packet timestamps, then difference them.

The last variant reconstructs timestamps from saved metadata and float32 gaps. It is an explicit sensitivity approximation, not proof of the historical exporter's exact quantization. No size, direction, length, weight, normalizer or acceptance policy changed. No training, calibration, selection, final-test data or network was opened.

## Actual results

Correct raw top choices at ten packets (five available flows):

| Model | Unchanged | Floor gap | Nearest gap | Floor reconstructed timestamps |
|---|---:|---:|---:|---:|
| B17 TCN | 0/5 | 0/5 | 0/5 | 0/5 |
| Older local forest | 1/5 | 4/5 | 4/5 | 4/5 |
| Current demo forest | 0/5 | 0/5 | 0/5 | 0/5 |

None correctly accepted a Spotify label at any tested prefix or variant. The older forest's acceptance policy is unfitted and deliberately refuses all cases; its raw ranking improvement is not accepted accuracy. At five packets its raw correctness improves from 1/5 to 2/5, but at twenty packets remains 0/5 and at thirty remains 0/3 under all variants. The current forest improves from 0/5 to 1/5 raw at twenty packets; all those cases remain refused. Its one wrong ten-packet acceptance disappears under each transformed variant, but without a correct replacement label. B17 still produces wrong accepted labels at later prefixes, and the reconstructed-timestamp variant additionally causes one at five packets.

Timing representation therefore affects some decisions on these inputs. It is not sufficient to repair Spotify, and improvement depends on model and prefix. The agreement among three variants is not three independent successful experiments; they share the same five connections. No variant/model is selected or activated from this diagnostic.

## Verification

There are 18 eligible flow/prefix cases, four variants and three models: 72 transformed input views and 216 model outputs. All 54 unchanged model cases match the preceding frozen comparison. The original current-forest live outputs were already bound to that comparison. Each input passes schema checks, preserves sizes/directions/length and gives identical results whether transforming just the prefix or the full flow then slicing. The latter check rules out future packets affecting the prefix transformation.

Three existing timing-transform unit tests pass. An independent JavaScript audit reconstructs all 72 timing vectors from original saved packets and recounts all 48 model/variant/budget summaries. Full probability vectors, policies, model identities, transformed gaps, runtime versions and checksums are saved privately. Production application code was not changed.

Original quality warnings remain: one exploratory visit, five QC-eligible connections, seven reported dropped events and two excluded socket prefixes. This is exposed development/diagnostic data, not final evaluation or fresh live validation.

Private root: experiments/spotify-timing-sensitivity-v1

- Protocol SHA-256: 309d72dae70311b6f293c67cce884a15b207b3878d7c7d669154d27335503d6e
- Report SHA-256: 68e0781e49f2861fe5a2272e0dacedf8b340bc44c6ca047c91411484a12e875e
- Predictions SHA-256: 6614233d9c6fcc33fbcc6901047a5b6c96650506e175ada5e6077bc882c4d4d3
- Runner SHA-256: c5b2871756b0e37e62b81ac5f09b78912aa2794fe81371ba1d2d785dc35a4287

To reproduce, copy compare.py and protocol.json into a new directory under experiments and run the copied script from the project root using the local virtual environment. It uses its own directory for outputs, refuses overwrite and needs the legitimate three frozen bundles, diagnostic input files and preceding frozen predictions. Benchmark data is not required.

The result narrows the next step: any further Spotify repair should evaluate timing compatibility alongside representative training data and public/per-service retention checks, rather than lower a threshold or replace the live model based on these five exposed examples. This scope ends without another recording, training run or deployment. Improvement remains unproven.

## Completed matched repair study

The [two-fit timing repair](spotify-timing-repair-v1.md) was rejected: consistent nearest-ms training/inference left Spotify at 0/5 at ten and twenty packets and 0/3 at thirty, while regressing local YouTube/Instagram and public Messenger retention. No candidate was activated. The earlier older-forest sensitivity gain did not establish a general repair.
