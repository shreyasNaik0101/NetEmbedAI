# Bounded Spotify data repair

This separate study follows the rejected timing-only repair. Six visits maximum, one slot per attempt, fixed roles before capture, no replacement recordings after an unusable visit or failed gate. It is implemented software; model improvement remains unproven.

## Reserved visits

| Slot | Role | Activity / gate |
|---|---|---|
| spotify-train-01 | Train | Different artist; play 60 seconds |
| spotify-train-02 | Train | Different playlist; skip two tracks over 60 seconds |
| spotify-train-03 | Train | Different album; later local date than both preceding training visits |
| spotify-dev-01 | Development | Different music; only after two trained bundles are frozen |
| spotify-cal-01 | Calibration | Only after development passes; uncalibrated candidate must be loaded |
| spotify-eval-01 | Evaluation | Later local date than calibration; fitted policy must be frozen and loaded |

Each visit needs three independently verified Spotify connections reaching ten packets, including one reaching thirty. Training therefore needs at least nine ten-packet/three thirty-packet flows across three distinct sessions and at least two dates. All eligible target flows are included regardless of prediction. The original five-flow Spotify diagnosis and casual test stay excluded from fitting.

Use the phone hotspot, Wi-Fi 9, normal Chrome, one Edge viewer, reference ON and longer windows OFF. Fully exit Chrome before each preparation. Start stripped NetLog, then deliberately Start capture, then navigate Spotify. Activity lasts 60 seconds; capture is capped at 120. Stop app and browser log; keep Chrome open until archival verifies lifetimes. Never refresh during capture or Start again before archive. The app retains one current session; archival binds the stopped session before processing. No automatic capture occurs.

Browser matching and unique socket-prefix QC determine usable flows. Ambiguous, missing and excluded cases remain in inventories. Evidence eviction or longer windows fails collection. Training/development/calibration can retain counted event/inference drops if target QC passes, and are not called clean operational validation. Final evaluation requires zero reported drops. The fixed expanded NetLog profile is 1 GiB/8M source events and 256 MiB/2M retained events; live limits and matching rules are unchanged. Processing errors resume on the same bound recording; unusable visits stop scope.

## Fixed model and policy rules

One seed-17 control/candidate pair: 32 trees, depth 12, minimum leaf 2, two CPU threads, original summary-v1 features and saved normalizer. Control retains the public 14,000 + local 62 YT/IG training rows and must reproduce current weights. Candidate adds all eligible new role=train Spotify rows. Both keep 75% public/25% class-balanced local training mass; candidate local mass is balanced across three classes. Data and per-class weighting change together; this is a pipeline intervention, not isolated data causality. No timing-repair retry, seed sweep, extra architecture or confidence transfer.

Development uses the new reserved Spotify visit plus original 17 YT/IG selection flows and first 50 public selection flows/class. Require Spotify raw recall at least 0.60 at 10/20/30 and at least one more correct primary case than control; no mean local macro-F1 loss or YT/IG per-prefix recall loss; public per-prefix F1 loss at most 0.02 and each class recall loss at most 0.05. All must pass. Reused retention is retrospective development, not fresh YT/IG generalization.

Calibration fits one global threshold using historical public calibration (first 50 eligible flows/class) and the separate local Spotify calibration visit. Select the lowest eligible value among 0.00–1.00 by 0.01. Public constraints: empirical error at most 0.10, coverage at least 0.50 and at least five accepted primary cases per class. Spotify requires at least two ten-packet accepts, primary coverage at least 0.50 and zero empirical accepted errors (also pooled 10/20/30). Infeasibility stops scope. Scores are not correctness probabilities or unknown-service detection.

The later final visit must run the actual fitted candidate in capture. Primary ten-packet checks: at least two accepted Spotify flows, coverage at least 0.50, zero accepted errors, raw correctness divided by all eligible target flows at least 0.60, real prediction/browser receipt samples and zero reported drops. Missing live checkpoints stay distinct from refusals and are never filled with replay. Other prefixes/latencies remain descriptive. One small visit cannot establish population reliability or a broad release. No automatic default promotion.

## Commands and artifacts

Config: configs/spotify-data-repair-v1.json
Canonical SHA-256: f4853905ca5bcb0b17bdda8ce92935737a0fa98ceb00c03a24fad33604a6f50e
Collection: artifacts/local/spotify-data-repair-v1
Stage bundles/results: experiments/spotify-data-repair-v1

