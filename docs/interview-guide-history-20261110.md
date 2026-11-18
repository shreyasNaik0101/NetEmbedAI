# Latest delivery evidence — 9 November 2026

The [controlled delivery check](delivery-check-v1.md) supports this statement: “I verified the local packet-to-browser pipeline on real user-started traffic. In one run it retained61 connections and delivered all223 checkpoint events with zero reported drops or missing receipts. It combined redundant cumulative packet-display updates while preserving model events. Median capture-to-browser receipt was about140 ms, with p95 about467 ms. That measures event delivery, not screen paint or time from connection start.”

“This is separate from classification accuracy: the check had no independent browser labels for all flows, and the candidate's acceptance policy is still unfitted. The earlier interrupted fresh-classification scope stays closed. Fresh service verification, separate calibration and later accepted-prediction checks remain necessary.”

# Latest model development — 8 November 2026

The [fixed ten-packet candidate](spotify-ten-packet-v1.md) supports this honest explanation: “I added independently verified Spotify training recordings. That improved Spotify on a new development visit, but some YouTube predictions became worse when more packets were included. I rejected those multi-prefix candidates under the rules I had frozen. A separate narrower model now uses exactly the first ten packets and clearly says so in the API and UI. Its reused development results are four Spotify connections correct out of four, while retaining seventeen YouTube/Instagram connections correct out of seventeen. Those small reused samples do not establish general reliability.”

“The candidate waits for ten packets, then later packets remain visible metadata. I tested that changing later packets cannot change its score, and that inference works without training files. Its confidence policy is still unfitted, so it withholds accepted labels. Fresh recordings covering both Spotify and retained services, separate calibration and genuine live latency checks are still required before I use it as a validated live demo. The running app has not switched to it.”

# Current live demo — 6 November 2026

Start with the [five-minute demo and plain-language explanation](demo-runbook.md), [current model choice](demo-model-decision.md) and [completed live measurements](ipv6-live-policy-results.md). The historical progress entries below retain earlier states; statements that candidate live validation is pending have been superseded by the two completed visits. Later confidence and generalization limitations still apply.

# NetEmbedAI: beginner-friendly interview guide

The [new refusal-policy work](ipv6-public-policy.md) explains the next distinction:
“A correct top guess is not automatically an answer I should trust. I fitted a
separate threshold only on the historical public calibration split, leaving the
new local evaluation untouched. It accepts275/500 ten-packet calibration cases
with3 mistakes, but answers only11/50 YouTube cases. I report both the error and
the rejection cost. Those are fitting-set results, not local confidence proof.”

“The exported policy keeps the same model weights and packet preprocessing. I
verified real-bundle API/CLI parity and1,000-call CPU timing without training
data. The UI explains whether calibration is missing or only public-data-based.
Local acceptance quality and live capture-to-screen timing for this replacement
still need separate evidence; I have not switched the app automatically.”

The [new four-visit evaluation](ipv6-fresh-evaluation-results.md) now supports a
stronger, specific interview statement: “I froze the model before collecting
four new visits over two dates. At ten packets, the forest trained with the
additional real examples classified all22 retained connections correctly;
the matched original forest classified7/22. Both services improved or held
their target-visit recall. I checked every saved probability vector and
independently recounted the metrics. I did not retrain after seeing the result.”

“This is evidence of improvement on this small YouTube/Instagram IPv6 hotspot
cohort. It is not proof of perfect future accuracy. There are only two visits
per service, repeated packet prefixes are correlated, and other networks remain
untested. Confidence calibration and the replacement model's actual live-app
validation are still pending, so I have not activated it.” The primary score
weights visits and services equally:1.0 versus0.462121. The ordinary22/22 and7/22
counts include one incidental YouTube connection reported separately from the
target visits. A raw correct guess still differs from a calibrated accepted
answer. The four-visit collection is complete and no extra take is requested.

