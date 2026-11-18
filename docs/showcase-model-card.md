# Showcase model card — 10 November 2026

## Intended use

The recommended local showcase is an experimental forest that scores the first
ten packets of a TShark-verified QUIC flow. It is intended for a user-started
learning/interview demonstration, not enforcement, unknown-service detection,
universal app identification, adversarial guarantees or hard real-time use.
Its policy is **unfitted**: the UI may show top model alternatives but accepted
labels are withheld. Model scores are not correctness probabilities.

This showcase profile is a deliberate local launch choice. It does not replace
the historical TCN benchmark decision in `configs/default-decision.json` or
rewrite earlier experiment outcomes. The ten-packet model's labels include ten
CESNET services; only YouTube, Instagram and Spotify were included in the small
fresh local studies described below. No claim is made that the other labels work
on this user's network.

## Artifact and inputs

* Local bundle: `experiments/spotify-ten-packet-v1/bundle`.
* Metadata identity/SHA-256:
  `fa1f4837e4ae11c9169258ecb20338ae3c0c81c2d206231fb6fe19405b8d8549`.
* `forest.json` SHA-256:
  `b5a312fe86850a93fdc1c7b74cbfb6ffa58009e781888bafa5e47062e6f42adf`.
* Architecture: a portable JSON random forest, `summary-v1`, fixed first ten
  packets. Inputs are UDP payload bytes, client/server direction and inter-arrival
  milliseconds. It uses no hostname, address, process name or packet payload.
* Bundle includes model weights, architecture, feature schema, labels,
  normalization metadata, policy, versions, provenance and checksums. The
  summary forest's feature path uses raw summaries; saved normalizer metadata is
  retained with the artifact for the shared contract. Inference needs no training
  data.

The artifact is Git-ignored and requires a legitimate local bundle or archive.
Its source uses CESNET-QUIC22 and private, user-authorized local training
evidence. Reproduction must follow the data attribution and role boundaries in
the [data card](data-card.md); local private evidence is not bundled for sharing.

## Measured results and limitations

The [fresh raw-guess verification](ten-packet-fresh-continuation-v1.md) found
7/7 YouTube, 4/4 Instagram and 5/5 Spotify eligible target connections correctly
ranked first, with actual native ten-packet events. The Instagram session ended
on viewer heartbeat expiry, so the frozen drop/receipt screen does not establish
uninterrupted viewer reliability. These 16 connections came from three visits on
one user-declared hotspot; they are correlated and do not prove population
accuracy or behavior on a different network.

A separate [acceptance-policy experiment](ten-packet-policy-v1.md) fit threshold
zero on three fresh calibration visits. On later final target visits it accepted
one wrong YouTube label: YouTube 8/9 correct accepted, Instagram 6/6 correct
accepted, Spotify 4/5 correct accepted with one withheld. The predeclared
per-service zero-error gate failed. This policy was not promoted, and threshold
zero provided no score-based rejection of in-scope top guesses. The final set
must remain excluded from training and candidate selection.

The [matched timing-jitter study](timing-jitter-matched-v1.md) passed its
development gates at seed 17 and failed at seeds 42 and 123; it was not promoted.
Its transformed views are abstract stress tests on reused development data.
The earlier nearest-millisecond repair was also rejected. No augmentation,
confidence rule or model replacement is implied by these results.

The [paired exporter check](paired-exporter-check-v1.md) matched 30 packet
directions, payload sizes and gaps on one deliberately user-started selected
connection read from the same PCAP offline. The connection's service was not
asserted. This is limited feature extraction evidence, not local classification
accuracy, live event parity, all-network parity or historical exporter proof.

Historical held-out CESNET TCN macro-F1 was 0.84285 at ten packets and 0.88636
at thirty. Those metrics refer to the neural reference, not this forest. The
matched CE/SupCon evidence did not support retaining contrastive loss; see the
[historical model card](model-card.md) and [data card](data-card.md).

## Operational boundaries

Capture is started only by the local user. A bounded flow table, retained prefix
and queues constrain memory; process cleanup occurs on Stop, viewer loss and
duration limit. The server binds to loopback. Some PCs require Npcap privileges;
the app reports an unavailable interface or model rather than using fake data.
The optional Chrome reference and PCAP export can contain sensitive metadata and
must be kept private. Browser receipt timing is not rendering time or a hard
real-time guarantee. The background-heartbeat repair has software and limited
local operational evidence, not a guarantee through sleep or suspension.

The application remains an experimental, evidence-bounded showcase. Future
changes need separately assigned development data and a new independent
evaluation; earlier final data must not select or fit a replacement.
