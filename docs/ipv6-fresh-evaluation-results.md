# Frozen forests on four new recording visits

The comparison completed on **6 November 2026** after all four declared,
user-started visits were archived. Both models, preprocessing, eligibility,
primary metric and descriptive rules were frozen before collection. No model
was fitted, tuned or activated using these visits.

At ten packets the added-real-data forest gets **22/22** retained local flows
right, versus **7/22** for the matched original forest. The predeclared primary
score gives each target visit equal weight within its service, then gives each
service equal weight: **1.000000 versus 0.462121**. All three descriptive checks
pass. This is a useful prospective result for the observed YouTube/Instagram
hotspot setting; it is not a universal 100% accuracy claim.

## What was measured

The fixed declaration is `configs/ipv6-frozen-evaluation-v1.json`, canonical
SHA-256 `dd0723d1dbefc777a586133a71de74a8f2478b2f427ee5d3ff349f02a913e616`.
The [collection protocol](ipv6-fresh-evaluation.md) preserves the raw acquisition
checks, date schedule and provenance. The [training pilot](ipv6-realdata-pilot.md)
describes the intervention: retain all 43 original local training flows, add
19 real IPv6 flows, keep the 14,000 public flows, forest settings, seed17 and
public/local weight mass unchanged. No augmentation or new model family.

The new assessment has four distinct browser/capture sessions over 5–6 November:
two visits per target service. All 22 eligible connections are IPv6. There are
15 target-visit YouTube flows, six target-visit Instagram flows, and one incidental
YouTube flow in an Instagram visit. That incidental flow is retained as secondary
evidence; it does not count as a target YouTube visit. References come from the
separately recorded Chrome log and socket matching, not either model's guesses.
Unmapped, ambiguous and unsupported reference inventories remain preserved.

Target-only primary results at ten packets:

| Target visit | Control correct / eligible | Added real IPv6 correct / eligible |
| --- | ---: | ---: |
| YouTube, 5 November | 0/4 | 4/4 |
| Instagram, 5 November | 2/3 | 3/3 |
| Instagram, 6 November | 3/3 | 3/3 |
| YouTube, 6 November | 2/11 | 11/11 |

Control target mean-visit recall is 0.090909 for YouTube and 0.833333 for
Instagram. Candidate recall is 1.0 for each. Their equal-class averages are
0.462121 and 1.0, a paired difference of **0.537879**. The minimum candidate
class recall is 0.80 and both primary/per-class nonregression checks pass.
These are descriptive rules, not statistical noninferiority tests.

All retained local flows, including the incidental YouTube connection:

| Actual prefix budget | Control correct / eligible | Added real IPv6 correct / eligible |
| --- | ---: | ---: |
| 5 | 8/22 | 22/22 |
| 10 | 7/22 | 22/22 |
| 20 | 5/20 | 20/20 |
| 30 | 8/17 | 17/17 |

Only flows that actually reached the requested budget appear in that row.
There are 81 distinct flow/prefix cases per model, not 81 independent connections.
The added-data forest gets all 81 top guesses right in this cohort. The absence
of IPv4 observations is reported as unavailable, never as zero error.

## Verification and preserved boundaries

- Every archived source file was rehashed. Plan, model identities and weights
  match the precollection declaration; sessions, roles, row/family inventories,
  Chrome lifetimes and two-date schedule were rechecked.
- The source B17 capture path reproduces all **564** saved live vectors exactly.
  This verifies acquisition and saved source inference, not new-forest live UI
  performance. The forest comparison uses the same measured packet arrays.
- A separate offline audit replays all **162 forest probability vectors** with
  maximum difference **0.0** and independently recounts all **eight** confusion
  matrices, target-visit/class averages, family cells and three decision rules.
  Training, earlier outcome records and network access are blocked during replay.
  It uses the same Predictor implementation, with independent metric arithmetic;
  it is not a second inference implementation or another cohort.
- Both forest policies remain `fitted:false`. Every accepted label is withheld.
  Raw top-class correctness does not establish a calibrated correctness
  probability or a validated acceptance threshold. B17 remains the visible app
  model; neither forest is automatically activated.
- The 424,276,064-byte second Instagram NetLog exceeded the normal 256 MiB source
  limit before QC. The existing expanded offline profile processed the **same**
  bound capture: 1 GiB/8M source events, 256 MiB/2M retained events. Its source hash
  was bound before processing; no event types, eligibility rules or quality
  thresholds changed. No replacement capture was collected.

