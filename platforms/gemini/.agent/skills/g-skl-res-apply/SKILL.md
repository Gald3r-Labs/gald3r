---
name: g-skl-res-apply
version: 1.4
description: >
  Convert a reverse-spec FEATURES.md (produced by g-skl-res-deep) into gald3r
  artifacts: project goals, PRDs, subsystem specs (merge or create), and tasks.
  Vault-aware — reads from {vault}/research/recon/{slug}/FEATURES.md when a
  shared vault is configured, else falls back to local research/harvests/{slug}/FEATURES.md.
  This is the "Execute" layer in the Discover → Curate → Execute harvest pipeline.
triggers:
  - g-res-apply
  - g-harvest-intake
  - "harvest intake"
  - "apply harvest"
  - "apply recon"
  - "convert features"
  - "intake reverse-spec"
input: "{recon_base}/{slug}/FEATURES.md"   # vault-aware — see Path Resolution below
outputs:
  - .gald3r/PROJECT.md (goals section appended)
  - .gald3r/features/prdNNN_*.md (one per category)
  - .gald3r/FEATURES.md (updated index)
  - .gald3r/SUBSYSTEMS.md (new or merged rows)
  - .gald3r/subsystems/{name}.md (new spec files)
  - .gald3r/TASKS.md (new task rows)
  - .gald3r/tasks/taskNNN_*.md (one per feature group)
token_budget: very_high
subsystem_memberships: [PROJECT_IDENTITY_SETUP, VAULT_AND_RESEARCH]
---

Provisioned by `gald3r platform install`.
Documentation: https://docs.gald3r.ai
