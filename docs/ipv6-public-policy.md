# Public-only refusal policy for the frozen forest

The added-data forest passed the [four new local visits](ipv6-fresh-evaluation-results.md)
as a raw classifier. Those visits remain evaluation data. This separate stage
fits a refusal threshold using only the existing historical CESNET calibration
partition, then checks API/runtime compatibility. It requests no new recording
and cannot establish local accepted-error or live-event latency by itself.

The declaration is `configs/ipv6-public-policy-v1.json`, canonical SHA-256
`c83ac2c52b58406994b9a79762545d91cfb8d06969767a24fda972a3cc94a5cb`.
It pins candidate identity, forest weights, data manifest, packet budgets,
sampling and policy rules before reading calibration examples. Seed, weights,
architecture, labels and training-only normalizer are unchanged.

## Fixed protocol

- Select the first50 CESNET calibration flows per class in stored order that
  actually reach ten packets. Preserve every selected ID and split checksum.
- Use each available10/20/30 prefix, with ten packets as the primary checkpoint.
  Correlated prefixes are not independent population samples.
- Check101 global thresholds0.00–1.00 in0.01 steps. Require pooled and ten-packet
  overall empirical error at most0.10 and coverage at least0.50. Require each
  class's pooled and ten-packet error at most0.10, and at least five accepted
  ten-packet cases per class. Choose the lowest eligible threshold.
- If no threshold works, preserve the entire curve and leave the policy
  unfitted. Do not retry, change the rules, fit weights or consult local scores.
- Python audit hooks reject local archives, other public splits, prior experiment
  outcomes and network connections during fitting. Complete bundle/source/data
  provenance is saved. No final-test records are used.

This fits a refusal rule, not a probability-of-correctness model or unknown-service
detector. The exported metadata states `validation_scope: cesnet_calibration_only`
and contains no locally checked labels. Its provenance is `public_calibration`,
not a browser/local-calibration claim. Even a feasible public policy does not
authorize an automatic switch of the live app. B17 stays in the current app;
independent local acceptance and replacement-model live evidence remain pending.

## Engineering changes

Predictions retain their existing status/label/score semantics and add
`policy_fitted`, `policy_scope`, and `decision_reason`. An unfitted policy still
withholds all accepted labels. The UI now says **Confidence check pending** for
that case and explains why, while keeping raw alternatives visible. A fitted
public-only policy displays its actual calibration scope in the model details.
Old recorded responses without the additional fields remain supported.

The existing API and capture pipeline accept a forest through the same complete
bundle interface. An isolated real-artifact API/Replay smoke check can verify
that contract without opening packet capture. Recorded replay and software
fixtures cannot close the new model's actual live-validation gate.

## Reproduction

From `traffic_classification`, using the existing real candidate and processed
CESNET calibration data, choose a new output directory:

```powershell
.venv/Scripts/python.exe scripts/fit_public_policy.py --output experiments/ipv6-public-policy-reproduction
```

The output directory must not exist. The run writes the full101-point `curve.json`,
`predictions.json`, `decision.json`, and only when feasible a complete `bundle/`.
Outputs bind source commit/hashes, exact model identity and cohort IDs. To inspect
the actual run, read `experiments/ipv6-public-policy-v1/decision.json` instead of
rerunning into that write-once location. Private data/artifacts are not committed.

## Actual outcome — 6 November 2026

The one declared fit completed from source commit
`1ce1848ded57a9b4888f20c00a1918bee42464fc`. It selected **0.76**, with at least
ten packets required. This rule is fitted on500 historical public calibration
flows /1,058 available prefix cases. These are **fitting-set statistics**, not
new local accuracy or an unseen-test error estimate:

| Calibration population | Accepted / total | Mistakes among accepted | Coverage | Accepted error |
| --- | ---: | ---: | ---: | ---: |
| Ten-packet primary | 275/500 | 3 | 55.0% | 1.09% |
| All available10/20/30 cases | 581/1,058 | 4 | 54.91% | 0.69% |

The rejection cost is substantial and uneven. At ten packets:

| Reference class | Accepted /50 | Mistakes among accepted |
| --- | ---: | ---: |
| YouTube | 11 | 0 |
| Spotify | 10 | 0 |
| Instagram | 39 | 0 |
| TikTok | 50 | 0 |
| Snapchat | 16 | 0 |
| WhatsApp | 25 | 1 |
| Messenger | 24 | 2 |
| Discord | 50 | 0 |
| Google Drive | 16 | 0 |
| Outlook | 34 | 0 |