The outcome is `promising_fresh_screen`. The four-visit scope is complete; no
extra recordings, seeds, treatments or retraining follow automatically. Further
confidence calibration and replacement-model live integration/quality/latency
evidence remain separate work. These evaluation visits keep their evaluation
role; they are not silently converted to confidence-calibration data.

## Limits and practical meaning

There are only four visits, two services, one laptop/browser setup and one
user-declared mobile hotspot. Flows and prefixes within a visit are correlated.
There is no new-campus, mixed-application, unsupported-protocol, open-world or
general reliability result here. The intervention adds real sessions and changes
within-class sample/forest bootstrap composition; it does not isolate IP family
as the sole cause. No family, endpoint, domain or process identity is a predictor
feature. Other public service quality is described by the separate pilot's
retention check, not by this two-service local cohort.

The previous [CPU measurement](ipv6-realdata-pilot.md#actual-outcome) on this
unchanged candidate was about 3.08 ms p50 / 4.10 ms p95 for ten-packet batch-one
inference. It excludes capture and UI transport. This comparison does not add
a candidate live-event latency measurement or hard real-time guarantee.

This is concrete progress: the added-data model repaired a severe failure on
new, separately collected visits without changing the model settings after
seeing their outcomes. It supports advancing this simple forest candidate to
the next evidence stage, while preserving the earlier failures and limitations.

## Artifacts and reproduction

All private outputs are under `artifacts/local/ipv6-frozen-evaluation-v1/`:
`comparison.json`, `paired-predictions.json`, `independent-audit.json`, the
write-once `audit-comparison.py`, four archives/completion receipts and
`collection-completion.json`. Recordings are not committed or uploaded.

| Evidence | SHA-256 |
| --- | --- |
| Comparison | `261a806d2c4e341c1a5c33abcc7d38beeb0e01a2dff70a2e37eede81fbe125c2` |
| Paired predictions | `ca74126b134bad0672da91974497f74a917ad1d7cbdd1b5162aadbb400d498e4` |
| Independent audit | `7ceec32d191a7b7d1223c2acd72686cb6c6a4352f4823566934e08cf8fdc8046` |
| Audit source | `9b9cba96b6f389fba7fc641a2b6269f3952dc31255d89b60bb2d55dde2ba67db` |
| Complete collection before scoring | `04d90b49146b927d47e20fe7eab42bb266f653d9f71b74fc6dedfa24dfc1fde3` |
| Final evaluation completion | `07df90224b3d02c52a61020ad4b04a410a18d5ba92cc60d4bdb295fbac891245` |

The candidate inference bundle remains
`experiments/ipv6-realdata-pilot-v1/plus-real-ipv6/bundle/`, artifact identity
`0b87d388d91fdeb4c6c87fc8a76ce8a718a02415c69c9346e1d222154b5b0473`.
Its forest checksum remains
`78efcee31f1ce49a882283b8d4a585bfbc9c0980e40ace68587a98b811d5eecb`.
The complete uncalibrated ZIP remains
`artifacts/local/NetEmbedAI-ipv6-pilot-seed17-UNCALIBRATED.zip`, SHA-256
`5ae0ce751fb7749b980d3d8755485471ba1bae7f7ee8b43063d0e3e559d5e90c`.
No trained bundle was rewritten to incorporate evaluation results.

The actual scoring and audit commands, already completed, were:

```powershell
.venv/Scripts/python.exe scripts/paired_capture.py --plan configs/ipv6-frozen-evaluation-v1.json --root artifacts/local/ipv6-frozen-evaluation-v1 score
.venv/Scripts/python.exe artifacts/local/ipv6-frozen-evaluation-v1/audit-comparison.py
```

They preserve existing outputs. For a fresh reproduction, use the pinned
environment and byte-identical private archives in a separate collection root,
without copied comparison/prediction outputs, then score that root. Creation
times may differ. Inspect the saved reports instead of overwriting this result.
Last full software checkpoint:438 Python tests,132-file lint/format pass; this
evaluation changes no production code or UI and is not another software test.

The final receipt additionally verifies the scoring source hash, unchanged ZIP,
stopped capture and B17 identity. Command execution was recovered using the
[explicit cmd/native-PowerShell route](windows-command-runner.md), allowing the
agent to run the actual comparison and audit without another manual user command.
