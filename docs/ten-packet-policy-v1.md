# Three-service acceptance calibration and later final test

This is a new six-visit protocol for the existing fixed-ten-packet forest. It
does not retrain weights, preprocessing or label ordering. The earlier 16-flow
fresh comparison remains evaluation evidence and cannot fit this policy.

The frozen plan is `configs/ten-packet-policy-v1.json`, SHA-256
`f81457112c67e119878533e6d1c3425ea9fa643480bb20985ec65f75a35ebe0c`.
It pins the source model, successful raw comparison, heartbeat engineering
check and relevant runtime/fitting source files. Collection and results live in
`artifacts/local/ten-packet-policy-v1`.

## What the user records

| Order | ID | Role | Activity |
| --- | --- | --- | --- |
| 1 | ten-policy-cal-yt-01 | Calibration | Different YouTube video, 60 seconds |
| 2 | ten-policy-cal-ig-01 | Calibration | Feed 30 seconds, different Reels 30 seconds |
| 3 | ten-policy-cal-sp-01 | Calibration | Different Spotify artist/album, play 60 seconds; no required skips |
| 4 | ten-policy-final-yt-01 | Final test | Previously unused YouTube video, 60 seconds |
| 5 | ten-policy-final-ig-01 | Final test | Different feed/Reels, 30 seconds each |
| 6 | ten-policy-final-sp-01 | Final test | Different Spotify music, 60 seconds |

Final visits are allowed only if a policy was fitted and frozen, its bundle was
explicitly loaded into the local validation service, and the local date is later
than every calibration visit. Do not collect final visits early. Calibration
visits may span dates without replacing any slot.

Before each preparation, close Chrome fully. Keep the same user-declared phone
hotspot and select Wi-Fi interface 9. After preparation, open normal Chrome and
start a **Strip private information** log at `chrome://net-export`, using the
prepared exact filename. Reference checking stays on and longer observation
windows off. Deliberately click Start once, then navigate to the target service.
Use Chrome normally for 60 seconds with Edge in the background, return to Edge,
and Stop. Stop Chrome logging and keep Chrome open until archive finishes.
Do not refresh or Start again within a visit. Capture has a 120-second cap.

Background use is user-declared; browser visibility is not instrumented here.
The uninterrupted session/delivery checks provide operational evidence, not
proof that Edge was hidden or that every background/sleep state is supported.

## Fixed decisions and failure rules

Each visit requires at least three independently browser-mapped, socket-prefix-QC
target connections reaching ten packets. There is one attempt per slot. Too
little support, bad QC, a restart, retained evidence eviction, drops, viewer
heartbeat/disconnection/process-error termination, or incomplete/evicted prediction
receipt tracking stops the scope. A parser/tool error preserves the same attempt
for diagnosis. No replacement recording or threshold/gate relaxation is allowed.

Fit one global acceptance threshold from 0.00 through 1.00 in steps of 0.01,
choosing the lowest eligible value. Per target service in its own calibration
visit, require at least two accepted connections, at least 50% coverage and zero
accepted errors. Across all independently mapped known-service calibration flows,
including incidental services, accepted error must be at most 10%. All eligible
first-ten inputs are retained independent of prediction. Short and ambiguous
references remain inventoried; they do not gain guessed ground truth.

Only YouTube, Instagram and Spotify can receive accepted labels under this
policy. A top guess among the other seven labels is withheld without changing
the model's original score ordering or its top-three alternatives. This is an
empirical refusal filter, not calibrated probabilities of correctness or
unknown-service detection. A score shown as 80% does not mean an 80% chance of
being right. Other protocols and arbitrary background apps remain outside the
quality claim.

Final testing applies the frozen threshold to entirely new visits without
fitting. The same accepted-error/coverage gates apply to both offline predictions
and actual native live labels. Each role also needs at least 80% actual native
ten-packet checkpoint coverage per target, exact native replay, clean capture
termination and complete receipt tracking. Missing native predictions stay
missing and lower end-to-end coverage. Neither a fitted policy nor a passing
small local final screen automatically changes the general demo/default model.

If calibration has no eligible threshold, it writes a failed decision and no
fitted bundle; final collection is blocked. Six correlated visits on one hotspot
cannot establish population accuracy, unseen-service safety or network transfer.
This procedure has no promise that another recording will improve model weights.

## Commands

From `traffic_classification`, use the existing Python virtual environment:

```powershell
.\.venv\Scripts\python.exe scripts/ten_packet_policy.py preflight
.\.venv\Scripts\python.exe scripts/ten_packet_policy.py status
# If an idle service needs replacing, stop only its verified process first.
.\.venv\Scripts\python.exe scripts/ten_packet_policy.py serve
# Close Chrome, then prepare exactly the next slot:
.\.venv\Scripts\python.exe scripts/ten_packet_policy.py prepare ten-policy-cal-yt-01
# Only after deliberate capture and stopped browser logging:
.\.venv\Scripts\python.exe scripts/ten_packet_policy.py archive ten-policy-cal-yt-01
# Repeat prepare/archive for cal-ig-01 and cal-sp-01, then fit once:
.\.venv\Scripts\python.exe scripts/ten_packet_policy.py fit
# Only if fit passed: replace the verified idle local validation service with:
.\.venv\Scripts\python.exe scripts/ten_packet_policy.py serve --fitted
# On a later local date: prepare/archive the three declared final slots, then:
.\.venv\Scripts\python.exe scripts/ten_packet_policy.py evaluate
```

