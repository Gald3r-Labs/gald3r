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

Delegates the actual scan/classify/rescue/prune work to
the absorbed engine verb `gald3r worktree janitor` (A1 / T1658). This hook stays
silent unless something goes wrong. The underlying janitor:

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

## BUG-106 Fail-Safe Gate (wrapper-owned `--apply` gating)

`--apply` (the flag that lets the engine's rescue-commit + prune actually mutate
anything) is **not** passed unconditionally anymore. Because the janitor's own
scan/classify/rescue/prune logic lives inside the compiled `gald3r` engine binary
— not source this repo can patch — the wrapper instead hard-gates the
*invocation* itself, before the engine ever runs:

1. Before every run, the wrapper classifies the target checkout: compares
   `git rev-parse --git-dir` against `--git-common-dir` (equal ⇒ this is the
   **primary** checkout, not a linked worktree), checks `git status --porcelain`
   for dirtiness, and checks for agent-worktree ownership evidence (a
   `.gald3r-worktree.json` marker file, or a path under `.claude/worktrees/`,
   `.cursor/worktrees/`, or `.gald3r-worktrees/`).
2. `--apply` is withheld (engine still runs, but dry-run only) whenever: git state
   is ambiguous (a git command failed — `ambiguous-git-state`); OR the checkout
   is the **dirty primary checkout** with no agent-worktree marker
   (`primary-checkout-dirty` — this is the exact condition recorded for all four
   observed BUG-106 misfires); OR the checkout shape is unrecognized — neither a
   confirmed primary checkout nor a recognized agent-worktree marker
   (`unrecognized-checkout-shape`). The reason is surfaced in the hook's
   `additional_context` output.
3. **Defense in depth**: even when `--apply` was allowed, the wrapper re-reads
   `HEAD` immediately after the engine call. If a rescue-style commit
   (`chore(worktree-janitor): rescue uncommitted work...`) landed directly on
   what was the primary checkout's pre-invocation `HEAD` anyway (an engine
   misfire despite the pre-check), the wrapper immediately reverts it with
   `git reset --soft` to the prior `HEAD` — the working tree is preserved
   exactly as in the manual coordinator recovery already on record for BUG-106;
   nothing is force-discarded.

This closes BUG-106 (T1592: the janitor auto-committed rescue commits directly
onto `main` in the primary checkout, four confirmed misfires on 2026-07-09 — see
`.gald3r/bugs/done/bug106_*.md`). The durable fix belongs inside the engine's own
`worktree janitor` verb so it self-guards regardless of which wrapper calls it
(the compiled binary's classify logic is not source this repo can patch); T93
tracks preparing that upstream requirement for the engine repo
(`Gald3r-Labs/gald3r_agent`) and recording the client-side gate retirement
decision once a fixed engine ships.

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
- BUG-106 (`.gald3r/bugs/done/bug106_*.md`) — janitor auto-committed rescue
  commits onto `main` in the primary checkout; local mitigation is the
  wrapper-owned fail-safe gate documented above.
- T93 — durable upstream fix: this gate lives in the invocation wrapper because
  the engine's classify logic isn't patchable from here; T93 tracks preparing
  the upstream requirement for the engine repo and the eventual client-side
  gate retirement decision once an engine release self-guards.
