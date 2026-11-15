# Fresh-session paired comparison

This separately declared study evaluates the frozen four-head model and the
latest forest on four future user-started recordings. It preserves the failed
development nonregression gates and does not promote either model. No fitting,
calibration, protected old evaluation data or automatic capture is involved.
The app continues to display B17; its displayed guesses must not guide activity.
Candidate scores are produced offline only after all four visits are archived.

The [fixed protocol](../configs/prospective-paired-v1.json) has LF-canonical SHA-256
`42a885ede594ce523bc3f2b35d223b4806683ffa6fd94dd5c21dea8322821d7f`.
It binds the complete candidate metadata identities: four-head model
`483dcd5ea9af2dce2da16c818ee73341f1eb328a032ad56a192c32b7f552e7dd`
and latest forest
`bd79923fabc4816cc2f15b4f150a5d3b428663c455d0fde3da6ab219eb666d62`.
Each loader verifies its component checksums. Prefix inference imports its
bundled pinned wheel. The initial fresh comparison does not erase earlier failures.

| Order | Slot | Activity | Date |
| --- | --- | --- | --- |
| 1 | `paired-ig-01` | Instagram feed 30 seconds, then Reels 30 seconds | First local date |
| 2 | `paired-yt-01` | A new YouTube video, watch 60 seconds | Same date as slot 1 |
| 3 | `paired-yt-02` | A different YouTube video, watch 60 seconds | Later local date |
| 4 | `paired-ig-02` | Feed 30 seconds, different Reels 30 seconds | Same date as slot 3 |

Dates use UTC+05:30. Archive each slot before preparing the next. Every slot
allows one stopped session; unusable evidence closes the study without replacing
the recording. Missing NetLog may be supplied for the same bound attempt.
Already stopped unrelated evidence is preserved separately and excluded before
preparation. A helper cannot prevent arbitrary manual Start presses; following
the sequence matters. Capture is always started deliberately by the user.

## Recording instructions

Use normal Chrome for the target activity and keep the Edge app visible beside
it. Close other Chrome tabs playing media or generating traffic. The app at
http://127.0.0.1:8001 stays in Edge. Select Wi-Fi, enable the reference checkbox,
leave longer-window statistics off, and use the two-minute capture cap.

1. Wait until the slot has been prepared. The helper prints its exact NetLog path.
2. In Chrome open `chrome://net-export`. Keep **Strip private information**;
   leave sensitive/raw-byte options off. Start logging to the prepared path.
3. Press **Start** in the Edge app. Then open a fresh target tab and perform the
   slot's activity for 60 seconds. Keep both windows visible.
4. Press **Stop** in the app and **Stop Logging** in Chrome. Tell the assistant
   “saved and stopped.” Archive before starting another session.

For slot 1 the exact Chrome log destination is:

```text
C:\Users\shrey\NetEmbedAI\traffic_classification\artifacts\local\prospective-paired-v1\paired-ig-01-netlog.json
```

The trial name describes activity only. Ground truth comes from the independent
browser matcher and socket-prefix QC. All mapped supported flows are retained;
ambiguous, unmatched and feature-excluded inventory remains recorded. Other
supported classes remain saved, but the two-service comparison does not score
them. There is no exclusion based on model correctness or confidence.

## Checks and analysis

The collector freezes raw capture/timing/status before QC, validates the genuine
stopped session against its pre-capture intent, checks source-model replay and
reference hashes, and uses the existing fixed feature eligibility rule.
Duplicate sessions, wrong date/order, old captures, drops and evidence eviction
fail the study. Each visit needs at least three independently referenced target
flows reaching ten packets and one reaching thirty. A missing support target
produces an inconclusive stopped study, not a request to keep recording until
predictions look good. Packet parity remains within-direction browser-socket
evidence, not full independent merged wire-order truth.

Both frozen candidates receive exactly the same eligible packet prefixes.
The primary endpoint is ten packets: average each independently referenced
class's recall equally across visits containing it, then average the two class
recalls. Report both models, their paired difference and per-visit counts.
Five/twenty/thirty-packet results are secondary. Withheld accepted labels are
reported separately from raw top-ranked predictions; neither candidate has a
new local confidence calibration.

