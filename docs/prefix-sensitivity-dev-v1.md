# Fixed-ten timing and ordering sensitivity

This is a descriptive stress test of the existing ten-packet forest, not a new
model, validated augmentation or final accuracy evaluation. The fixed declaration
was written before the runs: `configs/prefix-sensitivity-dev-v1.json`, SHA-256
`529288579fa82ba9424271190196ae77022783a023b4c283e156fe15c89e5a08`.
The model artifact is `fa1f4837e4ae11c9169258ecb20338ae3c0c81c2d206231fb6fe19405b8d8549`.
Its weights and preprocessing were not changed.

The inputs are the same 21 previously exposed development connections used in
the earlier fixed-ten study: ten YouTube, seven Instagram and four Spotify. They
come from a small number of visits and were already involved in prior model
selection. The unchanged scores for all 21 reproduce the saved baseline to
`1e-12`. No public training/calibration/test files, later local calibration,
final-test recordings or network access were permitted. A runtime audit guard
restricts reads to the four exact, checksum-bound development inputs, the frozen
model, the saved baseline and the new output root.

## Defined views

* **Unchanged:** the captured first ten packets.
* **Gap +0.1 ms / -0.1 ms:** add or subtract 0.1 ms from each of the nine
  observed gaps, clipping to valid bounds. The first gap remains zero. These
  changes may move the total prefix duration by up to 0.9 ms.
* **One opposite-direction swap:** if a neighbouring pair among packet indices
  1 through 9 has opposite directions and a gap at most 1 ms, swap the direction
  and size metadata of the first such pair while retaining the time slots.
  Otherwise leave the input unchanged. Packet zero is never swapped, and no
  information beyond the ten-packet prefix is used.

These are **abstract stress transformations**. They do not simulate a specific
network, prove which browser/capture interleaving is correct, or guarantee
protocol validity. Counts, labels and packet-size/direction values are not used
to choose a favourable perturbation or model.

## Results

| View | YouTube top-choice changes | Instagram changes | Spotify changes | Total changes |
| --- | ---: | ---: | ---: | ---: |
| Gap +0.1 ms | 0/10 | 0/7 | 0/4 | 0/21 |
| Gap -0.1 ms | 3/10 | 0/7 | 1/4 | 4/21 |
| One eligible swap | 0/10 | 0/7 | 0/4 | 0/21 |

The swap actually applied to only **8 of 21** connections (two YouTube, four
Instagram, two Spotify); the other 13 are unchanged, so the swap result is not
evidence of general ordering robustness. Under the negative-gap stress the
maximum individual class-score change was about 0.387 for YouTube, 0.341 for
Instagram and 0.354 for Spotify. Scores are model outputs, not probabilities of
being correct. All four changed top choices under the negative-gap view changed
from the correct development label to another class; this is a description of
these exposed inputs and is not a new local accuracy estimate. Changes in both
directions were fixed before running; no view was tuned or promoted afterwards.

These results make timing sensitivity a concrete issue for further study. They
do not establish the cause of the previously observed final-test errors or prove
the network would produce these exact changes. The earlier matched nearest-ms
training/inference repair was already rejected. No new replacement has been
demonstrated: any proposed timing-robust training or inference method needs a
separately fixed, same-data development comparison, class-specific retention,
and a new independent evaluation. The failed final set must not be used for
training, threshold selection or selecting a candidate.

## Evidence and checks

Output: `experiments/prefix-sensitivity-dev-v1/report.json`, SHA-256
`c4b6be1fbc6d364421dab86f63094abb36891d92c6b88895735a8dd7cd2c2bcb`.
The 84 per-flow/view probability vectors are in `predictions.json`, SHA-256
`cdae7111bc3d93dd8e9e9856676f9dbf9ef2e9b1764243005ade82589f53d3a1`.
They remain private local development evidence. An independent JavaScript
recount reproduced every saved per-class count, top-choice change and maximum
score shift. The scripts never capture packets or promote a model.

38 focused tests passed, including bounded/immutable first-prefix semantics,
no future-packet influence, clipping, swap conditions and guards against
training, calibration, final and network inputs. Python lint passed. Run:

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_prefix_sensitivity.py tests/test_ten_packet.py tests/test_order_diagnostic.py -q
.\.venv\Scripts\python.exe -m ruff check scripts/study_prefix_sensitivity.py src/netembed/prefix_sensitivity.py tests/test_prefix_sensitivity.py
```

The study runner `scripts/study_prefix_sensitivity.py` refuses to overwrite its
existing output. The configuration and report bind its exact inputs and source
checksums for a separately named reproduction. No new recordings were needed.
