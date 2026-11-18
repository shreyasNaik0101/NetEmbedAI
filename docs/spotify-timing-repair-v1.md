# Matched Spotify timing repair — fixed protocol

This is one seed-17 pair: current-forest control versus a forest with nearest-millisecond timing applied before summary features in both training and exported inference. Same 32 trees, depth 12, minimum leaf 2, two threads, public/local weights, examples, saved normalizer and prefix views. No Spotify diagnostic example enters fitting.

The control must reproduce current forest.json SHA-256 78efcee31f1ce49a882283b8d4a585bfbc9c0980e40ace68587a98b811d5eecb before the candidate fit. The new feature-map name summary-nearest-ms-v1 explicitly binds np.rint ties-to-even to a candidate bundle. Existing artifact maps retain their behavior. Both study exports deliberately have unfitted policies; confidence from the prior model is not transferred.

Training is the unchanged public 14,000 plus 62 local YouTube/Instagram flows (original 43 + adopted 19). Public mass is 75%, local mass 25% balanced between local classes, with four equally weighted 5/10/20/30 views. This isolates training/inference timing representation within this pipeline; it does not add representative Spotify training examples or isolate every source of domain shift.

Retention uses the existing 17 local selection connections and first 50 public selection flows per class. The five exposed Spotify diagnostic connections measure development behavior only. They remain excluded until both fits complete. Public calibration/test, four fresh evaluation visits, two live-policy visits, other diagnostics and remaining acquisition slots are blocked by an audit hook. Training is newer than reused local selection, so the result is retrospective development, not forward accuracy.

## Fixed gates

All must pass:

- Spotify raw correctness at least 4/5 at ten packets, 3/5 at twenty and 2/3 at thirty; at least two additional correct ten-packet choices versus control.
- No mean local macro-F1 loss and no YouTube/Instagram recall loss at any prefix.
- Public macro-F1 loss at most 0.02 at each prefix and each service recall loss at most 0.05 at each prefix.

Failure ends this scope without a replacement fit, alternate seed, changed threshold or new capture. Success is only a development candidate, requiring separate confidence calibration and fresh evaluation before any deployment. Original seven-drop/two-exclusion Spotify warnings remain.

Config: configs/spotify-timing-repair-v1.json
Canonical SHA-256: 8cb134a30cd7fa6f0f664a059113495c7c308dbd070bd704f3a71ef6f3a5931b

~~~powershell
.\.venv\Scripts\python.exe scripts/study_timing_repair.py
~~~

Requires the legitimate local public data, original local exports, three adopted training archives and frozen reference bundles. The runner refuses existing output paths. Outputs go to experiments/spotify-timing-repair-v1, including complete bundles, data/provenance manifests, probability vectors, development metrics and decision. It never starts capture, installs anything or changes the live profile.

## Actual outcome — 7 November 2026 local time

**Rejected: stop_repair_rejected.** The matched timing-rounded candidate does not repair Spotify and regresses retained services. No alternate fit, seed, threshold, calibration, extra recording or activation follows this result.

| Raw top-choice result | Control | Nearest-ms candidate |
|---|---:|---:|
| Spotify, 5 packets | 0/5 | 0/5 |
| Spotify, 10 packets | 0/5 | 0/5 |
| Spotify, 20 packets | 0/5 | 0/5 |
| Spotify, 30 packets | 0/3 | 0/3 |
| Local YouTube/Instagram, 5 packets | 15/17 | 16/17 |
| Local YouTube/Instagram, 10 packets | 17/17 | 16/17 |
| Local YouTube/Instagram, 20 packets | 15/15 | 13/15 |
| Local YouTube/Instagram, 30 packets | 14/14 | 11/14 |

Mean per-prefix local macro F1 fell from 0.983806 to 0.927771. Mean public selection macro F1 changed from 0.894825 to 0.892996, within the aggregate retention limit, but public Messenger recall at thirty packets fell from 48/50 (0.96) to 43/50 (0.86), failing the per-service guard. Only the public per-prefix F1 guard passed; the two Spotify checks, two local retention checks and public per-class check failed. A small five-packet local gain does not rescue later losses.

The control reproduced the current forest's weight SHA-256 exactly. Feature-building/fit/export took 113.73 seconds for control and 122.75 seconds for candidate on local CPU. JSON export versus sklearn maximum differences were 8.88e-16 and 1.22e-15. These are fit-pipeline timings, not request latency or model-only timings.

Independent evidence:

- All 4,162 saved probability vectors replay exactly (maximum difference zero), using only selection/diagnostic inputs; training/calibration/final files were blocked during the independent replay.
- All 2,081 candidate input cases match independently rounded raw gaps passed through the plain summary map and the same candidate trees.
- A separate JavaScript implementation recomputed all 4,162 top choices, per-class support/recall/F1, macro scores and all six gate outcomes.
- The full 485-test Python suite passed before the pre-fit checksum correction; all 13 timing-repair tests passed again after that correction. Ruff check and 141-file format check passed. UI code is unchanged in this experiment.

Execution diagnostics are retained under experiments/timing-repair-engineering. A raw-versus-canonical Windows line-ending checksum comparison stopped before any fit. A subsequent restricted execution could not create the Windows worker-pool named pipe, before workers fitted trees. That partial output is preserved as restricted-attempt. The identical protocol then completed with normal local process access. These execution recoveries changed no data, seed, hyperparameter or gate.

## Saved artifacts and hashes

- Control artifact identity: 9241752d4e500e1ae4a7c5e973072abacb4225d6a017c7941bb32d8094fe8221
- Control weights: 78efcee31f1ce49a882283b8d4a585bfbc9c0980e40ace68587a98b811d5eecb
- Rejected candidate artifact identity: 22dac0028ba843ca9ed6db742063f8f0417988063e71e2e433c5cccd117d29a0
- Rejected candidate weights: dced2ca71f7388838c2ffc15f0e992665b2e95536038a85e12b05c6c906e7785
- Decision SHA-256: 70c6bb84b7eb6c0d50019d4adb3087d58a550a5b4e7b1d5db7f85cacf6cce12c
- Data-manifest SHA-256: 3182e1b20b997249415d42387c16ba5dd1786828ace209665aa4946da80017ea
- Control predictions SHA-256: 5c78013921b908098cd12f16f6af02d5a04c80b8cc482d41eeeb4d901d35a220
- Candidate predictions SHA-256: c650b1ecdfbea64a75f36ef482f3d4f9205f83ccd8fba3a15602633bef1a6fb0

Bundles are in experiments/spotify-timing-repair-v1/control/bundle and nearest_ms/bundle. Both deliberately have unfitted acceptance policies. The control's metadata identity differs from the live artifact because study provenance/policy differ; its weights match. The candidate is retained as a rejected research artifact, not packaged as a validated release. Independent receipts are independent-replay.json and independent-metrics.json in the same output root. Source checkpoint: b7150c7 (implementation originally 15149d7).

The experiment is complete. The app keeps its existing model and documented Spotify limitation. Timing quantization alone is not a sufficient repair in this training pipeline. Further improvement would need a separately declared study, likely including representative Spotify development data and separate held-out evaluation; this result does not guarantee that will succeed.