The descriptive screen requires complete usable coverage, candidate primary
score at least as high as the forest and both candidate primary class recalls
at least 0.80. It does not establish statistical noninferiority, broad local
accuracy, calibrated reliability or authorize model promotion. Two visits per
service provide only an initial independent check. Any later tuning consumes
this data as development and requires fresh evaluation again.

Commands from the repository:

```powershell
.venv/Scripts/python.exe scripts/paired_capture.py prepare paired-ig-01
.venv/Scripts/python.exe scripts/paired_capture.py archive paired-ig-01
# Repeat prepare/archive in declared order; slots 3 and 4 require a later date.
.venv/Scripts/python.exe scripts/paired_capture.py score
.venv/Scripts/python.exe -m pytest tests/test_paired_study.py -q
```

The scorer refuses incomplete sets and existing comparison output. Artifacts,
raw snapshots, independent references, QC, inventories and immutable archives
stay under `artifacts/local/prospective-paired-v1/`. Once available,
`paired-predictions.json` stores both raw probability vectors per case and
`comparison.json` binds archives, models, protocol and predictions by checksum.
No candidate scores or quality results exist at preparation time. Actual capture
and independent comparison remain pending the user's four deliberate sessions.

Preparation verified: `paired-ig-01` was prepared at
`2026-10-31T09:52:38.829080+00:00` without starting capture. Intent SHA-256:
`3c79f7b87684a1f0c95f2123e65caaa2ccf6add8c4b2981728e5087d0a826c2b`.
The stopped session `a5622c24f766491685dfc1357bd6fbb7` was preserved in the
excluded-prior folder. Both real candidate bundles loaded and produced valid
ten-class probabilities while withholding accepted labels on an existing
standalone example. This smoke check does not score prospective data.
`preflight.json` records the checks and artifact bindings. All 348 Python tests
pass, including five new study tests; lint and formatting pass for 112 files.
The two existing dependency deprecation warnings remain. UI code was unchanged.
Actual new-session archival and the four-session comparison remain pending.

## Collection checkpoint 1 of 4

`paired-ig-01` is archived as usable, session
`9cf660e92a89430bb87233c28b966f17`. Eight mapped Instagram connections pass
the fixed feature checks: lengths 20 and seven at 30, giving 31 available
prefix cases. No mapped flow was excluded for packet quality. The full inventory
also retains 23 ambiguous connections, nine outside the supported set and three
unmatched; those are not assigned Instagram merely from the intended activity.
Drops, reordered inputs and stderr counters are zero; the session stopped at
the duration limit. Source replay and within-direction packet checks pass.
No candidate-model scores have been generated or inspected.

Archive raw SHA-256:
`e7e8685ebbcc03c89303d19b6b48f33e92e7f32947652bf33f91ea4936dd6489`.
The archive binds all ten input/evidence files by hash. `checkpoint-01.json`
records the independently rechecked hashes, counts and next preparation.

`paired-yt-01` was prepared at `2026-10-31T10:05:59.318910+00:00`, without
starting capture. Its intent SHA-256 is
`0829038cbb19ad8419b3cbbab8e90544c18d4ae397b8341427e7c6b6c9fa50a2`.
It must be recorded on the same UTC+05:30 date as slot 1. The log destination is
`artifacts/local/prospective-paired-v1/paired-yt-01-netlog.json`. The next two
slots remain reserved for a later local date. This is collection/QC progress,
not prospective model-quality evidence. No source code changed for this archive;
the 348-test/112-file lint checkpoint retains its scope.

## Finalized-log technical continuation

The first YouTube packet session is `8cf6a723c11d40ae88b551d10fb98e35`.
Its initial archive invocation occurred while Chrome was still logging and
incorrectly wrote `unusable_stop` for an unterminated JSON export. The log
continued growing after that receipt, so that receipt's provisional log hash
does not describe the final file. The original receipt and raw packet snapshot
are preserved; the original root is stopped, not silently rewritten as usable.

