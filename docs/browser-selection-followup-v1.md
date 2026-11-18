# One-recording selection follow-up — 30 October 2026

**Completed:** the single visit passed coverage and the fixed seed-17 comparison
ran. [Neither candidate passed the quality gate](browser-selection-followup-results.md).
The forest improves Instagram but regresses YouTube; repetitions/calibration
stop and no default changes. The preparation/declaration history below remains
preserved. No further recording is requested by this plan.

This plan addresses the YouTube selection shortfall with **one additional
user-started recording**, `youtube-dev-05`. The user requested this follow-up
after the original six-recording study closed. The original plan and its
recordings remain unchanged. This is a declared extension for development
coverage; it is not a claim that the original study passed.

The checksum-bound specification is
[`configs/browser-selection-followup-v1.json`](../configs/browser-selection-followup-v1.json),
SHA-256 `8bacececc733c8380a7de0b8d166fcb85803b107ab053650ba41d0a6abf7fadb`.
It records the ten existing trial summaries/packet-row hashes and all three
original runner-config hashes before this additional data is collected.

**State: helper support implemented; capture remains user-started.** The new
dispatcher accepts this explicitly pinned follow-up while the v3 reader keeps
its original limit. Parent recordings load against their original plans and
hashes. Generated runner configs retain every undeclared field and all numeric
settings. The protocol's `planned_not_prepared` value preserves its declaration
state; current preparation is recorded separately in the private intent.

Preparation now passed against the actual stopped service on 30 October:
`youtube-dev-05` is **prepared, not capturing**. All ten inherited recordings
and three generated configs validate; B17 is unchanged. Implementation commit:
`e9a1543`. Intent SHA-256:
`f61f1c1eb578837d32c2b2a08875a1091b1b8d3edc5ec91111f69d353f0517ec`.
The actual preflight is saved at
`experiments/browser-adaptation/followup-v1-engineering/prepared-youtube-dev-05.json`
(SHA-256 `43e4d9b7ca3cb685094db6396f4523ebb07f343f07ed2f1048a6a9dde617fca7`).
No NetLog or bound attempt exists yet; genuine capture and candidate fitting
remain pending.

The preparation statement above records the earlier checkpoint. The single
user-started follow-up is now archived, as detailed below.

## Single visit archived — 30 October

`youtube-dev-05`, session `eb34135d99944b00875a88fd52eb34b7`, contributes
**five verified YouTube connections, 142 packets and nineteen available prefix
points**. Four connections contain thirty packets; the fifth contains 22.
Every mapped connection passes the fixed unique-socket, missing-prefix and
within-direction payload-size checks. No mapped flow is excluded and no retained
evidence is evicted. The 31-flow inventory also preserves ten outside the
supported set, two unverifiable, five ambiguous, three unmapped and six unmatched
connections. They receive no assumed YouTube label.

All **99 original B17 predictions reproduce exactly**, including alternative
scores. Seventeen actual saved live checkpoint events belong to the five
verified connections: nine withheld, two accepted correctly and six accepted
incorrectly. Eight raw top choices match YouTube. These source-model diagnostics
and the nineteen available offline points have distinct denominators; they are
correlated development observations, not independent replacement accuracy.

Capture ended at its duration limit with zero recorded queue drops, backlog,
reordered prefixes or stderr errors. Sixteen jobs were coalesced; twenty idle
flow evictions and 16,977 frozen post-prefix inputs are separate counters.
Browser receipt p50/p95 is **212.68/519.01 ms over 99 acknowledgements**,
not paint latency or proof of loss-free capture. Longer-window statistics were off.

Pooled selection now contains **seven Instagram and ten YouTube connections**,
with five/nine full thirty-packet prefixes respectively. All fixed connection
and full-prefix support gates pass. The 63 available checkpoint cases come from
seventeen connections across three visits, not 63 independent sessions.
Training remains 22 Instagram/21 YouTube connections; none of this visit enters
training or normalization. The single additional attempt is consumed and
archived. No further capture is requested by this plan.

Archive summary SHA-256:
`fdee6b7d80e3b43a3bd581c7aefe364426ba9a88ee0e6178815736bed814add3`.
Bound private evidence stays at `artifacts/local/browser-development/youtube-dev-05-*`.
The verified source-count/checksum checkpoint is
`experiments/browser-adaptation/followup-v1-engineering/archived-youtube-dev-05.json`
(SHA-256 `0cfd93931763faa3921911eb9f1c1604ecd9c402ef696339be5510bb9add611b`).
The fixed seed-17 experiment follows these admission checks; archival itself
does not train or alter the app model.

