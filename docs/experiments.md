# Reproduction and model selection

All commands run from the repository root after setup. On PowerShell use .venv/Scripts/netembed.exe; once the environment is activated, the shorter netembed commands below are identical.

## Recover legitimate data

The original local HDF5 is truncated. CESNET's DataZoo endpoint currently returns HTTP 503 (https://github.com/CESNET/cesnet-datazoo/issues/13). The recovery script copies it to a separate path and resumes only when the official server honors the byte range; it never overwrites the original. CESNET points to the original CSV archive on Zenodo as a fallback: https://zenodo.org/records/10728760. Download `cesnet-quic22.zip` and `servicemap.csv` there; keep the ZIP compressed.

~~~powershell
.venv/Scripts/python.exe scripts/recover_data.py --seconds 300
netembed export-cesnet --source data/recovered/CESNET-QUIC22-XS.h5 --output data/processed/flows.jsonl --license CC-BY-4.0 --per-class-day 200
netembed prepare --source data/processed/flows.jsonl --provenance data/processed/flows.jsonl.provenance.json --output data/processed/v2
~~~

For the Zenodo CSV ZIP, use the streaming adapter after the download completes:

~~~powershell
netembed export-cesnet-csv --source C:/Users/shrey/Downloads/cesnet-quic22.zip --output data/processed/flows.jsonl --license CC-BY-4.0 --per-class-day 200
netembed prepare --source data/processed/flows.jsonl --provenance data/processed/flows.jsonl.provenance.json --output data/processed/v2
~~~

The CSV adapter verifies the complete ZIP against Zenodo's MD5 `2d52ad44ddb22645a3464634fc54bb9c` before streaming members. It reads only flow ID, capture time, APP and the three PPI channels; service-map domains are never predictor inputs. The official `flows-YYYYMMDD.csv.gz` file date defines chronological partitions, matching the HDF5 day tables. `TIME_FIRST` can show the previous UTC calendar day at a file boundary and is retained for audit, never model input. The adapter rejects invalid sequence shape, units, directions and sizes. The real ZIP passed its checksum and full bounded export: 42,000 rows, exactly 200 per selected class/day over 21 days. It retains deterministic first-per-class/day sampling and records counts and source checksums; this is an engineering sample, not a population-prevalence estimate.

Recovery is bounded to five minutes per invocation. At roughly 1 MB/s the missing 2.38 GB would take about 40 minutes, plus server delays; this is an estimate, not measured recovery throughput. The endpoint now returns HTTP 503. The expected complete local-file size from the HDF5 header is 2,714,067,131 bytes. Repeated invocations resume the recovery file when the server recovers. A checksum alone does not prove origin; retain the official source URL, license and exporter metadata.

The separate HDF5 exporter expects official /flows/DYYYYMMDD tables with APP enum, PPI and PPI_LEN. It rejects incompatible layouts. That adapter is tested against an explicit schema fixture; full HDF5 verification remains pending because the local HDF5 is truncated. Preparation checks class support and duplicate IDs/groups. Exact short packet-feature patterns recur across unique flow IDs and are retained with a collision audit in the manifest; feature equality alone is not proof of duplicate capture.

An already authorized JSONL export can be imported directly. Every row needs id, date (YYYY-MM-DD), label and packets; optional group_id controls session grouping. The provenance file requires dataset=CESNET-QUIC22, version, license, exporter, direction_verified=true and source_sha256 matching the JSONL file. Do not label synthetic fixtures as CESNET. Test-only fixtures must carry fixture=true.

## Pilot then fixed comparisons

~~~powershell
netembed train --data data/processed/v2 --config configs/pilot.json --output experiments
~~~

This is a two-epoch seed-17 exploratory pilot, not a benchmark or selected default. Record epoch time/memory before expanding. Training prints an immutable run directory; its bundle/ is independently loadable and resume.pt is a trusted local training checkpoint.

configs/matrix.json enumerates the 15 required candidate/seed combinations: forest plus A/B/C/D for seeds 17,42,123. Use one JSON object per train invocation. All neural runs share architecture, uniform prefix budgets, sqrt-inverse training class weights, Adam settings, epoch budget, stopping rule and development stresses. Seeds separate initialization, loader/prefix sampling, augmentation and evaluation.

