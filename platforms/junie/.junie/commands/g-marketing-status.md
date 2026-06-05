---
subsystem_memberships: [AGENT_ORCHESTRATION]
---
# @g-marketing-status

Show current marketing activity status — what's running, what's pending, recent wins.

## Usage
```
@g-marketing-status          # Full growth dashboard
@g-marketing-status --quick  # One-line summary of active channels
```

## What it does
1. Lists all marketing reports generated (`.gald3r/reports/marketing/`)
2. Shows open marketing tasks from TASKS.md
3. Summarizes active channels and their status
4. Lists recent wins (any tasks marked complete with marketing tag)
5. Recommends next best action

## Invoke
Activate `g-agnt-marketing` and run `g-skl-marketing` in STATUS mode.
