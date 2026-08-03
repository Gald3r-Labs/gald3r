---
name: g-skl-vault
description: Own and manage the file-first vault plus repo mirror metadata. Obsidian-compatible notes, wiki compilation, path resolution, reindexing, linting, and GitHub repo summaries.
token_budget: low
subsystem_memberships: [MEMORY_AND_KNOWLEDGE, VAULT_AND_RESEARCH]
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
# g-skl-vault — thinned shim (native verb group)

> **Handled by gald3r_core's native `gald3r vault` verb group** (T300) -- ships with every
> gald3r_core install, no vendored engine required. Full original procedure retained in
> **`SKILL.full.md`** so an install without the CLI on PATH still works.

**What it does:** file-first knowledge vault (vault/).

## Preferred — invoke the native verb group
- **CLI:** `uv run gald3r vault {ingest,list,reindex,lint,location,search} …` in a gald3r_core dev
  checkout (bare `gald3r` may resolve to a stale PATH install and silently produce wrong results
  — BUG-591; see `g-rl-09-python_venv.md`). Outside a dev checkout, the installed `gald3r` is fine.
- **MCP tools:** `gald3r_vault_*` not yet wired -- gald3r_core's MCP surface (`gald3r mcp
  serve`, T298 Gap 1) currently serves only `gald3r_prompt_get`/`gald3r_prompt_list`;
  `gald3r_vault_*` is a documented fast follow onto that same server.

`gald3r vault reindex` regenerates `_index.yaml` + `index.md` (a documented, intentionally
simpler form than the Stop hook's own automatic per-directory OKF regen -- see
`gald3r_core.project.gald3r_integration.vault.VaultSystem.reindex`'s docstring). `gald3r vault
location [--path DIR]` reports (or persists) the resolved vault path; the donor's `--select
{default,workspace,project}` layered-choice selector is not ported (honest partial -- no
portable-install-home or workspace-topology vault layer in gald3r_core yet). `.gald3r/vault/`
markdown stays the data source of truth.

## Manual fallback (native verbs not on PATH)
Follow **`SKILL.full.md`** (full procedure); the CLI validates via its embedded schemas (`gald3r validate`; `generic`).
Everything needed ships in the install — nothing external.

---

**Legacy `topics:` frontmatter**: `gald3r vault ingest`/`lint` migrate `topics:` → `tags:`
silently (D021). The standalone `scripts/migrate_topics_to_tags.py` helper was retired
(T1652 D7).
