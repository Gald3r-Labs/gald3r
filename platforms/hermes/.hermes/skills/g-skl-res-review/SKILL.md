---
name: g-skl-res-review
description: Analyze external sources (GitHub repos, URLs) for adoptable patterns and improvements. Vault-aware — reads from {vault}/research/recon/ when a shared vault is configured, else falls back to local research/harvests/. Uses _recon_index.yaml for cross-project dedup. Produces structured harvest reports and optional IDEA_BOARD suggestions. Zero-change-without-approval.
token_budget: very_high
subsystem_memberships: [VAULT_AND_RESEARCH]
---

Provisioned by `gald3r platform install`.
Documentation: https://docs.gald3r.ai
