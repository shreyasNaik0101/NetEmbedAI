# Varied browser development collection — version 3

The original six-session study is now closed with a YouTube selection support
shortfall. The user subsequently requested a [separate one-recording follow-up
plan](browser-selection-followup-v1.md). Its helper support is now implemented
and preserves this plan and all recorded roles. The additional capture still
requires the user's deliberate Start and a separate new intent.
The entries below retain this original study's evidence and stopping decision.

This is a new, bounded **development-data** cycle after two failed calibration
attempts and the rejected ordered-feature experiment. It is not another request
to repeat calibration until a score improves. There is no validated local-model
repair or guarantee that this collection will produce one.

Original collection-tool checkpoint: 222 Python tests passed, with one existing
Starlette/AnyIO deprecation warning; Ruff lint/format passed for 74 active
Python files. The eligibility rule also preserves all seven valid rows in
two historical development recordings. Those fixtures are regression checks;
the two genuine version-3 recordings are separately archived below.

Actual local preflight is complete: service readiness is true, source B17 is
unchanged, capture is off, and four recorded-prefix HTTP predictions match the
direct predictor exactly. The stopped previous session was hash-verified as
archived before the local service was restarted. The new status exposes the
selected interface field; Wi-Fi ID 9 was enumerated without capture. Trial 03
was prepared before capture, and repeated preparation preserved its intent.

The frozen plan SHA-256 is
`330597baa5fc8e5973c87eade6cbb06b86d2e73109b5756aa8b4157252735d59`.
The private `instagram-dev-03-intent.json` SHA-256 is
`fef479e4243a99c755a942b3bf29e3a92c080ee723e8e1af5790c309b1da24d7`.
Preflight details are in
`experiments/browser-adaptation/collection-v3-engineering/prepared-first-recording.json`.
No new capture or training run occurred during preflight. Source software and
plan were committed at `55cfb3f` before preparing the first recording.

## First recording archived — 28 October

The user-started Wi-Fi session `b16f1670ff9042a58d0708cda3bc72e0`
(`instagram-dev-03`) stopped at the two-minute capture limit. Of 78 retained
flows, six independently matched supported references passed the fixed feature
checks: five Instagram connections and one YouTube connection, containing 174
packets and 22 available prefix points. The incidental YouTube connection stays
labelled YouTube. No mapped flow was excluded; no evidence was evicted. All 211
original B17 predictions reproduce exactly, with zero score or label differences.
The training pool now contains ten Instagram and thirteen YouTube connections;
none of the new rows has been used for fitting or model selection.

There were 110 combined viewer-event/pending-inference queue drops and 47
coalesced events. This counter does not measure network packet loss. The eligible
prefixes have no missing packets or within-direction payload-size mismatches.
Capture-to-browser receipt p50/p95 was 119.96/612.45 ms over 211 receipts. This is
one post-UI-change observation, not a controlled latency comparison or a browser
paint measurement; queue drops remain a limitation.

Raw evidence, all reference refusals, hashes and the archive summary are retained
under `artifacts/local/browser-development/instagram-dev-03-*`. The archive can
be validated again without replacing files. The private progress checkpoint is
`experiments/browser-adaptation/collection-v3-engineering/first-recording-progress.json`.
Trial `instagram-dev-04` has its next pre-capture intent for Reels; it has not
started. Capture remains off and B17 remains the source model.

## Second recording archived — 28 October

The subsequent user-started Wi-Fi recording `instagram-dev-04`, session
`8e268de57671473e85bef7df59324a87`, is also archived. Seven independently
matched Instagram connections pass the fixed checks: 183 packets and 24
available prefix points. Of 27 retained flows, seven are mapped, two unmapped,
eight ambiguous, three unverifiable sessions, one outside the supported set and
six unmatched connections. No mapped connection was excluded; no retained
evidence was evicted. All 81 original B17 predictions reproduce exactly.

