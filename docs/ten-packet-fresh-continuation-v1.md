# Three-service verification after delivery repair

The frozen protocol is `configs/ten-packet-fresh-continuation-v1.json`, SHA-256
`c59b34bc3073ce68a0e5ee28d0a5eb069a2c56e898ab65eee72e5f50a1e6a9ca`.
It was declared before its first capture on 9 November 2026.

This is a separate technical continuation of the interrupted
`ten-packet-fresh-v1` scope. That scope remains blocked. The new protocol binds
its integrity review and the subsequent successful delivery check by checksum.
Their packet data is excluded from scoring. Model weights, minimum support and
quality gates have not been relaxed.

The user deliberately starts one visit each for YouTube, Instagram and Spotify,
in that order. Each visit uses a freshly opened normal Chrome session, stripped
NetLog, Wi-Fi interface 9 on the user-declared phone hotspot, reference checking
enabled and longer observation windows disabled. The user plays or browses the
declared service for 60 seconds. Capture is capped at 120 seconds. Chrome stays
open through archival so process lifetimes can be verified.

At least three independently browser-mapped and socket-prefix-verified target
connections must reach ten packets in each visit. Insufficient support ends the
scope; no replacement visits or post-result changes are permitted. Capture
history is bound at preparation: multiple Starts or loss of intervening session
history block grading and preserve diagnostic evidence. Eviction of known older
sessions is distinguished from missing new sessions.

Both frozen models are compared on identical first-ten-packet inputs only after
all three usable visits. The candidate has no fitted confidence policy, so the
app intentionally withholds accepted labels and displays confidence-check
pending. Raw guesses, actual native predictions and operational delivery are
checked separately. These recordings cannot fit weights or confidence thresholds.
One visit per service on one hotspot cannot establish broad generalization.

From `traffic_classification`, use the same prefix for each command:

```powershell
.\.venv\Scripts\python.exe scripts/ten_packet_fresh.py --plan configs/ten-packet-fresh-continuation-v1.json --root artifacts/local/ten-packet-fresh-continuation-v1 status
```

Replace `status` with `prepare ten-cont-yt-01`, `archive ten-cont-yt-01`,
and the corresponding `ten-cont-ig-01` / `ten-cont-sp-01` commands as each
visit becomes eligible. Use `score` only after all three archives are usable.
Preparation and archival do not start capture. Keep stopped browser logs and
capture exports private under the local artifact root.

## Observed result, 9 November 2026

All three declared single-attempt visits were archived as usable. Scoring ran
once after archival and produced `comparison.json` and `predictions.json` under
`artifacts/local/ten-packet-fresh-continuation-v1`. No weights or confidence
policy were fitted on these visits.

| Target visit | Eligible target connections | Candidate raw correct | Control raw correct | Actual native ten-packet guesses correct |
| --- | ---: | ---: | ---: | ---: |
| YouTube | 7 | 7 | 7 | 7 |
| Instagram | 4 | 4 | 4 | 4 |
| Spotify | 5 | 5 | 0 | 5 |

All 16 eligible target connections had actual native ten-packet prediction
events; replay was not used to fill missing live predictions. An incidental
YouTube connection in the Spotify visit is outside this primary target table.
Two mapped connections in that visit were excluded for missing socket prefixes.
Ambiguous, unmapped and unsupported references remain in the recorded inventory.

The frozen scorer returned `small_fresh_raw_and_delivery_pass`. All 562 tracked
prediction events had browser receipt samples, with zero reported event drops
and no pending or evicted receipt tracking. Across each full visit, median
capture-to-browser-receipt latency was approximately 227 ms (YouTube), 290 ms
(Instagram) and 157 ms (Spotify); corresponding p95 values were 509, 1015 and
498 ms. These samples include short no-score and later repeated-prefix events;
they are not page-paint latency or a timing guarantee.

Important operational limitation: Instagram stopped on viewer heartbeat expiry.
YouTube stopped at the duration cap and Spotify was stopped by the user.
The frozen operational screen checks drops, retained evidence, receipt samples
and native replay; it does not reject heartbeat expiry. Its passing field must
therefore not be presented as evidence of uninterrupted viewer reliability.
The raw model result is encouraging, but this timeout remains unresolved.

This is 16 correlated connections from three visits on one user-declared phone
hotspot, not a broad accuracy estimate or independent 16-session study. All
accepted labels remain withheld because the confidence policy is unfitted.
These verification visits must remain excluded from later calibration. Next
engineering work should address the viewer timeout; any later confidence-policy
calibration and final evaluation need separately declared roles and new data.

The prediction file SHA-256 is
`56161987f610b794431d0ddb0760187307c578e9985c72b16fbd50a4a6f72720`.
The comparison file SHA-256 is
`55ca82402a6204bc6bcf406121907e8f1decc4be1f4a4aa5a3fdfef9b1ab47a9`.
Archive and model identities are recorded in `comparison.json`; each archive
binds its original capture, browser log, QC and audit files by checksum.
