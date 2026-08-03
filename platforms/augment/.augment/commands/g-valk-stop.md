---
description: 'Stop the running Valkyrie world_tree connector for this project and clear its lock'
subsystem_memberships: [WORKSPACE_COORDINATION]
execution_tier: orchestration
---
# @g-valk-stop — Stop the Valkyrie world_tree connector

Run **`gald3r valk stop`** to stop the running Valkyrie connector (the resident world_tree sync
connector — the online coordination backbone) and clear its lock.

---

## Usage (PowerShell)

```powershell
gald3r valk stop
gald3r valk stop --root <path>       # project root containing .gald3r/ (default: discovered from cwd)
gald3r valk stop --data-dir <path>   # machine-wide gald3r data dir the registry lives under (default: $GALD3R_DATA_DIR or ~/.gald3r)
```

## What it does

1. Reads the connector lock for the project root. If no lock is found, reports there is
   nothing to stop and exits cleanly.
2. If the recorded pid is already dead, clears the stale lock and exits.
3. Otherwise sends a real termination signal (`SIGTERM`, which maps to `TerminateProcess` on
   Windows) to the connector process.
4. Force-releases the lock — a killed process's default `SIGTERM` handling does not guarantee
   its own cleanup runs, so the lock is not assumed to self-clean — and best-effort
   deregisters the project from the machine-wide connector registry.

## Flags

| Flag | Meaning |
|------|---------|
| `--root PATH` | Project root containing `.gald3r/` (default: discovered by walking up from cwd). |
| `--data-dir PATH` | Machine-wide per-user gald3r data dir the connector registry lives under (default: `$GALD3R_DATA_DIR` or `~/.gald3r`). |

## See also

- `@g-valk-start` — start the connector (`--detach` for the resident, world_tree-synced process)
- `@g-valk-status` — check whether the connector is running before/after stopping it
- `@g-valk-list` — list every registered connector on this machine