The session stopped at its duration limit, with no recorded queue drops, 16
coalesced events and no reordered packets. Browser receipt p50/p95 is
79.63/408.38 ms over 81 events. This is another single-session timing observation;
it does not demonstrate a controlled latency improvement, independent service
accuracy or browser paint time. Reference refusals remain preserved.

Training support is now **17 Instagram and 13 YouTube connections**. Two of the
six new development recordings are archived. None of these new rows has been
used to fit a model or tune a policy. The next Explore/profile trial,
`instagram-dev-05`, cannot be prepared before **29 October 2026 at +05:30**.
Actual preparation on 28 October correctly refused the date gate and created
no intent; an offline gate check at the earliest allowed date passed. It did
not prepare or start capture. No additional recording is needed today.

The second archive summary SHA-256 is
`3b017210fa266711426b6324ef38aa56b5f7ad33ceecc0c068feeeb420ddae63`.
Evidence hashes are in
`artifacts/local/browser-development/instagram-dev-04-collection-summary.json`;
the private verified progress checkpoint is
`experiments/browser-adaptation/collection-v3-engineering/second-recording-progress.json`.
Capture is off; B17 remains unchanged. Remaining support, chronological selection,
candidate, calibration and independent live-quality gates are still pending.

The prior local training set has only five Instagram connections across two
visits. The [committed collection plan](../configs/browser-collection-v3.json)
adds varied activities over two local dates, then reserves later visits for
selection. Six new deliberate recordings are the maximum in this plan.

| Order | Trial | Role fixed before capture | Intended activity |
| --- | --- | --- | --- |
| 1 | `instagram-dev-03` | Training | Home feed/photos, 60 seconds |
| 2 | `instagram-dev-04` | Training | Several Reels, 60 seconds |
| 3 | `instagram-dev-05` | Training, later local date than trial 03 | Explore/search and public profiles, 60 seconds |
| 4 | `youtube-dev-03` | Training control | Choose and watch a video, 60 seconds |
| 5 | `instagram-dev-06` | Fresh selection | Mix feed and Reels, 60 seconds |
| 6 | `youtube-dev-04` | Fresh selection | Choose a different video, 60 seconds |

The first four original `dev-01/dev-02` recordings remain training data under
the already declared forward-study roles. Both failed `cal-01` and `cal-02`
pairs are excluded from this new training and selection cycle. Future
`cal-03` and `eval-01` names are reserved but cannot be collected with this
development tool. Calibration follows an eligible frozen candidate; final
evaluation follows a frozen decision policy. Existing calibration cannot be
renamed as an untouched final test.

## Third recording archived — 29 October

The Explore/search/profile trial `instagram-dev-05`, session
`7f8aa34810a84d0e9cfa370aaae5e2ca`, is archived after genuine user-started Wi-Fi
capture and a stopped normal-Chrome NetLog. Five independently mapped Instagram
connections pass the fixed feature checks, with **112 packets and fifteen
available prefix points**. Their lengths are 13, 13, 30, 30 and 26 packets.
No mapped flow was excluded, no retained evidence was evicted, and within-
direction payload sizes match the browser socket prefixes with no missing
prefix packets. Browser userspace ordering/timing differences remain explicit;
this is not full merged on-wire exporter parity.

The complete inventory retains five mapped, fourteen ambiguous, seven outside
the supported set and five unmatched connections. The chosen Instagram activity
does not label those other flows. All **94 original B17 predictions reproduce
exactly**, with no changed scores or decisions. On the fifteen independently
referenced Instagram prefix decisions, B17 withholds ten labels and accepts five
wrong ones (four YouTube, one Google Drive). None of its fifteen raw top choices
is Instagram. This remains a failure of the unchanged current model; the usable
recording is retained regardless. These repeated points within five connections
are correlated training diagnostics, not a new independent accuracy estimate.

