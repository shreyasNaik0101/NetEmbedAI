# Architecture and contracts

A training process prepares and fits artifacts. The running service only reads a configured bundle. It never fits statistics, downloads data, trains on startup or starts capture on startup.

~~~mermaid
flowchart LR
  A[CESNET local export] --> B[Chronological manifests]
  B --> C[Train and development comparison]
  C --> D[Checksummed bundle]
  D --> E[Shared predictor]
  F[User starts TShark] --> G[Bounded bidirectional flow table]
  G --> E
  H[Explicit recorded replay] --> E
  E --> I[Decision policy]
  I --> J[FastAPI and one WebSocket]
  J --> K[Live / Replay screen]
~~~

## Feature schema 1

JSON packets contain iat_ms (finite, nonnegative), direction (+1 client→server, -1 reverse) and payload_bytes (integer 1..65527). The first interval is zero. Accept 1..30 observed packets; reject overlength API requests rather than silently truncating. The data exporter explicitly records when longer JSON source sequences are truncated. Padding is an internal all-zero representation, never an accepted packet.

Log1p applies to intervals and sizes. Mean and population standard deviation are fit on valid training packets only, with a minimum standard deviation of 1e-6. Saved statistics are used in every inference path; padding is re-zeroed. The causal TCN gathers length-1. Changing later values or padding must not change an earlier prediction. The forest uses prefix-only counts and directional size/gap summaries.

## Bundle boundary

metadata.json contains schema/architecture, ordered labels, normalizer, policy, library versions, training seeds/configuration, data fingerprints and provenance. weights.pt uses weights-only Torch loading; forest.json contains numeric trees. checksums.json binds both metadata and model file. A software fixture is rejected unless an internal test explicitly allows it, and capture always rejects fixture models. Historical weights are incompatible with the v2 readout.

Only trusted locally generated resume.pt checkpoints use full Torch checkpoint loading, explicitly through the training CLI. Never resume a checkpoint from an untrusted source. API requests cannot select files or models.

## Capture semantics

A fixed UDP/443 filter narrows candidates. TShark protocol evidence establishes QUIC eligibility. New tuple flows require a client Initial directed to port 443 (QUIC v1 or v2); unsupported protocols, missing beginnings, fragmentation, truncation and out-of-order timestamps are skipped with counters. A supported version is not evidence the service is in the trained label set.

Group the unordered IP/port endpoint pair; the client Initial defines +1. Keep at most 256 active flows, expire after 65 seconds of inactivity on the next ingestion, and freeze each first window at 30 packets. Adapter `tshark-prefix-ns-v3` corrects the former 30-second idle timeout to the [CESNET collection's 65-second setting](https://pmc.ncbi.nlm.nih.gov/articles/PMC9851865/). Tuple reuse within the idle interval and connection migration can confuse grouping; no connection-ID migration model is claimed. IPv6 extension fragmentation is rejected. Packet lengths come from UDP length minus eight bytes. RFC fixtures and one unknown-origin recording prefix independently match ipfixprobe; neither proves local classification quality. The Instagram socket follow-up matches sent and received payload-size sequences within direction. Browser userspace clocks produce merged-order differences and do not establish on-wire timing/order or complete local exporter parity.

Ingestion and inference are separate async tasks. At checkpoints 5/10/20/30, enqueue a snapshot. At most 64 jobs are pending; newer prefixes coalesce by flow and overload drops the oldest pending flow. Each viewer queue holds 64 events, dropping oldest on overflow. UI keeps at most 256 rows. Stderr is drained into eight bounded lines; raw payloads are not persisted. Session summaries retain at most 1,000 timing observations and no endpoint identities.

Exactly one connected viewer owns a capture session. Start rejects duplicates and invalid interfaces. Stop is idempotent, terminates the TShark process tree on Windows, joins tasks, clears pending state and ends ingestion. After cleanup, repeated Stop/disconnect/shutdown preserves the original terminal reason and evidence. Disconnect stops an active session; a lease also guards abandoned sessions. Duration is bounded. This is a local, single-user service; multi-worker deployment is unsupported.

An explicit `reference_check=true` Start option enables an independent evaluation
side channel. Only then are TShark SNI and ECH/ESNI reference fields requested.
The checksum-verified CESNET service map produces a conservative reference label;
the observed hostname is discarded. Reference data never enters `Flow`, saved
preprocessing or `Predictor.predict`, and `/predict` rejects reference fields.
Conflicting, encrypted and absent names stay unverified. The UI shows the
reference separately and can export up to 256 ephemeral flow windows with four
model checkpoints each through `/capture/local-evaluation`. Exports omit raw
hostnames, endpoints and payloads; evictions are counted, and the next Start or
service exit clears the retained diagnostic history. This is map agreement,
not guaranteed app ground truth. See [local testing](local-testing.md).

Fresh opted-in exports also carry a per-session HMAC key and connection-pair
pseudonyms plus first-packet timestamps. The offline `attribute-netlog` command
uses them to correlate Chromium QUIC session origins with received packet sizes
and times. It reads event enums and clock conversion from the supplied browser
log; exact tuple tokens, a fixed start-time gate and two distinct receive matches
are required. Ambiguous, migrated, incomplete and clock-incompatible sessions
stay unverified. Raw browser origins, endpoints and matching keys are omitted
from the reference report; all model predictions are preserved. This code is
outside the predictor and does not start capture or browser logging. Old exports
without connection metadata cannot be retroactively attributed. Details and
limits are in [browser attribution](browser-attribution.md).

## API and timing

Receipt acknowledgements require session ID, event type, sequence and a finite
bounded receipt timestamp. Prediction timing starts at the checkpoint packet;
descriptive window timing starts at server emission. Each channel independently
retains at most 64 pending/1,000 accepted samples, with pending/eviction counters.
The UI acknowledges on receipt before rendering and loads summaries after any
completed Stop. Wrong/stale/duplicate acknowledgements cannot create samples.
These are same-host wall-clock measurements, not paint or hard timing guarantees.
See the [engineering evidence and stage boundaries](engineering-checks-20261028.md).

GET /health/live, /health/ready, /model, /evaluation, /examples; POST /predict and /predict-batch. Capture routes are /capture/interfaces, /capture/status, /capture/start, /capture/stop, /capture/summary and WS /capture/events. Single requests cap at 30 packets, batches at 32 flows and HTTP bodies at 256 KiB. Origins and Host headers are restricted to local defaults.

Events carry schema/session/sequence/ephemeral flow IDs. Timings distinguish observation-window duration, capture→parser (wall clocks on one host), queue delay (monotonic), prediction pipeline, capture→event and browser receipt acknowledgement. Negative or clock-adjusted capture delays require interpretation; they are not hard real-time guarantees. The CLI measures full prediction pipeline and batch probability throughput; a separate loopback HTTP helper measures request round trips. Neither includes real capture or browser receipt. Three user-started sessions measured capture→event latency. The first two used animation-frame acknowledgment, which was delayed when Edge was in the background and cannot establish browser receipt or paint time. The third used the corrected WebSocket-handler timestamp: capture→browser receipt was 403.21/543.99 ms p50/p95 over 33 acknowledged events. Paint time remains unmeasured.
