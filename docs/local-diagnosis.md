# Local diagnosis: 25 October 2026

A measurement bug is fixed. Reliable local recognition is **not** established.
The default B17 weights, normalization, labels and threshold are unchanged.
No training or final-test tuning occurred in this investigation.

## Exact timestamp subtraction

The parser converted epoch timestamps to floats before subtraction. A true
one-microsecond gap could become about 0.000954 ms, and nanosecond reordering
could appear as equal timestamps. It now subtracts integer nanoseconds first,
then converts the gap to milliseconds. Wall-clock event/latency timestamps still
use seconds. This corrects numeric precision; feature units and prefix/model
semantics are unchanged. Status, events and exports identify the adapter as
`tshark-prefix-ns-v2`.

An existing recording, `C:/Users/shrey/Downloads/phone_youtube.pcap`, supplied an
independent compatibility check. The user subsequently said they do not remember
its origin and think it was downloaded. It is treated as unknown-provenance
downloaded material, excluded from training and local-quality claims. From
the first 12,000 frames, the earliest complete eligible 30-packet prefix was
selected before comparison. Original frames were
`3,4,10,12,24,27,28,29,30,31,32,33,34,56,59,60,63,64,65,66,67,68,69,70,71,75,76,77,78,79`.
Their original bytes were copied to an ignored local PCAP; no packets were
constructed or modified. The filename was not used as a service label.

Independent ipfixprobe 5.8.0 PSTATS matched all 30 sizes and directions. The old
parser's maximum raw gap error was 0.000170517 ms. After the correction, all raw
gaps match **exactly**, maximum error **0 ms**. The cached container ran with no
network, dropped capabilities, one CPU, 512 MiB RAM and only the PCAP mounted
read-only. No live interface, image pull or paid compute was used.

This verifies current-exporter compatibility on those recorded bytes. It does
not establish ownership/network provenance, historical 2022 integer-millisecond
conversion, a fresh live session with the new adapter, or the cause of weak scores.

Source PCAP SHA-256:
`c0fe5860b50af2f20b75946efcd006a018071e43133590c08e4183290ac87143`.
Selected prefix SHA-256:
`43ddbef754660921dd23eac69e8605b732ee8643e31b2e188331a161b5b4fb67`.
The original file is untouched; `artifacts/local/ipfixprobe-recorded/selection.json`
records the exact extraction. Repeat using a new output path:

~~~powershell
.venv/Scripts/python.exe scripts/check_ipfixprobe_fixture.py --image netembed-ipfixprobe-parity:local --pcap artifacts/local/ipfixprobe-recorded/recorded-prefix.pcap --source-description "Unknown provenance, possibly downloaded; parser compatibility only" --output artifacts/local/ipfixprobe-recorded/parity-repeat.json
~~~

## Timing and model comparisons

The fresh Chrome/Wi-Fi trial has four independently mapped YouTube connections,
giving 14 available offline 5/10/20/30-packet checkpoints. These remain separate
from its eleven actually delivered live decisions. Four fixed timing hypotheses
were tried without fitting: unchanged gaps, floor each gap, nearest-integer gap,
and floor absolute timestamps before differencing. The latter reconstructs times
from saved metadata; it is not verified historical exporter processing.

| Model/view | Accepted / 14 | Top-ranked reference agreement / 14 |
| --- | --- | --- |
| B17 unchanged | 1 | 10 |
| B17 floor each gap | 0 | 9 |
| B17 nearest gap | 0 | 10 |
| B17 floor timestamps first | 1 | 10 |
| A17 unchanged, plain CE | 3 | 9 |

A17 uses its own earlier calibrated threshold 0.64; B17 uses 0.67. Coverage does
not isolate augmentation's effect. All accepted labels in this small cohort were
YouTube, but prefixes share four flows from one session. Neither zero observed
accepted errors nor these counts establish a useful error bound or justify a new
default/threshold. The original full matched-seed decision stands. The diagnostic
reproduced byte-for-byte on a second run.

Training-only summaries show another sample difference: median packet size at
20 packets was 1,248 B locally versus 189 B for 1,235 eligible CESNET YouTube
training flows. This describes a difference, not its cause or a reason to rescale
sizes to force labels. Selection, calibration and final-test records were unopened.

~~~powershell
.venv/Scripts/python.exe scripts/diagnose_local_shift.py --evidence artifacts/local/capture-youtube-01.json --reference artifacts/local/reference-youtube-01.json --data data/processed/v2 --bundle B17 experiments/full-real/20261024-151720-3532794c/bundle --bundle A17 experiments/full-real/20261024-132801-9bc6963a/bundle --output artifacts/local/timing-diagnostic-repeat.json
~~~

