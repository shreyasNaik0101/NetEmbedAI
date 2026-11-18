# Four new visits for the frozen IPv6 candidate

**Current outcome, 6 November:** all four visits are usable and the frozen
[comparison is complete](ipv6-fresh-evaluation-results.md). The added-data forest
gets22/22 flows right at ten packets versus7/22 for the control; target-visit-
balanced recall is1.0 versus0.462121. All three descriptive checks pass. All162
forest vectors replay exactly and eight matrices independently recount. This
small two-service hotspot result is not broad accuracy or fitted confidence.
No more recordings are needed for this scope; the app still runs B17.

This is the next bounded check after the [real-data pilot](ipv6-realdata-pilot.md).
The pilot improved reused development but did not establish accuracy on new
sessions. Here the same control and candidate are frozen before any new packet
is collected. No old training slot is reused or relabelled as evaluation.

Declaration: `configs/ipv6-frozen-evaluation-v1.json`, canonical SHA-256
`dd0723d1dbefc777a586133a71de74a8f2478b2f427ee5d3ff349f02a913e616`.
The config pins both complete bundle identities and forest weight checksums.
Collection root: `artifacts/local/ipv6-frozen-evaluation-v1/`.

## Fixed scope

| Visit | Service | Date |
| --- | --- | --- |
| `ipv6-eval-yt-01` | YouTube | First date |
| `ipv6-eval-ig-01` | Instagram | Same first date |
| `ipv6-eval-ig-02` | Instagram | Later local date |
| `ipv6-eval-yt-02` | YouTube | Same later date |

Use the same user-declared phone hotspot and Wi-Fi interface9. The native
preflight on 5 November confirms global IPv6/default route and bounded TCP443
reachability in both families. It does not identify the hotspot independently,
test UDP/QUIC performance or establish campus-network transfer.

Each visit needs one browser-verified target IPv6 flow with a complete30-packet
prefix, plus the existing packet/socket/reference quality checks. All eligible
supported flows remain archived, including incidental services. This avoids
requiring a single video to create an arbitrary number of connections. Chrome
must be entirely closed before preparation, reopened after the saved intent,
and kept open after stopping the logs until archival checks its lifetime.
No tool starts capture or closes a browser automatically.

Exactly four slots, with one attempt per slot. Genuine quality/support failure
stops this scope; there are no automatic replacement visits. A processor failure
preserves the same capture for diagnosis. Large NetLogs can use the existing
explicit bounded expanded offline profile, selected before processing. No score
or prediction can decide which packets are retained.

## Scoring before any tuning

The scorer waits for all four usable archives, verifies their plan, session,
row, family, browser-proof and file bindings, then loads the two frozen forests.
Training/public data and earlier local outcome archives are blocked during
scoring; network connections are blocked. Source-model replay during archival
checks pipeline consistency only. It does not score either forest.

Primary: raw ten-packet target-service recall, averaged equally over the two
visits of each service and then equally over services. A busy visit receives
the same weight as a quiet one. Incidental local-service flows are reported
as secondary and do not count as target visits. Save both models' complete
probability vectors on identical actual prefixes, with prefix hashes and lengths.
Report5/10/20/30-packet outcomes, all-local confusion matrices, each target visit,
each service and family strata; missing strata remain unavailable.

The descriptive screen requires candidate recall of at least0.80 for each
service, with no primary or per-service loss against the frozen control. A pass
means `promising_fresh_screen`; a failure means `stop_failed_fresh_screen`.
There is no threshold fitting, extra seed, retraining, automatic capture or
model activation after either result. The failed earlier calibration remains
failed. Further calibration would require its own declared data roles.

Only two visits per service on one hotspot are planned. This cannot establish
broad reliability, statistical noninferiority, calibrated probabilities or a
causal IPv6 effect. Correlated prefixes are not independent observations.
Both forests remain uncalibrated and withhold accepted labels. The visible app
still runs B17, so its live guesses are not the candidate evaluation results.

## Operator commands

From `traffic_classification`, with Chrome fully closed before each preparation:

```powershell
.venv/Scripts/python.exe scripts/paired_capture.py --plan configs/ipv6-frozen-evaluation-v1.json --root artifacts/local/ipv6-frozen-evaluation-v1 status
.venv/Scripts/python.exe scripts/paired_capture.py --plan configs/ipv6-frozen-evaluation-v1.json --root artifacts/local/ipv6-frozen-evaluation-v1 prepare ipv6-eval-yt-01
```

The preparation prints the absolute NetLog filename and binds a role before
capture. Reopen normal Chrome, open `chrome://net-export`, keep **Strip private
information** selected, and start logging to that exact filename. In the Edge
app choose Wi-Fi9, reference checking ON, longer-window statistics OFF. Start
capture deliberately, then navigate to a different YouTube video and watch60s.
Stop capture and Chrome logging; keep Chrome open until archival finishes.

```powershell
.venv/Scripts/python.exe scripts/paired_capture.py --plan configs/ipv6-frozen-evaluation-v1.json --root artifacts/local/ipv6-frozen-evaluation-v1 archive ipv6-eval-yt-01
```

