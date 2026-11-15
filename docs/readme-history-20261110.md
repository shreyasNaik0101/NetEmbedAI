# NetEmbedAI

A local app that classifies supported encrypted QUIC traffic from early packet sizes, directions and timing. FastAPI serves one React screen; TShark captures only after the user presses Start. Inference loads a complete trained bundle without training data.

## Current evidence

A separate [bounded Spotify data study](spotify-data-repair-v1.md) trained on seventeen verified local Spotify connections. On its reserved development visit, the candidate recognized all four Spotify flows where the control recognized none, but worsened retained YouTube/Instagram quality and exceeded public per-class regression limits. The candidate is rejected under the frozen gates; calibration and final capture are blocked. The live profile is unchanged.

The subsequent [three-weight offline study](spotify-weight-study-v1.md) is also complete. Its 1% Spotify-weight candidate retained 17/17 existing local ten-packet decisions and recognized 4/4 Spotify flows, but lost correctness at later prefixes. None of the three candidates passed every frozen retention gate; no new model was activated and no more recordings are requested by these studies.

A separate [explicit ten-packet mode](spotify-ten-packet-v1.md) is implemented and packaged without refitting. It passed its narrower reused-development comparison: Spotify 4/4 versus 0/4, retained YT/IG 17/17 in both, public 407/452 versus 405/452 eligible exact-ten flows. It refuses shorter inputs and reports later packets as observations only. Confidence calibration and fresh genuine live verification remain pending; that offline study did not activate its candidate.

The [three-visit fresh verification protocol](ten-packet-fresh-v1.md) is frozen and its uncalibrated ten-packet validation profile is loaded on localhost8002. The interrupted recording received two connections and 57 retained early packets, but a viewer interruption and second Start require session-integrity review. Its latest stopped evidence is preserved, prospective grading is blocked, and no fresh quality or accepted-label result is claimed. The original default/demo decision is unchanged.

The [interruption diagnostic and recovery changes](capture-session-recovery.md) confirm one socket-verified YouTube connection with the correct raw ten-packet guess and exact replay of all seven native events. The service now preserves the last three stopped recordings in memory across another Start and exposes downloads and clearer stop reasons. The lost first session is not recovered; capture remains off and the interrupted fresh scope stays blocked.

A subsequent [unplanned active connection check](capture-delivery-pressure.md) stayed connected to its two-minute limit and computed all230 checkpoints, but reported120 drops and four unacknowledged predictions. Bounded cumulative packet-update coalescing, prediction-priority delivery and separate loss counters are implemented and software-tested, followed by the controlled delivery check below. No new classification-quality result is claimed.

A later [viewer conflict](viewer-conflict.md) was traced to NetEmbedAI previews inside VS Code holding the single live stream while Edge was rejected. The UI now explains this case and offers manual Reconnect without endless conflict retries. Edge was visibly reconnected before the controlled delivery check.

The [matched timing repair](spotify-timing-repair-v1.md) is complete and rejected: it left Spotify unrecognized and reduced retained service quality. The live profile is unchanged. No additional recording or fit is requested by that experiment.

A subsequent [Spotify diagnostic](spotify-diagnostic-v1.md) found a concrete failure: all five verified connections ranked YouTube first at ten packets, with one wrong accepted label and four refusals. The recording had seven reported drops and is diagnostic only. Spotify remains locally unvalidated; the successful two-service checks do not transfer automatically.

- Historical CESNET benchmark: the selected augmented cross-entropy TCN (B17) achieved macro F1 0.84285 at 10 packets and 0.88636 at 30 packets on the held-out week. These are stored-dataset results.
- Improved forest: four fresh local visits produced 22/22 correct raw ten-packet choices versus 7/22 for the older forest. This is a small YouTube/Instagram IPv6 hotspot comparison, not a comparison against B17.
- Two further genuine live visits: 8/11 verified connections received an accepted ten-packet label, all eight correct. One was refused and two checkpoints were missing. Later Instagram prefixes often fell below the confidence threshold.
- The missing-prefix queue behavior has since been fixed in software tests. That change has not received a new live evaluation. Viewer recovery has also been hardened; the original rejection was not conclusively diagnosed.

[Live results](ipv6-live-policy-results.md) · [Model choice](demo-model-decision.md) · [Interview guide](interview-guide.md)

## Run on this Windows laptop

From the traffic_classification directory:

~~~powershell
.\.venv\Scripts\python.exe scripts/serve_live_policy.py
~~~

Open http://127.0.0.1:8002 once in Edge. The explicit demo profile loads the improved forest and verifies its frozen bundle/policy identity. It never starts capture. If that port is already serving the app, use the existing instance. Select your interface, then press Start deliberately. Stop finishes capture; disconnect or the duration limit also ends it. Reconnect restores the viewer connection, not the recording. A backgrounded/throttled tab can expire its heartbeat; keep the viewer foreground for a demo.

[Step-by-step demo and recovery](demo-runbook.md)

## Fresh setup

Install Python 3.11, Node and native TShark/Npcap separately. Then:

~~~powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install --no-deps -r requirements-cpu.txt
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
npm --prefix ui ci
npm --prefix ui run build
~~~

Trained artifacts are local and ignored by Git. A fresh checkout needs a legitimate bundle copied or regenerated; it does not download or invent weights. For a portable extracted bundle, run:

~~~powershell
.\.venv\Scripts\netembed.exe serve --bundle PATH_TO_EXTRACTED_BUNDLE
~~~

Open http://127.0.0.1:8000. The fixed laptop demo launcher requires its exact local artifact paths; the generic serve command accepts a portable bundle. Linux/macOS use .venv/bin/python and .venv/bin/netembed and native TShark; only this Windows environment has been locally validated.

## Verify and reproduce

~~~powershell
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\ruff.exe check src scripts tests
npm --prefix ui test
npm --prefix ui run build
~~~

Tests use constructed fixtures and never start real capture. [Experiment commands](experiments.md), [public policy reproduction](ipv6-public-policy.md), and [live protocol](ipv6-live-policy-check.md) distinguish training, development, calibration and evaluation.

## Limits

The model uses payload bytes, direction and inter-arrival milliseconds. Addresses only group packets. Hostnames/browser logs provide separate evaluation references, never model input. UDP/443 alone does not prove QUIC. Unsupported traffic, unknown services, network changes and low confidence remain limitations. Model scores are not correctness probabilities. The live measurements do not establish universal accuracy or hard real-time behavior.

The compact TCN and same-data classical baseline, matched CE/SupCon studies, complete bundles, chronological evaluation, bounded capture, API, UI and CI are implemented. Old TensorFlow/PyTorch work stays under legacy/. See the [model card](model-card.md), [architecture](architecture.md), [data card](data-card.md), and [earlier progress history](readme-history-20261106.md).

The [controlled delivery check](delivery-check-v1.md) passed once on genuine user-started traffic: 61 connections, 223/223 checkpoint events acknowledged, zero missing checkpoints/drops/disconnects, and 1,296 redundant cumulative packet updates coalesced. Median capture-to-browser receipt was 139.6 ms (p95 466.7 ms). This is delivery evidence, not service-classification accuracy or fitted confidence.
