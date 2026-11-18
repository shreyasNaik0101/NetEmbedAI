# Release gates and remaining evidence

> **Current status, 10 November 2026:** The local fixed-ten raw-guess screen
> completed, but its separate fitted acceptance policy failed the final check;
> the later matched timing-jitter candidate also failed across fixed seeds. This
> is an experimental showcase, not a validated release. See the current
> [showcase model card](showcase-model-card.md). The entries below preserve older
> chronological checkpoints and should not be read as the latest status.

This is the current acceptance audit, not a declaration of a demo-ready release.

Latest [public-only policy/runtime stage](ipv6-public-policy.md) completes one
fixed historical calibration fit and exports the unchanged forest with scope
metadata. Ten-packet calibration coverage55%, accepted error3/275; strong class
rejection remains (YouTube11/50 accepted). All1,058 vectors preserve exactly and
101 curve points independently recount. Real API/CLI/direct parity and1,000-call
CPU checks pass.451 Python/19 UI tests,135-file lint-format and UI build pass.
No local outcomes fit this threshold; no capture or model activation occurred.
Local accepted-error/coverage and replacement live quality/latency remain open.

Latest: the [completed fresh four-visit comparison](ipv6-fresh-evaluation-results.md)
passes its fixed descriptive screen. At ten packets the added-data forest is
correct22/22 versus7/22 control; target-visit-balanced recall is1.0 versus0.462121.
All162 vectors replay exactly and eight confusion matrices independently recount.
This is bounded prospective evidence for two services on one IPv6 hotspot.
The cohort is not used for confidence fitting or retraining. Confidence-policy
evidence and replacement-model live integration/quality/latency remain pending;
there is no automatic activation. B17 remains visible. No more recording for
this four-visit scope;438-test software checkpoint unchanged.

Fresh evaluation collection now has two usable first-date visits:4 complete
YouTube/IPv6 flows and3 Instagram/IPv6 flows (17/30/30 packets). Packet/browser
checks and exact99/165-vector source replay pass. Candidate/control remain
unscored until the later-date pair is archived; neither later intent is prepared.
Earliest next date is6 November. Capture is stopped, with no more recording
today. This is acquisition evidence only, with no calibrated policy, default
change or replacement-model live-quality claim.438-test checkpoint unchanged.

Fresh evaluation engineering: [four declared new visits](ipv6-fresh-evaluation.md)
for the two frozen forests, with all-four-visits scoring embargo, target-visit
balancing, browser lifetime/IPv6/QC bindings and offline data guards.438 tests
and132-file lint/format pass. First YouTube intent is prepared; no user-started
evaluation capture or quality result exists yet. Both forests remain inactive
and uncalibrated; B17 stays in the app. Old training collection is paused.

