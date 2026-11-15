# Showcase consolidation checks — 10 November 2026

The README, demo runbook, beginner interview guide and showcase model card now
lead with the current local evidence and the failed acceptance-policy screen.
Historical README, runbook and guide content is preserved separately. The UI
shows a visible prototype notice explaining that model labels are not proof of
local reliability and scores are not correctness probabilities. The existing
`App.tsx` was not changed by this notice, preserving source bindings used by
the completed local policy study.

The local launcher `scripts/serve_showcase.py` checks the declared genuine,
unfitted fixed-ten artifact identity and configures loopback origins for its
selected port. A real local launch on port 18317 returned ready and reported
capture off; it was then cleanly shut down. The existing service at port 8002
was separately checked via HTTP: it had the same unfitted artifact, served the
built UI including the notice, produced a valid ten-packet fixture response
without an accepted label, and remained idle. These checks did not start real
capture or establish classification accuracy. Port 8000 was already occupied
by a service with no ready model, so no unknown process was stopped.

The deterministic local archive is
`artifacts/local/showcase/netembed-ten-packet-unfitted.zip`, SHA-256
`019369d9c9f88261fc3892a17facb92efaf4e3b7031ef80fd92a53890088a9be`.
Its extracted bundle identifies artifact
`fa1f4837e4ae11c9169258ecb20338ae3c0c81c2d206231fb6fe19405b8d8549`.
`scripts/check_showcase_archive.py` validated the inventory and loaded the
extracted bundle with training, local-capture and experiment paths denied. It
used a constructed packet input and checked unfitted label withholding and
first-ten invariance; this is an inference contract check, not benchmark data.

The full Python suite passed **633 tests** with two dependency deprecation
warnings before the final standalone archive-check helper was added. That
helper and launcher then passed their six focused tests. **29 UI tests** passed;
the production TypeScript/Vite build, Python lint, UI formatting and current
documentation link checks passed. The policy status command now verifies the
saved decision/prediction/archive bindings and reports `final_failed_stop`
instead of suggesting the completed final set should be scored again.

No fresh network capture, paid infrastructure, publishing or default promotion
occurred during consolidation. The user's pre-existing modified legacy notebook
was left untouched. Trained artifacts and local evidence remain Git-ignored;
a fresh checkout needs an authorized bundle or a documented regeneration.
Broader local quality, a valid confidence policy and independent multi-network
evaluation remain open; this is a showcase, not a model-validated release.
