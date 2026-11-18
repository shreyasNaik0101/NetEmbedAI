# Selection follow-up result — 30 October 2026

**The recording gap is resolved and the fixed seed-17 comparison completed.
Neither candidate qualifies for calibration.** The new forest recognizes more
Instagram prefixes but loses YouTube recall. The predeclared stopping rule ends
this cycle: no seeds 42/123, new calibration, additional capture or promotion.
B17 stays the original benchmark reference in the app; dependable recognition
on this local network remains unresolved.

The [declared one-recording protocol](browser-selection-followup-v1.md) follows
the closed six-recording study. Its original shortfall and evidence are preserved.
The one supplemental user-started session adds five verified YouTube connections
and passes the unchanged coverage/feature checks. Training remains **43 local
connections: 22 Instagram/21 YouTube**, plus 14,000 original public training flows.
Separate selection contains **17 connections across three visits: seven
Instagram/ten YouTube**. It has **63 available 5/10/20/30-packet cases**, not 63
independent sessions. No selection packet enters training or normalization.

## Paired results

F1 and service recall below average the four packet budgets equally. F1 is not
the percentage correct. Every model uses the same local selection inventory;
predictions to any other service count as errors. The public control is a fixed
balanced 500-flow historical selection cohort, fifty per service, not a forward
final test after local adaptation.

| Model | Correct / 63 repeated prefix cases | Mean-budget local macro-F1 | Instagram recall | YouTube recall | Public retention F1 |
| --- | ---: | ---: | ---: | ---: | ---: |
| B17 original reference | 18 | 0.26398 | 0.00000 | 0.45556 | 0.84401 |
| Previous adapted summary forest, paired control | 46 | 0.76035 | 0.73571 | 0.74722 | 0.90114 |
| New CE TCN, best observed checkpoint (epoch 5) | 37 | 0.50797 | 0.15714 | 0.84444 | 0.83513 |
| New summary forest | 47 | 0.78056 | 0.92857 | 0.64444 | 0.89690 |

The new forest passes the 0.75 overall floor, the 0.01 improvement requirement
(actual gain **0.02021**) and public retention. It fails two YouTube conditions:
mean-budget recall **0.64444 < 0.65**, and regression from the paired previous
forest's **0.74722**. The latter is a decline of about **10.3 percentage points**;
this is not solely a rounding difference at the minimum.

On the repeated saved cases, Instagram improves from **17/24 to 22/24**, while
YouTube drops from **29/39 to 25/39**. Overall this is one extra correct prefix,
46 to 47. These small correlated counts do not demonstrate a dependable or
statistically established improvement. The previous forest also remains
disabled after its earlier independent calibration failure; its development
score is not permission to enable it.

All five TCN checkpoints fail eligibility. Their local F1 values, in epoch order,
are **0.36462, 0.36496, 0.35830, 0.46500, 0.50797**. The epoch-5 checkpoint is
shown for diagnosis, not selected as a deployable model. No contrastive,
augmentation, architecture, feature or hyperparameter sweep was added.

## Artifacts and verification

Source commit: `f9c2966f79cf898737638420318c68920594bd2a`.
Config: `configs/browser-selection-followup-v1-seed17.json`.
Run directory: `experiments/browser-adaptation/selection-followup-v1-seed17`.
The five neural checkpoint bundles and forest bundle include weights, original
saved normalization, labels, schema/architecture, versions, provenance and an
explicit **unfitted policy**. They load without training data. Their runtime
does not commit a label under that policy; development scores use raw top choices.

