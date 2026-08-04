---
name: g-skl-wishlist-mine
description: Mine a free-form, human-prose intent/wishlist document into formal gald3r task specs — READ-ONLY against the prose doc, dedup against existing tasks, curation discipline (epics for vision, backlog-candidates for unsure). Productizes the DELIVERABLES.md mining pattern.
token_budget: medium
subsystem_memberships: [TASK_MANAGEMENT, MEMORY_AND_KNOWLEDGE]
skill_trust_level: core
---

## HELP CONTRACT (T442 — cross-platform, non-substitutable)

If the invoking command's arguments are EXACTLY `-h`, `--help`, or `help` (one
token, nothing else): do NOT run any operation of this skill. Respond ONLY with a
compact usage card — the command's name, its one-line purpose, each documented
argument/option on its own line (or "none"), and the path to its command file —
then STOP. Read-only: no `.gald3r/` writes, no state changes, no task/bug
creation. This block lives in the SKILL (not a rule) because skills are the
execution layer on every supported platform; rules are optional context on most.

Run: `gald3r wishlist mine`
Documentation: https://docs.gald3r.ai
