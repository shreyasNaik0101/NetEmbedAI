# Two user-started visits on the fixed public-policy forest

This stage runs the [unchanged public-policy artifact](ipv6-public-policy.md)
in the actual capture/UI pipeline. Exactly one YouTube and one Instagram visit
are declared. It measures actual accepted/refused decisions and browser receipt
latency, without training or threshold changes. The completed four-visit raw
evaluation is not reused or converted to calibration data.

Declaration: `configs/ipv6-live-policy-v1.json`, canonical SHA-256
`c2f040c50b540cf083451953d27d50dd42e96845afebd6a9113080127ecdf695`.
Artifact: `9878d0818370ede3e9897a9cc654b4ddc0afcd87d41b2d7134ccaf52592b528a`.
Threshold 0.76/minimum 10 packets, labels, preprocessing and weights are frozen.

## Actual readiness — 6 November

The temporary validation instance is running at `http://127.0.0.1:8002`.
The normal 8001 instance/default remains B17 and is stopped from capturing.
Use only the validation page for this check. This is a temporary second instance
of the same local service, not another application or distributed component.
Only the user's deliberate Start on the chosen page starts packet collection.

The first preview's restricted execution could not spawn TShark to list
interfaces. It had no capture/session and was stopped. Restarting only this
preview with approved normal-local-user process access fixed interface listing;
no driver install, administrator UI or Windows security setting changed.

Actual HTTP model/status, Wi-Fi interface 9 and an Origin-checked real WebSocket
status exchange pass. Capture is false and no user session exists. Readiness
report `artifacts/local/ipv6-live-policy-v1/startup-verification.json`, SHA-256
`e76901579e43de01667607325e9ca4c6a3bc9a7c66b04078b8123a69fa691f51`.
The native network preflight confirms current dual-family reachability; it does
not establish QUIC quality or independently identify the hotspot.

The first YouTube intent was saved at 15:12:23 UTC after verifying Chrome fully
closed. It is `prepared_not_capturing`. Instagram is not prepared. No packet
capture was started by service launch or readiness checking, and no quality or
candidate live-latency result exists yet.

## Two fixed visits and honest denominators

`live-yt-01` then `live-ig-01` must occur on the same local date, after declaration.
Use the same phone hotspot, Wi-Fi 9, normal Chrome, Edge viewer, reference ON,
longer windows OFF. Target activity 60 seconds; capture cap 120 seconds. No
deliberate background load; incidental traffic and attribution refusals remain
in the inventories. Before each preparation, fully exit Chrome; reopen after
the saved intent. Stop app/log and keep Chrome open until archival verifies its
process lifetimes. Each visit needs one complete browser-verified target IPv6
flow and the existing packet/socket checks. Exactly one attempt per slot; no
automatic replacements. Processor failures preserve the same recording.

Primary quality uses **actual emitted ten-packet predictions** on target-service
flows in their target visits. A missing emitted checkpoint is counted separately
from a model refusal. End-to-end coverage divides accepted decisions by all
eligible target flows reaching the budget; conditional model coverage divides
by actual emitted decisions. Replay never fills a missing live decision.
Available 5/10/20/30-prefix replay is saved separately as a diagnostic.

The descriptive policy screen requires each service to have at least one
accepted primary case, accepted error at most 0.10 and end-to-end coverage at
least 0.50. A busy visit cannot hide the other service's failure. Small support
cannot establish population reliability. A failure ends this scope without
retuning or asking for extra replacement recordings.

For all actual emitted events, including unverified/background flows, report
sample counts and p50/p95 capture-to-parser, queue, pipeline, capture-to-event
and capture-to-browser-receipt separately. Packet observation time is also
separate. Browser receipt is not paint; same-host wall clocks and a bounded
sample window limit interpretation. There is no hard-latency or line-rate
target. The operational screen needs stopped native capture, prediction and
browser-receipt samples, zero reported drops and no retained-evidence eviction.
Coalescing, pending/evicted receipt counters and missing checkpoints stay visible.

## Run and archive

The server is already running. To launch this exact validation profile later:

```powershell
.venv/Scripts/python.exe scripts/serve_live_policy.py
```

The launcher verifies the frozen real model and exact policy, binds only
localhost 8002, sets explicit local origins/two Torch threads and starts no capture.
It does not rewrite the normal startup default. Collection uses the existing CLI;
the service URL is selected from this fixed plan:

```powershell
.venv/Scripts/python.exe scripts/paired_capture.py --plan configs/ipv6-live-policy-v1.json --root artifacts/local/ipv6-live-policy-v1 status
.venv/Scripts/python.exe scripts/paired_capture.py --plan configs/ipv6-live-policy-v1.json --root artifacts/local/ipv6-live-policy-v1 prepare live-yt-01
.venv/Scripts/python.exe scripts/paired_capture.py --plan configs/ipv6-live-policy-v1.json --root artifacts/local/ipv6-live-policy-v1 --expanded-netlog archive live-yt-01
```

This scope requires the existing bounded expanded offline NetLog profile before
processing, including for YouTube: 1 GiB/8M source events, 256 MiB/2M retained events,
same event types and quality rules. No default live-capture memory budget changes.
Repeat preparation/archival with `live-ig-01` only after YouTube is usable and
Chrome is fully closed. Only after both usable archives:

```powershell
.venv/Scripts/python.exe scripts/paired_capture.py --plan configs/ipv6-live-policy-v1.json --root artifacts/local/ipv6-live-policy-v1 score
```

The offline scorer blocks all older cohorts, public data and network access.
It writes immutable `live-policy-report.json` and `live-policy-predictions.json`
with actual-live and secondary replay results clearly separate, source hashes,
model identity, roles and archive bindings. Neither outcome automatically
promotes the default or fits a policy.

## Software evidence

468 Python tests pass with two existing dependency warnings; 138-file Ruff
lint/format passes. New tests exercise missing live checkpoints versus refusal,
prevent replay from passing a live gate, require real receipt samples, check
frozen policy/weight identity and protect old datasets. Complete constructed
two-visit fixtures test both emitted/missing primary paths and write-once reports;
their reports are explicitly marked fixtures and are not live evidence. The
existing UI remains at its 19-test/TypeScript-build checkpoint. The next evidence
requires the user to Start real capture in the prepared slot.