~~~powershell
.\.venv\Scripts\python.exe scripts/spotify_data_repair.py status
.\.venv\Scripts\python.exe scripts/spotify_data_repair.py prepare spotify-train-01
.\.venv\Scripts\python.exe scripts/spotify_data_repair.py archive spotify-train-01
~~~

Repeat only for declared slots in order. The agent runs preparation/archival; the user deliberately starts/stops capture/logging. Later preparation is blocked until bound stage receipts pass. At the completed-data gates:

~~~powershell
.\.venv\Scripts\python.exe scripts/spotify_data_repair.py fit
.\.venv\Scripts\python.exe scripts/spotify_data_repair.py assess
.\.venv\Scripts\python.exe scripts/spotify_data_repair.py calibrate
.\.venv\Scripts\python.exe scripts/spotify_data_repair.py evaluate
~~~

After the corresponding stage passes, stop the verified idle validation service before launching its stage-bound source:

~~~powershell
.\.venv\Scripts\python.exe scripts/spotify_data_repair.py serve spotify-cal-01
# After calibration passes:
.\.venv\Scripts\python.exe scripts/spotify_data_repair.py serve spotify-eval-01
~~~

These serve the same localhost 8002 app with explicit origins; they never Start capture. Windows agent execution of sklearn may require normal local process access for its worker-pool named pipe. No cloud/GPU payment, administrator setting change or public deployment is required. Existing outputs/decisions are write-once. Execution failures are preserved, not permission for model tuning or replacement recordings.

## Evidence and pending work

512 Python tests passed with two dependency warnings; Ruff check and 145-file format checks pass. Constructed tests cover roles, dates/session isolation, support, blocked future stages, protected data, synthetic-capture rejection, public/local calibration conjunction and retention. Chrome preparation is tested open/closed without capture. UI is unchanged from the 23-test/build checkpoint.

First training visit on 7 November is archived usable: nine verified Spotify connections, zero reported drops, two excluded missing-socket-prefix cases. Available target prefixes: {"5":9,"10":9,"20":8,"30":5}. Source replay checked 201 actual prediction vectors with zero changed labels or alternative-score difference. Archive SHA-256: 6cd79eafc943216e63e08ed2bbb5d4f53e21c86fa35b7ebe84507bbcacd2ca0d.

Second training visit on 7 November is archived usable: four verified Spotify connections, two excluded missing-socket-prefix cases and two reported drops. The frozen training rules permit counted drops when target QC passes; this visit is not clean operational validation. Session: b46ca09a173b40ba8f55bbe521c7b025. Archived rows SHA-256: e638941352d51689355a008118b65b1d3d7db0d69adfbe5c6b7651f7ebb51f09. The user confirmed the first visit did not include two track skips; that is consistent with its play-only activity. Track skipping was assigned only to the second visit.

Third training visit on 8 November is archived usable: four verified Spotify connections, two excluded missing-socket-prefix cases and eleven reported drops. It is usable training data under the frozen rules, not clean live-operation evidence. Available prefixes: 5:4, 10:4, 20:3, 30:3. Session: 00771f63c6804f3e9622c45b90500dad. Archive SHA-256: 245562e49c2d8088d59cf34d01a412dab96296a894a883511a3a9c24e909c1f8. All 229 saved source prediction vectors reproduced without score differences or changed decision labels.

Three training visits across two local dates are complete: seventeen eligible Spotify flows at ten packets, fifteen at twenty and eleven at thirty. Both declared CPU fits completed on 8 November, with no extra seed or parameter search. Control feature generation/fit/export took 25.918 seconds and reproduced the existing weights exactly (SHA-256 78efcee31f1ce49a882283b8d4a585bfbc9c0980e40ace68587a98b811d5eecb). Candidate feature generation/fit/export took 29.093 seconds. Both portable exports passed sklearn probability parity on fixed public/local probes. An independent Node check verified all ten files in the training receipt without checksum mismatches.

