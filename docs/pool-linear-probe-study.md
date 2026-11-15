# Frozen pooling features and one linear classifier

This is a separate development experiment, declared on 31 October 2026 before
fitting. The completed selection-follow-up study stays closed. No new capture,
protected calibration/final data, app model replacement or policy fitting is
authorized by this experiment.

The [paper, section V-A](https://arxiv.org/html/2502.12930v2#S5.SS1), specifies
features after global pooling and before refinement for transfer. In the pinned
CESNET Models 0.4.1 architecture this is the 448-value output of
`backbone_model.cnn_ppi_global_pool`, also the input to `mlp_shared`.
`forward_features()` includes refinement and is therefore too late. The earlier
neighbor experiment used the final normalized 256-value embedding instead.
This is a concrete alternative representation/head, not proof that either change
causes any resulting improvement: both representation and classifier change.

For an interview, describe it this way: the pretrained network turns packet
sizes, directions and timing into 448 numerical features. We keep that network
fixed and teach a small classifier to combine those features into service
scores. Only the classifier and its training-data scaling are fitted here.
Changing the point where features are extracted changes what information the
classifier receives. A higher development score alone would not prove reliable
live classification; separate sessions and calibrated uncertainty would still
be required.

The source and official weight files are checked before use. Extraction observes
the original forward pass, checks equality with the refinement input, removes
hooks even on failure, and leaves all parameters and buffers frozen in eval mode.
Input remains actual packet prefixes, padded to 30, in channels-first order:
milliseconds, client/server direction, UDP payload bytes. The pinned upstream
clipping transform is saved with the artifact. Domains, addresses, trial names
and browser identity never enter the feature extractor or classifier.

This matches the stated feature tap, not every detail of the published transfer
experiments. In particular, we retain the published weight file unchanged rather
than applying the paper's unseen-packet-size embedding repair; our weighted
scaling and classifier settings are separately declared choices. No fine tuning
or claim to reproduce the paper's scores is made.

The immutable [configuration](../configs/pool-linear-probe-v1.json) binds:

- The same 14,000 public training flows and 43 local training connections
  (22 Instagram, 21 YouTube), with 75% public / 25% class-balanced local mass.
- Four training prefixes per flow, truncated to actual length, with equal shares
  of each flow's mass. One shared ten-class multinomial logistic regression:
  L2, C=1, LBFGS, at most 500 iterations, tolerance 1e-5, seed 17. Weighted
  StandardScaler is fitted only on training embeddings. No search or retry with
  different settings after nonconvergence or a failed gate.
- Existing selection: seven Instagram / ten YouTube connections, three visits,
  63 available prefix cases. These recordings have already been inspected and
  are development evidence, not an independent test.
- The same 500 public-selection control flows, 50 per class. This control
  predates pretrained week 46 and cannot establish forward retention. The old
  final-test week overlaps pretraining and must never be used here.
- A development screen requiring F1 >=0.75 and >=0.01 above the stronger fixed
  forest, recall >=0.65 for both local services and no recall regression against
  either fixed forest, plus historical control F1 within 0.02 of B17. Passing
  would justify independently declared future validation only.

Run from the repository with the existing local real data and upstream files:

```powershell
.venv/Scripts/python.exe scripts/study_linear_probe.py --output experiments/browser-adaptation/pool-linear-probe-v1
.venv/Scripts/python.exe -m pytest tests/test_linear_probe.py -q
```

The runner refuses an existing output directory. It records the declaration,
source hashes, versions, IDs and layer audit before fitting. A converged head is
exported before selection data is loaded. The export includes the original
weights, pinned pure-Python wheel, scaler, head, labels, schema, clipping settings,
unfitted policy and provenance. Inference needs no training data or pickle head:

```powershell
.venv/Scripts/python.exe scripts/predict_linear_probe.py --bundle experiments/browser-adaptation/pool-linear-probe-v1/bundle --flow experiments/browser-adaptation/pilot-01/benchmark-flow.json
```

Output always withholds an accepted label. Its alternatives are explicitly
uncalibrated model probabilities. The research artifact is not registered as an
app default. CPU timing covers one prediction call, excluding capture, HTTP and UI.

## Completed fixed run — 31 October 2026

The declaration and implementation were committed locally as
`4e884a7fa2f9e9327866dfccff41dd08391617d6` before
fitting. The one run completed; no layer/head/weighting/seed/regularization sweep
or post-result adjustment was made. It **improves overall development quality
but fails the declared per-service nonregression check**. B17 stays the app
default. There was no new capture, calibration, final evaluation or deployment.

The linear solver converged in 436 of its 500 allowed iterations, without a
convergence warning. Feature extraction took 170.82 seconds and fitting took
117.57 seconds on two CPU threads. These are training-stage durations, not
per-event inference latency. The encoder parameters and buffers stayed exactly
unchanged throughout fitting, scoring and save/load checks.

All comparisons below use the same 17 development connections across three
visits. The 63 prefix cases share connections and are not independent samples.
F1 is the equal-weight mean of the four observed-local-class macro-F1 scores;
recall is likewise the equal-weight mean over packet budgets, not a pooled count.

| Model | Correct prefix cases | Mean-prefix F1 | Instagram recall | YouTube recall |
| --- | ---: | ---: | ---: | ---: |
| B17 | 18/63 | 0.26398 | 0.00000 | 0.45556 |
| Previous adapted forest | 46/63 | 0.76035 | 0.73571 | 0.74722 |
| Latest adapted forest | 47/63 | 0.78056 | 0.92857 | 0.64444 |
| Frozen pooling + linear probe | **55/63** | **0.90272** | **0.80714** | **0.92500** |

The probe improves both services against the older forest, but not against the
latest forest: Instagram falls from 22/24 to 19/24 repeated prefix cases while
YouTube improves from 25/39 to 36/39. The rule was frozen against **both** fixed
forests before fitting; we do not relax it after seeing this trade-off.

| Prefix | Correct / available | Local macro-F1 | Instagram correct | YouTube correct |
| --- | ---: | ---: | ---: | ---: |
| 5 packets | 11/17 | 0.75253 | 4/7 | 7/10 |
| 10 packets | 16/17 | 0.93773 | 6/7 | 10/10 |
| 20 packets | 14/15 | 0.92063 | 4/5 | 10/10 |
| 30 packets | 14/14 | 1.00000 | 5/5 | 9/9 |

The thirty-packet result is encouraging, but only fourteen already inspected
development connections reach that budget. It is not a general 100% accuracy
claim, does not repair weaker early-prefix behavior, and cannot justify changing
the prefix policy after the result. No significance claim is supported by this
small, correlated, repeatedly reused cohort.

Four of the five aggregate checks pass: local F1 floor, gain over the stronger
forest, both recall floors and the historical public-control diagnostic.
Per-service nonregression fails on Instagram (0.80714 versus 0.92857). The
public-control F1 is 0.96848 over 500 historical selection flows/four prefixes;
it is explicitly retrospective to pretraining, not independent final evidence.
The declared screen therefore does **not** authorize progression to calibration
or automatic collection. This fixed experiment is complete.

## Artifact, checks and reproduction

The local ignored run is `experiments/browser-adaptation/pool-linear-probe-v1/`.
Its `bundle/` is complete for offline research inference. The original
declaration has LF-canonical SHA-256
`b5b88cc07317357a2c1b211c91b775075fc7892b4291d09f6921e5dd4af3db01`;
its current Windows file bytes hash to
`504e54bdc30aaff1fa48e7ae7ded1f0c6dfd9981409f629bf399f02be6247083`.
Evidence hashes below are always raw-file hashes.

| File relative to run | SHA-256 |
| --- | --- |
| `report.json` | `ee3d7927dc422c932ff36badf57dbf8ab9b5a0fbf6c2cd7dab5439c8bcef90e3` |
| `protocol.json` | `f19ada05a9612cd44d1ffc53c094da594dde93cf3b18bef87da50723a4946aa8` |
| `local-predictions.json` | `a221017bce84833060e31b5a2ef4f463a34151d6bd803bf6af3c84c7bc2eee22` |
| `independent-audit.json` | `0b98cd54d66c6b1141e0f366b4c055e20a86d7f7171db403fddabb0b7205b1ee` |
| `standalone-audit.json` | `5a38239603929e6bf4b58e39526c37210b459568c63626db52e6a076117c0ee9` |
| `evidence-checksums.json` | `ff48e86823f3b1c82b98d711a900f26a8a8f2362efdc101b5c012d1a97f2d93b` |
| `bundle/metadata.json` (artifact identity) | `b2fe68875f11b507f156aedae7c9300bdb8ee3f65db17a43f22b96c45b2bf5d6` |
| `bundle/head.json` | `982334a063123a88352ac570620617ab0f9f4b0bb0498a85d26cebd5120f59fa` |
| `bundle/encoder.pth` | `dc4b3333388239ac25b8c028c922965e2333cc151dd5fad951950099e86fabc4` |
| `bundle/cesnet_models-0.4.1-py3-none-any.whl` | `86acb26e5c1595e2d80546bc44859e3d0daf271a20cbb7fbc829fd513a56154b` |

`protocol.json` contains the full source commit/hashes, configuration, package
versions, training IDs and capture evidence. `fit.json`, `local-predictions.json`
and `control-predictions.json` preserve the actual fit and every scored output.
`evidence-checksums.json` inventories the result, audit and artifact files.
The source dataset, local recordings and optional upstream files remain local;
a fresh checkout needs their legitimate transfer to reproduce training. Nothing
has been uploaded or published.

Actual verification:

- **331 Python tests pass**, including 13 new tests for the pooling tap,
  hook cleanup, frozen state, portable probabilities, withholding, weighting,
  checksum/schema rejection, immutable config and protected/offline input guard.
  Ruff lint and formatting pass across 104 files. Existing Starlette/AnyIO and
  sklearn/SciPy deprecation warnings remain. UI code did not change; its earlier
  sixteen-test/build checkpoint was not rerun. No hosted CI run is claimed.
- Real-weight smoke test returns finite `(4,448)` features. Every extracted
  batch equals the input to the upstream refinement block. The saved portable
  head matches sklearn probabilities exactly in the training parity check.
- A fresh-process audit imports the pinned wheel directly from the bundle and
  exactly reproduces all 63 saved local probability vectors (maximum difference
  **0.0**). It recomputes the four local scores and rescores all 2,000 saved
  public-control predictions. Public inference itself was not repeated by that
  independent audit. Original upstream, training and protected input reads are
  blocked by a process audit hook.
- A second fresh-process check blocks **all dataset access**, including local
  recordings, and successfully predicts the real standalone example using only
  the bundle, supplied flow and runtime code. The documented prediction CLI
  produces the identical reply. It withholds the accepted label even when a raw
  model probability is high; those probabilities are not calibrated confidence.
- The trained-artifact CPU check uses the fixed **30-packet** real example,
  20 warmups and 100 calls on two CPU threads of this i7-1360P laptop:
  **p50 23.79 ms / p95 26.49 ms**. It includes the frozen encoder, head and reply,
  excluding model loading, capture, queueing, HTTP and browser rendering.
  This is offline model timing, not new live latency evidence.

The private audit source is
`experiments/browser-adaptation/pool-linear-probe-audit.py`, SHA-256
`aa1f29449c9cda9639d1b17f9f3b2a7db7686c5f37e3346dfbc08a9c3d5255ab`.
Its two invocation forms are:

```powershell
.venv/Scripts/python.exe experiments/browser-adaptation/pool-linear-probe-audit.py
.venv/Scripts/python.exe experiments/browser-adaptation/pool-linear-probe-audit.py --standalone
```

The result demonstrates that this combination of representation and classifier
is useful on existing development recordings. It does not isolate which change
caused the gain, establish unseen-session quality, fit an uncertainty policy,
or validate this new model in the live capture path. The previous 256-value
neighbor result used a different legacy cohort and is not a paired layer ablation.
