# One real-data IPv6 retraining pilot

The user requested a decisive offline comparison before spending more time on
recordings. This new declaration explicitly adopts exactly three usable fresh
acquisition archives as training data: `fresh-yt-01`, `fresh-ig-01`, `fresh-yt-02`.
They contain 19 IPv6 flows (15 YouTube, 4 Instagram), including incidental YouTube
flows in the Instagram visit. All eligible examples are retained. Earlier failed
campus/hotspot/calibration visits and completed paired comparisons are excluded.

The six-visit acquisition plan remains incomplete and paused. Its remaining
three slots are not read and are not silently converted into tests. Adopting
these three training-role archives here does not relabel old failed receipts
or declare the six-visit collection complete. No recording is requested for
this pilot, and no automatic capture is started.

## Frozen comparison

The declaration is `configs/ipv6-realdata-pilot-v1.json`, canonical SHA-256
`0de33a8b63290f34c1055f273a32a9a31443c47dc335dc49d7cc5a9e2fc1f6f2`.
Only two fits, seed17, two CPU threads:

| Arm | Public training | Original local training | New IPv6 training |
| --- | --- | --- | --- |
| Matched control | Original14,000 flows | All43 | None |
| Plus real IPv6 | Same14,000 | Same43 retained | All19 adopted flows |

Both use the original raw34-value summary features,32 trees, depth12, minimum
leaf2, no augmentation and the existing training-only normalizer metadata. No
feature-map/architecture/seed/hyperparameter sweep. Local total weight remains
25%, equally split between the two local classes; public weight remains75%.
Each flow contributes four equally weighted5/10/20/30 prefix views, truncated to
its available length, matching the original recipe. The candidate has36 YT and
26 IG local flows. Weights are per flow within class, not per session; therefore
new YT and IG examples contribute different within-class fractions. This is a
declared partial-cohort limitation, not an isolated causal test of IP family.
Adding rows also changes bootstrap samples. Do not attribute every resulting
score change solely to IPv6.

Before fitting the candidate, the matched control's forest weights must exactly
reproduce SHA-256
`fc735ea2f5e821bfba3832a588bdb3e62fde7a0c8f47c55567cb4cd5a2ee0494`.
The source artifact is
`bd79923fabc4816cc2f15b4f150a5d3b428663c455d0fde3da6ab219eb666d62`.
Both exports must agree with sklearn predictions within1e-12 before quality
reporting. Complete numeric forest/metadata/checksum bundles remain uncalibrated.

## Assessment and limits

Local assessment reuses the existing17 development connections (seven IG,ten YT),
with63 available prefix cases. The public retention control uses the same first
50 selection flows per class in stored order (500 flows), with up-to-budget
prefixes and explicit actual lengths. It is not the public calibration or final
split. All classes, confusions, per-budget metrics and probability vectors are
saved. Local macro-F1 averages the four observed-prefix checkpoints equally;
each checkpoint's macro averages the two services present in local references,
while the confusion matrix retains all ten possible predicted labels. It is
not the all-ten-class macro average or raw accuracy. The per-class guard uses
mean-budget recall. Family strata are descriptive,
joined through hash-verified existing selection-family metadata, not model inputs.
Missing IG/IPv4 coverage is reported as unavailable, not zero error.

**This is retrospective exploratory development.** The newly adopted training
captures are later than the old selection visits; that selection has also been
reused in previous experiments. It can reveal whether the intervention is
promising on known development challenges. It does not estimate fresh forward
accuracy, statistical reliability or performance on a new independent network.
Correlated prefixes do not create independent samples. No probability-of-
correctness guarantee is fitted here.

A positive screen requires every predeclared guard relative to the matched control:

- Local clean mean-budget macro-F1>=0.75 and gain>=0.01.
- Neither local class loses mean-budget recall.
- Public clean mean-budget macro-F1 loses at most0.02.
- No public class loses more than0.05 mean-budget recall.

If the candidate fails, stop this repair direction without extra recordings,
alternate weights, more seeds or another treatment in this pilot. A positive
result means only `promising_for_fresh_evaluation`; it does not activate a model.
Fresh, separately declared evaluation would still be needed. B17 stays in the
app throughout. The earlier contrastive-learning comparison is not rerun.

## Reproduction

With private source archives and existing processed training/selection data:

```powershell
.venv/Scripts/python.exe scripts/study_ipv6_realdata.py --output experiments/ipv6-realdata-pilot-reproduction
```

