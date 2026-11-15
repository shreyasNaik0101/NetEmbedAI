# Revised hotspot acquisition: fresh browser sessions

**Current status, 5 November:** acquisition is paused after the three usable
visits below. Their 19 verified IPv6 flows were explicitly adopted for the
[single real-data training pilot](ipv6-realdata-pilot.md), which completed with
promising development results. The six-visit plan is not declared complete.
The remaining three slots are unprepared; instructions below to continue them
describe the earlier acquisition checkpoint, not a current recording request.

## Second YouTube visit archived — 5 November

**YouTube session2 passes:** seven matched IPv6 flows, all30 packets, with packet
QC, fresh-Chrome proof and source replay passing. Three of six planned visits
are usable (two YouTube, one Instagram). Next is `fresh-ig-02`, after a separately
verified Chrome exit and preparation. No model fit/evaluation has occurred.

Session `f99fe6fc82b5474f8e6ae697630e18b8` is usable. Mapped-QC exclusions are
empty. Reference inventory preserves23 outside-supported,10 ambiguous,5 unmapped
and2 unmatched connections. Wi-Fi9/reference ON, zero reported drops/reordering
and no capture error. Chrome lifetimes validate against the intent/first packet.
Source replay matches134 saved predictions with zero changed labels and maximum
alternative-score difference0.0. This is acquisition/pipeline consistency, not
a model-quality result. The log is37,747,541 bytes, SHA-256
`58d1cd23f0cb1cf9a3035e25c96e5608423e7c20b9613ce1a136efed6b634478`.
Normal bounded offline processing sufficed.

Evidence root: `artifacts/local/hotspot-fresh-sessions-v1/`. Archive SHA-256:
`e6dfe59c84147e49d924975be625770c5b04e59d2bc00d64c2e013b8cc7792a6`.
`fresh-yt-02-completion.json` SHA-256:
`a123996667df2f4634978d2897f0d87f3c9ebd5d75e88d501ad17135432895a6`.
Completion independently rechecks archive hashes and browser lifetimes.
Next are `fresh-ig-02`, `fresh-yt-03`, `fresh-ig-03` on this same later date,
each separately prepared after Chrome exit. No next intent, model training,
freeze, evaluation or promotion starts automatically.412-test software checkpoint
unchanged; private evidence/documentation changes only. Earlier checkpoints below
preserve their original state.

**5 November readiness:** IPv4/IPv6 connectivity was rechecked successfully,
capture was stopped and zero Chrome processes were verified. `fresh-yt-02` is
prepared at `2026-11-05T11:53:51.715856+00:00`; no capture starts automatically.
Today's additional network preflight is bound in
`fresh-yt-02-network-preflight.json` (SHA-256
`a22153c97b5be7ed72b63e4c94e2ce9d65ed48e723bc0ff6ee81d75dbb6fdb78`).
The next three slots still await separate preparation/archival on this date.
The first-date checkpoint below preserves its original state.

**Both first-date visits now pass.** YouTube has six complete IPv6 flows.
Instagram has four IPv6 flows (three30-packet and one16-packet), plus two
incidental complete YouTube flows. These count as one planned visit per service.
No more recording on4 November: the remaining four visits must occur on the
same later local date,5 November or later. All future intents remain unprepared.
Chrome may be closed now; browser-lifetime evidence is archived.

**First actual session passed:** `fresh-yt-01` contains six browser-matched
YouTube IPv6 flows, all30 packets, with fresh-Chrome proof and packet QC passing.
This counts as one verified visit, not six independent sessions or an accuracy
result. The next slot is `fresh-ig-01`, which still requires a new closed-Chrome
preparation. No Instagram intent is created automatically.

The previous hotspot visit captured two valid YouTube IPv6 QUIC flows. Its
three-connection gate failed because watching one video does not guarantee
three new connections. This new, explicitly revised scope uses the **visit** as
the acquisition unit. It does not relabel earlier failures as passes or count
their flows toward fresh-session support.

## Fixed scope

At most six user-started visits, three per service over two local dates:

| Order | Slot | Date group | Activity |
| --- | --- | --- | --- |
| 1 | `fresh-yt-01` | First date | Different YouTube video,60s |
| 2 | `fresh-ig-01` | First date | Feed30s, different Reels30s |
| 3 | `fresh-yt-02` | Later date | Another video,60s |
| 4 | `fresh-ig-02` | Same later date | Different feed/Reels |
| 5 | `fresh-yt-03` | Same later date | Another video,60s |
| 6 | `fresh-ig-03` | Same later date | Different feed/Reels |

Each visit needs **one matched target-service IPv6 flow reaching30 packets**.
All eligible flows are retained, rather than selecting the best-looking one.
The same reference matching, unique-socket, missing-packet, within-direction
payload and native source-replay checks apply. Classifier output/confidence
does not determine eligibility. Three passing visits per class provide at least
three distinct capture/browser sessions; those sessions remain correlated by
network, user and dates and are not statistically independent population samples.

