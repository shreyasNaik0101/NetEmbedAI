# Bounded real-family coverage plan — 2 November 2026

**Actual outcome,4 November: stopped after the first visit.** The capture and
reference checks pass on five YouTube connections, all IPv4 and all30 packets.
There are zero matched YouTube IPv6 connections, so the declared IPv6 training
support gate fails. This is a coverage shortfall, not a recording mistake. No
replacement visit, Instagram intent, other slot, fit or promotion follows.
The instructions below preserve the closed declaration and collection history;
they are not a request to start recording again.

The subsequent [network diagnosis](network-ipv6-check.md) confirms no global
Wi-Fi IPv6 address/default route and an IPv6 NetworkUnreachable connection error,
while IPv4 works and YouTube has AAAA records. IPv6 acquisition is currently
blocked on this connection; router/ISP cause remains to be established.

The [completed existing-data audit](family-coverage-audit.md) verifies43 IPv4-only
training connections. Selection has7 IG/IPv6,5 YT/IPv6 and5 YT/IPv4, with no
IG/IPv4. The plan addresses these specific coverage gaps, not a universal
assumption that IPv6 breaks classification.

This is a new development collection scope following the closed size-robustness
pilot. Earlier calibration, paired comparison and diagnostic visits retain their
roles and cannot enter this training or selection set. No capture starts from
this plan. The family-aware preparation/archive checks are implemented and
tested as of4 November. Use the commands below; older calibration commands do
not apply. The new-data trainer/scorer is still a subsequent implementation
stage; selection collection is blocked until a verified training/model binding exists.

The fixed comparison forest is
`bd79923fabc4816cc2f15b4f150a5d3b428663c455d0fde3da6ab219eb666d62`,
weights SHA-256 `fc735ea2f5e821bfba3832a588bdb3e62fde7a0c8f47c55567cb4cd5a2ee0494`.
Capture continues with B17 artifact
`18c43fe12262b81d4a3001df150a278865f3908ddd3aab934822fc0c9e5750fb`
and adapter `tshark-prefix-ns-v3`. Neither candidate scores nor the activity name
supplies a reference label. Actual browser-to-flow reference matching does.

## Acquisition and stopping rules

At most eight deliberate visits: four training, then four development selection.
One stopped attempt per slot; all attempts and exclusion inventories remain
saved. A processing failure stays pending for the same session. A genuine
coverage/QC failure stops this scope; no automatic replacement visits or relaxed
support rules. No model predictions participate in flow eligibility.

Use normal Chrome, the local Edge app, Wi-Fi, reference checking ON, longer
windows OFF, and stripped NetLog with sensitive/raw bytes OFF. Start browser
logging before app capture and fresh target navigation; stop both after the
60-second activity. The app's 120-second cap remains a backup. Leave the OS's
normal IPv4/IPv6 configuration intact. Family is verified from the matched
browser socket, never guessed from size or supplied as a model feature.

| Order | File stem | Role | Activity |
| --- | --- | --- | --- |
| 1 | `family-train-yt-01` | Training | Different YouTube video,60s |
| 2 | `family-train-ig-01` | Training | Feed30s, Reels30s |
| 3 | `family-train-yt-02` | Training, later local date | Another video,60s |
| 4 | `family-train-ig-02` | Training, same date as3 | Different feed/Reels,30s each |
| 5 | `family-select-yt-01` | Development, later date after training freeze | Another video,60s |
| 6 | `family-select-ig-01` | Development, same date as5 | Feed/Reels,30s each |
| 7 | `family-select-yt-02` | Development, later date than5 | Another video,60s |
| 8 | `family-select-ig-02` | Development, same date as7 | Feed/Reels,30s each |

Training visits target missing IPv6 coverage: each must contain at least three
target-service IPv6 flows reaching10 packets and one reaching30. Retain all
eligible mapped supported flows, including IPv4, in the archive. Only YouTube
and Instagram enter local adaptation. Across training, each service therefore
has at least six new IPv6 ten-packet flows over two dates. If ordinary browser
use does not produce this coverage, report that feasibility blocker and stop;
do not force a family or repeatedly reconnect until the desired sample appears.

Each selection visit needs at least three target flows at10 and one at30,
regardless of family. The complete four-visit set must cover each of the four
service/family cells (YT/IG × IPv4/IPv6) with at least three unique flows at10
and one at30. Keep all valid cases, not a matching subset. Missing cells stop
candidate scoring. Natural dual-family coverage is not guaranteed; this is an
explicit feasibility gate rather than a promised recording schedule.

## Training and evaluation decision

Preserve the original43 local training flows and14,000 public training flows;
add the eligible new local training flows. Keep25% total local weight, balanced
between the two local labels, and75% public weight. Retain four prefix views
per flow with equal within-flow mass. Use the existing raw-summary forest:
32 trees, depth12, minimum leaf2. No size jitter or relative-size treatment in
this scope. Existing clean examples stay present. This tests real data coverage
while keeping model settings fixed.

Freeze training exports and their hashes before preparing any selection slot.
Fit seed17 once; keep the current frozen forest as the paired reference. After
all four selection archives meet coverage gates, score every eligible case.
Primary endpoint:10-packet recall per service/family cell. Require each cell
>=0.75 and no cell regression versus the reference. Also require mean available-
prefix two-service macro-F1>=0.75 and at least0.01 above the paired reference,
with no mean-prefix recall loss for either service. These are descriptive
development gates on a small cohort, not population guarantees.

