---
name: g-skl-res-deep
description: Analyze any external repository and produce a whole-system, consumer-neutral functional specification (FEATURES.md + supporting notes). Centralizes output in the shared vault at {vault}/research/CRR_FunctionalSpecs/{slug}/ so a run from any project/workspace lands in one place reusable across projects; falls back to local research/CRR_FunctionalSpecs/{slug}/ only when no shared vault is configured. Documents the ENTIRE source system regardless of relevance to any one consumer project. Performs cross-project dedup via _recon_index.yaml. Agents are reporters — humans are editors. No .gald3r/ writes until human approves APPLY.
token_budget: very_high
subsystem_memberships: [VAULT_AND_RESEARCH]
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
