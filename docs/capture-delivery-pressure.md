# Connection check and viewer delivery pressure

The requested background-browser check was capture-off. The server instead observed POST /capture/start200 and a full active session, so this is an unplanned engineering diagnostic, not the prescribed idle check or any prospective model-quality visit. No browser NetLog was requested for this check, and no per-flow service labels are assigned from the user's selected tab.

After the deliberate page refresh, the available server log contains no unexpected WebSocket close. Session 9ab3c233650e46dda671643db50848a5 ran 120.734 seconds and stopped at the capture duration limit, with viewer_close=null. This is one limited active-session connection observation; it does not establish that all disconnect causes are eliminated.

The stopped session contains 64 connections and 1,779 retained early packets. All 230 available 5/10/20/30 checkpoints were computed, including all 64 ten-packet checkpoints. The browser acknowledged226 events; four prediction receipts remain pending, with zero receipt-tracking evictions even in the later summary. The aggregate drop count is120. This points toward delivery pressure rather than absent packet ingestion or missing model computations. The former aggregate counter cannot identify which of those120 losses were packet updates versus predictions or inference queue events, so no exact historical breakdown is invented.

The new recovery buffer successfully retained the stopped capture, timing and status. A disk copy is saved under artifacts/local/connection-check-unplanned-9ab3c233650e46dda671643db50848a5. saved-session.json SHA-256: fc729af7b080d33ef3922bf332324da3edb87e12f70cade6012b39a694ff6dd8. diagnostic-report.json records the observation and limits; final-timing.json preserves the later four-pending receipt state. These files are diagnostic only, excluded from training, calibration and fresh evaluation. The interrupted three-service scope remains blocked.

## Implemented queue changes

One WebSocket and a capacity64 viewer queue remain. Each packet-display event contains the cumulative prefix for a connection. When a newer packet snapshot for the same connection is already pending, it replaces the older one without losing those packet values. This lossless supersession is counted as packet_updates_coalesced, not as a drop.

Under a full viewer queue, a prediction displaces a packet/status/window event before displacing another prediction. Actual discards remain counted, including prediction loss if the entire queue is saturated by predictions. New counters distinguish inference_queue_drops from viewer_event_drops by event type; the original aggregate drops counter remains. A packet update rejected because prediction capacity is full still counts as a real drop. No zero-loss guarantee or unbounded buffering is introduced.

Prediction events now also carry their actual observed-prefix packet metadata. The UI can therefore show the real packet view associated with a delivered model checkpoint even when a separate packet-display update was dropped. It merges cumulative metadata by longest observed prefix so a delayed shorter update cannot shrink the chart. The model still uses exactly its declared first10 packets; the added transport metadata is not a new model feature or future-packet input. Exported prediction scores and packet units remain unchanged. No weights, normalizer, labels or decision policy were fitted or changed.

## Verification and remaining evidence

569 Python tests pass with two existing dependency warnings; 26 UI tests and the production build pass. Active lint, 156-file Python formatting and UI formatting pass. Constructed tests cover full-prefix snapshot supersession, independent 5/10/20/30 checkpoint ordering, prediction priority, honest overflow counters, waiter timeout/reuse and delayed-packet UI behavior. These are software burst tests, not a new genuine live capture result.

The code change has not yet demonstrated a reduction from120 real drops to zero. A future controlled user-started engineering capture is needed to measure actual viewer drops and receipt completeness with this queue; it must not be called fresh classification evaluation without its own role/reference contract. No additional recording was started by the agent or requested during this implementation. The current capture is stopped and its evidence was preserved before reloading the validation service.

Follow-up: the [single controlled delivery check](delivery-check-v1.md) subsequently delivered223/223 native events with zero reported drops, zero pending receipts and no disconnect. That result supersedes the pending-delivery-measurement status above; its workload was not a matched experiment and it does not establish classifier accuracy or a universal zero-loss guarantee.
