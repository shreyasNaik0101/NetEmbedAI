# Explicit follow-up after the missing-evidence attempt

**Completed:** all four visits are archived and the frozen comparison has run.
See [results and evidence](prospective-paired-followup-results.md). The primary
ten-packet endpoint ties at 20/22 correct for both models. No policy or default
change follows. The declaration and preparation history below are preserved.

The [original study](prospective-paired-study.md) remains stopped, with its
third attempt and zero retained native flows preserved. The separate
`configs/prospective-paired-followup-v1.json` declaration allows exactly two
new sessions: `paired-yt-followup-01`, then `paired-ig-followup-01`, on the same
later local date. No extra replacement follows if either is unusable.

The two prior usable visits are inherited by exact archive hashes and unchanged
evidence files. They were collected after the fixed models existed, and no
candidate predictions were inspected on them. They are not represented as
newly collected after this follow-up declaration. Candidate weights, support/QC,
ten-packet session-balanced primary comparison, secondary budgets, thresholds
and the four-visit scoring embargo are unchanged. No fitting, confidence policy
or promotion is authorized by this follow-up.

The declaration's LF-canonical SHA-256 is
`c8aed9b2c6fe1138e574b8e6af8a8c9d7ddbb3ba62b57359922e829b37f6f289`.
The inherited archive hashes are pinned in that declaration, validated before
preparation/scoring and checked against their original plan identities. New
sessions must follow this new declaration's timestamp. Status understands both
inherited and new archives without changing the original study's rules.

The separate working root is `artifacts/local/prospective-paired-followup-v1/`:

```powershell
.venv/Scripts/python.exe scripts/paired_capture.py --plan configs/prospective-paired-followup-v1.json --root artifacts/local/prospective-paired-followup-v1 status
.venv/Scripts/python.exe scripts/paired_capture.py --plan configs/prospective-paired-followup-v1.json --root artifacts/local/prospective-paired-followup-v1 prepare paired-yt-followup-01
.venv/Scripts/python.exe scripts/paired_capture.py --plan configs/prospective-paired-followup-v1.json --root artifacts/local/prospective-paired-followup-v1 archive paired-yt-followup-01
```

Only after that archive passes, prepare/archive `paired-ig-followup-01` with the
same flags. Score only after all four usable visits, using those flags and
`score`. The original roots stay unchanged. All failed attempts remain visible;
no candidate result selects which recording to retain.

Before Start, refresh the Edge app to load the rebuilt UI. The setup area now
displays **Reference evidence OFF** or **Reference evidence ON** outside the
collapsed research panel. Expand **Optional research tools** and explicitly
enable **Check predictions against a separate handshake reference**. Verify
the visible ON message before Start. The explicit choice is remembered across
refreshes in that browser tab using session storage; a new tab still defaults
off. Storage failure falls back to the visible checkbox without auto-enabling
anything. Capture still starts only when the user presses Start.

Keep longer-window statistics off. Begin Chrome logging to the exact prepared
path, then Start capture before opening a fresh target tab. Watch the different
YouTube video for 60 seconds. Stop capture and Chrome logging. On the final
Instagram visit, use feed for 30 seconds then Reels for 30 seconds. Keep normal
Chrome and Edge visible and archive each visit before proceeding. The app still
displays B17; selected candidates are compared offline only after collection.

Actual preparation completed on `2026-11-01T12:01:50.978229+00:00` without
starting capture. The two inherited archives revalidated and were copied
byte-for-byte. The first new slot's intent SHA-256 is
`f9d139df60e1f34f8a05b181e34519f1a2b5cb8fad9dfcb6f018663f51389b7c`.
Its exact NetLog path is
`C:\Users\shrey\NetEmbedAI\traffic_classification\artifacts\local\prospective-paired-followup-v1\paired-yt-followup-01-netlog.json`.
`preflight.json` binds preparation and the UI index hash. The service's HTML
matches the rebuilt UI index; refresh the browser to load that build.

The implementation/declaration were committed as `0cf18d4` before preparation.
354 Python tests, 17 UI tests, production build, lint and formatting pass.
The first sandboxed UI test/build could not spawn esbuild (EPERM); the same
commands succeeded under the approved local-process execution. No hosted CI or
new live-capture result is claimed. No candidate results were inspected.

## YouTube follow-up archived; final Instagram prepared

The new YouTube session `47a37b661c784363b2f6b5fd49a01cb8` is usable.
Reference evidence was enabled; all four mapped YouTube connections reach
thirty packets, giving sixteen available prefix cases. No mapped flow was
excluded for packet quality. The remaining inventory preserves seven ambiguous,
thirteen outside-supported, four unmatched and three unmapped connections.
Native/socket consistency and original B17 replay pass. This is collection/QC
evidence; candidate performance remains unscored.

The Chrome log was found in the previous study folder. A byte-identical copy
and a location sidecar preserve both paths, SHA-256
`584bba8cc14949870b576be595b8dc1cd4661683aae3886ff090a71e10f70fac`.
No capture replacement or data transformation was needed. Archive SHA-256:
`46355eaac3bf167ec557380523278d01155cca8c126891d6c5f32706a9772486`.
`checkpoint-youtube-archived.json` verifies the archive, support and final intent.

Three of four visits are now usable, including the two immutable inherited
visits. The final `paired-ig-followup-01` slot was prepared at
`2026-11-01T12:12:45.542267+00:00` without starting capture. Its intent SHA-256 is
`d70140985a48d287bc30b2546219318a196da6a27740b2685263c51fa57efd37`.
It must be recorded on the same UTC+05:30 date as this YouTube visit. Paste the
entire new path into Chrome's Save dialog:
`C:\Users\shrey\NetEmbedAI\traffic_classification\artifacts\local\prospective-paired-followup-v1\paired-ig-followup-01-netlog.json`.
Actual final capture, archival and paired scoring remain pending. No source
code changed or tests were repeated for this evidence-only checkpoint.
