# Browser calibration failure and forward study — 26 October 2026

Later result: the replacement's [fresh calibration on 26–27 October](browser-calibration-02.md)
also fails the frozen acceptance limits, despite improved raw predictions.
It remains disabled. This report preserves the preceding development checkpoint.

**The first adapted forest failed its separate calibration visit. It was not
enabled.** The earlier 22/27 development result did not carry over to the next
Instagram recording. Both the good and bad results remain preserved.

## Actual separate calibration evidence

The user deliberately started the two recordings after the candidate weights,
normalization, choice and calibration rules were frozen. The fixed browser-log
matcher attributed seven Instagram and seven YouTube connections. One Instagram
flow has 16 packets; the other 13 have 30, giving 54 available prefix points.
All 406 payload sizes matched their independent browser socket sequence within
direction, with no missing prefix packets. This does not establish wire timing
or merged order. Both sessions stopped at the duration guard, with no processing
drops, evidence evictions or process errors. Their 255 original B17 live
predictions reproduced exactly. The forest results below are offline inference
on the separately collected metadata, not arriving live forest events.

| Frozen forest, unthresholded top-1 | Correct | Available prefix points |
| --- | ---: | ---: |
| Instagram calibration | 5 | 26 |
| YouTube calibration | 22 | 28 |

The predeclared policy requires at least 30 accepted local points, five per
service, ≤0.10 empirical accepted error overall and per local service, and a
historical public-calibration error/support control. The 500 historical flows
produce 1,419 valid checkpoints, not 2,000, because short flows are not padded
into extra calibration points.

| Threshold | Local accepted | Local errors | Instagram accepted | Instagram errors |
| --- | ---: | ---: | ---: | ---: |
| 0.00 | 54 | 27 | 26 | 21 |
| 0.40 | 32 | 11 | 13 | 10 |
| 0.50 | 20 | 4 | 6 | 4 |
| 0.56 | 15 | 0 | 1 | 0 |

No grid threshold satisfies all constraints. At 0.56 the accepted examples are
correct, but there are too few overall and only one Instagram point. Lower
thresholds admit too many Instagram errors. This is a model-quality failure,
not merely a shortage of raw calibration points. More repetitive recordings
were not requested to inflate the denominator. No limits were relaxed, weights
refit, calibrated bundle created or default switched during this attempt.

The report is `experiments/browser-adaptation/calibration-01/report.json`.
It contains the full 101-threshold curve, source hashes and role/time checks.
Its `policy.fitted` is false and `selected` is null. Local and historical raw
probabilities are saved in separate prediction files. Original model bytes and
the old CESNET22 final report remain unchanged.

## Explicit retirement before further diagnosis

`calibration-01/retirement-decision.json` records the failure and retires the two
calibration trials to **diagnostic development selection only**. They cannot be
called independent calibration or final evidence again. Original files, roles,
checksums and failed results are preserved rather than rewritten. Every future
replacement requires fresh calibration after its weights and choice are frozen.

A fixed-model diagnostic comparison also found only 9/26 Instagram and 23/28
YouTube top-1 points correct for the first adapted TCN. Swapping to that model
would not establish a repair, and these results are now development diagnostics.

## Bounded chronological follow-up

The follow-up trains on the first **two** visits per service: 17 local flows
(five Instagram, twelve YouTube) plus the original 14,000 public training flows.
It checks the later retired recordings: fourteen flows, seven per service.
Whole sessions remain separate and training precedes selection. There is no
random prefix split and no new final data. The retirement/report checksums bind
the role transition, and the loader prevents retired calibration from silently
entering training in this study.

Two local training masses, 0.25 and 0.50, were frozen before fitting, using the
same TCN, forest, learning rate, five-epoch/50-step budget, four prefix budgets,
training-only normalization and public data. No architecture, feature channel,
augmentation, SupCon or destination-based feature was added. Stronger gates
require local mean-budget F1 ≥0.75, recall ≥0.65 for each service, improvement
over the failed forest and historical public-retention loss ≤0.02. The public
control is historical development data, not a forward generalization test.

At seed 17, both forests passed these **development** gates:

| Local training mass | Local mean-budget F1 | Instagram recall | YouTube recall | Historical clean F1 |
| --- | ---: | ---: | ---: | ---: |
| 0.25 | 0.87386 | 0.77976 | 0.89286 | 0.90114 |
| 0.50 | 0.88199 | 0.77381 | 0.92857 | 0.89994 |

