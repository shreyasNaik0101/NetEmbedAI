# Diagnostic review of two final-test outcomes

This is a descriptive inspection of the already-scored final set, not a new
selection, training, calibration or final test. The result and failed gate in
`artifacts/local/ten-packet-policy-v1/final-report.json` remain unchanged. No
threshold or model parameters were chosen using these outcomes.

## YouTube accepted as Spotify

The independently browser-mapped YouTube flow `f54b14793ada` had a native
ten-packet top guess of Spotify (model score 0.5610), with YouTube second
(0.3675). The fitted policy accepted Spotify because the top class was in its
three-label scope and its score threshold was zero. The mistake therefore has
two observable parts: the model ranked Spotify above YouTube, and the policy
did not withhold that in-scope top guess. Scores are not probabilities of
correctness.

The reference matched one browser QUIC candidate and a unique socket. Browser
and capture prefixes had no missing packets and their ordered payload sizes
matched within each direction. The merged cross-direction sequence had
disagreements at indices 19 and 20 of the 30-packet comparison. This distinction
matters: the existing QC gate does not prove the two sources agree on every
interleaving or timing value. The reported disagreement indices are later than
the model's ten-packet input, but this is not proof that all input semantics are
perfect. Capture reported zero drops, and the native prediction reproduced in
the existing audit. These checks support the recorded result; they cannot prove
why the model ranked this flow incorrectly or exclude every attribution error.

## Spotify withheld

The independently browser-mapped Spotify flow `27ed1f70cb50` had Outlook as
the model's top guess (0.3087), followed by Snapchat (0.2247) and YouTube
(0.1856). Because Outlook is outside the three allowed accepted labels, the
policy withheld the label with reason `outside_policy_scope`. This withholding
was due to the class restriction, not a score-based confidence threshold. The
model also failed to rank Spotify among its top three alternatives on this flow.

The reference matched one browser QUIC candidate and a unique socket. Again,
there were no missing prefix packets and ordered payload sizes matched within
each direction. The merged comparison showed direction disagreement at indices
6, 9, 10, 11, 26 and 27, and size disagreement at 6, 8, 9, 10, 11, 26 and 27.
Some disagreements occur around the first ten packets, so a difference in
cross-direction ordering is a possible contributor to investigate, not a
confirmed explanation of the model's guess. Browser and capture observe packets
at different points and timestamps; these comparisons do not identify which
ordering is the model's correct input. No change to eligibility or scoring is
justified after seeing this outcome.

Both flows retained 30 packets, but the tested model deliberately uses only the
first ten. Its 20- and 30-observed-packet events repeated the ten-packet scores;
they do not demonstrate what a separately trained longer-prefix model would do.
The independent NetLog reference is used to check the outcome, not as a model
feature.

## Practical next work

The final set exposed a ranking error and a separate scope-based refusal, with
an ordering uncertainty in the Spotify case. It cannot tell which proposed fix
will generalize. Before requesting more recordings, investigate packet-order
semantics and feature-parity fixtures using existing non-final development data;
compare any candidate on predeclared development inputs and reserve new,
independent evaluation data for a later decision. A confidence cutoff chosen
from these final errors would leak test information and invalidate this result.
Do not relabel the failed screen or promise that more data will fix it.

Evidence: `final-predictions.json`, each visit's `reference.json`,
`socket-parity.json`, `audit.json` and `capture.json` under
`artifacts/local/ten-packet-policy-v1`. These local browser/capture artifacts can
contain sensitive metadata and should remain private.
