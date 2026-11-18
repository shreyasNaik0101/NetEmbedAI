# Size robustness: a separate development experiment

This new study follows the [YouTube failure diagnosis](youtube-failure-diagnosis.md).
The user authorized a development repair experiment after the earlier calibration
closed. This is not a continuation or relaxation of that failed protocol. Its
recordings, the paired comparison and public calibration/final rows stay excluded.
The app keeps B17 throughout; no capture or confidence-policy fitting is started.

The [declaration](../configs/size-robustness-v1.json) was frozen before treatment
scores, LF-canonical SHA-256
`8ff86861442284f840321aae8eb84f85c5c867d2eb94d1291a72a57baf9c29e1`.
Implementation/test commit: `10c86b7`.

## The matched comparison

All arms use the original 14,000 public training flows and43 local training
connections (21 YouTube,22 Instagram). Local training retains25% of total sample
weight, divided equally between local classes; public training has75%. Every
flow contributes the same four5/10/20/30-packet prefix views, truncated at its
available length, and the same weight across arms. No extra augmented rows alter
bootstrap sample counts or minimum-leaf semantics. The32-tree forest, maximum
depth12 and minimum leaf2 are fixed. Two CPU threads; sequential stages.

| Arm | Training inputs | Inference feature map |
| --- | --- | --- |
| Clean control | Original packet metadata | Original34-value raw summary |
| Size jitter | One deterministic bounded size-perturbed view per original flow, shared across its prefixes | Original raw summary |
| Relative size | Original packet metadata | Same34 statistics, with size statistics divided by the current observed prefix's maximum payload |

The relative map keeps packet counts and timing statistics unchanged. It does
not change the raw byte schema, inspect later packets, fit a scaler or use
addresses/domains/IP family. Its explicit artifact architecture map is
`summary-relative-size-v1`; old artifacts keep their original feature maps.
The saved original normalizer remains packaged but is unused by either summary
map. A new trained model is required for the new representation.

Size jitter selects a single flow-level integer byte delta from-32 through32
with a fixed clean draw. It affects only original payloads>=1200, clips results
to1200..65527 bytes and leaves timing, direction, order and packet count intact.
The SHA256-keyed assignment uses augmentation seed70017 and the sample ID; it is
independent of iteration order and reused unchanged across forest seeds. The
manifest saves each nominal delta, actual byte change and changed-packet count,
with zero added duration/removed packets. This is **abstract training augmentation**,
not a protocol-preserving transport simulation. Its physical usefulness remains
an evidence question.

## Development evidence and fixed gates

Selection reuses the same17 local connections across three historical development
visits: seven IG and ten YT, with63 available correlated prefix cases. The
historical public retention control uses the first50 flows per each of ten
classes, in saved selection order. Public prefixes use up to each requested
budget even if shorter, exactly as the original control; saved predictions
include requested and actual lengths. This reused development evidence is
optimistic for generalization and is not an untouched or forward final test.

Clean and abstract-20/+20-byte stress conditions are reported separately.
Stresses use the same near-large-packet/clipping rule, fixed before treatment
scores, and are identical across arms. The stress results measure sensitivity
to that family, not performance on actual IPv4/IPv6 sessions. Correlated
prefixes/altered copies do not create independent visits.

Relative to the same-seed clean control, an arm must satisfy every fixed gate:

- Local clean mean-budget macro-F1>=0.75, with loss<=0.01, and no loss in either
  local class's mean-budget clean recall.
- Local stress macro-F1, averaged over both signs and four budgets, improves
  by>=0.03. Neither local class's averaged stress recall may regress; each must
  reach>=0.65. At10 packets, each class's recall averaged across both stresses
  must also reach>=0.65.
- Public clean macro-F1 may lose<=0.02; no public class's clean mean-budget
  recall may lose>0.05. Public stress macro-F1 must not regress, and no public
  class's averaged stress recall may lose>0.05.

Seed17's clean refit must reproduce the original forest's exact weight checksum
before treatments are scored. Its reference artifact is
`bd79923fabc4816cc2f15b4f150a5d3b428663c455d0fde3da6ab219eb666d62`,
forest bytes SHA-256
`fc735ea2f5e821bfba3832a588bdb3e62fde7a0c8f47c55567cb4cd5a2ee0494`.
This is a software/reproduction gate, not a model-selection score.

If neither treatment qualifies at17, stop. Otherwise freeze the eligible arm
with the highest local stress score, preferring relative size within0.01 of
the best. Only clean plus that fixed arm run at42 and123. Both repetitions must
pass unchanged gates; a better later seed cannot replace17 or switch arms.
Three-seed mean/spread and per-seed class guards determine whether the seed17
artifact is only a candidate for future real-family evaluation. No calibration
or operational promotion follows automatically.

## Reproduction and outputs

With private local exports and the processed public train/selection splits
present, from the repository directory:

