# Local paired exporter check

This is an engineering check, not a labelled service-quality study. One
deliberately user-started local PCAP is selected offline, then the current
TShark adapter and an independent ipfixprobe 5.8.0 exporter process the **same
selected PCAP bytes**. There is no model inference, fitting, browser logging,
service attribution or automatic live capture. It does not compare a native
live app event against the PCAP, reconstruct the 2022 exporter, or prove
classifier accuracy.

## Privacy and collection

The PCAP records raw UDP/443 packets, which can include payload bytes, IP
addresses and other sensitive traffic metadata for connections on the selected
interface. It can include background traffic from other apps. It stays locally
under the Git-ignored `artifacts/local/paired-exporter-check-v1`; the workflow
does not upload it or delete it automatically. The local Docker exporter mounts
only the selected PCAP read-only, uses `--network none`, drops capabilities and
never pulls an image. Exporter stdout is also saved locally and can contain
network metadata. The user controls later retention or deletion.

Capture is started only when the user deliberately runs the command. It stops
at the first of 30 seconds, 12,000 packets or the 4,096 KiB file cap. A 45-second
process timeout terminates the capture process tree and preserves any partial
file for diagnosis. The raw file, intent and subsequent outputs are write-once:
existing evidence is never silently overwritten. The capture receipt binds the
original bytes by SHA-256. A failed or short capture is a finding, not proof of
parity. The NetEmbedAI live Start button is not needed for this separate check.

## Steps

Run only after the user has chosen the active interface and understands that raw
packet data will be stored. On this laptop Wi-Fi was interface `9` when checked;
interface numbers can change, so verify first if the network configuration has
changed. Close unrelated applications if the user wants less background data.

```powershell
cd C:\Users\shrey\NetEmbedAI\traffic_classification
.\.venv\Scripts\python.exe scripts\paired_exporter_capture.py capture --interface 9
```

After the command prints its startup message, wait five seconds and open an HTTPS
site in Chrome. The command stops automatically and writes a receipt. No Chrome
NetLog is necessary. The flow is selected solely by seeing the first verified
QUIC Initial-based flow reach ten ordered packets, without hostnames, service
labels, model scores or user activity as a selection shortcut. It may be a
background connection; do not call it YouTube or Spotify based on what was open.

After capture ends, run the following offline commands from the same directory:

```powershell
.\.venv\Scripts\python.exe scripts\paired_exporter_capture.py select
.\.venv\Scripts\python.exe scripts\paired_exporter_capture.py compare
```

The selection receipt binds both original and selected PCAP checksums. The
comparison checks them again and checks the fixed local image ID before running
the existing offline exporter checker. Reported raw features include up to the
first 30 packets, their directions, UDP payload sizes and inter-arrival gaps.
The report records whether they agree within `1e-7` ms and the maximum gap
difference. A mismatch or processing failure must be reported as observed;
the PCAP and partial outputs remain available for diagnosis. The existing
checker requires one extracted flow and imposes its own input and process caps.
Do not modify input bytes, pick a different flow based on a preferred outcome,
or use this check to revise the already completed final model test.

## Fixture validation

The local image `sha256:c673a8e1b05c9678d33dcd851c0f7a9ba572f4ec2f263419a3da1d23e813f196`
was available. A previously constructed `windows.pcap` fixture was processed
through the same selector; both exporters agreed, with maximum raw timing error
0 ms. The result is explicitly marked `fixture: true`:
`artifacts/local/paired-exporter-fixture-v1/parity-bound.json`, SHA-256
`e56d64ea61d3a94f07940fbbbb32a9b2c38385e4879478ab1f8fba4bedd0595e`.
This is software evidence, not actual live-traffic validation. The separate RFC
fixture comparison passed as well. Twenty-two focused tests passed and Python
lint passed. Tests mock capture process startup; none capture network traffic.

Re-run focused software tests with:

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_paired_exporter_capture.py tests/test_reference_parity.py tests/test_encapsulation.py -q
```

## Observed user-started check, 10 November 2026

The user deliberately ran the capture command on the declared Wi-Fi interface.
The receipt records exit code 0, 4,096,735 bytes and SHA-256
`af21725d5d89e258c9e9f8801785c7ae2aad862d9524e28c05ec7aa4c9591ef2`.
The recorded interval from intent to receipt was about 17.4 seconds, below the
30-second cap; the tool did not record which stop condition fired. The file size
was near the configured 4,096 KB cap.

The fixed selector chose the first qualifying QUIC flow, independently of
service identity or prediction. Its selected PCAP SHA-256 is
`f18ae936b21ecd8b2e33a51a91d31016db82487ae812d110e9e7cac6361206da`.
Both the current adapter and ipfixprobe 5.8.0 produced 30 prefix packets with
**zero direction mismatches, zero payload-size mismatches and maximum timing
difference 0 ms**. An independent JavaScript recount confirmed these values.
The local, network-disabled container used the pinned image ID above.

Report: `artifacts/local/paired-exporter-check-v1/parity.json`, SHA-256
`8b1ddd4bee8b49c8bd8bdcae3c09b52baf19debb7487766dfd4cab51f0fd9355`.
Capture, selection, receipt and exporter stdout remain private under the same
root. The user may choose when to remove these sensitive files.

This is one user-started local PCAP and one first-eligible connection. Its
service has not been independently labelled, even if a site was opened. Both
extractors read the same saved bytes offline: this result supports compatibility
for that prefix, but does not prove native live app event parity, all traffic,
the historical 2022 exporter's semantics, model accuracy or the cause of the
previous Spotify misclassification. No model, threshold or final-test result
was changed. No additional capture is implied by this result.
