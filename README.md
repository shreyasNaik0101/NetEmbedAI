# NetEmbedAI

NetEmbedAI is an **experimental local application** for exploring whether early
encrypted QUIC packet patterns can distinguish services. A user starts capture
in one React screen; a local FastAPI service feeds packet sizes, directions and
timing to a trained model. It also supports explicitly separate recorded replay.

The model does not read packet contents, destination names, IP addresses or
process names. Endpoints group packets temporarily; optional Chrome reference
logging is used separately for evaluation. The capture adapter requires a
TShark-dissected QUIC Initial to begin a flow: UDP/443 alone is not proof of QUIC.

## What works, and what the evidence says

The recommended **showcase profile** is a locally trained, fixed-ten-packet
forest. It waits for ten packets and uses only those first ten for its scores;
later packets remain visible. Its acceptance policy is unfitted, so the app
shows experimental alternatives and withholds accepted labels. Model scores are
not probabilities of correctness, and a list of model labels is not proof that
every service works on your network.

* In one small fresh local raw-guess check, all **16** eligible connections were
  ranked correctly: YouTube 7/7, Instagram 4/4 and Spotify 5/5. They came from
  three visits on one user-declared hotspot; the Instagram viewer timed out.
* A separately fitted acceptance policy selected threshold zero and **failed**
  its later final screen. In the three target visits it accepted a YouTube
  connection as Spotify (8/9 correct accepted YouTube), accepted 6/6 Instagram,
  and accepted 4/5 Spotify with one withheld. The policy was not promoted.
* A matched timing-jitter forest passed its development gates at seed 17 but
  failed at seeds 42 and 123. It was not promoted. These are reused development
  examples and abstract stress tests, not new final accuracy.
* Separately, the historical CESNET held-out week gave the augmented TCN macro-F1
  **0.84285 at ten packets** and **0.88636 at thirty**. Those figures describe a
  different model and stored dataset; they are not local showcase accuracy.
* One deliberately user-started PCAP prefix matched the current adapter and
  ipfixprobe 5.8.0 on 30 packet sizes, directions and timing values. Both read
  the same saved bytes offline. This is limited parser evidence, not proof of
  classifier accuracy or full live-event parity.

This is an interview/learning prototype, **not a validated release or an
unknown-service detector**. It has no guarantee for new networks, devices,
apps, VPNs, adversarial traffic or hard real-time response. The honest details
and evidence links are in the [showcase model card](docs/showcase-model-card.md).

## Run the local showcase on Windows

Prerequisites: Python 3.11, Node.js/npm, native TShark and Npcap. From the
`traffic_classification` directory, with the local trained bundle present:

```powershell
.\.venv\Scripts\python.exe scripts/serve_showcase.py
```

Open `http://127.0.0.1:8002` in one browser tab. If port 8002 already runs this
profile, use the existing tab; otherwise choose another port with `--port 8003`.
The launcher verifies the exact unfitted bundle before starting. Confirm **Stream connected**,
select the actual network interface, press **Start**, then open a fresh QUIC
connection. Inspect arriving packet metadata and model alternatives, then press
**Stop**. A disconnected or unresponsive viewer stops capture; reconnecting
does not restart it. Nothing captures during installation or server startup.

For a detailed walkthrough and troubleshooting, see [the demo runbook](docs/demo-runbook.md).
The optional Chrome NetLog/reference workflow is not required for ordinary use;
it is a separate evaluator and can contain sensitive network metadata.

### Fresh setup and model files

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --no-deps -r requirements-cpu.txt
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
npm --prefix ui ci
npm --prefix ui run build
```

Trained bundles and datasets are ignored by Git. A fresh checkout therefore
needs a legitimate bundle copied from an authorized local archive or regenerated
from the documented data and training artifacts; no weights are downloaded or
fabricated automatically. Inference itself does **not** need the training data.
For the same showcase bundle elsewhere, pass its extracted directory to the
launcher with `--bundle`. The bundle
contains checksummed weights, preprocessing, labels, architecture, versions,
policy and provenance. The local showcase bundle identity is
`fa1f4837e4ae11c9169258ecb20338ae3c0c81c2d206231fb6fe19405b8d8549`;
its `forest.json` SHA-256 is
`b5a312fe86850a93fdc1c7b74cbfb6ffa58009e781888bafa5e47062e6f42adf`.
A local archive is at `artifacts/local/showcase/netembed-ten-packet-unfitted.zip`,
SHA-256 `019369d9c9f88261fc3892a17facb92efaf4e3b7031ef80fd92a53890088a9be`.
Check its extracted inference with training and capture files denied using
`.\.venv\Scripts\python.exe scripts/check_showcase_archive.py`.
To create it at a new path, run:

```powershell
.\.venv\Scripts\python.exe scripts/package_bundle.py --bundle experiments/spotify-ten-packet-v1/bundle --decision experiments/spotify-ten-packet-v1/decision.json --model-card docs/showcase-model-card.md --output artifacts/local/showcase/new-archive.zip
```

Local user-derived data and PCAPs are private; do not redistribute them without
appropriate authorization.

Linux/macOS users can use `.venv/bin/python` and native TShark; this showcase
setup has only been checked locally on Windows. Docker is optional and used for
the independent exporter check, not for normal inference.

## Verify

```powershell
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m ruff check src scripts tests
npm --prefix ui test
npm --prefix ui run build
```

Tests use constructed fixtures and do not start real capture. Real live quality,
benchmark results and software tests are separate evidence. See the
[beginner interview guide](docs/interview-guide.md),
[final policy result](docs/ten-packet-policy-v1.md),
[timing experiment](docs/timing-jitter-matched-v1.md),
[showcase verification](docs/showcase-verification-20261110.md),
[data card](docs/data-card.md), and
[historical README](docs/readme-history-20261110.md). The compact TCN and
same-data classical baseline remain in the repository; contrastive learning was
not retained as the default based on the matched development comparison.
