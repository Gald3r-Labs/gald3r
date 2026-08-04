---
name: g-skl-res-deep
description: Analyze any external repository and produce a structured FEATURES.md harvest report. Writes to {vault}/research/recon/{slug}/ when a shared vault is configured, else falls back to local research/harvests/{slug}/. Performs cross-project dedup via _recon_index.yaml. Agents are reporters — humans are editors. No .gald3r/ writes until human approves APPLY.
token_budget: very_high
subsystem_memberships: [VAULT_AND_RESEARCH]
---

Provisioned by `gald3r platform install`.
Documentation: https://docs.gald3r.ai
