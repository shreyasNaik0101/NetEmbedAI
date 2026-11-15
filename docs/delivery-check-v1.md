# Controlled delivery check: passed once

This is engineering evidence from a genuine user-started local capture, not a service-classification accuracy test. The one-attempt intent was saved before capture under artifacts/local/delivery-check-v1/intent.json, with the frozen model identity, interface/settings, no-drop/completeness rules and a minimum twenty events for the burst screen. No NetLog or per-flow service labels were collected. Selected YouTube activity cannot label every connection.

Session bf52ecad768e46b1a5692b2e3a610874 ran110.600 seconds and stopped by the user, within the120-second cap. Edge was visibly connected with capture off before Start. The available server-log interval has one Start, one Stop and no viewer disconnect during capture. The recovery buffer reports one new stopped session and no history eviction.

| Delivery measure | Result |
|---|---:|
| Retained connections | 61 |
| Retained early packets | 1,708 |
| Available / computed checkpoint events | 223 / 223 |
| Browser acknowledgements | 223 |
| Missing checkpoints / pending receipts | 0 / 0 |
| Reported drops / inference-queue drops | 0 / 0 |
| Viewer packet/prediction/status/window drops | All0 |
| Receipt-tracking / retained-evidence eviction | 0 / 0 |
| Cumulative packet snapshots superseded | 1,296 |

All ten predeclared engineering gates pass. Of the223 events,61 are five-packet insufficient-evidence responses with no scores. The other162 contain model scores using exactly the first ten packets, including repeated ten-packet scores at later observed checkpoints. These are not223 accepted classifications; every accepted label is withheld by the unfitted policy. Superseded packet-display events were cumulative snapshots of the same connection, so their packet values remain in newer snapshots; they are separate from actual drops.

## Measured latency

| Timing basis | Samples | Median | p95 |
|---|---:|---:|---:|
| Scored-event model pipeline | 162 | 4.487 ms | 7.284 ms |
| Scored-event queue | 162 | 5.656 ms | 23.683 ms |
| Scored-event capture → parser | 162 | 86.661 ms | 451.747 ms |
| Scored-event capture → event | 162 | 110.157 ms | 470.025 ms |
| All checkpoint events capture → browser receipt | 223 | 139.582 ms | 466.735 ms |

Scored-event and all-event percentiles use different cohorts and should not be ordered as though paired. Capture-to-receipt starts at the checkpoint packet, not connection start; it excludes waiting for ten packets and does not measure browser paint. Same-host clocks and one run cannot establish a hard timing bound.

The earlier unplanned run had64 connections/230 native events,120 aggregate drops and226 receipts. This run had61/223 and no losses. That is a useful descriptive improvement at similar event counts, but workloads were not matched or randomized. No universal zero-loss guarantee or isolated causal performance claim follows. Neither run supplies browser-verified labels for all flows or calibrated classification evidence.

## Saved evidence

Root: artifacts/local/delivery-check-v1. Artifact fa1f4837e4ae11c9169258ecb20338ae3c0c81c2d206231fb6fe19405b8d8549; weights and unfitted policy unchanged. Adapter tshark-prefix-ns-v3, Wi-Fi9, reference ON, longer windows OFF. Capture mode and timestamps match the intent; source is user_started_capture and fixture=false.

| File | SHA-256 |
|---|---|
| intent.json | 09ddb40b59d732ae8a439203797843bf7dcff95f3ee99e8da706dac04654af6b |
| baseline-status.json | aef9d3d7fa85b18cc42314ce07df1295dd492a7ef329ec7284830cf8e4c9d89a |
| saved-session.json | 7d44ba6c636ecd76919d40a84051cd78c7815137a08d7d2ad45d582c580a87eb |
| final-summary.json | 967b81351c98015897c274ce7142f2d3b1d77820719006238386778ff3bdb392 |
| delivery-report.json | cd17689d2b7070c2019748355c224f0a0e9db2131929c290ffed4bd4beab105f |

The private write-once audit runner uses only saved engineering inputs:

```powershell
.\.venv\Scripts\python.exe experiments/delivery-check-v1/check_result.py
```

It checks identity, timestamps, settings and completeness, and preserves existing results. An independent JavaScript recount checked223 events,162 scored events,223 receipts, timing percentiles, loss counters and all four input hashes with zero mismatches; independent-check.json is beside the report.

No production code changed in this evidence-only step; the preceding569 Python tests,27 UI tests and successful build remain the software checkpoint. This real result adds delivery evidence beyond constructed queue tests. The interrupted three-service fresh scope remains blocked. New model evidence still needs a separately fixed fresh service-verification protocol, separate calibration and later accepted-prediction checks. This delivery check does not reset those roles or prove recognition quality.