After the user stopped Chrome logging, the final log was 556,149,205 bytes,
above the default 256 MiB source limit. A separately committed, pre-QC technical
continuation is declared in
`configs/prospective-paired-log-recovery-v1.json`. It permits reprocessing this
same stopped packet attempt, not an extra capture. Candidate artifacts, slots,
dates, support/QC, primary endpoint and scoring embargo remain the same. Any
actual QC/support failure still stops collection. Candidate outcomes have not
been inspected to choose this recovery.

The explicit offline `scripts/project_netlog.py` scans up to 1 GiB/eight million
events. It retains every event of the same existing QUIC-reference and UDP-socket
types, with no time, hostname, connection, activity or prediction filtering.
Default application limits and the 64 MiB/500,000 retained-event limits remain
unchanged. Every line and footer is validated; file changes during reading are
rejected. Re-reading the projection verifies its retained event inventory exactly.
An unfinished/oversized browser log now leaves a bound capture pending before
capture-quality assessment, rather than prematurely finalizing an unusable result.

The actual full scan read 2,701,915 events and retained 226,586 events, with
39,797,978 encoded bytes in the retained inventory. Full source SHA-256:
`cec1083c0a4e1fc3528181d326f04e20158a0102673fc42bb5180bbaca58d782`.
Projected file SHA-256:
`2a4fbaa7d4ab7a8fc8ac61a34b3bc06a8637db46241ddba59384de6a1d7b46f5`.
Original and projection provenance is saved in
`experiments/prospective-paired-engineering/youtube-final-projection.provenance.json`.

Continuation receipts live in the distinct root
`artifacts/local/prospective-paired-log-recovery-v1/`. The first usable Instagram
archive and its inputs are byte-identical copies. The YouTube capture, status,
timing, attempt and pre-capture intent are also byte-identical; only the completed
NetLog's type projection is the derived reference input. A continuation sidecar
binds the original failed receipt, finalized raw log, declaration and projection.
It is included in the new archive's checksums. Future commands must explicitly
use the continuation root:

```powershell
.venv/Scripts/python.exe scripts/paired_capture.py --root artifacts/local/prospective-paired-log-recovery-v1 archive paired-yt-01
# On the later local date, after slot 2 passes:
.venv/Scripts/python.exe scripts/paired_capture.py --root artifacts/local/prospective-paired-log-recovery-v1 prepare paired-yt-02
```

This is a transparent technical amendment after an input-finalization failure;
it does not erase the original stop or count a second packet attempt as slot 2.

### Continuation checkpoint: two usable visits

The recovered same-session YouTube archive passes all unchanged reference,
within-direction packet, replay and support checks. All three eligible YouTube
connections reach thirty packets, giving twelve available prefixes. No mapped
flow was excluded for packet quality. The complete inventory also preserves ten
ambiguous, eleven outside-supported, two unverifiable, three unmapped and seven
unmatched connections. These are not assigned target labels from user activity.

The new YouTube archive SHA-256 is
`820f90c7e5c2ad7959df83cd5ce8d5fcffb572a4aab7453f05d191ad554b3173`.
Its eleven evidence files include the technical-continuation declaration and
full-source/projection provenance. The copied Instagram archive retains exactly
`e7e8685ebbcc03c89303d19b6b48f33e92e7f32947652bf33f91ea4936dd6489`.
`checkpoint-02.json` in the continuation root independently rechecks both
archives, records support and confirms no candidate prediction/comparison files.

Two of four visits are now usable. The earliest next local date is
**1 November 2026** (UTC+05:30); the current-date stage check rejects slot 3.
Neither next slot is prepared or capturing. On that later date use the
continuation root to prepare `paired-yt-02`, then archive it before preparing
`paired-ig-02`. No extra or replacement capture was used for this recovery.
No candidate scores, model fit, policy or promotion were produced.

