---
description: 'Show CRASH activation stats (Commands/Rules/Agents/Skills/Hooks) from crash_activations.jsonl.'
argument-hint: '[--write-report] [--reset] [--json] [--root <path>]'
subsystem_memberships: [LOGGING_SYSTEM]
execution_tier: orchestration
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

Engine equivalents (the command is a thin wrapper over the native `gald3r crash-stats` verb,
`gald3r_core.crash.activation` + `cli/commands/crash_stats_cmd.py`, T301):

```bash
gald3r crash-stats                        # report
gald3r crash-stats --write-report         # report + dated .md
gald3r crash-stats --reset                # archive + fresh start
gald3r crash-stats --json                 # JSON
gald3r crash-stats --root PATH            # target a project other than cwd
```

## Output Modes (session signature)

Set `GALD3R_CRASH_STATS` to surface a compact 3-5 line stats summary automatically:

| Value | Effect |
|---|---|
| `show_in_response` | Append the compact summary to the agent response (signature mode). |
| `show_in_log` | Write the summary to `.gald3r/logs/crash_stats_signature.log` only. |
| `show_in_terminal` | Print the summary table to stdout at session/dispatch end. |
| (unset / `off`) | **Disabled — zero overhead.** No recording, no signature. |

## Recording Activations (honest scope, T301 update)

**gald3r_core's own CLI dispatch (`cli/main.py`) does not yet auto-record every Command it
runs** — porting that producer (the donor's `CrashTracker` debug-tracer bridge) is out of T301's
scope (reader/reporter + thin verb only; see the filed follow-up task). Until that producer
lands, every activation in `.gald3r/logs/crash_activations.jsonl` comes from the
**manual/heuristic path**: the `g-hk-crash-record` hook (wired to the IDE's `stop` event, T1624)
or an explicit `record_activation(...)` call from a hook/agent/script. This means
`gald3r crash-stats` on a project where `GALD3R_CRASH_STATS` was never enabled and no hook has
fired honestly reports `total_activations: 0` — never fabricated numbers (g-rl-35) — rather than
implying command-level coverage that does not exist yet.

From a hook or script:

```bash
uv run python -c "from gald3r_core.crash import activation; activation.record_activation('skill','g-skl-tasks',trigger_source='@g-status',force=True)"
```

The **Never Activated** and **Should Be Called But Isn't** sections turn the gap into a positive
signal: any registered component (scanned from `.claude/`/`.cursor/` skills, rules, commands,
agents, hooks) with zero records is surfaced — rather than silently assumed-active. Rules/skills
that declare intent (`fires_on:` / `activate_for:`) but have 0 activations are flagged with ⚠️.

## Integration

- Complements **T432 debug mode** (`@g-... --debug`): debug shows the live call stack; CRASH stats
  store historical usage. When both are active, a command dispatch writes both in the same event.
- The compact signature is designed to drop into the standard `---` footer added by `g-rl-00`.
