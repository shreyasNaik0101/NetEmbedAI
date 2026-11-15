# Engineering work independent of new recordings — 28 October 2026

Source commit `18b8650` closes several independent software/measurement gaps.
No new capture, browser logging, data-role change, model training, threshold
tuning or default promotion is part of this work. B17 remains unchanged.

## Stop evidence and session timing

Once Stop has completed, later viewer disconnect, shutdown or repeated Stop
returns the preserved stopped state. It does not replace a duration-limit stop
with a new reason or emit a second terminal event. Process/task/flow cleanup
still occurs on the first Stop. Tests cover the previously observed reason
overwrite and new-session reset of timing records.

Prediction and descriptive observation updates now have separate receipt
channels. The browser acknowledges both in its WebSocket message handler,
before requesting an animation frame. Acknowledgements bind session, event type
and integer sequence; stale-session, duplicate, malformed and invalid-clock
messages do not contribute or consume valid pending evidence.

`/capture/summary` preserves the old prediction timing fields and adds:

- `observation_emit_to_browser_receipt_ms`, `observation_receipt_n`,
  `observation_receipt_p50_ms`, `observation_receipt_p95_ms`;
- `receipt_tracking_pending` and `receipt_tracking_evicted`, by event type;
- an explicit description of the timing anchors.

Prediction receipt starts at the checkpoint packet timestamp. Observation
receipt starts at server emission and therefore excludes its one-/three-second
observation wait and prior parsing. Neither measures browser paint. Both use
wall clocks on the same local host and reject negative or over-ten-minute
samples. Each channel retains at most 64 pending acknowledgements and 1,000
accepted samples; summaries are bounded retained samples, not a loss-free or
complete-session latency distribution. Pending/evicted observations must be
considered when interpreting them. Invalid-clock rejection is not clock
synchronization. Historical exports are unchanged and gain no retrospective
timing evidence.

The UI fetches the stopped session's summary after automatic Stop as well as
manual Stop. A delayed old-session response cannot overwrite the next session.
Window metadata remains descriptive and never creates a model prediction.

## Native offline window checks and bounded extraction

