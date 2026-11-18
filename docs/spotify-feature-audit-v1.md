# Spotify feature audit — 6 November 2026

A bounded training-only audit found differences in timing precision, payload-size distribution and direction alternation between the five verified local Spotify connections and historical Spotify training examples. It does not identify a single cause or establish a repaired classifier.

The frozen rule selected the first 30 stored records with at least ten packets per service per training date, across 31 October–6 November 2022. That gives 210 Spotify and 210 YouTube flows. The same rows are reused at each budget when long enough. This is deterministic per-day sampling, not random population sampling. Local inputs are exactly the five previously QC-eligible flows; views of one connection are not independent samples.

## Ten-packet measurements

The table shows medians across per-flow summaries. Timing gaps exclude the structural zero before the first packet.

| Per-flow measurement | Local Spotify (5) | Historical Spotify (210) | Historical YouTube (210) |
|---|---:|---:|---:|
| Prefix duration, ms | 63.78 | 53.00 | 34.00 |
| First payload, bytes | 1230 | 1250 | 1250 |
| Median payload, bytes | 1230 | 342.25 | 815.75 |
| Mean payload, bytes | 790.50 | 576.50 | 687.90 |
| Fraction of payloads at least 1200 bytes | 0.60 | 0.30 | 0.40 |
| Client-to-server packet fraction | 0.40 | 0.50 | 0.50 |
| Direction changes | 2 | 4 | 2 |
| Zero-gap fraction after first packet | 0.00 | 0.33 | 0.56 |
| Fractional-millisecond gap fraction | 1.00 | 0.00 | 0.00 |
| Median inter-arrival gap, ms | 0.120 | 3.00 | 0.00 |

All five local prefixes have exactly two direction changes. The sampled historical Spotify central 90% spans three to six changes; the local value is below that range. Four of five local median payload sizes remain inside the historical Spotify central 90%, so larger typical packets do not mean every local size pattern is unseen. Prefix durations and first-packet sizes remain within the historical Spotify central range.

The local timing values have submillisecond detail; historical stored gaps are whole milliseconds. This is a precision mismatch, not evidence that one side uses seconds or microseconds. It could matter to a model, but only a controlled sensitivity check can measure its effect. Earlier studies on other local services do not establish the answer for Spotify.

YouTube shares the median direction-change count and has larger typical payloads than historical Spotify in this sample. That is compatible with some model confusion, but no distance/classifier was fitted and no overall similarity ranking or causal explanation follows.

## Feature-contract inspection

The processed-data exporter directly validates the first three PPI channels. The shared schema declares milliseconds, direction signs (+1 client to server, -1 reverse) and UDP payload bytes. The capture adapter derives integer nanosecond timestamp differences divided by one million, removes the eight-byte UDP header from udp.length, and assigns signs from the observed Initial origin. All sampled first directions are +1; first gaps are zero. Existing per-flow browser checks remain part of the original diagnostic evidence.

This code/data inspection found no obvious declared unit conversion or direction reversal error. It is not new full wire/exporter parity proof, and it cannot rule out other capture/network/browser differences. No input was rounded, rescaled, reversed or otherwise changed for this audit. No model was called or fitted.

## Evidence and limits

Only train.jsonl and its manifest were opened under data/. An audit hook rejects selection, calibration, final-test, other local cohorts, unrelated experiments and network access. Training and diagnostic source hashes were checked. Independent JavaScript calculations verified 1,176 saved quantiles and 252 local feature values reconstructed from original packets (0.001 tolerance for float32 conversion).

The original seven dropped events and two excluded socket prefixes remain explicit quality limitations. This recording is exposed diagnostic/development data, not a held-out final test. No new capture, training, policy change or deployment occurred.

Private evidence root: experiments/spotify-feature-audit-v1

- Protocol SHA-256: a5f15932d8575f9f18d1510cb0d4c4c3ea5f22bff8c575d1415971e3ee8fa634
- Report SHA-256: 425bb894120ac6b9abbaa01551d73eef7b2b7c0091772a112d0a38a395f8eadd
- Per-flow features SHA-256: 27415e78b01285f268f5a9331ee0b9a8c823dbe6330310f5bfe2763ccb69b788
- Runner SHA-256: 60c56c87b767f4168a30daab6116eadb1b9fa51c163c4ed5c6e652013395bbaf

The private report saves all sampled IDs, per-date counts, 5/10/20/30-packet summaries and opened data paths. To reproduce with the local real training artifact and diagnostic files, copy audit.py and protocol.json to a new directory under experiments, then run the copied script from the project directory. It uses its own directory for outputs and refuses overwrite. The original result stays intact.

The next bounded diagnosis would compare unchanged versus fixed timing-precision transformations on these same saved inputs and frozen models. That can test timing sensitivity without another recording; it must not be called a deployment repair or used to tune on final-test data. Representative Spotify training data could later be investigated under a separate protocol, with no improvement guarantee.

## Completed timing check

The [fixed timing sensitivity comparison](spotify-timing-sensitivity-v1.md) improves the older forest raw ten-packet ranking from 1/5 to 4/5 under each integer-timing variant, but produces no correct accepted Spotify labels and does not recover later prefixes. B17 and the current forest remain 0/5 raw at ten packets. Timing matters for some decisions but is not a sufficient repair.
