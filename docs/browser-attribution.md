# Checking local predictions with a browser connection log

The passive hostname checker can refuse ECH/GREASE traffic. Its refusal does not
prove the hostname was encrypted, identify the actual app, or explain an unexpected
model prediction. The next reference source is the browser's own QUIC session log.
It is a separate evaluator and never changes a prediction.

## Prepare one controlled trial

Use the rebuilt app and a fresh user-started capture. The earlier exports lack
connection-matching metadata and cannot be retroactively attributed with this tool.
The following is a diagnostic trial, not a final local-accuracy study.

1. In Chrome, visit `chrome://net-export/`. Leave the default **Strip private
   information** mode selected; keep raw bytes and sensitive-data modes off.
   Press **Start Logging to Disk** yourself. Save to
   `artifacts/local/chrome-netlog-TRIAL.json` in the repository, substituting a
   unique trial name. Keep that Chrome tab open.
2. In NetEmbedAI, refresh the page, select the active interface, tick the separate
   reference checkbox and press **Start capture** yourself.
3. Open a fresh supported service connection in another normal Chrome tab and use
   it for about 30 seconds. Start both logs before the target connection. Existing
   pooled connections may lack a new session beginning and remain unmatched;
   don't assume that reopening a page guarantees a new QUIC session.
4. Press **Stop** in NetEmbedAI, then **Stop Logging** in Chrome. Save the NetEmbedAI
   trial evidence before starting another capture; the next Start replaces it.
5. Run the offline matcher, or give the local agent the saved log path so it can
   read the app's current evidence and run the command. No upload is required.

This follows Chromium's [NetLog capture procedure](https://www.chromium.org/for-testers/providing-network-details/).
Default logs omit raw packet bytes, but still contain browsing metadata such as
origins and endpoints. Keep them local and outside Git. The matcher reads the
file locally; it sends nothing to a server or cloud service. The generated report
omits raw hostnames, addresses, connection IDs and the session matching key.
Do not disable ECH, QUIC, browser security or privacy settings for this test.

From the repository root, with the service currently on port 8001:

~~~powershell
Invoke-WebRequest http://127.0.0.1:8001/capture/local-evaluation -OutFile artifacts/local/capture-TRIAL.json
.venv/Scripts/netembed.exe attribute-netlog --evidence artifacts/local/capture-TRIAL.json --netlog artifacts/local/chrome-netlog-TRIAL.json --output artifacts/local/reference-TRIAL.json
~~~

Choose a new output path for each run; the matcher refuses to overwrite a report.
The reference report binds both input files with SHA-256 and keeps every retained
capture flow, including unmatched rows, refusals and mismatches. The first actual
Chrome trial is recorded below; software fixtures remain separate evidence.

## How matching works

Only explicit reference mode adds a random session key, a keyed pseudonym of each
UDP endpoint pair, and its first-packet timestamp to the bounded trial evidence.
The addresses themselves are not exported. These are connection pseudonyms,
not a guarantee of anonymization; keep the matching key and raw NetLog local.

The matcher reads Chromium's per-file event constants and clock offset, takes the
origin from a `QUIC_SESSION` beginning, then correlates its received datagrams:

- Exact session-keyed endpoint-pair token match, including both UDP ports.
- QUIC session beginning within 2,000 ms of the captured first packet.
- At least two distinct one-to-one received-packet matches with equal UDP payload
  sizes and timestamps within 100 ms. Millisecond-identical duplicate log events
  cannot supply extra matches.
- A unique browser session candidate. Changed endpoint tuples, reported successful
  migration, duplicate session beginnings, missing required fields, clock gaps or
  ambiguous matches stay unverified.

These gates are fixed before real trials. They are matching heuristics, not a
cryptographic proof of app ownership. A browser session can pool several origins,
and proxies, VPNs, NAT/capture point changes, coalescing or sleep can prevent a
match. The reference identifies the browser QUIC session's initial origin, not
every tab, request or content stream using that connection. The service category
is mapped through the separately checksummed CESNET map; missing or overlapping
map rules remain unverified. Neither the intended demo app nor the model's output
chooses a matching candidate.

