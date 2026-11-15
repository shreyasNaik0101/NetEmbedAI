# Research review: practical real-time encrypted-traffic classification

Reviewed 28 October 2026 against the current NetEmbedAI implementation and
primary papers, standards, official tools and model source. This is research,
not a new trained model, benchmark, scope change or promotion decision.

Subsequent user-authorized work is recorded in the
[implementation/comparison report](approach-comparison.md). The research-stage
statements below describe the state before those experiments; they do not
override the actual negative results or pending live gates.

Real-time traffic classification is feasible at defined levels of detail and
observation budgets. Our failures establish that our current selected model
does not transfer reliably to the measured local traffic. They do not establish
that early packet classification is impossible. The most useful next step is
a small existing-data diagnostic study, before another manual collection cycle.

## What the running system actually observes

The live adapter accepts supported QUIC beginnings, groups bidirectional endpoint
pairs, and retains at most the first thirty UDP-datagram observations. It passes
only payload bytes, direction and millisecond gaps to the predictor. It stops
adding features to a connection at thirty observations. A sixty-second browsing
visit can therefore create multiple short examples, but does not supply sixty
seconds of behaviour to any one prediction. See [the implementation](../src/netembed/capture.py).

A read-only calculation on the six currently authorized training recordings
(`instagram/youtube-dev-01`, `instagram/youtube-dev-02`, `instagram-dev-03/04`)
finds thirty connections: seventeen Instagram and thirteen YouTube. Twenty-four
have thirty packets. Their retained-prefix duration median is **102.6277 ms**;
21/24 finish within one second and 23/24 within three seconds. These are training
coverage descriptions, not evaluation results. The previously reported roughly
49 ms median came from a different, earlier training/development cohort.

