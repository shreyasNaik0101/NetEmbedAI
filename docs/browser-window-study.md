# Browser-side longer-window diagnostic — 28 October 2026

The fixed one- and three-second feature models did **not** improve on the matched first-30-datagram control. Both fail the development F1-gain and per-service recall gates. Keep B17 unchanged; neither new model is deployed or calibrated.

This diagnostic used existing legitimate Chrome UDP socket records, not a new capture. It does not establish accuracy on TShark traffic. The separate [genuine window recording](window-engineering-01.md) verifies collection functionality and remains unscored.

## Frozen comparison and data roles

Source/config commit: `c51efe8e120557d3216459de5a7275d722036e09`, committed before scoring. Config: `configs/browser-window-study.json` (SHA-256 `23097095d1926f1892409c398a06bd77b4874ba58a2a7d52ad073d3fd7e7d3d0`).

Training uses legacy `instagram-dev-01/02` and `youtube-dev-01/02`: 17 connections, five Instagram and twelve YouTube, from four recordings. Selection uses the explicitly retired `cal-01` pair: fourteen connections, seven per service, from two later recordings. These visits were already reused for development. They are not an independent test or calibration set. All 31 originally eligible connections pass the additional fixed window checks; no new exclusion was needed.

No cal-02, prospective dev-03 or later inputs, original final-test data, or unscored window-engineering-01 data enter the study. The audit guard rejects these paths. Origins supply independently matched references only; model features contain no names, endpoints, processes or identifiers.

Every model is the same fixed 32-tree Random Forest, depth 12, minimum leaf size two, balanced class weights, seed 17, two jobs. The comparison is local-only and closed-set YouTube versus Instagram. It is **not** the earlier ten-class public+local forest, and its fourteen connection decisions cannot be directly compared with that study’s 54 repeated prefix checkpoints.

The primary control uses summaries of at most thirty UDP datagrams from the same browser observer, same retained connections and same labels. A secondary capture-prefix control exposes observation-point differences. Windows use twelve predefined scalars plus sixty directional 100 ms packet-mass bins; the one-second model pads the unused bins with zero. There is no learned window normalization. Prefix duration varies while windows have fixed time budgets, so this does not isolate a causal effect of a single feature change.

## Actual selection results

| Model | Correct / 14 | Macro-F1 | YouTube recall | Instagram recall |
| --- | --- | --- | --- | --- |
| Browser first-30-datagram control | 11 | 0.78462 | 6/7 | 5/7 |
| Capture first-30-packet control | 9 | 0.62567 | 6/7 | 3/7 |
| Browser one-second window | 9 | 0.64103 | 5/7 | 4/7 |
| Browser three-second window | 9 | 0.62567 | 6/7 | 3/7 |
| Training-majority YouTube control | 7 | 0.33333 | 7/7 | 0/7 |

All four fitted models classify their seventeen training connections correctly. That training result, coupled with much weaker later-visit selection, is consistent with overfitting; it is not evidence of generalization. Connections within visits are correlated and these few recordings cannot support a population accuracy claim.

The windows did observe extra traffic: ten of fourteen selection connections exceed their browser prefix at one second, and twelve at three seconds. Five receive additional datagrams between seconds one and three. Thus this failure is not explained by every window being an unchanged short prefix. Counts across different flow windows or nested horizons are not independent samples. This one fixed representation does not show that every possible longer-window approach fails. The protocol stops here rather than searching the same small selection set.

## Artifact verification and CPU measurements

The saved numeric window forests reload without pickle. Window prediction requires an explicit `browser_udp_socket` observer and matching horizon; the ordinary live Predictor rejects their inventory. Scores remain uncalibrated and `label` is null. Saved-model probabilities match scikit-learn across all 31 train/selection connections per model, with maximum absolute difference at most 1.12e-16. Source tests verify half-open windows, future-packet exclusion, histogram mass, feature-label independence, export parity and protected-input/observer/budget rejection.

The actual trained-model benchmark performs 50 warmups and 1,000 calls on the first retained selection connection on this laptop. These are inference-call measurements, not end-to-end latency and not a controlled explanation of speed differences between export implementations:

| Model | p50 ms | p95 ms |
| --- | --- | --- |
| Browser prefix | 8.134 | 10.603 |
| Capture prefix | 8.444 | 10.185 |
| One-second window | 1.106 | 1.747 |
| Three-second window | 1.056 | 1.868 |

A window decision still needs its one-/three-second observation budget, plus capture, queue and delivery time. These browser-recorded windows were computed offline. They do not measure native live window inference, browser event receipt, paint latency, transfer parity or packet loss.

Full Python verification after the run: **264 passed**, one existing Starlette/AnyIO deprecation warning. Ruff lint/format pass for 90 active source files. The preceding ten UI tests/build remain unchanged. An additional scoped audit-hook check loads query inputs first, then permits file access only to the two window bundles and its report, and blocks network operations. Both denial probes pass; each saved window model reproduces all 31 saved decisions with zero score difference. This is scoped Python evidence of standalone artifact inference, not an OS sandbox or live accuracy.

## Private artifacts and reproduction

All paths below are relative to `experiments/browser-adaptation/browser-windows-01/`, remain local/ignored and contain genuine-data-derived evidence:

| File | SHA-256 |
| --- | --- |
| `report.json` | `064a9210fc2a52ca2df6c016929c171b26668c7ce8bcccf224417d0cda0a61aa` |
| `protocol.json` | `7948e80a351169fd5d4fb98ea0a418b851927ac12102df8220b2f18285c6b6aa` |
| `window1000/window-model.json` | `ad914abd0aebb122ee590e8b5b07ab846d8c97ced2fe9109079ea6b3c0188307` |
| `window3000/window-model.json` | `151680a8cbb1b0c60e4b5773617d8cf655febc9af2622d858a0b66c860708d98` |
| `browser_prefix/metadata.json` | `0d59762b80b806c2cd7a37a6d13c4df7347c6bf16b8618078db52a2542f3d4ef` |
| `capture_prefix/metadata.json` | `d9e2064302daeb34ded79d7034bfd96bb304b78a3165c94a4983155512b2fa90` |
| `standalone-verification.json` | `3e880fe1695aabe2a0724245e58926d34361bb05ca81294c4c36a77f3c989aaf` |

The directory also contains checksums, train/selection feature records, per-model saved predictions and the private `verify_standalone.py` harness. That harness can be rerun from the project directory after preserving its existing output: it deliberately refuses overwriting `standalone-verification.json`. Browser logs are private and are not published. To reproduce with the existing legitimate legacy recordings, choose a new output path:

```powershell
.venv/Scripts/python.exe scripts/study_browser_windows.py --output experiments/browser-adaptation/browser-windows-repeat
.venv/Scripts/python.exe -m pytest -q
.venv/Scripts/python.exe -m ruff check src/netembed scripts tests
.venv/Scripts/python.exe -m ruff format --check src/netembed scripts tests
```

Do not rerun against protected or newer data, overwrite this evidence, tune on the original final test, or enable browser-trained artifacts in capture. The next scheduled evidence step remains [the frozen version-3 sequence](browser-development-v3.md): its Explore/profile training visit is allowed on 29 October or later at +05:30, followed by the remaining YouTube training control and later separate selection visits. That bounded cycle can still fail and is not a promise that more data will repair recognition.
