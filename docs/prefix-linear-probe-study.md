# Four checkpoint-specific linear heads

This is a separately declared experiment on 31 October 2026. The shared-head
study remains closed. Its eight errors include six at five packets and two on
one Instagram connection at ten/twenty packets. That error inspection motivates
this hypothesis; the reused selection cohort is not a new independent test.

The [fixed declaration](../configs/prefix-linear-probe-v1.json) inherits the
[shared-head protocol](pool-linear-probe-study.md), including all data bindings,
training roles, solver settings and the five forest/B17 checks. Only the heads
are specialized: one each at 5, 10, 20 and 30 packets. All four must converge
before any new development scoring. No winning-head mixture, shared-head
fallback, seed/regularization sweep, calibration, capture or app replacement.

The pretrained 448-value pooling encoder stays frozen. Its clipping transform
and the exact weighted training-only scaler from the shared model are reused.
Each head sees the same 14,000 public and 43 local training flows, truncated to
its checkpoint. The 75% public/25% class-balanced local weighting stays fixed;
each row retains its original quarter share of its flow weight, for total mass
14,043/4 per head. C=1, L2, LBFGS, tolerance 1e-5, maximum 500 iterations, seed17,
two CPU threads. Separate L2-regularized heads add parameters and penalties;
this is an experiment in specialization, not an equal-parameter architecture claim.

Short public flows remain present: a two-packet flow can be scored under an
explicit thirty-packet checkpoint using its two observed packets and zero
padding. The head budget is recorded separately from actual length. This
matches the training convention and the earlier public comparison's feature
budget. The standalone default uses the smallest checkpoint at least as large
as actual length; arbitrary intermediate lengths have no separate quality claim.
Over-budget input is rejected by the predictor. The CLI explicitly truncates
to `--budget` before prediction. Below five packets it reports insufficient
evidence; every other reply also withholds the accepted label because there is
no calibrated policy.

Selection remains seven Instagram / ten YouTube connections, three visits and
63 correlated available prefixes. The same 500 historical public-selection
flows are scored. No protected calibration/final files or additional sessions
are allowed. In addition to the unchanged forest/B17 checks, the four-head
candidate must not regress shared-head mean F1 or either mean class recall,
and must improve five-packet local macro-F1 by at least 0.01. These requirements
are fixed before fitting. Passing would motivate a separate independent
validation protocol; it does not itself authorize collection or promotion.

Run once with existing legitimate local inputs from the repository directory:

```powershell
.venv/Scripts/python.exe scripts/study_prefix_probe.py --output experiments/browser-adaptation/prefix-linear-probe-v1
.venv/Scripts/python.exe -m pytest tests/test_prefix_probe.py -q
```

The runner refuses existing output directories and preserves each converged
head and fit log. Any nonconverged head stops the experiment without development
scoring or a partial deployed model. All four heads and the complete base bundle
are exported before selection input is loaded. The base includes the frozen
encoder and scaler; its historical shared classifier is retained for provenance
and is never a fallback in the four-head predictor. Bundle checksums cover both
levels. No training data is required for inference:

```powershell
.venv/Scripts/python.exe scripts/predict_prefix_probe.py --bundle experiments/browser-adaptation/prefix-linear-probe-v1/bundle --flow experiments/browser-adaptation/pilot-01/benchmark-flow.json --budget 10
```

For an interview: the earlier experiment taught one classifier to handle all
four packet counts. This experiment keeps the feature extractor and scaling
identical but teaches a different small classifier for each count. We must
measure whether that improves early decisions without losing performance for
either service later. A wrong high score remains a wrong prediction, not proof
of certainty. Final local quality and genuine live-path evidence stay separate.

## Numerical stop and separately recorded recovery

The original declaration and implementation were committed as `e1f3c14` before
fitting. Its five-packet head reached 500 iterations without convergence after
34.36 seconds of fitting and 41.24 seconds of feature extraction. The original
stop rule was honored: no other head was fitted, no development prediction was
scored and no bundle was exported. This is an **inconclusive numerical attempt**,
not evidence that specialization improves or worsens quality.