All **351 Python tests pass**, including regression checks that unfinished logs
leave the same attempt pending, explicit larger source budgets preserve retained
event limits, and projection round trips preserve all selected events and bind
the full original hash. Lint/format pass for 113 files. The existing two dependency
deprecation warnings remain; the UI was unchanged and its prior checkpoint was
not rerun. The recovery software/declaration was committed as `00368bc` before
processing the finalized source or checking its references/QC.

### Work completed while waiting for the later date

The read-only status command verifies archive checksums, slot identities,
session/date order and the next collection gate without loading candidate models,
starting capture, creating an intent or writing any study files:

```powershell
.venv/Scripts/python.exe scripts/paired_capture.py --root artifacts/local/prospective-paired-log-recovery-v1 status
```

It was actually run against the continuation receipts: eight Instagram and
three YouTube connections remain verified, slots 3/4 are unprepared, the earliest
next date is 1 November 2026, and no saved comparison exists. The private output
is `experiments/prospective-paired-engineering/status-after-resume-tools.json`.
Using the original stopped root reports its failed integrity state; it does not
silently redirect or replace those records.

An end-to-end test now runs the complete paired scoring path over four small
constructed visits in a temporary directory, with fake test predictors. It
verifies identical packet arrays/checkpoints across both predictors, correct
date/slot traversal, recorded withholding and immutable report output. All
fixture reports are explicitly marked `fixture: true`. This is software evidence
only; neither real candidate nor any actual prospective packet row is evaluated
by this test. The final report also binds the technical-continuation sidecar
when present, in addition to its archive/projection chain.

The full software checkpoint is **353 Python tests passed**, Ruff lint passed
and formatting passed for 113 files. The two existing dependency warnings remain.
UI code was unchanged, so its existing sixteen-test/build checkpoint was not
rerun. No hosted CI run or untested-platform result is claimed. No new model,
policy, recording or candidate outcome was produced while waiting. Remaining
independent-quality/live-path evidence is still listed in the release checklist.

### 1 November preparation

The actual read-only status revalidated both saved archives and reported
`ready_to_prepare`. Slot 3, `paired-yt-02`, is now prepared in the continuation
root at `2026-11-01T11:36:02.541382+00:00`, with capture stopped and B17 still
the source app model. Intent SHA-256:
`3cd3faf7f9e4eac6597ad6c8ff3bb662280221f1a8f20e7df4de3498ba12e429`.
The private `checkpoint-03-preparation.json` records this preparation.
Its Chrome log destination is
`artifacts/local/prospective-paired-log-recovery-v1/paired-yt-02-netlog.json`.
No new capture or candidate scoring was started. After this visit passes and
is archived, the final Instagram slot must be prepared and recorded on the same
local date. No software changed or tests were repeated for this preparation.

### Third attempt unusable: study stopped

The 1 November session `e3b9a9e7a64644b68e7c4feaa374a52c` had reference
checking off and **zero retained native flow records**. Source model and adapter
match the prepared intent. The Chrome log was found in the previous root and
preserved/copied byte-for-byte, SHA-256
`27f5222ef700d772456cd9d2f0216e691d0c09cde233e5380c06f7e133474df9`.
Fixing its location cannot recover native packets that were never retained;
browser-only reconstruction would not validate the genuine capture pipeline.

The attempt is archived as `unusable_stop`, archive SHA-256
`27bfcadf37d58755c7a5605148201e7fe8ff3484397b0e34bd95f9e5bd91718f`.
`checkpoint-03-outcome.json` records the verified failure and a direct check
that slot 4 is blocked. The one-attempt rule applies: this study/continuation
is **stopped**, with two usable prior visits preserved. No replacement capture,
final Instagram slot or candidate scoring follows automatically. Any later
collection requires a separately declared scope. No candidate quality result
exists from this study; no model, calibration or default change was made.

The UI currently initializes the reference checkbox to off on page reload.
This could explain the setting, but this session's UI actions are not recorded.
Future setup must verify it immediately before Start; enabling it afterwards
cannot restore missing evidence. No source change or test rerun for this archival.