The policy therefore does not answer reliably or frequently for every service
just because its aggregate accepted error is low. In particular, it rejects
78% of the public YouTube primary cases. No threshold is lowered after viewing
this result. The completed four-visit local test and older failed calibration
stay unchanged and are not used to fit or retune this policy.

## Real-artifact runtime evidence

The independent verifier replays all1,058 calibration vectors with maximum
difference0.0, checks that policy export changes no probability vector, and
independently reconstructs every statistic/eligibility result in all101 curve
points. The forest weights, labels and normalizer remain identical.

The actual complete bundle loads without source-dataset access and passes
direct/API/CLI parity. API checks use in-process TestClient at5/10/30 packets,
including batch requests, readiness, model identity, policy reason/scope and
stopped capture. They open no packet capture. Windows' event-loop self-pipe needs
an internal loopback connection; only the API verification phase permits that.
External connections remain blocked. An initial verifier failure at this socket
was preserved and fixed in the harness, without refitting or changing policy.
The CLI is checked as a separate process with explicit bundle/example paths.

On this laptop, Python3.11.9 / Torch2.5.1 CPU, two Torch/BLAS threads, using one
real public-calibration connection, each prefix had50 warmups,1,000 timed
single-flow calls and100 batches of32:

| Packets | Prediction pipeline p50 | p95 | Batch32 probability-pipeline flows/s |
| --- | ---: | ---: | ---: |
| 10 | 1.122 ms | 2.067 ms | 580.2 |
| 30 | 2.069 ms | 2.552 ms | 564.1 |

The pipeline includes feature extraction and response/policy formatting; model
load/imports are excluded. Batch throughput is not packet-capture line rate.
Core-model-only, actual HTTP TCP, capture/UI latency and concurrent-load timing
are not measured by this check. Different laptop runs/load can differ; this is
not evidence that the threshold itself improved speed.

Software checks: **451 Python tests**, two existing dependency warnings;
**135-file Ruff lint/format**, **19 UI tests**, UI formatting, TypeScript and
Vite build pass. The first restricted UI runner could not spawn esbuild; the
same tests/build passed with approved local execution. No dependency was added
and no remote CI run or capture is claimed.

## Inference artifact and evidence

The complete public-policy bundle is
`experiments/ipv6-public-policy-v1/bundle/`, artifact identity
`9878d0818370ede3e9897a9cc654b4ddc0afcd87d41b2d7134ccaf52592b528a`.
Its forest checksum remains
`78efcee31f1ce49a882283b8d4a585bfbc9c0980e40ace68587a98b811d5eecb`.

The local ZIP `artifacts/local/NetEmbedAI-ipv6-public-policy-v1.zip` is1,215,711
bytes and contains all three bundle files plus scope/attribution notes. ZIP
integrity and byte-for-byte file checks pass. SHA-256:
`82b6fc9f388602d96e0d11162c67476f5b83d1ded63fe06323ad45c3fcc2cd1f`.

Additional local reports under `experiments/ipv6-public-policy-v1/`:

| Evidence | SHA-256 |
| --- | --- |
| Decision | `ce3a08134b05ebd7c70a4c43306a403fecf485ed36ece26f01d67f8f43fc73c2` |
|101-point curve | `b4a17ba28806a491d73c8e8493213a825108b1685508802217b4467c89ba1b00` |
| Predictions | `f06c50d019009d400c2fca2fbf5687fd8e94081203c5aa64909f04fe560b0c61` |
| Runtime/recount report | `65c1b9e44e0f165f35c3561c10cf1cf88ca86e6d23f26da43790e4d74b16d88b` |
| Completion | `84743711742d8ea7f19ee8a8f70a5fc26867452b5c0ed9a49d121a9797466f1f` |

`verify-runtime.py` is saved beside its report, with source hash recorded in that
report. The script is write-once; inspect existing outputs instead of overwriting
them. The original uncalibrated bundle/ZIP and completed local test remain intact.

## Controlled preview and remaining live gate

The existing service can load this forest without another architecture or API.
For a deliberate candidate-validation preview, first stop the existing service
so only one capture service is used at a time. From a PowerShell in the project:

```powershell
$env:NETEMBED_ORIGINS = "http://127.0.0.1:8002,http://localhost:8002"
.venv/Scripts/python.exe -m netembed.cli serve --bundle experiments/ipv6-public-policy-v1/bundle --port 8002
```

Open `http://127.0.0.1:8002`; Start is still a separate deliberate user action.
No preview service was started by this stage, and the current8001 app remains
B17 with capture stopped. The UI displays this bundle's public-only scope.
Do not describe that preview as locally confidence-validated: accepted
error/coverage and packet-to-screen latency must be measured in separately
declared new user-started sessions. This stage requests no new recordings and
does not repurpose the four completed evaluation visits.
