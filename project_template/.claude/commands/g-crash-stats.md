---
subsystem_memberships: [LOGGING_SYSTEM]
---
Show CRASH activation stats (Commands / Rules / Agents / Skills / Hooks): $ARGUMENTS

## What This Command Does

Displays the **CRASH activation tracking** report (T433) — datetime invocation statistics for the
five gald3r extension-point types: **C**ommands, **R**ules, **A**gents, **S**kills, **H**ooks.
It answers: what is actually being invoked, what is never called, and what *should* be called
(declares intent) but isn't.

The data lives in `.gald3r/logs/crash_activations.jsonl` — one JSON line per activation:
`{component_type, component_name, activated_at, session_id, trigger_source, elapsed_ms}`.

## Operations

| Invocation | Effect |
|---|---|
| `@g-crash-stats` | Render the current stats report (Most Active / Least Active / Never Activated / Should Be Called But Isn't). |
| `@g-crash-stats --write-report` | Also write the dated `.gald3r/logs/crash_stats_YYYYMMDD.md`. |
| `@g-crash-stats --reset` | Archive `crash_activations.jsonl` → `crash_activations_YYYYMMDD_HHMMSS.jsonl` and start fresh. |
| `@g-crash-stats --json` | Machine-readable stats payload. |

Engine equivalents (the command is a thin wrapper over the engine):

```bash
uv run gald3r crash-stats                 # report
uv run gald3r crash-stats --write-report  # report + dated .md
uv run gald3r --crash-stats-reset         # archive + fresh start
uv run gald3r --json crash-stats          # JSON
```

## Output Modes (session signature)

Set `GALD3R_CRASH_STATS` to surface a compact 3-5 line stats summary automatically:

| Value | Effect |
|---|---|
| `show_in_response` | Append the compact summary to the agent response (signature mode). |
| `show_in_log` | Write the summary to `.gald3r/logs/crash_stats_signature.log` only. |
| `show_in_terminal` | Print the summary table to stdout at session/dispatch end. |
| (unset / `off`) | **Disabled — zero overhead.** No recording, no signature. |

## Recording Activations (honest scope)

The engine auto-records every **Command** it dispatches. IDE harnesses do **not** emit a discrete
event for every Rule/Skill/Agent/Hook activation, so those are recorded on the
**manual/heuristic path**: a hook or an agent reports an activation explicitly. From a hook or
script:

```bash
uv run python -c "from gald3r import crash; crash.record_activation('skill','g-skl-tasks',trigger_source='@g-status',force=True)"
```

The **Never Activated** and **Should Be Called But Isn't** sections turn the gap into a positive
signal: any registered component (scanned from `.claude/`/`.cursor/` skills, rules, commands,
agents, hooks) with zero records is surfaced — rather than silently assumed-active. Rules/skills
that declare intent (`fires_on:` / `activate_for:`) but have 0 activations are flagged with ⚠️.

## Integration

- Complements **T432 debug mode** (`@g-... --debug`): debug shows the live call stack; CRASH stats
  store historical usage. When both are active, a command dispatch writes both in the same event.
- The compact signature is designed to drop into the standard `---` footer added by `g-rl-00`.
