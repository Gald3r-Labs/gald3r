---
subsystem_memberships: [PLATFORM_INTEGRATION]
---
Scaffold a new gald3r hook script + companion `hook.md` self-description in one step.

```
@g-hook-create <hook-name> <event>
```

- `<hook-name>` — slug like `g-hk-my-thing`. The `g-hk-` prefix is required.
- `<event>` — one of `sessionStart`, `stop`, `beforeShellExecution`, `preToolUse`, `postToolUse`, `subagentStart`, `subagentStop`, `beforeSubmitPrompt`, `afterFileEdit`, `pre_skill`, `post_skill`, `pre_session`, `post_session`, `manual`, `git-pre-commit`, `git-pre-push`, `nightly`.

### gald3r-internal lifecycle events (T1055)

`pre_skill`, `post_skill`, `pre_session`, and `post_session` are **gald3r-internal**
lifecycle events, not native Cursor / Claude Code harness events — neither IDE
exposes a skill-boundary or gald3r-session-boundary event. They are dispatched by
the gald3r skill/command runner (or fired manually) and, like `manual` / `nightly`,
are scaffolded but **NOT auto-wired** into `hooks.json`. Their payloads (on stdin):

| Event | Payload fields | When it fires |
|-------|----------------|---------------|
| `pre_skill` | `skill_name`, `skill_path`, `timestamp` | Immediately before a skill body executes |
| `post_skill` | `skill_name`, `skill_path`, `timestamp` | Immediately after a skill body finishes |
| `pre_session` | `session_id` (if available), `project_path` | At the start of a gald3r work session |
| `post_session` | `session_id` (if available), `project_path` | At the end of a gald3r work session |

Reference examples (with companion `hook.md`): `hooks/g-hk-pre-skill-timing.ps1`,
`hooks/g-hk-post-skill-timing.ps1` (per-skill timing/tracing), and
`hooks/g-hk-pre-session-trace.ps1`, `hooks/g-hk-post-session-trace.ps1`
(per-session observability). They are non-blocking and emit the standard
`{ continue = true }` stdout envelope. The `_doc.gald3r_lifecycle_events` block in
`hooks.json` records the same contract.

## What it creates

For each gald3r IDE target (`.cursor/`, `.claude/`, `.agent/`, `.codex/`, `.opencode/`):

1. `<ide>/hooks/<hook-name>.ps1` — PowerShell skeleton (Cursor / Claude hook contract on stdin / stdout, exit-code based BLOCK / ALLOW, idempotency guard pattern from T839 when appropriate).
2. `<ide>/hooks/<hook-name>.md` — companion self-description with the canonical 5-section template (see below).

It also wires `<ide>/hooks.json` (Cursor + Claude) and `.github/hooks/gald3r-hooks.json` (Copilot) to the new hook when `<event>` is a registered Cursor / Claude / Copilot lifecycle event. `manual`, `git-pre-commit`, `git-pre-push`, and `nightly` are scaffolded but NOT auto-wired to `hooks.json` — they are invoked by other paths (`core.hooksPath`, HEARTBEAT scheduler, direct shell call).

## Companion `hook.md` template

```markdown
# Hook: <hook-name>

## Fires On
<event description: trigger, matcher, idempotency story>

## What It Does
<2-3 sentence description of the hook's job — what it inspects, what it decides>

## Side Effects
<files written, processes run, state changed, allow / deny verdicts>

## Related Tasks
<T### IDs that introduced or modify this hook; cross-links to rules / constraints>
```

The 5-section format is intentionally lean (~30-60 lines max per `hook.md`). It is *not* full design documentation — full designs live in `docs/<timestamp>_*_HOOK_*.md`. The companion is the runtime context the harness injects when the hook fires (Task T1171).

## Pattern reference

Activates the **hook-create** skill (`skills/hook-create/SKILL.md`) for the underlying Cursor / Claude hook-authoring conventions: hooks.json schema, JSON envelope contract on stdin, exit codes (0=allow, 2=block), matcher syntax, `failClosed` vs warn-only, T600 hook contract extensions (`block_on_failure`, `tool_match`, HTTP hook type, shell-safe arg substitution).

For the gald3r-specific idempotency guard pattern (`$env:GALD3R_HK_<NAME>_APPLIED`), see `skills/g-skl-platform-cursor/SKILL.md` §11 "Hook Authoring — Idempotency Guard Pattern".

## Subsystem Tagging (g-rl-38 — mandatory)

The scaffolded `.ps1` hook MUST include `# @subsystems: GROUP` in its first 15 lines.
This is already part of the scaffold template output. If omitted, the git pre-commit hook
`g-hk-component-tag-check` will block the next commit. Valid groups listed in `g-rl-38`.
After scaffolding, offer to regenerate `PRODUCT_SYSTEMS.md`:
`pwsh .gald3r_sys/scripts/aggregate_subsystems.ps1`

## After scaffolding

1. Implement the hook body in `.cursor/hooks/<hook-name>.ps1` (canonical).
2. Mirror to `.claude/`, `.agent/`, `.codex/`, `.opencode/` (the scaffold step does this automatically; subsequent edits use `custom_scripts/platform_parity_sync.ps1`).
3. Update the `hook.md` `## Side Effects` and `## Related Tasks` sections to match the final implementation.
4. Add an entry to `CHANGELOG.md` under `### Added` per `g-rl-26`.
5. Run the hook directly to verify the JSON contract and exit-code behavior.

## Related

- Task: T1171 (OpenClaw hook.md self-description pattern → gald3r hooks)
- Source: V18 OpenClaw Hooks Crash Course harvest (Bdr7afGhh4I, 2026-05-13)
- Skill: `hook-create` (generic Cursor hook authoring)
- Skill: `g-skl-platform-cursor`, `g-skl-platform-claude` (hook.md companion pattern documentation)
