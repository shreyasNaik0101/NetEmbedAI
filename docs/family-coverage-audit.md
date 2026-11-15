# Existing family coverage — 2 November 2026

The original local training set is entirely IPv4. Development selection already
contains IPv6, but lacks the Instagram/IPv4 cell. This supports collecting real
training diversity and balanced evaluation coverage; it does not establish that
IPv6 alone causes misclassification.

| Existing role | Instagram IPv4 | Instagram IPv6 | YouTube IPv4 | YouTube IPv6 |
| --- | --- | --- | --- | --- |
| Training | 22 | 0 | 21 | 0 |
| Development selection | 0 | 7 | 5 | 5 |

All60 included connections have a unique matched browser UDP socket and one
consistent local/peer family. Families came from socket addresses matched using
the original session-salted endpoint token; they were not inferred from packet
sizes. Addresses are not exported by this audit or passed to a model. Source
rows/summaries match the frozen forest's provenance; capture/reference/log hashes
are checked. Logs are parsed one at a time with the existing bounded reader.
The audit covers the prevalidated model exports, not all traffic in those visits.
No new training, predictions, capture, calibration/final access or model changes.

Recounting the already saved clean ten-packet development predictions gives:

| Model | IG/IPv6 | YT/IPv4 | YT/IPv6 |
| --- | --- | --- | --- |
| Original forest / exact clean refit | 6/7 | 5/5 | 1/5 |
| Size-jitter pilot | 7/7 | 5/5 | 3/5 |
| Relative-size pilot | 4/7 | 5/5 | 5/5 |

This is a post-hoc descriptive view of reused selection data. It does not reopen
the pilot or replace its multi-budget/class guards: both treatments still fail
the previously frozen overall decision. In particular, ten-packet improvement
does not erase regressions at other checkpoints. There is no IG/IPv4 estimate
from this selection cohort. IPv6 is also present in the IG cases the original
forest often recognizes, so a universal IPv6 failure claim would be incorrect.

The [bounded collection plan](family-coverage-plan.md) reserves at most four new
training visits and four later development visits. It targets the missing IPv6
training cells, preserves original clean examples and requires all four cells
in subsequent evaluation. Missing natural coverage stops the scope instead of
starting a recording loop. Old calibration/comparison data retain their roles.
Collection tooling must enforce the new rules before any first intent is prepared.

Audit command, from the repository directory:

```powershell
.venv/Scripts/python.exe scripts/audit_family_coverage.py
```

The completed report is preserved at
`experiments/family-coverage-audit-v1/report.json`, SHA-256
`ac3bdef530ce2655ea7b65ce8f7809f19950d35704af47580e7e63508717987b`.
It binds eleven per-visit reports containing pseudonymous flow IDs, family,
length and first payload size plus source hashes. Audit source SHA-256:
`b23b60a2b56366002a2a8c6613f45ff24205cd1d32c6ddcb1bddf42b81d3e84a`.
The script refuses to overwrite its completed report; a fresh reproduction
needs a separate copy/output location. Existing partial visit reports allow
same-input processing continuation. The frozen comparison model is
`bd79923fabc4816cc2f15b4f150a5d3b428663c455d0fde3da6ab219eb666d62`.
The derived table uses saved `predictions.json` files from the closed
`experiments/size-robustness-v1-execution-recovery/seed17/` arms.
