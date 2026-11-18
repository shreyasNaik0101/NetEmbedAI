# Frozen-model Spotify comparison — 6 November 2026

Three existing trained artifacts were compared offline on exactly the five QC-eligible Spotify connections from the [diagnostic recording](spotify-diagnostic-v1.md). All use their original saved preprocessing and policies. No training data, other local cohorts or network were accessed; an audit hook blocks those sources. No fitting, threshold sweep, capture or deployment occurred.

## Ten-packet results

| Frozen model | Raw top choice correct | Correct accepted | Wrong accepted | Refused |
|---|---:|---:|---:|---:|
| B17 augmented-CE TCN | 0/5 | 0 | 0 | 5 |
| Older local forest | 1/5 | 0 | 0 | 5 |
| Current IPv6 demo forest | 0/5 | 0 | 1 | 4 |

The older forest has an unfitted acceptance policy and deliberately refuses all cases. Its raw choice is correct for only one case; its refusals are not a calibrated reliability result. The fitted policies of B17 and the current forest differ. Raw ranks and accepted/refused counts are therefore reported separately, without interpreting score magnitudes as comparable correctness probabilities.

## Prefix results

| Model | 5 packets | 10 packets | 20 packets | 30 packets |
|---|---:|---:|---:|---:|
| B17 raw correct | 0/5 | 0/5 | 0/5 | 0/3 |
| Older forest raw correct | 1/5 | 1/5 | 0/5 | 0/3 |
| Current forest raw correct | 0/5 | 0/5 | 0/5 | 0/3 |

B17 additionally accepts two wrong labels at 20 packets and one at 30. No artifact correctly accepts Spotify at any available prefix. The forest's 18 replayed prefix outputs exactly match its original native live outputs; the other models were evaluated offline, not live. All full probability vectors and policy responses are saved. An independent JavaScript recount confirmed all twelve model/budget summaries.

## Interpretation and limits

Simply switching back to B17 does not repair these inputs. Lowering a refusal threshold also cannot repair the wrong top choices. The shared failure is consistent with a mismatch between historical learned patterns and current local Spotify traffic, but this comparison does not establish its cause. It does not isolate transport changes, feature differences, network, browser or local-adaptation effects. Representative local Spotify development data may help, but improvement is not guaranteed.

The source is one exploratory session with five eligible connections, seven reported dropped events and two excluded socket prefixes. It is not a clean operational or independent final evaluation. Prefix views of one connection are not independent samples. The recording has now been inspected and must remain diagnostic/development evidence in any later study, with fresh data reserved for evaluation.

No model is promoted. Spotify remains locally unreliable; successful YouTube/Instagram checks do not establish broader support. No extra recording is requested by this comparison.

## Reproduction and evidence

Private root: experiments/spotify-frozen-comparison-v1

- Protocol SHA-256: 6df25bd58427822eee60d79168c61e37087c9984c84512533794be0493e71fb3
- Report SHA-256: 6cb672a2f60a69a413c575966ae1143d0bb04837f7ce7c70a16a4ab8cb38e21e
- Predictions SHA-256: 66f2ca39fff440dc99d90053ee3729b3e2f6b9ca70fb2459fa50adc9aac688ed
- Runner SHA-256: 0f8c74bc6f342ab4f8379eb5a3113bb1560432edd89f0b2cfb1db9f215b161db

The private report pins bundle paths, artifact identities, exact policies, diagnostic source hashes and runtime versions. With these local artifacts present, run the fit-free runner from the project directory:

~~~powershell
.\.venv\Scripts\python.exe experiments/spotify-frozen-comparison-v1/compare.py
~~~

The runner refuses to overwrite existing outputs. To repeat, copy its runner/protocol into a new directory under experiments, leaving the original result intact; the script uses its own directory for outputs. Legitimate artifacts must be supplied on a fresh checkout. No benchmark dataset is required for inference.

## Completed feature audit

The [training-only feature audit](spotify-feature-audit-v1.md) identifies finer live timing precision, larger typical early payloads and fewer direction changes relative to a bounded seven-day Spotify training sample. It finds no obvious declared unit/direction error and does not prove causality. Final-test data stayed unopened.