The recording ended at the two-minute duration limit. Recorded queue drops,
reordered prefixes, backlog and stderr errors are zero; fifteen inference jobs
were coalesced. Nineteen idle-flow evictions and 75,050 post-prefix frozen inputs
are separate counters, not evidence of packet loss or discarded training rows.
Browser receipt p50/p95 is **83.86/476.92 ms over 94 acknowledged predictions**.
This single-session observation is neither paint time nor proof of a causal
latency improvement from the UI refresh. Capture is stopped.

Training support is now **22 Instagram and thirteen YouTube connections**, 35
total, with new Instagram training dates spanning 28/29 October at +05:30.
The fixed per-service counts and two-date condition are met. Three of six new
recordings are complete. The declared `youtube-dev-03` training control is still
required; it now has its pre-capture intent but has not started. Later separate
selection visits and their sixty-minute post-training-prefix gap remain required.
No fitting, new calibration, threshold change or promotion has occurred.

Summary SHA-256:
`9969db750045f30664f8d904648d23c2c887a05c12e70bceff410df56042bcd7`.
Its bound evidence remains at `artifacts/local/browser-development/instagram-dev-05-*`.
Verified pool counts and source-model decisions are in
`experiments/browser-adaptation/collection-v3-engineering/third-recording-progress.json`
(SHA-256 `f4321e9bd6609edce5da0230503a13b797f27857a75563bb2c20682286b00fc8`).
Archival rechecked the existing fixed matcher, socket checks and actual source
prediction replay; no source edits or repeated software tests were needed for
this evidence-only checkpoint. The [UI/backend checks](ui-refresh-20261029.md)
retain their previous scope.

An earlier unplanned user-started UI session on 29 October had its reference
channel off and no pre-capture trial intent. Its counters/timing are preserved
as `unplanned-20261029-ea257e36-*`, explicitly excluded and unscored. It receives
no training, selection, calibration or final role and is not counted as a
declared development recording.

## Fourth recording archived — 29 October

The YouTube training control `youtube-dev-03`, session
`7192ba2ba2da4e509382b7d796733b89`, is archived. Eight independently mapped
YouTube connections pass the fixed socket/prefix checks, each with thirty
retained packets: **240 packets and 32 available prefix points**. No mapped flow
was excluded and no retained evidence was evicted. The 42-flow inventory also
preserves sixteen outside the supported set, nine ambiguous, three unmapped and
six unmatched connections. Those other flows receive no assumed YouTube label.
[The beginner explanation](capture-checks.md) describes the actual acceptance rules.

All **114 original B17 predictions reproduce exactly**. Nineteen saved live
checkpoint predictions belong to the eight independently referenced YouTube
connections: twelve withheld a label, two accepted YouTube and five accepted a
different service. Four of nineteen raw top choices match the reference. These
are correlated training diagnostics from the unchanged model, not independent
quality of a replacement. There are 32 possible offline prefix points but only
nineteen retained live predictions on these connections; the denominators are
distinct. Forty jobs were coalesced across the session, so intermediate live
checkpoints need not all produce a model event. Complete packet prefixes remain
available for the offline study.

The session ended at its duration limit. Queue drops, reordered prefixes, backlog
and stderr errors are zero; twenty-five idle-flow evictions and 31,813 frozen
post-prefix inputs are separate counters. Browser receipt p50/p95 is
**200.82/504.67 ms over 114 acknowledgements**, not browser paint or a controlled
latency comparison. Zero reported queue drops does not prove zero network loss.

All declared training recordings are now archived: **22 Instagram and 21 YouTube
connections, 43 total**, with the required two new Instagram training dates.
Four of six new recordings are complete. No new model has been fitted, calibrated
or promoted. The next two are selection-only visits, not extra training repeats.

The latest retained training-prefix packet is at **01:37:38.021355 IST on
29 October**. The frozen sixty-minute gap therefore permits selection from
**02:37:38.021355 IST**; use **02:38 AM IST or later**. The real current-time
stage check refused early selection. An offline check at the computed boundary
passed; it created no future intent and started no capture. Fresh selection
still requires six valid connections and three complete thirty-packet prefixes
per service. Support or model gates can still fail; they are not relaxed.

