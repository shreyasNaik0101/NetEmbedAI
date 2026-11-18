# Live policy results — 6 November 2026

The two declared user-started visits passed the fixed descriptive live screen. Both were archived as usable: five YouTube and six Instagram IPv6 connections verified against Chrome NetLog. This is a small same-hotspot check, not population accuracy.

At the primary ten-packet checkpoint:

| Service | Eligible | Emitted | Accepted | Wrong accepted | Missing |
|---|---:|---:|---:|---:|---:|
| YouTube | 5 | 3 | 3 | 0 | 2 |
| Instagram | 6 | 6 | 5 | 0 | 0 |

Instagram had one refusal. Overall end-to-end coverage was 8/11 (72.7%). All nine emitted raw top choices were correct. Missing live checkpoints remain missing; replay is not substituted. Both predefined per-service coverage/error checks passed.

Later prefixes remain a limitation: at 20 packets, only 1/6 Instagram connections was accepted; at 30 packets, none of the three eligible Instagram connections was accepted. Raw top choices were correct, but the unchanged confidence threshold withheld labels. No threshold or model was adjusted from these results.

There were 109 YouTube-visit and 165 Instagram-visit prediction events, including background traffic. All had browser receipts. Reported drops and receipt eviction/pending counts were zero. Coalescing counts were 16 and 19; missing intermediate checkpoints remain visible.

| Visit | Pipeline median / p95 | Packet-to-browser-receipt median / p95 |
|---|---|---|
| YouTube | 2.21 / 4.65 ms | 172.87 / 495.59 ms |
| Instagram | 2.49 / 4.05 ms | 149.43 / 832.05 ms |

These are same-host event measurements, not browser paint or time from starting a connection. Capture/parser delay dominates model pipeline time. No hard real-time guarantee is established.

Both archives reproduced their saved source predictions. An independent JavaScript recount confirmed the primary decision counts. The initial viewer connection failure required an idle server restart; three reconnection checks passed afterward. This recovery is a remaining operational limitation, not evidence of uninterrupted reliability.

Private evidence: artifacts/local/ipv6-live-policy-v1/live-policy-report.json
Report SHA-256: 453a04e7bf140e11285aa11c818d3bc91454788b458474c8bf1d061ec74aa9e8
Prediction SHA-256: a4553c1005402722484c6ec8d36e33ee975a5c06efafe89202b162e13a78d95f
Artifact: 9878d0818370ede3e9897a9cc654b4ddc0afcd87d41b2d7134ccaf52592b528a

The frozen protocol is [documented here](ipv6-live-policy-check.md). Both visits are complete; no additional recordings or policy fitting are part of this scope. The normal startup default has not been promoted. Next engineering work should address viewer recovery and skipped prefix delivery, preserving these results as the original measurement.

## Engineering follow-up

After sealing these results, the inference queue was changed from one pending item per flow to one per (flow, prefix). Its total capacity remains 64; overflow still evicts the oldest item and increments drops. A deterministic burst test checks all four prefixes and a capacity-two overload. These software fixtures are not new live evidence.

The UI now offers a manual Reconnect button after a lost connection and detaches old socket callbacks. Reconnection does not start capture. The original server rejection cause remains unresolved; this control does not prove it cannot recur.

Validation: 470 Python tests passed (two dependency warnings), 20 UI tests passed, TypeScript/Vite production build passed. Models, threshold and archived reports were unchanged. No new recordings requested.
