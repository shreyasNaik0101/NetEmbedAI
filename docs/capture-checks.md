# How a recording is judged usable

“Usable capture” means it passes the declared recording, reference and packet
checks. It does not mean that the current classifier guessed correctly.

1. **The right session.** Before capture, an intent fixes its training/selection
   role, chosen interface, model identity and intended activity. The stopped
   export must match that intent, include the reference channel and start after
   preparation. A previous or unplanned session cannot silently take its place.
2. **Eligible packet metadata.** The live parser requires dissected QUIC and a
   fresh client Initial; a UDP/443 port alone is insufficient. Units, direction,
   valid sizes and timing follow the shared contract. A usable example needs at
   least five actual observed packets. Unsupported/malformed inputs are counted.
3. **An independent browser reference.** Chrome's stopped NetLog is matched to
   the captured connection using pseudonymised endpoint pairs, a fixed start-time
   window and at least two distinct receive matches. Only an unambiguous mapped
   browser-origin reference can supply a supported service label. Opening a
   YouTube tab does not label every background connection YouTube.
4. **Packet consistency.** The browser socket log must contain the expected early
   datagrams. Ordered payload sizes must match separately for outgoing and incoming
   directions, with no missing prefix entries. Browser and network capture clocks
   and merged ordering can differ; this is not full on-wire timing/order parity.
5. **A preserved audit.** Original files are checksummed and not overwritten.
   Saved predictions are replayed through the same bundle and compared to the
   actual recorded outputs. Drops, coalescing, errors, evictions and timing are
   retained. Reproducing a wrong prediction proves consistency, not correctness.

The classifier receives only packet sizes, directions and intervals. Chrome's
origin/reference is used separately for data labelling and diagnosis; it is not
fed into the packet classifier. Eligibility never depends on the intended app,
model's chosen label or confidence. Wrong predictions and all reference refusals
remain recorded. Keeping only successful predictions would bias the evidence.

For example, `youtube-dev-03` retained 42 connections. Eight had usable mapped
YouTube references and passed the packet checks, supplying 240 prefix packets.
The other 34 were outside the supported map, ambiguous, unmapped or unmatched;
they were not assigned YouTube merely because a video was playing. The complete
inventory is preserved in the [collection record](browser-development-v3.md#fourth-recording-archived--29-october).

These checks provide defensible browser-referenced examples. They cannot prove
perfect labels, loss-free capture, that every connection carried only one site's
content, or generalisation to another browser/network. Repeated prefixes within
a connection and connections within a visit are correlated. Training collection,
model selection, calibration and final evaluation retain separate roles; only
later independent evidence can judge a proposed replacement.
