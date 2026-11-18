# YouTube failure diagnosis — 1 November 2026

Follow-up: the [separate size-robustness experiment](size-robustness-study.md)
is complete. Both treatments improve abstract stress metrics in one seed, but
neither passes all clean/class retention gates. It stops without a replacement,
new policy or further recordings. This diagnosis and failed calibration remain
unchanged evidence; their packets were excluded from that training/selection.

**The forest is strongly sensitive to a real packet-size change that coincides
with an IPv4-to-IPv6 change between these recordings.** The selected packet sizes
agree with independently recorded browser socket metadata. This analysis found
no size-extraction error for those matched flows. It does not prove that IP
family alone caused the real-world quality change, or establish a repaired model.
No retraining, new confidence threshold, capture or deployment was performed.

This is explicitly **post-hoc diagnosis**, after examining the failed calibration.
The [bounded declaration](../configs/youtube-failure-diagnostic-v1.json) records
what was already known before the additional browser replays and abstract size
sensitivities. Earlier comparison/calibration decisions remain sealed. These
recordings cannot become an untouched final test for a repair informed by them.

## What changed in the actual recordings

All13 YouTube connections from the three named visits were included. Connections
were matched to browser UDP sockets by the existing exact session-salted endpoint
token and start/reference checks. The report exports IP family only, with no
addresses, domains or endpoint identities as classifier features.

| Visit | YouTube connections | Matched local/peer family | First UDP payload | Raw correct at10 /20 /30 |
| --- | --- | --- | --- | --- |
| `paired-yt-01`,31 October | 3 | IPv4/IPv4, all3 | 1,250 bytes, all3 | 3/3,3/3,3/3 |
| `paired-yt-followup-01`,1 November | 4 | IPv4/IPv4, all4 | 1,250 bytes, all4 | 4/4,4/4,4/4 |
| `forest-cal-yt-01`,1 November | 6 | IPv6/IPv6, all6 | 1,230 bytes, all6 | 3/6,0/6,4/6 |

The packet metadata itself is different; this is not a guessed family from size.
All three logs report the same browser version,155.0.8059.80, and all captures
use `tshark-prefix-ns-v3`, interface9, with zero queue drops/reordered packets
and no recorded capture error. These counters do not establish completeness of
every on-wire packet. All39 unchanged capture probability vectors replay exactly
against saved results using the frozen forest artifact
`bd79923fabc4816cc2f15b4f150a5d3b428663c455d0fde3da6ab219eb666d62`.

## Extraction, direction and timing checks

Each selected connection has a unique matched browser UDP socket, enough browser
prefix records and exact ordered payload-size agreement within each direction.
The browser records also start with1250 or1230 respectively. Parser inspection
shows `udp.length -8` for the UDP payload in either IP family, and integer
nanosecond subtraction before conversion to milliseconds. New constructed IPv4
and IPv6 fixtures verify different payload sizes at equal frame length without
subtracting the IP header twice. Such fixtures are engineering checks, not
traffic-quality evidence.

Bidirectional order does differ between capture and browser events. The browser
logs have millisecond userspace event times; they are not on-wire ground truth.
Maximum per-direction absolute timestamp differences across each visit are
2.517,1.109 and1.824ms, respectively. First-server delays range14.61–56.97ms,
8.40–97.07ms and25.28–102.36ms, respectively. This does not show an obvious
seconds-versus-milliseconds error; it cannot exclude timing effects or other
measurement differences. No order mismatch was silently removed.

Replaying the fixed forest on the browser's own recorded order/times does not
repair YouTube recognition:

| Recorded browser socket metadata | Correct at10 | Correct at20 | Correct at30 |
| --- | --- | --- | --- |
| Two earlier visits combined | 7/7 | 6/7 | 6/7 |
| Failed calibration visit | 3/6 | 2/6 | 0/6 |

This is offline replay at another observation point, not a live adapter or a
candidate selected for deployment. Reference attribution is conditioned on
successful matching, not independent full ipfixprobe/CESNET feature parity.

## A bounded sensitivity isolates the model's size dependence

Two declared substitutions were applied to every selected YouTube flow at each
of10/20/30 packets: exact1230→1250 and exact1250→1230. Other sizes, packet order,
directions and times stay byte-for-byte/numerically unchanged. These are
**abstract metadata transformations**, not corrected captures, transport
simulations, augmentation validation or measured accuracy of a repaired system.
Both directions of the sensitivity were recorded; no parameter search followed.

| Input and diagnostic substitution | Correct at10 | Correct at20 | Correct at30 |
| --- | --- | --- | --- |
| Earlier actual capture prefixes, combined | 7/7 | 7/7 | 7/7 |
| Earlier prefixes, exact1250→1230 | 1/7 | 2/7 | 6/7 |
| Failed actual capture prefixes | 3/6 | 0/6 | 4/6 |
| Failed prefixes, exact1230→1250 | 6/6 | 5/6 | 6/6 |