Candidate bundle: experiments/spotify-data-repair-v1/training/plus_spotify/bundle. Artifact ID: 59758540df8582e665994c3d55d986a84bc79c17676791e87e0cec5b13b63b9b. Candidate weights SHA-256: fab948ac0d4b676ed38d9355344697e1e11c8325d5bc163c62870f8f0bd742c5. Training receipt: artifacts/local/spotify-data-repair-v1/training-stage.json, SHA-256 9e7f1dde2213b0bedf4d93b1cb739856e7f7ec682c3a1058347a20322fdeaf57. Data manifest SHA-256: 97007f32673c1bcbc262cc1a237bdc8c629dc232658a6b4b951fc9620db39b4d.

## Development result: stopped before calibration

The reserved spotify-dev-01 visit on 8 November was archived usable: four independently verified Spotify flows, all reaching thirty packets, two excluded missing-socket-prefix cases and twenty-two reported drops. This is an offline model-development comparison, not clean operational validation. Session: a2477a50fade4d398057e7378f3ea962. Archive SHA-256: 2c6641e357febaff4597f549020a8eb995b16e379be593f686413c499298ee66. Archived row SHA-256: 3eaa25474592b0ca2899f876faa115f08d4d8648e47651c6fa408a0ae61f092e.

The control and candidate were frozen before this visit. Their raw top-choice results are:

| Cohort / packet budget | Control correct | Candidate correct |
|---|---:|---:|
| New Spotify / 5 | 0/4 | 4/4 |
| New Spotify / 10 | 0/4 | 4/4 |
| New Spotify / 20 | 0/4 | 4/4 |
| New Spotify / 30 | 0/4 | 4/4 |
| Existing YT/IG selection / 5 | 15/17 | 14/17 |
| Existing YT/IG selection / 10 | 17/17 | 15/17 |
| Existing YT/IG selection / 20 | 15/15 | 14/15 |
| Existing YT/IG selection / 30 | 14/14 | 13/14 |

This is evidence of improved Spotify raw classification on four connections from one new development session. It is not calibrated acceptance, final accuracy or four independent user sessions. Additional local data and class weighting changed together. All cohort comparisons are offline replay; missing live predictions are not filled for a live-operation claim.

Three of six frozen gates passed: Spotify per-prefix recall, primary correct-count gain and public per-prefix macro-F1 retention. Three failed: local mean macro-F1 retention, local per-class/per-prefix recall retention and public per-class/per-prefix recall retention. Existing local mean macro-F1 fell from 0.983805668 to 0.941893903. Local YouTube recall at 5/10/20/30 fell from 9/10, 10/10, 10/10, 9/9 to 7/10, 9/10, 9/10, 8/9. Local Instagram ten-packet recall fell from 7/7 to 6/7. Public mean macro-F1 slightly increased from 0.894825332 to 0.895525721, but this aggregate masks class regressions exceeding the five-percentage-point allowance: Snapchat ten-packet recall fell 41/50 to 37/50; WhatsApp thirty-packet recall 47/50 to 44/50; Messenger thirty-packet recall 48/50 to 45/50.

Independent JavaScript checks recounted all 4,158 probability-vector argmaxes, all 24 cohort/budget metric tables including every class's precision/recall/F1, cohort mean macro-F1 and all five development output checksums, with no mismatches. Receipt: experiments/spotify-data-repair-v1/independent-development-check.json. No new software code was changed for these experiment results; the prior 512-test checkpoint still describes the implementation.

The write-once development decision is failed_stop. Decision: experiments/spotify-data-repair-v1/development/decision.json, SHA-256 12643618187ce9b4685e0a3017e8ca4fd92a73aa2feb47fef2c7ead217b6d2d7. Full probability files: control-predictions.json (SHA-256 432fb2ff03eb09b1bb255509fe4d6b54efbd3b2361f96ab1e49230e823a3b038) and plus_spotify-predictions.json (SHA-256 7ee5dad10d7c0605a65baffeedb3aaa4d115d72d603a36028f35269a7be029c3) in the same directory.

This study stops after four of the six reserved visits. Calibration and final evaluation are blocked by the failed development gates, not merely pending a new recording. No replacement fit, seed, relaxed gate or extra visit is authorized by this protocol. Both study bundles retain unfitted refusal policies and were not activated; the live app continues to use the existing public-policy model. The data intervention helped Spotify in this small development sample but did not meet the required overall retention. A future study would require a separately declared protocol rather than relabeling this result as a pass.