Both TCN settings failed the stronger eligibility gates. A recorded rule picks
the higher-retention, lower-mass forest when local scores are within 0.01.
The tie rule was recorded before reading the mass-0.50 result, after fitting;
the two masses and eligibility gates were frozen before fitting. Seeds 42 and
123 then completed their predeclared stability checks:

| Seed, mass 0.25 forest | Local mean-budget F1 | Correct Instagram points | Correct YouTube points | Historical clean F1 |
| --- | ---: | ---: | ---: | ---: |
| 17 | 0.87386 | 20/26 | 25/28 | 0.90114 |
| 42 | 0.87149 | 19/26 | 26/28 | 0.89990 |
| 123 | 0.90937 | 20/26 | 28/28 | 0.90314 |

All pass the stronger development gates. F1 averages the four budget-specific
observed-class macro scores; it is not the fraction of correct points. These
54 points come from only fourteen connections across two visits, so they are
correlated. The fixed deployment seed remains 17, not the best seed. The seed-17
TCN reaches only 0.57459 local F1 and fails eligibility. These development
results do not overturn failed calibration or prove future local accuracy.

The replacement decision is frozen at
`experiments/browser-adaptation/forward-mass25-seed17/calibration-candidate-decision.json`.
Its uncalibrated bundle is `forward-mass25-seed17/forest/bundle`, artifact ID
`132caf41f5eb517afdb806bd1cab8b1e503e977adb3703b4d33d588264471ffb`.
All model choices and normalization are frozen. A new version-2 calibration
plan reserves the still-uncollected `instagram-cal-02` and `youtube-cal-02`
visits. It supersedes only the unused reservations from version 1; both original
plans and the failed report remain intact. No original `cal-01` recording may
be reused for policy fitting. No new capture was started to produce this result.

The descriptive feature audit found all 31 collected connections started with
1,250-byte payloads. Timing distributions changed across visits: for example,
Instagram's median first-five-packet duration changed from 15.21 ms on its first
visit to 6.43 ms on the later visit. This is a diagnostic clue, not a proven
cause or a justification for mapping a byte count directly to a service.

Exact configs and commands are retained:

```powershell
.venv/Scripts/python.exe scripts/adapt_browser.py --data data/processed/v2 --collection artifacts/local/browser-development --initial-bundle experiments/full-real/20261024-151720-3532794c/bundle --config configs/browser-forward-mass25.json --output experiments/browser-adaptation/forward-mass25-repeat
```

Other configs are `browser-forward-mass50.json` and the seed-42/123 versions.
Use new output paths. The private collection plan, retirement, diagnostic model
comparison and feature audit are retained locally. No training uses the later
retired recordings; they serve selection only. A promising follow-up still
needs fresh calibration and user-started live evaluation before release.

## Artifact and software verification

The actual trained seed-17 forest passes direct/API alternative-score parity
with readiness and prediction HTTP 200. Its unfitted policy withholds labels.
Loading and inference succeeded while `Path.open` access to processed training
data and private browser references was blocked; this is a scoped access check,
not a complete filesystem sandbox. The isolated API check never starts capture
or changes the running service.

With two Torch threads, the same retained 30-packet input, 50 warm-up calls and
1,000 measured calls, CPU pipeline p50/p95 is **27.02/30.01 ms**. Batch-32
throughput is 371.87 flows/s in this synthetic call-load benchmark. This is
trained-model execution on a recorded input, not live quality, packet-arrival
throughput, browser latency or a hard real-time guarantee. Hardware/runtime and
exact values are in `forward-mass25-seed17/forest/cpu-benchmark.json`.

**184 Python tests passed**, with one existing Starlette/AnyIO deprecation
warning. Ruff lint and format passed for all 65 active Python files. UI code
was unchanged; its preceding seven-test/build result is not a new UI run.
The new CLI's real-artifact missing-input check refuses calibration before
creating output. The running B17 identity and original final-report checksum
were rechecked unchanged, with capture stopped. Raw logs and generated evidence
remain local and ignored; no publication or merge occurred.

| Local artifact | SHA-256 |
| --- | --- |
| `forest/bundle/forest.json` | `6e1276901dddb09e5bb307a7c4fa668db1cf37778d4fcae846492afd520c0b1e` |
| `calibration-candidate-decision.json` | `2656a77b3754d7a2d2994b3be319b9b5f4904544084aa94845251a6986b0a13d` |
| `forest/cpu-benchmark.json` | `13b120c5cb379e0ea0d535018485cda17d85eff29fcbf9e2f4a585c909ef5c71` |
| `forest/api-parity.json` | `e61bbb55b26a792a9d2619102aac5847ef5da926d7d0751f91f69e823c0795a3` |