Latest completed experiment: [real IPv6 training pilot](ipv6-realdata-pilot.md#actual-outcome).
The matched control reproduces. The added-data candidate passes all five fixed
local/public gates: local F1 0.780557 to 0.983806; ten-packet correctness 12/17 to
17/17 on reused development. All 4,126 vectors replay exactly; 16 matrices
independently recount. 424 Python tests and 130-file lint/format pass. This
candidate has a complete inference bundle but remains uncalibrated and inactive.
Fresh unseen-session quality, a valid confidence policy, and this replacement
model's real live-path quality/latency remain open. No broad reliability or
new-network guarantee is supported. Remaining acquisition slots are paused;
the old failed calibration is preserved. B17 remains the app default.

The following entries preserve earlier checkpoints.

Latest completed experiment: [size robustness](size-robustness-study.md).
The matched control reproduces exact weights. Both new treatments improve
abstract stress metrics in the seed17 pilot, but neither preserves all clean
local/public class guards. No extra seeds, selected candidate, calibrated policy,
new CPU benchmark or live activation follows.18,567 vectors replay exactly and
all72 matrices independently recount.395 Python tests/121-file lint/format pass.
Original calibration stays closed; reliable real IPv4/IPv6 recognition and
replacement-model live validation remain pending. B17 stays in the app.

Latest diagnosis: [packet-size sensitivity](youtube-failure-diagnosis.md) coincides
with IPv4/1250-byte versus IPv6/1230-byte YouTube starts, verified by browser
sockets. Abstract size swaps change predictions in both directions; no deployed
correction or reliability claim follows. Training coverage/robustness needs a
separate development experiment and fresh evaluation.375 Python tests/118-file
lint/format pass; UI unchanged. No further capture or automatic model activation.

Latest outcome: the [fixed forest calibration](forest-policy-calibration.md#actual-calibration-result-stop)
stops after two usable visits: ten-packet raw correctness is5/5 Instagram and3/6
YouTube. No declared threshold satisfies local error/coverage/support, so there
is no policy bundle, final recording request or promotion. A fresh-process audit
exactly replays1,089 vectors and independently recounts all101 thresholds. This
failure is preserved; the later-date final pair is cancelled under the frozen
rule. Dependable local classification remains unresolved. B17 stays in the app.

The following entries preserve earlier checkpoints.

Latest completed evidence: the [explicit paired follow-up](prospective-paired-followup-results.md)
ties at its primary endpoint (both 20/22 correct across four visits/two dates),
passes its descriptive screen and exactly replays all 170 saved vectors. This
adds small-sample independent local evidence. Both candidate policies remain
unfitted, and neither new model is validated in the live UI. B17 remains the
default. Original stopped protocols and their failures below remain historical.

Latest prospective outcome: slot 3 had reference checking off and retained zero
native flow records. The four-visit study is stopped under its frozen rule, with
two usable visits preserved and no candidate scores. A separate collection scope
and clearer pre-Start setup are needed before another independent comparison.
The original benchmark model is validated on its frozen CESNET sample. Dependable
local recognition, full real-capture parity and independent local evaluation
remain unresolved. New recordings are not needed to run the software checks.

Current checkpoint while waiting for the later-date recordings: the
[prospective paired study](prospective-paired-study.md) has two usable visits
in its explicitly documented same-session log-recovery continuation. The next
two slots are unprepared and date-gated. Archive integrity, read-only resume
status and the complete scorer path on constructed fixtures are verified.
**353 Python tests and 113-file lint/format pass.** No actual candidate scores,
calibration or new live-model validation exist for this fresh cohort yet.
The following experiment paragraphs retain their earlier software checkpoints.

The latest [checkpoint-specific heads](prefix-linear-probe-study.md) improve
reused development to 59/63, F1 0.95120, with a large five-packet gain. Instagram
still fails forest nonregression. The complete offline artifact and exact
replay/dataset-free checks pass; 343 Python tests and 109-file lint/format pass.
The artifact remains uncalibrated and outside the app default. Independent
quality and this new model's live-path evidence remain open.

The [31 October frozen-pooling linear probe](pool-linear-probe-study.md) improves
reused development F1 to 0.90272, but fails its Instagram nonregression check.
Its complete offline artifact, exact saved-prediction replay and dataset-free
inference are verified; it is uncalibrated and not integrated into the live
default. This does not close the independent local-quality or live-latency gates.
Latest software check: 331 Python tests and 104-file lint/format pass; UI unchanged.

| Requirement | Current evidence / remaining limit |
| --- | --- |
| One active implementation and setup | Installable `src/netembed`, pinned requirements, React UI; historical code under `legacy/`. Windows setup and an isolated real-artifact checkout were verified. Other platforms are not locally verified. |
| Shared raw feature contract | CLI/API/replay enforce schema 1: milliseconds, UDP payload bytes, initiator direction and explicit lengths. Invalid inputs fail. [Architecture](architecture.md). |
| Length-aware readout and prefixes | Retrained TCN gathers the last valid step; causal/padding regressions and 5/10/20/30-packet evaluation exist. [Model card](model-card.md). |
| Bounded default stress suite | Paired deterministic timing, additive abstract size padding and observation loss, in raw units; tested timestamp/count semantics. No transport/adversarial guarantee. |
| Complete standalone artifact | B17 contains weights, labels, normalizer, architecture/schema, policy, versions/provenance and checksums. No training files are required. Local archive and clean-checkout inference were verified. [README](../README.md). |
| Same-data baseline and matched losses | Fifteen fixed runs: forest and CE/CE+SupCon, each with/without matched augmentation across three seeds. [Experiments](experiments.md). |
| Default decision | Augmented CE seed 17 remains B17. Matched SupCon improvement fails the rule; simpler forest is not comparable on the original score. No later local diagnostic replaces this decision. |
| Frozen final evaluation | Original week-46 report/predictions are preserved, with per-class/prefix/stress evidence. Sampling and correlated-flow limitations remain explicit. Later official pretrained weights overlap that period and cannot reuse it as an independent test. |
| Decision policy | Original B17 has its saved CESNET policy. Earlier local forest calibration remains failed. The unchanged new forest now has a separately fitted public-only policy, explicitly scoped to historical CESNET; local accepted-error/coverage is still unvalidated and it remains inactive. [Current policy](ipv6-public-policy.md). |
| CPU timing | Trained pipeline/HTTP measurements exist; [stage benchmark](engineering-checks-20261028.md) adds separate preprocessing, forward and probability-conversion timing. Loading, HTTP, capture and paint are separate boundaries. |
| API/CLI parity and readiness | Bounded request validation, missing/fixture-model handling, local origins, actual real-artifact HTTP/direct parity and readiness checks. |
| Genuine user-started Live and separate Replay | Actual Wi-Fi recordings feed B17 and the WebSocket UI; Start/Stop/interface controls and replay stepping exist. No tests or installation open capture. |
| Flow/feature parity and lifecycle | Independent exporter prefix evidence is partial. Native RFC fixture checks cover IPv4/IPv6, variable headers, directions, timing and windows past packet 30. Bounded queues/state, timeout, process cleanup, overload and Stop-reason regressions pass. Full independently referenced on-wire local windows remain pending. |
| Local quality and screen timing | Real labelled local failures and prediction browser-receipt timing are documented separately from CESNET. New window-delivery instrumentation is implemented, but no genuine measured window-receipt or browser-paint result is claimed. [Window trial](window-engineering-01.md). |
| Clean setup and legitimate artifacts | Legitimate CESNET source/checksums/credit and local artifact packaging are documented. Data/weights are private, ignored and not published. A new checkout needs local artifact transfer or regeneration. No cross-platform success is inferred. |
| Tests and CI | Local Python/native fixture/build/lint checks are recorded in the engineering report; the [UI refresh](ui-refresh-20261029.md) adds a sixteen-test UI checkpoint and browser review. Windows/Linux CI is configured; no hosted run was triggered or claimed. Native tests explicitly skip if TShark is absent. |
| Documentation and interview explanation | README, architecture, model/data cards, experiment evidence and [beginner guide](interview-guide.md) distinguish software, historical benchmark and current local limitations. |
| Honest predictions and scope | No synthetic/random-weight fallback, hardcoded benchmark response, endpoint/name shortcut in the packet model, open-world detection, paid infrastructure or automatic capture. Optional metadata identity remains visibly separate. |

## What still needs external evidence

The [declared one-recording follow-up is complete](browser-selection-followup-results.md).
It resolves selection support and the fixed seed-17 experiment ran. Its forest
improves Instagram but loses YouTube recall (0.64444), failing the minimum and
nonregression rule; the neural candidate also fails. Repetitions/calibration
stop. No more capture is requested under this plan and no default changes.
The original study's shortfall below is preserved as history. Local per-service
quality and subsequent independent evaluation remain the blockers. All eight
exports reproduce their saved local probabilities exactly in a read-only audit;
artifact integrity does not establish dependable live accuracy.

The following paragraphs preserve preceding collection checkpoints.

The bounded [version-3 collection](browser-development-v3.md) has six of six
new recordings archived. All declared training recordings are complete, with
22 Instagram and 21 YouTube connections and the required date coverage.
Separate selection has seven Instagram and five YouTube connections, with five
full prefixes per service. YouTube is one below the fixed six-connection minimum.
The exact seed-17 runner refused at its support guard before fitting or creating
model output. No model comparison, repetitions or calibration ran. The frozen
collection cap is reached, so no extra capture, role change or relaxed gate
follows automatically. Any follow-up needs its own explicit scope. Independent
local quality remains unresolved; replay and more model searches cannot supply
the missing evidence.

The user has now requested the [one-recording follow-up plan](browser-selection-followup-v1.md).
It binds the existing data/configs and allows one additional selection visit,
with no changed numeric gates or automatic retries. Helper support is now
implemented and the real-data parent preflight passes. Additional capture,
candidate fitting and independent quality remain pending; the helper cannot
start capture. The single follow-up intent is prepared against the stopped
service; its checksummed preflight is linked in the follow-up document.
The original shortfall remains recorded. The new full Python checkpoint is
318 passing tests, with lint/format for 99 files and one existing deprecation
warning. UI code is unchanged from its sixteen-test/build checkpoint.

Separately, the new window timing path needs a genuine deliberately started
session before reporting live window-event delivery. Browser paint and full
real-capture window parity remain unmeasured. Hosted CI needs an authorized
push/PR; Linux/macOS verification needs an appropriate host. No such action was
performed by this work. These are different gaps, not reasons to relabel the
existing engineering or development records as a completed release.