The [real-data pilot](ipv6-realdata-pilot.md#actual-outcome) gives a concrete
answer to what the recordings achieved: “My original local training examples
covered IPv4 only. I kept them and added 19 real, independently browser-verified
IPv6 flows, using the same forest settings and weighting. On the old development
set, ten-packet correctness improved from 12/17 connections to 17/17, with neither
service losing average recall. The public benchmark control changed only
slightly, within the limits declared before fitting. The control reproduced
exact weights and every saved prediction replayed exactly.”

“This tells me real training coverage is useful for this development failure.
It does not guarantee new traffic will behave the same: the set is small and
reused, new training was recorded later, and Instagram/IPv4 is untested here.
I saved the candidate but kept it out of the app until fresh evaluation and
confidence calibration. A model's top guess and its permission to show an
accepted answer are separate decisions.” The 0.984 figure is mean macro-F1
over four packet budgets for the two observed services, not a universal accuracy
percentage. The random forest is a collection of small decision trees voting
from packet-pattern summaries; endpoints and browser identity never enter it.

Earlier experiment checkpoints below explain how this candidate was reached.

The [size-robustness pilot](size-robustness-study.md) now tests two concrete
repairs on the original training/development data: “I trained a forest with
bounded size variation and another using relative sizes. The first improved
our abstract stress score, but reduced clean Instagram recall from92.9% to87.9%
and hurt some public classes. Relative sizes reduced clean Instagram recall
to47.9%. I kept the per-service gates, saved the failures and stopped before
extra seeds or deployment.” Those recalls average prefix budgets on reused
development connections; they are not real IPv6 test accuracy. All18,567 saved
vectors reproduce exactly;395 software tests pass. This is a completed
single-seed experiment and a useful direction, not a finished robust classifier.

The [YouTube diagnosis](youtube-failure-diagnosis.md) explains a specific weakness
in plain terms: “The earlier YouTube connections used IPv4 and1,250-byte starting
payloads. The next batch used IPv6 and1,230-byte payloads. Both measurement tools
agree on those sizes. Changing only that size in an offline sensitivity replay
flips many model answers; its trees are too sensitive to that boundary. All my
local training examples started at1,250 bytes. I need to test robustness across
legitimate size/path variation, rather than change measurements to make answers
look correct.” IP family is diagnostic information, never a service shortcut.
The replay is not repaired live accuracy, and the association does not prove IP
family alone caused the real-world change. No new capture or training followed;
the failed calibration stays failed.375 Python tests pass at this checkpoint.

The latest [confidence-policy check](forest-policy-calibration.md#actual-calibration-result-stop)
failed on two new, usable recordings. At ten packets the fixed forest gets all
five Instagram connections right, but only three of six YouTube connections.
We checked the101 cutoffs declared beforehand. None could answer often enough
while keeping mistakes within the per-service limits. Raising the cutoff cannot
fix the underlying ordering of correct and incorrect predictions. We saved the
failure and stopped; no extra final recordings or replacement activation follow.
This is a model limitation on this small batch, not a mistake by the person
recording. The cause of the change from earlier visits is not established.

For an interview: “The earlier comparison looked promising, but the next
calibration batch exposed poor YouTube recognition. I preserved the failed
result instead of lowering the acceptance rules. A reproducible pipeline and
good performance on one batch do not establish reliable recognition on my Wi-Fi.”
The app keeps B17. A score such as0.8 is not automatically an80% chance of being
correct, and these correlated calibration prefixes are not an untouched test or
a population guarantee. Reliable local deployment remains unfinished.

The [completed fresh-session comparison](prospective-paired-followup-results.md)
is a useful interview result: two frozen models each classify 20/22 connections
correctly at ten packets over four visits/two dates. Equal weighting by visit
and class gives a 93.3% primary score; the raw correctness is 90.9%. The neural
model helps earlier, while the forest is better at twenty packets. Neither
clearly dominates. All saved scores reproduce exactly from the exported models.
This does not prove general accuracy: there are only two services and four
visits, and repeated prefixes are correlated. Both models still withhold accepted
labels because their local confidence policies are unfitted. The app retains
B17 until a separately supported operational decision. This distinguishes a
promising classification result from a trustworthy deployed confidence policy.

The [fresh-session protocol](prospective-paired-study.md) froze the four-head
model and forest before collecting new visits. The completed follow-up reused
two immutable visits and declared the remaining two explicitly. Both models
received identical saved packet features and independent browser references.
Each visit had equal weight within a service, so a busy visit did not dominate.
We waited for the full set before examining candidate results. Broad reliability
and calibration still need further evidence.

The [latest experiment](prefix-linear-probe-study.md) gives each packet count
its own small classifier while keeping the pretrained network and scaling
fixed. This improves five-packet predictions from 11/17 to 16/17, and overall
correct prefix cases from 55/63 to 59/63. Both services improve against the
shared classifier, but Instagram remains one repeated case behind the forest.
The recorded rule still prevents promotion. These are seventeen reused
development connections, so the improvement does not establish future live
accuracy. The initial solver limit was insufficient; a separately declared
training-only retry gave the same optimization more iterations before scoring.

The [preceding experiment](pool-linear-probe-study.md) tests transfer learning:
keep a pretrained packet-pattern network fixed, take its 448 numerical features
before the final refinement layers, and train one small linear classifier on
those features. Only the scaling and classifier learn from our training flows.
This improves the existing development result to 55/63 repeated prefix points
from the latest forest's 47/63. YouTube improves, but Instagram loses three
correct points, so the stricter per-service rule still blocks promotion.

In an interview, say: “This is evidence that the representation/classifier
combination is promising, not proof of reliable live accuracy. We changed both
the feature layer and classifier, so we cannot attribute the gain to either
one alone. The recordings are reused development data; the app retains its
previous default.” The new artifact works without training files, but its raw
scores are uncalibrated and it always withholds an accepted service label.

The [preceding local adaptation study](browser-selection-followup-results.md) is a
useful example of an honest model decision. The forest improves Instagram but
loses YouTube recall, so we reject it even though its combined F1 rises. It gets
47 of 63 repeated prefix points right versus the earlier forest's 46. Those
points come from seventeen connections across three visits, not 63 independent
tests. The recording gap was resolved and the experiment completed; quality
still fails the predeclared rule. We preserve the result and stop instead of
turning a development score into a live-accuracy promise.

To explain [why a capture is usable](capture-checks.md), separate data quality
from model accuracy. The prepared session must match the interface/model/time
rules; Chrome supplies a separately matched origin reference; packet sizes must
agree within each direction; counters and saved-model replay are audited.
Unknown or ambiguous references stay unlabelled. A wrong model prediction does
not disqualify an otherwise usable recording. No classifier receives the
browser hostname as an input. Passing these checks is not a guarantee of perfect
labels, loss-free capture or generalisation.

We distinguish three timing questions: how long we watch traffic, how long
the model takes, and how long an event takes to reach the browser. The latest
[CPU stage check](engineering-checks-20261028.md) measures B17 forward at about
15.7 ms median and full prediction at 16.3 ms on this laptop. A three-second
traffic window still needs its observation wait. New window-event delivery
instrumentation starts at server emission; it is separate from model timing
and does not measure browser paint. Software tests can verify this accounting
without proving new live latency or better classification.

We also [tested whether watching for longer helps](browser-window-study.md).
On the same fourteen old development connections, a first-thirty-datagram
control gets eleven right and the one-/three-second models each get nine.
Longer observation is a useful hypothesis, but this feature/model combination
did not improve results. It stays disabled. These are browser-side records,
not a fresh live accuracy test; two services and a handful of visits cannot
represent general internet traffic.

The latest [research alternatives](approach-comparison.md) are now tested on
reused development data. Ordered nearest neighbours get 25/54 checkpoints right;
an official frozen pretrained encoder gets 43/54, compared with the existing
forest's 45/54. Neither passes its fixed local comparison gate. This shows why
"pretrained" is a hypothesis to test, not a reason to deploy. The pretrained
weights also overlap our old final-test week, so that test cannot grade them
independently. Their similarity values are not correctness probabilities.

The screen also distinguishes a service associated with name evidence from a
service estimated by the packet model. They can disagree. Optional one-/three-
second statistics describe actual observed traffic but do not yet classify
activity. Explain the observation budget: a model using thirty packets may see
only a fraction of a second even when someone browses for a minute. A live
statistics path, a trained classifier and independently measured useful accuracy
are three separate achievements. A fixed browser-side window classifier has now been fitted and rejected;
useful accuracy and capture-side transfer remain unresolved.

The latest [browser study](browser-calibration-failure.md) is a useful interview
example: a model can improve on development data and still fail on a new visit.
Our first adapted forest got 22/27 development prefix predictions right, then
only 5/26 Instagram points right during separate calibration. We kept the
failed result and did not enable it. A follow-up trains on earlier visits and
uses those failed recordings as explicitly retired development data. Its
forest improves at three fixed seeds. Its [fresh calibration](browser-calibration-02.md)
gets 17/22 Instagram and 23/24 YouTube points right, but still fails the required
tradeoff between accepted errors and coverage, so it stays disabled. Reusing
those recordings as a new final test would be misleading. Only packet sizes,
directions and gaps reach the model; browser names supply separate references.

One later hypothesis also failed: adding ordered packet features to the forest
improved its historical dataset score but worsened Instagram development recall.
We stopped that experiment at its first-seed gate. Explain why per-service
results matter: an easier service can improve the average while another gets
worse. There is no validated local repair yet; reporting failures is part of
an honest evaluation, not a reason to rename development results as test results.

The [next collection cycle](browser-development-v3.md) fixes each recording's
role before it begins. Feed, Reels and Explore/profile visits add training
variation; later visits stay separate for model selection. Counts and time
gaps are checked before training. These are planned data roles, not accuracy
results or a promise that more examples will fix the model.

We also [tested a simple packet-only heuristic](packet-rule-comparison.md):
compare a prefix with typical class profiles fitted only on training data.
It got 26/54 development prefix cases right versus the forest's 45/54. A stricter
interval rule answered 19 cases but got four wrong. It was faster on CPU and
still unsuitable as a replacement. An activity rule saying "streaming" would
answer a different question from "which service?"; it cannot simply be renamed
"YouTube." The internship's full naming/protocol cascade was not tested as
part of this packet-only baseline. These are development findings, not a new
independent test or a conclusion that every heuristic fails.

## A truthful sixty-second explanation

“NetEmbedAI is a local tool for investigating which supported service an encrypted QUIC flow resembles. It looks at early packet sizes, directions and timing. A Python service applies saved preprocessing and a classifier, while a browser shows arriving metadata, alternatives and uncertainty. I compared a compact sequence model with a Random Forest. A matched three-seed comparison selected augmented cross-entropy; contrastive loss did not reliably help. On a held-out CESNET week, clean macro-F1 rose from 0.791 at five packets to 0.886 at thirty. Those balanced dataset results did not transfer reliably to my Wi-Fi. User-started recordings exposed confident errors using independent browser references. Adaptation improved fresh raw predictions to 40 of 46 calibration points, but confidence filtering still failed our per-service error and coverage rules. I kept the replacement disabled and preserved the failures. A reliable local repair remains unfinished.”

Update the status sentence as remaining gates are satisfied. Personal contribution: **[write only the parts you personally implemented, reviewed or tested]**. Do not claim an internship role, research novelty or sole ownership without evidence.

## The basic ideas

A **packet** is one small unit of network traffic. A **flow** groups related packets traveling between two endpoints. **QUIC** is an encrypted transport commonly carried over UDP; not all UDP traffic is QUIC. A **service label** is a category such as a supported video or messaging service. It is not an identification of a person, page or message.

Encryption hides content but leaves observable metadata. For example, request and response packet sizes and gaps may correlate with a service's behavior. Those correlations may change across devices, versions and networks. The application does not decrypt payloads or look up domains/IPs to produce labels.

**Normalization** puts differently scaled features into a range the model can learn from. Here we log-transform time/size and standardize with statistics fitted only on training packets. **Training** learns parameters; **selection/development** chooses a model; **calibration** chooses a score threshold; **test** estimates performance after decisions are frozen. Reusing test outcomes to tune the model would make the test score optimistic.

A **TCN**, or temporal convolutional network, slides learned filters over a sequence. Dilations let those filters connect observations farther apart. A causal filter cannot read later packets. Padding fills unused batch slots, so the model must read the last actual packet, not the final padded slot. Tests directly check that future values and padding cannot change an earlier prediction.

**Augmentation** modifies training examples. This project uses bounded timing changes, observation removal with reconstructed gaps, and abstract additive size edits. **Contrastive loss** additionally encourages examples with the same label to have similar representations. It adds complexity and is justified only if matched comparisons show a repeatable useful improvement.

**Macro-F1** gives every service equal influence, so a common class cannot hide poor performance on a rare one. A confusion matrix shows which classes are mixed up. **Coverage** is the fraction of predictions accepted by the decision policy; accepted error is the error fraction among those accepted predictions. Lower coverage can buy lower error. A confidence score is not automatically a calibrated probability of being correct.

**Latency** needs a boundary: observing five packets takes network time; queuing takes additional time; preprocessing and model execution take compute time; delivery and rendering take more time. A fast neural forward pass does not establish a fast live system.

## Trace one request

1. In Replay, the user provides an authorized recorded JSON sequence and selects five packets. Reference labels, if maintained separately, never enter the request.
2. React sends exactly that prefix to POST /predict. A stale-response guard prevents an older request from replacing a newer selection.
3. FastAPI validates schema, finite values, directions, positive sizes and the first zero interval. Invalid inputs receive a validation error, not a model uncertainty result.
4. The predictor uses bundle statistics, pads internally and passes the actual length to the TCN. The classifier returns scores in the saved label order. The forest path shares the same request/response contract.
5. The saved policy accepts a label or returns insufficient evidence/confidence. The response includes alternatives, artifact identity and measured pipeline time.
6. The screen renders that response. In Live, TShark arrival events feed the same predictor via a bounded queue; they do not replay a saved example.

## Twenty likely questions

1. **Why can encrypted traffic reveal anything?** Encryption protects content, while observable sizes, directions and timing can retain statistical patterns. Their usefulness must be measured.
2. **Why only QUIC?** The dataset and feature contract target QUIC. Generalizing to TCP/TLS would require new data and validation.
3. **Why not use the destination IP or domain?** Those can leak identity and shortcut the learning task. Endpoints are used only for transient flow grouping.
4. **Why early packets?** They permit decisions before the flow ends. Evaluate 5/10/20/30 separately; never use whole-flow totals to claim early classification.
5. **Why a causal TCN?** It processes prefixes without future dependence and is compact. It is a reference candidate, not a predetermined winner.
6. **What was wrong with the old readout?** It read the final padded slot. New code gathers the last valid timestep and needs retraining.
7. **Why keep a Random Forest?** A simpler model might match quality and be easier to operate. It receives summaries from the same prefixes and splits.
8. **Does contrastive learning help?** Not enough to retain here. With the same augmentation, its three paired development changes were +0.0024/−0.0040/−0.0010. The strong augmentation gain cannot be assigned to the contrastive loss.
9. **How do you avoid leakage?** Chronological partitions, training-only fitting, separate calibration, duplicate/group checks and an explicit final-test gate.
10. **Are the splits perfectly independent?** Not proven. Native export lacks host/session identity; correlated flows and host overlap must be disclosed.
11. **Why macro-F1 instead of accuracy alone?** It emphasizes every class equally. Both and per-class results should be reported.
12. **What does low confidence mean?** The policy refuses a commitment; it does not establish that the service is unknown.
13. **What happens when the model is missing?** Readiness fails, capture cannot start, and the UI reports the operational problem. No random fallback exists.
14. **How does live capture start?** The local user selects an interface and presses Start. Installation and tests never start capture.
15. **How do you identify QUIC?** TShark dissector evidence and a supported client Initial are required for a new flow. UDP/443 alone is only a candidate filter.
16. **How do you prevent memory growth?** Cap active flows, store at most 30 packets each, bound inference/event queues, coalesce pending prefixes and expose dropped work.
17. **What happens on Stop or tab close?** The service terminates the capture process tree and joins tasks. Software lifecycle tests and four real user-started Stop checks passed. Actual disconnect cleanup has software tests; it is not a separate measured local trial.
18. **Does the public dataset score predict my Wi-Fi accuracy?** No. Capture point, network, device and app changes can shift feature distributions. Local testing is separate.
19. **Are the stress tests real adversarial attacks?** They are a bounded set of declared feature/measurement changes. Size padding is abstract, and observation loss is not retransmission behavior. No general robustness guarantee follows.
20. **What can you demonstrate today?** Software tests, the frozen default and held-out CESNET report, API and replay predictions, the UI, exact offline RFC parser output, and one genuine user-started Wi-Fi session with model-event acknowledgments and Stop cleanup. Independently labeled local accuracy and live ipfixprobe feature parity remain pending.

## Practice an honest demonstration

Start the service with the selected local bundle and explain its model identity and saved preprocessing. Run the deterministic tests and show the offline fixture comparison. Open the screen and distinguish Live from Replay; use a recorded flow for a prefix prediction without describing it as live capture. Show the frozen decision, then the held-out report and its 5/10/20/30-packet quality. Describe the real user-started session as a functional check with measured latency, not as a service-accuracy study. Explain why CESNET results do not establish local-network accuracy. Finish with the remaining labeling and feature-parity gates and the reproduction commands.

For a defensible next local test, follow [Testing on your laptop](local-testing.md).
The optional handshake reference is a separate evaluator using CESNET's published
hostname map. It never becomes a model feature or changes an output. A visible
reference mismatch is useful evidence to investigate, not a reason to hide a flow.
The feature export supports checking local payload sizes, timing and direction;
independent exporter parity still needs verification.

For ECH/GREASE traffic, an offline browser-log matcher can use the browser QUIC
session origin plus exact connection tokens and packet sizes/times as a separate
reference. It preserves model decisions and refuses ambiguous attribution. Its
software fixtures pass, and a real Chrome/Wi-Fi diagnostic trial matched four
YouTube connections. Only one of their eleven live prefix decisions committed
to a label (correctly YouTube); the rest withheld a decision. Eight other accepted
predictions occurred on references outside the supported set. Explain this as a
closed-set limitation, not unknown-app detection or successful local deployment.
The full record is in [browser attribution](browser-attribution.md). Independent
real-trace parity and a held-out local study remain pending.

The subsequent [local diagnosis](local-diagnosis.md) found a concrete measurement
bug: subtracting large floating-point timestamps slightly changed tiny packet
gaps. Integer-nanosecond subtraction now matches independent ipfixprobe output
exactly on one existing 30-packet recording prefix. Explain the limit clearly:
correcting a measurement bug does not prove an accuracy improvement. Timing
rounding and a browser socket-view replay still mostly withheld decisions. Old
phone recordings were discovered, but the user does not remember their origin
and thinks they were downloaded. They are excluded from training and local-quality
claims. Keep separate, attributable recordings for
development and held-out checking, and never label every flow from the filename.

The [Instagram diagnostic](instagram-trial.md) is a clear example to explain in
an interview: four independently attributed connections produced eight live
decisions. Three accepted a label, all wrong; five withheld. The software replayed
all 71 retained predictions exactly, but that consistency did not make them
correct. The plain TCN and forest were not reliable fallbacks. Say plainly that
the model transfers poorly in this check and that a high score is not a
correctness guarantee. New attributable development data and a separate held-out
local evaluation are needed before claiming a repair. Passing software tests
and a good stored-benchmark result cannot substitute for that evaluation.

The next [training pilot](quicext25-pilot.md) tested that lesson: a newer public
dataset, a 20-epoch supervised TCN and a forest still did not repair the local
errors. The forest scored well against the newer dataset's reference labels
but accepted wrong labels on both local services. Meanwhile, an independent
browser-socket check matched all sent and received payload sizes within each
direction. Explain this as a remaining transfer problem with partial feature
parity evidence, not proof of its exact cause. More architectures or a higher
model score would not replace representative labelled data and separate tests.
