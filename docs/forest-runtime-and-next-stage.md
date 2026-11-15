# Forest runtime and the next operational stage

The forest is the preferred candidate for the next two-service local calibration
stage: it ties the neural model on the frozen primary endpoint (20/22 correct),
is structurally simpler and is stronger at twenty packets. The neural model's
five-packet advantage remains documented. This is not a new app default or a
claim that the forest has independent local validation for all ten services.

The previous JSON-forest implementation allocated numpy index/mask arrays at
each branch even for a one-flow request. A scalar tree traversal now handles
that common case, preserving the same features, threshold comparisons, leaf
probabilities, tree order and accumulation order. Batched inference keeps its
existing path. No weights, normalization, labels or confidence policy changed.
The bounded cycle check remains in both paths.

The independent before/after audit reloaded the same real bundle and replayed
all 85 sealed local prefix cases. Probability differences are exactly **0.0**
against both the old implementation and saved forest predictions. Artifact
identity stays
`bd79923fabc4816cc2f15b4f150a5d3b428663c455d0fde3da6ab219eb666d62`.
The frozen comparison/prediction files are unchanged. No new quality experiment,
checkpoint selection or threshold tuning was performed on these cases.

An alternating before/after CPU check used the same existing real input,
two CPU threads, 20 warmups per implementation and 100 calls per implementation
per budget on the i7-1360P laptop. It includes preprocessing and predictor reply,
excluding loading, capture, HTTP, queueing and UI.

| Packets | Before p50 / p95 ms | After p50 / p95 ms |
| --- | ---: | ---: |
| 10 | 27.66 / 30.98 | 3.13 / 3.95 |
| 30 | 21.43 / 23.41 | 3.16 / 3.70 |

These timings describe these implementations/input/host, not a line-rate or
hard real-time guarantee. Earlier sealed timing reports retain their old
implementation measurements. The active B17 service is not switched or restarted
for this change; a future forest service loads the optimized code on startup.

355 Python tests pass, including exact single-versus-batch/sklearn parity over
varying prefixes and feature values, equal-threshold routing, root-leaf trees and
cycle rejection. Ruff lint/format pass for 113 files. UI code is unchanged from
the seventeen-test/build checkpoint. Existing dependency warnings remain.

Audit files are local and ignored under `experiments/forest-runtime-check/`:
`bundle_before_scalar.py`, `audit.py`, `report.json`. The retained old source
SHA-256 is `1ebcfbc7e9f9644d3ed17b2d13533d34c49f44a4dca214022a05c53252a7a3cd`;
optimized source SHA-256 is
`7fca97cfb08d97fabbb6d9b353379bcb19c9fc285152f5391349343d999a16f4`;
audit source SHA-256 is
`7529307a637253d7838b034efe1c056db5eeefe0136ddaf208c3f8481eaa20be`.

```powershell
.venv/Scripts/python.exe experiments/forest-runtime-check/audit.py
.venv/Scripts/python.exe -m pytest -q
```

## Remaining step before local deployment

Prepare a fixed confidence-policy workflow for this forest, using separately
declared fresh calibration sessions and then an untouched final check. The
completed four-visit comparison has already informed candidate choice and must
not be relabelled as calibration or final evaluation. Older failed calibration
records also remain excluded. No new recordings or intents are prepared here.

The workflow must state the coverage/error/support rules, class-specific results,
what happens when no threshold passes, and the small correlated-sample limits
before collecting. It must preserve the forest weights and export any selected
policy with new provenance/checksums. A separate genuine capture-to-model check
is still needed before claiming this candidate works in the live UI. These
steps are pending; raw scores remain uncalibrated and B17 remains the app model.
