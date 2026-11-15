# Development failure audit and one rejected feature change — 27 October 2026

**No validated model repair was found.** The audit found weak early Instagram
decisions and overlapping correct/error scores. One fixed attempt to retain
packet order in the same forest made local development results worse, so it
stopped after seed 17. No newer calibration record was used, new confidence
policy fit, default switched or further user recording requested.

## What the existing development records show

Training has only five independently attributed Instagram connections from two
visits, versus twelve YouTube connections. Selection uses seven connections
per service from the explicitly retired first calibration visits. Those visits
were already used for model selection; this audit is not an independent test.
The newer `*-cal-02` recordings remain protected calibration data.

The existing summary forests get all 67 available training checkpoints right
at all three seeds, while making mistakes on three to five of fourteen later
selection connections. This is consistent with limited transfer and small
training coverage; it does not identify a sole cause.

| Instagram selection checkpoint | Seed 17 correct | Seed 42 correct | Seed 123 correct |
| --- | ---: | ---: | ---: |
| 5 packets | 4/7 | 5/7 | 5/7 |
| 10 packets | 5/7 | 5/7 | 5/7 |
| 20 packets | 6/6 | 5/6 | 6/6 |
| 30 packets | 5/6 | 4/6 | 4/6 |

Longer observation is not uniformly better: thirty-packet results regress from
twenty. A wrong ten-packet label scores 0.644 at seed 17, while correct
twenty-packet Instagram scores range only 0.351–0.548. Merely raising a global
score threshold can therefore reject correct later predictions while retaining
an earlier error. A score is not a correctness probability. These small,
correlated development counts cannot justify a new production policy.

Replaying all saved selection probabilities matches within 1e-12. An actual
trained TCN bundle also passes unpadded/padded/changed-future readout checks at
5/10/20/30 packets: maximum logit difference 4.77e-7, within the 1e-6 tolerance.
No padding-readout bug was found. This does not establish every capture/export
semantic or solve the outstanding historical timing-parity limitation.

The forest's existing summaries retain counts and per-direction time/size
statistics but lose packet order. A constructed software example demonstrates
different orders with identical summaries. No exact cross-label summary
collision was found in the 31 development flows; the example is not evidence
that order loss caused the actual errors.

## One frozen hypothesis and its negative result

[The study config](../configs/browser-ordered-forest-study.json) was committed
before fitting. It changes only the forest input map, retaining the same packet
channels, 5/10/20/30 budgets, 32 trees, depth 12, minimum leaf 2, mass weighting,
local sessions, public training/retention cohorts, two threads and saved
training-only normalizer. No new architecture, destination feature or SupCon
term was added.

The experimental map contains 154 derived values: 34 previous summaries,
90 saved-normalized ordered packet values padded with zeros, and 30 observed
position-mask values. The mask derives only from the actual prefix length.
Increasing dimensionality also changes the forest's default square-root feature
sampling; this is not an isolated causal test of order alone.

The frozen gate requires ≥0.01 local F1 gain over the paired summary forest,
no local class-recall regression, and historical clean F1 loss ≤0.01. Seeds
42/123 run only if seed 17 passes.

| Seed 17, development only | Summary forest | Summary + ordered prefix |
| --- | ---: | ---: |
| Mean-budget local observed-class F1 | 0.87386 | 0.81120 |
| Instagram mean-budget recall | 0.77976 | 0.58333 |
| YouTube mean-budget recall | 0.89286 | 1.00000 |
| Historical public clean F1 | 0.90114 | 0.92822 |

Better public retention and YouTube recall do not compensate for worse local
Instagram quality. **Seed 17 fails; seeds 42/123 were not run.** No extra sweep,
new calibration or candidate promotion followed. Exported probabilities match
the fitted scikit-learn model within 3.34e-16. Feature preparation took 129.22 s;
total study time after cohort loading was 146.99 s. No performance benchmark or
new live validation of this rejected candidate is claimed.

The new map is explicitly versioned in bundle architecture metadata; legacy
bundles keep their original summary map. Export refuses mismatched training
dimensions; load refuses unknown maps/out-of-range split indices. Tests cover
order distinctions, padding/masks and numeric export parity without fitting
preprocessing at inference. It is experimental reproducibility support, not
an enabled application model.

## Evidence, reproduction and the next decision

187 Python tests pass (one existing Starlette/AnyIO deprecation warning), and
Ruff lint/format passes for 67 active files. The portable study CLI's help was
checked. UI code did not change in this step; its prior nine tests/build remain
separate evidence. Neither the audit nor experiment reads the newer local
calibration records; final-data loading also remains guarded by `read_split`'s
default final-data refusal. Python open guards add scoped path checks, not a
complete OS sandbox. Actual capture remains user-started and stopped.

| Local evidence | SHA-256 |
| --- | --- |
| `development-failure-audit/report.json` | `afd7365c8f7db06d19f44133d41b60d9703d5ee28140b5d396b5c9e66b97c3d1` |
| `ordered-forest-01/protocol.json` | `d620a01acc929c3e2558da2c6fd95e247117acf2cec2263462e43b8fcc653e6a` |
| `ordered-forest-01/result.json` | `c7c99b9bf37e713c7546a5e29b79f76eee5dc348b71a4cc4a062263b6af37789` |
| `ordered-forest-01/seed-17/bundle/forest.json` | `19d5819a22ac0e1074a757d477e046fc151c6d9d92f811590d4c2b84c30ac9ae` |

Paths are relative to `experiments/browser-adaptation/`. The rejected artifact
identity is `070cb81d77794c0993f5ab83cb34541af810d98b78dadc9ebcc93471ca0107a8`.
Its policy is unfitted. The original run's private launcher and source hash are
retained with the protocol; the tracked CLI exposes equivalent cohort/output
arguments. From `traffic_classification`, with the existing private inputs and
earlier reference results, use a fresh output path:

```powershell
.venv/Scripts/python.exe scripts/study_ordered_forest.py --output experiments/browser-adaptation/ordered-forest-repeat
.venv/Scripts/python.exe -m pytest -q
.venv/Scripts/python.exe -m ruff check src tests scripts
.venv/Scripts/python.exe -m ruff format --check src tests scripts
```

More identical calibration visits or arbitrary model tweaks are not justified
by this result. A credible next model-development cycle needs broader,
independently labelled Instagram development coverage and separately reserved
later sessions, with collection roles fixed before use. Five training
connections across two visits do not cover many browser/session/network
conditions. This is a data-coverage limitation, not a claim that more data alone
will guarantee success. Existing `cal-02` records cannot become a new untouched
final test. Until a candidate passes new independent validation, reliable local
recognition and the live UI-latency remeasurement remain unfinished.
