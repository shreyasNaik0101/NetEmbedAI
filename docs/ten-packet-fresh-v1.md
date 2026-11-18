# Three fresh ten-packet visits

This prospective verification follows the narrower reused-development pass. The weights and unfitted policy are frozen before these recordings. It is not calibration, training or final accepted-label evaluation. No previous failed study or unused slot is reopened.

Protocol: configs/ten-packet-fresh-v1.json, canonical SHA-256 5d69cabd395e168a1c06bbebd9f9a7de16d5e82434c203acf7406536c71f8cac.

Collection root: artifacts/local/ten-packet-fresh-v1. Source artifact: fa1f4837e4ae11c9169258ecb20338ae3c0c81c2d206231fb6fe19405b8d8549, weights b5a312fe86850a93fdc1c7b74cbfb6ffa58009e781888bafa5e47062e6f42adf. Control artifact: 9878d0818370ede3e9897a9cc654b4ddc0afcd87d41b2d7134ccaf52592b528a, weights 78efcee31f1ce49a882283b8d4a585bfbc9c0980e40ace68587a98b811d5eecb. All inference comparisons use identical first-ten-packet inputs.

## Three visits only

| Order / ID | Activity in fresh normal Chrome | Role |
|---|---|---|
| ten-fresh-yt-01 | Different YouTube video, 60 seconds | Fresh verification |
| ten-fresh-ig-01 | Scroll feed 30 seconds, different Reels 30 seconds | Fresh verification |
| ten-fresh-sp-01 | Different Spotify artist/album, play 60 seconds; no required skips | Fresh verification |

Each visit needs at least three independently browser-verified target-service connections reaching ten packets. There is no thirty-packet requirement. All eligible mapped rows, incidental services, exclusions, short flows and ambiguous/unmapped inventories remain recorded. Primary metrics use each target service's own visit; incidental traffic is secondary and cannot inflate primary support. Sessions must be distinct, sequential and nonoverlapping; dates may advance without replacing a slot. Each slot allows one stopped capture, no replacement after QC/support failure. A processing error preserves the same bound attempt for diagnosis.

Use the same user-declared phone hotspot, Wi-Fi9, one Edge viewer at http://127.0.0.1:8002, reference ON and longer windows OFF. Chrome must be fully closed before preparation; reopen normal Chrome afterward. Start Strip private information NetLog, then deliberately Start app capture, then navigate the target. After starting playback, keep Edge visible/foreground while Chrome stays open. Stop app and browser logging, then keep Chrome open until archival verifies process lifetimes. Do not refresh or restart capture during a visit. Refresh the existing Edge viewer once while idle after the validation service changes, so its model metadata is current.

The model shows no scores before ten packets. Thereafter it shows experimental alternatives while accepting no labels, because its policy is unfitted. At twenty/thirty observed packets it still uses only the first ten; those events are not extra model evidence. User-selected tabs and browser names never enter inference.

## Fixed gates and measurement

After all three usable visits, score once. For every primary service require offline candidate recall at least 0.80 and no correct-count loss to the matched control. Spotify additionally needs at least one more correct primary case than control. Separately require actual native ten-packet checkpoint coverage at least 0.80 and native raw correctness divided by all eligible target flows at least 0.80. Missing checkpoints remain missing; offline replay cannot fill them.

An operational pass requires zero reported drops, no retained-evidence eviction, real timing/receipt samples and source-prediction replay parity. Counted event drops can retain independently QC-verified offline packets but cannot pass the clean operational gate. Raw/native gates and operational measurements are reported separately, and all are needed for full screen pass. Any failure closes this scope without extra slots, seeds, relaxed gates or threshold fitting.

Timing reports distinguish actual target ten-packet prediction processing/event times from all-event receipt summaries. The latter also include five-packet no-score events and repeated first-ten scores at later observation checkpoints. Same-host browser receipt is not paint, and no hard real-time bound is claimed. Confidence calibration and later accepted-prediction verification need separate, subsequently frozen data; these verification visits must never be used to fit them.

## Commands and safeguards

