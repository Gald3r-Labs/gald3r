---
name: g-skl-compress-memory
description: Compress the NON-gald3r sections of AGENTS.md/CLAUDE.md (and *memory*.md) to cut token overhead, while strictly preserving the install-managed gald3r SECTION ranges, code blocks, and URLs. Dry-run by default; apply only after confirmation.
token_budget: low
skill_trust_level: core
allowed-tools: [Read, Edit, Bash]
subsystem_memberships: [MEMORY_AND_KNOWLEDGE]
---

Provisioned by `gald3r platform install`.
Documentation: https://docs.gald3r.ai
