---
subsystem_memberships: [PLATFORM_INTEGRATION]
---
Show the cross-platform capability status index: $ARGUMENTS

## What This Command Does

Displays a concise read-only summary of `.gald3r/PLATFORM_STATUS.md` — the honest capability
index across all 23 platforms — and the rollup counts (N healthy, M need attention, K rework,
U unknown). Report-only; does not modify any file.

## Delegates To

- Skill: `g-skl-platform-monitor` (reads `PLATFORM_STATUS.md` / `PLATFORM_CAPABILITY_MATRIX.md`)
- Agent: `g-agnt-platformer`

## Workflow

1. Activate `g-agnt-platformer`.
2. Read `.gald3r/PLATFORM_STATUS.md`.
3. Print the summary line and any platforms not at `✅`.
4. To regenerate (not just read) the index, use `@g-platform-check` or
   `g-skl-platform-monitor GENERATE_MATRIX`.

## Safety Boundaries

- This command is report-only — it never writes status files.
- Honest status only: `❓` platforms stay `❓` until a per-platform task verifies them.

## Usage Examples

```
@g-platform-status
```

> **Status (T1460):** scaffolding. Reads the status stubs created by T1460; rows are filled by
> T1461–T1483.
