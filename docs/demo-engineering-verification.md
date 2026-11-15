# Demo engineering verification — 6 November 2026

Completed in order: bounded viewer expiry/exclusive ownership, confidence explanation, scoped model decision, current setup/demo/interview documentation. The default decision and measured model limitations are in demo-model-decision.md and ipv6-live-policy-results.md.

The server reserves viewer ownership before awaiting its handshake; a failed handshake releases it. A viewer that sends no message for 15 seconds is closed and capture cleanup runs before ownership is released. The browser sends a heartbeat every three seconds, clears its timer and callbacks on replacement/unmount, and offers manual reconnection. Reconnect never starts capture. A backgrounded or suspended viewer can expire; the demo should keep it foreground. The original rejection was not conclusively diagnosed, so this is tested hardening rather than proof of its historical cause.

Validation: 472 Python tests passed with two existing dependency warnings; 21 UI tests passed; Ruff lint and TypeScript/Vite production build passed. One existing display-row test timed out on the initial concurrent run; the unmodified rerun passed. Backend tests cover idle viewer expiry, subsequent ownership and second-viewer rejection. Browser tests cover heartbeat timer cleanup and explicit reconnect without capture. Three actual localhost WebSocket reconnect checks passed after service restart, with capture false and no session throughout.

Earlier burst/overload tests verify separate queued prefixes. No new live capture was started for engineering checks. The completed two-visit report remains unchanged with its original missing checkpoints. This is not a new accuracy/latency evaluation of the updated queue.

Verified SHA-256 values:

- artifacts/local/NetEmbedAI-ipv6-public-policy-v1.zip: 82b6fc9f388602d96e0d11162c67476f5b83d1ded63fe06323ad45c3fcc2cd1f
- artifacts/local/NetEmbedAI-v2-default-B17.zip: f9ca92fd82ea3cbc4254238b68993027e3a12715aa02f6ff9d1107bd21abd746
- artifacts/local/ipv6-live-policy-v1/live-policy-report.json: 453a04e7bf140e11285aa11c818d3bc91454788b458474c8bf1d061ec74aa9e8

The app is served locally on port 8002 with the explicitly selected forest profile. No publish, push, merge, cloud spending or default-model promotion was performed. The user's modified legacy notebook was preserved.