Paths in this table are relative to
`experiments/browser-adaptation/forward-mass25-seed17/`. The full version-2
calibration plan SHA-256 is
`7aa92b49492f94f29134d747d53c476bb0eb090259c28a3816ed2e435e56a8e6`.
The local portable archive is
`artifacts/local/NetEmbedAI-v2-browser-forward-forest-seed17-UNCALIBRATED.zip`
(10,843,840 bytes), SHA-256
`1373a24b5432e44a7da07ebd16d07198a48e47b765301a32a1210014ba5735b2`.
It includes weights, preprocessing, labels, policy, provenance, checksums and
the decision/report snapshot. It contains no browser recordings or training
data and deliberately remains uncalibrated.

Additional commands from `traffic_classification`, with the existing local
data and evidence paths:

```powershell
.venv/Scripts/python.exe -m pytest -q
.venv/Scripts/python.exe -m ruff check src tests scripts
.venv/Scripts/python.exe -m ruff format --check src tests scripts
.venv/Scripts/python.exe -m netembed.cli benchmark --bundle experiments/browser-adaptation/forward-mass25-seed17/forest/bundle --flow experiments/browser-adaptation/pilot-01/benchmark-flow.json --output experiments/browser-adaptation/forward-mass25-seed17/forest/cpu-benchmark-repeat.json
```

The original experiment commands also accept the explicit seed-42/123 configs
and distinct output paths. Private source recordings are necessary to reproduce
training, but are unnecessary for bundle inference. To fit only policy **after**
new reference-audited calibration recordings have been collected:

```powershell
.venv/Scripts/python.exe scripts/calibrate_browser.py --data data/processed/v2 --collection artifacts/local/browser-development --bundle experiments/browser-adaptation/forward-mass25-seed17/forest/bundle --decision experiments/browser-adaptation/forward-mass25-seed17/calibration-candidate-decision.json --plan-name calibration-collection-plan-v2.json --output experiments/browser-adaptation/calibration-02
```

Currently that command must refuse missing fresh recordings. Passing software
checks or replay does not satisfy the remaining new-model calibration and
genuine user-started live-quality gates.

## Fresh replacement calibration: collection in progress

The user completed `instagram-cal-02` after the replacement and version-2 plan
were frozen. Session `e8d7a644dae84198af59611a623edb72` stopped at the duration
guard. The complete inventory has 37 retained connections: six independently
mapped Instagram, eleven outside the supported set, fifteen ambiguous, one
unverifiable session and four unmatched. No refusal was removed from the report.
One mapped connection has 13 packets and the other five have 30: 163 packets
and 22 available 5/10/20/30-packet checkpoints. All mapped socket prefixes are
unique, with no missing packets or within-direction size mismatches. This does
not prove merged wire ordering or historical timing parity.

All 99 saved B17 live predictions reproduce exactly; these are source-artifact
checks, not replacement predictions. Browser receipt latency p50/p95 is
168.48/511.15 ms for those 99 events, not rendering latency or replacement
latency. The session reports zero processing drops, 34 coalesced checkpoints,
zero reordered packets and zero capture-process errors. Its raw browser log is
108,665,070 bytes and stays private. The collection summary SHA-256 is
`d2310af3c00f38e7581da2226f8defea2b40bc3066137b2d2b001b8f9dfd2cfb`;
capture SHA-256 is
`42bda38be630c5972de26c24fb3af408ee21c135be671df0fe4ecac10b1ea288`.
Files are under `artifacts/local/browser-development/instagram-cal-02-*`.

The calibration-only loader passes all role/hash/packet-reference checks.
The CLI still refuses missing `youtube-cal-02` before output or historical
calibration access. No replacement probabilities were inspected on this
partial collection; no weight fitting, threshold fitting or candidate switch
occurred. A pre-capture YouTube intent is saved against the same frozen
candidate/plan. Complete that separately before joint policy fitting. Both
fresh recordings remain excluded from training and model selection.

The policy-fitting CLI accepts `--plan-name calibration-collection-plan-v2.json`
for the replacement; its default remains version 1 for reproducibility. The
candidate/plan checksums, new pre-capture intents, whole-session exclusion and
post-freeze timestamps must all match. Until both fresh recordings exist, the
command fails before fitting. No deadline or accuracy guarantee is inferred.