| Artifact | SHA-256 / identity |
| --- | --- |
| `result.json` | `8fd1606140be1512a54036510ce5f55c714b34597a662bf133e18b8a8a8f6325` |
| `data-manifest.json` | `83bac5d76a1b44f9276147b6f2968bb672266e01a6c4bfa260b5279d958883ac` |
| `config.json` provenance | `0b32a1bafc7d679e427edbf36ab67092d1f07f7f6625d5e966631fb6a860a055` |
| New forest `forest/bundle/metadata.json` / identity | `bd79923fabc4816cc2f15b4f150a5d3b428663c455d0fde3da6ab219eb666d62` |
| New forest `forest/bundle/forest.json` | `fc735ea2f5e821bfba3832a588bdb3e62fde7a0c8f47c55567cb4cd5a2ee0494` |
| Epoch-5 `tcn-epoch-5/bundle/metadata.json` / identity | `f5cc25e3ef0983935d1681984a00aecd1fc1a95b811ed98abb6932aa6df7831b` |
| Epoch-5 `tcn-epoch-5/bundle/weights.pt` | `abe74ed381fe1da74a46482b37918e5a137ce4917de3af91657b1a2eae948068` |
| `experiments/browser-adaptation/selection-followup-v1-decision.json` | `76ccc61e6a8ee46237016f9d8f7e110fd0d6098ad6bd4438022515a48f0263ec` |

An independent read-only audit reloads all **eight exported models** (two
controls plus six candidates), repeats **504 local predictions**, and reproduces
every saved probability exactly: maximum difference **0.0**. Local metrics and
the 500-flow public retention metrics also reproduce. It saves all **16,000
public-selection predictions** in 32 checksummed files. All new candidate
normalizers match B17 and their policies remain unfitted. No training,
calibration or final partition is read by this audit.

Audit report:
`experiments/browser-adaptation/followup-v1-engineering/seed17-audit/report.json`,
SHA-256 `aa76a3049e960bb41c69061eb291345d5581c8efd3ba66dc148d14fef34c1de0`.
The complete gate/artifact/source-state checkpoint is
`experiments/browser-adaptation/followup-v1-engineering/completed-study.json`,
SHA-256 `9952aa31af52e6d788f92cfa0c2461dbfb034b977b6ba37fc7cf68fc58f37e55`.
It explicitly lists only seed 17 as executed; stability across three seeds was
not evaluated because the first-seed gate failed. Private inputs, prediction
files, bundles and audit script remain local/ignored, not published.

Training used two CPU threads, batch size 64, five epochs of fifty steps, CE
only and 25% local training mass. Recorded TCN/forest stage times are
**59.59/78.48 seconds**, including development/export (and forest feature
preparation), excluding initial admission/reference checks. These are not
inference latency measurements. No new inference benchmark runs for ineligible
candidates. The latest software checkpoint remains **318 Python tests passed**,
Ruff lint/format for 99 files, and the unchanged sixteen-test UI/build checkpoint.
This evidence-only turn adds no new unit-test result or hosted CI claim.

## Reproduce and limits

Use the [exact collection/experiment commands](browser-selection-followup-v1.md#exact-helper-commands)
with the checksummed real private inputs. Existing output directories are
preserved and refused, so reproduction needs a fresh working copy/output tree
at the declared paths; do not erase the evidence to rerun. The private independent
audit runs with:

```powershell
.venv/Scripts/python.exe experiments/browser-adaptation/followup-v1-engineering/audit_seed17.py
```

It also refuses an existing audit output directory. The saved audit script and
all output-file checksums are bound in the completed-study checkpoint.

The added capture has partial browser/socket feature parity, not independent
full exporter/wire-order parity. Its B17 browser receipt p50/p95 is
212.68/519.01 ms over 99 events, not paint time. Development uses one laptop,
normal Chrome and Wi-Fi; three visits and two local services cannot establish
cross-browser/network or ten-service live quality. The follow-up was declared
after observing parent development diagnostics, so this enlarged cohort is
not a blind final test. Historical final-test data remains outside this work.

The remaining blocker is **local per-service model quality**, rather than a
missing recording or artifact. This declared study has finished. No further
recording, relaxed threshold or model search is authorized by its failed gate.
An additional modeling study would need a distinct prospective protocol and
appropriate independent evaluation. The app has not learned from this visit
automatically and is not a validated live-classification release.
