# Explicit ten-packet classifier

This separate narrower development task follows two failed multi-prefix studies. It does not revise their gates or outcomes. The 1% Spotify-weight forest is reused without fitting; both candidate and original control are now assessed using exactly ten observed packets. This choice was motivated by exposed development results and cannot be called independent model selection or fresh validation.

## Runtime behavior

The checksummed forest architecture declares fixed_prefix_packets=10. Fewer than ten packets return insufficient_evidence with no scores or label; direct probability scoring rejects short inputs. At ten or more, inference validates the submitted packet schema and uses only the first ten for feature extraction. The forest weights, saved normalizer, labels and raw feature units are preserved. Valid later packets cannot affect the score. There is no cached earlier accepted label or post-hoc display smoothing.

The API distinguishes observed_packets from model_packets and model_prefix_limit. model_packets is zero before scoring and ten afterward; model_observation_ms describes the ten-packet feature window, while the existing observation_ms retains the observed sequence duration. The UI shows the fixed budget and separately describes later observed packets. Recorded replay and live capture remain distinct. Capture is never started automatically.

This new artifact has an explicitly unfitted acceptance policy with minimum ten packets; no confidence threshold is inherited. Alternative scores remain experimental. The current live service is not switched to this artifact. The runtime support can render such an artifact honestly if a future separately authorized validation loads it.

## Frozen development comparison

Config: configs/spotify-ten-packet-v1.json, canonical SHA-256 9b30398a2a3c2788a908b3669371965399af99cb2910a0ea696aa762e6ec2158.

Source candidate: experiments/spotify-weight-study-v1/spotify-001/bundle; original artifact eddce5a1bcbcc80ec43b4b9b89b642827e74df7fde2f08a0cc81db2756f7b613. Weights SHA-256 b5a312fe86850a93fdc1c7b74cbfb6ffa58009e781888bafa5e47062e6f42adf.

All four Spotify development flows and seventeen original retained YT/IG flows reach ten packets. The previously frozen public selection cohort has 500 flows, of which 48 have fewer than ten packets. This was found in a preflight length inventory before exporting or evaluating the mode. The config therefore records the correction from the initial 500-case wording: exclude those 48 without replacement and compare both models on exactly the same 452 eligible IDs. The manifest retains all excluded IDs and lengths. These results are conditional on reaching ten packets, not full coverage over all public flows. No unknown data was pulled in to refill classes.

Six gates are fixed at this ten-packet feature budget: Spotify recall at least 0.60 and one additional correct case versus control; no retained local macro-F1 or per-class recall loss; public macro-F1 loss at most 0.02 and each class recall loss at most 0.05. These are gates for a new narrower task, not a retrospective pass for the 5/10/20/30 task. Training, calibration and final records are blocked by an offline access guard. Previous training archive metadata is read only to verify selection chronology; training packet data is not read. No new fits, seeds, weight variants or threshold search occur.

Run from traffic_classification with the existing legitimate local artifacts:

```powershell
.\.venv\Scripts\python.exe scripts/study_ten_packet.py
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m ruff check src scripts tests
.\.venv\Scripts\python.exe -m ruff format --check src scripts tests
cd ui
npm test
npm run build
npm run format:check
```

Output experiments/spotify-ten-packet-v1 is write-once. It contains a standalone bundle, source bindings, full predictions, metrics, exact-cohort inventory, real-artifact prefix invariance checks and a two-thread CPU benchmark (50 warm-ups, 500 calls). CPU timings are not packet-to-browser latency. Real-live recognition, confidence-policy quality, short-flow yield and time-to-tenth-packet require fresh evidence before a usable live demonstration can be claimed.

## Completed development evidence

The fit-free comparison on 8 November passed all six gates for this narrower ten-packet task:

| Exact ten-packet cohort | Control correct | Candidate correct | Control macro-F1 | Candidate macro-F1 |
|---|---:|---:|---:|---:|
| Spotify, one exposed development visit | 0/4 | 4/4 | 0.000000 | 1.000000 |
| Existing YouTube/Instagram selection | 17/17 | 17/17 | 1.000000 | 1.000000 |
| Eligible historical public selection | 405/452 | 407/452 | 0.902414 | 0.906845 |

