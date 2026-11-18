# Spotify weighting study

This separately authorized offline follow-up preserves the failed six-visit study. It uses the same public 14,000 and local 79 training flows (36 YouTube, 26 Instagram, 17 Spotify). No development example becomes training. All three Spotify training sessions remain distinct from the four-flow Spotify development session. The original five-flow diagnosis, casual captures, calibration/final scopes and other recordings are excluded.

The fixed protocol is configs/spotify-weight-study-v1.json, canonical SHA-256 b2bf81f86cdd9d4247eee771c695da8b482c6df483553130fc76131d87ecb6fc. Three new fits only: Spotify gets 1%, 2.5% or 5% of total training sample weight. Public weight stays 75%; the remaining 24%, 22.5% or 20% is split equally between YouTube and Instagram. Within each class, weight is divided equally over its flow/prefix examples. This replaces the previous candidate's 8.333% Spotify weight. Seed 17, two CPU threads, 32 trees, depth 12, minimum leaf 2, original summary-v1, saved normalizer and budgets 5/10/20/30 remain fixed. No augmentation, new architecture, extra seed or timing change.

The existing control is replayed and must reproduce all earlier development metrics. The exact prior training manifest, failed decision and training-stage checksums are bound before fitting. Each portable export is checked against sklearn probabilities on fixed public/local probes. Full probabilities, row IDs, configurations, source hashes, weights, timings and gates are saved under experiments/spotify-weight-study-v1. An offline access guard blocks calibration, final and unrelated private cohorts. Outputs are write-once; execution failures are preserved.

Development reuses the exposed four-flow Spotify visit, original seventeen-flow YT/IG selection cohort and first fifty public selection flows/class. Apply all six previous gates without relaxation: Spotify recall at least 0.60 at 10/20/30 and at least one additional correct ten-packet case; no existing local mean macro-F1 or per-class/per-prefix recall loss; at most 0.02 public macro-F1 loss per prefix and 0.05 recall loss for every public class/prefix. Rank eligible candidates by minimum Spotify recall at 10/20/30, then ten-packet correct count, then lowest Spotify training weight. No eligible candidate means stop without expanding the grid.

This is adaptive model development on reused selection data, not fresh evaluation. Even a passing candidate remains uncalibrated and requires a separate frozen fresh verification/calibration protocol before any live use. No capture, calibration, activation or default promotion occurs here. The former failure remains failed, and its unused calibration/final slots are not reopened by this study.

Run from traffic_classification:

```powershell
.\.venv\Scripts\python.exe scripts/study_spotify_weights.py
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m ruff check src scripts tests
.\.venv\Scripts\python.exe -m ruff format --check src scripts tests
```

Windows sklearn worker pipes require normal local process access; no administrator settings or paid compute are involved. The CLI has no configurable grid or seed override. Inference reads only exported model artifacts, never these training datasets.

## Completed result: no eligible candidate

Exactly three fits completed on 8 November 2026. The control reproduced the prior development metrics exactly. Shared feature generation produced 56,316 examples with 34 features in 117.103 seconds. Candidate fit/export/assessment took 18.084, 16.604 and 16.565 seconds respectively; each portable export agreed with sklearn to at most 9.9921e-16 on the fixed probes. These timings are experiment execution costs, not inference or live event latency.

Raw Spotify top-choice counts on the same four-flow development session:

| Total Spotify training weight | 5 packets | 10 packets | 20 packets | 30 packets |
|---|---:|---:|---:|---:|
| Control, no local Spotify | 0/4 | 0/4 | 0/4 | 0/4 |
| 1% | 1/4 | 4/4 | 3/4 | 4/4 |
| 2.5% | 3/4 | 4/4 | 3/4 | 4/4 |
| 5% | 4/4 | 4/4 | 4/4 | 4/4 |

Existing local YouTube/Instagram retention counts:

| Total Spotify training weight | 5 packets | 10 packets | 20 packets | 30 packets | Mean macro-F1 |
|---|---:|---:|---:|---:|---:|
| Control | 15/17 | 17/17 | 15/15 | 14/14 | 0.983806 |
| 1% | 15/17 | 17/17 | 13/15 | 13/14 | 0.956643 |
| 2.5% | 14/17 | 16/17 | 14/15 | 13/14 | 0.957430 |
| 5% | 13/17 | 16/17 | 13/15 | 13/14 | 0.934786 |

All candidates passed both Spotify gates and public per-prefix macro-F1 retention. Only 1% passed public per-class/per-prefix recall retention; 2.5% and 5% failed that gate. All three failed existing local mean macro-F1 and per-class/per-prefix recall retention. No candidate passed all six gates, so the frozen selection is null and status is failed_stop. The 1% candidate's ten-packet result is encouraging, but selecting it only at that prefix would change the declared rules after seeing outcomes. It is not activated or calibrated.