After freezing `configs/selection-policy.json`, materialize explicit run configs and train one candidate at a time on memory-limited laptops:

~~~powershell
.venv/Scripts/python.exe scripts/materialize_matrix.py --matrix configs/matrix.json --policy configs/selection-policy.json --output experiments/configs/generated
netembed train --data data/processed/v2 --config experiments/configs/generated/tcn-ce-aug-17.json --output experiments/full-real
~~~

The 15 generated names cover three forest seeds and A/B/C/D for each neural seed. On this laptop two concurrent neural trainings left under 1 GB available RAM, so the remaining formal runs should be sequential. An interrupted run can resume from its `resume.pt` with the exact same config using `--resume`; a resume creates a new immutable run directory and preserves the partial original.

`.venv/Scripts/python.exe scripts/run_matrix.py --dry-run` lists the remaining work without starting it. After any separately running training has stopped, `.venv/Scripts/python.exe scripts/run_matrix.py` executes one local candidate at a time, resumes the newest matching checkpoint, evaluates completed bundles on the development selection split, and refreshes `comparison.json`. It skips completed runs and stops on a failed command; it never reads the final test or starts capture. For earlier unaugmented runs, the helper ignores the subsequently added unused augmentation-policy field. For forests it also ignores the training worker count, since the model parameters and data remain the same.

First reproduce A with the declared full budget (default 20 epochs, patience 5). The full-data seed-17 A run selected epoch 16: development clean mean macro-F1 0.8503663777292364 and 16-case score 0.7134464878753982. The common B/C/D `clean_floor` was frozen at **0.8403663777292364** before those runs. B/C/D reject a missing floor. Record the fixed floor in each config and the decision record. Every epoch uses mean macro-F1 across four budgets and clean/timing/padding/observation-loss conditions, subject to that clean floor. A two-epoch pilot must not be compared with a twenty-epoch finalist.

For B and D, `single-edit-50-clean-v1` deterministically assigns each flow/epoch to three clean slots and one slot each for the fixed timing, abstract +128-byte size padding and 10% observation-loss transformations. It applies at most one edit in raw units; the same seed/flow/epoch receives the same edit in both candidates regardless of loader order. This policy was frozen after an exploratory seed-17 B run revealed that applying all three edits to every example collapsed clean quality and that the trainer stopped before any epoch met the clean floor. That five-epoch run is excluded from formal comparisons. The trainer now waits for the full epoch budget if no eligible checkpoint exists and writes a failure record if the floor remains unmet.

~~~powershell
netembed train --data data/processed/v2 --config CONFIG.json --output experiments
netembed train --data data/processed/v2 --config CONFIG.json --output experiments --resume experiments/RUN_ID/resume.pt
netembed evaluate --data data/processed/v2 --bundle experiments/RUN_ID/bundle --split selection --output experiments/RUN_ID/selection
.venv/Scripts/python.exe scripts/compare_runs.py --root experiments/full-real --output experiments/full-real/comparison.json
~~~

Resume requires identical configuration and data hash. Increasing a run budget is a new declared experiment, not a silent resume change. Training never opens the final test. Calibration is fit only on calibration rows; the selection subset chooses epochs/models. The comparison script reads completed selection reports only, verifies bundle identity and manifest consistency, reports paired score/clean differences and lists missing runs. It evaluates the predeclared SupCon rule only after all three B/D pairs exist. An incomplete comparison is not a model decision.

Select the simplest viable model using configs/selection-policy.json. SupCon is retained only when D beats B in all three paired seeds, mean score gain is at least 0.01 and clean loss is no more than 0.01. Report A/B and C/D separately to distinguish augmentation effects. Prefer the forest when within 0.01 and measured CPU latency is no worse. Use a predeclared seed for deployment (17), not the best-looking test run. The completed comparison selects augmented cross-entropy B; its frozen [decision record](../configs/default-decision.json) predates the held-out evaluation. The comparison script aggregates evidence but does not silently select a default.

