# A five-minute honest demo

1. Run scripts/serve_live_policy.py from the project with the existing virtual environment; open http://127.0.0.1:8002 in one Edge tab. This is the explicit forest demo profile. Keep the viewer foreground.
2. Confirm the model identity, Stream connected and your actual network interface. Reference checking is optional and separate from prediction. Leave longer windows off for the prefix demo.
3. Explain the three inputs: sizes, directions, time gaps. Press Start yourself, then open a new supported service connection in Chrome. Show arriving packets, prefix length, alternatives and the current decision.
4. Explain an uncertain result honestly. A top choice can stay correct while falling below the threshold; later packets can reduce confidence. Do not claim that reference labels are model predictions.
5. Press Stop. Show measured event latency and the saved evaluation report. You do not need to start another research recording or Chrome NetLog for an ordinary demonstration.

## Recovery

If the stream disconnects, capture stops. Close duplicate viewer tabs, allow up to 15 seconds for an unresponsive owner's heartbeat to expire, then click Reconnect. This never starts capture automatically. If the server itself is unavailable, restart the launcher and reconnect. Preserve any unsaved evidence before restarting a service. Existing archived reports stay on disk.

An idle viewer sends a heartbeat every three seconds. A suspended laptop or heavily throttled background tab may lose its connection; keep the demo page foreground. This is deliberate bounded cleanup, not uninterrupted-session support.

## Explain the result

The historical TCN benchmark and local forest demo are different evaluation settings. In the latest two live visits, eight of eleven ten-packet cases received labels, all eight correct. One was refused and two intermediate checkpoints were missing. The queue fix was subsequently software-tested; do not rewrite the original result as eleven delivered predictions.

Measured capture-to-browser receipt medians were about 173 ms and 149 ms; p95 values were about 496 ms and 832 ms. Model pipeline medians were about 2.2–2.5 ms. Browser receipt is not paint, and these are measured observations, not timing guarantees.

## Interview explanation

“I built a local encrypted-traffic classifier using metadata rather than decrypted content. I compared a compact temporal network with classical methods, packaged preprocessing with weights, and kept chronological benchmark evaluation separate from local capture. Local domain shift required better representative training data. A frozen forest then passed small prospective YouTube/Instagram checks, with explicit abstention and measured delivery latency. It remains a scoped prototype, not a universal traffic detector.”

[Full beginner guide](interview-guide.md) · [Model choice and checksums](demo-model-decision.md) · [Measured live results](ipv6-live-policy-results.md)

## Reload during capture

A page reload can overlap the prior viewer’s capture-process cleanup. The new viewer may be temporarily rejected while that cleanup holds ownership. The UI now retries at 0.5, 1, 2, 4 and 8 seconds, then offers manual Reconnect. It never restarts capture. Close duplicate viewer tabs if retries exhaust. A new successful status exchange resets the failure budget.