One stopped attempt per slot. Genuine QC/session/coverage failure stops the
scope; processor failures preserve the same captured attempt for continuation.
There are no automatic replacement visits. Completion only establishes an
acquisition set. No fitting, scoring, training freeze, calibration, final test
or promotion follows automatically. Future training/evaluation requires its
own bound declaration. Existing closed campus/hotspot/calibration roles remain
unchanged. B17 stays in the app.

Machine declaration: `configs/hotspot-fresh-sessions-v1.json`, canonical SHA-256
`8d457350c09f8dfeaac13d30f792bd073f4ab41490d4dca8c737b01c285e8a2d`.
The revised one-flow threshold applies only to this new scope. Tests verify the
old three-flow scope still rejects a one-flow visit.

## Freshness checks and user procedure

Before every preparation, the user saves any needed tabs and fully exits Chrome
using its menu. Edge and the local app can remain open. The collector queries
Windows Chrome process lifetimes, refuses to prepare while any Chrome process
exists, and never closes or launches a browser itself. A new intent records
that closed-browser check, the immutable plan, network proof, interface, role,
source model, timestamp and prior excluded capture session.

After receiving confirmation that the intent is prepared:

1. Stay connected to the phone hotspot. Reopen normal Chrome, keeping old
   YouTube/Instagram tabs closed so they do not preload target connections.
2. Open `chrome://net-export/`, keep Strip private information and start logging
   to the prepared slot's filename, such as `fresh-yt-01-netlog.json`.
3. In the Edge app choose Wi-Fi, Reference evidence ON and longer windows OFF.
   Press Start, then navigate to the slot's target and do its60-second activity.
4. Stop the app, then immediately Stop Logging in Chrome. **Keep Chrome open
   until the archival check completes.** Report “saved and stopped.”
5. Only after archival confirmation, save tabs and exit Chrome for the next
   separately prepared visit. Do not record slots in advance.

At archival, a bound private process snapshot verifies every currently running
Chrome process began after the intent, and that at least one existed before
the first retained capture packet. Renderer processes may start later. A browser
reopened only after capture cannot supply a valid lifetime proof. Missing/stale
proof is not silently accepted. PIDs/start times remain private protocol metadata,
never classifier inputs. This checks the stated restart procedure, not an
independent browser-profile fingerprint or statistical independence. It currently
requires Windows; unavailable native inspection fails explicitly.

## Commands and readiness

```powershell
.venv/Scripts/python.exe scripts/paired_capture.py --plan configs/hotspot-fresh-sessions-v1.json --root artifacts/local/hotspot-fresh-sessions-v1 status
.venv/Scripts/python.exe scripts/paired_capture.py --plan configs/hotspot-fresh-sessions-v1.json --root artifacts/local/hotspot-fresh-sessions-v1 prepare fresh-yt-01
.venv/Scripts/python.exe scripts/paired_capture.py --plan configs/hotspot-fresh-sessions-v1.json --root artifacts/local/hotspot-fresh-sessions-v1 archive fresh-yt-01
```

The first intent is now prepared at `2026-11-04T13:05:49.535485+00:00` after
verifying zero Chrome processes. Closing windows initially left13 background
processes; the user deliberately exited those, then the closed-browser check
passed. No process was terminated by the assistant. The intent excludes prior
session `94895a1f0d79402681ca92ccfff570c1` and binds the recorded closed-browser
proof. `first-intent-checkpoint.json` preserves this readiness change separately
from the earlier engineering checkpoint. No automatic recording starts.
Use `fresh-yt-01-netlog.json` for this visit and keep Chrome open after stopping
logging until archival completes. After all six passing archives, status is
`session_acquisition_complete_no_scoring`; generic scoring and training freeze
are explicitly blocked for this scope.

The current hotspot was rechecked without capture/settings changes. IPv4/IPv6
TCP both connect, with global IPv6 addresses and a default route. Private proof:
`experiments/fresh-session-hotspot-check-v1/report.json`, SHA-256
`90624fe303cc7662535654e25771a1859da422332720add4f8867f7e53cdac17`.
The network remains user-declared and differs from the institutional network;
successful acquisition here does not establish campus generalization.

## Verification

Implementation commit `1f8eac3`.412 Python tests pass with two existing dependency
deprecation warnings in39.48s. Ruff lint/format pass for127 files. Tests exercise
fresh/old/missing process evidence, late browser restart, closed-browser gating,
one-complete-flow support, preserved old thresholds, session/date separation
and completion without scoring or training freeze. A native Windows smoke test
also verifies the actual PowerShell process query. Its initial formatting bug
was detected and fixed before any capture/intent; the passing native check and
full run follow that correction. No browser was killed or launched by a test.