## Socket observation-point comparison

Exact endpoint tokens, both ports, connect beginning/completion and unique socket
identity bind browser UDP transfer records to the four mapped connections.
Ambiguous, reconnected, failed or endpoint-changing sockets are refused. Chromium
[omits the error field on successful completion](https://raw.githubusercontent.com/chromium/chromium/main/net/log/net_log_with_source.cc).
The initial checker wrongly required explicit zero; its refusal report is
preserved as `browser-socket-consistency-youtube-01.json`. Corrected-schema results
use `-v2`; completion is still required. Software tests cover both forms and errors.

Within each direction, **all 53 sent and 59 received sizes match in order**.
The merged sequence has 25 direction mismatches and 25 size mismatches at 29
distinct positions among 112 packets. These mismatches remain in the report.
Browser event logging and capture observe different points, and the browser
event clock has millisecond resolution. Browser order is not a reference for
on-wire order and is not substituted into live processing. Actual
[UDP socket transfer counts](https://raw.githubusercontent.com/chromium/chromium/main/net/socket/udp_socket_win.cc)
avoid confusing [individual/coalesced QUIC events](https://raw.githubusercontent.com/chromium/chromium/main/net/quic/quic_event_logger.cc)
with UDP datagrams.

An explicitly offline B17 replay of the socket metadata retained the same
top-ranked labels at all 14 checkpoints. Scores changed and the single accepted
decision moved from 10 to 20 packets; 13/14 still withheld a label. This is no
reliable repair, live prediction or unbiased quality estimate. Attribution itself
used size/time anchors, so comparisons are conditioned on successful correlation.

~~~powershell
.venv/Scripts/python.exe scripts/check_browser_receive_parity.py --socket-mode --socket-replay-bundle experiments/full-real/20261024-151720-3532794c/bundle --evidence artifacts/local/capture-youtube-01.json --netlog artifacts/local/chrome-netlog-youtube-01.json --reference artifacts/local/reference-youtube-01.json --output artifacts/local/socket-diagnostic-repeat.json
~~~

## Verification and remaining evidence

All **104 Python tests passed**, including epoch-sized microsecond/nanosecond gaps
and nanosecond reordering. Ruff passed. The existing UI was unchanged. The service
on port 8001 restarted idle with the corrected adapter and unchanged B17 artifact;
API/direct scores matched exactly and UI returned HTTP 200. Capture stayed stopped.
This checks startup and recorded inference, not fresh live validation. The portable
model archive is unchanged.

Local reports under `artifacts/local/` are ignored by Git:

| Report | SHA-256 |
| --- | --- |
| `timing-model-diagnostic-youtube-01.json` | `3c0d9e82b6803a149abc2f076b1ea032c9e48ecaa6226aeef97d443e86bd47ef` |
| `browser-socket-replay-youtube-01-v2.json` | `1da97f237a728b1b970dfbc429725eb988024d19716d0a08527ac48e9b032ea0` |
| `ipfixprobe-recorded/final-parity.json` | `8bca523221639185a2911313a483bfd21a3a662ddce800daaa3160eba9e6acf2` |
| `ns-v2-service-check.json` | `f216ae0f64fd9b4b4c84a65850aca0122e5afc6fdcf3a84b5805ee1fb7c3c8a0` |
| `recording-inventory.json` | `dec04721a8ffc314c0e286bba075f0c5f1748fea85d414cad380930d74a8a868` |

Five existing recordings were inventoried: YouTube, Instagram, WhatsApp,
Instagram `_2` and WhatsApp `_2` filenames. Across 107,243 packets there were no
identical timestamp-plus-packet-byte records between files. This does not establish
ownership, user actions, network identity or full session independence.
Instagram/WhatsApp model predictions remain unexamined, and no local recordings
were used to fit a model. They are excluded from training and local-quality
evaluation because their provenance remains unknown. The immutable decision in
`artifacts/local/recording-provenance-decision.json` has SHA-256
`79fc56d379a9cab980d59226ed1e6e28af0348b04f7ae2039dd36630095dd439`.
Earlier checksummed reports are preserved and retain their then-pending wording;
this later provenance decision governs their use. A related project's notes
describe PCAPdroid capture-tool artifacts for similar filenames, but exact file
identity was not verified and no stronger provenance was inferred. Never derive
service labels from filenames.

Remaining gates: fresh attributable local recordings; a separated two-service local
quality study; any justified adaptation on development data only; and a fresh
user-started check of the corrected adapter. Historical timing quantization and
capture-point transfer remain limitations. A few metadata adjustments have not
repaired the model.
