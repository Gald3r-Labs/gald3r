---
name: g-skl-tasks
maturity: production
description: Own and manage all task data — TASKS.md index, tasks/ individual files, status transitions, sync validation, complexity scoring, and sprint planning. Single source of truth for everything task-related.
token_budget: low
subsystem_memberships: [TASK_MANAGEMENT]
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
# g-skl-tasks — thinned shim (engine-backed)

> **Handled by the bundled gald3r engine** (`.gald3r_sys/engine`, pure Mode-A, no LLM). Full original
> procedure retained in **`SKILL.full.md`** so an install without the engine still works.

**What it does:** task lifecycle over TASKS.md + tasks/<status>/.

## Preferred — invoke the engine
- **CLI:** `uv run gald3r task …` in a gald3r_core dev checkout (bare `gald3r` may resolve to a
  stale PATH install and silently write into the wrong repo's `.gald3r/` across a worktree
  boundary — BUG-591; see `g-rl-09-python_venv.md`). Outside a dev checkout, the installed
  `gald3r` is fine.
- **MCP tools:** `gald3r_task_*`   ·   facade `Gald3r(...).tasks`

The engine owns ID allocation, file placement, status→folder moves, index regeneration, and
validation. `.gald3r/` markdown stays the data source of truth.

## `gald3r task add` flag reference (BUG-270/BUG-271)

| Flag | Repeatable? | Purpose |
|---|---|---|
| `-d`, `--description TEXT` | no | Task description / body text. |
| `--description-file PATH` | no | Read the description from `PATH` instead of argv text (avoids shell-quoting multi-paragraph prose). Mutually exclusive with a non-empty `-d`/`--description`. |
| `--acceptance-criteria TEXT`, `--ac TEXT` | yes | One acceptance criterion per flag use; rendered as an unchecked checklist item. Omit to leave the section for reviewers to derive criteria from the description (BUG-255). |
| `--acceptance-criteria-file PATH`, `--ac-file PATH` | no | Read additional criteria, one per non-blank line, from `PATH`; merges with any `--acceptance-criteria`/`--ac` values passed on the same invocation. |

**Stdin (`-`) convention**: `-d`/`--description`, `--description-file`, and
`--acceptance-criteria-file`/`--ac-file` all accept the literal value `-` to read that field's body
from stdin instead of argv/a file — either spelling works (`-d -` or `--description-file -`), so
you only need to remember one. Reads are byte-faithful: CRLF / lone-CR line endings are preserved
verbatim, not normalized to `\n`.

**Known caveat — only one `-` per invocation**: stdin is a single-consume stream. If both
description and `--ac-file` resolve to `-` in the same command (e.g. `-d -` together with
`--ac-file -`), only the FIRST one actually read wins — `gald3r task add` resolves description
before acceptance-criteria, so the description read gets the whole piped body and the `--ac-file -`
read that follows silently gets an empty result (no error). Pipe at most one field's body into a
single `gald3r task add` call; use `--description-file PATH` / `--acceptance-criteria-file PATH`
(real files) instead of stacking multiple `-` reads.

## Active agent run → inbox routing (T585)
During a multi-agent / autopilot run (marker `.gald3r/logs/ggo_run_state.json` `active: true`,
or env `GALD3R_AGENT_RUN=1`), the engine `create()` **auto-routes** a new task to `tasks/inbox/`
as an **id-less draft** (uuid-suffixed filename) instead of assigning an id directly. The
hot-inbox **intake** (run at each iteration boundary) is the *single ID-assigning authority* and
assigns ids atomically — so concurrent agents can never collide on the next id. Idle (no run) →
direct create, unchanged. **Hand-writing agents (manual fallback) MUST drop new-task drafts in
`tasks/inbox/` during a run — never write `tasks/open/` + regenerate the index directly.**

## Manual fallback (engine not provisioned)
Follow **`SKILL.full.md`** (full procedure); the engine validates via its embedded schemas (`gald3r validate`; `task-file`).
Everything needed ships in the install — nothing external.