The output root must not exist. The loader checks exact acquisition archive
hashes, original collection/role bindings, Chrome lifetime proofs, family/row
inventories and original training/selection export hashes. IDs/sessions cannot
cross roles. A combined manifest saves exact training and assessment IDs.
Audit hooks reject failed/prior-protected/remaining acquisition data, calibration,
public final records and network connections. No raw endpoints or process identity
become classifier features. Source-model replay evidence is not a selection score.

The run outputs `config.json`, `data-manifest.json`, each arm's complete `bundle/`,
`development.json`, `predictions.json`, and one write-once `decision.json` under
`experiments/ipv6-realdata-pilot-v1/`. Source/version/seed/normalizer/provenance
are bound into the exports. No template or fixture is evidence of a trained win.

## Actual outcome

The fixed pair completed on 5 November 2026. The control reproduced the original
forest weights exactly before the candidate fit. Both numeric exports matched
their sklearn models. All five declared gates passed:

| Reused development measure | Matched control | Plus real IPv6 |
| --- | ---: | ---: |
| Local mean-budget macro-F1 | 0.780557 | 0.983806 |
| YouTube mean-budget recall | 0.644444 | 0.975000 |
| Instagram mean-budget recall | 0.928571 | 0.964286 |
| Public mean-budget macro-F1 | 0.896904 | 0.894825 |

The local F1 gain is 0.203249; the public F1 loss is 0.002078, below the fixed
0.02 allowance. Neither local service regresses and every public class stays
within the fixed 0.05 recall-loss limit. These are raw top-class decisions, not
accepted predictions under a calibrated confidence policy.

Raw local top-class counts make the effect easier to interpret:

| Requested packets | Control correct / eligible | Plus real IPv6 correct / eligible |
| --- | ---: | ---: |
| 5 | 13/17 | 15/17 |
| 10 | 12/17 | 17/17 |
| 20 | 10/15 | 15/15 |
| 30 | 12/14 | 14/14 |

At ten packets, YouTube/IPv6 improves from 1/5 to 5/5 and Instagram/IPv6 from
6/7 to 7/7; YouTube/IPv4 stays 5/5. There is no Instagram/IPv4 assessment cell.
At five packets, one Instagram and one YouTube/IPv4 connection remain wrong.
No public class improves uniformly: mean recall drops 0.025 for Spotify and
0.030 for Snapchat, within the predeclared 0.05 limit. Do not hide those losses.

This is useful evidence that adding real examples can repair the observed
development failure. It does **not** justify a claim of 98.4% accuracy on new
traffic. The assessment has only 17 local connections from three old visits;
prefixes are correlated, the development set has been reused, the new training
visits are later, and Instagram/IPv4 is absent. Only one seed was run. The
result cannot isolate an IPv6 effect from the other new-session differences.

The decision is `promising_for_fresh_evaluation`. No extra seed or treatment was
run after seeing the result. The candidate remains uncalibrated and is not
activated; the app still uses B17. The remaining acquisition slots stay paused.
A separately declared, unseen-session evaluation and a confidence-policy check
are required before making a reliability claim or promoting this candidate.

An independent offline audit blocked all original/new training rows, protected
records and network connections, replayed all **4,126 probability vectors** from
the exported bundles with **zero difference**, and independently recounted all
**16 confusion matrices** and five gates. This verifies saved inference and
metric arithmetic; it does not supply independent traffic or a second model
implementation.

Actual fit/feature/export/assessment wall time was 107.0 seconds for the control
and 114.3 seconds for the candidate on this laptop, with two CPU threads. These
are training-run durations, not live packet-to-prediction latency measurements.

An additional bounded CPU check loaded both exported models while all source
datasets and network connections were blocked. With 20 warmups and 100 timed
batch-one `Predictor.predict` calls per case, two CPU threads, one real saved
development connection, and Python 3.11.9 on this Windows laptop:

| Model | Packets | p50 inference, ms | p95 inference, ms |
| --- | ---: | ---: | ---: |
| Control | 10 | 3.347 | 4.251 |
| Control | 30 | 3.215 | 4.209 |
| Plus real IPv6 | 10 | 3.082 | 4.105 |
| Plus real IPv6 | 30 | 3.162 | 4.135 |

