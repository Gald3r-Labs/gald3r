# Hook: g-hk-agent-worktree-janitor

Auto-prunes stale native Cursor/Claude background-agent worktrees (T1592). Evidence:
2026-06-24 had 23 stale worktrees under `.claude/worktrees/agent-<hash>` plus 12
orphaned `claude.exe` processes (8+ hours old) holding several git-locked, so a plain
`git worktree remove --force` hung until manual `unlock` + `remove -f -f` + process
kill was applied.

## Fires On

Both **`SessionStart`** and **`Stop`** (Cursor `sessionStart`/`stop`, Claude Code
`SessionStart`/`Stop`). Wired in `.cursor/hooks.json` and `.claude/settings.json`
alongside the other session-boundary hooks. Each event runs at most once per session
via an idempotency env-var guard (`GALD3R_HK_WORKTREE_JANITOR_<EVENT>_APPLIED`), so a
SessionStart run and a Stop run in the same session are independent but neither
re-fires within itself.

## What It Does

Delegates entirely to
the absorbed engine verb `gald3r worktree janitor` (A1 / T1658), invoked with `--apply --quiet` so pruning actually runs
but this hook stays silent unless something goes wrong. The underlying janitor:

1. Scans `.claude/worktrees/agent-*` and `.cursor/worktrees/agent-*` for native
   background-agent worktrees (distinct from gald3r-owned worktrees under
   `.gald3r-worktrees/`, which `gald3r worktree cleanup` already handles).
2. Classifies each as stale when its owning process (resolved from the git worktree
   lock reason's `pid`) is dead **and** the worktree has been idle past the threshold
   (`GALD3R_JANITOR_STALE_HOURS`, default 2h). A live owning process always protects
   the worktree regardless of age.
3. **Rescues dirty worktrees first**: any uncommitted changes are committed to the
   worktree's own branch before removal — never force-discarded.
4. Unlocks + force-removes the worktree directory, keeping the branch ref.
5. Deletes the branch only if fully merged into `main`; unmerged branches are kept
   for triage.
6. Optionally (only when `GALD3R_JANITOR_REAP_PROCESSES=1`) terminates orphaned
   `claude`/`cursor` processes past the same stale threshold that are not protecting
   any live worktree.

## Side Effects

- Removes stale worktree directories (`.claude/worktrees/agent-*`,
  `.cursor/worktrees/agent-*`) and deletes their branch **only if merged into main**.
- May create a rescue commit on a worktree's own branch before removing it.
- Appends a structured summary line to `.gald3r/logs/worktree_janitor.log` on every
  run (counts: scanned/pruned/rescued/skipped/branches_deleted/branches_kept/
  processes_terminated/errors) — this is the audit trail, independent of git history.
- Process termination is opt-in and guarded; default behavior never kills anything.
- Never blocks the host session — any error is caught and surfaced only via
  `additional_context`; the hook always returns `{"continue": true}`.
- Idempotent: a repeat run finds nothing left to prune once cleaned.

## Related Tasks

- T1592 — Auto-prune stale agent worktrees + orphaned claude.exe processes.
- Core logic: the `gald3r worktree janitor` verb in the agent binary (A1 / T1658)
  (core scan/rescue/prune/reap logic, unit-tested against synthetic git repos).
- Distinct from (does not replace) `gald3r worktree cleanup`, which only
  ever touches `.gald3r-worktree.json`-owned worktrees.
