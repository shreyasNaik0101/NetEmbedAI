# Data card

## Source and rights

Target: CESNET-QUIC22, October 31–November 27, 2022, captured on the CESNET backbone. Source record: https://zenodo.org/records/10728760 (DOI 10.5281/zenodo.10728760). Its API reported CC BY 4.0, open access on 2026-10-23. Attribution and source/version links must accompany derived published data. No real benchmark samples or trained weights are redistributed in this change. No separate repository software license is invented.

Feature references: https://cesnet.github.io/cesnet-datazoo/features/ and the dataset record. Sizes are UDP payload bytes, intervals are milliseconds, +1 means client→server. The live extractor must independently establish compatibility with the particular exporter and capture point; matching names/units alone is insufficient.

## Local inventory

The local data/cesnet/XS/CESNET-QUIC22-XS.h5 is truncated: 330,301,440 bytes versus HDF5's stored EOF of 2,714,067,131 bytes. data/recovered/ holds a separate preserved copy. The official DataZoo HDF5 endpoint returned HTTP 503 on 2026-10-23; CESNET confirmed its storage outage (https://github.com/CESNET/cesnet-datazoo/issues/13). The original Zenodo CSV ZIP is now downloaded at C:/Users/shrey/Downloads/cesnet-quic22.zip. Its 20,952,008,298-byte size and MD5 `2d52ad44ddb22645a3464634fc54bb9c` match the published record; SHA-256 is `17ecb8991cb44abd1b33b8fb448e5119407388b91aa50a1a5e83b486116f6176`. No historical PyTorch or processed artifact was substituted. Legacy TensorFlow weights were not substituted.

## Planned partitions implemented in preparation

Training: 2022-10-31 through 2022-11-06 (week 44). Development: November 7–13 (week 45). Final test: November 14–20 (week 46). CSV partitions use the official `flows-YYYYMMDD.csv.gz` file day, matching HDF5 day tables. `TIME_FIRST` sometimes falls on the preceding UTC calendar day; it is retained for audit and excluded from features. The real bounded export contains 200 flows per selected class/day: 14,000 training, 14,000 development and 14,000 sealed final-test rows. Group-hash seed 17 assigns development flow IDs to 10,467 selection and 3,533 calibration rows; grouping by ID cannot establish host/session independence. Each class has at least 333 calibration rows. These counts are the balanced export policy, not source prevalence.

Fixed initial labels: youtube, spotify, instagram, tiktok, snapchat, whatsapp, facebook-messenger, discord, google-drive, microsoft-outlook. Preparation never silently drops a class. Native HDF5 export samples the first bounded records per class/day (default 200). This yields a bounded engineering pilot, not an unbiased prevalence estimate. Larger, representative experiments must record their sampling policy.

Manifests include counts, dates, source checksum, per-split hashes, duplicate audit and limits. The real export has 42,000 unique flow IDs and 39,120 unique packet-feature fingerprints. There are 63 feature fingerprints shared across chronological periods, covering 2,923 rows; 2,844 of those are Outlook and all shared fingerprints have 2–8 packets. Two shared fingerprints have conflicting service labels. Repeated short feature patterns are retained because equality alone does not prove the same capture was repeated; an exact feature-match cohort can be reported separately. Duplicate IDs and explicit groups spanning chronological periods still fail. Host/session overlap and correlated flows remain unaudited because the source flow IDs do not encode them. An authorized JSONL export may supply group_id for stronger checks.

## Boundaries

Predictors receive only the three packet channels. Labels and audit identifiers never enter their feature arrays. Final-test reading requires explicit evaluation opt-in and a matching frozen decision file. Data preparation must inspect test integrity/counts; training and model selection must not inspect its outcomes.

Local browser/app versions, VPNs, devices and networks differ from the 2022 backbone data. No accuracy transfer to this computer is established. Local trial context is not a ground-truth label for every concurrent flow.