The new [constructed fixture](../tests/fixtures/README.md#longer-window-regression-fixture)
contains four interleaved IPv4/IPv6 flows with variable link/IP headers and
66 datagrams each. Only public RFC 9001 vectors and documentation addresses are
used. No packets are sent. A separate construction oracle checks all window
counts, bytes, moments, directional switches and histogram bins against actual
TShark and the shared live flow builder. Each flow has 61/64 datagrams before
one/three seconds, while model input freezes at thirty. Exact boundary packets
are excluded; early EOF remains partial. Both reference-check settings pass.

`capture-file --observation-windows` exposes this same offline path. Timestamps
come from the file, never a fabricated live clock. A ten-second deadline now
covers reading stdout as well as process exit; a stalled reader is killed,
joined and its pipe closed. A no-interface mock regression verifies this cleanup.
Native tests explicitly skip when TShark is missing; they ran on this host.
Fixture parity does not establish parity on a real local trace or service
accuracy. The generic extraction JSON must retain its constructed provenance
when used as evidence.

```powershell
.venv/Scripts/python.exe -m scripts.build_window_fixture --output artifacts/local/windows-copy.pcap
.venv/Scripts/python.exe -m netembed.cli capture-file --pcap artifacts/local/windows-copy.pcap --output artifacts/local/windows-copy.json --observation-windows
.venv/Scripts/python.exe -m pytest tests/test_window_pcap.py tests/test_delivery.py tests/test_capture.py tests/test_offline.py -q
```

Fixture SHA-256:
`0e650ab918445e577608cb603b49cbddc071f98b0b5dc920695193528d22afa0`.
The actual CLI extraction is saved privately at
`artifacts/local/window-fixture-offline-20261028.json`; it is constructed-data
software evidence and has no training/calibration/test role.

## Real-artifact CPU timing stages

The new helper measures preprocessing (validation, saved normalization, padding
and tensor views), the actual TCN forward, probability conversion and the full
unchanged predictor separately. It checks prepared-path probability parity
before timing, requires a legitimate trained artifact and refuses a fixture
performance report. The module forward includes the existing embedding/head
work performed by the predictor. Temperature/softmax uses fixed saved logits
in its isolated stage. Stage percentiles are not additive.

```powershell
.venv/Scripts/python.exe scripts/benchmark_stages.py --bundle experiments/full-real/20261024-151720-3532794c/bundle --flow experiments/full-real/benchmark-flow.json --output experiments/browser-adaptation/cpu-stages-repeat.json --threads 2
```

Use a fresh output filename. The benchmark performs 50 warmups and 1,000 calls
per stage sequentially on the same existing recorded nineteen-packet input.
It excludes model loading, API validation/serialization, HTTP, observation time,
capture and browser delivery/paint. Host load affects these CPU measurements;
this cannot establish a causal speed improvement over an earlier run.

Actual B17 results on this i7-1360P Windows host (sixteen logical CPUs, two
Torch threads), in milliseconds:

| Stage | p50 | p95 |
| --- | --- | --- |
| Preprocessing | 0.449 | 1.367 |
| Model forward | 15.731 | 18.885 |
| Probability conversion | 0.091 | 0.170 |
| Full predictor | 16.258 | 19.467 |

Prepared and shared-predictor probabilities match exactly. Input SHA-256 is
`ad7ac5a843a1de53d95f743b606def07110e2245ad8d70ebabf025054a644ed3`.
No quality evaluation or final-test reading was done for this benchmark.

## Completed verification and local service

**295 Python tests pass**, including all native offline window checks on this
host, with one existing Starlette/AnyIO deprecation warning. **Thirteen UI tests**,
TypeScript/production build, Prettier and Ruff lint/format for 96 active Python
files pass. Hosted CI was not triggered or claimed. The full Python suite ran
after the CPU benchmark ended; no benchmark ran alongside it.

Before restarting the stopped service, the retained prefixes and window records
were compared to the previously bound genuine archive and matched. The original
archive's hashes are unchanged. Additional stopped responses are preserved
privately; their stop reason is historical evidence and is not rewritten to
pretend the fix had already been present.

The updated service is ready at `http://127.0.0.1:8001`, serving the verified new
production assets with the same B17 identity:
`18c43fe12262b81d4a3001df150a278865f3908ddd3aab934822fc0c9e5750fb`.
Actual HTTP/direct predictions at 5/10/20/30 packets from a retained genuine
recording match exactly, including decisions and alternatives. Original B17
evaluation binding is preserved. Capture, reference checks and optional windows
are off; no capture interface was opened. Refresh the app next time it is used
so the browser and updated acknowledgement handler match. An idle zero-sample
summary is a readiness check, not measured live window latency or visual proof.

Private report paths below are relative to
`experiments/browser-adaptation/engineering-20261028/`:

| File | SHA-256 |
| --- | --- |
| `cpu-stages.json` | `fbedd64abe403b9268eabf891899cc2e85f8ecebb8bd3bf48b049bfee47e679d` |
| `service-verification.json` | `06b0fe05542acfb3df568fee436b3cea1d0f36061d57ea5c71284338ac8a1839` |
| `pre-restart-verification.json` | `9486e8ddfbfec0d5812b707e33e458e4310ba16238401c307c1a4a9c4205159c` |

The constructed CLI extraction at
`artifacts/local/window-fixture-offline-20261028.json` has SHA-256
`d4fdb0ad9ad48f9cafbb0457536c81ef3844658e91d8c299a806fd429441f12f`.
Service stdout/stderr are `service.out.log` and `service.err.log` in the private
report directory. No data, artifacts or commits were pushed/published.

```powershell
.venv/Scripts/python.exe -m pytest -q
.venv/Scripts/python.exe -m ruff check src/netembed scripts tests
.venv/Scripts/python.exe -m ruff format --check src/netembed scripts tests
npm --prefix ui test
npm --prefix ui run build
npm --prefix ui run format:check
```

The [acceptance audit](release-checklist.md) separates these completed tasks
from remaining local-quality, genuine window delivery/paint, full local parity,
hosted CI and platform evidence. The frozen prospective recordings and all
protected calibration/final roles are unchanged.