`preflight` is a write-once metadata inventory: it reads recording intents, not
packet rows. The first run excluded 49 prior intents and found zero eligible
calibration intents. `status` is repeatable. Preparation, serving and tests never
start capture. Fitting runs offline and denies public data, prior private studies,
verification recordings, unrelated experiments and final-visit files. Exported
policy bundles retain the exact forest weights, architecture, normalization and
labels, with new policy metadata, provenance and checksums. `policy-freeze.json`
binds the write-once decision before final preparation; final intents bind its
checksum and fitted artifact identity.

Calibration is now complete as recorded below. Final accepted-label evaluation
is pending. The earlier raw comparison and its Instagram timeout remain unchanged.

Engineering validation: 597 Python tests and 28 UI tests passed, with two existing
Python dependency deprecation warnings. Production TypeScript/Vite build and
targeted Python lint passed. Tests cover infeasible fitting, deterministic
threshold choice, restricted acceptance without score renormalization, invalid
bundle scopes, duplicated/invalid fitting records, denial of old/public/final
inputs, missing-native penalties, and rejection of fixture/timeout/drop/pending
receipt sessions before fitting rows are read. A heartbeat test was corrected
to allow a legitimate queued status before the next heartbeat on reconnection.
These are software checks, not completed calibration or a final traffic result.

The tested local validation service was loaded with the original unfitted
ten-packet source model. It starts idle and ready, and does not capture until
the local user clicks Start. Reload Edge while idle before the next preparation.

## Calibration result, 9 November 2026

All three new calibration visits were archived as usable. There were five
eligible YouTube, four Instagram and five Spotify connections, all correctly
guessed with actual native ten-packet checkpoints. No counted drops, pending
prediction receipts or receipt-tracking evictions were reported. Browser receipt
sample counts were 143, 318 and 169 respectively; these include all emitted
checkpoints, not only the 14 independently mapped calibration connections.
YouTube/Instagram ended at the capture cap and Spotify was stopped by the user;
none ended on heartbeat expiry. This supports normal operation during these
specific user-declared background-window visits, not every browser/sleep state.

One fitting invocation selected threshold **0.0**, accepting all 14 calibration
cases with zero observed errors. This follows the declared lowest-eligible
threshold rule, which was not changed after seeing the result. Crucially, it
does not learn a useful score-based uncertainty cutoff: every top guess within
YouTube/Instagram/Spotify is accepted regardless of score, while other top-label
classes are withheld by the explicit scope. Do not describe this as calibrated
probabilities or reliable confidence rejection. Fourteen correlated cases from
three visits provide little evidence about mistakes or unknown/background apps.

The fitted bundle is frozen **for final validation only**, at
`artifacts/local/ten-packet-policy-v1/policy-bundle`. It has not been activated in
the running service or promoted to the general demo default. The current
unfitted validation service therefore still withholds labels. All model weights,
feature semantics, label order and normalization remain unchanged. No public,
old verification or final-test data were used for fitting.

* Decision SHA-256: `e106e6e11a3522138874976f252e06799f7d25ad03a376f33fbdd813bc3049fc`.
* Fitted artifact ID: `a72fb145943ac3828ab659eb560592a90998f3cbc935f5af04a1547429434573`.
* Forest SHA-256: `b5a312fe86850a93fdc1c7b74cbfb6ffa58009e781888bafa5e47062e6f42adf`.
* Freeze time: `2026-11-09T10:57:32.384744+00:00`.

`calibration-summary.json` records checkpoint/receipt counts and stop reasons;
`calibration-decision.json`, `calibration-curve.json`, `calibration-predictions.json`
and `policy-freeze.json` preserve the complete selection evidence and bindings.
The repeatable status command checks the frozen bundle and reports the next visit
blocked by the date rule. The earliest final-test date is **10 November 2026**
on the same declared hotspot, after the fitted validation profile is explicitly
loaded. No additional calibration recordings or threshold changes are allowed
within this scope. Final testing remains pending; no quality promise is made.

## Final result, 10 November 2026

The three final visits were completed after the policy freeze on a later local
date. The write-once result is `final_failed_stop`: the YouTube visit had one
incorrect accepted label, violating the predeclared zero-error per-service gate.
Offline replay and actual native ten-packet outcomes agreed:

| Target | Eligible | Accepted | Incorrect accepted | Withheld |
| --- | ---: | ---: | ---: | ---: |
| YouTube | 9 | 9 | 1 | 0 |
| Instagram | 6 | 6 | 0 | 0 |
| Spotify | 5 | 4 | 0 | 1 |

The overall inventory has 21 eligible flows, including one incidental YouTube
flow in the Spotify visit: 20 accepted, one incorrect accepted, one withheld.
All three capture sessions stopped by the user, reported zero drops and did not
end on viewer heartbeat expiry. These three visits do not establish general
accuracy. Threshold 0 accepts any top guess within the three-service scope and
provides no score-based uncertainty cutoff. The policy failed the fixed final
screen and must not be promoted as reliable. No threshold was retuned and no
replacement visit was collected.

`final-report.json` and `final-predictions.json` contain the frozen result and
per-flow evidence. Prediction SHA-256:
`104163a9dfb478d22df6617cddfb38d82c90598c2f24200a3534dad73462c52a`.
The idle fitted validation service was stopped after archival and replaced by
the unfitted source service; refresh Edge to load the current model. Capture is
off and the user can close Chrome. Any future work needs a new, separately
declared development/evaluation scope and cannot use this final set for fitting.
