# Newer-data investigation — 26 October 2026

This is the initial inspection checkpoint. The subsequent
[training pilot](quicext25-pilot.md) audited an alternative label rule and trained
real candidates; neither repaired the local errors. Statements below about
training not having started describe the earlier checkpoint.

The next model experiment needs defensible labels and browser-relevant
development data. Downloading newer traffic alone does not establish those
conditions. No new model was trained or deployed in this investigation.

The official [CESNET-QUICEXT-25 record](https://zenodo.org/records/17249078)
contains daily Parquet members inside monthly archives. Its May 2025 archive
has an accessible [member index](https://zenodo.org/api/records/17249078/files/2025-05.zip/container).
The prepared XS HDF5 and service-map endpoints on `liberouter.org` both timed
out on this host after approximately 19 seconds. This is an observed access
failure, not a claim that the public dataset is generally unavailable.

The 1 May 2025 member was obtained directly through the official HTTPS API:

- Local path: `artifacts/local/quicext25-schema/20250501.parquet`.
- Size: 37,801,895 bytes; 262,269 flow records.
- SHA-256: `22592795db66ca4b7d8fe5efbfee12612d03c74dcc52339538703822a1216631`.
- CRC-32: `4dd974f7`, matching the official member index, as did the file size.
- License: CC-BY-4.0, checked through the record API.
- The complete monthly ZIP was not downloaded, so its published MD5 was not verified.

This date was marked development/training-only before inspecting records. It
must not later be presented as untouched final-test data. The source, index,
download provenance, schema and aggregate inspection are retained locally and
ignored by Git. No browser capture started during this work.

## What the bounded inspection found

The raw file has `PPI`, `PPI_LEN`, QUIC protocol metadata and `QUIC_SNI`, but
**no `APP` label column**. The official [feature documentation](https://cesnet.github.io/cesnet-datazoo/features/)
describes milliseconds, signed directions and transport-payload bytes. All
16,384 inspected records passed the existing packet-feature contract.

The existing conservative CESNET22 hostname map was used only to inspect
possible coverage. This does not turn those matches into official QUICEXT25
training labels. Names and addresses are excluded from the aggregate output,
and nothing is passed to a predictor. ECH/ESNI indications remain excluded from
candidate references even though such indications can be GREASE.

| Outcome in the first 16,384 source rows | Count |
| --- | ---: |
| Provisional supported-service name match | 4,812 |
| Ambiguous name mapping | 3,406 |
| Outside current supported set | 3,787 |
| Unmapped name | 4,030 |
| Unavailable name | 349 |

After basic UDP/443, version, direction, length, size and multiplexing checks,
and protected-name exclusion, provisional counts were Instagram 959, YouTube
1,597, Snapchat 603, Spotify 215, WhatsApp 30, Discord 8, Outlook 3 and TikTok 2.
There were no provisional Google Drive or Facebook Messenger candidates in
this bounded sample. These are not population prevalence estimates or proof
that the full dataset lacks those services. The basic checks alone also do
not prove a client Initial; exact packet-type eligibility still needs an
audited adapter before export.

The 959 provisional Instagram candidates began with 1,200-byte (22),
1,232-byte (193) or 1,252-byte (744) payloads. None began with the 1,250-byte
payload observed in all four independently referenced local Instagram flows.
That difference is a useful diagnostic clue, not proof of client platform or
the cause of classification errors. The sampling and provisional attribution
limits prevent drawing a general conclusion from it.

A first whole-file inspection reached its 180-second execution budget without
producing a completed report. The saved result is explicitly the bounded
16,384-row inspection, not an all-file audit. A timezone conversion attempt
also exposed missing Windows timezone data; the final inspector avoids
unneeded timestamp conversion and leaves chronological partitioning unimplemented.

## Reproduction and remaining work

The inspector is read-only and refuses an unexpected source checksum or an
existing output. Install its optional dependency and run from the project:

```powershell
.venv/Scripts/python.exe -m pip install -e '.[parquet]'
.venv/Scripts/python.exe scripts/inspect_quicext25.py --source artifacts/local/quicext25-schema/20250501.parquet --expected-sha256 22592795db66ca4b7d8fe5efbfee12612d03c74dcc52339538703822a1216631 --output artifacts/local/quicext25-schema/inspection-repeat.json --max-rows 16384
.venv/Scripts/python.exe -m pytest -q tests/test_quicext_inspection.py
```

The source member is available at the official
[daily download link](https://zenodo.org/api/records/17249078/files/2025-05.zip/container/20250501.parquet).
The actual inspection used PyArrow 21.0.0. Seven new tests passed, covering the
row budget, exclusion of identifying fields, protected-name refusal and invalid
or ineligible records. Ruff lint/format and `pip check` passed. The previous
137-test application run and UI build remain separate evidence; they were not
rerun for this standalone inspector.

The aggregate report is `artifacts/local/quicext25-schema/inspection-16k.json`,
SHA-256 `c2c04870fc68965aefd5b9edb28ac4dd14e057bf2232a94a12fa24e948255e0f`.

Before retraining, recover the official prepared labels/service map or audit
a documented alternative label source, confirm client-Initial eligibility,
and obtain sufficient examples of the intended browser traffic. Freeze
chronological development/calibration/final partitions and sampling before
fitting. Existing local Instagram and YouTube trials are development evidence,
so a candidate will require separate fresh user-started sessions for final
local assessment. More unlabelled visits or an automatic threshold reduction
would not satisfy that requirement.

The smallest data requirement is independently attributed browser development
recordings with enough repeated flows for the services being supported, plus
separate sessions reserved for evaluation. The current four mapped flows per
service are a diagnostic sample, not an adequate replacement training corpus.
No long-running download or training job remains active after this inspection.
