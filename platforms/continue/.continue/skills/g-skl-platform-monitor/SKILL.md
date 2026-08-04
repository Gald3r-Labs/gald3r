---
name: g-skl-platform-monitor
description: Cross-platform health and freshness monitor for the registry-driven gald3r platform roster (PLATFORM_REGISTRY.yaml — single source of truth, T516). Checks per-platform capability gaps against the Cursor reference, scans official docs for breaking changes, validates platform-specific config, and generates the PLATFORM_STATUS / PLATFORM_CAPABILITY_MATRIX living indexes. Owned by g-agnt-platformer.
token_budget: low
subsystem_memberships: [PLATFORM_INTEGRATION]
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
