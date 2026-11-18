# Implemented approach comparisons — 28 October 2026

## Prefix-specific linear heads — 31 October

The [four-head experiment](prefix-linear-probe-study.md) improves the shared
head's 55/63 to 59/63 on the same development cases, F1 0.95120. Five-packet
correctness rises from 11/17 to 16/17 and both class mean recalls improve.
Instagram remains one repeated prefix case behind the latest forest; the strict
nonregression rule still blocks progression. The original solver-limit stop and
separate pre-score numerical recovery are preserved. Exact replay, dataset-free
inference, 343 Python tests and 109-file lint/format pass. No default change or
new capture. These reused selection results are not independent local accuracy.

## Fixed pooled-feature linear probe — 31 October

The [new separately declared experiment](pool-linear-probe-study.md) is complete:
official frozen pre-refinement 448-value features plus one trained linear head
give 55/63 correct, mean-prefix F1 0.90272 on the same seventeen connections as
the latest forest (47/63, 0.78056). YouTube recall improves; Instagram recall
falls against the latest forest, failing the fixed per-service gate. Exact
artifact replay and dataset-free inference pass; B17 remains unchanged.
331 Python tests and 104-file lint/format pass. This is reused development,
not new independent local accuracy. The older 256-value neighbor screen below
used another cohort; it does not isolate the feature layer's causal contribution.
Linear probing is now tested; encoder fine-tuning remains untested.

The following entries preserve their historical dates and conclusions.

## Latest prospective follow-up — 30 October

The [single supplemental recording and fixed seed-17 CE/forest comparison](browser-selection-followup-results.md)
are complete. On seventeen later selection connections (63 correlated prefix
cases), the new forest gets 47/63, macro-F1 0.78056, versus the paired previous
forest's 46/63, 0.76035. Instagram recall improves, but YouTube recall regresses
from 0.74722 to 0.64444 and fails the frozen gate. Best neural checkpoint F1 is
0.50797; no candidate qualifies. The first-seed stopping rule prevents additional
seeds and calibration. No further capture or default change. This is a different
cohort from the legacy 54-case screens below; their counts are not a paired
comparison with this result. The independent artifact audit reproduces saved
local probabilities exactly. Current software checkpoint: 318 Python tests;
no new software changes or test rerun for this result-only update.

The following entries preserve their earlier checkpoints.

## Current status audit — 29 October

The following distinguishes actual experiments from partial implementation and
research. Saved ordered-neighbour, pretrained-encoder and browser-window report
hashes were rechecked against the recorded values and are unchanged. No new fit,
parameter search, capture or model promotion was performed for this status audit.

| Approach | Work actually completed | Outcome / missing evidence |
| --- | --- | --- |
| Packet-only heuristic profiles | Exported nearest signatures and conservative interval rules; same underlying training data and declared development cases | Nearest signature 26/54 correct; interval rule answers 19/54 with four errors. Fails the gates. This is not the internship's whole activity/identity cascade. |
| Ordered raw-packet neighbours | Implemented and evaluated fixed 1-NN over size/direction/time sequences | 25/54 correct against the earlier summary forest's 45/54. Fails local comparison and recall gates. |
| Official pretrained CESNET encoder | Legitimate downloaded weights, validated transforms, frozen embeddings, fixed cosine 1-NN, standalone artifact and CPU checks | 43/54 correct, but weaker Instagram recall, especially at thirty packets. Fails the gate. Linear-probe heads and encoder fine-tuning were not tested. |
| Feature and early-position diagnostics | Fixed size/direction, timing/direction and first-eight-position masking variants of ordered retrieval | No successful repair. Masking and original retrieval both get 17/40 on the shared surviving budgets. No paired masked-input neural retraining or causal handshake explanation is established. |
| One-/three-second features | Bounded native collector/UI, genuine unscored collection check, offline native fixture parity, and a fixed browser-observer forest comparison | Both browser-window models get 9/14 connections versus 11/14 for their matched browser-prefix control. No validated native-capture window classifier or activity classifier. |
| Separate name evidence plus packet estimate | Independent metadata identity lane, explicit disagreement/refusals and coverage check | Zero usable passive names among the 31 legacy browser-mapped development connections under the conservative policy. Coverage does not establish identity accuracy or prove actual ECH. |
| nDPI, JA4, DNS/IP and OS/process-assisted methods | Primary-source research and review of the internship's design principles | No full integrated cascade or head-to-head local evaluation. No hostname/IP/process shortcut silently enters packet prediction. |
| CE versus CE+SupCon | Original matched augmentation/no-augmentation comparison at three seeds | Augmented CE B17 remains the frozen default. Contrastive loss did not meet its retention rule; this original benchmark is separate from local transfer. |

