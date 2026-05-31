---
subsystem_memberships: [PLATFORM_INTEGRATION]
---
# g-hook-new - Scaffold a new hook in YOUR project

Creates a new automation hook for your own project. You choose which AI platform folder it targets
(e.g. `.cursor/hooks/`, `.claude/hooks/`) and it wires that platform's `hooks.json`. Never writes
to `.gald3r_sys/`.

## Usage

```
@g-hook-new <hook-name> <event>
```

- `<hook-name>` - slug for the hook script.
- `<event>` - a lifecycle event for your platform (e.g. `sessionStart`, `beforeShellExecution`,
  `postToolUse`, `afterFileEdit`, `stop`).

## Steps

Activates **g-skl-hook-new**.

1. Ask **which platform(s)** to target (only those you have installed: `.cursor/`, `.claude/`, ...).
2. Write `<platform>/hooks/<hook-name>.ps1` (or `.sh`) using the stdin-JSON contract
   (exit 0 = allow, exit 2 = block) and a companion `<hook-name>.md` description.
3. Wire `<platform>/hooks.json` for `<event>` if it is a registered event for that platform.
4. Implement your hook body and test the JSON contract.

## Related

- Skill: `g-skl-hook-new` (implementation)
- Maintainer-only equivalent (edits gald3r itself): `@g-gald3r-hook-new`
