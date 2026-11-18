# Fixed forest decision policy, then untouched final check

**Outcome, 1 November: calibration failed; collection stopped.** Both calibration
visits are usable, but no threshold meets the fixed local rules. No final visits
are needed on2 November or later under this protocol. There is no new policy
bundle or model activation. See the [actual result](#actual-calibration-result-stop).
The sections below preserve the declaration and collection history.

A later [read-only diagnosis](youtube-failure-diagnosis.md) finds size sensitivity
coinciding with an IPv4/1250-byte to IPv6/1230-byte shift. Abstract size-only
metadata swaps change model answers strongly. This does not repair or reopen
the failed calibration, alter its thresholds or authorize final recordings.

This workflow freezes the selected forest
`bd79923fabc4816cc2f15b4f150a5d3b428663c455d0fde3da6ab219eb666d62`.
It fits an answer/withhold threshold, not new model weights or a probability of
being correct. The completed four-visit comparison stays sealed and cannot be
reused for calibration or final scoring. All earlier local calibration records
remain excluded. No model activation follows automatically.

The [declaration](../configs/forest-policy-calibration-v1.json) is pinned by
LF-canonical SHA-256
`3f8cc1029137439d2a3a82563ea1c6b462019a4d03587dbc3777dc1499f1d693`.
Its four new slots, each with one deliberate capture attempt, are:

| Order | Slot | Role | Schedule |
| --- | --- | --- | --- |
| 1 | `forest-cal-ig-01` | Calibration | Feed 30s, Reels 30s |
| 2 | `forest-cal-yt-01` | Calibration | Different video 60s; same local date as slot1 |
| 3 | `forest-eval-yt-01` | Final check | After successful policy freeze, on a later local date |
| 4 | `forest-eval-ig-01` | Final check | Same local date as slot3 |

If an attempt is unusable or no calibration threshold passes, stop. No extra
recording, changed threshold grid, seed, model, support/error gate or calibration
role conversion is permitted automatically. The final pair stays blocked until
calibration succeeds and a complete policy bundle is frozen. Final timestamps
must follow that freeze. Fit never opens final archives/rows; its process audit
hook rejects final, prior local-study, training and public-test reads.

## Fixed policy rules

- Use actual available 10/20/30-packet prefixes. Below10 is insufficient evidence.
  Temperature remains1. Scores/weights/normalization/labels stay unchanged.
- Search a global threshold from0.00 to1.00 in0.01 steps, selecting the lowest
  eligible threshold. This maximizes monotone coverage without a second model
  or hyperparameter search. Equal probability ties use saved label order.
- Require empirical accepted error <=0.10 and coverage >=0.50 overall and for
  each local class. Apply the same constraints separately at the ten-packet
  primary checkpoint, with at least three accepted primary connections per
  class. These support counts refer to unique ten-packet cases, not three
  repeats of one flow. Report all other prefix counts as correlated points.
- As a separate historical control, use the first50 public calibration flows
  per class with >=10 packets, in stored order, and their available checkpoints.
  Require at least30 accepted control points overall, at least5 per public
  class, and accepted error <=0.10 overall/per class. This older period is a
  retrospective diagnostic, not forward local evidence or a new final test.
- Each capture must first pass independent reference/packet QC, with at least
  three target flows reaching10 and one reaching30. All mapped supported flows
  remain archived; only the two declared local classes enter local policy fitting.

No eligible threshold yields an immutable `fitted:false` decision and no policy
bundle. A feasible threshold creates a new complete bundle whose forest bytes,
normalization and class order match the original exactly; only policy/provenance
and its metadata checksum change. The proof binds both calibration archives,
all scored predictions and the full threshold curve. Final preparation/evaluation
revalidates that chain. Stable label-order ties are used only by the new policy;
existing artifacts retain their previous tie behavior.

The final pair is evaluated once at the saved threshold with the same local
coverage/error/primary support rules. Its report cannot overwrite an earlier
result, does not refit anything and does not auto-promote the model. An ineligible
final result stays a failure; do not tune on it and continue calling it untouched.

These are empirical small-sample rules on correlated prefixes, **not a population
error guarantee**. A cutoff such as0.70 does not mean70% correctness probability.
Local checks cover Instagram and YouTube only; other classes have the separate
historical control. Unseen-service detection and general confidence guarantees
are not provided. New-model live-path validation remains separate.

## Commands and files

Use normal Chrome and the rebuilt Edge app side by side. Verify visible
**Reference evidence ON** before each Start, Wi-Fi selected, longer windows off.
Keep Strip private information in Chrome NetLog, raw/sensitive bytes off. Begin
browser logging before Start and new target navigation; stop both logs afterwards.
The helper never starts capture.

```powershell
.venv/Scripts/python.exe scripts/paired_capture.py --plan configs/forest-policy-calibration-v1.json --root artifacts/local/forest-policy-calibration-v1 prepare forest-cal-ig-01
.venv/Scripts/python.exe scripts/paired_capture.py --plan configs/forest-policy-calibration-v1.json --root artifacts/local/forest-policy-calibration-v1 archive forest-cal-ig-01
# After both calibration archives pass:
.venv/Scripts/python.exe scripts/local_policy.py fit
# Only after successful freeze and the later-date final pair is archived:
.venv/Scripts/python.exe scripts/local_policy.py evaluate
```

Repeat prepare/archive for each declared slot, in order, with the same flags.
The generic paired `score` command rejects this workflow; use `fit`/`evaluate`.
`status` uses those flags and reads no candidate scores. Completed raw logs saved
elsewhere can be copied byte-identically with a path/hash sidecar; they cannot
replace missing native capture evidence.

Local output root: `artifacts/local/forest-policy-calibration-v1/`.
Calibration emits `calibration-local-predictions.json`, historical control
predictions, `calibration-curve.json`, `calibration-decision.json` and, only if
feasible, `policy-bundle/`. Final emits `final-predictions.json` and a sealed
`final-report.json`. Loading the exported policy bundle needs no training data.
Original candidate files, previous comparison and B17 app default are preserved.

The constructed end-to-end test fits a tiny fixture forest, forbids final reads
while fitting, checks policy export/weight/probability parity, exercises the
policy-freeze/date gate, evaluates a final fixture pair and rejects refitting or
overwriting its final report. Fixture outputs are explicitly marked and cannot
load in production as real models. No real calibration or final result exists
when this workflow is prepared. User-started recordings are still required.

## Verified preparation

The implementation/declaration were committed as `00c249e` before preparation;
explicit role binding was completed in `b6ded76`. All **363 Python tests pass**,
with lint/format for116 files. Existing dependency deprecation warnings remain.
UI code is unchanged from its seventeen-test/build checkpoint. The fixture path
does not constitute real calibration evidence or a successful final result.

The real-input preflight verifies the candidate metadata/forest checksum and
original processed-data manifest. Every public class has at least50 eligible
calibration flows; no public predictions or threshold search ran. No old local
calibration/comparison rows or public final-test data were opened. The private
`input-preflight.json` records eligible counts and hashes.

`forest-cal-ig-01` is prepared, **not capturing**, at
`2026-11-01T13:02:50.944054+00:00`, with role explicitly `calibration`.
Intent SHA-256:
`2fb743dc068828e11c487955ea52f362ec90fa52f13efb3d6b743205c6f3a6a9`.
A provisional earlier intent with a generic comparison-role label was preserved
before updating that label/time; no capture attempt existed at that update.
`preflight-prepared.json` records the final preparation. No actual calibration
predictions, policy bundle, final intent or final outcome exists yet.

The first NetLog filename is **`forest-cal-ig-01-netlog.json`**; the prepared
destination is
`C:\Users\shrey\NetEmbedAI\traffic_classification\artifacts\local\forest-policy-calibration-v1\forest-cal-ig-01-netlog.json`.
If Chrome keeps its previous folder, retain this exact filename and preserve
the original; the assistant can locate and copy the closed log byte-identically
with a path/hash sidecar before QC. A location correction never substitutes
browser packets for missing native capture evidence.

## First calibration visit archived after processing repair

The same native session `5f1b5e537847404b8e48a0c7b0fe5322` passes the unchanged
reference, within-direction packet, source-replay and support checks. Five mapped
Instagram connections have lengths16,30,30,30,30: thirteen policy prefixes at
10/20/30. No mapped flow was excluded for packet quality. The full inventory
preserves26 ambiguous,12 outside-supported and one unmatched connection.
No candidate policy predictions or fitting have run.

Chrome was still finalizing its log at the first check. The completed raw file,
preserved in the previous Chrome folder, is361,918,926 bytes, SHA-256
`98b25b8f31e8352954af8635fd78d41386d2b6c5dfc45b75664041dfcde90939`.
It exceeded normal retained-event/byte budgets. An explicit **offline expanded
profile** was added: source<=1GiB/8million events, retained<=256MiB/2million
events. Default application budgets remain256MiB/2million source and
64MiB/500,000 retained; all matching/session/anchor/QC/support gates stay fixed.
Every selected reference/socket event is retained, without label, hostname,
time, connection, prediction or outcome filtering. All input lines/footer and
file stability are validated and the projection's semantic inventory roundtrips.

Actual scan:1,822,552 source events,572,084 retained events/121,801,539 encoded
retained bytes. Projection SHA-256:
`ef99fe0bc6955224ccabcd16d1fd978de415b4414371a63f1ca9ef0975a9c227`.
The profile declaration and projection provenance bind the original raw source
and identical native packet snapshot. Parser/profile implementation was recorded
before QC completed; no quality result or model score chose a replacement.

The initial collector prematurely finalized a generic subprocess failure: its
reader used the expanded capacity, but its matcher still checked500,000 combined
events. That software mismatch was fixed and regression-tested. Subprocess
failures now produce a processing-pending diagnostic, not a capture-quality
verdict. Such a pending attempt cannot be replaced with another capture. The
earlier failed receipt remains intact in the original root; it is not relabelled.

A distinct **same-session processing continuation** is active at
`artifacts/local/forest-policy-calibration-recovery-v1/`. It has byte-identical
capture/status/timing/attempt/intent/reference/projection inputs and the exact
same calibration declaration. A sidecar binds the original failure receipt and
correction; no new capture, role, model, threshold or acceptance rule is involved.
The corrected archive SHA-256 is
`39db76d619cba587c8d5bec6dd3b4ea59150b4502de9de221bbe0acbcfecc569`.
All future commands must explicitly use this continuation root:

```powershell
.venv/Scripts/python.exe scripts/paired_capture.py --plan configs/forest-policy-calibration-v1.json --root artifacts/local/forest-policy-calibration-recovery-v1 status
.venv/Scripts/python.exe scripts/local_policy.py fit --root artifacts/local/forest-policy-calibration-recovery-v1
.venv/Scripts/python.exe scripts/local_policy.py evaluate --root artifacts/local/forest-policy-calibration-recovery-v1
```

When needed for a large stopped log, pass `--expanded-netlog` explicitly to the
projector or before the collector's `archive` subcommand. Capacity is propagated
through reader, matcher and socket checks; the recorded limits do not relax QC.
366 Python tests and116-file lint/format pass. Two dependency deprecation warnings
remain. UI code is unchanged from its seventeen-test/build checkpoint. New tests
verify expanded/default capacity, identical matcher output and pending processing
failures. Initial missing fields in the new synthetic error fixture were fixed
before the passing full run; no real capture input was edited by that test fix.

The second calibration slot, `forest-cal-yt-01`, is prepared at
`2026-11-01T14:01:53.078063+00:00`, intent SHA-256
`130bda4475a1664de86c984eab366ce1d141c5d12a84090ceb547c2abd063e0f`.
It must share the first calibration visit's UTC+05:30 date. No capture was
started. `checkpoint-instagram-archived.json` records the verified archive and
next intent. Actual threshold fitting and final collection remain pending.

## Actual calibration result: stop

Both declared1 November calibration visits are now archived in
`artifacts/local/forest-policy-calibration-recovery-v1/`. The YouTube visit is
session `81e7a599b1b94c03bdc2a9a9d2c8d338`, with six mapped YouTube connections
and one mapped WhatsApp connection. All supported mapped records remain in the
archive; the declared two-service policy fit excludes WhatsApp. No mapped flow
failed packet QC. The reference inventory also preserves14 outside-supported,
five ambiguous, four unmapped and four unmatched connections. No queue drops
or reordered packets were recorded. This establishes usable captured evidence,
not full capture completeness or general label certainty.

The raw Chrome file saved in the earlier folder was complete and stable before
being copied byte-identically:22,029,503 bytes, SHA-256
`92b09822fb0b1006e3df2e35538b19723ee1cbcf8a36f735f086c73b458eafa1`.
The path/hash sidecar is retained. No capture was repeated for the folder issue.

The fixed forest and normalization were unchanged. Local fitting used11 unique
connections across two visits and31 available, correlated prefix checkpoints:

| Service | Raw correct at10 packets | Raw correct across10/20/30 |
| --- | --- | --- |
| Instagram | 5/5 | 13/13 |
| YouTube | 3/6 | 7/18 |
| Combined | 8/11 | 20/31 |

These raw counts accept every top-ranked label for diagnosis. They are not
accepted-label deployment accuracy or independent31-trial evidence. At every
declared threshold retaining at least three YouTube ten-packet cases and50%
coverage, YouTube accepted error is at least50%, exceeding the fixed10% cap.
Thus **no threshold satisfies even the local rules**, regardless of public
control. At0.50, only1/18 YouTube prefix cases survives and that prediction is
wrong; at0.60 none survives. These example cutoffs are descriptive, not selected
policies or new tuning candidates.

The separate historical control uses500 connections, first50 eligible per class
in the saved calibration order, yielding1,058 prefix cases. Its own constraints
pass at0.69 through0.84 inclusive, but local constraints pass nowhere on the101-
point grid. Benchmark confidence behavior does not rescue local coverage.

The actual fit completed at `2026-11-01T14:12:58.557278+00:00`, with `fixture:false`,
`fitted:false`, `selected:null`, `policy_artifact_id:null`, `default_promoted:false`.
There is **no `policy-bundle/`**. The stored1.0 threshold is an unfitted-policy
sentinel, not a selected cutoff or exported model. Final policy validation
rejects this decision; neither final slot is prepared. The frozen stop rule
means no extra recordings, relaxed gates or retuning in this protocol.

A fresh process replayed all1,089 saved local/public vectors with maximum
absolute difference0.0. Independent counting matched every aggregate in all101
grid points, including the failed local constraints. The audit uses the same
saved forest predictor, so it checks reproducibility and independent aggregation,
not an independent implementation of the classifier. Its audit guard excludes
prior local studies, training, selection, public test, final records and network
connections. No final data exists or was used. It also verifies archive/output
checksums and that final policy loading fails. This does not identify why the
YouTube batch differs from earlier visits; poor transfer or changed traffic
composition remain possible explanations, not demonstrated causes.

| Evidence file in the active root | SHA-256 |
| --- | --- |
| `forest-cal-yt-01-archive.json` | `2579da65f5570cbb9b8e3568c2f2b35f287610b72163477d80742dcdcfdbc8df` |
| `calibration-local-predictions.json` | `15688e789b9bd26afa2ee52ab55cd9ce2510c8788d6d0d4cc287c8872ab86453` |
| `calibration-public-predictions.json` | `9d377c57f39ddd5be4d6ee2d6e44b8aadd5fefc0287a4c5fec72cc8f043e6e5f` |
| `calibration-curve.json` | `38821d6501086e32d678ee162659fde9ad995e01dd89b48dd567ee87e5bd0f75` |
| `calibration-decision.json` | `881a1d846932a8d31040195514beaec767bcf0be9b44d1b42f16ae764ef594b5` |
| `independent-calibration-audit.json` | `3bfd32b547353e55f9b3605b75e05642d8da9a87d1b849b63bb3b72576206912` |

Fit source commit: `d9bc4890a07e98a9857e31a103a646e1f4c30c5b`, module SHA-256
`f12b7e75cd5b4c925630fa3251b98ae292fe87d49347fb113aaaa7b15cd546d7`.
Private audit script: `experiments/forest-calibration-engineering/audit-fixed-policy-result.py`,
SHA-256 `c1d57d24b07251f9c585c49d5ce977ffc132bac2fe346d145c9e3fdcae04acbb`.
Original candidate, plan, comparison and both calibration receipts remain sealed.
Only documentation changes accompany this result; the previous full suite is366
passing Python tests,116-file lint/format, and the unchanged UI checkpoint is17
tests plus production build. No hosted CI or cross-platform run is claimed.
For this result, the focused calibration/collection contracts were rerun:
`pytest tests/test_local_policy.py tests/test_paired_study.py -q` —18 passed.
`git diff --check` passed. Read-only service checks confirm capture stopped and
the model identity remains B17 (`18c43fe12262b81d4a3001df150a278865f3908ddd3aab934822fc0c9e5750fb`).

Read-only inspection (repository working directory):

```powershell
Get-Content artifacts/local/forest-policy-calibration-recovery-v1/calibration-decision.json
Get-Content artifacts/local/forest-policy-calibration-recovery-v1/independent-calibration-audit.json
.venv/Scripts/python.exe scripts/paired_capture.py --plan configs/forest-policy-calibration-v1.json --root artifacts/local/forest-policy-calibration-recovery-v1 status
```

The recorded fit command earlier in this guide generated the saved decision
once; rerunning it refuses to overwrite. The audit script similarly preserves
its output. Replay in a separate copy with that copy's audit output absent;
do not remove or alter the original evidence. The operational limitation remains
unresolved: the forest cannot yet provide a useful, empirically supported local
confidence policy. The app retains B17; this result does not validate B17 locally.
