---
name: g-skl-qa
description: Track bugs, QA, and fixes in .gald3r/. For bug reports, issues, quality, fixes, QA workflows.
token_budget: low
subsystem_memberships: [BUG_AND_QUALITY]
---

## HELP CONTRACT (T442 — cross-platform, non-substitutable)

If the invoking command's arguments are EXACTLY `-h`, `--help`, or `help` (one
token, nothing else): do NOT run any operation of this skill. Respond ONLY with a
compact usage card — the command's name, its one-line purpose, each documented
argument/option on its own line (or "none"), and the path to its command file —
then STOP. Read-only: no `.gald3r/` writes, no state changes, no task/bug
creation. This block lives in the SKILL (not a rule) because skills are the
execution layer on every supported platform; rules are optional context on most.

<!-- gald3r-thinned-shim -->
# g-skl-qa — thinned shim (prompt-layer)

> **Judgment served by gald3r_core's package-embedded prompt library** (`gald3r prompt get`,
> T298) — ships with every gald3r_core install, no vendored engine required. Full original text
> retained in **`SKILL.full.md`** as a manual fallback.

**What it does:** bug tracking + quality gates (zero-tolerance error logging).

## Preferred — fetch the centralized judgment
`gald3r prompt get role.qa_engineer` (MCP `gald3r_prompt_get id=role.qa_engineer` -- served over stdio by `gald3r mcp serve`; hosts add {"command": "gald3r", "args": ["mcp", "serve"]} to their MCP config)

## Manual fallback (gald3r not on PATH)
Follow **`SKILL.full.md`** in this directory, plus any `rules.md` / `reference/` / `examples/`.