Private engineering evidence is at
`experiments/fresh-browser-session-engineering-v1/`. The completion record binds
the network proof, native query, source hash, tests and unchanged earlier failed
receipts. Its SHA-256 is
`a685dc75a56044c995eb60caa8af721121c91c49c8f704b2bcc0286d69fd4468`.
No new live recording, trained artifact or quality result exists for this scope.
UI remains at the earlier17-test/build checkpoint; no hosted CI/other OS claim.

## First YouTube visit archived

Native user-started session `961d7bd1770043b78ac19a24d33c54a3` is usable under the
fixed new declaration. All six retained mapped flows are YouTube/IPv6 with30
packets each; mapped packet-QC exclusions are empty. Reference inventory also
preserves16 outside-supported,7 unmapped,10 ambiguous and1 unmatched connection.
Queue drops/reordered packets are zero and no capture error is recorded.
Browser socket matching, within-direction payload checks, source replay and
fresh-process checks pass. All current Chrome processes started after the intent,
and a Chrome process existed before the first retained packet. The bound private
process snapshot preserves those times. This supports the restart procedure,
not statistical independence or full exporter parity.

The native-source replay compares107 saved predictions, with zero changed
decision labels and maximum alternative-score difference0.0. This confirms
reproducible source inference; no new candidate accuracy evaluation was run.
The Chrome log was saved directly at the prepared path:32,253,471 bytes, SHA-256
`f52e84ba9dad773478c44a05c604c78a010e4a02a54a37c06d1b39f009e12009`.
Its browser reference and native packet evidence are preserved unchanged.

Evidence root: `artifacts/local/hotspot-fresh-sessions-v1/`.
`fresh-yt-01-archive.json` SHA-256:
`9c6c2513496a52fe7ebe4f82a9fd3b7dc25c0ff6472d90adc15af67f33002cde`.
`fresh-yt-01-completion.json` SHA-256:
`10850fdd78cd5c80d76122dcf857dc323a77277c2d1df60e41ee17e7a7b69b40`.
The completion independently revalidates archive hashes and process lifetimes.
All later slots remain unprepared. The model has not been retrained and no
scope completion, quality claim or default promotion follows this one visit.
The412-test software checkpoint is unchanged; this result changes private
evidence and documentation only.

## First Instagram visit and first-date completion

Session `f343c785ede54a3a814a0173e74fb800` is archived as usable. Four mapped
Instagram flows are IPv6 with lengths16,30,30,30. Two matched YouTube IPv6 flows
of30 packets also remain in the export; they do not substitute for a reserved
YouTube browser session. No mapped flow was excluded by packet QC. Source
inventory preserves33 ambiguous,17 outside-supported,6 unmapped and3
unverifiable sessions. No unsupported reference was silently assigned a label.

Wi-Fi9/reference ON, zero queue drops/reordered packets and no capture error
were recorded. The closed-Chrome intent and process-lifetime proof validate
independently. Native-source replay compares191 saved predictions with zero
changed decision labels and maximum alternative-score difference0.0. This checks
source inference consistency, not quality of a new model.

The completed log is372,390,088 bytes, SHA-256
`031eed091d2dc4aeea5516cf595c98e408c476158e995732304d68a3bc9ef35e`.
Its size exceeds the normal256MiB source budget, so the existing explicit
`expanded-offline-v1` profile was selected before processing. Actual scan:
1,842,439 source events,596,513 retained reference/socket events,125,150,990
encoded retained bytes. Bounds are1GiB/8million source events and256MiB/2million
retained events. Every selected event type is retained; no prediction, label,
origin, connection or time filtering is introduced. Reference/packet/support
gates and normal application limits are unchanged. This resource-heavy offline
reference analysis is separate from live inference latency.

Command used:

```powershell
.venv/Scripts/python.exe scripts/paired_capture.py --plan configs/hotspot-fresh-sessions-v1.json --root artifacts/local/hotspot-fresh-sessions-v1 --expanded-netlog archive fresh-ig-01
```

The unchanged packet data, source log, browser proof and outputs remain under
`artifacts/local/hotspot-fresh-sessions-v1/`. Archive SHA-256:
`c85084c79e8ec4df4c90ba9505304d7a3c8c8bbd9b2e6ac8ebc92812fc0bab37`.
`fresh-ig-01-completion.json` SHA-256:
`fcd86a867a17a04d928443d6167f13547c8db72c75d6ff9847258762c38397ce`.
Completion revalidates archive hashes/process lifetimes and records actual reader
limits. Both first-date visits are usable. Resume at `fresh-yt-02` on a later
local date; no further slot is prepared today. No training freeze, fitting,
quality evaluation or promotion occurred.412-test software checkpoint unchanged.
