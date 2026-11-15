# Spotify diagnostic — 6 November 2026

The frozen forest fails on the browser-verified Spotify connections in this one exploratory visit. Do not advertise locally reliable Spotify classification.

The user deliberately started and stopped capture on Wi-Fi with the unchanged public-policy forest, normal fresh Chrome and a stripped NetLog. Seven connections mapped to Spotify under the existing matcher; two failed missing-socket-prefix checks. Five remained for diagnosis. Other ambiguous, unmapped and outside-supported traffic stays in the inventory rather than being assigned Spotify from activity.

| Prefix | Eligible | Actual emitted | Accepted YouTube (wrong) | Refused | Raw top choice YouTube |
|---|---:|---:|---:|---:|---:|
| 5 | 5 | 5 | 0 | 5 | 5 |
| 10 | 5 | 5 | 1 | 4 | 5 |
| 20 | 5 | 5 | 1 | 4 | 5 |
| 30 | 3 | 3 | 0 | 3 | 3 |

The five-packet decisions correctly abstain under the minimum-ten-packet policy, but raw choices are still wrong. The ten- and twenty-packet wrong accepts show that confidence is not a correctness guarantee. Lowering the threshold cannot repair the raw rankings.

All 121 saved source predictions reproduced exactly, with zero changed labels or alternative-score difference. An independent JavaScript recount confirmed the primary counts. The capture reported seven drops (a shared queue/event counter, not a measured wire-packet loss rate), so this is explicitly not a clean operational validation. Retained evidence had no eviction. Two excluded connections remain excluded. No missing checkpoint was replaced by replay.

This is one exploratory diagnostic visit, not a final-test accuracy estimate. It establishes a concrete failure on five independently attributed connections; it does not explain the cause or measure every Spotify component. The existing matcher only covers its published service map; no domains were added after seeing this outcome.

Protocol SHA-256: 6d0515c12ec8a586cb1a2fe39f3d775f7c2532d7ec155f0d22227a70d9fb7991
Report SHA-256: a3a2832c1d462b460d102b8009f2af4bf95ba199759f68d36ed0a40c56e04299
Private evidence root: artifacts/local/spotify-diagnostic-v1
Report: spotify-01-report.json
Artifact: 9878d0818370ede3e9897a9cc654b4ddc0afcd87d41b2d7134ccaf52592b528a

No model, normalization or policy was changed. This slot is complete; no replacement recording is requested. The next useful work is an offline failure comparison using these saved inputs and existing frozen models. Any later fitting must treat this exposed recording as development evidence and reserve genuinely new data for evaluation. Improvement is not guaranteed.

## Completed offline comparison

The [three-model comparison](spotify-frozen-comparison-v1.md) found no model correctly accepts Spotify at any available prefix. At ten packets B17 and the current forest both have 0/5 correct raw choices; the older forest has 1/5. Switching artifacts alone does not repair this recording. No model was promoted or fitted.
