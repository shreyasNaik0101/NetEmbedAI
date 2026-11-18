# Matched timing-jitter forest experiment

## Result

**Stop: no validated candidate.** Seed 17 passed the fixed development gates;
seeds 42 and 123 failed the local clean/stress retention and stress-gain gates.
All three seeds had to pass. The jitter model is not promoted, calibrated or
loaded into the app. The earlier final-test failure remains unchanged.

The following are raw top-choice counts on the **same 21 previously exposed
local development connections**, not fresh accuracy estimates:

| Seed | Clean control | Clean jitter | Minus-0.1-ms control | Minus-0.1-ms jitter | Gate result |
| --- | ---: | ---: | ---: | ---: | --- |
| 17 | 21/21 | 21/21 | 17/21 | 21/21 | Passed |
| 42 | 21/21 | 19/21 | 17/21 | 19/21 | Failed |
| 123 | 20/21 | 19/21 | 20/21 | 19/21 | Failed |

At seed 42, the clean jitter model lost one YouTube and one Instagram correct
choice compared with its control. At seed 123, it lost one Instagram correct
choice. The table is descriptive and the examples are correlated and reused;
it cannot establish performance on other sessions or networks. All three
candidate seeds passed the declared historical public clean macro-F1 and
per-class retention checks on the 452 eligible public **selection** examples.
Those public checks do not override the failed local gates.

## Fixed comparison

The protocol `configs/timing-jitter-matched-v1.json` was declared before any
fit, SHA-256 `0a446675f24664cf236aca8eb9823bd5c310ec93854b7a6c1351b13b5c201cc5`.
For each seed, both forests used the same 14,000 public training flows, 79
role-bound local training flows, four prefix views, per-example weights,
normalizer, 32-tree architecture and CPU thread limit. The control used clean
inputs. The candidate used one deterministic per-flow choice of -0.1, 0 or
+0.1 ms on every noninitial gap, clipped to valid bounds and shared across all
prefixes. No training rows were added. This is abstract metadata augmentation,
not a measured or protocol-preserving network simulation.

Evaluation used the same 21 local and 452 public previously exposed selection
connections at ten packets. Each arm was checked on unchanged data and the
same positive/negative 0.1-ms abstract gap stresses. The fixed gates required no
local class loss on clean or either stress, at least two more correct local
stress cases in aggregate, no more than 0.02 public clean macro-F1 loss, and no
more than 0.05 public clean recall loss for any class. These are small
development screens, not a guarantee of robustness or accepted-label safety.

The seed-17 control reproduced the existing forest weights byte for byte and
the previously saved baseline probabilities before candidate fitting. Each
exported forest also matched its scikit-learn reference within `1e-12` on the
declared probes. Each seed used identical checksum-bound training examples and
augmentation assignments. Final-test and calibration files were blocked by the
offline access guard. No new captures, thresholds, model promotion or paid
resources were used.

## Execution and evidence

The initial sandboxed attempt failed **before any tree was fitted** because
Windows denied creation of a worker-pool pipe. Its partial manifests are
preserved in `experiments/timing-jitter-matched-v1`. The identical recipe was
rerun with local worker-pool access at
`experiments/timing-jitter-matched-v1-execution-recovery`; the data and
augmentation manifests were verified byte-identical before fitting.

The first runner stopped after seed 42 failed, although the written protocol
called for both seed 42 and seed 123 following a seed-17 pass. The already
declared seed-123 pair was therefore completed separately at
`experiments/timing-jitter-matched-v1-seed123-continuation`, without repeating
the first two fits. Its input and augmentation manifests were verified identical.
The seed-42 failure remains binding; seed 123 cannot rescue it. This execution
correction introduced no new seed, threshold, selection rule or data.

* Seed-17/42 decision SHA-256:
  `2f870812203b41fca33e852f47ff67d58b6545b686e770bf6b78b9078f0aefa1`.
* Seed-123 continuation decision SHA-256:
  `905fd03dc47bfb831320efb0f75954c7e27aed58a70f02350675d3c9ac3982a5`.
* Shared data manifest SHA-256:
  `b4792438ebc8b112528b301750a7f2bee2642e21ee79b5bf86f5fc45e6b9cd0b`.
* Shared augmentation manifest SHA-256:
  `b96f4994b0e98ef956843a10d3c8a5ca14994135730f5eb0f7e6ae47cdcb7e4a`.

Detailed metrics, per-flow probabilities, bundle checksums and fit timings are
saved under each seed/arm. An independent JavaScript recount of all saved
prediction counts, class counts, macro-F1 values and declared gates matched the
reports. **31 focused tests passed** before execution, including jitter bounds,
immutability, prefix consistency and protected-data/network guards; Python lint
passed. The app remained idle with capture off.

This scope stops here: do not rescue it by trying extra seeds, tuning the
augmentation against these results or using the final-test records for fitting.
Any future candidate requires a separately declared research scope and new,
independent evaluation before a release claim.