Summary SHA-256:
`06adcecf9f793675d93ce4069cb212cd35eca71fc96ac3531bf6bcb76635456d`.
Bound evidence remains at `artifacts/local/browser-development/youtube-dev-03-*`.
Verified counts and the time-gate checkpoint are in
`experiments/browser-adaptation/collection-v3-engineering/fourth-recording-progress.json`
(SHA-256 `9200f808858801a830422e36dcdf20c27f39eb686928e5a9367d0e32c1126ced`).
The matcher, socket comparison, actual-model replay and all training proof bindings
ran during archival. This evidence-only update changes no software and requires
no repeated unit suite. Capture is off; selection is not prepared early.

## Fifth recording archived — 30 October

The Instagram selection visit `instagram-dev-06`, session
`814db3cae98c46eeaa360ee503f1751f`, is archived separately from training.
Seven independently mapped Instagram connections pass the unchanged socket and
prefix checks, with **178 packets and 24 available prefix points**. Five have
complete thirty-packet prefixes; the other lengths are thirteen and fifteen.
This meets the Instagram selection minimum of six connections and three full
prefixes. No mapped connection was excluded or retained evidence evicted.
The 41-flow inventory also preserves 21 ambiguous, nine outside the supported
set and four unmatched connections without guessed labels.

Every mapped connection has a unique browser UDP socket, no missing prefix
entries and zero within-direction ordered payload-size mismatch. These checks
do not establish merged wire order or full exporter parity. All **146 saved
B17 predictions reproduce exactly**, including their alternative scores.
Twenty actual saved live checkpoint predictions belong to the seven referenced
connections: fourteen withheld a label and six accepted an incorrect service;
zero raw top choices match Instagram. The 24 available offline points and twenty
saved live events are distinct denominators. These correlated development
observations diagnose the unchanged source model, not a replacement's quality.
Wrong predictions have not affected data eligibility.

Capture ended at its duration limit with zero reported queue drops, backlog,
reordered prefixes or stderr errors. Nine jobs were coalesced; twenty idle-flow
evictions and 76,418 frozen post-prefix inputs are separate counters. Browser
receipt p50/p95 is **84.97/480.28 ms over 146 acknowledgements**, not paint time
or proof of loss-free capture. Longer-window collection was off.

Five of six declared recordings are archived. Training remains **22 Instagram
and 21 YouTube connections**; this selection recording does not enter training.
The actual capture follows the fixed post-training gap. The remaining reserved
visit is `youtube-dev-04`, also selection-only. Fitting remains blocked until
its independent-reference support and chronology checks pass; no model, policy
or default changed. No additional recording or relaxed gate is authorized by a
failed result.

Summary SHA-256:
`cab17786304cde1682b741688e4c07bc6e52c50370d72567d1a8b60675ce1318`.
Bound source files remain at
`artifacts/local/browser-development/instagram-dev-06-*`. The archive command ran
the fixed matcher, socket comparison, source-model replay and checksum/role
validation. This evidence/documentation update changes no software; the prior
295 Python and sixteen UI test checkpoints retain their existing scope.
All bound source hashes and diagnostic counts were checked again in
`experiments/browser-adaptation/collection-v3-engineering/fifth-recording-progress.json`
(SHA-256 `588f335386bcdd05b7716d1aae07a71621155a91db81f405c48e03884142b291`).
The helper has prepared `youtube-dev-04` after validating its prerequisites;
this creates its intent and exact log filename only. Capture remains off and
must be deliberately started by the user.

## Sixth recording archived; support gate refused fitting — 30 October

The final reserved visit `youtube-dev-04`, session
`4b9ff2c9ce8a453eb4848e4ca35f7083`, is archived as selection-only.
Five independently referenced YouTube connections pass all fixed socket/prefix
checks, each with thirty packets: **150 packets and twenty available prefix
points**. No mapped flow was excluded and no retained evidence evicted. The
32-flow inventory also preserves nine ambiguous, thirteen outside the supported
set, two unmapped and three unmatched connections without guessed labels.
All five mapped connections have unique browser UDP sockets, no missing prefix
entries and zero within-direction ordered payload-size mismatch. This remains
a partial parity check, not proof of merged wire order or full exporter parity.