```powershell
.venv/Scripts/python.exe scripts/study_size_robustness.py --seed 17 --output experiments/size-robustness-reproduction
# Run only if seed17/result.json has a non-null chosen treatment:
.venv/Scripts/python.exe scripts/study_size_robustness.py --seed 42 --output experiments/size-robustness-reproduction
.venv/Scripts/python.exe scripts/study_size_robustness.py --seed 123 --output experiments/size-robustness-reproduction
.venv/Scripts/python.exe scripts/study_size_robustness.py --decision --output experiments/size-robustness-reproduction
```

Every seed directory is write-once; a
reproduction needs a separate `--output` root. The runner verifies row/summary
hashes against original artifact provenance and keeps whole-session roles and
chronology. It reuses prevalidated local exports without claiming fresh raw
packet QC. The streaming public reader verifies source checksums and limits
memory. Audit hooks exclude old calibration, comparison, diagnosis and final
files and disallow network connections. No fitting entry point receives their
packets or labels.

Each arm saves a complete portable bundle, config/source/version/provenance,
per-condition/per-budget precision, recall, F1, support, confusion matrices and
probability vectors. The study binds manifests, augmentation assignment and
result hashes. Exported forest inference is compared with sklearn before
quality reporting. Models remain explicitly uncalibrated and withhold accepted
labels. A stable eligible candidate gets a trained-model CPU benchmark on a
fixed first complete local training flow (20 warmups/100 calls,10/30 packets),
excluding loading, capture, HTTP and UI. Real live-family quality/latency remains
separate and pending.

## Actual outcomes

The initial sandboxed attempt at `experiments/size-robustness-v1/seed17/` could
not create the Windows thread-pool IPC pipe. It stopped at the clean forest fit
before any model score or bundle existed. Its input/config/augmentation manifests
and `execution-error.json` are preserved. The identical declaration/source
continues in `experiments/size-robustness-v1-execution-recovery/` with execution
permission for local IPC. No data, seed, gate, parameter or feature changed.

Seed17's clean control passes the exact original forest-weight checksum gate.
It reproduces local clean mean-budget F1=0.7805568818 and public clean F1=
0.8969037329. Its local two-sign stress F1 is0.6575806369. Its143.83 seconds
include feature construction, fitting, export and both-domain development
scoring, not just model fitting or per-event inference. Treatment results and
completed verification are below.

### Completed seed17 pilot: neither treatment qualifies

| Arm | Local clean mean-budget F1 | Local abstract-stress F1 | Historical public clean F1 | Public abstract-stress F1 |
| --- | --- | --- | --- | --- |
| Matched clean control | 0.780557 | 0.657581 | 0.896904 | 0.467240 |
| Size jitter | 0.823198 | 0.852214 | 0.875925 | 0.871118 |
| Relative size | 0.756676 | 0.769799 | 0.879579 | 0.847366 |

This is a **single-seed exploratory development pilot**, not a repeatable
improvement claim. Stress columns average the two declared abstract byte shifts
and four budgets. They do not measure real IPv6 recognition. Clean/stress copies
and budgets share original flows; there are17 local selection connections and
500 public control flows, not thousands of independent sessions.

Size jitter improves both aggregate local scores but fails four of ten guards:

- Clean Instagram mean-budget recall falls0.928571→0.878571, while YouTube rises
  0.644444→0.772222. Aggregate improvement cannot hide the Instagram regression.
- Public clean F1 loses0.020978, beyond the fixed0.02 cap. The cap is unchanged.
- Public clean Snapchat recall loses0.060, beyond the0.05 class cap.
- Public stressed Spotify recall loses0.080, also beyond the0.05 class cap,
  despite a large aggregate public stress improvement.

Relative size fails six of ten guards. Clean local F1 loses0.023881, beyond0.01.
Clean IG recall falls to0.478571, despite YT increasing to0.922222. IG stress
recall is0.478571, below the0.65 floor and the control; ten-packet stressed IG
recall is0.571429. Public clean Spotify/Snapchat recall lose0.065/0.085, and
public stressed Spotify loses0.115. Removing absolute size loses useful service
information too. Its passing aggregate public F1 guards do not override these
class failures.

The fixed seed17 decision is `chosen:null`. The consolidated decision is
`stop_no_validated_candidate`, with no development candidate, fitted policy,
promotion or CPU benchmark. **Seeds42/123 were not run** because seed17 produced
no eligible arm; no better seed or relaxed guard was tried. There is no three-
seed stability result. All three complete research bundles are retained and
remain uncalibrated. No final visit is requested, and the earlier failed
calibration remains closed. B17 stays in the app.

The treatments took143.83/137.35/147.45 seconds respectively, including feature
construction, fitting, export and assessment. The new training manifest contains
14,043 flow assignments, changing61,168 packet sizes with a net+45,005 bytes over
the full retained training prefixes before the four budget views. Per-flow
deltas/clipping are saved. No time or observation count changed. This records
abstract training overhead, not real network transmission overhead.

### Independent audit and artifact identities