Public support varies by class after excluding short flows: Outlook has fourteen eligible cases; YouTube forty-six; other classes forty-seven to fifty. Candidate public Messenger recall falls from 46/50 to 44/50, within the declared five-percentage-point limit; aggregate improvement does not mean every class improved. The 48/500 short-flow exclusions are an eligibility cost, not successful classifications or evidence about the distribution of real local short connections.

All 473 candidate probability vectors match the frozen source evaluated on ten packets exactly. Fifty-eight available real local 10/20/30-packet views produce zero score change when the fixed-ten model sees later packets. This demonstrates the declared scoring restriction, not later-prefix quality gain. Independent JavaScript checks verified 946 probability vectors, six cohort metric tables with all class metrics and confusion matrices, all six gates, identical eligible IDs, the short-flow inventory and eleven output hashes with zero mismatches.

The actual nonfixture bundle passed CLI and API checks after all dataset/capture-file reads were blocked. API requests with five packets returned no scores; ten/twenty/thirty observed packets all reported ten used and identical alternatives. Batch parity passed and capture remained stopped. The private verification runner is experiments/spotify-ten-packet-v1/verify_portable.py; its portable-check.json receipt is API/replay evidence, not live capture. The private probe-flow.json comes from the already exposed development recording.

CPU predict-call timing: two threads, fifty warm-ups and five hundred measured calls, median 3.866750 ms and p95 5.689985 ms on this machine during this run. This measures trained-model request processing on one real ten-packet input, not time to the tenth packet, queueing, capture-to-browser receipt or display latency. The separate CLI call is a parity check, not another timing distribution.

Software evidence: 547 Python tests pass with two existing dependency warnings. All 24 UI tests pass and the production build succeeds; Python lint, 151-file Python formatting and UI formatting pass. An initial concurrent UI run timed out in an existing 300-flow display test; it passed when the full UI suite ran alone. No timeout was relaxed. The new UI contract test passed in both runs. Tests cover short-input refusal without scoring, exact-prefix scalar/batch invariance including changed valid future packets, checksum/fixture preservation, invalid prefix/policy rejection, API reporting, and blocked training/calibration/final paths. The real-artifact experiment separately exercised the current study runner after its final formatting-only changes.

## Artifact and reproduction

Bundle: experiments/spotify-ten-packet-v1/bundle.

Artifact ID: fa1f4837e4ae11c9169258ecb20338ae3c0c81c2d206231fb6fe19405b8d8549.

Weights SHA-256: b5a312fe86850a93fdc1c7b74cbfb6ffa58009e781888bafa5e47062e6f42adf (unchanged from source).

Decision: experiments/spotify-ten-packet-v1/decision.json, SHA-256 e7536256414fc2a0ed6de05be790e64eb9a9f5a1312c2f11332054fafe1e11ac. It binds the output files, including full class probabilities and cohort inventory. independent-check.json and portable-check.json contain the subsequent verification receipts.

Local ZIP: artifacts/local/NetEmbedAI-ten-packet-v1-UNCALIBRATED.zip, 1,234,771 bytes, SHA-256 1dfea5e5bf1fab01f895243d784e126612c0804d945799b0397a361cbfc47f1e. Its three bundle files were compared byte-for-byte with the original files after packaging, and ZIP integrity checks pass. The ZIP contains the bundle and evidence summaries, not the private probe recording or training data. Use the updated repository runtime implementing this architecture contract.

An exact already-available replay command, from traffic_classification:

```powershell
.\.venv\Scripts\python.exe -m netembed.cli predict --bundle experiments/spotify-ten-packet-v1/bundle --flow experiments/spotify-ten-packet-v1/probe-flow.json
```

This returns policy_not_fitted, no accepted label, thirty observed packets and ten model packets. It is intentionally an uncalibrated model. For a new input, replace the flow path with a locally authorized schema-1 JSON flow; inference requires no training files.

The current live service and default model remain unchanged. The required next evidence is a separately frozen fresh verification/calibration protocol that covers Spotify and retained services, includes short-flow yield and measures actual user-started capture-to-model/browser behavior with this artifact. No such recording has occurred, no policy has been fitted and this is not a model-validated live release. Existing failed studies and their unused capture slots stay closed.
