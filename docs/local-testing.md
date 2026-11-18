# Testing on your laptop

The latest [explicit follow-up](prospective-paired-followup.md) preserves the
stopped original study and the two usable recordings, and declares two new slots.
Follow its prepared paths. Refresh Edge to load the rebuilt UI, enable the
reference checkbox and verify the visible **Reference evidence ON** message
before Start. The selected choice is now remembered on refresh within that tab;
a new tab defaults off. This supersedes the old UI-reset behavior described below.

The prospective paired study is now **stopped** after its third attempt had
reference checking off and retained zero native flows. Preserve that attempt;
do not repeat it or start slot 4 under this plan. New collection needs a new scope.
For future referenced captures, verify **Check predictions against a separate
handshake reference** under **Optional research tools** immediately before Start.
A page reload initializes this option to off; enabling it after capture cannot
restore missing evidence. Stop both capture and Chrome logging and use the exact
prepared log path.

For the current prospective study, check collection readiness with:

```powershell
.venv/Scripts/python.exe scripts/paired_capture.py --root artifacts/local/prospective-paired-log-recovery-v1 status
```

This verifies saved evidence and displays the next date/slot without starting
capture or computing candidate predictions. Follow the
[four-visit protocol](prospective-paired-study.md) before preparing another visit.
The original collection root preserves the premature archive failure; use the
documented continuation root for this study's remaining sessions.

New experimental option: the [approach comparison](approach-comparison.md)
documents the current results and pending gates. **Collect experimental 1- and
3-second statistics** defaults off. When selected before a deliberate Start,
the same live screen counts beyond the model's thirty-packet prefix and shows
window statistics separately. Stop, then **Download observation windows** to
preserve them before the next Start. This tests collection/display only; it
does not run a trained activity or longer-window service model. Keep this
experiment separate from the fixed version-3 development recording protocol.

The latest [Instagram diagnostic](instagram-trial.md) is saved and complete.
It exposed confident model errors, so repeating the same visit is not needed
now. Capture automatically stops at its two-minute limit or after the viewer
disconnects for ten seconds. Earlier versions combined those stop reasons;
the saved session cannot distinguish them. Automatic stop retains the bounded
evidence report. A normal `N packets captured` TShark shutdown line is not a
capture failure.

The live path works, but an app visit does not label every connection on the
laptop. Unexpected predictions could be background traffic **or model errors**.
Repeating an unlabelled YouTube visit cannot distinguish those explanations.

For the ECH/GREASE refusals observed on this laptop, use the new
[browser connection-log workflow](browser-attribution.md) with a fresh export.
Do not keep repeating the passive-only trial. The first real Chrome-log trial
matched four YouTube connections, mostly withheld decisions, and exposed confident
labels on references outside the supported set. Its complete results and local
artifact checksums are in the browser workflow guide. It is a diagnostic session,
not evidence that arbitrary local services are reliably recognized.

## One useful check

1. Refresh NetEmbedAI in Edge. Keep its tab open. Select the active Wi-Fi
   interface and confirm **MODEL LOADED** and **stream connected**.
2. Tick **Check predictions against a separate handshake reference**. This is
   optional and starts off. It lets TShark inspect a visible QUIC handshake name
   and match it to CESNET's historical service map. The name never enters the
   predictor; only packet sizes, directions and gaps do.
3. Press **Start capture** before opening a fresh supported service connection.
   For example, open YouTube in a new Chrome private window and play a video.
   A private window is optional; it helps create a separate browsing session.
   QUIC is not guaranteed: TCP/TLS, missing handshakes and unsupported flows are
   skipped rather than assigned a QUIC label.
4. Return to NetEmbedAI and click a new **ARRIVING FLOWS** row that shows
   **Reference: youtube**. Inspect its packet table and the **MODEL DECISION**.
   The separate reference panel reports agreement, disagreement or a withheld
   model decision. A different reference does not change the model's output.
5. Press **Stop**, then **Download local trial evidence** to keep the bounded
   feature/prediction report. When working with this agent, the same report can
   be read locally through `/capture/local-evaluation`; no manual download is
   needed unless you want your own copy.