A fresh process, with training/calibration/paired-comparison/diagnostic/final
inputs and network connections blocked, replayed **18,567** saved vectors
(6,189 per arm) with maximum absolute probability difference0.0. Each arm has
189 local and6,000 public correlated prediction cases. The audit verifies the
complete expected ID/budget/variant inventory, all72 confusion matrices, supports,
recalls and independently computes macro-F1 from the matrices. It checks model
identities, evidence hashes and that uncalibrated predictors withhold labels.
It uses the same predictor for replay, so this is independent aggregation and
fresh-process reproducibility, not a separate classifier implementation.

Actual bundle paths are under
`experiments/size-robustness-v1-execution-recovery/seed17/<arm>/bundle/`:

| Arm | Artifact ID: SHA-256 of metadata |
| --- | --- |
| Clean | `e0ae9f5fcc28a2e0c30d1b3008e935df496c4737d53a71aa8806ebc0332e2d3a` |
| Size jitter | `f6f15b4dbd48f62aaa743a225aea6d06704875053e0f7fade5e795951640b9db` |
| Relative size | `e87b6123137a9c2a8708ac78a3027b6f2699ad0cc3468ef6966c8f1994925bcd` |

The clean artifact's metadata identity differs because it has new study
provenance; its forest weights are byte-identical to the old reference.
Each bundle's `checksums.json` binds its weights and metadata. Fixed feature
semantics are saved in its architecture map and inference-source checksums.
Exported inference agrees with sklearn within1e-12 before any quality report.
Actual fit/inference use Python3.11.9, numpy2.1.3, torch2.5.1 and sklearn1.6.1
on this Windows CPU host. No cloud resource was used.

| Evidence in the active execution-recovery root | SHA-256 |
| --- | --- |
| `seed17/result.json` | `d0493741cf49a9756f0638323bc0b51233fc1045d540398801ad04acd7f61454` |
| `decision.json` | `8f05267d5d94419128a91e13b5fce76dcf36a288d3a78c6c0d47e2ca9efb40c2` |
| `independent-audit.json` | `65889b09ce9bb05dc7ceff0d6c607a4c2910d10f356366832eafed08501ffcf2` |
| `seed17/data-manifest.json` | `00bdd9afa923115af32424fce8d7fe9ad0f2c78f4d926cae25f89344e4f428ae` |
| `seed17/training-augmentation-manifest.json` | `6d6845b51abf7e6f2d61a834f90ad23e944db0985de236663919f8b26a69f469` |

The preserved initial attempt has byte-identical data and augmentation manifests.
Private audit source is `experiments/size-robustness-engineering/audit-development.py`,
SHA-256 `1d55ff8e3bb5037a3dcf185da75d26235dd5bb6bdcd03ffa3eb2c782a76cd7cc`.
Detailed per-arm report/prediction checksums live in `seed17/result.json` and the
audit. The original control artifact, paired comparison and failed calibration
files remain unchanged. Size-jitter forest weights SHA-256:
`841eda5f23baf4fd23bd3219ebeff1a0421a504067e8f79f21886482ef8fd138`;
relative-size weights SHA-256:
`6b99205611a741154e61d4345ed2f6fb2853bb2a42402520f4db3f03202c4c60`.

Full Python suite: **395 passed**, two known dependency deprecation warnings,
39.03 seconds. Ruff lint/format pass for121 files; `git diff --check` passes.
Tests cover bounded/immutable/prefix-consistent augmentation, stateless assignment,
relative feature scaling and preserved timing/counts, sklearn/export agreement,
training-data-independent inference, excluded inputs, class guards, write-once
decisions and prevention of seed rescue. The UI is unchanged from its17-test/
production-build checkpoint; no hosted CI or other OS result is claimed.

`completion-evidence.json` in the active root binds output/weight hashes,
unchanged previous evidence, identical retry inputs, environment, tests and
read-only app status. Its SHA-256 is
`5224d9bfe66e3ee4f67071c2595a0ca876569541981fb4ab0000bacbe70d0749`.
The app is still B17 (`18c43fe12262b81d4a3001df150a278865f3908ddd3aab934822fc0c9e5750fb`),
capture is stopped, and its last session remains the earlier user-started visit.
Nothing was published or merged.

Inspect the saved result without fitting or capturing:

```powershell
Get-Content experiments/size-robustness-v1-execution-recovery/seed17/result.json
Get-Content experiments/size-robustness-v1-execution-recovery/decision.json
Get-Content experiments/size-robustness-v1-execution-recovery/completion-evidence.json
```

### What this establishes and leaves unresolved

In this pilot, bounded size jitter helps the diagnosed sensitivity much more
than discarding absolute size. Its clean IG and public class losses prevent
calling it a safe replacement. Relative size causes a severe IG regression.
The study ends at that result; it does not claim a repaired confidence policy,
local IPv6 accuracy, a validated augmentation simulation or a live showcase.

A future repair would need to preserve clean/class-specific information while
adding verified path diversity, then meet new declared development gates and
separate real-family evaluation. That is a new study, not an automatic extra
arm or tuning round here. No additional recording is needed to reproduce these
results. Real family-stratified quality, confidence calibration, selected-model
CPU/live-path validation and release acceptance remain unresolved.
