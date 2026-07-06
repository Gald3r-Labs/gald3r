---
gald3r_rel_version: "3.0.0"
schema_version: "generic-v1"
---
# HEARTBEAT.md — gald3r Scheduled Routines

Defines recurring "cron" routines for this project. Read by `g-hk-session-start.py`
(watchdog entries, T968), `g-hk-nightly-learn.py` (`nightly_learn:` switch), and the
SWOT/curator scheduled flows.

> FULL layout only. Slim installs do not ship this file. Lives at `.gald3r/config/HEARTBEAT.md`.

---

## Global Switches

```
nightly_learn: true
```

- `nightly_learn: false` disables the session-summary extraction in `g-hk-nightly-learn.py`.

---

## Cron Entries

Each routine is a YAML list item under this section. Two execution modes:

| Mode | `no_agent` | Behavior |
|------|-----------|----------|
| **Agent routine** (default) | `false` / absent | The scheduler invokes a gald3r agent/command on schedule. Full reasoning. |
| **Watchdog** (T968) | `true` | The `script:` runs **directly** at session start. Output is delivered **only if stdout is non-empty**. No agent, no LLM cost. Silent on empty output. |

### Entry fields

| Field | Required | Notes |
|-------|----------|-------|
| `id` | yes | Stable identifier; used for log filenames and banner labels. |
| `schedule` | yes | Cron expression (advisory; watchdogs also fire opportunistically at session start). |
| `no_agent` | no | `true` → watchdog mode. Defaults to `false`. |
| `script` | watchdog only | Path to the script to run directly (relative to project root or absolute). `.ps1` runs under PowerShell; other paths run as executables. |
| `output` | no | `log` (append to `.gald3r/logs/watchdog_<id>.log`) or `terminal` (default — surfaced in the session-start context banner). |
| `command` | agent only | The `@g-*` command/agent the scheduler should invoke (agent routines). |

### Watchdog contract (T968)

- Non-empty stdout is delivered **verbatim** to the configured channel.
- Empty stdout → completely silent: no agent call, no banner, no log line.
- A failing or missing script never blocks session start (errors are swallowed).

---

```yaml
# ── Watchdogs (no_agent: true) — cheap health checks, output only when non-empty ──

- id: disk-space-check
  schedule: "0 * * * *"
  no_agent: true
  script: .claude/skills/g-skl-medic/scripts/watchdog_disk_space.ps1
  output: terminal

- id: stale-worktree-check
  schedule: "0 */6 * * *"
  no_agent: true
  script: .claude/skills/g-skl-medic/scripts/watchdog_stale_worktrees.ps1
  output: terminal

- id: gald3r-sync-drift-check
  schedule: "*/30 * * * *"
  no_agent: true
  script: .claude/skills/g-skl-medic/scripts/watchdog_sync_drift.ps1
  output: log

# ── Agent routines (no_agent: false / default) — full reasoning, unchanged ──

- id: weekly-swot
  schedule: "0 14 * * 5"
  no_agent: false
  command: "@g-swot-review"

- id: skill-curator
  schedule: "0 3 * * 0"
  command: "@g-curator"
```

---

## Notes

- Watchdog scripts should print to stdout **only when there is something worth surfacing**
  (e.g. "WARNING: disk 92% full"). On a healthy check they should print nothing, keeping
  session start silent and zero-cost.
- The three example watchdog scripts above are illustrative health checks; create the
  referenced scripts under `.claude/skills/g-skl-medic/scripts/` (or repoint `script:`
  to your own). Missing scripts are skipped silently.
- This file is not committed by default (`.gald3r/` is gitignored in source repos).
