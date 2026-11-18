# Fresh replacement calibration — 27 October 2026

**The replacement improved its fresh raw predictions but failed the frozen
calibration gate. It remains disabled.** It got 17/22 Instagram and 23/24 YouTube
available prefix points correct. These are correlated calibration points, not
final-test accuracy. No further recording was requested to dilute the errors;
no new training followed.

## Collection and checks

The seed-17 forest and version-2 protocol were frozen before both user-started
recordings. The unchanged B17 live model collected metadata; the replacement
was evaluated offline only after both recordings passed checks. Independent
browser references supply labels. Origins, endpoints and activity names never
enter model features.

| Recording | Session | Mapped connections | Packets | Prefix points |
| --- | --- | ---: | ---: | ---: |
| Instagram, 26 October | `e8d7a644dae84198af59611a623edb72` | 6 | 163 | 22 |
| YouTube, 27 October | `8ca6a999aab04598be875406e7d816b4` | 6 | 180 | 24 |

One Instagram connection has 13 packets; all others have 30. Budgets are
5/10/20/30 without padding extra quality points. All 343 sizes match unique
browser socket prefixes within direction, with no missing prefix packets.
This does not establish merged wire order, wire timing or historical exporter
quantization. All 193 original B17 live predictions reproduce exactly.

The complete Instagram inventory has 37 connections: six mapped, eleven outside
the supported set, fifteen ambiguous, one unverifiable and four unmatched. The
YouTube inventory has 35: six mapped, six outside the supported set, four
ambiguous, two unmapped and seventeen unmatched. Every refusal is preserved;
all mapped references enter calibration after feature checks. Whole sessions
remain excluded from weight fitting and candidate selection.

Both captures stopped at the two-minute guard, with zero processing drops,
zero reordered packets and no capture-process error. Coalesced counts are 34
and 22. All raw logs, packets, timing, references, audits, packet-only rows and
source hashes remain private under
`artifacts/local/browser-development/{instagram,youtube}-cal-02-*`.

## Why the policy remains unfitted

The unchanged protocol searches a global threshold on 0.00–1.00 in 0.01 steps.
It requires at least 30 accepted local points, five per service, and at most
10% empirical accepted error overall **and per local service**. The historical
public-calibration control also must pass (500 flows, 1,419 valid points).
Temperature stays 1 and minimum packets 5.

| Threshold example | Local accepted | Local errors | Instagram accepted/errors | Failure |
| --- | ---: | ---: | ---: | --- |
| 0.00 | 46 | 6 | 22 / 5 | Error limits |
| 0.41 | 37 | 3 | 18 / 3 | Instagram error 16.7% |
| 0.50 | 28 | 2 | 11 / 2 | Support and Instagram error |
| 0.55 | 21 | 0 | 6 / 0 | Fewer than 30 accepted |

At 0.41 the overall error is only 3/37, but YouTube performance must not hide
Instagram errors. At 0.55 accepted points happen to be correct but support is
too low for the frozen rule. None of 101 thresholds meets every constraint.
The report records `policy.fitted=false`, `selected=null`; no calibrated bundle
was created. Limits were not changed after viewing labels. These recordings
remain protected calibration data, not another training/selection study.

The remaining model issue is separation of correct Instagram decisions from
errors at useful coverage. Its specific cause and future-network performance
are unproven. A further model-development cycle requires a newly declared study
and independent evaluation; choosing another seed or tweaking this threshold
using these labels would not establish a valid repair.

## Latency and bounded browser work

The YouTube session exposes slow browser delivery. These are separate stage
distributions, not paired causal attribution:

| Stage, ms | p50 | p95 |
| --- | ---: | ---: |
| Capture to parser | 289.55 | 500.18 |
| Queue | 0.98 | 46.83 |
| Model pipeline | 26.86 | 56.44 |
| Capture to model event | 347.77 | 531.23 |
| Capture to browser receipt | 4,583.05 | 27,642.55 |

All 94 YouTube events were acknowledged. The Instagram session's 99 receipts
were 168.48/511.15 ms p50/p95. No averaging hides this regression. Receipt is not
paint latency. The cause, including any browser scheduling effect, is unverified.

The UI previously requested React row updates for every packet event. It now
keeps the latest actual update per flow and refreshes display rows once per
animation frame. Pending and visible rows are capped at 256. Actual cumulative
packet prefixes and model predictions are preserved. Every prediction is still
acknowledged immediately, before paint. Start/unmount cancel pending display
work. Nine UI tests pass, including burst coalescing, immediate acknowledgements,
bounded rows while paint is paused, and cleanup. TypeScript/Vite build and
Prettier pass. **Real-live latency improvement is unverified.** The preceding
184-Python-test result was not rerun for this UI-only change; actual calibration
and role/hash checks executed against these new records.

## Evidence and reproduction

Uncalibrated identity stays
`132caf41f5eb517afdb806bd1cab8b1e503e977adb3703b4d33d588264471ffb`.
Its weights/normalization, original B17 bundle and original held-out CESNET
report were rechecked unchanged. B17 remains loaded, capture is off, no training
job is running, and local commits are unpublished. Refresh loads the rebuilt UI
without starting capture.

| Evidence | SHA-256 |
| --- | --- |
| `experiments/browser-adaptation/calibration-02/report.json` | `70e38d5445a3913e886b6f327dfb88aa08307a010f3c273e2908ac1697400fa2` |
| `youtube-cal-02-capture.json` | `f34f3c1b4827dfafb3d10eb67bf5720120a617edb7ab994481f321cc2f957498` |
| `youtube-cal-02-collection-summary.json` | `a7ee67e911956443bf83acca5c3231ec1af1514a2e10d8162013350a6198f3af` |
| `instagram-cal-02-collection-summary.json` | `d2310af3c00f38e7581da2226f8defea2b40bc3066137b2d2b001b8f9dfd2cfb` |

Collection names are under the private collection directory. Output retains
all local/historical probabilities, the full curve and `verification.json`.
Reproduce from `traffic_classification` using existing private inputs and a new
output directory:

```powershell
.venv/Scripts/python.exe scripts/calibrate_browser.py --data data/processed/v2 --collection artifacts/local/browser-development --bundle experiments/browser-adaptation/forward-mass25-seed17/forest/bundle --decision experiments/browser-adaptation/forward-mass25-seed17/calibration-candidate-decision.json --plan-name calibration-collection-plan-v2.json --output experiments/browser-adaptation/calibration-02-repeat
cd ui
npm run test
npm run build
npm run format:check
```

Blockers remain: a candidate meeting local calibration, independent live quality
evaluation of that candidate, and live remeasurement of the UI change. Replay,
old CESNET scores and software checks cannot substitute for these gates.