## Freeze and evaluate once

Create a decision JSON with artifact_id (bundle metadata SHA-256), data_manifest_sha256, rationale and development_runs (the supporting run IDs). This is an audit gate, not proof that a human made a sound decision. The completed local choice is in `configs/default-decision.json`, saved before the test was opened. To reproduce its final evaluation from the same verified data and bundle:

~~~powershell
netembed evaluate --data data/processed/v2 --bundle experiments/full-real/20261024-151720-3532794c/bundle --split test --decision configs/default-decision.json --output experiments/full-real/20261024-151720-3532794c/final
netembed predict --bundle experiments/full-real/20261024-151720-3532794c/bundle --flow experiments/full-real/benchmark-flow.json
$env:NETEMBED_THREADS='2'
netembed benchmark --bundle experiments/full-real/20261024-151720-3532794c/bundle --flow experiments/full-real/benchmark-flow.json --output experiments/full-real/20261024-151720-3532794c/cpu-2threads.json
.venv/Scripts/python.exe scripts/benchmark_http.py --bundle experiments/full-real/20261024-151720-3532794c/bundle --flow experiments/full-real/benchmark-flow.json --output experiments/full-real/20261024-151720-3532794c/http-2threads.json
~~~

Evaluation writes predictions.jsonl and report.json with checksums. Protocols distinguish matched ≥30-packet and all-flow cohorts, budgets 5/10/20/30, clean and three deterministic stresses. Observational loss retains the first packet and reconstructs survivor gaps; timing adds bounded cumulative delay; additive size padding is an abstract feature transformation, not a claim about valid transmitted encrypted QUIC modifications. No fragmentation/dummy injection enters the official suite.

The evaluator refuses an existing output directory. Keep the original report immutable; choose a new output directory if checking a reproduction. The recorded final result is described in the [model card](model-card.md).

The CPU benchmark warms up 50 calls, measures 1,000 single-flow pipeline calls and 100 batches of 32. It records hardware, Torch threads and artifact identity. The separate HTTP helper starts a loopback-only local inference process, sends 1,000 keep-alive `/predict` calls, checks artifact identity and stops the process; it never starts capture. This measures local HTTP round trips, without a browser or packets. On the same recorded 19-packet flow and two-thread setting, the selected augmented TCN measured 16.06/18.94 ms CPU pipeline p50/p95 and 25.07/30.58 ms HTTP p50/p95; forest HTTP measured 122.92/141.09 ms. Earlier unaugmented TCN HTTP (4.80/7.15 ms) and forest CPU (111.6/128.1 ms) measurements were taken during different host loads; do not treat the cross-run differences as architecture-only effects. Separate preprocessing, model-forward, probability and full-predictor timing is now [measured on unchanged B17](engineering-checks-20261028.md). This closes the CPU-stage accounting gap; genuine new window delivery, browser paint and broader capture-to-screen evidence remain pending.

## Local validation gate

The [beginner local-testing guide](local-testing.md) describes the optional
handshake-reference checkbox, its separate map-based attribution, bounded feature
export, and limitations. Reference labels must never alter model outputs.

1. Load the selected legitimate bundle and a matching evaluation report. Verify the offline RFC fixture. Then compare an authorized capture against an independent CESNET/ipfixprobe reference export; the RFC fixture alone does not prove full exporter parity.
2. Personally select the intended interface and press Start before generating new connections. Confirm fresh packet events and model predictions at checkpoints. Stop and verify process exit. Record the predeclared load, duration, number of sessions and dropped/coalesced events.
3. Collect multiple fresh trials for at least two supported services, with separate development and held-out sessions. Maintain independently defensible per-flow labels; browser navigation is only trial context. Include background/unsupported traffic and report the denominator and failures.
4. Read /capture/summary before starting another session. Its bounded samples contain timing only: parser/queue/pipeline/event and browser receipt timing with p50/p95 when acknowledgements exist. Report p50/p95 plus counts/drops and observation delay. No local operational or quality claim exists until this real user-started gate is completed.

No test, install command, recovery script, or service startup starts real capture. Paid compute, publishing and merging require separate authorization.
