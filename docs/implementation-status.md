# Implementation status — 6 November 2026

Latest implementation: [public-only refusal policy and runtime integration](ipv6-public-policy.md).
One fixed fit uses only500 CESNET calibration flows/1,058 prefix cases, with
local outcomes and final/train/selection inputs blocked. Threshold0.76 accepts
275/500 ten-packet calibration cases with3 mistakes; YouTube coverage is only22%,
so rejection cost is explicit. The new complete bundle preserves weights,
normalizer and every probability vector, and passes actual API/CLI/direct
checks without dataset access or capture.101 curve points independently recount.
Two1,000-call CPU checks measure1.122/2.067ms p50/p95 at ten packets.451 Python
tests,19 UI tests,135-file lint-format and TypeScript/Vite build pass. The UI
distinguishes unfitted policy from low confidence and shows calibration scope.
The candidate is packaged but inactive: B17/current stopped capture unchanged,
and local accepted-error/coverage plus new-model live latency remain pending.

The following entries preserve preceding checkpoints.

Latest completed evidence: [four new frozen-model visits](ipv6-fresh-evaluation-results.md).
All four archives are usable. At ten packets the added-data forest gets22/22
local flows right versus7/22 control; equal-target-visit/class recall is1.0
versus0.462121. All descriptive checks pass.162 vectors reproduce exactly and
eight matrices independently recount with training/prior outcomes/network
blocked. The cohort is22 IPv6 flows from four visits/two dates/two services on
one hotspot, so no broad reliability or calibrated confidence claim follows.
No more recordings for this scope. Both policies remain unfitted and inactive;
B17 stays in the UI. Software checkpoint remains438 tests/132-file lint-format.
The [explicit cmd/native-PowerShell route](windows-command-runner.md) restores
agent command execution; the automatic Store PowerShell launcher still fails.

The following entries preserve preceding checkpoints.