To complete the authorized comparison, a separate [numerical-recovery declaration](../configs/prefix-linear-probe-solver-recovery-v1.json)
was recorded before any development scoring. It permits one new set of four
heads with a 2,000-iteration cap. This explicitly amends the computational limit
in a separate attempt; it does not rewrite or count as completion of the
original 500-iteration protocol. Solver, C, tolerance, data, quarter weights,
encoder, shared scaler, seed and quality rules remain unchanged. If any head
still fails to converge, the recovery stops without scoring or further retries.

The runner checks the original attempt's bound fit/protocol hashes and requires
that directory to contain only `fit.json` and `protocol.json`, so a scored or
otherwise changed attempt cannot enter this recovery path. Its distinct command is:

```powershell
.venv/Scripts/python.exe scripts/study_prefix_probe.py --config configs/prefix-linear-probe-solver-recovery-v1.json --output experiments/browser-adaptation/prefix-linear-probe-solver-recovery-v1
```

Use the recovery run's `bundle/` path in the prediction command if all four
heads converge. The original command intentionally retains its 500-iteration
limit. No recovery results were available when this amendment was written.

## Completed comparison

The recovery declaration was committed as `39a0ebe` before fitting. All four
heads converged, at 763 / 316 / 113 / 109 iterations for 5 / 10 / 20 / 30 packets.
Their portable probability calculations match sklearn exactly. The encoder
parameters/buffers and inherited training-only scaler are exactly unchanged.
No settings were changed after these development results were produced.

| Model | Correct prefix cases | Mean-prefix local macro-F1 | Instagram mean recall | YouTube mean recall |
| --- | ---: | ---: | ---: | ---: |
| Latest forest | 47/63 | 0.78056 | 0.92857 | 0.64444 |
| Shared pooled-feature head | 55/63 | 0.90272 | 0.80714 | 0.92500 |
| Four checkpoint heads | **59/63** | **0.95120** | **0.91429** | **0.94722** |

The hypothesis helps on this reused development set. Five-packet correctness
improves from 11/17 to 16/17, while Instagram improves from 19/24 to 21/24
repeated prefix cases and YouTube from 36/39 to 37/39. Both mean class recalls
improve relative to the shared head. The latest forest still has 22/24 correct
Instagram cases, so the original nonregression requirement remains unmet.
Seven of eight checks pass; that failed class check is retained. No automatic
calibration, additional captures, further numerical retries or default change.

| Checkpoint | Correct / available | Local macro-F1 | Instagram correct | YouTube correct |
| --- | ---: | ---: | ---: | ---: |
| 5 packets | 16/17 | 0.97368 | 7/7 | 9/10 |
| 10 packets | 16/17 | 0.96154 | 6/7 | 10/10 |
| 20 packets | 14/15 | 0.94444 | 4/5 | 10/10 |
| 30 packets | 13/14 | 0.92513 | 5/5 | 8/9 |

F1 averages the two observed local classes while predictions can be any of ten
supported services; it is not raw accuracy. The headline score and class recalls
give each checkpoint equal weight. The thirty-packet head loses one correct
YouTube case relative to the shared head. We preserve that result and do not
substitute the shared thirty-packet head after inspecting development scores.
Historical public-control mean F1 is 0.97452, versus shared-head 0.96848. This
control remains retrospective to pretraining, with no forward-test claim.

These are 17 connections across three visits, producing 63 correlated prefix
cases. The hypothesis was motivated by earlier inspection of these same errors.
It is useful development evidence, not an independent 93.7% live-accuracy claim
or a causal claim about future networks. Independent local quality, uncertainty
calibration and this model's genuine capture-path validation remain pending.
B17 remains the app default.

## Artifact and timings

The complete research artifact is
`experiments/browser-adaptation/prefix-linear-probe-solver-recovery-v1/bundle/`.
The run also contains the declaration/provenance in `protocol.json`, per-head
fit records, all 63 local prediction vectors, 2,000 historical-control vectors
and `report.json`. The original stopped attempt remains at
`experiments/browser-adaptation/prefix-linear-probe-v1/`, with only its original
fit and protocol. Files are local and ignored, with no upload or publication.

CPU measurements use the fixed real thirty-packet example, truncated explicitly
for each checkpoint, two CPU threads, 20 warmups and 100 calls per checkpoint.
The i7-1360P timings include the frozen encoder, selected head and reply. They
exclude loading, capture, queueing, HTTP and browser rendering.

