---
name: g-skl-api-doc-gen
description: Auto-generate OpenAPI 3.1 specs from FastAPI/Express/Flask routes; fill docstring gaps for undocumented functions; update README API tables. Covers Python FastAPI, Express.js, and Flask. Also generates MCP tool descriptions for FastMCP plugins.
token_budget: medium
subsystem_memberships: [BUG_AND_QUALITY, PLATFORM_INTEGRATION]
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