All **102 saved B17 predictions reproduce exactly**, including alternative
scores. Fourteen actual saved live checkpoint events belong to the five labelled
connections: thirteen withheld, one accepted an incorrect service, and six raw
top choices match YouTube. The twenty possible offline points and fourteen saved
live events are distinct denominators; prefixes within a flow are correlated.
Wrong predictions do not affect capture eligibility or supply a local accuracy
claim for a replacement model.

Capture ended at its duration limit, with zero reported queue drops, backlog,
reordered prefixes or stderr errors. Sixteen jobs were coalesced; twenty idle
flow evictions and 70,544 frozen post-prefix inputs are separate counters.
Browser receipt p50/p95 is **101.59/496.71 ms over 102 acknowledgements**,
excluding any claim of paint time or zero network loss. Longer-window
collection was off.

All **six of six** declared recordings are now archived. Training stays at
22 Instagram/21 YouTube connections. Separate selection has seven Instagram
and five YouTube connections (328 packets, 44 available prefix points), with
five full thirty-packet connections per service. Train/selection record IDs
and session IDs are disjoint. Instagram meets its coverage minimum; YouTube
is **one connection below the fixed six-connection minimum**. Full-prefix
coverage passes for both services, but does not replace the connection minimum.

The exact frozen seed-17 runner was invoked to verify its guard. It exited 1
with `insufficient independently referenced local class support`, before
creating its output directory, reading public splits or fitting any model.
This is a support-gate refusal, not a completed or failed model comparison.
There is no new candidate result, repetition, calibration, final evaluation or
promotion. B17 remains unchanged. The six-capture limit is reached: no extra
capture, role rewrite, ambiguous-flow relabelling or lowered requirement is
silently permitted. The existing valid records are preserved; any follow-up
study needs an explicitly declared scope rather than a continuation disguised
as the completed frozen study.

Summary SHA-256:
`ebd5e962534fa933fb96e5a6d464ef074661eab8f65a3dd356d9d6baa820266f`.
Bound evidence remains at `artifacts/local/browser-development/youtube-dev-04-*`.
The final progress checkpoint is
`experiments/browser-adaptation/collection-v3-engineering/sixth-recording-progress.json`
(SHA-256 `7b1986a772ba2532e9e73f6695e021d9b35271027eb320ee5cac55fa68996bd4`).
The actual guard transcript is `expanded-v3-seed17-support-gate.log` alongside
it (SHA-256 `44259c859586c4a38bd2429dcc49f8d3743321387d5270a772aaa197d80ea2c9`).
The matcher, packet checks, source replay and source hashes were verified;
this evidence/documentation update introduces no software change or new unit
test result. Capture is off. The preceding 295 Python/sixteen UI test
checkpoints retain their recorded scope.

## Support and time gates

Before preparing selection, training must contain at least twenty independently
referenced Instagram connections and twelve YouTube connections. The new
Instagram training visits must cover two dates at the declared +05:30 offset.
Trial 05 cannot be prepared on the same local date as trial 03. Selection must
start at least sixty minutes after the last retained training-prefix packet, after every
training recording is archived. Selection needs six valid connections per
target service, including at least three complete thirty-packet prefixes each.

The timing gate now sums each connection's retained interarrival gaps, rather
than using its start as its end. Tests cover an earlier-starting connection that
finishes later and reject selection while its full sixty-minute gap is pending.
Legacy experiment proof dictionaries are unchanged; new version-3 proofs include
the observed packet bounds. No frozen role, plan byte or recorded row changed.