From traffic_classification:

```powershell
.\.venv\Scripts\python.exe scripts/ten_packet_fresh.py status
.\.venv\Scripts\python.exe scripts/ten_packet_fresh.py serve
# After the user closes Chrome and confirms the declared hotspot:
.\.venv\Scripts\python.exe scripts/ten_packet_fresh.py prepare ten-fresh-yt-01
# Only after the user deliberately captures and stops logging:
.\.venv\Scripts\python.exe scripts/ten_packet_fresh.py archive ten-fresh-yt-01
# Repeat declared prepare/archive slots in order; after all three:
.\.venv\Scripts\python.exe scripts/ten_packet_fresh.py score
```

Serve never starts capture. It validates both genuine frozen models and uses explicit localhost origins. Stop only a verified idle previous validation process before serving; no launcher kills a browser or starts traffic collection. Normal local process access is required for TShark, not a paid service or administrator setting change. Archive uses the existing bounded expanded NetLog profile and unchanged reference/socket-prefix QC. Audit now safely compares empty short-input alternative lists. Scoring blocks public datasets, old/private cohorts and unrelated experiment outcomes; no fitting code is called.

Implementation checks: 562 Python tests pass with two existing dependency warnings; active lint and 154-file formatting checks pass. Tests cover support, role/session/date order, Chrome preparation open/closed without capture, native missing-checkpoint penalties, incidental-flow isolation, empty-alternative audit parity and protected-input guards. The capture export now retains model packet budget, policy state and actual per-checkpoint event timing fields; a constructed event test verifies those fields survive export storage. This was fixed and the never-capturing service reloaded before any visit preparation. UI is unchanged from its 24-test/build checkpoint. The new validation service was readied on 9 November with the correct artifact, fixed prefix ten, policy unfitted, Wi-Fi9 available and capture stopped. The old stopped service evidence was preserved under excluded-prior-a2477a50fade4d398057e7378f3ea962 and is excluded from scoring.

## First visit interrupted: integrity review required

The first intent was prepared after closed-Chrome proof at 2026-11-08T18:56:08.207490+00:00 (9 November locally). The validation server subsequently logged a successful Start, viewer connection closure, a replacement viewer connection, a second successful Start and a user Stop. The first session was not archived before the second Start; only the latest session remains in the live API. The single-attempt protocol cannot grade a replacement session as its first visit.

Latest stopped session 45519e9b8ca442289f4ffda6f2a6d207 contains two connections with thirty and twenty-seven retained packets, seven acknowledged prediction events, zero reported drops and no capture-process error. The frozen counter is 6,628, recording additional packets beyond retained early-prefix limits; this is not a complete packet dump. It demonstrates that capture received traffic, not that the browser-reference QC or three-flow target support passed. No service identity or model-quality verdict is assigned until separate diagnostic processing.

Status, capture, timing and model snapshots are preserved under artifacts/local/ten-packet-fresh-v1/technical-interruption-45519e9b8ca442289f4ffda6f2a6d207. session-integrity-review.json records hashes and the observed server-log sequence. Preparation, prospective archival and scoring now refuse to continue while that review marker exists, and status reports session_integrity_review_required. This preserves the one-attempt rule; it does not request another recording or silently reset the visit. A constructed regression test checks that grading is blocked before loading models or accepting replacement evidence. Diagnostic NetLog finalization/inspection can proceed on this same stopped recording.

The current source remains a deliberately selected validation profile; B17 and the existing demo model decision remain separate. No fresh three-service screen, calibration or accepted-label validation has completed. Three visits, one per service on one declared hotspot, would not establish population reliability or new-network generalization even if all gates passed.

The stopped log has now been [processed diagnostically and recovery improved](capture-session-recovery.md). One browser-verified YouTube connection passes socket-prefix QC and its ten-packet guess was YouTube; the other connection is outside the supported set. All seven saved events replay exactly. This does not restore the lost first capture or meet the three-flow minimum. The service now retains three stopped sessions across later Starts, and records viewer-close details. No replacement capture or fresh-screen pass is claimed.