| Head | p50 prediction ms | p95 prediction ms |
| --- | ---: | ---: |
| 5 | 19.54 | 26.37 |
| 10 | 20.52 | 24.07 |
| 20 | 19.88 | 23.53 |
| 30 | 21.89 | 27.74 |

Feature extraction took 176.70 seconds in total; fitting took 86.95 seconds.
The earlier stopped attempt separately took 41.24 seconds extracting features
and 34.36 seconds fitting. These stages exclude import, input verification,
development scoring, export and benchmark overhead. No new live event latency
measurement is inferred from these CPU timings.

## Verification and evidence inventory

343 Python tests pass, including twelve new prefix/recovery tests. Ruff lint
and formatting pass for 109 active files. Two dependency deprecation warnings
remain (Starlette/AnyIO and sklearn/SciPy). UI code is unchanged; its earlier
sixteen-test/build checkpoint was not rerun. No hosted CI run is claimed.

A fresh-process audit replays all 63 saved local probability vectors exactly
(maximum difference 0.0), independently recomputes local class counts and scores,
and rescores the 2,000 stored public-control predictions. It does not repeat
public inference. Original training data, protected inputs and original model
directories are blocked by a process audit hook. A second process blocks all
dataset access and runs all four heads using only the exported bundle, runtime
and supplied real example. The documented CLI matches its ten-packet reply
exactly. Accepted labels remain withheld even when raw scores are high.

The audit source is local at
`experiments/browser-adaptation/prefix-probe-audit.py`, SHA-256
`2f66b6c0555186750d4dba7127dbda85293f7e4d57d30faf144780524b95f9f7`.
Reproduce the checks with:

```powershell
.venv/Scripts/python.exe experiments/browser-adaptation/prefix-probe-audit.py
.venv/Scripts/python.exe experiments/browser-adaptation/prefix-probe-audit.py --standalone
.venv/Scripts/python.exe scripts/predict_prefix_probe.py --bundle experiments/browser-adaptation/prefix-linear-probe-solver-recovery-v1/bundle --flow experiments/browser-adaptation/pilot-01/benchmark-flow.json --budget 10
.venv/Scripts/python.exe -m pytest -q
.venv/Scripts/python.exe -m ruff check src scripts tests
.venv/Scripts/python.exe -m ruff format --check src scripts tests
```

The full recovery source commit is
`39a0ebefe30e6cc718257713e7295f98dbd70c7a`. The recovery declaration's
LF-canonical SHA-256 is
`5a1a34698a8438d047e6543b8a72e093c9377a9aa67a9bcf4966d01fa9ebc889`.
The original declaration's LF-canonical SHA-256 is
`77bcae2b5120293b413c16f8ec0683bf959837b3d0d05ab682d2de5d71cfe8de`.
Only committed configuration line endings are canonicalized. The following
evidence hashes are raw bytes, relative to the recovery run:

| File | SHA-256 |
| --- | --- |
| `bundle/metadata.json` (artifact identity) | `483dcd5ea9af2dce2da16c818ee73341f1eb328a032ad56a192c32b7f552e7dd` |
| `bundle/heads.json` | `1b159bdf23c85a33fc585c26de2d98ba762bc46f285e72c9722428b5232595ca` |
| `protocol.json` | `46b76ac93c8a03d33711fa7871200f2867d952368c05c6e663c33880ef08f96c` |
| `report.json` | `4e21a0623ad799d891ba49b311f88c19391173c2b7af17adf610cd15e4328632` |
| `local-predictions.json` | `d236485182d5d8894e85b7720bc0c726c1c124b222d054ab5a6356b901980392` |
| `independent-audit.json` | `474203f0f0a2bfdc5d5261ba7334ac4863e45fdaad787bad923caba789e7c995` |
| `standalone-audit.json` | `ab7df91faea903c3c5d0e1cb9fec22fc217dff545b90e12766451ab32445ca39` |
| `evidence-checksums.json` | `c6bbd09cda958f752d227d3cb2263ed3e83d0db283d7c9a774b130b2bcf69e67` |

The inventory includes every result and bundle component with byte counts.
The original encoder and bundled wheel retain their published-source local
hashes documented in the shared-head study. A fresh checkout needs legitimate
local transfer of the recordings/public inputs to retrain, or transfer of just
the research bundle and example to perform inference. No app integration or
real-live validation of these four heads has been performed.