Latest collection: [first-date evaluation pair passes](ipv6-fresh-evaluation.md#first-actual-instagram-visit-and-first-date-completion).
Instagram contributes three IPv6 flows (17/30/30 packets), with clean packet/
browser checks, no mapped exclusions and exact165-vector source replay.
Together with YouTube4 complete flows, two of four evaluation visits are now
usable. Both archives/completion receipts are verified and bound in the
first-date receipt. Capture is stopped. Remaining Instagram then YouTube slots
are unprepared and date-gated to6 November or later. No more recording today,
candidate scores, policy fitting or promotion.438-test checkpoint unchanged.

The following entries preserve preceding checkpoints.

Latest real evaluation collection: [first YouTube visit passes](ipv6-fresh-evaluation.md#first-actual-youtube-visit--usable).
Four verified IPv6 flows all reach30 packets, with no mapped QC exclusions,
clean browser/packet checks and exact99-vector source replay. Archive and
completion checksums are recorded; one of four visits is now usable. The two
forests remain unscored under the all-four-visits embargo. Next is Instagram
after full Chrome exit and preparation; later-date pair remains unprepared.
No fit, calibration, promotion or software change;438-test checkpoint unchanged.

The following entries preserve preceding checkpoints.

Next evidence stage: [four new frozen-model evaluation visits](ipv6-fresh-evaluation.md).
The complete collector/scorer is implemented and tested. First YouTube slot
`ipv6-eval-yt-01` is prepared with Chrome closed, capture stopped, source B17
unchanged and current dual-family reachability verified. Capture remains
user-started. Primary results wait for all four usable visits across two dates;
no candidate scores, confidence fitting or activation have occurred.438 Python
tests and132-file lint/format pass. The old training slots remain paused.

The following entries preserve preceding checkpoints.

Latest completed work: [one matched real-data retraining pilot](ipv6-realdata-pilot.md#actual-outcome).
The original control weights reproduce exactly. Adding all 19 verified IPv6
training flows raises reused local mean-budget macro-F1 from 0.780557 to 0.983806
and ten-packet raw correctness from 12/17 to 17/17. Both services improve and
all five declared local/public retention gates pass. Public F1 is 0.894825
versus 0.896904. All 4,126 vectors replay exactly; 16 matrices independently
recount. 424 Python tests and 130-file lint/format pass. Candidate inference
bundle and complete evidence are saved locally. No confidence policy, fresh
forward evaluation, model activation or replacement-model live validation is
claimed. B17 remains in the app; remaining three acquisition slots are paused.
Earlier instructions to continue acquisition below are historical checkpoints.

The following entries preserve preceding checkpoints.

Latest acquisition: [YouTube session2 passes](fresh-browser-sessions.md#second-youtube-visit-archived--5-november).
Seven YouTube/IPv6 flows all reach30 packets. Packet/reference/restart checks
pass, no mapped exclusions, and134-vector source replay is exact. Three of six
planned visits are usable. Next Instagram2 needs a new Chrome exit/intent, then
YouTube3/Instagram3 on the same later date. No new fit/evaluation/promotion;
412-test software checkpoint unchanged.

The following entries preserve preceding checkpoints.

Latest acquisition: [both first-date visits pass](fresh-browser-sessions.md#first-instagram-visit-and-first-date-completion).
IG contributes four IPv6 flows (16,30,30,30 packets) plus two incidental30-packet
YT flows. Fresh Chrome, packet/reference QC and191-vector source replay pass.
The372MB log required the already declared expanded offline resource profile;
no quality gate or event-selection rule changed. Two planned sessions are now
usable. Remaining four wait for one later date,5 November or later; no more
recording today and no further intent is prepared. No new fit/evaluation/default
promotion.412-test software checkpoint unchanged; browser may now be closed.

The following entries preserve preceding checkpoints.
Latest actual session: [fresh YouTube passes](fresh-browser-sessions.md#first-youtube-visit-archived).
Six YouTube/IPv6 flows all reach30 packets and pass packet/reference/source-replay
and Chrome-lifetime checks, with no mapped exclusions. One of three planned
YouTube visits is archived; next is separately prepared Instagram after Chrome
exit. No model fit or quality evaluation.412-test software checkpoint unchanged;
no further intent or capture is started automatically.

The following entries preserve preceding checkpoints.
Latest revision: [fresh-browser acquisition](fresh-browser-sessions.md) replaces
incidental within-video flow yield with six fixed visits, three per service over
two dates, each requiring one complete verified IPv6 flow. New plan only; earlier
failed receipts/thresholds remain intact. Preparation requires Chrome fully closed;
archive checks process starts after intent and before capture.412 tests pass,
including a native Windows query;127-file lint/format pass. An initial query
formatting bug was corrected before use. Hotspot IPv6 recheck passes. No first
intent or capture is prepared while Chrome remains open. No fit/scoring/promotion.

The following entries preserve preceding checkpoints.
Latest actual hotspot visit: [two real IPv6 QUIC connections](hotspot-family-feasibility.md#first-actual-user-started-visit)
are browser-matched YouTube, each30 packets, with unique sockets and clean
within-direction packet QC. Source replay matches80 saved predictions exactly.
The declared support minimum is3 at10 packets; only2 were captured, so the
immutable receipt stops the scope. A bound post-archive family diagnostic
confirms IPv6 without changing eligibility. Acquisition is physically observed;
the single-video collection instruction did not guarantee the required sample
count. No replacement/Instagram intent, training or promotion follows.406-test
software checkpoint unchanged. Acquisition design needs review before more visits.

The following entries preserve preceding checkpoints.
Latest network: [mobile hotspot IPv6 works](hotspot-family-feasibility.md).
Global IPv6 addresses/default route and both-family TCP443 reachability pass.
A separate two-visit acquisition-feasibility scope is implemented; the first
YouTube intent is prepared without capture. Each visit requires verified IPv6
QUIC support; no fit, freeze, scoring or activation follows the pair. Stopped
campus study stays closed.406 tests/125-file lint/format pass. Actual hotspot
QUIC acquisition remains pending the user's deliberate Start. B17 stays default.

The following entries preserve preceding checkpoints.
Latest inspection: [gateway/client IPv6 status](router-ipv6-inspection.md).
Gateway public pages identify an institution-branded24Online user login, with
no exposed WAN IPv6 status. Client Router Discovery is enabled; no IPv6-disable
registry override was found. Router model/upstream ISP/configuration remain
unverified. An authorized network administrator's IPv6 provisioning/advertisement
status is needed next. No credentials, configuration change, capture or new
training; previous application test checkpoint unchanged. Collection stays closed.

The following entries preserve preceding checkpoints.
Latest network check: [IPv6 currently unreachable](network-ipv6-check.md).
Wi-Fi has only link-local IPv6, no global IPv6 address and no listed IPv6 default
route. YouTube advertises eight AAAA records; IPv4 TCP443 connects and explicit
IPv6 TCP443 fails Windows10051/NetworkUnreachable. Read-only native/.NET checks
and bounded probes ran without capture or configuration changes. Router/ISP
cause remains unverified. The stopped collection is not repeated on this network;
model quality remains unresolved. Script parsing and evidence-preservation checks
pass; previous403-test application checkpoint is unchanged.

The following entries preserve preceding checkpoints.
Latest actual visit: [family collection stopped](family-coverage-plan.md#first-visit-valid-recorded-metadata-ineligible-family-coverage).
Five verified YouTube flows each reach30 packets and pass browser/socket and
native source-replay checks, but every matched socket is IPv4. Required IPv6
support is0/3 at10, so the frozen first slot is ineligible and the scope stops.
This is no recording mistake and does not prove global IPv6 unavailability.
Raw evidence and the immutable receipt are saved; no replacement, later intent,
fit or deployment follows.403-test software checkpoint remains unchanged.

The following entries preserve preceding checkpoints.
Latest engineering: [family-aware collection](family-coverage-plan.md) now
enforces one attempt, packet QC, IPv6 training support, four-cell selection
coverage, relative dates and immutable training/model binding. Generic scoring
is disabled; selection waits for the later new-data trainer stage.403 Python
tests pass and124-file lint/format pass. No capture was started. The first
YouTube training intent is the next user-action boundary; no new model or
real-family quality result exists. UI unchanged and B17 remains the app model.

The following entries preserve preceding checkpoints.

Latest: [family coverage audit](family-coverage-audit.md) completes all eleven
existing train/selection visits. Training:22 IG/IPv4 and21 YT/IPv4, no IPv6.
Selection:7 IG/IPv6,5 YT/IPv6 and5 YT/IPv4, no IG/IPv4. No endpoint identity
enters prediction. The [new bounded plan](family-coverage-plan.md) reserves at
most four training and four later selection visits, with explicit family/QC,
date, isolation and stopping gates. It is a plan, not implemented collection
enforcement: no first capture intent is prepared and no recording is requested.
Family-aware preparation/archive checks are the next implementation task.
Original failed studies remain closed; no retraining or activation occurred.

The following entries preserve preceding checkpoints.

Latest completed study: [matched size robustness](size-robustness-study.md).
Clean seed17 refit exactly reproduces original weights. Size jitter changes
local clean/stress F1 from0.780557/0.657581 to0.823198/0.852214, but loses clean
IG recall, public clean F1 and class retention. Relative size gives
0.756676/0.769799 with severe IG regression. Neither qualifies under fixed gates.
The study is closed: no42/123, selected candidate, policy, benchmark or activation.
Training uses original14k public+43 local rows; assessment uses reused17 local
development connections and500 historical public flows. Failed calibration,
paired comparison, diagnostic captures and public calibration/final stay excluded.
Independent fresh-process replay matches all18,567 vectors exactly and recounts
72 matrices.395 Python tests and121-file lint/format pass; two dependency
deprecation warnings remain. UI unchanged. B17 stays in the stopped capture app.
The initial Windows IPC permission failure and identical-input retry are preserved.
These single-seed/abstract-stress results do not establish real IPv6 quality.

The following entries preserve preceding checkpoints.

Latest diagnosis: [YouTube size/path sensitivity](youtube-failure-diagnosis.md).
All seven earlier matched YT connections use IPv4/1250-byte starts; all six
failed-batch connections use IPv6/1230-byte starts, confirmed by browser sockets.
All39 saved vectors replay exactly. Abstract size-only swaps improve failed10-
packet predictions3/6→6/6 and damage earlier ones7/7→1/7. Tree traces expose
repeated server-max-size splits at1241 bytes. All21 original local YT training
examples begin1250 (as do22 IG); public training/final records remain unopened.
Browser event order/timing replay does not repair recognition. This identifies
a concrete model sensitivity, not a real-world causal proof or validated fix.
No new model, threshold, capture or activation.375 Python tests and118-file
lint/format pass, with two known dependency deprecation warnings. UI unchanged.

The following entries preserve preceding checkpoints.

Latest outcome: [fixed forest calibration stopped](forest-policy-calibration.md#actual-calibration-result-stop).
Both visits pass capture/reference QC: five Instagram and six YouTube connections
enter policy fitting. At ten packets the unchanged forest is correct on 5/5 IG
and 3/6 YT; across correlated available10/20/30 checkpoints it is13/13 and7/18.
None of101 declared thresholds meets local constraints, independently of the
historical public control. The immutable decision is `fitted:false`, with no
exported policy, final preparation or default promotion. All1,089 probability
vectors replay exactly in a fresh process; all101 grid points independently
recount. No further recordings under this protocol, including on2 November.
B17 remains in the stopped capture app. The full-suite software checkpoint stays
366 Python tests/116-file lint/format; this result changes documentation only.

The following entries preserve preceding checkpoints.

Latest calibration collection: [Instagram's same native session](forest-policy-calibration.md)
is archived as usable after a transparent processing repair. Its large closed
Chrome log required an explicit bounded expanded reader/matcher profile; default
budgets and QC/support/policy rules remain unchanged. Original failed receipt is
preserved. Five matched IG connections yield13 available policy prefixes. Use
`artifacts/local/forest-policy-calibration-recovery-v1` for future workflow commands.
YouTube calibration is prepared without capture, for the same local date. No
threshold fitting, candidate policy or final capture exists. 366 Python tests
and116-file lint/format pass. Subprocess failures now stay processing-pending
rather than falsely finalizing capture quality. B17 remains in the app.

The following entries preserve preceding checkpoints.

Latest preparation: [fixed forest policy calibration](forest-policy-calibration.md)
is implemented. Two fresh calibration visits precede any threshold fitting;
two later-date final visits stay blocked until a successful policy freeze.
The threshold grid, empirical coverage/error/support rules and failure stop
are fixed. Fit excludes final/prior local/training/public-test reads. Successful
export keeps weights/normalization/class order unchanged; final evaluation cannot
refit or overwrite. 363 Python tests and 116-file lint/format pass, including a
constructed end-to-end calibration/export/final fixture. Real-input support
checks pass without prediction; first Instagram calibration is prepared, not
capturing. Actual policy fit/final outcomes remain pending user-started visits.
The completed comparison remains sealed; B17 is still the app model.

The following entries preserve preceding checkpoints.

Latest engineering: [single-flow forest inference](forest-runtime-and-next-stage.md)
now avoids per-branch numpy allocation. All 85 sealed forest probability vectors
remain exact; weights, policy and artifact identity are unchanged. Alternating
before/after calls reduce ten-packet p50 from 27.66 to 3.13 ms on the fixed input.
355 Python tests/113-file lint/format pass. The forest is preferred for the next
two-service calibration stage after its primary quality tie, subject to fresh
policy/final evidence. No calibration or new capture is prepared; B17 stays in
the app. Completed comparison records remain sealed.

The following entries preserve preceding checkpoints.

Latest result: the [paired fresh-session comparison](prospective-paired-followup-results.md)
is complete on 22 connections/four visits/two dates. The primary ten-packet
endpoint ties: both models 20/22 correct, balanced mean visit recall 0.93304,
YouTube 1.0 and Instagram 0.86607. The descriptive screen passes. Neural is
better at five packets, forest at twenty; both get 20/20 at thirty on this small
sample. All 170 saved vectors replay exactly in an independent audit. No policy
is fitted; all candidate accepted labels are withheld, and B17 remains in the
app. No new candidate live-path validation or broad accuracy claim. Full hashes,
CPU measurements and limitations are recorded. No more collection is requested
under this completed protocol. The preparation software checkpoint remains
354 Python tests/17 UI tests/build/lint/format; no source change for this result.

The following entries preserve preceding checkpoints.

Latest collection: the [explicit follow-up YouTube visit](prospective-paired-followup.md)
is archived and usable: four matched thirty-packet connections, no mapped QC
exclusions. Its Chrome log was located in the previous folder and preserved/copied
byte-identically. Three of four visits are usable. The final Instagram slot is
prepared without capture and must use the same local date. Both candidate models
remain unscored until the complete set. No source change or software test rerun.

The following entries preserve preceding checkpoints.

Latest preparation: [explicit paired follow-up](prospective-paired-followup.md)
inherits the two usable visits by immutable hashes and allows two new sessions,
preserving the stopped original study. A new YouTube slot is prepared without
capture. Use `--plan configs/prospective-paired-followup-v1.json --root
artifacts/local/prospective-paired-followup-v1` for this new scope. The visible
reference ON/OFF message and per-tab refresh-stable opt-in are built and served.
354 Python tests, 17 UI tests, production build and formatting/lint pass.
Candidate weights, QC, endpoint and embargo remain fixed; no new candidate scores.

The following entries preserve preceding checkpoints.

Latest outcome: the [third prospective attempt](prospective-paired-study.md)
is unusable and the frozen comparison is stopped. Reference checking was off,
so no native flow records were retained. The Chrome log was located in the
previous folder and preserved/copied, but browser evidence cannot replace
missing native packets. Two usable prior visits remain. Slot 4 is blocked;
no replacement or scoring is authorized by this study. No source change or
test rerun for this archival. B17 remains the app default.

The following entries preserve preceding checkpoints.

Latest preparation: the [prospective study](prospective-paired-study.md) date gate
is open. Both prior continuation archives revalidate, and `paired-yt-02` is
prepared without capture or candidate scoring. The final Instagram slot remains
unprepared until this YouTube visit is archived. Both day-two visits must use
the same local date and the explicit log-recovery continuation root. The latest
software checkpoint remains 353 tests/113-file lint/format; no source change.

The following entries preserve preceding checkpoints.

Latest independent engineering: added a read-only paired-study status command
and end-to-end scoring test on four constructed fixture visits. The actual
status audit rechecks the two usable continuation archives, confirms slots 3/4
are unprepared and date-gated, and reads no candidate outcomes. The scorer test
checks identical model inputs, fixture labels, withheld decisions and refusal
to overwrite results. Continuation provenance is bound in eventual reports.
353 Python tests plus 113-file lint/format pass. No new recording, training,
calibration or fresh-cohort model score. See the study document for exact commands.

The following entries preserve preceding checkpoints.

Latest checkpoint: [same-session finalized-log recovery](prospective-paired-study.md)
has completed. The growing/incomplete YouTube log initially caused a premature
failed archive, which is preserved. After Chrome logging stopped, a declared
bounded type-only projection scanned the finalized 556 MB source and preserved
all 226,586 reference/socket events without label/time/model filtering. A separate
continuation root retains the identical packet attempt and first Instagram
archive. The same YouTube recording passes QC with three thirty-packet flows.
Two visits are usable; the next two require 1 November or a later local date.
Use `artifacts/local/prospective-paired-log-recovery-v1` for future commands.
Original stopped receipts remain unchanged. Candidate scoring is still withheld.
351 Python tests and 113-file lint/format pass; no new model or policy exists.

The following entries preserve preceding checkpoints.

Latest collection checkpoint: [prospective paired slot 1](prospective-paired-study.md)
is archived and usable, with eight independently matched Instagram connections,
31 available prefixes and no mapped packet-quality exclusions. Ambiguous and
unsupported reference inventory is preserved. Source replay passes; candidate
scoring remains withheld until all four visits. Today's YouTube slot is prepared
without starting capture. Two subsequent slots require a later local date.
No new model fit, confidence policy or promotion. No source changes or software
test rerun for this evidence-only checkpoint.

The following entries preserve preceding checkpoints.

Latest preparation: [fresh-session paired evaluation](prospective-paired-study.md)
is declared and implemented. It freezes the four-head model and latest forest,
uses four deliberate sessions across two dates, and blocks candidate scoring
until all four usable sessions are archived. The primary ten-packet score gives
each visit equal weight within a class. Original failed development gates remain
recorded; this study cannot promote a model or fit a policy. The first Instagram
slot is prepared, not capturing. Prior stopped evidence is preserved separately.
Both real models pass the existing-example smoke test, and 348 Python tests plus
112-file lint/format pass. New capture, archival and prospective scores are pending.

The following entries preserve preceding checkpoints.

Latest result: the [four checkpoint heads](prefix-linear-probe-study.md) complete
the early-prefix experiment. The original 500-iteration attempt stopped unscored;
a separately committed, training-only numerical retry at 2,000 iterations
converged all four heads. Correct development cases improve from 55/63 to 59/63,
mean-prefix F1 from 0.90272 to 0.95120, and five-packet correctness from 11/17 to
16/17. Both class recalls improve against the shared head. Instagram remains
21/24 versus the latest forest's 22/24, so strict nonregression still fails.
Seven of eight checks pass; no policy fit, capture, default promotion or final
evaluation. All 63 probability vectors replay exactly, all four heads work with
datasets blocked, and 343 Python tests/109-file lint/format pass. B17 remains
the service model. This is promising reused development evidence; independent
local quality and new-model live-path validation remain pending.

The following entries preserve preceding checkpoints.

Latest result: the [fixed frozen-pooling linear probe](pool-linear-probe-study.md)
is implemented and evaluated. One converged head uses the official network's
448-value pre-refinement pooled features, frozen encoder and training-only
scaling. It gets 55/63 existing development prefix cases right, F1 0.90272,
versus the latest forest's 47/63 and 0.78056. YouTube recall improves to 0.925,
but Instagram recall is 0.80714 versus the latest forest's 0.92857, failing the
frozen nonregression gate. No default promotion, new capture, protected data,
calibration or final evaluation. Both earlier collection studies remain closed.

The bundle includes the encoder, optional wheel, head, preprocessing and
provenance. Fresh-process replay exactly reproduces all 63 saved local vectors;
a separate all-dataset-blocked check verifies standalone inference. Trained CPU
p50/p95 are 23.79/26.49 ms for the fixed 30-packet example, excluding capture/UI.
331 Python tests and lint/format for 104 files pass. The source/protocol were
committed as `4e884a7` before fitting. Full scores, hashes, commands and limitations
are in the study document. These reused development results are promising but
do not satisfy independent local quality or live-release gates.

The following entries preserve preceding checkpoints.

Latest result: [the one-recording follow-up and fixed seed-17 comparison are complete](browser-selection-followup-results.md).
The valid additional recording contributes five YouTube connections and resolves
the support shortfall. Separate selection now has seven Instagram/ten YouTube
connections and 63 correlated prefix cases across three visits; training stays
22 Instagram/21 YouTube. The new forest gets 47/63 versus the previous forest's
46/63, improving mean-budget F1 from 0.76035 to 0.78056. Instagram recall improves
to 0.92857, but YouTube falls from 0.74722 to 0.64444, failing both its 0.65 floor
and nonregression rule. Best TCN F1 is 0.50797; all candidates are ineligible.
The declared first-seed stop applies: no seeds 42/123, calibration or new capture.
An independent artifact audit exactly reproduces all 504 saved local probability
vectors across eight models and verifies 16,000 public-selection predictions.
All result, provenance, prediction and bundle hashes are recorded. B17 remains
unchanged and capture is off. The blocker is now per-service local model quality,
not missing data support. No new software test run; the 318-test/99-file lint
checkpoint and unchanged UI checks retain their scope.

The following entries preserve preceding checkpoints.

Latest preparation checkpoint: `youtube-dev-05` is **prepared, not capturing**
under the [implemented one-recording follow-up](browser-selection-followup-v1.md).
The actual stopped-service/model check, all ten parent recordings and generated
config comparisons pass. The private preflight proof and intent hashes are
recorded in that document. B17 and every original data role remain unchanged.
No new log, bound attempt, training run or policy exists yet; the remaining
action is the user's single deliberate recording followed by archival.

The following entries preserve preceding checkpoints.

Latest engineering checkpoint: the [single-recording follow-up helper](browser-selection-followup-v1.md)
now supports original per-trial plan/hash bindings, an immutable stopped-attempt
snapshot, preserved unusable attempts, chronology/support guards, and exact
inherited configs. Repetitions cannot rescue seed 17 or change its selected
family/epoch. The read-only real-data preflight verifies all ten parent
recordings, unchanged counts, distinct sessions and the timing gates. Capture
and fitting have not started; the app stays on B17. The original six-session
study remains closed with its recorded shortfall.
All **318 Python tests pass**, with the existing Starlette/AnyIO deprecation
warning; Ruff lint/format passes for 99 active files. The config-generation CLI
ran successfully. UI code is unchanged and retains its sixteen-test/build
checkpoint; no new live quality or latency evidence is claimed.

The following entries preserve preceding checkpoints.

Latest planning checkpoint: the user requested a follow-up after the collection
support shortfall. The [one-recording plan](browser-selection-followup-v1.md)
declares one additional YouTube selection session, retains all existing records
and numeric model/support gates, and binds parent evidence/config hashes. An
unsuccessful attempt ends the follow-up without another capture. Seed 17 runs
only after coverage passes; later fixed seeds cannot rescue an ineligible first
seed or be cherry-picked. No follow-up capture is prepared and the existing
helpers do not yet support the new protocol. Their parent-plan bindings and
limit tests are the next implementation step. No model or capture changes.

The following entries preserve preceding checkpoints.

Latest collection checkpoint: [all six version-3 recordings are archived, but the support gate refuses fitting](browser-development-v3.md#sixth-recording-archived-support-gate-refused-fitting--30-october).
The final YouTube selection recording adds five verified full-prefix connections,
150 packets and twenty available prefix points, with no mapped-flow exclusion
or retained evidence eviction. All 102 saved source predictions reproduce
exactly. Fourteen labelled live events contain thirteen withheld decisions and
one wrong accepted label; six raw top choices match. Browser receipt p50/p95 is
101.59/496.71 ms, not paint time. Selection totals are seven Instagram/five
YouTube connections, with five full prefixes per service. YouTube is one below
the frozen six-connection requirement. The exact experiment runner exited at
its support guard before creating a model output directory or fitting. Training
remains 22 Instagram/21 YouTube; there is no new model comparison, calibration
or promotion. The six-recording cap is reached. No extra recording or relaxed
rule follows automatically, and B17 stays unchanged. This is a documented
data-support shortfall, not a validated release or a model-quality finding.

The following entries preserve preceding checkpoints.

Latest collection checkpoint: the [Instagram selection visit is archived](browser-development-v3.md#fifth-recording-archived--30-october).
Seven independently mapped connections pass the fixed packet checks, including
five complete thirty-packet prefixes, meeting the Instagram selection coverage
minimum. No mapped-flow exclusion or retained evidence eviction; all 146 original
source predictions replay exactly. Of twenty saved labelled live checkpoint
events, fourteen withheld and six accepted incorrectly, with zero raw top-choice
matches. This remains an unchanged-model development diagnosis, separate from
training. Browser receipt p50/p95 is 84.97/480.28 ms, not paint time. Five of six
declared recordings are archived. The training pool stays 22 Instagram/21 YouTube;
only the reserved YouTube selection visit remains before the fixed candidate
comparison can run if its support/chronology checks pass. No fitting, policy
change, promotion or new software test run occurred.

The following entries preserve preceding checkpoints.

Latest collection checkpoint: [all version-3 training recordings are archived](browser-development-v3.md#fourth-recording-archived--29-october).
The YouTube control adds eight independently referenced connections, 240 packets
and 32 available prefix points, without mapped-flow exclusions. All 114 saved
source predictions replay exactly. Of nineteen actually retained labelled live
checkpoint predictions, twelve withheld, two accepted correctly and five accepted
incorrectly; four raw top choices match. Intermediate coalescing and offline
checkpoint counts are distinguished. This is unchanged-model training diagnosis,
not replacement-model evaluation. No queue drops/errors or evidence eviction;
browser receipt p50/p95 is 200.82/504.67 ms over 114 events, not paint time.
The training pool is now 22 Instagram/21 YouTube connections, 43 total. The two
reserved selection visits may begin at 02:38 AM IST or later on 29 October,
after the fixed hour from the latest retained training-prefix packet. The
current-time gate correctly refused early preparation; no new intent/capture,
training, policy fitting or promotion followed. [How capture checks work](capture-checks.md)
explains why valid data and correct predictions are different requirements.

The following entries preserve preceding checkpoints.

Latest collection checkpoint: the [third version-3 recording](browser-development-v3.md#third-recording-archived--29-october)
adds five independently matched Instagram connections, 112 packets and fifteen
prefix points, with no mapped-flow exclusions or evidence eviction. All 94
original B17 predictions reproduce exactly. The current B17 still fails these
Instagram references: ten decisions withheld, five wrong accepted labels and
zero raw top-choice matches across the fifteen repeated points. This is retained
training evidence, not an independent accuracy estimate or a replacement model.
No recorded queue drops/errors; browser receipt p50/p95 is 83.86/476.92 ms over
94 acknowledgements, not paint or a controlled UI latency improvement. The pool
now has 22 Instagram/thirteen YouTube connections over two new Instagram dates.
Minimum counts/date coverage are met, but the declared YouTube training control
and later selection remain pending. The next training control is prepared;
capture is off. No fitting/policy/default change or new software test run.

The following entries preserve preceding checkpoints.

Latest UI checkpoint: the [screen refresh](ui-refresh-20261029.md) improves
capture guidance, friendly interface names, searchable retained connections,
packet/estimate layout, uncertainty wording and responsive styling. Research
options remain explicit and off by default. Replay validation now prevents
malformed packet objects from crashing the view; selection follows retained
rows after eviction. Sixteen UI tests, TypeScript/production build and UI
formatting pass. Actual browser review covers desktop/mobile and genuine
saved-model recorded replay, including invalid-input recovery; no live capture
or new quality/latency evidence follows. Backend/model/threshold/data roles
are unchanged; the preceding 295 Python tests remain the backend checkpoint.
The new build is served on port 8001 and capture is off.

The following entries preserve preceding checkpoints.

Latest independent engineering checkpoint: [Stop, receipt, native windows and CPU stages](engineering-checks-20261028.md)
preserves the first Stop reason, separates session-bound prediction/window
receipts and loads summaries after automatic Stop. A constructed 264-datagram
native TShark fixture checks four encapsulations and complete/partial windows
past packet thirty against an independent oracle. Stalled offline reading now
has a deadline and cleanup regression. B17 stage timing on the existing nineteen-
packet recording measures preprocessing/forward/probability/full-predictor p50
0.449/15.731/0.091/16.258 ms, with full-predictor p95 19.467 ms; probabilities
match exactly. These exclude HTTP/capture/browser timing and are not additive.
295 Python tests, thirteen UI tests, production build and lint/format pass.
The stopped original evidence was verified and preserved before updating the
local service on port 8001. Four actual HTTP/direct prefix predictions match
exactly; new assets and idle timing fields are verified. Capture remains off.
No new data, training, policy fitting or promotion. The [release checklist](release-checklist.md)
keeps genuine new window receipt/paint, full real-window parity, independent
local quality, hosted CI and other-platform verification explicitly pending.

The following entries preserve preceding checkpoints.

Latest fixed comparison: [browser-side longer-window features](browser-window-study.md)
failed both development gates. On the same fourteen legacy selection connections,
the browser prefix control gets 11 correct (F1 0.78462), versus nine for both
one second (0.64103) and three seconds (0.62567). All use seventeen legacy
training connections, two labels and the same fixed forest parameters. Newer
calibration/development/final and the unscored window trial remain excluded.
Numeric artifacts reproduce native probabilities within 1.12e-16; inference
p50/p95 is 1.106/1.747 ms and 1.056/1.868 ms for the window models, excluding
their observation waits and capture/delivery. These browser-observer models
refuse implicit transfer into live capture. No promotion or policy fitting.
The completed full suite passes 264 Python tests and lint/format pass for
90 active files; the preceding UI checks apply to unchanged UI code. A scoped
audit-hook check blocks external files/network after loading inputs and both
window models reproduce all 31 decisions exactly, with both denial probes passing.
The next planned prospective training visit remains date-gated to 29 October
or later; nothing requires another recording tonight.

The following entries preserve preceding checkpoints.

Latest genuine window trial: [the first unscored engineering recording](window-engineering-01.md)
archives 33 actual Wi-Fi QUIC flow windows from the user's normal Chrome visit.
Fifteen exceed their retained model prefix, up to 1,700 packets in one flow.
The nested 1/3-second totals are 3,808/3,856 observations, with no recorded queue
drops or evidence eviction. Nineteen late revisions in three one-second windows
remain explicit. All 86 source-model predictions reproduce exactly; prediction
browser receipt p50/p95 is 320.69/546.28 ms. These are internal consistency and
functional collection results, not independently labelled quality or full
on-wire parity. Independent window-panel inspection timed out awaiting app
access; observation receipt/paint metrics are absent. All passive names remain
unverified; the chosen site supplies no labels. Capture is stopped. The new
reproducible validator brings verification to 256 Python tests and Ruff for 87
active files. No training, policy fitting or model promotion followed this test.

Latest implementation: [the research follow-up](approach-comparison.md) evaluates
fixed ordered packet retrieval (25/54 development caps, F1 0.53896) and the
official frozen pretrained encoder (43/54, F1 0.83954), against the same legacy
forest's 45/54/F1 0.87386. Both fail local comparability/class-recall gates.
Feature/early-position ablations do not establish a repair. No cal-02, new
development or final inputs enter these studies; pretraining-week overlap is
explicit. Actual artifacts, standalone checks, CPU measurements, sources and
commands are recorded. None is promoted.

Optional bounded 1/3-second windows now collect/display statistics beyond packet
thirty, with partial/late/reordered handling. The separate metadata identity
lane preserves model disagreement and refuses name-derived accuracy claims.
Usable passive-name coverage is zero of 31 browser-mapped legacy development
connections under the conservative ECH/GREASE policy. Longer-window service or
activity training, genuine window-to-screen validation and independent model
quality remain pending. This is experimental engineering, not a model-validated
release. 248 Python tests, Ruff for 84 files, ten UI tests, production build and
Prettier pass. The stopped session was verified archived, then the local service
restarted with the unchanged B17; four HTTP/direct prefix checks match exactly.
Capture and experimental windows are off. No interface was opened by this work.

Latest research: [the practical real-time classification review](realtime-classification-research.md)
compares primary papers, protocol standards, official tools and model source
with the actual pipeline. It identifies official 30pktTCNET embeddings, ordered
raw-packet neighbours, and handshake-dependence diagnostics as untested paths.
An official weight HEAD request succeeds (7,179,018 bytes); no weights were
downloaded or executed. Upstream pretraining uses week 46, overlapping our old
final-test period, so a separate evaluation is required. On current training
records, 24 complete prefixes have median duration 102.63 ms; 21 finish within
one second. This describes observation limits, not new accuracy. Longer windows
or hybrid name/process-assisted identities would change the original scope.
No capture, model/config change, training, new calibration or extra test run
occurred. The existing version-3 roles remain frozen; further collection is
not a substitute for deciding which evidence a classifier should use.

Latest collection checkpoint: the second [version-3 development recording](browser-development-v3.md#second-recording-archived--28-october)
is archived. Seven independently matched Instagram connections supply 183
packets and 24 valid prefix points, with no mapped-flow exclusions, no queue
drops and no evidence eviction. All 81 original B17 predictions reproduce
exactly. Browser receipt p50/p95 is 79.63/408.38 ms, a single-session observation
rather than a controlled improvement or paint measurement. The pool is now
17 Instagram/thirteen YouTube connections, with no new fitting or policy tuning.
Two of six new development recordings are complete. The next training activity
is reserved for 29 October or later at +05:30; actual early preparation correctly
refused and wrote no intent. Capture is off. No source change or additional
test suite run was needed for this evidence-only archive; the 222-test software
checkpoint below remains current. Independent new-model quality remains pending.

The following entries preserve preceding checkpoints.

Latest collection checkpoint: the first [version-3 development recording](browser-development-v3.md)
is archived from genuine user-started Wi-Fi capture. Five Instagram and one
YouTube connections pass the independent reference and feature checks: 174
packets, 22 prefix points, no mapped-flow exclusions, and 211 exactly reproduced
B17 predictions. Training support is now ten Instagram/thirteen YouTube
connections; no new model fitting or quality claim follows this partial input.
The next Reels recording has a frozen intent, with capture off.

Browser receipt p50/p95 was 119.96/612.45 ms over 211 events. This single
post-UI-change observation does not establish a causal improvement or paint
latency. There were 110 combined viewer/inference queue drops and 47 coalesced
events; no evidence eviction or eligible-prefix mismatch was found. The
selection-gap gate now waits after the last retained training-prefix packet,
rather than the last connection start. **222 Python tests** and Ruff checks for
74 active files pass. New-model calibration and independent live quality remain
blocked on the frozen development sequence and a qualifying candidate.

The following entries preserve prior checkpoints.

The [packet-only heuristic comparison](packet-rule-comparison.md)
completed under a fixed config, without new capture or newer calibration/final
input. A training-derived nearest signature gets 26/54 development caps right
(mean-budget target F1 0.56923), versus 30/54 for the paired CE TCN (0.57459)
and 45/54 for the summary forest (0.87386). Unique interval rules match 19/54
cases with four errors, all on Instagram, and fail the fixed support/error
gates. No predictor was promoted. This tests one declared packet-only baseline,
not the internship's broader activity/naming cascade or every possible rule.

At that checkpoint, 220 Python tests and Ruff checks for 74 active files passed. Saved numeric rules
infer without source data/model access; checksummed results and a local
experimental archive are retained. CPU p50/p95 is 0.98/1.61 ms for the rules,
14.99/18.65 for the paired TCN and 25.61/31.32 for the forest over 1,000 calls.
These are recorded-input CPU timings, not fresh live validation. B17 and the
capture configuration remain unchanged; capture is off. The prepared new
collection was not consumed or started by this experiment.

Prior preparation: [version-3 collection](browser-development-v3.md)
has fixed activities, training/selection roles, six-session cap, independent
reference eligibility, support/date/time gates, and prepare/archive/status
commands. Archival preserves all refusals and feature exclusions, binds the
actual source model/interface, and refuses overwrite or active-capture export.
Both failed calibration pairs stay excluded. The unchanged B17 source remains
configured; no new capture, training or model promotion is performed by these
commands. The first genuine development recording is pending.

203 Python tests and Ruff checks for 70 active files pass. Fixed eligibility
preserved every valid row in two historical development records. These checks
do not satisfy fresh live collection, new-model quality or latency gates.

Runtime preflight also passed: the archived previous session was preserved,
the verified localhost service restarted with the same B17 bundle, and readiness
is true with capture off. Four recorded-prefix API predictions match direct
inference. Wi-Fi interface 9 and the new interface-status field are present.
`instagram-dev-03` has a frozen pre-capture intent; repeated preparation leaves
it unchanged. The report gives hashes and private verification paths. Genuine
collection and any subsequent model improvement are still pending.

Latest engineering: the [development audit and one feature-map experiment](development-failure-audit.md)
found no trained-TCN padding-readout fault. Early Instagram errors and overlapping
correct/error scores persist across three forest seeds. A fixed ordered-prefix
forest variant worsened local development F1 from 0.87386 to 0.81120 and Instagram
recall from 0.77976 to 0.58333. Its seed-17 gate failed; further seeds were not
run. Newer calibration and final records were excluded. No new model policy,
default switch or user recording followed. 187 Python tests and Ruff checks
pass; the explicit feature-map decoder and reproducible study CLI are retained.
No verified model repair was found, and the release blockers below remain.

Latest: [fresh replacement calibration completed](browser-calibration-02.md).
Six independently referenced connections per service produced 17/22 correct
Instagram and 23/24 YouTube prefix points, but no threshold meets every frozen
error/support constraint. No calibrated bundle, default switch, relaxed limit
or further training followed. Both fresh recordings stay protected calibration
input. Capture is stopped; no recording was requested to dilute failures.

YouTube capture-to-browser receipt p50/p95 was 4,583.05/27,642.55 ms despite
capture-to-model-event values of 347.77/531.23 ms. Cause is unverified. A bounded
UI display buffer coalesces redraws independently of immediate prediction
acknowledgements. Nine UI tests, production build and formatting pass; live
causal improvement remains unverified. Local calibration, independent new-model
live quality and broader UI latency/loss validation remain release blockers.

The next entry preserves the preceding partial-collection checkpoint.

Fresh replacement-calibration collection: `instagram-cal-02` is archived from
the user's new stopped Wi-Fi session. The fixed browser matcher identifies six
Instagram connections (163 packets, 22 available prefix points). All retained
payload sizes match within direction, with no missing prefix packets. All 99
original B17 live predictions reproduce exactly. This is calibration input,
not replacement accuracy evidence; the replacement has not been scored or fit
on this partial input. Separate `youtube-cal-02` remains pending. The fitter
refuses partial collection before creating output. Weights, normalization,
candidate choice and threshold remain unchanged; capture is stopped.

Current stage: the first forest **failed separate calibration**. Both reserved
recordings are archived, with seven independently attributed connections per
service, 406 matching within-direction payload sizes and 255 exactly reproduced
B17 live predictions. The frozen forest got only 5/26 Instagram and 22/28
YouTube prefix points correct. No threshold satisfied the error/support limits;
no calibrated bundle was created or default changed.

The [failure and bounded follow-up](browser-calibration-failure.md) preserve that
result. An explicit retirement decision permits those failed recordings to
serve development selection only, never calibration/final again. Training uses
the 17 earlier local flows plus original public training data. A forest with
0.25 local training mass passes stronger development gates at all three fixed
seeds (F1 0.87386/0.87149/0.90937). Seed 17 remains the deployment candidate,
with policy unfitted. Fresh calibration and fresh user-started live evaluation
remain required. The app remains on B17 with capture off; no new recording was
requested during diagnosis. A versioned replacement calibration plan preserves
the failed candidate's original plan and excludes its retired recordings.

Current verification: **184 Python tests passed**, Ruff lint and format passed
for 65 active Python files, and the actual trained replacement passed isolated
API/direct parity without training-data reads. Its 1,000-call CPU p50/p95 is
27.02/30.01 ms. The report links the uncalibrated portable archive, checksums,
fixed-seed results and exact reproduction commands. New live quality remains
unverified; no capture, publication or default switch was performed.

The following entry describes the preceding training checkpoint, before its
candidate failed calibration.

Current stage: the [browser adaptation pilot](browser-adaptation-pilot.md)
completed after four genuine user-started v3 recordings. First visits supplied
ten local training connections; second visits supplied seven independent-session
development connections. The selected forest candidate gets 22/27 available
development prefix points correct, versus 20/27 for the adapted TCN and 1/27 for
B17, while passing the historical public-retention guard. This is not final
local accuracy. The candidate and training statistics are frozen for separate
calibration, then fresh live evaluation. Its policy remains unfitted; the
service still loads B17 with capture off. All 169 Python tests and lint/format
checks passed. The report gives exact identities, paths and commands.

Entries below describe earlier checkpoints.

Latest work: the [newer-data pilot](quicext25-pilot.md) completed three genuine
training runs, including a 20-epoch supervised TCN and a same-data forest, on
1,390 training / 813 selection / 749 calibration flows. Alternative reference
labels passed an audit against 3,021 original training APP labels. Neither
candidate repaired the saved local browser failures; none was promoted. No
new final-test data was downloaded or opened. A socket-mode follow-up matched
all 41 sent and 61 received Instagram payload sizes within direction, while
browser-order replay still failed. Fresh independently attributed browser
development recordings and separate evaluation sessions are now required for
further adaptation. All model/data/evidence paths and hashes are in the report.

Current verification: **163 Python tests passed**, no skips; Ruff lint/format
passed for all 59 active Python files, and `pip check` passed. The prior seven
UI tests/build remain separate evidence; this stage did not change UI code.

The following paragraphs retain earlier checkpoints.

Follow-up [newer-data inspection](newer-data-inspection.md): a real 37.8 MB
official QUICEXT25 daily member was downloaded and its size/CRC verified.
The first 16,384 records pass our packet contract, but the raw file lacks APP
labels and the prepared-label host timed out. Provisional class coverage is
insufficient in the bounded sample; browser relevance remains unverified.
A bounded read-only inspector and seven tests
were added. No new training or capture began; label provenance and suitable
development coverage remain prerequisites for a new candidate.

Latest evidence: the [Instagram diagnostic](instagram-trial.md) matched four
real user-started connections. Three of eight live model decisions accepted
labels, all wrong; five were withheld. All 71 retained live predictions replay
exactly. The plain TCN and forest did not establish a reliable fallback. No
weights, policy or default-model selection changed. Reliable local accuracy is
an unmet release gate, rather than a successful local deployment.

Current source uses adapter `tshark-prefix-ns-v3`: a 65-second idle timeout,
distinct duration/viewer stop reasons and filtering of normal TShark shutdown
statistics. The actual Instagram session used v2; all 31 saved windows are
unchanged under the timeout correction, and fresh live v3 validation remains
pending. A bounded opt-in Chrome-log stream reader handled the actual 165 MB
export; incremental numeric-tree loading reduced forest JSON loading overhead.
**137 Python tests, seven UI tests, production UI build and lint/format checks
passed locally.** The service is intended to remain idle until the user presses
Start. Private browser logs and trial artifacts remain ignored and unpublished.

The following entries preserve earlier checkpoints and their limitations.

Earlier update: [the local diagnosis](local-diagnosis.md) fixed epoch timestamp
subtraction precision and independently matched a 30-packet recorded prefix to
ipfixprobe exactly. Adapter `tshark-prefix-ns-v2` is loaded on the idle local
service; all 104 Python tests passed at that checkpoint. Fixed timing/model/socket-view comparisons did
not establish a reliable prediction repair. Existing phone recordings were found,
but the user cannot confirm their origin and thinks they were downloaded. They
are excluded from local-quality evaluation and training.
No local retraining or threshold change has occurred.

A related-project review contributed a new variable-header golden fixture:
IPv4/IPv6, VLAN stacking, IPv4 options and IPv6 extension headers all preserve
the same UDP-payload bytes, directions and gaps. Seven new checks passed locally,
including actual offline TShark parsing. CI now lints/formats every active helper
script, including the recent diagnostics. The related project was read-only;
none of its code, private captures, models or claimed performance was imported.
Combined local verification: **111 Python tests passed**, with native TShark
checks executed and no skips; Ruff lint/format passed. Hosted CI remains unrun
on the unpublished branch. The related project retained its pre-existing
`.obsidian/app.json` change and was otherwise untouched by the review.

**A real-data model is selected and its held-out CESNET test is complete. One genuine user-started Wi-Fi capture verified the live packet-to-model-to-browser path; local prediction quality and independent feature parity remain unverified.** Replay and offline PCAP tests cannot establish those remaining claims.

## Source and local environment

The reviewed plan baseline was `bbd8d3f1b5f4a5b919b68d3b7e025d20d0ca2d47`. Work began from the newer, clean `47a355c5a3757b8c73f932ce3bdbca1efbe34f6d` and is on an unpublished local branch. Existing TensorFlow and earlier PyTorch work is preserved in `legacy/`. No paid GPU/cloud work, publication or merge occurred.

This Windows 11 laptop has an Intel i7-1360P, about 16 GB RAM, Python 3.11.9, CPU-only PyTorch 2.5.1, Node 20.17, TShark 4.6.8 and Npcap 1.88. Interface enumeration worked; real capture access has not been verified. The official `C:/Users/shrey/Downloads/cesnet-quic22.zip` is 20,952,008,298 bytes. Its published MD5 matches `2d52ad44ddb22645a3464634fc54bb9c`; SHA-256 is `17ecb8991cb44abd1b33b8fb448e5119407388b91aa50a1a5e83b486116f6176`. The original HDF5 download remains truncated and the DataZoo host returned HTTP 503, so the legitimate Zenodo CSV ZIP supplied the experiments.

The bounded prepared data manifest is `data/processed/v2/manifest.json`, SHA-256 `46ef59ce749e8c3da1d7bde4597e1e9697a7e97a046f01a48af0ec5f0612eae3`. It records 14,000 week-44 training, 10,467 week-45 selection, 3,533 week-45 calibration and 14,000 week-46 final-test flows, with deterministic 200-per-class/day sampling. These are balanced engineering samples, not source prevalence. Host/session independence cannot be proved from the export identifiers; short packet-feature fingerprints recur across unique IDs.

## Implemented and checked

- One active `src/netembed` package; validated feature schema, training-only normalization, causal length-aware TCN and same-data Random Forest; bounded raw-unit stresses; checksummed self-contained bundles with labels, policy and provenance. No random-weight or training-data dependency at inference.
- A frozen chronological split and three-seed candidate matrix with separate calibration, saved predictions/configs, explicit final-test gate and resumable local training. The 15 development runs are indexed in `experiments/full-real/comparison.json`.
- A local FastAPI service, bounded TShark flow/event pipeline, user-controlled Start/Stop, and one React Live/Replay screen. Recorded replay is visibly separate. The constructed RFC 9001 PCAP verifies parser output `[0 ms,+1,1200 B]`, `[8.5 ms,-1,135 B]`, `[1.5 ms,+1,1200 B]`; it does not verify ipfixprobe parity.
- Local checks before the new reference workflow passed: 52 Python tests, Ruff lint/format, five UI interaction tests, production Vite build and Prettier. The reference workflow adds boundary/opt-in, map, bounded-history and mismatch-display tests; its latest verification is recorded below. Hosted CI and a fresh-clone install have not run.

## Frozen decision and evaluation

The [decision](../configs/default-decision.json) was saved before the held-out test. Development mean 16-case macro-F1 across 5/10/20/30 packets and four declared conditions: forest 0.68949; plain cross-entropy TCN A 0.71124; augmented cross-entropy B 0.82777; plain CE+SupCon C 0.71329; augmented CE+SupCon D 0.82689. B–A improves by +0.11100/+0.12109/+0.11749 across seeds 17/42/123, with clean changes −0.00066/−0.00701/−0.00233. D–B changes +0.00239/−0.00401/−0.00102, so the declared all-seed and ≥0.01 mean SupCon rule fails. Forest is outside the 0.01 comparable-quality margin. The predeclared deployment seed is 17, not the best development seed.

Selected bundle: `experiments/full-real/20261024-151720-3532794c/bundle`, metadata SHA-256/artifact ID `18c43fe12262b81d4a3001df150a278865f3908ddd3aab934822fc0c9e5750fb`. The ignored local artifact must be regenerated from the verified dataset on a fresh checkout. Its week-46 held-out report is `experiments/full-real/20261024-151720-3532794c/final/report.json`, SHA-256 `ec0e7fb5f1a6da476de8926da26bbc62ce6fa2317c82494b36a2065a6af34246`; saved predictions SHA-256 `45183e7ad19c1432c99d8be8c544b7a3d9ad9973806b961d03329669ea967a9a`.

On 14,000 final-test flows, clean macro-F1 at 5/10/20/30 packets is 0.7912/0.8428/0.8761/0.8864. The 16-case all-flow mean is 0.8237. At five packets, Google Drive F1 is 0.536, YouTube 0.643 and Snapchat 0.676; Google Drive is often confused with YouTube. Observation loss gives 0.7146/0.7654/0.8159/0.8359 at the four budgets. At the saved 0.67 threshold, clean five-packet coverage is 0.7183 with 0.0990 accepted error, and thirty-packet coverage is 0.8718 with 0.0664 accepted error. These are dataset estimates, not local Wi-Fi or unseen-service guarantees; the size-padding stress is an abstract feature edit.

With two Torch threads and a recorded 19-packet flow, the selected TCN measured 16.06/18.94 ms p50/p95 over 1,000 CPU pipeline calls and 25.07/30.58 ms over 1,000 local keep-alive HTTP calls. Forest HTTP latency was 122.92/141.09 ms under the same protocol. The selected CPU, HTTP and forest HTTP reports have SHA-256 `056348d7db1d19c6e586a0c500235c4cc337923cb7564e45cb35a0824c92c57e`, `7a4d6e96685a7d63d6e0e4ee948f787e0d47c82ac25c93c131871b059109322e` and `de0994023c8ec54c40a3aacf76864be10f54d493971c5c505c55e003b98a0f4a`. These exclude packet observation and browser rendering. Runtime can vary with host load. The [model card](model-card.md) and [experiment guide](experiments.md) give interpretation and reproduction commands.

## First real local capture

The local user selected Wi-Fi (TShark interface 9), pressed Start in the browser and later pressed Stop. Session `46d24f6322cb438d93588a004ce276db` reported 45 acknowledged prediction events, zero dropped events, eight coalesced pending checkpoints, 209 ignored packets, 12 evicted idle flows, 82 packets beyond the 30-packet cap and zero reordered packets. The browser showed a live event stream connection, and Stop returned `stopped by user`; the session's TShark process was no longer running. `Capturing on 'Wi-Fi'` was a normal TShark stderr line, not an inference error. A regression-tested fix filters that line on subsequent service starts.

The bounded timing summary is `experiments/full-real/live-wifi-20261025-session.json`, SHA-256 `6efa7cb2ef5c904c58b419cd8a02967a21bb1c5571a6f5e7aa925b2fe46572ac`. Over 45 prediction events, capture timestamp to emitted model event was 380.63/532.60 ms p50/p95; model pipeline time was 11.91/29.46 ms. The old UI acknowledged events from an animation-frame callback, which can be delayed in background tabs. Its 395.90/2869.88 ms acknowledgment figures are retained in the raw summary but **must not be called browser receipt or paint latency**. Packet observation time is part of capture-to-event latency. No independent per-flow app label was recorded, so this is functional and latency evidence, not local accuracy evidence.

A second user-started session opened YouTube in Chrome while the NetEmbedAI screen stayed in Edge. It stopped cleanly with 105 model-event acknowledgments, zero dropped events, 24 coalesced checkpoints and no remaining capture process. Its capture-to-event p50/p95 was 294.94/536.08 ms and model pipeline p50/p95 was 11.73/24.37 ms. The old animation-frame acknowledgment measured 982.56/11639.29 ms, illustrating the background-tab delay rather than true receipt or paint latency. Its ignored local summary is `experiments/full-real/live-chrome-youtube-20261025-session.json`, SHA-256 `7b38480d036e9d9ae89817dc24d142f6ca0aebb1eadaf02b50f8454f77c4cabc`. The user reported an insufficient-confidence result and a WhatsApp label, but the interface did not independently associate those flow rows with the YouTube tab. No YouTube accuracy or error claim follows. The UI was then changed to timestamp acknowledgments immediately in the WebSocket message handler.

A third user-started session used the rebuilt UI and also stopped cleanly. It produced 33 acknowledged predictions with zero drops. Capture-to-event p50/p95 was 401.69/540.13 ms; corrected capture-to-browser-receipt p50/p95 was 403.21/543.99 ms; pipeline time was 13.16/24.27 ms. These are 33 event observations from one session, with no hard latency guarantee. The bounded summary is `experiments/full-real/live-chrome-youtube-corrected-20261025-session.json`, SHA-256 `2a1d43abf40a2e65c85bdcc7a4591c282d4f2595ac5b795d76ffca5ac9f95371`. The user reported separate WhatsApp, Snapchat, Discord and insufficient-confidence flow rows while visiting YouTube, but the rows were not independently tied to that browser tab. No local classification accuracy is inferred.

## Separate reference workflow

Unexpected labels must be investigated as possible model errors as well as
background traffic. The optional **Check predictions against a separate handshake
reference** checkbox is now implemented. With explicit opt-in, TShark reads the
visible SNI and ECH/ESNI indicator fields. A checksum-verified copy of CESNET's
published `servicemap.csv` produces a conservative evaluation-only reference;
the hostname is then discarded. It cannot replace or affect a model prediction.
Missing, encrypted, conflicting and overlapping matches stay unverified. The UI
shows reference agreement/refusal/mismatch independently and can export bounded
packet features plus all retained checkpoint predictions for feature inspection.
Exports contain no raw hostnames, addresses or payloads. This helps attribution
but is not independent ipfixprobe feature parity or guaranteed app identity.

The official map MD5 is `89b5080480db4be0c31bbbbdedd62451`, SHA-256
`90041edb9cb760265ca8fcdaaa3b1ed6138c7a4c44d3f07b2f063b75776cc5c3`.
Its bytes and CC-BY-4.0 license were checked through Zenodo's API, and attribution
is packaged with it. Offline TShark recovers `example.com` from the RFC fixture;
reference mode leaves the exact raw packet features unchanged and marks that
name unmapped. Mocked end-to-end checks preserve a WhatsApp model result beside
a YouTube reference, demonstrating that the reference does not override it.
The built wheel loads the map from its packaged resource without repository data.
Final local verification passed: 63 Python tests, seven UI tests, Ruff lint/format,
Prettier, and the production TypeScript/Vite build. The updated service on port
8001 returned readiness, the same selected artifact identity, a real-bundle
19-packet replay prediction and HTTP 200 for the screen. Reference collection
and capture were both off after startup; no test opened a live interface.
The new reference mode still needs an explicit user-started live trial; none of
the previous sessions collected reference labels or retained packet windows.
See [local testing](local-testing.md) for the next useful trial.

The first real opt-in trial is now recorded: session
`c1d16eeeb34b4d2eb77c9a9453577d8d`, eight retained flows / 233 packets, 27 live
predictions and browser acknowledgments, zero drops, four coalesced jobs and clean
Stop. Browser receipt p50/p95 was 352.87/517.43 ms. All eight references were
refused by the ECH/ESNI-indication guard. The old status name `encrypted_name`
overstated what was observed: ECH can be GREASE, and a passive extension marker
does not establish encryption or the actual origin name. The status is now
`protected_name_unverified` with a reason, still without assigning a reference.
See [RFC 9849 section 6.2](https://www.rfc-editor.org/rfc/rfc9849.html#section-6.2).
There are zero defensibly referenced flows in this trial; the reported WhatsApp,
Discord and refusal outputs cannot be scored or dismissed as background traffic.

The ignored metadata-only export is
`experiments/full-real/live-reference-ech-20261025.json`, SHA-256
`2a6d2909eb65a181864cad1bef470e9a84c869e4abd1286b85b549bb712d0f1f`.
Its timing report SHA-256 is
`ac91cdf9e214558598176d61ba223ec2adda4b1e799d3d4599d06088f4b7765b`.
The raw features contain no oversized payloads (>1500 B); the maximum is 1452 B.
All 14,000 training flows use whole-millisecond intervals, whereas 96.6% of this
trial's intervals have fractional milliseconds. Exact exporter quantization
semantics still need verification. The reproducible `scripts/audit_local_trial.py`
reads training only and explores, without deployment changes, floor/nearest-ms
replay. Flooring changes 1/31 top-ranked prefix labels, so this difference alone
does not explain the output pattern. The exploratory report is
`experiments/full-real/live-reference-ech-20261025-audit.json`, SHA-256
`c9441653d7487533778998d53338c972dfda00f599af8ea0be2777901c518a0f`.
No accuracy or causal improvement is claimed. The affected 25 Python tests and
all seven UI tests, production build and Prettier passed after the diagnostic
wording correction. Inference semantics and model identity were not changed.

## Remaining gates

The offline `attribute-netlog` command is now implemented using Chromium's
documented QUIC-session origin and packet-receipt schema, each file's own event
constants and its clock offset. New explicitly opted-in captures retain session
matching keys, connection pseudonyms and first-packet timestamps. Raw endpoints
are not exported. The matcher requires exact tuple tokens, equal payload sizes,
two distinct receive matches within 100 ms, a session beginning within 2 seconds,
and a unique non-migrated browser session. It refuses old exports and incomplete
or ambiguous references; browser origins never enter the model or select a match.

Verification: all 82 Python tests, Ruff lint/format, seven UI tests, production
build and Prettier passed. The installed CLI processed an explicitly flagged
software schema fixture and retained a YouTube origin reference alongside the
unchanged WhatsApp prediction, counting a mismatch. This validates software, not
actual Chrome-log correlation or local accuracy. No browser log or new capture
was started during implementation. [Browser-attribution instructions](browser-attribution.md)
give exact user steps, commands, bounds and pooling/clock/capture-point limits.

1. Clean Windows checkout/setup is verified below. Hosted CI has not run on the unpublished branch; fresh Linux/macOS installation remains unverified.
2. Compare a real captured trace's feature sequence with an independent ipfixprobe reference where available. Inspect the selected live flow's packet rows and model identity directly in the screen. Do not classify generic UDP/443 as confirmed QUIC.
3. The browser matcher is now validated on the actual Chrome/Wi-Fi diagnostic trial documented below. Verify timing quantization/feature parity before any adaptation. Then collect separate development and held-out sessions for at least two services, retain failures and refusals, and report missing/ambiguous references and explicit denominators. All four earlier functional sessions remain unlabelled. The UI measures browser receipt, not paint time. Replay and synthetic/offline fixtures cannot replace local quality evidence.

No hard real-time, open-world, adversarial, VPN or enforcement claim is supported.

Independent offline fixture parity is now verified with current ipfixprobe 5.8.0
(RPM `5.8.0-20260901120711.el9`) in a network-disabled, capability-restricted local
container. It exported payload sizes 1200/135/1200, directions +1/−1/+1 and gaps
0/8.5/1.5 ms, matching TShark's adapter within `1e-7`. No live interface was opened.
The raw output SHA-256 is
`4c557358b427087ce811194bb54b85fed40366888a6c462c3f5a6b084b795429`.
The local report `artifacts/local/ipfixprobe/parity.json` has SHA-256
`0b01f2a80d08b23e2272eca36da77d96bc48bce36896dab4d311b1e449745b72`.
The [committed fixture reference](../tests/fixtures/rfc9001.ipfixprobe-reference.json)
binds actual output to the known PCAP hash and records the container identity.
[The optional reproduction helper](../tools/parity/README.md) pins the base and
exporter package versions and never captures or pulls images on its own. This is
constructed-fixture evidence, not historical CSV quantization, real captured
trace parity, or local service quality. Those narrower remaining gates stand.

Final combined verification after adding the independent reference fixture:
**88 Python tests passed**, all seven UI tests passed, Ruff lint/format passed,
and the TypeScript/Vite production build and Prettier passed. The versioned
Dockerfile rebuilt from cache and the hardened no-auto-pull fixture helper
repeated the successful independent comparison. All reference containers exited;
none opened a live interface. At that checkpoint the browser-origin matcher had
only software validation; the subsequent real trial is recorded below.

## Clean Windows install and portable inference archive

A shallow clean checkout of commit `7f6bd231fb979a7a5a0a42b3712d5e3b585ebe3a`
at `artifacts/local/clean-checkout-20261025` was installed into a new Python 3.11
venv with system/user site packages disabled. The explicit CPU-index step installed
`torch==2.5.1+cpu`; the project then resolved its lock from the normal package
index/cache. `pip check` found no broken requirements, all 88 Python tests passed
(zero skips), and Ruff passed. Fresh `npm ci` reported zero vulnerabilities;
all seven UI tests and the production build passed. This verifies this Windows
host with its existing Node/TShark prerequisites, not an untouched OS or other
platforms. CI now selects CPU wheels explicitly to avoid Linux CUDA dependency
downloads; its hosted execution remains pending publication authorization.

The clean checkout contains no active v2 training data. The selected real bundle
loaded, matched the earlier 19-packet replay within `1e-6`, matched direct/API
outputs, served the built UI with HTTP 200 and kept capture/reference collection
off. The input was a training-example functionality check, never an accuracy
estimate. `artifacts/local/clean-checkout-report.json` records package versions,
module locations and checks, SHA-256
`2664f7e3dcdb2a9918a3ffe5165ba8593bf53d1e20da06adcf0eddabd07c0e0a`.
The JUnit file `artifacts/local/clean-checkout-pytest.xml` has SHA-256
`7c6ca977384ff738d3fe5e08b087fb843dc47ba40d9317ae1064d762a535160f`.

The local inference archive `artifacts/local/NetEmbedAI-v2-default-B17.zip` is
423,237 bytes, SHA-256
`f9ca92fd82ea3cbc4254238b68993027e3a12715aa02f6ff9d1107bd21abd746`.
It contains checked weights, preprocessing, labels, architecture, policy, versions
and provenance, plus the frozen decision, model card and dataset credit. It omits
training data and training checkpoints. It was extracted and loaded in the clean
isolated checkout: model identity matched the decision, real direct/API inference
worked and capture stayed off. The verification report
`artifacts/local/default-archive-verification.json` has SHA-256
`ecef5c695b5ab3154ff6ccf4b49560524f30938345f8f1ea84fbffba92fab4b3`.
The archive remains local and unpublished; `scripts/package_bundle.py` reproduces
it from identical input bytes and never overwrites, trains or publishes.

## Actual Chrome origin-reference diagnostic trial

On 25 October the user completed a fresh opted-in Wi-Fi capture alongside Chrome
155.0.8059.80 NetLog. Session `38502a842a1f4afdacf60216daa76aad` stopped cleanly.
The unchanged matcher read 165,965 events without schema errors and retained all
31 flows: four YouTube references, ten ambiguous service-map references, ten
outside the supported set, four invalid/migrated sessions and three unmatched.
The four YouTube connections each had a unique origin session and 8–12 matched
receive records. This passes the real-browser diagnostic integration check on
this host, not the multi-service held-out local-quality gate.

Their eleven delivered prefix decisions included one accepted YouTube prediction
and ten refusals. Eight accepted labels on outside-supported-set references
expose the closed-set limitation; confidence does not establish app presence.
All 99 live predictions replayed with exactly equal scores and unchanged labels
using the same B17 artifact. Explicit offline replay fills missing prefixes
separately and is not counted as live delivery. Browser receipt p50/p95 was
259.28/506.44 ms over 99 acknowledgments, with zero queue drops, 20 coalesced
checkpoints, 25 active-state expirations/evictions and zero evidence-history
evictions. No model, policy, feature semantics or attribution gate was tuned.

[The full trial record](browser-attribution.md#first-actual-chrome-trial-25-october-2026)
provides counts, limitations, local filenames, SHA-256 values and the repeatable
`scripts/audit_browser_trial.py` command. Raw browser logs and endpoint matching
keys remain local and ignored by Git. Real captured-trace exporter parity,
historical time quantization and separated two-service local sessions still
remain. The portable model archive is unchanged.

Verification for this diagnostic update: 27 attribution/reference Python tests
passed, seven UI tests passed, Ruff lint/format and Prettier passed, and the
TypeScript/Vite production build passed. The audit helper also executed against
the actual stopped trial and verified all 99 saved predictions. Capture stayed
stopped throughout; no new traffic collection or model fitting was started.

A follow-up receive-prefix consistency check compared all 59 server-to-client
packets on the four mapped connections in order against the first corresponding
browser receive events. Sizes matched exactly with no missing prefix records;
absolute timestamp differences were 0.625/1.223 ms p50/p95 and 1.384 ms maximum.
The check keeps same-millisecond events and does not filter mismatched sizes.
This narrows gross receive-side conversion/omission concerns, but 53 outgoing
packets, bidirectional gaps, historical quantization and real-trace ipfixprobe
parity remain unverified. These connections were conditioned on successful
origin correlation; no broader quality inference follows. No verified model fix
or cause of weak local recognition was identified, and nothing was deployed.

The repeatable helper is `scripts/check_browser_receive_parity.py`; its report
`artifacts/local/browser-receive-parity-youtube-01.json` has SHA-256
`9787a7e1cad5d80af0f82bddbc9c7ee3bf43bf8dfb5ff2fc6ba365bef696b26e`.
Ruff lint/format passed and 23 relevant Python tests passed, including four new
regression checks for duplicate timestamps, size mismatches, missing packets and
clock disagreement. See [the scope and reproduction command](browser-attribution.md#ordered-receive-prefix-consistency-check).