Public mean macro-F1 was 0.894825 for control and 0.900023, 0.898190, 0.898137 for the three candidates. Aggregate improvements do not override individual service failures. This study does not establish that weighting alone explains the previous failure or that an untested weight would solve it. Selection was reused and exposed, and the four Spotify flows share one session. No broad local accuracy or fresh validation claim follows.

Independent JavaScript checks verified 8,316 saved probability-vector argmaxes, 48 cohort/budget metric tables including per-class precision/recall/F1 and confusion matrices, all 18 gates, the no-eligible decision and twenty output checksums, with zero mismatches. Receipt: experiments/spotify-weight-study-v1/independent-check.json. Software verification: 528 Python tests passed, two existing dependency warnings; active src/scripts/tests lint passes and all 148 Python files pass formatting. A separate repository-wide lint scan found 54 existing issues in archived legacy code; no legacy/user notebook was edited. UI code is unchanged from the earlier 23-test/build checkpoint.

Decision: experiments/spotify-weight-study-v1/decision.json, SHA-256 d8a640a18f6c73a4f6cc5e89a17ea18915ab1b33b23792f897705a3bd1adf857. It binds all output paths/checksums, including reports, complete class probability vectors, protocol snapshot and training/selection row IDs. Each bundle also contains weights, preprocessing, labels, schema, architecture, versions, an explicitly unfitted policy and provenance. The new runner was uncommitted during execution; exported provenance binds its actual source SHA-256 alongside the prior HEAD commit.

| Weight | Bundle under experiments/spotify-weight-study-v1 | Artifact ID | Weights SHA-256 |
|---|---|---|---|
| 1% | spotify-001/bundle | eddce5a1bcbcc80ec43b4b9b89b642827e74df7fde2f08a0cc81db2756f7b613 | b5a312fe86850a93fdc1c7b74cbfb6ffa58009e781888bafa5e47062e6f42adf |
| 2.5% | spotify-0025/bundle | 8333adfe18b938661c4869b5163d90d5fc31592d44c8753d3bb6f8410f894567 | b0a0e231753bdb2d85a808195bf1089a6b30e5b3645516ed92f7c8dc92d69c5f |
| 5% | spotify-005/bundle | 0a701e1004ad849fa406f79df77e739153d4c4986d3984fbd826ec177c1dcc8d | 616accc993b4e7a6b005e9c8eab7f0dc10236a54b07c5ed1b9d9145bfc6efa5f |

The authorized grid is complete and closed. No extra recordings, weight variants, seeds, calibration or default changes follow from this protocol. The live app continues serving its existing model. The useful finding is that lower Spotify weight can recover the ten-packet balance in this reused development sample, while the later-prefix trade-off remains unresolved.

## Fit-free paired error follow-up

An additional read-only audit of the saved prediction files identifies the closest candidate's actual regressions. Evidence: experiments/spotify-weight-study-v1/paired-error-audit.json. It binds the original decision and all three candidate prediction files by SHA-256. No model fitting, threshold search, new data access, activation or role changes occurred.

The 1% candidate's three later correct-to-wrong checkpoints involve two independently referenced YouTube connections from two retained sessions:

| Flow suffix | Actual service | Candidate at 10 | Candidate at 20 | Candidate at 30 |
|---|---|---|---|---|
| 8858ef8f99dd | YouTube | YouTube, score 0.733661 | Spotify, score 0.733266 | Spotify, score 0.761690 |
| 176b76eac7ff | YouTube | YouTube, score 0.967138 | Spotify, score 0.308542 | YouTube, score 0.527953 |

The control was correct for all of these checkpoints. The first connection's error is a substantial vote shift, not just a near-tie; the second's twenty-packet Spotify/YouTube margin is only 0.004520. A uniform confidence story does not explain both. These are raw scores from an unfitted policy, not correctness probabilities. The audit selects no confidence threshold and makes no calibrated-acceptance claim.

At five packets the 1% candidate also introduces a YouTube-to-Spotify error on flow 0b7b6bb79bc5, while correcting a different error; the unchanged aggregate 15/17 therefore masks changed individual decisions. It is inappropriate to describe unchanged aggregate correctness as every flow being preserved. At ten packets every retained YT/IG flow is correct in both models.

The current summary-v1 code explicitly includes prefix length and per-direction timing/size statistics. It omits ordered packet positions. Later prefixes change these summaries, and the shared forest has no monotonic-correctness guarantee. This observation does not prove order loss, feature semantics or cross-prefix sharing caused these specific errors. The [older ordered-forest study](development-failure-audit.md) already failed its own fixed gates on a different cohort; repeating that feature change is not an unexplored solution, and its older failure does not settle performance on the new data.

A possible separate next hypothesis is an explicitly ten-packet-only classifier, with both control and candidate assessed at that identical feature budget and a fresh verification protocol. The existing ten-packet result motivates that narrower task; it cannot retrospectively make the failed multi-prefix study pass. Such a model must advertise its ten-packet budget, retain truthful uncertainty and undergo separate confidence fitting and genuine live checks. Freezing the UI's earlier label would be a new decision policy requiring validation. No such mode or future study is implemented or enabled by this audit.