These are engineering coverage targets, not independent population sample sizes
or statistical guarantees. Prefixes within one connection and connections
within a visit are correlated. All captures may still share one browser,
machine and Wi-Fi network; cross-browser/network generalization is not claimed.
If the six-session cap does not meet support or quality requirements, record
the shortfall. Do not silently add sessions, relax limits or rewrite roles.

## One recording at a time

From `traffic_classification`, the first preparation command is:

```powershell
.venv/Scripts/python.exe scripts/collect_browser.py prepare instagram-dev-03
```

Preparation copies the plan into the private collection directory without
overwriting a different frozen plan. It validates prerequisites, checks the
stopped local service and real source bundle, confirms the selected interface,
and writes a pre-capture intent. It does **not** press Start, open an interface,
train or fit confidence. The source remains B17 during data collection, so its
visible predictions are not results from a repaired model.

The user then:

1. Keeps NetEmbedAI in Edge and opens normal Chrome at `chrome://net-export/`.
   Leaves **Strip private information** selected and raw/sensitive bytes off.
   Starts logging to the exact new filename printed by preparation.
2. Refreshes the rebuilt Edge app, selects Wi-Fi, enables the separate reference
   checkbox and presses Start deliberately. Keeps both Edge and Chrome visible
   side by side to make browser delivery conditions explicit.
3. Opens a fresh Instagram connection in another Chrome tab and performs the
   intended activity for about sixty seconds. The activity never supplies a
   flow label; existing pooled connections may remain unverifiable.
4. Stops NetEmbedAI, then Chrome logging. Does not Start another capture yet.

Archive before the next Start:

```powershell
.venv/Scripts/python.exe scripts/collect_browser.py archive instagram-dev-03
.venv/Scripts/python.exe scripts/collect_browser.py status
```

The archive command saves stopped HTTP evidence bytes, applies the existing
fixed NetLog matcher, checks socket-prefix sizes, replays the actual source
model, and writes checksummed packet-only rows plus a summary. Outputs are
resumable and never overwrite different evidence. It uses only local GET
endpoints and offline scripts; it cannot start capture. Its source model,
selected interface and capture time must match the frozen intent. New capture
status retains the selected interface after Stop.

Only fixed data-quality rules determine eligibility: a mapped supported
reference, at least five observed packets, a unique socket, no missing prefix,
and zero within-direction payload-size mismatch. All reference refusals and
every mapped-flow exclusion remain recorded. No activity name, prediction or
confidence chooses an example. Browser userspace order/timestamps do not prove
wire order, full exporter parity or historical timing quantization.

Other supported-service references stay in the exported inventory. The declared
local study trains/scores only its YouTube/Instagram targets and explicitly
records other supported references as unscored. Unsupported protocols and
unmapped origins never get a guessed service label. Raw logs stay local and
ignored by Git.

## Training remains gated

The three `configs/browser-expanded-v3-seed{17,42,123}.json` configs freeze the
existing compact CE TCN and summary forest, original training-only
normalization, public data/control cohorts, 0.25 local mass and bounded CPU
budget. The failed ordered-feature change is excluded. Seed 17 runs first;
if no candidate passes development gates, repetitions and calibration stop.
The gate requires local F1 ≥0.75, each local recall ≥0.65, gain ≥0.01 over the
paired previous summary forest, no class-recall regression, and original
historical clean-retention loss ≤0.02. Forest preference retains the existing
quality/CPU comparability rule. These are frozen development tolerances.

Only after all support, timing, role and checksum checks pass:

```powershell
.venv/Scripts/python.exe scripts/adapt_browser.py --data data/processed/v2 --collection artifacts/local/browser-development --initial-bundle experiments/full-real/20261024-151720-3532794c/bundle --config configs/browser-expanded-v3-seed17.json --output experiments/browser-adaptation/expanded-v3-seed17
```

No training job is launched by collection. The remaining recordings require
genuine user-started data; software fixtures and replay cannot satisfy that
gate. A successful development cycle would still need new calibration,
independent live quality evaluation and broader latency/loss measurements.