The parser supports documented `QUIC_SESSION` host/port and
`QUIC_SESSION_PACKET_RECEIVED` self-address/peer-address/size fields, with
`logEventTypes`, `logEventPhase` and `timeTickOffset` constants. Other or redacted
schemas fail clearly or yield unmatched references. Sources checked on
25 October 2026: Chromium's [event schema](https://raw.githubusercontent.com/chromium/chromium/main/net/log/net_log_event_type_list.h),
[QUIC event implementation](https://raw.githubusercontent.com/chromium/chromium/main/net/quic/quic_event_logger.cc)
and [clock conversion](https://chromium.googlesource.com/chromium/src/+/HEAD/net/log/net_log_util.cc).

Default input limits: 64 MiB per JSON file, 500,000 events, 4,096 QUIC sessions, 512 matching
receive records per session/tuple and 16 candidate sessions per capture flow.
Exceeding attribution limits cannot select a convenient label. Capture evidence
remains capped at 256 flow windows and four model checkpoints each; evictions are
reported. File order does not replace source-ID matching, and endpoint identities
never become model features.

For a larger Chrome line-oriented export, explicitly add `--stream-netlog` to
`attribute-netlog`. This bounded reader allows at most 256 MiB raw input, two
million source events and 2 MiB per line/footer, retaining at most 64 MiB and
500,000 reference events. It validates the complete file and hashes the raw
source. It keeps all QUIC-session, received-packet and successful-migration
events by event type, without filtering by label or prediction. Other matcher
limits remain unchanged. It rejects unsupported formatting and oversized
records. In the parity helper, combining `--stream-netlog --socket-mode` explicitly
retains all four UDP socket event types under the same projection caps; the
default attribution reader still omits them. The [socket follow-up](quicext25-pilot.md)
exercised this profile on the actual Instagram log. The [original Instagram trial](instagram-trial.md) exercised
this path; the earlier YouTube report was also reproduced identically apart
from reader metadata.

## Interpreting the report

`reference_counts` inventories all retained capture flows by attribution outcome.
`agreement_by_prefix` and `agreement_by_service` use only mapped browser-origin
references and state the number of predictions, accepted predictions, accepted
mismatches, coverage and top-ranked reference agreement. Refusals stay in the
referenced-prediction denominator. Unmatched/unsupported references remain in the
inventory, not silently counted as successes.

## First actual Chrome trial: 25 October 2026

The user started and stopped both logs on this Windows/Wi-Fi host. Chrome
155.0.8059.80 produced 165,965 events and 28 QUIC sessions. The unchanged matcher
read every event without schema errors and retained all 31 capture flow windows:
four mapped to YouTube, ten had overlapping service-map rules, ten mapped outside
the supported set, four had invalid/migrated connection identities and three
remained unmatched. No attribution tolerance or mapping rule was changed after
seeing the results. The four YouTube references each had a unique session and
8–12 distinct matching receive records. This verifies this real browser-log path
on one host, not arbitrary browser schemas or tab/request identity.

Those four flows had eleven delivered prefix predictions. Ten withheld a label;
one accepted YouTube at ten packets (score 0.6718, threshold 0.67). There were no
accepted mismatches on these eleven checkpoints, but that very low coverage and
four-flow sample cannot establish useful local accuracy. The top-ranked label
could still be wrong when a commitment was withheld. Eight accepted predictions
on the ten outside-supported-set reference flows named Discord, WhatsApp or
YouTube. This is evidence of the closed-set limitation: the score threshold does
not identify unsupported services. Those predictions are retained and are not
counted as successful supported-service recognition.

All 99 saved live predictions replayed with exactly equal alternative scores and
unchanged decision labels using the frozen B17 artifact. An additional explicitly
offline pass fills prefixes omitted by live coalescing. For the four available
flows at 5/10/20 packets, top-ranked YouTube agreement was 2/4, 3/4 and 4/4;
at 30 packets it was 1/2. Accepted counts were 0/4, 1/4, 0/4 and 0/2. This is one
diagnostic development session, not an independent held-out quality study.

Capture stopped cleanly with no queue drops, 20 coalesced checkpoints and zero
evidence-history evictions. Active flow state expired/evicted 25 entries; that
counter is separate from the retained evidence history. All 99 model events were
acknowledged. Capture-to-browser receipt p50/p95 was 259.28/506.44 ms; paint time
was not measured. The raw local logs remain ignored by Git. Session ID is
`38502a842a1f4afdacf60216daa76aad`; artifact ID is
`18c43fe12262b81d4a3001df150a278865f3908ddd3aab934822fc0c9e5750fb`.

Local files and SHA-256:

| File under `artifacts/local/` | SHA-256 |
| --- | --- |
| `capture-youtube-01.json` | `41096905dadc660fb519d1b93c072629cfdf926ae319676ef825406bb62b9f04` |
| `chrome-netlog-youtube-01.json` | `fc5b30f87045b649ba2eb707e81097f7f64ad7b43f27e5f60b80b6ec5527281b` |
| `reference-youtube-01.json` | `94f3783d24f7f43affe3b51efd662a56ca95b985dfc0c891b18a4393de5508eb` |
| `audit-youtube-01.json` | `93bc577ec4074f9ef9f352bff002e80da563f17237e04d4481658d6a18947c85` |
| `timing-youtube-01.json` | `f14325bb9a849615d35e72c305abb773e4101f1c0c1df0d20b6493b16c49396b` |

To repeat the audit on these same saved files, choose a new output path:

~~~powershell
.venv/Scripts/python.exe scripts/audit_browser_trial.py --evidence artifacts/local/capture-youtube-01.json --reference artifacts/local/reference-youtube-01.json --bundle experiments/full-real/20261024-151720-3532794c/bundle --output artifacts/local/audit-youtube-01-repeat.json
~~~

The audit checks evidence and artifact identities, original packets/predictions,
and numerical live/replay parity. It neither captures nor fits anything. Real
captured-trace exporter parity, historical timing quantization, and separate
development/held-out local sessions spanning two supported services remain gates.

## Ordered receive-prefix consistency check

The subsequent offline check compares every early received packet on the four
mapped connections, using the first N browser receive events in stable timestamp
order (file order breaks ties). It retains distinct equal-millisecond datagrams
and does not search ahead for equal sizes or discard mismatches. All **59**
server-to-client packet sizes matched in order, with zero missing browser prefix
records. Absolute browser-event versus capture timestamp difference was
0.625/1.223 ms p50/p95, maximum **1.384 ms**. This narrows the investigation:
these receive prefixes show no gross byte-count, packet omission or timestamp-
unit discrepancy. It does not explain weak model decisions.

The 53 client-to-server packets were not compared: browser sent-packet logging
can involve separate QUIC/coalesced-packet events, and this checker does not
assume their sizes equal UDP datagram sizes. Reverse-only timing comparisons do
not validate bidirectional inter-packet gaps, historical integer-millisecond
conversion, or ipfixprobe output for a real captured trace. These four connections
were already selected using size/time anchors for attribution; this is a
consistency check conditioned on that selection, not unbiased quality evidence.
All other attribution outcomes remain in the saved inventory.

~~~powershell
.venv/Scripts/python.exe scripts/check_browser_receive_parity.py --evidence artifacts/local/capture-youtube-01.json --netlog artifacts/local/chrome-netlog-youtube-01.json --reference artifacts/local/reference-youtube-01.json --output artifacts/local/browser-receive-parity-youtube-01-repeat.json
~~~

The saved report `artifacts/local/browser-receive-parity-youtube-01.json` has
SHA-256 `9787a7e1cad5d80af0f82bddbc9c7ee3bf43bf8dfb5ff2fc6ba365bef696b26e`.
Inputs are checksum-bound and the complete origin correlation is rerun before
comparison. Four software regression tests exercise repeated timestamps, size
mismatches, missing records and large clock disagreement; they are not extra
live evidence. No capture, model fitting, preprocessing or policy change was
performed. The official [feature definitions](https://cesnet.github.io/cesnet-datazoo/features/)
and [original dataset article](https://pmc.ncbi.nlm.nih.gov/articles/PMC9851865/)
describe payload size, directions and time units, but do not by themselves verify
the historical integer-millisecond conversion used for these CSV records.

For example, a mapped YouTube browser reference alongside a WhatsApp model label
is retained as an accepted mismatch. An unreferenced flow cannot be declared a
YouTube mistake or dismissed as background traffic. Save exploratory failures;
verify independent feature parity before adaptation, freeze changes using local
development sessions, then assess separate held-out sessions of at least two
available services. This report does not replace the frozen CESNET evaluation.
