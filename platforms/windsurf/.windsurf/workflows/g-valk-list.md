---
description: 'List every registered Valkyrie world_tree connector on this machine via gald3r valk list'
subsystem_memberships: [WORKSPACE_COORDINATION]
execution_tier: orchestration
---
# @g-valk-list — List every registered Valkyrie connector on this machine

Run **`gald3r valk list`** to list every Valkyrie connector — the resident world_tree sync
connector, the online coordination backbone — registered machine-wide, across every project on
this machine.

---

## Usage (PowerShell)

```powershell
gald3r valk list
gald3r valk list --data-dir <path>   # machine-wide gald3r data dir the registry lives under (default: $GALD3R_DATA_DIR or ~/.gald3r)
gald3r valk list --json              # machine-readable output
```

## What it does

Read-only: reads the machine-wide connector registry (populated once a `valk start --detach`
child has registered itself) and reports, per registered connector: alive/dead state, `pid`,
`project_root`, `project_id`, `base_url`, and `started_at`.

With `--json`, emits `{"data_dir", "count", "daemons": [...]}` — one object per registered
connector, with fields `pid`, `alive`, `project_root`, `project_id`, `base_url`, `started_at`.

An empty registry still reports cleanly — a "no connectors registered" line in human mode, or
`"daemons": []` in JSON mode — rather than erroring.

## Flags

| Flag | Meaning |
|------|---------|
| `--data-dir PATH` | Machine-wide per-user gald3r data dir the connector registry lives under (default: `$GALD3R_DATA_DIR` or `~/.gald3r`). |
| `--json` | Emit the listing as structured JSON instead of human-readable lines. |

## See also

- `@g-valk-start` — start a connector (`--detach` for the resident, world_tree-synced process)
- `@g-valk-status` — check a single project's connector status
- `@g-valk-stop` — stop a running connector
