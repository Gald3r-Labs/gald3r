---
name: g-skl-res-apply
version: 1.4
description: >
  Convert a reverse-spec FEATURES.md (produced by g-skl-res-deep) into gald3r
  artifacts: project goals, PRDs, subsystem specs (merge or create), and tasks.
  Vault-aware — reads from {vault}/research/CRR_FunctionalSpecs/{slug}/FEATURES.md when a
  shared vault is configured, else falls back to local research/CRR_FunctionalSpecs/{slug}/FEATURES.md.
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

## HELP CONTRACT (T442 — cross-platform, non-substitutable)

If the invoking command's arguments are EXACTLY `-h`, `--help`, or `help` (one
token, nothing else): do NOT run any operation of this skill. Respond ONLY with a
compact usage card — the command's name, its one-line purpose, each documented
argument/option on its own line (or "none"), and the path to its command file —
then STOP. Read-only: no `.gald3r/` writes, no state changes, no task/bug
creation. This block lives in the SKILL (not a rule) because skills are the
execution layer on every supported platform; rules are optional context on most.

Provisioned by `gald3r platform install`.
Documentation: https://docs.gald3r.ai