The public control remains the original first50 selection flows per class in
stored order. Mean-budget clean macro-F1 may lose at most0.02, and each class's
mean-budget recall at most0.05 versus the reference. Public calibration/test
remain excluded. Report available5/10/20/30 prefixes, actual counts, all class
confusions, family strata, inventory exclusions and saved predictions.

If seed17 fails, stop. If it passes, run unchanged seeds42/123 on the same frozen
training and selection sets; both must meet the same gates. No seed substitution,
alternative architecture or hyperparameter search follows. A successful outcome
is only a candidate for a separately declared confidence-calibration/final/live
validation stage. B17 is not automatically replaced. No final-test visit is
scheduled by this plan.

## Required implementation before collection

The collector must bind role, session, interface, adapter, baseline identity,
date and plan hash before Start; export immutable native capture and closed-log
hashes; verify unique reference/socket matching and existing packet QC; derive
family without exporting endpoint addresses; enforce per-slot and cumulative
coverage without reading model scores; and refuse replacement sessions or
role changes. Its status must explain a coverage shortfall without requesting
unbounded retries. Tiny fixtures must exercise mixed families, missing cells,
session/date reuse, processing continuation and training/selection separation.

## Implemented collection commands

```powershell
.venv/Scripts/python.exe scripts/paired_capture.py --plan configs/family-development-v1.json --root artifacts/local/family-development-v1 status
.venv/Scripts/python.exe scripts/paired_capture.py --plan configs/family-development-v1.json --root artifacts/local/family-development-v1 prepare family-train-yt-01
.venv/Scripts/python.exe scripts/paired_capture.py --plan configs/family-development-v1.json --root artifacts/local/family-development-v1 archive family-train-yt-01
```

Preparation reads the local service, verifies B17 and the declared Wi-Fi
interface and writes a bound intent; it never calls Start. Archive preserves
one stopped session, verifies native/reference/socket/source-replay QC, then
adds separate family metadata and applies fixed coverage gates. All eligible
packet rows remain intact; family does not become a classifier input. Processing
errors retain the same attempt for diagnosis. An unusable receipt stops later
slots. The fourth usable training receipt freezes all four archives and recipe.
Selection requires that freeze and a matching seed17 forest artifact, including
its provenance binding. Generic paired scoring rejects this workflow.

The immutable machine declaration is `configs/family-development-v1.json`,
LF-canonical SHA-256
`24a45e295b63e4ffce390e5a5d9b7f51a7dc968b31c6df3fa1f63e5459e7af17`.
Implementation commit: `60b0424`.403 Python tests pass, with two existing
dependency deprecation warnings, in65.17s; Ruff lint/format pass for124 files.
Fixtures cover endpoint-token family matching, missing cells, duplicate support,
date/session reuse, freeze integrity and pre-fit selection blocking. Existing
processing-continuation and capture tests also pass. These are software checks;
no new real capture or family-quality result is claimed. UI unchanged from its
earlier seventeen-test/build checkpoint. Hosted CI/other platforms are unverified.

For the first prepared visit, save the stripped Chrome NetLog as
`family-train-yt-01-netlog.json`, start app capture on Wi-Fi with reference ON,
then navigate to a fresh YouTube video for60 seconds. Stop the app and Chrome
logging. A closed log saved in the usual older folder can be copied byte-identically
with a hash/path sidecar; that folder issue does not require another capture.
Later slots must be prepared individually after each archive passes. Do not
record all eight visits in advance. Reliable dual-family recognition remains
unvalidated, and the prior failed calibration remains closed.

## First visit: valid recorded metadata, ineligible family coverage

Session `a9cc7e568e03482981f398764fecdfcd` was deliberately started/stopped by
the user on Wi-Fi/interface9 with reference checking ON. Queue drops and
reordered packets are zero; no capture error was recorded. The browser reference
maps five retained YouTube flows, each with30 packets and one unique socket.
Both directions have zero missing browser-prefix packets and zero ordered
payload-size mismatches. All five matched sockets are IPv4. Native source replay
compares141 saved predictions with zero changed decision labels and maximum
alternative-score difference0.0. This is source-pipeline consistency, not a new
classifier-accuracy evaluation or full exporter parity.

The outside inventory remains18 outside-supported,11 ambiguous,4 unverifiable
sessions,5 unmapped and4 unmatched connections. Those are not silently assigned
YouTube labels. The complete closed Chrome log in the usual prior folder was
copied byte-identically to the study root:43,767,294 bytes, SHA-256
`7de2fe31823c4a67838a3bf2cba808ee99ab2ef5d1b9b260cfe3bc64a0e1f0a9`.
Its stable-file/path/hash sidecar remains archived. No recapture for the folder.

The immutable receipt is `unusable_stop` **for this declared training slot**:
five IPv4 examples do not supply the required three IPv6 ten-packet examples.
The receipt was not relabelled or weakened. All captured rows and family metadata
remain saved at `artifacts/local/family-development-v1/`. Archive SHA-256:
`7e39cfd39362f630da2d3d2b8ea97b713cc0a464f39d674d427e871c03b8ccad`.
`coverage-outcome.json` explains the distinction between capture quality and
study eligibility and binds the receipt/source log. All seven later slots remain
unprepared; no training freeze, new model or evaluation was produced. Earlier
403-test/124-file lint/format checkpoint is unchanged; this result changes
documentation and private evidence only.

The visit establishes only that these matched YouTube connections used IPv4.
It does not establish that Wi-Fi lacks IPv6 globally or explain why this visit
chose IPv4. A next investigation can check ordinary IPv6 availability without
changing OS/browser routing or gathering another classifier recording. A new
collection scope would need an explicit feasibility basis; this stopped attempt
cannot become an automatic recording loop.