The 54-case screens reuse fourteen legacy development connections with repeated
prefixes; they are not 54 independent tests. The browser-window experiment uses
one decision per connection, a two-label local-only model and a different matched
control. Its 9/14 cannot be compared directly with 25/54 or 43/54. All are small
development findings, not current-network accuracy guarantees.

The old adapted forest's 45/54 development result also did not make it a reliable
deployment: it subsequently failed fresh calibration support/per-service error
gates and stays disabled. The app has not silently switched to that forest.

The [new collection](browser-development-v3.md#fourth-recording-archived--29-october)
now has all six declared recordings archived. Training remains 22 Instagram/21
YouTube connections. Selection has seven Instagram/five YouTube connections,
five full prefixes per service, and stays separate from training. YouTube is
one short of the fixed six-connection minimum; the exact runner refused before
fitting or creating model output. This cycle therefore has no new candidate
comparison result. The six-recording cap is reached, with no automatic extension
or relaxed gate. Its frozen candidate set remains the compact CE TCN and
same-data summary forest. It does
not silently add the alternative heads, retraining studies or full hybrid cascade
listed above. Further experiments would need a separate declared protocol and
appropriate independent evidence; continuing to search the old selection records
would not supply that evidence.

The sections below preserve the original experiment and software checkpoints.

Latest follow-up: the [browser-window study](browser-window-study.md)
completed its frozen same-connection comparison. The browser-prefix control
gets 11/14 development connections right (F1 0.78462); one-/three-second
models each get 9/14 (0.64103/0.62567). Both fail improvement and recall gates.
These are reused two-service browser-observer records, not live-capture
accuracy; no model was promoted. Full Python verification is now 264 tests.
The earlier approach results below retain their original cohorts and budgets.

The ordered-neighbour and official pretrained-encoder screens are complete.
Neither passes the fixed local comparison gate against the previous summary
forest. The pretrained representation improves substantially over the earlier
adapted TCN on this reused development set, but loses Instagram recall at thirty
packets. No default model or confidence policy changes.

The user authorized implementing the research alternatives sequentially on
28 October. Optional longer-window statistics and a separate metadata identity
lane are now implemented too. They are not a trained activity classifier or a
new validated service classifier. Actual longer-window capture validation and
matched labelled training/evaluation remain pending.

Follow-up: the [first genuine window trial](window-engineering-01.md) is archived.
It verifies server collection beyond packet thirty and internal consistency;
independent window-panel delivery, full parity and model-quality gates remain
pending. The implementation-stage statements below preserve their original
software/preflight checkpoint.

## Fixed existing-data comparison

Both new retrieval methods use the same 14,000 public training flows and seventeen
legacy local training connections (five Instagram/twelve YouTube). The local
development set is fourteen later connections from two visits, seven per service,
with 54 available 5/10/20/30-packet checkpoints. These are explicitly retired
`cal-01` recordings, already used in development. `cal-02`, prospective `dev-03`
onwards, and all final examples/reports are excluded by the study's scoped Python
open guard. Source hashes, record IDs, independent-reference bindings, original
retirement authorization and session separation are verified before fitting.

Each retrieval method retains one reference per training flow. Unlike the paired
forest/TCN, it does not impose 75/25 public/local mass weighting. The underlying
data and query budgets match, but differences cannot be attributed solely to
the choice of learner. These are exploratory comparisons, not independent local
accuracy or causal transfer-learning estimates.

| Approach | Correct / available local checkpoints | Mean-budget target macro-F1 | CPU p50/p95, ms |
| --- | ---: | ---: | ---: |
| Existing adapted CE TCN, epoch 5 | 30/54 | 0.57459 | 14.99/18.65 (preceding comparison) |
| Existing summary forest | 45/54 | 0.87386 | 25.61/31.32 (preceding comparison) |
| Ordered packet 1-NN | 25/54 | 0.53896 | 9.70/11.35 |
| Official frozen embedding + cosine 1-NN | 43/54 | 0.83954 | 19.37/24.13 |

F1 averages per-budget macro-F1 over the observed target classes; it is not the
fraction correct. Wrong rankings to any of the other eight classes remain
errors. Prefixes and connections share visits. CPU figures use the same real
thirty-packet input, 1,000 calls, fifty warmups and two configured threads.
The two new timings were measured during these studies; paired baseline timings
are retained from the earlier experiment, not claimed as a simultaneous speedup
experiment. All exclude capture, HTTP and browser delivery. Neither retrieval
distance nor cosine similarity is a calibrated correctness probability.

## Ordered retrieval and feature/early-position diagnostics

Config and source were committed at `bdf5ba4` before evaluation. Exact L1 nearest
neighbours compare ordered packet triples with IPT clipped at 1,000 ms and
divided by ten, unscaled sizes/directions, and zero padding. One bank is used per
checkpoint; an arbitrary short query uses the smallest bank at least its actual
length, independent of the requested future cap. No future query values enter
inference. Reference-order ties are deterministic and agree with alternatives.

| Fixed representation | Local correct | Local mean-budget F1 | Historical control F1 |
| --- | ---: | ---: | ---: |
| Original three channels | 25/54 | 0.53896 | 0.91295 |
| Size and direction, no timing | 26/54 | 0.57468 | 0.91346 |
| Timing and direction, no size | 24/54 | 0.45947 | 0.79120 |
| Mask first eight positions in queries and references | 17/40 ranked; fourteen withheld | Not comparable across all four budgets | Not comparable across all four budgets |

Masking eight positions leaves no evidence at budget five. Such queries abstain;
short references with no remaining observations are excluded. The full four-budget
mean is null rather than fabricated from the surviving subset. On the common
10/20/30-budget local cohort, both original and masked retrieval get 17/40 right.
At thirty packets both get zero of six Instagram connections right. This fixed
retrieval diagnostic does not establish that handshake dependence explains or
cannot explain a differently trained neural model. No neural masked-input
retraining or threshold search is claimed.

The ordered candidate passes the historical-public retention screen but fails
local comparability (within 0.01 of the forest) and per-service recall
nonregression. Ablations are diagnostics, not extra promotion candidates selected
after looking at their scores. No neighbour-count or scaling sweep followed.

## Official frozen encoder transfer

Config and source were committed at `4609a9c` before evaluation. The pinned
`cesnet-models==0.4.1` wheel is installed with `--no-deps --target` into an ignored
project directory, leaving the active service environment unchanged. The official
encoder has 1,004,117 parameters and produces normalized 256-dimensional features.
Its head is a fixed exact cosine 1-NN over training-only embeddings, separately
computed for each prefix budget. The encoder is frozen; no fine-tuning, head
search or new neural training took place.

The adapter uses upstream clipping and channel order `(batch, 3, 30)`, restores
padding zeros, loads all encoder parameters strictly with weights-only Torch
loading, and validates finite unit-length outputs. It never downloads weights
on inference or substitutes random weights when loading fails.

| Packet budget | Valid connections | Correct | YouTube recall | Instagram recall |
| --- | ---: | ---: | ---: | ---: |
| 5 | 14 | 11 | 7/7 | 4/7 |
| 10 | 14 | 12 | 7/7 | 5/7 |
| 20 | 13 | 12 | 7/7 | 5/6 |
| 30 | 13 | 8 | 6/7 | 2/6 |

More packets do not uniformly improve this candidate. Its mean-budget Instagram
recall is about 0.613, below the forest's 0.780, despite better YouTube recall.
It fails both predeclared local gates; this is not a reason to hide its thirty-
packet results or select a new stopping budget on the same evaluation records.

The historical public control gives 1,940/2,000 capped cases correct and F1
0.96997. **It is retrospective:** the published encoder was pretrained on week
46, after that control's week 45. Its original pretraining also overlaps our
old final-test period, so that final test is never opened or presented as an
independent comparator. No exact pretraining-record overlap audit is claimed.
The old B17 final report remains its own result.

Official HTTPS weight retrieval succeeded after transient TLS/connection errors;
certificate verification stayed enabled. The wheel hash matches PyPI. The
weight hash is locally measured from the official download, not an independently
published checksum. Upstream software attribution is carried in the saved wheel;
the generated artifact stays local and unpublished.

## Explicit metadata identity: implemented, limited coverage

`GET /capture/assessment` and the screen keep a name-derived identity separate
from the unchanged packet-model estimate. A mapped name can supply an identity
association with its source, without receiving a model confidence score.
Missing, protected, conflicting, ambiguous and unsupported name outcomes remain
unresolved. A confident model estimate cannot overwrite those refusals, and a
name cannot overwrite the model output. Conflicts stay visible.

On the six legacy development recordings above, all 31 browser-mapped
connections have `protected_name_unverified` passive status. **Zero have usable
named identity under the current conservative policy.** This is coverage, not
classification accuracy or proof that all 31 actually negotiated ECH: GREASE
can produce an indication too. Adding this lane has not established a repair
for these local flows. Browser name-derived references cannot independently
grade a name-derived identity. No nDPI, JA4, DNS/IP or OS-process classifier is
silently substituted, and endpoint-assisted live attribution remains future work.

## Longer windows: collection/display ready, model evidence pending

Before Start, the new **Collect experimental 1- and 3-second statistics** option
enables a separate observation path. It defaults off. The existing model still
uses its exact first thirty packets. Supported Initial/grouping rules and
millisecond/UDP-payload/client-direction semantics stay unchanged.

Windows are half-open intervals from the first captured packet: `[0, 1s)` and
`[0, 3s)`. Bounded accumulators record directional packet/byte counts, payload
moments, large-payload fraction, direction switches and 100-ms packet-count bins.
They continue after the thirty-packet model prefix freezes. No complete-flow
totals or packets beyond the horizon become early features. Guard ticks publish
through the same WebSocket, the UI retains the same bounded flow rows, and
`GET /capture/windows` exports up to 256 retained observations without names,
addresses or payload content. Stop snapshots partial windows and clears active
grouping state. Evidence is ephemeral until exported and clears on the next Start.

An elapsed window is not proof of loss-free capture. Delayed parsing can revise
an elapsed snapshot; a dedicated counter records that. Reordered observations
are excluded and counted. Queue/evidence evictions remain limitations. The
screen explicitly says statistics only: there is no trained activity or
longer-window service classifier, inferred activity truth or live quality score.

Constructed metadata tests verify interval boundaries, units, continued counting
past packet thirty, partial Stop, late revisions, reordering and bounded state.
They do not satisfy genuine live validation. Saved prefix-only exports cannot
recover later on-wire traffic; a deliberate live session and a separately frozen
matched-data study are needed before assessing classification benefit. Keep
this experiment separate from the frozen version-3 development roles.

## Software, artifacts and reproduction

**248 Python tests passed**, one existing Starlette/AnyIO deprecation warning;
Ruff lint and formatting passed for 84 active Python files. **Ten UI tests**,
TypeScript/production build and Prettier passed. Hosted CI is configured, not
claimed executed. No test opened a live capture interface.

Both actual retrieval artifacts reload and infer with external training/browser
files, original source weights and network access blocked by a scoped Python
audit hook. All 54 local probes reproduce after save/load for each model (each
variant for ordered retrieval). The pretrained maximum similarity delta is zero.
These are scoped checks, not an OS sandbox or new accuracy observations.

| Local file | SHA-256 |
| --- | --- |
| `ordered-neighbors-01/report.json` | `e8dd1b1583ee391de9ebacc0893764df1f1a1f3c1268d5529d1b53f4d90094e8` |
| `ordered-neighbors-01/neighbors/metadata.json` | `321673e5280c20254fecc1067c603da41bfac80c6367c273edd3d9bcce3c1757` |
| `ordered-neighbors-01/neighbors/references.npz` | `ea5fcf86a9e12c4985a005851065348532d80d969eeb278c7a1a0315487629ab` |
| `pretrained-neighbors-01/report.json` | `cd47dc9d319f4dfafcc1da3fab78f4ff9241f6fef7922abbf3e8deb3733d1c5b` |
| `pretrained-neighbors-01/bundle/metadata.json` | `176a385e31913c6f25bbd446f335abc85e73b5ac282b1b8204a3a5824353de73` |
| `pretrained-neighbors-01/bundle/encoder.pth` | `dc4b3333388239ac25b8c028c922965e2333cc151dd5fad951950099e86fabc4` |
| `pretrained-neighbors-01/bundle/banks.npz` | `2271a07a6c349fba20d345775dbc2b992e6dd45179cafa5c1b491e7702f7f031` |

Paths in the table are relative to `experiments/browser-adaptation/`. The
pretrained bundle includes its pinned wheel, weight file, four reference banks,
class map, transform/policy/provenance and file checksums (about 58 MB); the
ordered artifact contains its saved exemplars and metadata (about 1 MB).
The examples inside a retrieval artifact are its model reference memory, not a
requirement to reopen the original training dataset. They remain local/private.

From `traffic_classification`, with the existing legitimate private data and
upstream files, use fresh output directories:

```powershell
.venv/Scripts/python.exe scripts/study_packet_neighbors.py --output experiments/browser-adaptation/ordered-neighbors-repeat
.venv/Scripts/python.exe -m pip install --no-deps --target artifacts/local/upstream-models/python artifacts/local/upstream-models/cesnet_models-0.4.1-py3-none-any.whl
.venv/Scripts/python.exe scripts/study_pretrained_neighbors.py --output experiments/browser-adaptation/pretrained-neighbors-repeat
.venv/Scripts/python.exe -m pytest -q
.venv/Scripts/python.exe -m ruff check src/netembed scripts tests
.venv/Scripts/python.exe -m ruff format --check src/netembed scripts tests
npm --prefix ui test
npm --prefix ui run build
npm --prefix ui run format:check
```

The wheel can be recovered with `pip download --no-deps cesnet-models==0.4.1`
into the upstream directory; its expected SHA-256 is
`86acb26e5c1595e2d80546bc44859e3d0daf271a20cbb7fbc829fd513a56154b`.
The exact official weight URL and checksum are frozen in
`configs/pretrained-neighbor-study.json`. Download it to
`artifacts/local/upstream-models/30pktTCNET_256_CESNET_QUIC22_Week46_Domains.pth`.
The runner refuses a different hash. Do not disable HTTPS verification.

The updated service on `http://127.0.0.1:8001` is ready with the unchanged B17
artifact; four recorded 5/10/20/30-packet HTTP/direct checks match exactly with
two Torch threads. New routes start empty, both capture and experimental windows
are off, and no TShark interface was opened. The old stopped Reels session was
verified archived before restart. Further live work must be deliberately started
by the user. Neither new model is promoted or attached to the old B17 evaluation.

Private verification is in
`experiments/browser-adaptation/research-20261028/{implemented-standalone-verification,metadata-availability,service-verification}.json`.
The next evidence-dependent step is a controlled observation-window capture,
followed by a bounded matched training/selection protocol if the feature path is
usable. No reliable longer-window activity/service accuracy, new independent
calibration, full local exporter parity or completed live release is claimed.

One unscored engineering recording, `window-engineering-01`, has a pre-capture
intent in `artifacts/local/window-validation/`. Intent SHA-256 is
`2ba0be1ee96d5d76a890d0639ad9bdb1281323dfba2e62eeb4930662ffa05e26`.
It binds B17, Wi-Fi interface 9, the served UI, both explicit collection options,
one-/three-second horizons and a one-recording cap. It was prepared before the
subsequently archived recording linked above.
This functional check has no training/calibration/final role and does not replace
or bypass the later-date requirement of `instagram-dev-05`.

The following is the archived procedure for the completed engineering check,
not a request for another recording. For that check, refresh the app, select Wi-Fi, enable both the separate handshake
reference and experimental statistics, and deliberately Start. Open a fresh
Chrome YouTube connection and watch for sixty seconds while keeping the app
visible. Inspect the experimental window rows; model labels remain B17 estimates.
Stop and archive the stopped `/capture/local-evaluation`, `/capture/windows`,
`/capture/summary` and `/capture/status` responses before any new Start. No
browser NetLog or model accuracy claim is needed for this functional check.