Repeat with each next declared slot after preparation, never overwriting logs.
Instagram activity: feed30s, then different Reels30s. The second-date slots
cannot be prepared until the first pair is archived and a later local date
arrives. Read status to distinguish waiting for a log, processing, a stopped
scope or a date gate.

Only when all four visits are usable:

```powershell
.venv/Scripts/python.exe scripts/paired_capture.py --plan configs/ipv6-frozen-evaluation-v1.json --root artifacts/local/ipv6-frozen-evaluation-v1 score
```

The write-once `paired-predictions.json` and `comparison.json` bind both models,
archives, source code and the paired outcomes. No candidate-quality result
exists before these real user-started visits are collected and scored. Software
fixtures test the workflow only; they cannot satisfy the live evidence gate.

## Actual preparation — 5 November

The first YouTube intent was saved at13:34:54 UTC after verifying zero Chrome
processes, source B17 identity, stopped capture and available Wi-Fi9. It is
`prepared_not_capturing`; no evaluation packet collection has started. The
previous stopped training capture was preserved in an excluded-prior subdirectory
and cannot be read by the evaluation scorer. The other three slots are unprepared.
The native preflight report SHA-256 is
`4a26c097d14959140669fd62574b2328778fd136fa0ea7012d3f728bdda3b51b`.

Software verification:438 Python tests pass in16.94s, with two existing dependency
deprecation warnings; Ruff check and132-file format check pass. New constructed
tests cover complete IPv6 support, inventory mismatch, frozen-weight changes,
the all-four-visits embargo, identical paired prefixes, write-once scoring,
target-visit balancing and earlier-data/network blocking. Preparation fixtures
exercise open/closed Chrome for both the older acquisition scope and this scope,
with no capture-start route. No UI change or candidate quality claim follows.

## First actual YouTube visit — usable

Session `a7f1e50501a842929cee16c106eff1db` was deliberately started/stopped by
the user. All four mapped eligible flows are YouTube/IPv6 with30 packets; no
mapped-flow QC exclusions. Reference inventory also preserves5 unmapped,
17 outside-supported,10 ambiguous and1 unmatched connection. Those references
are not silently counted as classified examples. Wi-Fi9/reference ON, longer
windows OFF, zero reported capture drops/reordering and no capture error.
Chrome process lifetimes pass. The source B17 replay has99 vectors, zero changed
accepted labels and maximum alternative-score difference0.0. This checks
consistency of capture and saved inference, not either frozen forest's quality.

Normal bounded offline processing handled the25,307,145-byte NetLog. Its SHA-256:
`88a49e4aa22d15ec16c706ce98cdcf62eb0a08522b7458ddc76a7764bec37669`.
Archive SHA-256:
`171260b352998b0a00e683bbd97c0469d9000ad1f5368254bb852592182fbbea`.
The completion receipt independently rechecks every archived file, original
Chrome-lifetime proof, exact row/family inventory and one-complete-IPv6 support:
`ipv6-eval-yt-01-completion.json`, SHA-256
`9d518bd36dbb02ccdd310333300ffd9f36d1e8a7c397984d13aba7ee62ccd7e7`.
Candidate scoring is not run; no comparison/predictions output exists. No
software implementation changed and the438-test checkpoint remains applicable.
Three visits remain, including today's separately prepared Instagram slot;
the later-date pair remains date-gated and unprepared. No capture starts
automatically and the old training collection remains paused.

## First actual Instagram visit and first-date completion

Session `058ebbb447e34b77880776f2ac39bca3` passes: three mapped Instagram/IPv6
flows with17,30,30 packets, no mapped-flow QC exclusions. Reference inventory
also preserves15 outside-supported,21 ambiguous,3 unmapped,6 unverifiable-session
and2 unmatched connections. They are not silently counted as labelled examples.
Fresh Chrome proof, packet/socket checks and165-vector source B17 replay pass
with zero changed accepted labels and maximum alternative-score difference0.0.
Wi-Fi9/reference ON, longer windows OFF, zero reported drops/reordering and no
capture error. The normal offline profile processed the233,463,779-byte NetLog;
no budget or quality rule was changed.

NetLog SHA-256:
`366c9ef2544c7e0e55e95a57af948e0483cbebe1e5872396fd88cc04beb5708c`.
Archive SHA-256:
`4443eefd5756dc300f0bc081ca970feb12c6827c896f9d68592bdf08f505e110`.
The independent checksum/lifetime/inventory/support recheck is saved as
`ipv6-eval-ig-01-completion.json`, SHA-256
`8611dd3838922cc2f12de031ec1ceb39c43982e908d2529d9aea3fe41f4764d6`.
The first-date receipt binds both archives and completion files, verifies the
next date gate and records stopped capture:
`first-date-completion.json`, SHA-256
`cf5d0ec66aee7e56478c170f94cceb027d3d98755c24c71fed180bec2e57f11e`.

Both current-day visits are usable; neither later-date intent exists. Next is
`ipv6-eval-ig-02`, then `ipv6-eval-yt-02` on the same later local date. Earliest
is6 November2026. Candidate/control scoring remains embargoed; no comparison or
paired-predictions output exists. No fitting, calibration, model activation or
software change follows this archive.438-test checkpoint remains applicable.
Chrome and the laptop may now be closed; no capture or further recording is
required today. These are acquisition-quality results, not classifier accuracy.
