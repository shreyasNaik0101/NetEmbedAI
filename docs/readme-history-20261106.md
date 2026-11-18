# NetEmbedAI v2

The [public-only refusal policy](ipv6-public-policy.md) is fitted and exported
for the unchanged forest: threshold0.76, minimum ten packets. On the historical
calibration primary cases it accepts275/500 with3 mistakes (55% coverage,1.09%
accepted error); these are fitting-set statistics, not local accuracy. API/CLI
parity and dataset-free CPU checks pass, and the UI explains policy scope and
pending calibration.451 Python tests,19 UI tests,135-file lint/format and UI
build pass. The app still uses B17; local acceptance/live-candidate validation
remains pending. No capture or default switch starts automatically.

The following entries retain earlier experiment checkpoints.

The [completed fresh evaluation](ipv6-fresh-evaluation-results.md) compares
the same two frozen forests on four new user-started visits over5–6 November.
At ten packets, the added-data forest gets22/22 local flows right versus7/22
for the control; target-visit-balanced recall is1.0 versus0.462121. All three
fixed descriptive checks pass, all162 vectors replay exactly, and eight matrices
independently recount. This is a small two-service IPv6 hotspot result, not
universal accuracy or calibrated confidence. No extra recording, fit or default
change follows; B17 remains in the app.438-test software checkpoint unchanged.
The agent's [working Windows command route](windows-command-runner.md)
restores autonomous execution through `cmd.exe` without changing permissions.

The following entries retain earlier experiment checkpoints.

