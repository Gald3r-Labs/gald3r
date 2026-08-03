---
description: 'Check whether this project''s Valkyrie world_tree connector is currently running (read-only)'
subsystem_memberships: [WORKSPACE_COORDINATION]
execution_tier: orchestration
---
# @g-valk-status — Check the Valkyrie world_tree connector's status

Run **`gald3r valk status`** to check whether the Valkyrie connector — the resident world_tree
sync connector, the online coordination backbone — is currently running for this project.

---

## Usage (PowerShell)

```powershell
gald3r valk status
gald3r valk status --root <path>   # project root containing .gald3r/ (default: discovered from cwd)
gald3r valk status --json          # machine-readable output
```

## What it does

Read-only: reads the project's connector lock (never writes) and reports:

- **Lock state** — `running` if the recorded pid is alive, `stale (pid dead — reclaimable on
  next start)` if the pid is dead, or "no connector lock found" if there is no lock at all.
- `pid`, `started_at`, `project_id`, and the resolved `lock_path`.

With `--json`, the same fields are emitted as a structured object instead of human-readable
lines: `found`, `running`, `pid`, `started_at`, `project_id`, `lock_path`.

## Flags

| Flag | Meaning |
|------|---------|
| `--root PATH` | Project root containing `.gald3r/` (default: discovered by walking up from cwd). |
| `--json` | Emit the status as structured JSON instead of human-readable lines. |

## See also

- `@g-valk-start` — start the connector (`--detach` for the resident, world_tree-synced process)
- `@g-valk-stop` — stop the running connector
- `@g-valk-list` — list every registered connector on this machine
