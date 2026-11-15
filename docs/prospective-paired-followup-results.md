# Completed paired local comparison — 1 November 2026

The [declared follow-up](prospective-paired-followup.md) is complete. Four usable
visits across two local dates contain 22 independently attributed connections:
15 Instagram and seven YouTube. Both frozen models receive the same eligible
actual packet prefixes. Candidate scoring began only after all four archives
passed. No training, augmentation, model selection sweep or policy fitting ran.

**The primary comparison ties.** At ten packets, both models get 20/22 raw
top-ranked predictions correct. The predeclared visit-balanced macro recall is
0.9330357143 for both, paired difference zero. This is a descriptive pass of the
screen; it is not a statistical noninferiority result or general local accuracy.

| Ten-packet class | First visit | Second visit | Mean visit recall, both models |
| --- | ---: | ---: | ---: |
| Instagram | 7/8 | 6/7 | 0.86607 |
| YouTube | 3/3 | 4/4 | 1.00000 |

The primary score averages visit recalls within each class, then averages the
two classes. It is **not** raw accuracy: 20/22 raw correctness is 90.9%, while
the declared balanced score is 93.3%. Both class recalls exceed the fixed 0.80
screen floor. Visits with more connections do not receive more primary weight.

| Packet checkpoint | Four-head model correct | Forest correct | Four-head balanced score | Forest balanced score |
| --- | ---: | ---: | ---: | ---: |
| 5 | 20/22 | 17/22 | 0.88542 | 0.78720 |
| **10 (primary)** | **20/22** | **20/22** | **0.93304** | **0.93304** |
| 20 | 18/21 | 20/21 | 0.84375 | 0.96875 |
| 30 | 20/20 | 20/20 | 1.00000 | 1.00000 |

Across all available checkpoints, the four-head model gets 78/85 and the forest
77/85. Those 85 cases repeat prefixes from only 22 connections and four visits;
they are not independent trials. The neural model helps earliest decisions,
the forest is stronger at twenty packets, and neither dominates. The primary
tie provides no clear neural superiority. We do not select a new checkpoint or
mix winning heads after observing these secondary results. The thirty-packet
20/20 is a small-sample observation, not a perfect-accuracy guarantee.

## What the check does and does not authorize

This is fresh-session comparison evidence for these selected candidates on this
laptop and these two services. Two visits were collected before the follow-up
declaration but after the models were frozen; their candidate outcomes had not
been inspected, and their immutable archives were inherited explicitly. The
failed original attempt and technical log continuation remain documented. No
failed attempt was silently replaced under the original stopped protocol.

The earlier development nonregression failures remain recorded. This new
descriptive pass does not rewrite those gates, establish performance on the
other eight supported services, or establish robustness to other networks,
browsers, background mixes, unsupported protocols or future visits. No
connection-independent uncertainty interval is claimed from correlated prefixes.

Both candidate policies are still unfitted: **all 85 accepted labels are
withheld for each model**. The table evaluates raw top-ranked labels separately,
not calibrated confidence, released prediction coverage or accepted-label
accuracy. Confidence policy fitting and a later independent check remain
separate work. The app continues to use B17; new-model live capture integration
has not been validated or promoted. These recorded native packets were evaluated
offline using the frozen candidates, not a new candidate running in the live UI.

The neural model has an early-prefix advantage; the simpler forest remains
comparable at the primary endpoint and stronger at twenty packets. No model is
automatically promoted by this protocol. Further operational choice needs the
uncertainty policy and relevant evidence; no extra capture is requested here.

## Independent replay and CPU check

`experiments/prospective-paired-engineering/audit-completed-followup.py` is a
separate local audit script, SHA-256
`0934af7c2cc127235b3ec1d79be6494bf2903f6f5893a3883055d6b28bb6dfbb`.
It verifies every archive, exact case inventory, unique connections/sessions,
raw references, prediction checksums and fitted-policy flags. Reloaded artifacts
reproduce **all 170 probability vectors exactly**, maximum difference 0.0 for
both models. The audit independently recomputes per-visit/class primary recall,
secondary counts and the descriptive screen. Network, training-corpus and
protected-data access is blocked during the audit. No weights or policies change.

It also measures both trained predictors on the same fixed existing real
example, truncated to ten/thirty packets, with 20 warmups and 100 calls, two
CPU threads on the i7-1360P. Calls include preprocessing, predictor and reply;
loading, capture, queueing, HTTP and UI rendering are excluded.

| Model | 10-packet p50 / p95 ms | 30-packet p50 / p95 ms |
| --- | ---: | ---: |
| Four-head model | 13.04 / 15.76 | 17.63 / 23.75 |
| Exported JSON forest | 30.02 / 36.02 | 21.55 / 25.39 |

These sequential measurements use the current implementations on a shared
laptop with uncontrolled background load. They are not an architecture speed
guarantee or newly measured live event latency. Simpler architecture did not
imply lower measured single-flow latency for this exported forest implementation.

## Files, identities and reproduction

Local output root: `artifacts/local/prospective-paired-followup-v1/`.

| File / identity | SHA-256 |
| --- | --- |
| Four-head bundle metadata | `483dcd5ea9af2dce2da16c818ee73341f1eb328a032ad56a192c32b7f552e7dd` |
| Forest bundle metadata | `bd79923fabc4816cc2f15b4f150a5d3b428663c455d0fde3da6ab219eb666d62` |
| Declaration | `c8aed9b2c6fe1138e574b8e6af8a8c9d7ddbb3ba62b57359922e829b37f6f289` |
| `comparison.json` | `508d2db99b0d5de320e5c6c85053065583af4bac35513c2813d2247e0e86c385` |
| `paired-predictions.json` | `65885c351b67fd0e62c404c8eff157ffb994de4dfa18dab0811f5b60a0b02c8f` |
| `independent-result-audit.json` | `1924286773edccc6fb7c1889d5cb5a9f4c6b095ce4d779d674b913260640a998` |
| `completion-evidence.json` | `5a9b65962d81211726ce94f4c031f588eefefb70038c6ed0ad966b035999d892` |

`completion-evidence.json` records source commit, versions, all four archive
hashes and result byte counts. The archive chain binds native capture, Chrome
reference, QC, source replay, file-location copies and the earlier projection.
The last Instagram log was found in the prior folder and copied byte-identically;
its native capture was not replaced. Runtime: Python3.11.9, NumPy2.1.3,
PyTorch2.5.1 CPU, scikit-learn1.6.1. Software remains at the preparation checkpoint
of 354 Python tests, 17 UI tests and successful build/lint/format. No source code
changed or full tests were rerun for this evidence-only completion.

```powershell
# Verify collection/archive readiness without predicting:
.venv/Scripts/python.exe scripts/paired_capture.py --plan configs/prospective-paired-followup-v1.json --root artifacts/local/prospective-paired-followup-v1 status
# Independently reproduce the saved result using local artifacts and recordings:
.venv/Scripts/python.exe experiments/prospective-paired-engineering/audit-completed-followup.py
```

The actual scoring command used those same flags and `score`; it refuses to
overwrite the now-frozen comparison. Re-auditing does not create a new test set.
All model/data artifacts and browser logs remain local, ignored and unpublished.
Capture is stopped. This comparison is complete; local calibrated deployment
and the overall demo-ready release are still pending.