The [first fresh-evaluation visit](ipv6-fresh-evaluation.md#first-actual-youtube-visit--usable)
is archived: four browser-verified YouTube/IPv6 flows, all30 packets, with clean
packet checks and exact99-vector source replay. One of four visits is usable;
both frozen forests remain unscored until collection completes. No model-quality
claim or default change follows.438-test software checkpoint unchanged.

The following entries retain earlier experiment checkpoints.

The [next fresh evaluation](ipv6-fresh-evaluation.md) has a frozen four-visit
protocol and tested collection/scoring path. First YouTube slot is prepared;
capture is stopped and remains user-started. Both forests will be scored only
after all four new visits are archived.438 Python tests and132-file lint/format
pass. No fresh quality result, policy fitting or default change yet.

The following entries retain earlier experiment checkpoints.

The [real-data retraining pilot](ipv6-realdata-pilot.md#actual-outcome)
completed on 5 November: adding the 19 verified IPv6 training flows improved
reused local development F1 from 0.781 to 0.984. At ten packets, raw correctness
rose from 12/17 to 17/17; both services improved. All five fixed local/public
checks pass, and all 4,126 saved vectors replay exactly. This is a promising
single-seed development result, not fresh accuracy or a calibrated live release.
The candidate is saved separately; B17 remains in the app, and further acquisition
is paused. 424 Python tests and 130-file lint/format pass.

The following entries retain earlier experiment checkpoints.

The [first-date fresh sessions](fresh-browser-sessions.md#first-instagram-visit-and-first-date-completion)
both pass: complete YouTube IPv6 acquisition and four Instagram IPv6 flows,
including three complete prefixes. Browser/reference/packet/source-replay checks
pass. Remaining four sessions are reserved for a later date. This adds real
acquisition data; it does not establish a repaired classifier or new accuracy.

The following entries retain earlier experiment checkpoints.

The [first fresh-session visit](fresh-browser-sessions.md#first-youtube-visit-archived)
passes: six browser-verified YouTube IPv6 flows, each30 packets, with fresh-Chrome
proof and packet checks. This is one usable acquisition visit. New model training,
independent quality evaluation and deployment remain pending.

The following entries retain earlier experiment checkpoints.

The [revised acquisition workflow](fresh-browser-sessions.md) uses distinct
Chrome/capture sessions, with one complete IPv6 flow per visit and six visits
maximum. Browser-lifetime checks enforce the restart procedure.412 Python tests
and127-file lint/format pass. Chrome must be fully closed before first preparation;
capture stays user-started. Earlier failed scopes remain closed and model
reliability remains unresolved.

The following entries retain earlier experiment checkpoints.

The [hotspot visit](hotspot-family-feasibility.md#first-actual-user-started-visit)
captures two verified YouTube IPv6 QUIC connections, both30 packets with clean
packet checks. Real IPv6 acquisition works, but the declared three-connection
support minimum is unmet, so the scope stops. No repeated recording or model
promotion follows. Single-video connection yield is a collection-design limit;
these two flows are not a model-quality or reliability result.

The following entries retain earlier experiment checkpoints.

The [current network check](network-ipv6-check.md) confirms Wi-Fi has no
usable IPv6 Internet path: no global IPv6 address/default route, and explicit
IPv6 TCP fails NetworkUnreachable while IPv4 connects. YouTube advertises IPv6
addresses. The missing-IPv6 collection scope stays stopped; router/ISP cause
and dependable model recognition remain unresolved.

The following entries retain earlier experiment checkpoints.

The [new family collection](family-coverage-plan.md) stopped at its first
visit: five browser-verified YouTube connections passed packet checks but all
used IPv4. The declared IPv6 training-support gate was not met. The capture is
preserved; no repeat recording, later slot, training or promotion follows.
Network-wide IPv6 availability is not established by this result.

The following entries retain earlier experiment checkpoints.

The [verified family audit](family-coverage-audit.md) finds IPv4-only local
training and uneven family coverage in development. The [bounded new collection
workflow](family-coverage-plan.md) now checks family support, single attempts,
dates and training isolation before the next real-data study.403 Python tests
and124-file lint/format pass. Capture remains user-started; new model fitting,
real-family evaluation and calibrated deployment are still pending.

The following entries retain earlier experiment checkpoints.

The [bounded size-robustness pilot](size-robustness-study.md) is complete.
The exact matched clean forest reproduces. Size jitter improves local abstract-
stress F1 from0.658 to0.852, but loses clean Instagram recall and public class
quality. Relative-size features also help stress scores but severely regress
Instagram. Neither passes all fixed gates; seeds42/123, calibration, live
activation and candidate benchmarks stop. All18,567 vectors replay exactly.
395 Python tests and121-file lint/format pass. These are single-seed reused
development/stress results, not real IPv6 accuracy. B17 remains the app model.

The following entries retain earlier experiment checkpoints.

The [YouTube failure diagnosis](youtube-failure-diagnosis.md) finds a concrete
size-sensitivity problem: earlier matched YouTube flows use IPv4/1,250-byte
starts; the failed batch uses IPv6/1,230-byte starts. Browser records confirm
the sizes. An abstract size-only substitution improves the new ten-packet
predictions from3/6 to6/6, while the reverse damages earlier results from7/7 to1/7.
This diagnoses model brittleness, **not a validated correction or new accuracy
claim**. Original local training starts at1,250 bytes for both services. No
retraining, policy change, capture or activation followed.375 Python tests and
118-file lint/format pass; UI unchanged. B17 remains the app model.

The following entries retain earlier experiment checkpoints.

The [fixed forest confidence-policy workflow](forest-policy-calibration.md#actual-calibration-result-stop)
has stopped after two usable calibration visits. At ten packets, raw predictions
are correct for 5/5 Instagram and 3/6 YouTube connections. None of the 101 declared
thresholds meets the local error/coverage/support rules. No policy bundle or final
recordings follow this failed calibration. An independent audit replays all 1,089
local/public vectors exactly and recounts the grid. These small calibration results
do not establish general accuracy. Current software:
366 Python tests and 116-file lint/format pass; UI unchanged from its seventeen-
test/build checkpoint. B17 remains the app model.

The following entries retain earlier experiment checkpoints.

The [forest runtime check](forest-runtime-and-next-stage.md) preserves
all saved predictions exactly while reducing measured ten-packet single-flow
p50 from 27.7 to 3.1 ms. The simpler forest is the next local calibration
candidate after its primary quality tie; confidence-policy/final evidence and
live integration are still pending. B17 remains the app model. Latest checks:
355 Python tests and lint/format pass; UI unchanged from its seventeen-test/build
checkpoint.

The latest [paired fresh-session result](prospective-paired-followup-results.md)
completes four visits across two dates: both frozen candidates get **20/22**
connections right at the primary ten-packet endpoint. The neural model helps at
five packets; the forest is stronger at twenty. The descriptive screen passes,
but both policies remain unfitted and B17 stays in the app. All 170 saved vectors
replay exactly. The UI now shows reference evidence ON/OFF before Start and
remembers explicit selection across refreshes in the same tab. Current checks:
354 Python tests, 17 UI tests, production build and formatting/lint pass.
These are small-sample local results; calibrated live deployment remains pending.

The [fresh-session paired comparison](prospective-paired-study.md) is stopped:
the third attempt had reference checking off and retained zero native flow
records. Two prior usable visits and the failed attempt are preserved. No
replacement recording, final slot or candidate scoring follows under this plan.
The browser log alone cannot recover the missing native evidence. Current
software checks: 353 Python tests and 113-file lint/format pass; prior experiment
checkpoints below retain their dates.

A local application for studying **early encrypted-QUIC service classification** from packet sizes, directions and timing. One FastAPI service serves one React/TypeScript screen with separate Live and Replay modes.

**Status: real trained artifacts and user-started live capture work; dependable local service recognition remains unresolved. This is not a model-validated live release.** A frozen three-seed comparison selected augmented cross-entropy TCN B17. Its held-out CESNET results are recorded separately from local-network failures; contrastive loss did not justify retention. Missing weights cause an explicit error, never random or recorded predictions.

The [latest checkpoint-specific-head experiment](prefix-linear-probe-study.md) gets **59/63** existing development prefix cases right, with mean-prefix F1 **0.95120**. Five-packet correctness improves from **11/17 to 16/17** over the [shared pooled-feature head](pool-linear-probe-study.md), which gets 55/63 overall. Both services improve against that shared head, but Instagram remains one repeated case behind the latest forest (21/24 versus 22/24), failing the strict nonregression gate. A recorded solver retry extended only the iteration cap after the initial attempt stopped before scoring. Both artifacts pass exact replay and dataset-free inference. These are seventeen reused development connections across three visits; B17 remains the default.

The [completed preceding adaptation study](browser-selection-followup-results.md) preserves the forest/TCN result and its first-seed stop. It is not reopened by the separate linear-probe experiment.

The [earlier approach comparisons](approach-comparison.md) test ordered packet retrieval and a frozen official pretrained encoder: **25/54 and 43/54** legacy development checkpoints correct, versus the earlier forest's **45/54**. Neither passes its fixed local comparison gate. Their cohort differs from the latest study. Protected calibration/final records stay excluded from the new development comparison, and the app still uses B17.

A further [same-connection browser-window comparison](browser-window-study.md) got **9/14** development connections correct at both one and three seconds, versus **11/14** for its browser-prefix control. Both fail the fixed improvement/recall gates. This tiny reused two-service diagnostic does not validate capture-side accuracy.

The screen shows arriving prefixes, model alternatives, uncertainty and measured event timing. An optional metadata identity lane stays separate from the packet model. Optional **1- and 3-second statistics** continue after packet thirty. Their [first genuine capture](window-engineering-01.md) retained 33 flow windows, including 15 exceeding the model prefix, with up to 1,700 packets. Internal consistency passes; independent window-panel verification, full feature parity and a validated capture-side longer-window classifier remain pending. Capture starts only with the user's selected interface and Start button.

Further [engineering checks](engineering-checks-20261028.md) preserve the original Stop reason, measure window-event receipt separately, verify offline windows beyond thirty packets with native TShark, and bound stalled extraction. A real-artifact CPU stage benchmark records B17 forward/full-predictor p50 at 15.7/16.3 ms on this host; those measurements exclude capture and browser delivery.

The [refreshed screen](ui-refresh-20261029.md) adds guided setup, readable interface names, searchable connections, a chart beside the service estimate and expandable research details. **Sixteen UI tests, production build and UI formatting pass at the unchanged UI checkpoint.** The latest Python checkpoint is **343 passing tests**, plus lint/format for 109 active files on this Windows host. Hosted CI and untested platforms are not claimed as passed. The [release-gate audit](release-checklist.md) lists remaining evidence. The original [bounded collection plan](browser-development-v3.md) retains its frozen roles; its declared follow-up and the unscored window check remain separately documented.

Read the [beginner-friendly interview guide](interview-guide.md), [model card](model-card.md), [data card](data-card.md), [architecture](architecture.md), and [full evidence/status history](implementation-status.md). The [research review](realtime-classification-research.md) explains the alternative approaches and their limits.

## Run locally

Python 3.11 is the tested Python version. Node 20.17 worked locally; Node 22 is used in CI. TShark/Npcap is required only for capture and offline PCAP extraction.

For a fresh checkout, in PowerShell:

~~~powershell
python -m venv .venv
./.venv/Scripts/python.exe -m pip install --no-deps -r requirements-cpu.txt
./.venv/Scripts/python.exe -m pip install -r requirements.txt
npm --prefix ui ci
npm --prefix ui run build
./.venv/Scripts/netembed.exe serve
~~~

Open http://127.0.0.1:8000. This starts the application, **not capture**. Without a bundle it provides an honest unavailable-model screen. After generating a legitimate artifact, use:

~~~powershell
./.venv/Scripts/netembed.exe serve --bundle experiments/full-real/20261024-151720-3532794c/bundle
~~~

The selected bundle is a local, ignored artifact and must be regenerated if absent; its expected metadata SHA-256 is in the decision record. Select a local interface, then personally press Start. Sessions last two minutes in the UI (API maximum ten minutes); Stop, viewer disconnect, or service shutdown ends capture. Start before creating new QUIC connections. VPNs, TCP/TLS and mid-flow packets can be unsupported. Do not assume a browser navigation labels every background flow.

This laptop also has a verified local inference archive at
`artifacts/local/NetEmbedAI-v2-default-B17.zip` (423,237 bytes), SHA-256
`f9ca92fd82ea3cbc4254238b68993027e3a12715aa02f6ff9d1107bd21abd746`.
It includes the complete bundle, frozen decision, model card and dataset credit;
it contains no training data or resumable checkpoint. It is not tracked or hosted.
Copy it to a fresh checkout, verify the checksum, extract to a new directory and
pass its `bundle/` folder to `serve --bundle`. The archive was actually loaded in
the isolated clean checkout and produced matching real-model/API inference.
To reproduce a local archive from the selected bundle:

~~~powershell
./.venv/Scripts/python.exe scripts/package_bundle.py --bundle experiments/full-real/20261024-151720-3532794c/bundle --output artifacts/local/default-copy.zip
~~~

The helper validates the real bundle and decision, refuses existing output paths,
and writes deterministic ZIP headers for identical member bytes plus a `.sha256`
sidecar. It neither trains nor publishes. The selected metadata identity remains
`18c43fe12262b81d4a3001df150a278865f3908ddd3aab934822fc0c9e5750fb`.

For a useful local test, follow [Testing on your laptop](local-testing.md).
The optional handshake-reference checkbox checks a visible hostname against the
published CESNET map **only for evaluation**; it never changes model predictions.
An attributed mismatch is retained rather than explained away as background traffic.
If handshake attribution is unavailable, the optional offline
[browser-log matcher](browser-attribution.md) correlates a user-saved Chrome
NetLog with a fresh opted-in capture export. It preserves all model outputs and
refuses ambiguous matches. The [local development recordings](browser-selection-followup-v1.md#single-visit-archived--30-october) now have independently matched references and socket-prefix checks. These partial checks do not establish full exporter/wire-order parity or general live accuracy.

On Linux/macOS use .venv/bin/python and .venv/bin/netembed; install native TShark through your OS package manager. The app never installs capture drivers. NETEMBED_TSHARK overrides the executable path. NETEMBED_THREADS defaults to four for CLI inference. NETEMBED_EVALUATION can point to a generated report whose artifact ID matches the bundle. Origin restrictions default to localhost ports 8000 and 5173.

The first pip step selects the pinned CPU Torch wheel on Windows/Linux x64 from
[PyTorch's official CPU index](https://pytorch.org/get-started/previous-versions/#v251).
It installs no dependencies until the second step resolves them under the lock.
macOS and other architectures skip that CPU-index pin and use the native wheel
available through the project requirements; those platforms have not been tested
locally. No GPU hardware or CUDA packages are required for the CPU setup.

## What is implemented

- A shared strict 1–30-packet schema, explicit valid lengths, training-only saved normalization and last-valid causal TCN readout.
- Checksummed inference bundles for the existing compact TCN and a Random Forest baseline. Inference never opens training data. JSON forest export avoids runtime pickle loading.
- Chronological data manifests, bounded HDF5 and Zenodo CSV ZIP export, matched CE/SupCon training configurations, deterministic raw-unit stresses, resumable training, per-prefix/per-class reports, saved predictions and calibration coverage curves.
- Local API with readiness, bounded requests, single/batch inference and one WebSocket capture stream.
- TShark field parsing, bidirectional IPv4/IPv6 grouping, Initial-packet eligibility, bounded flows/queues, prefix checkpoints, loss/backlog counters and process cleanup.
- One responsive screen showing actual packet metadata, alternatives, decision status, model identity and measured timing; recorded JSON replay supports stepping and prefix controls.

The default is the seed-17 augmented cross-entropy TCN, selected by the frozen development rule and evaluated once on the held-out week. The forest is substantially worse under that rule; matched SupCon runs did not meet the retention threshold. The [model card](model-card.md) gives the measured quality and limits. One real user-started session verified packet-to-model delivery, not local service accuracy.

## Verify and reproduce

~~~powershell
./.venv/Scripts/python.exe -m pytest -q
./.venv/Scripts/python.exe -m ruff check src/netembed tests
./.venv/Scripts/python.exe -m ruff format --check src/netembed tests
npm --prefix ui test
npm --prefix ui run build
./.venv/Scripts/netembed.exe capture-file --pcap tests/fixtures/rfc9001.pcap --output parity.json
~~~

The PCAP is an attributed, constructed RFC test vector, not captured user traffic or benchmark data. Tests never start real capture. CI runs software checks on Windows/Linux and frontend checks; full training is intentionally outside CI.

[Reproduction commands and experiment rules](experiments.md) · [architecture](architecture.md) · [data card](data-card.md) · [model card](model-card.md) · [beginner interview guide](interview-guide.md)

## Scope and evidence

The model may use only transport payload bytes, client/server direction and milliseconds between observed packets. Addresses group packets transiently; domains, addresses, process names and whole-flow totals are excluded from prediction. Scores are not guaranteed correctness probabilities. A confidence refusal does not detect an unknown service.

Historical TensorFlow work remains in legacy/. The previous PyTorch scripts and results are preserved under legacy/pytorch-v1/ with provenance. Their metrics do not describe this version. eBPF, cloud infrastructure, open-world/few-shot recognition, extra architectures and line-rate or adversarial guarantees are out of scope.
