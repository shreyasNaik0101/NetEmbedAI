# Default and demo model decision — 6 November 2026

Retain B17 as the historical benchmark selection. Use the improved forest only through the explicit local demo profile. This is a scoped decision, not an automatic promotion from a small evaluation.

B17 was selected by the original frozen development rule. Matched augmented CE and SupCon mean development F1 were 0.82777 and 0.82689; the evidence does not support an additional contrastive-learning benefit. Its held-out CESNET results are documented in the model card.

The new forest adds 19 verified local IPv6 training flows. Development and four fresh evaluation visits favor it over the old forest. This is not a fresh head-to-head comparison with B17. Public selection F1 changed from 0.896904 to 0.894825 in the pilot. The fixed public-only acceptance policy has threshold 0.76 and minimum 10 packets.

Two subsequent live visits passed the predefined descriptive screen: eight accepted labels, zero errors, eleven eligible ten-packet cases. Instagram acceptance deteriorated at later prefixes. Only two services and one user-declared hotspot were tested. These limitations prevent a broad reliability claim or universal-default switch. No further recording or model tuning is required to present this honest scoped demonstration.

## Complete local artifacts

- Forest demo ZIP: artifacts/local/NetEmbedAI-ipv6-public-policy-v1.zip
- ZIP SHA-256: 82b6fc9f388602d96e0d11162c67476f5b83d1ded63fe06323ad45c3fcc2cd1f
- Forest artifact identity: 9878d0818370ede3e9897a9cc654b4ddc0afcd87d41b2d7134ccaf52592b528a
- B17 ZIP: artifacts/local/NetEmbedAI-v2-default-B17.zip
- ZIP SHA-256: f9ca92fd82ea3cbc4254238b68993027e3a12715aa02f6ff9d1107bd21abd746

Verify with Get-FileHash -Algorithm SHA256 before copying/extracting. Bundles include model parameters, preprocessing, labels, architecture/schema, policy and provenance. They contain no training dataset. Neither archive is publicly hosted by this project.

## Subsequent Spotify diagnosis

The [single Spotify diagnostic](spotify-diagnostic-v1.md) found all five verified ten-packet raw choices were YouTube; one was wrongly accepted and four refused. The capture also reported seven drops. This strengthens the decision against a broad default promotion and limits the demo claim to its tested setting. No retraining or policy change follows automatically.