## What we already have

| Role | Instagram connections | YouTube connections |
| --- | ---: | ---: |
| Training, unchanged | 22 | 21 |
| Selection, retained in full | 7 | 5 |
| Selection minimum, unchanged | 6 | 6 |

Each selection service already has five complete thirty-packet prefixes,
exceeding the minimum of three. YouTube needs at least one more independently
referenced connection to meet the connection-count gate. A valid recording does
not guarantee that Chrome will create a new, unambiguously matched QUIC
connection. Six is a declared engineering coverage requirement, not a
statistical guarantee; nearby connections and prefixes remain correlated.

## The single additional visit

The additional recording is **selection-only**. It never enters model training
or normalization. All valid connections from it join the existing two selection
recordings; we do not keep just the one needed to cross the threshold or choose
connections by prediction, confidence or correctness. Other supported services
remain in the inventory but outside this two-service local comparison.

After the helper is implemented, verified and has printed a pre-capture intent:

1. Save any browser work, exit Chrome and reopen a normal window without
   restoring YouTube pages before capture. This gives the collector a chance to
   observe fresh connections. It does not guarantee them. Keep NetEmbedAI in
   Edge, with both windows visible beside each other.
2. Open `chrome://net-export/` first. Keep **Strip private information** selected
   and sensitive/raw bytes off. Start logging to the new intended path:

   ```text
   C:\Users\shrey\NetEmbedAI\traffic_classification\artifacts\local\browser-development\youtube-dev-05-netlog.json
   ```

3. In NetEmbedAI select **Wi-Fi**, enable **separate handshake reference**, leave
   longer-window statistics off and deliberately press **Start capture**.
4. Open a different YouTube video in a new Chrome tab and watch for **60 seconds**.
   Keep the Edge app visible. No protocol flags, private window, forced network
   resets or repeated captures are part of this procedure.
5. Stop NetEmbedAI, then stop Chrome logging. Archive before any other Start.

The existing session cap stays at 120 seconds. The limit is **one additional
user-started session in total**, including an unusable or interrupted attempt.
There is no automatic retry. No further Instagram visit is requested.

## Admission and stopping rules

The existing matcher and eligibility rules stay fixed: verified eligible QUIC,
at least five actual packets, an independently mapped origin, unique browser
UDP socket, no missing prefix entries, and zero within-direction ordered
payload-size mismatch. Preserve every refusal/exclusion. Replay the actual
B17 predictions and check source hashes. The visible model remains B17 during
collection; browser names do not become prediction inputs.

The new intent must precede capture. The new recording must follow the last
retained packet of the parent selection visits, remain separate from every
training session, and satisfy the existing sixty-minute post-training gap.
Training is unchanged, so this creates no new date or one-hour waiting period
after the previous selection visit. The helper must validate actual timestamps.

If the additional visit is unusable, or pooled selection still contains fewer
than six verified YouTube connections, **stop this follow-up without fitting**.
Record the shortfall. Do not relax matching/count rules, relabel ambiguous
flows, move training into selection or request another capture under this plan.

If it passes, freeze the complete enlarged selection inventory and its hashes
before training. Retain all seven existing Instagram and five existing YouTube
connections; no removal based on their already observed results is permitted.

## The comparison after coverage passes

Reuse the existing compact supervised CE TCN and same-data summary forest.
Training remains the same public data plus 43 local training connections, with
the original public-training-only saved normalizer, 25% local training mass,
two CPU threads, batch size 64, and at most five epochs of fifty steps per seed.
No new augmentation, SupCon comparison, architecture or feature sweep is added.

Run seed **17 first** in a new output directory
`experiments/browser-adaptation/selection-followup-v1-seed17`.
Compare with B17 and the previous summary forest on the same enlarged selection
set. Preserve configs, IDs, seeds, per-prefix predictions, provenance, runtime
and CPU timings. Public historical selection remains a retention control;
public final-test and protected local calibration/final data stay out of tuning.

The existing numeric eligibility rules remain:

- Mean 5/10/20/30-budget local macro-F1 at least **0.75**.
- Mean-budget recall for each local service at least **0.65**, without regression
  against the paired previous forest.
- Local score gain of at least **0.01** over that forest.
- Mean public clean-retention loss no greater than **0.02** against B17.
- Prefer an eligible forest within **0.01** of the selected score when its
  measured CPU median is no worse.

