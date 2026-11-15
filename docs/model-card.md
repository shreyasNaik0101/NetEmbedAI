# Model card

> **Current showcase, 10 November 2026:** This file retains the historical TCN
> default and earlier chronological notes. For the currently recommended local
> fixed-ten forest, its unfitted policy, completed local tests and failed
> accepted-label screen, see the [showcase model card](showcase-model-card.md).

Latest candidate evidence: the frozen added-data forest passes the [four new
local visits](ipv6-fresh-evaluation-results.md) as a raw classifier. Its separate
[public-only refusal policy](ipv6-public-policy.md) uses threshold0.76/minimum ten
packets: historical calibration coverage55%, accepted error3/275 at ten packets,
with only11/50 YouTube cases accepted. Those are fitting-set statistics, not
local confidence validation. The complete policy bundle preserves every weight
and probability, and passes real API/CLI/runtime checks.451 Python and19 UI tests
plus build pass. The candidate stays inactive; local accepted-error/coverage
and replacement-model live quality/latency remain pending. The default below
remains B17.

Status: the augmented cross-entropy TCN, seed 17, is the frozen default. Its held-out week-46 test is complete. User-started Wi-Fi sessions verified live packet-to-model delivery and Stop cleanup. The [Instagram diagnostic](instagram-trial.md) exposed three wrong accepted labels among eight live decisions on four independently attributed connections; five decisions were withheld. The plain TCN and forest also failed the saved-prefix diagnostic, so no alternative was promoted. Reliable local-network accuracy remains an unmet release gate. Independent parity is partial and scoped in that report. All CESNET figures use deterministic first-per-class/day sampling and are not prevalence estimates.

Initial candidate: ordinary cross-entropy training of the existing compact causal TCN, now with last-valid readout and uniform sampled 5/10/20/30-packet budgets. Smaller valid flows use their available prefix. A Random Forest trained on the same partitions and prefix-only summaries is the classical comparison. The TCN projection/classification structure is retained from the previous implementation; new readout and prefix semantics require retraining.

The [first browser adaptation pilot](browser-adaptation-pilot.md) achieved 22/27
development prefix points but then **failed separate calibration**, getting
5/26 Instagram and 22/28 YouTube points correct. No threshold met the frozen
error/support limits. No calibrated bundle was created or default changed.
The [follow-up](browser-calibration-failure.md) explicitly retires those failed
recordings to development selection. With 17 earlier local training flows and
14 later selection flows, its forest passes development gates at seeds
17/42/123 (F1 0.87386/0.87149/0.90937). The fixed deployment seed remains 17,
not the best seed. Its [fresh calibration](browser-calibration-02.md) then got
17/22 Instagram and 23/24 YouTube points right but failed the frozen per-service
error/support limits at every threshold. Its policy remains unfitted and it is
not enabled. These records remain calibration-only. Small correlated samples
and historical public controls cannot establish future local accuracy or
general superiority; no independent live validation of the replacement passed.

A [development-only audit and ordered-prefix forest experiment](development-failure-audit.md)
found no trained-TCN readout fault. The added packet-order map reduced local
F1 from 0.87386 to 0.81120 and Instagram recall from 0.77976 to 0.58333, despite
better historical public retention. Its fixed first-seed gate failed, so no
further seeds or calibration followed. The explicit experimental map remains
reproducible; legacy bundles retain their unchanged summary map. This negative
result does not provide a new default or reliable local repair.

The [fixed packet-rule comparison](packet-rule-comparison.md) adds a transparent
training-derived signature and unique-interval rule over the same raw channels,
training pool and four budgets. Raw local mean-budget F1 is 0.56923, compared
with the paired CE TCN's 0.57459 and forest's 0.87386; historical public control
F1 is only 0.43522. The interval rule matches 19/54 local cases with four wrong,
including four errors among five Instagram matches. It fails the frozen gates
and is not promoted. Exported distances are not probabilities. This is a
standalone experimental artifact; it does not replace or extend the live API's
model inventory. Newer calibration and final data were excluded.

An earlier [QUICEXT25 reference-labelled pilot](quicext25-pilot.md) trained a new
20-epoch CE model and same-data forest. On 14 saved Instagram prefix points,
their top-1 counts were 1 and 2; the CE model withheld all decisions, and all
four forest commitments were wrong. The CE model also made one wrong YouTube
commitment. These small development diagnostics did not justify promotion.
The original B17 selection decision and final report remain unchanged.

Contrastive learning was optional. CE versus CE+SupCon was compared both without augmentation and with identical bounded augmentation, at seeds 17, 42 and 123. The matched evidence does not support retaining SupCon. Historical contrastive+augmentation improvements cannot identify the loss's causal contribution.

The default policy refuses commitments until calibration succeeds. A threshold is fit on the separate calibration subset to maximize empirical coverage subject to ≤10% empirical accepted error and at least 30 accepted prefixes. If infeasible, it stays uncommitted. Temperature remains 1; temperature scaling is not claimed. Confidence is a model score. This policy does not detect unseen services.

Bundle schema version 2 binds architecture, preprocessing, labels, policy, provenance and checksums. Tests establish numerical save/load parity at tolerance 1e-7 and forest probability parity. Test artifacts are marked fixture and blocked from live capture.

Forest seed 17 development report: all-flow clean macro-F1 0.9097/0.9252/0.9202/0.9182 at 5/10/20/30 packet budgets on 10,467 selection flows. Matched 30-packet cohort has 4,475 flows; 5/30 clean macro-F1 is 0.9040/0.8840. These are development observations only, and the model was fit on 14,000 training flows from the same bounded sample policy. Its 16-case selection mean is 0.6923; the abstract +128-byte size-padding stress averages only 0.1121 macro-F1 over the four budgets. Its JSON bundle is 221 MB. On this host, with two Torch threads and another model training concurrently, 1,000 trained-bundle single-flow calls measured 111.6 ms p50 and 128.1 ms p95. This excludes HTTP and capture latency. The two-epoch TCN pilot used a separate 2,000-flow-per-split subset and is not a comparable winner.