The improvement is evidence of sensitivity inside this fixed model; it must not
be advertised as new6/6 real-traffic accuracy. The reverse transformation damages
previously correct predictions too. In the six current ten-packet cases,24–28
of32 trees reach a different leaf after changing6–8 exact-size packets per case.
The first divergent split is repeatedly `server.payload_bytes.max <=1241`;
other divergent splits involve payload maxima/sums/standard deviations. These
are concrete path traces, not general feature importance or independent trials.

The candidate's original, hash-verified local training inventory has21 YouTube
and22 Instagram examples, **all beginning at1250 bytes**. This establishes a local
coverage gap. Public training was deliberately not opened, so this analysis does
not claim1230-byte traffic is absent from the entire training set. Training IP
families were not inferred from sizes. Both local classes share the1250 start;
it is not a unique YouTube signature. The forest uses the34-value raw summary
feature map; its predictions do not recompute or apply training normalization
under `summary-v1`. Normalization leakage is not the explanation found here.

## What this supports next

The next repair experiment should address legitimate size/path diversity in
training and evaluate both services under IPv4 and IPv6. First use development
data to assess a bounded size-robust training treatment or feature treatment;
compare it with the unchanged model, including regression checks for Instagram
and other supported classes. It must use a new declared study and fresh
evaluation after decisions are fixed. The13 analyzed flows are diagnostic
evidence, not an untouched final set for that repair.

Do not hardcode1230→1250, force IPv4 to make the demo look better, relax the failed
confidence gate or use IP family/domain/address as a service shortcut. IP family
may stratify an evaluation; it is not a service label. The abstract substitution
has not established a safe real-traffic augmentation. Time/path/session/content
changes remain confounded in these small visits. No reliable replacement has
been validated, and B17 remains in the app. No further user capture is requested
by this diagnostic task.

## Reproduce and inspect

From the repository directory, with the private evidence present:

```powershell
.venv/Scripts/python.exe scripts/diagnose_youtube_failure.py --output experiments/youtube-failure-diagnostic-reproduction
.venv/Scripts/python.exe -m pytest tests/test_youtube_diagnostic.py tests/test_capture.py tests/test_browser_receive_parity.py -q
```

The output directory must not already exist; the tool refuses to overwrite
evidence. It verifies all selected archive file hashes, binds original saved
prediction files, replays every available declared prefix, rechecks browser
socket consistency, verifies local-training row hashes against artifact
provenance and exports numeric sensitivity/tree traces. Public processed data,
final records and network connections are excluded. No fitting entry point is
called. Synthetic unit fixtures are kept separate from actual report evidence.

Private outputs are `report.json`, `predictions.json` and `checksums.json` under
`experiments/youtube-failure-diagnostic-v1/`. The report binds source/config/model
identity and all input archive/prediction/training-row hashes; checksums bind
both output files. Original report SHA-256:
`cb6fbadd432585d8dcb2c8ee2ab0cd1a342928ac3acbdd83e0ffdbbe009116cc`.
Original predictions SHA-256:
`2c47d9283540e6d3ce221ad6d2e1d9c9fbb89dbe27564ac652793f7bc857ee04`.
The additional replay at
`experiments/youtube-failure-diagnostic-v1-guarded-replay/` uses normalized-path
guards, tested against relative public-data/final paths and network connections.
All numeric report content and prediction bytes match the original exactly.
Its source commit is `244a19411b52db0741fff0972845636f5f38dd45`, source SHA-256
`0260ea52fd276d35cf3d06f8cbaae8241559244be3e6a920e8f97b2a1d914839`,
and report SHA-256
`1d4aef468733b5ab52ca7eddfd76ce083550eaae05797fcaa7331515a58555b0`.
The original outputs remain intact. `completion-evidence.json` in that second
directory, SHA-256
`d83da536b834dc88d09be2145daa7ab0eb29d0d26679b4d8f9a05aeb4ad1054f`,
binds both-run agreement, frozen input hashes, environment and test checkpoint.

Full Python suite: **375 passed**, with two known dependency deprecation warnings,
in36.86s. Ruff lint and format checks pass for118 active files. New tests cover
exact-size-only mutation, token-based family identification, protected reads,
network exclusion, IPv4/IPv6 payload parsing and forest branch tracing. UI code
is unchanged from its seventeen-test/production-build checkpoint; no new UI,
hosted CI or cross-platform result is claimed. Python3.11.9, numpy2.1.3,
torch2.5.1 and scikit-learn1.6.1 were used on the existing Windows host.
`git diff --check` passes. Read-only service checks confirm capture stopped and
the app artifact remains B17. No local policy or final preparation was created.
