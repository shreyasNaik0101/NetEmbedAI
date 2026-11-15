# Mobile hotspot: bounded IPv6 acquisition feasibility

**Actual outcome: real YouTube IPv6 QUIC was observed on two verified connections,
but the first visit fails the declared three-connection support minimum.** Both
connections reach30 packets and pass the packet checks. The scope stops with no
replacement or Instagram intent. The one-video instruction does not guarantee
three new connections; this is a collection sample-count shortfall, not a user
recording error or evidence that hotspot IPv6 capture is impossible.
The declaration/instructions below are historical and are not a request to
record another visit under this closed scope.

On4 November2026 the user connected the laptop to their phone hotspot. The
read-only check at12:30:48UTC found two candidate global IPv6 addresses, one
IPv6 default route and successful TCP443 connections to YouTube over both
IPv4 and IPv6. Explicit DNS and the normal resolver both returned IPv6 records.
This supports trying a real capture; it does not establish QUIC/UDP behavior,
model accuracy or equivalence to the previous institutional Wi-Fi network.

Private connectivity report: `experiments/mobile-hotspot-ipv6-check-v1/report.json`,
SHA-256 `6fda779a5cb7273747ad81a02d570919bbcf28e5d678cc5f34b7484ee06fdce8`.
The earlier unavailable-IPv6 network and stopped campus collection remain intact.
No routing, adapter, DNS or browser family setting was changed by the assistant.

## Two visits only

This is a new explicitly labelled **user-declared mobile hotspot** scope,
`configs/hotspot-family-feasibility-v1.json`, canonical SHA-256
`8742c0a5b24be8edf9912428689dcdfc4a332e96d3c1d2fe1f5e7587a4f01a70`.
It does not reuse or replace a failed campus attempt. Network identity is
provenance, not a classifier feature. No client addresses or SSID are required.

1. `hotspot-train-yt-01`: a fresh YouTube video for60 seconds.
2. Only after slot1 archives successfully, prepare `hotspot-train-ig-01`: feed
   scrolling30 seconds and different Reels30 seconds, on the same local date.

Exactly one stopped attempt per slot. Each must pass the existing independent
reference/socket/native-source-replay checks and contain at least three mapped
target IPv6 flows at10 packets, with at least one reaching30. Keep all eligible
mapped flows and inventory exclusions. Family comes from matched socket endpoints,
not payload size or classifier output. A coverage/QC failure stops this scope;
processing failures preserve the same capture for continuation. No extra visits,
network-forcing tweaks or threshold changes are requested automatically.

The successful pair establishes acquisition feasibility only. It produces no
training freeze, candidate scoring, fitted model, confidence policy, performance
claim or automatic promotion. Future training use requires a separately bound
declaration and independent evaluation. Old data roles stay unchanged. Different
network/CDN/path/session conditions prevent treating hotspot-versus-campus results
as a controlled causal comparison of IP families.

## Prepared first visit

The first intent was prepared at `2026-11-04T12:35:11.243494+00:00`. It binds the
network-report hash, scope, role, plan, interface9, source B17 and adapter version.
Prior stopped session `a9cc7e568e03482981f398764fecdfcd` is excluded and preserved.
Preparation never starts capture. Stay connected to the phone hotspot throughout.

Open Chrome `chrome://net-export/`, keep Strip private information, and start
logging to `hotspot-train-yt-01-netlog.json`. In the Edge app choose Wi-Fi,
Reference evidence ON, longer windows OFF, then Start. Navigate to a fresh
YouTube video for60 seconds. Stop the app and immediately stop Chrome logging.
The usual log-save folder is acceptable: a stable closed log can be copied
byte-identically with a hash/path sidecar, without repeating capture.

Collector commands from the repository directory:

```powershell
.venv/Scripts/python.exe scripts/paired_capture.py --plan configs/hotspot-family-feasibility-v1.json --root artifacts/local/hotspot-family-feasibility-v1 status
.venv/Scripts/python.exe scripts/paired_capture.py --plan configs/hotspot-family-feasibility-v1.json --root artifacts/local/hotspot-family-feasibility-v1 archive hotspot-train-yt-01
```

No second intent is prepared until the first attempt passes. The collector
rejects generic model scoring, blocks training freeze for this scope and ends
with `feasibility_complete_no_scoring` after a successful pair. A changed
connectivity proof blocks preparation before any service request. Existing
campus archives cannot be enrolled as hotspot slots. The network label is
user-declared; the point-in-time probe does not prove the physical network
remained unchanged later. The actual capture's IPv6 acquisition is checked anew.

## Verification and limits

Implementation commit `a8f537f`.406 Python tests pass, with two known dependency
deprecation warnings, in52.30s. Ruff lint/format pass for125 files. New fixtures
verify two-slot completion without scoring/freeze, cross-plan rejection and
network-proof integrity; existing family, capture and calibration contracts pass.
These fixtures are not live evidence. UI code is unchanged from the prior
seventeen-test/build checkpoint. No hosted CI or other OS result is claimed.
The private `engineering-checkpoint.json` binds the plan, intent, network proof
and software checkpoint. No capture was started, and B17 remains the app model.

## First actual user-started visit

Session `94895a1f0d79402681ca92ccfff570c1` is stopped, with reference ON, Wi-Fi9,
zero queue drops/reordered packets and no recorded capture error. Two retained
browser-matched YouTube connections reach30 packets, each has a unique UDP socket,
and both directions have zero missing browser-prefix packets and zero ordered
payload-size mismatches. Other references remain inventoried:12 outside-supported,
6 ambiguous,1 unverifiable session,2 unmapped and3 unmatched connections.
The native-source replay comparison covers80 saved predictions, with zero
changed decision labels and maximum alternative-score difference0.0. This is
pipeline consistency, not a model-accuracy measurement.

The archive's generic target support gate runs before its family gate. It
therefore stops at2/3 ten-packet target connections and does not emit the normal
family sidecar. A subsequent read-only diagnostic applies the same endpoint-token
family matcher to those two QC-passed rows: both sockets are IPv6. It writes
`hotspot-train-yt-01-family-diagnostic.json` outside the original receipt's file
inventory and binds that receipt's hash. This does not rewrite the stop, relax
support, enroll failed data, enable scoring or prepare slot2. It establishes
that actual IPv6 QUIC acquisition worked on the recorded pair. Correlated flows
from one visit do not establish statistical reliability or useful training volume.

The stable completed Chrome log was found in the usual prior folder and copied
byte-identically:38,797,083 bytes, SHA-256
`c95e8479f1598d83a3e08118540fc7ddf875934147fd1f3ecf78fce8f81b9965`.
The source/path/hash sidecar is bound in the archive. No replacement capture
was requested for the file location.

Evidence root: `artifacts/local/hotspot-family-feasibility-v1/`.

| Evidence | SHA-256 |
| --- | --- |
| `hotspot-train-yt-01-archive.json` | `e05382c5c480b4721dfd591ff64bab69799bc830d01dbc8f06a98fe5d1799070` |
| `hotspot-train-yt-01-family-diagnostic.json` | `0e6b8f1c78cb8618c6cb10ba7b34a67ca74958da64d30bf756b00a458a30c537` |

`hotspot-outcome.json` binds these outputs and explains observed acquisition
versus formal study eligibility. No new model, training freeze, scoring,
calibration or activation follows. Previous406-test software checkpoint is
unchanged; this result adds private evidence/documentation only. The campus
failure remains separate. Future acquisition design should address independent
session/sample units and browser connection reuse before requesting further
recordings; it must not promise a fixed flow count from one video. Any future
training use needs a new explicit data-role declaration and separate evaluation.