These are mean-budget measures, not a guaranteed minimum at every prefix or an
accuracy percentage. The runner's numeric fields and `passes_guard` define the
inherited rules; a stale prose string in the parent config mentions a different
gain. New config prose must accurately describe the unchanged numeric 0.01 gate.

If no seed-17 candidate qualifies, stop repetitions and calibration. Otherwise
repeat the same bounded comparison at seeds **42 and 123**, each once in a new
directory. Keep the seed-17 family/checkpoint decision; never choose the best
seed after seeing results. This follow-up also predeclares a conservative
stability check: the chosen family must remain eligible in both repetitions.
If it does not, report instability and stop before calibration, without switching
to another family or adding seeds. All repetition results remain reported.

An eligible, stable candidate is still uncalibrated and cannot replace the app's
default automatically. New calibration and independent live evaluation need
their own prospective collection instructions. No such recordings are requested
by this one-session plan. Previously observed development results and this
adaptive enlargement cannot serve as blind final accuracy evidence.

## Engineering before the recording

Add explicit support for this follow-up instead of editing the closed v3 plan.
Inherited records must validate against their original plans and checksums;
the new trial must validate against its new intent and protocol. Keep the old
v3 reader's six-session limit and role rejection intact. Use separate runner
configs/output paths; do not overwrite the original guard refusal or artifacts.

Before preparing capture, verify rejection of changed parent hashes, selection
being reassigned to training, undeclared second trials, reused session IDs,
early timestamps and insufficient coverage. Tests must not start native capture.
Check that generated configs differ from the bound originals only in declared
cohort/provenance fields and accurate descriptions, with numeric training and
quality settings unchanged. Save the preflight evidence, then print the exact
log path and user steps. The helper now implements these checks; passing them
does not establish new live validation or classification quality.

The first stopped session passed to archival is bound to an immutable attempt
record **before** eligibility checks. Raw capture/status/timing bytes survive an
unusable attempt; the helper refuses another preparation and resumes only that
same saved snapshot. This controls the archival workflow, not arbitrary manual
Start presses in the generic app. Use exactly one Start and archive after Stop;
do not restart the app capture while waiting for archival. The helpers make
loopback GET requests and cannot start native capture.

Only committed config text tolerates Git's LF/CRLF conversion. Parent private
plans, packet rows, source logs and captured evidence retain their raw-byte hash
requirements. Existing files are never rewritten to make a check pass.

The completed local checkpoint is **318 Python tests passed**, one existing
Starlette/AnyIO deprecation warning, and Ruff lint/format for 99 active files.
It covers the new guards alongside the existing native offline fixtures; it
does not start live capture. The actual ten-recording parent preflight and
three generated-config comparisons also pass. No UI change or retraining is
part of this checkpoint.

## Exact helper commands

From `traffic_classification`, generate the three fixed configs idempotently:

```powershell
.venv/Scripts/python.exe scripts/browser_followup.py configs
```

Prepare, then wait for the user to perform the single visit above:

```powershell
.venv/Scripts/python.exe scripts/collect_browser.py --plan configs/browser-selection-followup-v1.json prepare youtube-dev-05
```

After the user stops NetEmbedAI and Chrome logging:

```powershell
.venv/Scripts/python.exe scripts/collect_browser.py --plan configs/browser-selection-followup-v1.json archive youtube-dev-05
```

Only after the archive passes support checks, run seed 17 once:

```powershell
.venv/Scripts/python.exe scripts/adapt_browser.py --data data/processed/v2 --collection artifacts/local/browser-development --initial-bundle experiments/full-real/20261024-151720-3532794c/bundle --config configs/browser-selection-followup-v1-seed17.json --output experiments/browser-adaptation/selection-followup-v1-seed17
```

If it has an eligible candidate, use the corresponding `seed42` and `seed123`
config/output names in that order, each once. The runner refuses an altered
config, wrong destination, missing/ineligible first seed or changed repetition
cohort; repeats keep the seed-17 candidate's exact family/epoch choice. They
cannot select a better seed or another family to rescue instability. Then:

```powershell
.venv/Scripts/python.exe scripts/browser_followup.py decision
```

This saves an immutable development stability decision and never promotes a
default, fits a policy or collects traffic. Missing recordings/results remain
errors, with no substitute data or fallback predictions. The protocol and
generated configs are committed; private logs, intents and resulting artifacts
remain local and ignored.
