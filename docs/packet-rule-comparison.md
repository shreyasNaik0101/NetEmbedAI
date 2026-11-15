# Packet-only heuristic comparison — 28 October 2026

**The tested heuristic does not justify replacing the forest.** A simple
training-derived packet signature scores 0.569 local development F1 versus
0.575 for the paired CE TCN and 0.874 for the summary forest. A conservative
rule answers only 19/54 prefix cases and gets four wrong, all on Instagram.
No threshold sweep, new capture, model promotion or live-service change followed.

This is a new, fixed diagnostic baseline inspired by the internship's
size/direction/timing approach. It is **not** a transplant or validation of that
project's full activity/naming pipeline. The latter uses different outputs,
observation windows and structural/name/DNS/address evidence. No private
internship code, captures, headline metrics or dependencies were copied.

## What was compared

[The config](../configs/packet-rule-study.json) and implementation were committed
at `1cc1625` before the real-data fit. This is still a post-failure development
comparison: its selection data was already used in earlier studies, so gains
would not constitute independent validation.

All methods have the same underlying public/local training pool: the original
14,000 public training flows and 17 local training connections (five Instagram,
twelve YouTube). The rule and forest use all four capped prefixes per training
flow, with the same 0.75 public / 0.25 local global mass and balanced local
classes. The TCN uses its previously frozen sampled-prefix CE warm-start run.
Different fit procedures and feature transforms are explicit; this is not a
single-factor causal experiment.

Local selection has fourteen later independently referenced connections from
two sessions: seven per service, 54 valid 5/10/20/30 checkpoints. The previously
failed `cal-01` pair was explicitly retired to development before the original
forward study. Newer `cal-02`, future `cal-03`, prospective `dev-03..06`, and
final samples/reports were excluded by the comparison's Python open guard.
The ordinary data reader also refuses final examples by default. Guards are
scoped Python checks, not an OS sandbox.

The heuristic has ten fixed descriptors: packet count, outbound packet/byte
fractions, large-payload fraction, direction-switch fraction, mean/std payload
size, log duration, log median gap and long-gap fraction. It reads only actual
UDP payload sizes, client/server directions and millisecond gaps. No domain,
address, process, payload content or filename enters prediction.

Training builds weighted 5/50/95% feature quantiles and global IQR scales for
each actual-length bucket, with fixed scale floors. Profiles require three
distinct training flows per class/bucket; repeated caps do not count as new
flows. All ten classes met support in every bucket. Inference exports both:

- **Nearest signature:** the class median closest in mean IQR-scaled absolute
  distance. This forces a raw ranking for comparison, without pretending its
  distances are probabilities.
- **Unique-profile rule:** an answer only when exactly one class's training
  interval box matches all ten observed features and at least five packets
  were observed. Overlap/no match causes abstention. This is an uncalibrated
  heuristic match, not structural proof or unknown-application detection.

The bucket depends only on actual observed length, not a requested future cap.
Identical short inputs therefore always produce the same result. Quantiles,
scales, feature/rule versions, labels and full provenance are saved together;
inference never recomputes training statistics.

## Actual quality results

Raw local F1 averages the four budget-specific macro-F1 scores over the two
observed target classes. Incorrect predictions of other supported classes
remain errors; all ten-class confusion matrices are saved. F1 is not the
fraction of correct prefix cases.

| Raw ranking, fixed seed-17 references | Local mean-budget F1 | Correct / 54 | Historical public mean-budget F1 |
| --- | ---: | ---: | ---: |
| Training-majority control | 0.34167 | 28 | 0.01818 |
| Nearest packet signature | 0.56923 | 26 | 0.43522 |
| Fine-tuned CE TCN, epoch 5 | 0.57459 | 30 | 0.83960 |
| Summary forest | 0.87386 | 45 | 0.90114 |

The nearest signature's raw accuracy is below the majority control despite its
higher target-class macro-F1. It is not comparable to the forest under the
fixed local/public/class-recall gates. The forest's development lead does not
overturn its later failed calibration; it is not a validated local replacement.
This paired CE TCN is also distinct from the B17 model still loaded in the app.

| Budget | Valid local cases | Signature correct | CE TCN correct | Forest correct |
| --- | ---: | ---: | ---: | ---: |
| 5 | 14 | 6 | 4 | 10 |
| 10 | 14 | 6 | 10 | 12 |
| 20 | 13 | 8 | 8 | 12 |
| 30 | 13 | 6 | 8 | 11 |

The historical public control uses the same first 50 flows/class as the paired
models: 500 flows and 2,000 requested caps, including actual short prefixes.
Local checkpoints require the full observed count; no padding creates extra
quality points. The public control predates local adaptation and is not a
forward local test. Stored source-model probabilities and F1 values reproduce
exactly, with 54 local probability-vector comparisons per model.

The unique-profile rule is separate from forced nearest ranking:

| Independent reference | Available cases | Rule matches | Wrong matches |
| --- | ---: | ---: | ---: |
| YouTube | 28 | 14 | 0 |
| Instagram | 26 | 5 | 4 |
| Total | 54 | 19 | 4 |

