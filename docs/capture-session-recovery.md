# Interrupted recording diagnosis and bounded recovery

On 9 November locally, the first fixed-ten fresh visit was interrupted by a viewer disconnection and followed by a second Start. The old service retained only its latest session. The stopped log and current capture have now been preserved and processed as a diagnostic, never as a replacement fresh-evaluation visit.

## What the stopped log establishes

Session 45519e9b8ca442289f4ffda6f2a6d207 contains two retained connections, with thirty and twenty-seven packets. Browser-origin correlation maps one to YouTube and places the other outside the supported service set. The YouTube flow passes the existing unique-socket and per-direction packet-prefix QC; no eligible mapped flow was excluded. Thus the app captured packets: a connection row is not one packet. The separate frozen counter of 6,628 records packets arriving after retained early-prefix limits, not a full-stream recording. No reported drops or capture-process error occurred in the surviving session.

The verified YouTube connection's actual ten-packet top guess was YouTube, score 0.7804149003, with Spotify 0.1900837217 second. Its accepted label was null because policy_fitted=false. All seven native events from both connections reproduce with maximum alternative-score difference zero and no changed accepted labels. A single event had pipeline 2.904800 ms, queue 5.704000 ms, parser delay 99.359751 ms and capture-to-event 109.919548 ms. These are diagnostic event samples, not a latency bound, browser-paint timing or population accuracy.

Only one eligible target connection survived, below the frozen three-flow minimum. More importantly, the first Start's data was not archived before the second Start. These facts do not support a clean fresh-screen pass. The integrity-review marker remains active; original preparation/archival/scoring stays blocked. No threshold fitting, model training, replacement recording or new quality verdict occurred. The original viewer-close cause cannot be recovered from the former logs, which did not preserve a close code or distinguish heartbeat timeout.

Evidence directory: artifacts/local/ten-packet-fresh-v1/technical-interruption-45519e9b8ca442289f4ffda6f2a6d207.

Diagnostic report SHA-256: 0c9a58cd523d075567e55eb1fbe5e4df7434df03048e819c0fd8f51a4d8a4d8b.

Copied finalized NetLog: 48,892,005 bytes, SHA-256 663b621d1796d6c1dbfa8adf66e32761b6cf503e3b93dd8724e4a07c876ac585. The source and diagnostic copy match. The report binds all nine evidence files; an independent Node check found zero checksum mismatches. Native Chrome lifetime proof was recorded while Chrome remained open after logging stopped. The private write-once diagnostic runner is experiments/ten-packet-fresh-diagnostic-v1/diagnose_recording.py; its inputs and results remain private local artifacts, not benchmark training or final-test data.

## Implemented engineering changes

The service now keeps the last three stopped sessions in memory, including capture metadata, per-checkpoint predictions, timing samples and status. Each stop creates an independent deep snapshot before another Start can clear the current session. A fourth stopped session evicts the oldest; the status reports the eviction count. The buffer is bounded, contains the same metadata-only exports and is cleared when the service exits. It is not automatic disk recording, permanent archival or recovery of the already lost first session.

Read-only endpoints list and export these snapshots:

```text
GET /capture/recent-sessions
GET /capture/recent-sessions/{session_id}
```

An unavailable/evicted session returns404, never replacement data. After Stop, the UI offers Recent stopped recordings with connection/packet counts, stop reason and explicit downloads. A user download saves the capture/timing/status bundle locally. The UI also explains that each connection has its own chart and only the first thirty packets are retained; the classifier's separate ten-packet limit stays visible.

The server now distinguishes viewer heartbeat expiry from ordinary WebSocket closure and stores the close code, bounded reason and timestamp in active-session stop evidence. Heartbeat expiry closes with1008; disconnects and invalid large messages have separate reasons. The existing fifteen-second heartbeat limit and immediate cleanup on viewer disconnect are unchanged. No automatic reconnect-to-capture or automatic Start was added. These changes preserve evidence and improve future diagnosis; they do not establish why the original viewer disconnected or prove that browser/network interruptions have been eliminated.

The summary endpoint now uses the same Capture.summary implementation as saved snapshots. Fixture-model exports retain fixture=true, so constructed software records cannot masquerade as genuine traffic evidence. One older software fixture was updated to carry its explicit fixture provenance.

## Verification and current state

565 Python tests pass with two existing dependency warnings; 25 UI tests pass, production build succeeds, active Python lint and 155-file formatting pass. Tests verify immutable snapshots across later session resets, the three-session bound and eviction, duplicate-stop handling, retained timing and close reason, fixture propagation, read-only retrieval/404 and heartbeat-timeout cleanup. UI tests verify download controls without starting capture. These are constructed lifecycle tests, not fresh real-live recognition evidence.

The idle validation service was reloaded only after the latest session, stopped NetLog, browser proof, reference, socket QC and prediction audit were saved and checked. Its frozen model weights and unfitted policy are unchanged; capture is off. No new recording is requested by this engineering step. A future fresh-check continuation needs a separately explicit protocol; the interrupted one-attempt scope is not silently reset.

## Server-driven heartbeat repair, 9 November

The later Instagram visit in `ten-packet-fresh-continuation-v1` recorded an
explicit viewer heartbeat expiry. Its four verified target connections remain
usable for the fixed raw-model comparison, but that comparison's drop/receipt
gate does not establish uninterrupted viewer reliability. Its original status,
stop cause and archived files remain unchanged.

Code inspection found that viewer liveness depended on a three-second browser
interval timer, with a fifteen-second receive timeout at the server. Hidden-page
timer throttling is a plausible explanation, not a proven reconstruction of
this particular browser failure. See [Chrome's timer-throttling documentation](https://developer.chrome.com/blog/timer-throttling-in-chrome-88/).

The server now sends an application heartbeat every three seconds on the existing
WebSocket, independently of whether capture events are arriving. The page replies
directly in its message handler, before session filtering or animation-frame
rendering. The browser interval timer has been removed. Heartbeats do not create
prediction receipt samples or classify packets. Ownership remains single-viewer;
reconnection never starts capture. A genuinely frozen, suspended or disconnected
page can still miss the fifteen-second deadline; expiry still closes the socket,
stops capture, and retains the stopped-session evidence. Sleep is not supported
as uninterrupted capture.

Validation: 12 targeted API/recovery tests and all 27 UI tests passed; production
TypeScript/Vite build, Python lint, and UI formatting passed. Regression tests
exercise a timer-free viewer beyond the scaled receive deadline, cleanup and
ownership release, a nonresponding viewer despite outgoing server heartbeats,
and immediate UI replies with hidden document state and no timer advance.
An isolated real loopback WebSocket also stayed connected for 18.125 seconds,
answering six server heartbeats without a timer. It loaded no model and never
started capture. Its explicitly marked software-test report is
`artifacts/local/heartbeat-fix-v1/idle-smoke.json`.

The idle local service was restarted with the same frozen model after all three
visits and their comparison were archived. Capture remains off. Reload Edge once
to load the updated page. Native Edge background-window behavior under actual
traffic has not yet been validated for this repair; the software and loopback
checks are not a substitute for that evidence. Confidence calibration is also
still pending and the verification recordings cannot be used to fit it.
