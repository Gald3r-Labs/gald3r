---
subsystem_memberships: [MEMORY_AND_KNOWLEDGE]
---
Toggle terse mode on or off: $ARGUMENTS

Activates the **g-skl-keep-it-simple** skill, which suppresses the active
personality pack, markdown decoration, and end-of-turn footer for the
remainder of the current session. Use for rapid Q&A, live debugging, or
token-budget-sensitive batch work.

## Usage

```text
@g-keep-it-simple              # turn terse mode ON
@g-keep-it-simple off          # turn terse mode OFF
@g-keep-it-simple status       # show current terse-mode state
/g-keep-it-simple              # alias for @-form
```

`$ARGUMENTS` is one of `on` (default when empty), `off`, `status`.

## On activation

The agent acknowledges with a single line — for example:
`Terse mode on.` — and then proceeds in terse mode (no persona, no
structure, no footer) until deactivation.

## On deactivation

The agent acknowledges with a single line — for example:
`Terse mode off.` — and resumes normal verbose behavior.

## Scope

- **Session-scoped**: terse mode does not persist to
  `.gald3r/.identity`, `AGENT_CONFIG.md`, vault memory, or any other
  durable surface. A new session starts in normal verbose mode.
- **Per-conversation**: in multi-window setups, terse mode is per
  conversation, not global.
- **Tool calls unaffected**: terse mode changes output presentation only.
  Tool calls, hooks, PCAC checks, and gald3r system gates execute
  unchanged.

## Safety

All gald3r safety gates continue to fire in terse mode:

- Bug-discovery gate (`g-rl-35`)
- Todo-completion gate (`g-rl-34`)
- Code-change-requires-task gate (`g-rl-33`)
- Member-marker invariant (`g-rl-36`)
- PCAC inbox gate, Clean Controller Gate, secrets detection

Terse mode reduces ceremony, not safety.

## See also

- Skill: `g-skl-keep-it-simple` (`.claude/skills/g-skl-keep-it-simple/SKILL.md`)
- Related: `@g-pers-pick`, `@g-pers-list`

## Source

Task 1052 (2026-05-13).