Coverage is 35.2%; error among matches is 21.1%, including 80% for the five
Instagram matches. It fails the frozen support/error gates. The public rule
matches 511/2,000 caps, with 170 wrong (33.3%). A unique training box does not
establish a correct identity. No model confidence policy was calibrated here.

These are correlated prefixes within fourteen connections/two selection visits,
not 54 independent trials. No significance, population-risk guarantee, new
held-out-test accuracy or evidence against every possible heuristic is claimed.

## What transfers from the internship work

The reviewed project separates service identity from activity. Its shape/rhythm
rules can return call/stream/text rather than Instagram/YouTube; a STREAM label
does not identify which service produced it. The current dataset supplies
service references, not defensible per-flow activity truth. Activity accuracy
is therefore recorded as unavailable rather than fabricated from app names.

Across the 31 existing training/development connections, 29 complete thirty-
packet prefixes have median duration 48.93 ms; 27/29 are shorter than three
seconds and none lasts fifteen seconds. Several original rhythm rules require
such longer observations. Original structural call evidence and IP-byte/full-
flow rates are also unavailable in this three-channel QUIC prefix contract.
Thresholds from the other project's IP-byte/seconds contract were not silently
applied to UDP-payload/millisecond inputs.

Its naming/DNS/ASN/nDPI cascade may be relevant to a separately specified hybrid
identifier, but is outside this packet-only comparison. NetEmbedAI's browser
and handshake references remain evaluators, not classifier inputs. Grading a
name-based predictor against labels derived from the same names would be
circular. Neither that broader cascade nor the original activity rules were
scored as an app classifier here, and no internship headline score was reused.

## Compute, artifact and reproduction

The real profile fit took 41.72 s after cohort loading/prefix construction.
Trained-artifact CPU timings use the same real recorded thirty-packet input,
two Torch threads, 50 warmup calls and 1,000 measured calls per method:

| CPU prediction call | p50 ms | p95 ms |
| --- | ---: | ---: |
| Packet rules/signature | 0.98 | 1.61 |
| Paired CE TCN | 14.99 | 18.65 |
| Paired summary forest | 25.61 | 31.32 |

Response shapes differ (distances/rule matches versus model probabilities).
These measurements exclude HTTP, packet observation, capture and browser
delivery, and depend on host load. Faster incorrect answers do not justify
promotion. There is no hard real-time, throughput or live-latency claim.

220 Python tests pass with one existing Starlette/AnyIO deprecation warning;
Ruff lint/format passes for 74 active files. Tests cover units, actual-length
bucketing, overlap abstention, distinct-flow support, serialization, fixture
blocking, protected inputs and per-class error accounting. UI code is unchanged.
The actual saved rule also reproduces with fitting disabled and Python open
access to processed/browser data and paired model bundles blocked. That is
recorded-input inference, not new live evidence.

The output root is `experiments/browser-adaptation/packet-rules-01/`.
`rules/rules.json` is 55,910 bytes. It is an experimental standalone artifact,
not an accepted FastAPI live-model bundle; the app refuses its inventory rather
than silently switching predictors. All raw probabilities/rule decisions,
confusion matrices, source hashes, gate decisions and timings are retained.

| Local artifact | SHA-256 |
| --- | --- |
| `rules/rules.json` | `905fa21c6efcde02a6f819fba7346ad2b55aaf8ffc7a839c2ba54e906220dd28` |
| `protocol.json` | `74cac464cd88363f2e49ac69fb687c5c32e353c22b250664037ad1d48960b5e5` |
| `report.json` | `2db0ae88f6682bd9199c52cf1f03621b8b498b66b56a7c2a78d646dc826c6945` |

The local portable archive
`artifacts/local/NetEmbedAI-packet-rules-01-EXPERIMENTAL.zip` is 189,972 bytes,
SHA-256 `ece44942b37cbccecc4542c6c0cad478ea68eab9263f09656300e37ff5b92ceb`.
It includes numeric profiles/checksums, config, provenance, report, verification
and dataset attribution; no raw browser logs or paired model weights. Nothing
was published or merged.

From `traffic_classification`, with existing private training/reference files,
reproduce into a new output directory:

```powershell
.venv/Scripts/python.exe scripts/compare_packet_rules.py --output experiments/browser-adaptation/packet-rules-repeat
.venv/Scripts/python.exe -m pytest -q
.venv/Scripts/python.exe -m ruff check src tests scripts
.venv/Scripts/python.exe -m ruff format --check src tests scripts
```

For standalone inference on the existing recorded CPU input, without reopening
training data:

```python
import json
from pathlib import Path
from netembed.contract import Flow
from netembed.packet_rules import PacketRules
rules = PacketRules.load("experiments/browser-adaptation/packet-rules-01/rules")
recorded = json.loads(Path("experiments/browser-adaptation/pilot-01/benchmark-flow.json").read_text())
result = rules.predict(Flow(**recorded).array())
```

The original B17 live identity remains unchanged and capture is off. The
prospective collection is still prepared but was not used by this comparison.
No winning replacement or model-validated release emerged. Broader development
coverage, independent local calibration/quality validation and UI-latency
remeasurement remain pending under the original packet-only scope.
