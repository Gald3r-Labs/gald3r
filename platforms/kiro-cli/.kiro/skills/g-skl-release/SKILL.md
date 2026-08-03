---
name: g-skl-release
description: Own and manage all release data — RELEASES.md index and releases/ individual files. Operations: CREATE new release, ASSIGN tasks to a release, STATUS summary, PUBLISH ROADMAP.md, ACCELERATE target dates with cascading shift to subsequent planned releases, SYNC reconcile CHANGELOG entries against release records (C-023).
token_budget: low
subsystem_memberships: [RELEASE_AND_VERSIONING]
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
# g-skl-release — thinned shim (engine-backed)

> **Handled by the bundled gald3r engine** (`.gald3r_sys/engine`, pure Mode-A, no LLM). Full original
> procedure retained in **`SKILL.full.md`** so an install without the engine still works.

**What it does:** release records (RELEASES.md + releases/).

## Preferred — invoke the engine
- **CLI:** `uv run gald3r release …` in a gald3r_core dev checkout (bare `gald3r` may resolve to a
  stale PATH install and silently produce wrong results — BUG-591; see
  `g-rl-09-python_venv.md`). Outside a dev checkout, the installed `gald3r` is fine.
- **MCP tools:** `gald3r_release_*`   ·   facade `Gald3r(...).release`

The engine owns ID allocation, file placement, status→folder moves, index regeneration, and
validation. `.gald3r/` markdown stays the data source of truth.

## Manual fallback (engine not provisioned)
Follow **`SKILL.full.md`** (full procedure); the engine validates via its embedded schemas (`gald3r validate`; `generic`).
Everything needed ships in the install — nothing external.

## Public-publish history mode (T423)
Publishing/graduating to a **public** repo chooses how git history is handled:
`carry` (default — keep history, safe) vs `scrub` (Mode A — zero-history publish for IP
protection, DESTRUCTIVE). `scrub` is OFF by default, opted in at `@g-setup`
(`publish_history_mode` in `.gald3r/.identity`), and at publish time **requires an explicit
`-ConfirmScrub`**. Full contract + the current-architecture caveat are in **`SKILL.full.md`**
-> "Public-Publish History Mode (T423)".
