---
subsystem_memberships: [PLATFORM_INTEGRATION]
---
Check platform capability gaps vs. the Cursor reference: $ARGUMENTS

## What This Command Does

Reports the current capability state of one platform (or all 23 if no argument) by comparing
its declared support against the Cursor reference implementation. Delegates to
`g-skl-platform-monitor` operation `CHECK` and the `check_platform_status.py` script.

## Delegates To

- Script: `custom_scripts/check_platform_status.py -Platform <name>` (default: all)
- Skill: `g-skl-platform-monitor` → `CHECK`
- Agent: `g-agnt-platformer`

## Workflow

1. Activate `g-agnt-platformer`.
2. Run `check_platform_status.py -Platform $ARGUMENTS` to read `.gald3r/PLATFORM_STATUS.md`
   and report the current state.
3. For a deeper gap analysis, run `g-skl-platform-monitor CHECK <platform>` which compares the
   platform's `g-skl-platform-<name>/SKILL.md` against `g-skl-platform-cursor`.
4. Surface gaps: "cursor has X; <platform> has no equivalent".

## Usage Examples

```
@g-platform-check                # all 23 platforms
@g-platform-check windsurf       # one platform
```

> **Status (T1460):** scaffolding. The script reads/reports PLATFORM_STATUS.md; deep per-platform
> gap heuristics are fleshed out by T1461–T1483.
