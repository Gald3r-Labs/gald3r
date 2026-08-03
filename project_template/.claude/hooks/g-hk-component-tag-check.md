---
subsystem_memberships: [PROJECT_IDENTITY_SETUP]
---
# Hook: g-hk-component-tag-check

## Thinned to a resolver+verb dispatcher (T318)

Following T179's pattern, the inline git+regex staged-file scan now lives in the binary as
`gald3r lint tag-check` (`gald3r_core.project.lint.tag_check.lint_tag_check`, wired in
`cli/commands/lint_cmd.py`). This hook resolves the engine via `_hook_common.resolve_engine_argv`
and forwards its stdio/exit-code untouched -- same violation wording, same exit-code contract,
same not-a-git-repo no-op as before. Fail-open when no engine is resolvable (disclosed trade-off,
matching every other absorbed-verb hook in this tree).

## Keep-Justification (T1624, decision D-7)

Reviewed for retire-vs-keep under D-7 ("delete setup-user/component-tag-check if
superseded"): **KEPT — not superseded.** This is the only enforcement path for
`g-rl-38` subsystem tagging on `.gald3r_sys/` components. `gald3r validate`
(T520) enforces the task/bug *file* contract on staged `.gald3r/**` only — it
does not check component tagging. Intentionally NOT an agent-lifecycle event
hook: it is a git `pre-commit` / direct-check tool (allowlist it in the WS-A-5
hook-parity lint alongside `g-hk-pre-commit` / `g-hk-pre-push`).

## Relocation (T290) -> Unification (T293)
`.gald3r_sys/` is retiring. This hook's git-hooks wrapper directory moved from
`.gald3r_sys/git-hooks/` to a plain top-level `git-hooks/` directory in T290 --
the D-7 KEEP decision stands (the enforcement mechanism is unchanged; only the
install location moved). T293 went one step further and retired the standalone
`git-hooks/` directory entirely: this hook now runs as **stage 2** of the single
shared `.githooks/pre-commit` dispatcher, immediately after `g-hk-encoding-normalize`
(stage 1) -- see that hook's own doc. Repos still on the old `git-hooks/` setup
should re-run the setup snippet below, which now points `core.hooksPath` at
`.githooks` instead. Supersedes the failed T276 delete attempt (T276 confirmed
this file carries a live KEEP decision and cannot be deleted outright).

## Fires On
Git `pre-commit` event. Inspects every staged file under `.gald3r_sys/` at commit time.
Not auto-wired to `hooks.json` — activated via `git config core.hooksPath`.
See setup instructions below.

## What It Does
Scans staged `.md` files in `skills/`, `commands/`, `agents/`, `rules/` for a
`subsystem_memberships:` YAML frontmatter field, and staged `.ps1` files in
`hooks/`, `scripts/` for a `# @subsystems:` comment in the first 15 lines.
Blocks the commit (exit 1) if any staged file is missing its tag. Prints the
violation list and the valid group names.

## Side Effects
- No files written, no state changed — read-only scan
- Exits 0 (allow) on clean or non-.gald3r_sys files
- Exits 1 (block) on any untagged `.gald3r_sys` component file

## Setup (one-time per repo clone)

Both pre-commit checks -- `g-hk-encoding-normalize` and `g-hk-component-tag-check`
-- now share ONE tracked hooks directory, `.githooks/`, wired via `core.hooksPath`
(T293; there is no longer a separate `git-hooks/` directory to create):

```powershell
git config core.hooksPath .githooks
```

This points `core.hooksPath` directly at the already-tracked `.githooks` (T274:
the prior `install_git_hooks.py` installer script no longer exists anywhere in
the shipped payload -- `.gald3r_sys/` is purged from every project -- and was
never more than this one `git config` call).
`.githooks/pre-commit` is a small dispatcher that runs the encoding-normalize
check first, then the component-tag-check second, stopping on the first
nonzero exit; either stage skips gracefully if its target hook script is not
present in this project.

Run setup once; it persists in `.git/config`. After that every `git commit`
runs both checks.

## Related Tasks
- T1458 — subsystem sprawl prevention enforcement
- T1459 — the `aggregate_subsystems.ps1` aggregation script this tag-check enforces tagging
  for; the script itself was documented but never authored (BUG-196) and is now implemented
  natively as `gald3r subsystem aggregate`
- Rule: `g-rl-38` — component creation standards (always-applied)
- Commands: `@g-skill-new` / `@g-command-new` / `@g-rule-new` / `@g-create-hook` / `@g-agent-hire` — scaffold correctly-tagged components