We have not measured the handshake/application-data fraction of those prefixes.
Short duration alone does not prove a prefix contains only handshake traffic:
QUIC permits application data during connection establishment. Likewise, sizes
near 1,200 bytes are not a service identity. QUIC requires minimum-sized client
Initial datagrams and permits padding and coalescing. [RFC 9000](https://www.rfc-editor.org/rfc/rfc9000.html#section-14.1)

Prediction compute and useful observation time are separate quantities. A system
can update a live display immediately, provide an early uncertain ranking, and
make a later decision after more evidence. A proposed one- or three-second
window would be an experimental observation budget, not a measured latency
guarantee or a reason to call completed-flow statistics early features.

## Different tasks require different evidence

| Question | Potential evidence | What it does not establish |
| --- | --- | --- |
| Is this QUIC, TLS, DNS or RTP? | Protocol structure and a supported parser | Exact service or user activity |
| Which service does this connection resemble? | Packet sequences and a model trained for these labels | A reliably known service outside the trained set |
| Which name was contacted? | Visible handshake name, DNS, or authorized endpoint telemetry | Which browser tab owns all related background traffic |
| Is the user streaming, calling or browsing? | Longer flow/session behaviour plus appropriate activity labels | YouTube versus another streaming service |
| Which local executable owns an endpoint? | OS endpoint/process telemetry | Instagram versus YouTube within Chrome |

Your internship's pipeline separates identity from activity and records the
evidence basis. It also has safeguards against grading a name-based predictor
against labels obtained from the same names. Those design principles are useful.
Its activity rules, protocol evidence and naming/ownership cascade do not become
one packet-only service classifier by sharing a UI. The local repository was
read only; no private code, captures, internal references or headline metrics
are redistributed here.

## Finding 1: practical systems use more than packet shape

The official nDPI documentation describes protocol dissection, encrypted-traffic
metadata and classification. Its QUIC source processes TLS ClientHello content,
and includes hostname-based service matching. This is a credible practical
comparison, but its service labels cannot be interpreted as evidence that our
three packet channels alone should yield the same result. [nDPI documentation](https://www.ntop.org/products/deep-packet-inspection/ndpi/),
[QUIC implementation](https://github.com/ntop/nDPI/blob/dev/src/lib/protocols/quic.c)

Cisco's ETA documentation combines early length/time sequences with initial
packet and TLS metadata. Its existence supports the feasibility of online
analysis, not a promise of exact browser-service identification from three
channels. [Cisco ETA configuration guide](https://www.cisco.com/c/en/us/td/docs/ios-xml/ios/sec_data_eta/configuration/xe-16-12/sec-data-encrypted-traffic-analytics-xe-16-12-book/sec-data-encrypted-traffic-analytics-xe-16-6-book_chapter_01.pdf)

An explicit hybrid monitor could use a conservative evidence ladder: recognized
protocol; independently obtained unambiguous service-name evidence when present;
packet-model estimates separately identified; ambiguity retained when evidence
conflicts or is absent. Company-level information must not silently become an
exact app label, and shared CDN addresses cannot serve as unconditional identities.

This would revise the original prohibition on name/IP/process prediction
shortcuts. The current reference lane already keeps names separate from model
inputs; that separation must remain unless a new product scope is agreed.
Existing name-derived labels would not independently validate a name-based lane.

QUIC Initial protection can be removed using public connection information;
that does not decrypt subsequent application traffic. Actual ECH can hide the
inner service name, so a hybrid system still needs an honest unresolved outcome.
An ECH-like extension alone is not proof that ECH was actually used; GREASE must
not be confused with an encrypted inner name. [RFC 9312](https://www.rfc-editor.org/rfc/rfc9312.html#section-2.4),
[RFC 9849](https://www.rfc-editor.org/rfc/rfc9849.html)

## Finding 2: a relevant pretrained packet model was not tested

CESNET publishes **30pktTCNET_256**, a packet-sequence encoder producing
256-dimensional embeddings. A separate labelled classifier/reference database
is needed to turn those vectors into our service predictions. This is not a
ready-made ten-service replacement. [Official model reference](https://cesnet.github.io/cesnet-models/reference_models/)

Its accompanying paper evaluates frozen-embedding nearest neighbours, linear
probing and fine-tuning. It also tests an ordered raw-packet nearest-neighbour
baseline, while warning that near-duplicate/random-split datasets can make
nearest-neighbour results deceptively strong. Those are reasons for a bounded
comparison, not predicted success on this laptop. [Paper, revised January 2026](https://arxiv.org/html/2502.12930v2)

The checked upstream source declares 1,004,117 parameters, packet-only input,
saved clipping transforms, and weights trained on **CESNET week 46**. A local
HEAD-only request to the exact official weight URL returned HTTP 200 and
Content-Length **7,179,018 bytes**. No weight body was downloaded, package
installed, model executed or CPU performance measured. A header check establishes
availability at that time, not a verified artifact checksum or successful load.
[Weight metadata and architecture](https://github.com/CESNET/cesnet-models/blob/main/cesnet_models/models.py)

Week 46 is our original final-test period. These weights must therefore not be
scored on that old test as an independent competitor. Exact record overlap is
not audited. A separate current-local development/validation protocol is needed;
the existing B17 results and frozen version-3 two-family study remain intact.
Upstream software has a BSD-3-Clause licence; the weight provenance and applicable
redistribution terms must also be recorded before packaging an artifact.
[Upstream licence](https://github.com/CESNET/cesnet-models/blob/main/LICENCE)

An isolated screening study should begin with a frozen encoder and a small
training-only reference set, preserving whole-session splits. Use the upstream
input transform, not B17 normalization. Audit channel order, padding, interval
units and missing-prefix handling. Thirty-packet model availability does not
establish 5/10/20-packet quality: cap actual input before inference and measure
each supported budget separately. Published GPU throughput is not a laptop CPU
benchmark. Prefer a simple head; do not start a new large neural architecture
sweep or claim a few-shot/unseen-service result.

## Finding 3: handshake dependence is a specific hypothesis to test

The original CESNET QUIC study reported drift associated with a certificate-size
change and tested training without the first eight packet positions. Its results
show a stability/recall trade-off. It also used whole-flow statistics and
histograms, so those figures cannot be copied to our prefix-only model. This
motivates a matched handshake-dependence study, not dropping packets from the
live model without retraining. [Original QUIC classification paper, section V-A](https://tma.ifip.org/2023/wp-content/uploads/sites/12/2023/06/tma2023-final13.pdf)

Our local captures and the historical data differ in initial sizes and timing,
but that does not prove those differences caused the errors. A useful diagnostic
would compare size/direction-only, timing-only and original features, then one
fixed handshake-reduced representation if justified. It must fit transformations
on training data and select only on permitted development data. Early prefixes
with no remaining evidence must abstain rather than borrowing later packets.
An inference-only occlusion is a sensitivity check on changed inputs, not a
fair retrained-model comparison or a repair.

The 2025 IEEE S&P systematization highlights outdated data, session artifacts and
context/temporal overfitting as recurring problems in encrypted-traffic research.
It supports checking representation and collection before pursuing a larger
model. It does not identify the cause of our particular failures. [Primary paper](https://arxiv.org/html/2503.20093v1)

## Finding 4: longer online observation is a defensible alternative

Longer bounded windows can retain rates, direction balance, burst sizes and
periodicity while a connection continues. These can be computed with bounded
counters/histograms instead of retaining unlimited packets. They still need
training examples collected with the same observation budget and capture point.
They must never use future flow duration, final byte totals or the eventual
flow-end reason at an earlier decision time.

Published QUIC window representations exist: VisQUIC uses temporal packet
size/direction histograms. Its example task estimates HTTP/3 response counts;
that is evidence that this representation supports a different useful task,
not evidence of Instagram/YouTube classification. A simple window summary
baseline would precede image encoders or other extra architectures.
[VisQUIC paper](https://arxiv.org/html/2410.03728v2)

Our thirty-packet exports cannot reconstruct later on-wire bursts. Browser
NetLog records observe a different point and cannot silently substitute for
missing capture packets. A longer-window candidate requires a new versioned
feature/capture protocol and eventually deliberate user-started capture. This
is a scope/budget change, so it is not the first thing to implement merely to
avoid testing the cheaper existing-data hypotheses.

## Finding 5: fingerprints and endpoint attribution have limits

JA4 fingerprints client TLS characteristics, including QUIC. Its own examples
include a Chrome QUIC fingerprint. A browser fingerprint is not an exact
YouTube/Instagram identity: the same browser stack can contact both. It may
help describe collection domains or support a hybrid model; it cannot be
treated as a service answer key. [JA4 specification](https://github.com/FoxIO-LLC/ja4/blob/main/technical_details/JA4.md),
[official examples](https://github.com/FoxIO-LLC/ja4#examples)

Windows exposes UDP endpoint ownership, and Chrome exposes request events with
permissions. These enable useful local telemetry, but do not automatically give
an unambiguous tab-to-QUIC-datagram mapping. A Chrome process label alone cannot
distinguish its websites. Such telemetry could improve separate references or
an explicitly endpoint-assisted product, with connection-pooling and attribution
refusals preserved. It would not establish passive packet-model accuracy.
[Windows API](https://learn.microsoft.com/en-us/windows/win32/api/iphlpapi/nf-iphlpapi-getextendedudptable),
[Chrome webRequest API](https://developer.chrome.com/docs/extensions/reference/api/webRequest)

## Recommended decision order

| Priority | Work | Evidence it could add | Current-contract impact |
| --- | --- | --- | --- |
| 1 | Reconcile packet contract and run a fixed ordered raw-packet neighbour diagnostic on existing permitted development records | Whether summaries discarded useful local similarity | Same three channels; separate diagnostic protocol |
| 2 | Isolated official frozen-embedding screening with a simple classifier | Whether learned packet features transfer better than our scratch-trained reference | Same raw channels; additional experimental model, no default switch |
| 3 | Training-only handshake/feature-dependence study | Whether the front of the prefix creates fragile dependence | Requires a frozen paired representation study and retraining |
| 4 | If early packet evidence remains inadequate, agree on bounded longer windows | Whether additional observed behaviour improves the required task | New feature budget, matched data and evaluation |
| Optional product choice | Explicit protocol/name/packet hybrid | Greater visibility when other evidence is available | Changes original packet-only identity requirement |

The previous signature heuristic compressed each prefix into ten descriptors.
Ordered raw-packet nearest neighbours and a pretrained encoder are therefore
untested comparisons, not reruns of that failed heuristic. An already explored
ordered forest is also a different learner; its failure does not settle them.

For screening, use only declared training and already-retired development
records. Preserve `cal-02`, future selection and final records. Do not inspect
protected data to choose features, neighbour counts or thresholds. Screening
scores on reused development records remain exploratory. Freeze a candidate
before independent calibration and new live quality measurements. A proposed
third-model study must not silently amend the already frozen version-3 study.

Evaluate per-service error, abstention/coverage, actual packet budget and CPU
latency; compare at the connection/session level as well as the prefix level.
Capture/reference eligibility coverage is separate from model confidence
coverage. ECH ambiguity, unsupported services and new connections missed because
capture began late must not disappear from the inventory. A low maximum score
does not prove a service is unknown, and a high score does not prove it is known.

No new capture is needed for the initial existing-data screening. If it finds
no meaningful signal, stop that branch and make an explicit product/observation
budget decision. Do not begin another open-ended collection or architecture
search, relax failed calibration limits or imply that the original plan is a
completed model-validated release.

## Evidence and changes made for this review

Local calculations and the HEAD-only availability result are retained in
`experiments/browser-adaptation/research-20261028/verification.json`, with hashes
of the six training-row files. The online source links above were checked on
28 October 2026; moving upstream source links should be pinned before execution.
No accuracy experiment, model training, dependency installation, live capture,
threshold change, publication or paid compute occurred during this research.
The running B17 artifact and all frozen data roles are unchanged. The existing
222-test checkpoint is software evidence; no new test-suite run is claimed for
this documentation-only review.
