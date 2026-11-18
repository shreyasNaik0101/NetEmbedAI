# NetEmbedAI: a beginner-friendly interview guide

## The short explanation

“I built a local app that explores service recognition from encrypted QUIC
traffic. It looks at the sizes, directions and timing of early packets, not
their contents. The user deliberately starts a TShark capture, the backend groups
eligible packets into flows, and a model scores the early prefix. A screen shows
the actual arriving metadata, model alternatives and timing.”

“It is a prototype. A small local three-service raw-guess test was encouraging,
but a later accepted-label test failed. I keep the showcase policy unfitted and
show guesses without accepting a service label. I can explain both the result and
what would be needed to improve it.”

## How the pieces fit

1. **Capture:** the user picks an interface and presses Start. TShark filters
   UDP/443 candidates and identifies QUIC. A new flow needs a supported QUIC
   Initial; UDP/443 alone is not a QUIC label.
2. **Flow:** packets are grouped by endpoint pair while capturing. The model sees
   only each packet's UDP payload size, direction and inter-arrival time.
   Addresses, domains and process names do not enter the model.
3. **Prediction:** the showcase forest waits for ten packets and uses exactly
   that prefix. More packets can appear in the display, but this model's answer
   does not use them. Its bundle includes weights, preprocessing and label order;
   inference doesn't need the training dataset.
4. **Display:** the page shows arriving packet metadata, the alternatives and
   measured event timing. A model score is not the chance the answer is right.
   The unfitted showcase policy withholds accepted labels.
5. **Stop:** the user clicks Stop, or the bounded session ends on timeout or a
   lost viewer. Replay is a separate mode for saved metadata, not live traffic.

## Evidence you can quote

* **Historical benchmark:** a separately selected augmented TCN achieved
  macro-F1 0.84285 at ten packets and 0.88636 at thirty on the held-out CESNET
  week. This is a stored-dataset result for the TCN, not the local forest.
* **Fresh local raw guesses:** the fixed-ten forest ranked the correct service
  first for 7/7 YouTube, 4/4 Instagram and 5/5 Spotify connections in three
  small visits on one declared hotspot. The Instagram viewer timed out; this
  does not establish uninterrupted delivery or general accuracy.
* **Later policy check:** threshold zero accepted one YouTube connection as
  Spotify in the final visits, failing the frozen zero-error-per-service gate.
  The other target outcomes were 6/6 correct accepted Instagram and 4/5 correct
  accepted Spotify, with one Spotify withheld. The policy was not promoted.
* **Timing experiment:** a matched jitter-trained forest passed development
  gates at seed 17 but failed them at seeds 42 and 123. The examples were
  previously exposed and the perturbation was an abstract stress, not a proven
  network simulation. The candidate was not promoted.
* **Parser check:** on one deliberately user-started selected connection, the
  current adapter and ipfixprobe agreed on the first 30 packet sizes, directions
  and gaps when reading the same saved PCAP. This is not a service-accuracy
  result, and the selected connection's service was not asserted.

## Questions an interviewer may ask

**How can you learn anything from encrypted traffic?** Encryption protects the
content, but packet lengths, directions and timing are still observable and can
carry statistical patterns. Those patterns can change with networks and apps.

**Why not use the hostname or IP?** That can turn the task into an identity
lookup. Endpoint information groups a flow; the classifier receives packet
metadata only. An optional browser log supplies a separate reference for tests.

**Why compare a TCN and a forest?** The compact causal TCN is the neural
reference; a forest on the same prefix data is a simpler baseline. Local
adaptation was investigated separately, with evidence and limits recorded.

**What did you fix in the neural model?** The old encoder read a padded final
slot. The corrected readout uses the last valid packet, and changed semantics
require retraining and testing across prefix lengths.

**Did contrastive learning help?** In the matched comparison, CE+SupCon did not
consistently improve over cross-entropy with the same augmentation. The observed
augmentation gain cannot be attributed to contrastive loss alone.

**Why is the policy unfitted?** Correct top guesses do not automatically make a
reliable acceptance rule. The separately tested threshold accepted a wrong
YouTube prediction. The showcase therefore shows experimental scores and does
not commit to an accepted service label.

**Does the app detect unknown apps?** No. Withholding a label does not prove a
service is unknown, and the model's list of labels does not establish local
reliability for each one.

**What would you improve?** Collect representative, independently attributed
development sessions across more devices, networks and services; investigate
capture/exporter differences; compare fixed candidates against a control; then
test the chosen model and acceptance policy on new held-out sessions. There is
no guarantee that more recordings alone will fix the problem.

## A demo sentence

“This is a real user-started capture, and these are actual packet metadata and
model scores. The acceptance policy is intentionally unfitted because the
previous fitted policy failed its final check. The benchmark numbers and this
local result are separate.”

Use the [demo runbook](demo-runbook.md) for commands and the
[showcase model card](showcase-model-card.md) for checksums and boundaries.
The longer chronological guide is preserved in
[interview guide history](interview-guide-history-20261110.md).
