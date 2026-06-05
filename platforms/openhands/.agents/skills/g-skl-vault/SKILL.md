---
name: g-skl-vault
description: Own and manage the file-first vault plus repo mirror metadata. Obsidian-compatible notes, wiki compilation, path resolution, reindexing, linting, and GitHub repo summaries.
token_budget: low
subsystem_memberships: [MEMORY_AND_KNOWLEDGE, VAULT_AND_RESEARCH]
---

<!-- gald3r-thinned-shim -->
# g-skl-vault — thinned shim (engine-backed)

> **Handled by the bundled gald3r engine** (`.gald3r_sys/engine`, pure Mode-A, no LLM). Full original
> procedure retained in **`SKILL.full.md`** so an install without the engine still works.

**What it does:** file-first knowledge vault (vault/).

## Preferred — invoke the engine
- **CLI:** `uv run --project .gald3r_sys/engine gald3r vault …`  (or the installed `gald3r`)
- **MCP tools:** `gald3r_vault_*`   ·   facade `Gald3r(...).vault`

The engine owns ID allocation, file placement, status→folder moves, index regeneration, and
validation. `.gald3r/` markdown stays the data source of truth.

## Manual fallback (engine not provisioned)
Follow **`SKILL.full.md`** (full procedure) + the schema in `.gald3r_sys/schemas/` (`generic`).
Everything needed ships in the install — nothing external.