If no row has a mapped reference, report that outcome. Do not select a convenient
prediction and declare it the target app. Missing or encrypted names, historical
map gaps, shared infrastructure and overlapping rules can prevent attribution.
The interface deliberately shows those cases as unverified, ambiguous or outside
the supported set. A hostname-map reference is evidence of a service category,
not proof of a browser tab, user action or message content.

An ECH/ESNI indication is handled conservatively as **protected name unverified**.
It does not prove that the name was encrypted: browsers can send a GREASE ECH
extension that looks like real ECH (see [RFC 9849, section 6.2](https://www.rfc-editor.org/rfc/rfc9849.html#section-6.2)).
This may prevent the reference checker from attributing otherwise visible traffic.
Do not disable browser privacy/security settings to make a demo succeed. If all
references are unverified, stop repeating the same trial; browser-side connection
attribution or another independent label source is needed before scoring it.

The original map comes from CESNET-QUIC22 version 3, with published MD5
`89b5080480db4be0c31bbbbdedd62451`. The packaged copy's SHA-256 is
`90041edb9cb760265ca8fcdaaa3b1ed6138c7a4c44d3f07b2f063b75776cc5c3`.
Full attribution and CC-BY-4.0 license links are in
`src/netembed/reference_data/ATTRIBUTION.md`. Pattern matching is conservative:
`*.example.com` requires a preceding hostname label, suffix boundaries are
checked, conflicting matches and detected ECH/ESNI are unverified.

## Reading the results

- **Collecting:** the next supported prefix has not arrived yet.
- **Insufficient confidence:** the model's top score is below its saved 0.67
  threshold. An alternative such as WhatsApp is a score, not an accepted label.
- **Model differs from this reference:** a model error is plausible on this
  attributed flow. Keep it in the report; don't dismiss it as background traffic.
- **No visible mapped reference:** no defensible label is available for this
  flow. A browser visit by itself cannot fill the gap.

Predictions update at 5/10/20/30 packets. Newer pending checkpoints may coalesce,
and the first window stops growing after 30 packets. This is intentional; a
streaming video can continue while the early-window result stays fixed.
Percentages are model scores, not guaranteed probabilities of correctness.

## What the evidence contains

With reference mode on, at most 256 flow windows and four prediction checkpoints
per retained flow stay in memory. The report includes the separate reference
status/category, the actual raw metadata and model identity/scores, explicit
denominators and prefix agreement/coverage counts. It omits observed hostnames,
addresses and payload contents. Grouping addresses are transient and clear on
Stop. A new Start or service exit discards this evidence unless explicitly saved.
`evidence_evicted` reports any bounded-history loss; retained rows are not silently
presented as the entire session. Default capture does not collect the reference
fields or keep these diagnostic feature snapshots.

The timing summary separates parser, queue, model and emitted-event delays.
Browser receipt is timestamped in the WebSocket handler and includes event-loop
delivery delay. It is not a measured paint timestamp. Report p50/p95 and sample
count; don't interpret a single run as a hard latency guarantee.

## Before claiming local accuracy

First use exploratory sessions to audit feature parity and reference availability.
For a later evaluation, predeclare at least two available supported services and
a fixed number of fresh sessions. Keep collection/development and held-out
sessions separate. Freeze any adapter changes or local adaptation before the
held-out trials. Save every trial, including failures and unsupported/background
flows, and report mapped/unmapped/ambiguous counts plus retained-flow limits.
Report results by prefix and service, with refusals and a stated denominator.
The JSON's `agreement_by_prefix` is **agreement with the hostname map among
retained referenced predictions**, not general app accuracy.

If attributed flows are misclassified, inspect raw feature units, direction,
first-packet semantics, coalesced/jumbo datagrams, capture point and independent
ipfixprobe parity before retraining. Small local trials cannot replace the frozen
CESNET test. Never change predictions using hostnames, process names or the app
the user intended to open.

The diagnostic helper below reads only the training partition, compares feature
distributions, and replays unchanged versus floor/nearest-millisecond timing on
saved opted-in metadata. These are exploratory sensitivity checks, not validated
exporter rules or changes to inference. No local accuracy can follow without labels.

~~~powershell
.venv/Scripts/python.exe scripts/audit_local_trial.py --evidence experiments/full-real/live-reference-ech-20261025.json --data data/processed/v2 --bundle experiments/full-real/20261024-151720-3532794c/bundle --output experiments/full-real/live-reference-ech-20261025-audit.json
~~~