The timed function includes feature extraction and response/policy formatting;
process imports, model load, capture, packet arrival and UI transport are
excluded. Model load took 745 ms for the control and 614 ms for the candidate
in this process. This small sequential measurement verifies usable CPU inference
without training-data access. It is not a general speed comparison, p95 live
event latency, concurrency result or hard timing guarantee. All individual
timings are preserved in `cpu-benchmark.json`.

Local artifacts are under `experiments/ipv6-realdata-pilot-v1/`:

- `plus-real-ipv6/bundle/`: complete candidate inference bundle.
- `control/bundle/`: matched control; metadata identifies this pilot but weights
  reproduce the original forest exactly.
- Each arm's `development.json` and `predictions.json`: full per-budget,
  per-service/family results and probability vectors with observed lengths.
- `config.json`, `data-manifest.json`, `decision.json`, `independent-audit.json`:
  fixed inputs, inventories, checksums, gates and replay evidence.
- `cpu-benchmark.json`, `completion.json`: actual CPU timings, verification,
  preserved earlier-result checksums and artifact inventory.

These private/local experiment outputs are ignored by Git. Preserve them with
the private recording archives when reproducing the run; the committed code and
config do not contain those recordings. Candidate artifact identity:
`0b87d388d91fdeb4c6c87fc8a76ce8a718a02415c69c9346e1d222154b5b0473`.
Decision SHA-256:
`8b045c3b15c8044b26b443624b629aafff4dc84573e107d7463aabc2ef6f378f`.
Candidate `forest.json` SHA-256:
`78efcee31f1ce49a882283b8d4a585bfbc9c0980e40ace68587a98b811d5eecb`.
Combined data manifest SHA-256:
`e8ca6c74870b50da2ff500fb5f3b5fc52cf0c2c3b433edf29920080d709cd33e`.
Independent audit SHA-256:
`bb758a7e0a645fca7d2b28a22a8365b09d85e3347cc888c2805fff36f6af84aa`.
The local audit and benchmark source scripts are preserved at
`experiments/ipv6-realdata-engineering/audit-pilot.py` and
`experiments/ipv6-realdata-engineering/benchmark-pilot.py`, each bound by its
saved report's source hash. They are write-once evidence producers; preserve
their existing outputs instead of rerunning into the same files.

The complete candidate is also packaged locally as
`artifacts/local/NetEmbedAI-ipv6-pilot-seed17-UNCALIBRATED.zip` (1,212,465 bytes).
Its three bundle files were verified byte-for-byte against the originals and
the ZIP integrity check passed. SHA-256:
`5ae0ce751fb7749b980d3d8755485471ba1bae7f7ee8b43063d0e3e559d5e90c`.
CPU report SHA-256:
`090632fcf66701c2b091e33dd86907766b50aff5a52123c9d0892da84506a87b`.
Completion receipt SHA-256:
`31d2b60041592cfefd89e18ae27aac8c00d1d0c1af0c3895b3c8230b523a449e`.

The completion check rehashed the original forest, failed calibration decision
and completed paired comparison: all are unchanged. Read-only local API checks
confirm the B17 artifact identity is unchanged and capture is stopped. None of
the remaining three acquisition intents exists. The forest is retained as a
promising simple candidate; its development gain does not replace the earlier
matched neural/contrastive comparison or authorize a default change. B17 stays
default because this candidate still lacks fresh evaluation and fitted local
acceptance policy.

Software verification after both fits: `python -m pytest -q` passed all 424
tests in 37.00 seconds, with two existing dependency deprecation warnings.
`python -m ruff check src tests scripts` and
`python -m ruff format --check src tests scripts` pass (130 files). The UI was
not changed by this pilot; these checks do not constitute live validation.

To inspect the actual local results without rerunning a fit:

```powershell
Get-Content experiments/ipv6-realdata-pilot-v1/decision.json
Get-Content experiments/ipv6-realdata-pilot-v1/plus-real-ipv6/development.json
Get-Content experiments/ipv6-realdata-pilot-v1/independent-audit.json
Get-Content experiments/ipv6-realdata-pilot-v1/cpu-benchmark.json
Get-FileHash artifacts/local/NetEmbedAI-ipv6-pilot-seed17-UNCALIBRATED.zip -Algorithm SHA256
```

Refitting with the reproduction command above should reproduce forest weights
and predictions with the pinned environment and inputs; creation timestamps,
source-commit metadata, bundle identity, durations and ZIP bytes may differ.
Do not activate this uncalibrated bundle to demonstrate accepted live labels.