The full-data seed-17 supervised TCN selected epoch 16 of 20 on the same development selection score: 0.7134 across the 16 fixed budget/stress cases and 0.8504 clean mean. Its clean/timing/abstract padding/observation-loss means are 0.8504/0.6320/0.6508/0.7206. A 1,000-call CPU benchmark measured 2.54 ms p50 and 3.82 ms p95 single-flow pipeline latency with two Torch threads. A separate 1,000-request local loopback keep-alive HTTP benchmark measured 4.80 ms p50 and 7.15 ms p95. Neither includes browser or capture latency. This one-seed result is insufficient to declare a default. The clean-quality floor for B/C/D was frozen at 0.8403663777292364, exactly 0.01 below this A checkpoint's clean mean, before those comparisons started.

The other supervised TCN development scores are 0.7085 (seed 42) and 0.7118 (seed 123), giving a three-seed mean of 0.7112 and range 0.7085–0.7134. This is the completed unaugmented reference, not a final-test estimate.

With the fixed half-clean/single-edit policy, full-data seed-17 augmented cross-entropy TCN (B) selected epoch 20: 16-case development score 0.82445 and clean mean 0.84971. The paired B–A score gain is 0.11100; clean difference is −0.00066. B's timing/abstract padding/observation-loss means are 0.84119/0.82286/0.78405. The saved-prediction report reproduces its training score. This seed alone does not identify any effect of SupCon.

All three B runs passed the frozen floor and have independent development reports. B's scores are 0.82445/0.82961/0.82924 for seeds 17/42/123 (mean 0.82777). The matched B–A improvements are +0.11100/+0.12109/+0.11749, with clean differences −0.00066/−0.00701/−0.00233. These results isolate this augmentation policy against plain cross-entropy training on the declared development protocol.

The unaugmented CE+SupCon candidate C scored 0.70737/0.70049/0.73201 (mean 0.71329). Relative to matched A, the changes are −0.00607/−0.00802/+0.02025, so its mean gain of 0.00205 is inconsistent. Augmented CE+SupCon D scored 0.82684/0.82560/0.82822 (mean 0.82689). Its paired D–B differences are +0.00239/−0.00401/−0.00102, failing the predeclared all-seed improvement and ≥0.01 mean-gain requirements. The simpler forest's 0.68949 mean is well outside the 0.01 comparability margin. [The decision record](../configs/default-decision.json) therefore selects B's predeclared seed 17, without consulting the final test.

The one-time held-out test uses 14,000 week-46 flows, balanced by selected class and day. Clean macro-F1 at 5/10/20/30 packets is 0.7912/0.8428/0.8761/0.8864. The 16-case all-flow mean is 0.8237. At five packets, the weakest class F1 values are Google Drive 0.536, YouTube 0.643 and Snapchat 0.676. Google Drive is often confused with YouTube. At thirty packets, Snapchat 0.772, YouTube 0.797 and Google Drive 0.810 remain among the weakest. Timing, abstract padding and observation-loss stresses give 5-packet macro-F1 0.7840/0.7723/0.7146 and 30-packet macro-F1 0.8755/0.8493/0.8359. These are declared feature transformations, not simulated valid on-wire QUIC attacks.

The separately calibrated threshold is 0.67; the model's score is not a calibrated correctness probability. On clean final-test flows, five-packet coverage is 0.7183 with 0.0990 error among accepted predictions; thirty-packet coverage is 0.8718 with 0.0664 accepted error. A threshold targeting ≤10% empirical calibration error cannot guarantee that bound on other networks. The complete report and prediction rows are in the ignored local `experiments/full-real/20261024-151720-3532794c/final/` directory; its report SHA-256 is `ec0e7fb5f1a6da476de8926da26bbc62ce6fa2317c82494b36a2065a6af34246`.

Runtime evidence: with two Torch threads and the same recorded 19-packet flow, the selected TCN measured 16.06/18.94 ms p50/p95 over 1,000 local CPU pipeline calls, and 25.07/30.58 ms over 1,000 loopback HTTP calls. The forest measured 122.92/141.09 ms over the same 1,000-call HTTP protocol. Three real user-started sessions produced 45, 105 and 33 acknowledged model events. Capture timestamp to model event p50/p95 was 380.63/532.60 ms, 294.94/536.08 ms and 401.69/540.13 ms. The first two sessions' UI delayed acknowledgment until animation frames, so their multi-second values cannot establish browser receipt or paint latency. The corrected third session measured actual browser receipt at 403.21/543.99 ms p50/p95; it still does not measure paint time. No performance number is copied from legacy results.

Intended use: a bounded local learning/interview application. Exclusions: enforcement, malware detection, unknown-service recognition, VPN generalization, hard real-time or adversarial guarantees. Inspect docs/implementation-status.md before presenting a release as complete.

The optional handshake-reference workflow now makes supported SNI-map references
visible separately from unchanged model predictions and can export raw metadata
for diagnosis. A subsequent real Chrome-origin diagnostic matched four YouTube
connections: ten of their eleven live prefix decisions withheld a label, and one
accepted YouTube. Eight accepted labels on other references outside the supported
set exposed the closed-set limitation. All 99 live predictions replayed exactly.
These small development observations do not establish held-out local accuracy;
the earlier unlabelled sessions remain unlabelled. No artifact or threshold was
changed. See [the complete trial record](browser-attribution.md#first-actual-chrome-trial-25-october-2026).
