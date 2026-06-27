---
subsystem_memberships: [AGENT_ORCHESTRATION]
---
Show whether an active g-go-go run is ALIVE, IDLE-WAIT, or STALLED: $ARGUMENTS

## Purpose (T1585)

`g-go-status` is a **one-shot health indicator** for a `@g-go-go` autopilot run. When the
conductor runs (detached or in-session) there is no glanceable signal that it is alive and
making progress — the launcher session may show a red "Stop hook error" (the BUG-107
keep-alive, which *looks* like a failure), so a healthy run is easy to mistake for a wedged
one. This command collapses the manual `git log` + PID-probing dance into a single verdict you
can read in seconds.

It is strictly **READ-ONLY**: it reads the run-state marker and the last git commit, and never
writes `.gald3r/` state, never touches the marker, and never commits.

## Usage

```
@g-go-status                      # status of the run rooted at the nearest .gald3r
@g-go-status --json               # machine-readable (for scripts / CI gates / dashboards)
```

Run the reader directly (stdlib-only; `uv run python` also works):

```bash
python .gald3r_sys/scripts/ggo_status.py
python .gald3r_sys/scripts/ggo_status.py --json
python .gald3r_sys/scripts/ggo_status.py --project-root <dir>
```

## What it reports

- **VERDICT** — `ALIVE` / `IDLE-WAIT` / `STALLED` (plus `STOPPED`, `INACTIVE`, `NO-ACTIVE-RUN`)
- `active`, `iter`, `budget_remaining`, `mode`, `run_scope`, `platform`, `session_id`
- **Conductor process** — alive (if a PID is recorded/derivable), `in-session` (no detached
  process to probe), or `unknown` — best-effort, never hard-depends on a PID
- **Marker `updated_at`** + age, and the **last git commit** (time + subject) + age
- **Seconds since last progress** — the MOST RECENT of the marker stamp and the last commit
- The last `completed_iterations[]` summary, and `authorized_hard_stop` if a run stopped

## Verdict logic (thresholds are constants in the script)

Progress age = `min(marker_age, last_commit_age)` — the most recent of two independent
signals. A long single iteration that is still committing work stays ALIVE even while the
marker sits between per-iteration stamps; a frozen marker with no commits reads as STALLED.

| Verdict | Condition | Meaning |
|---------|-----------|---------|
| **ALIVE** | progress within `ALIVE_THRESHOLD_SEC` (default 10m) | making progress |
| **IDLE-WAIT** | progress between 10m and `STALLED_THRESHOLD_SEC` (default 30m) | healthy but waiting on the model — API I/O wait (0% CPU but progressing), **not** a wedge |
| **STALLED** | no progress > 30m and no recent commit | likely wedged — check the conductor |
| **STOPPED** | marker has `authorized_hard_stop` | run halted with a recorded reason |
| **INACTIVE** | marker present but `active:false` | the run has finished |
| **NO-ACTIVE-RUN** | no marker found | nothing running (graceful) |

The default thresholds are tuned to the conductor's behavior: the per-coordinator hang timeout
defaults to 25 min and a single Phase 1 + Phase 2 iteration legitimately runs many minutes while
waiting on the model, so the 10–30 min band is the normal "long iteration" zone (IDLE-WAIT),
and only past ~30 min with no new commits is it called STALLED. Edit `ALIVE_THRESHOLD_SEC` /
`STALLED_THRESHOLD_SEC` in `ggo_status.py` to retune.

Exit code: `0` for every verdict except **STALLED**, which exits `1` so a watchdog or CI gate
can trigger on a likely wedge.

## Follow-up — `--watch` (T1585 option 2, NOT in this command)

A refreshing heartbeat view (`--watch`, re-rendering this status every N seconds so the user
can leave it open and see it tick) is the documented next step. It is intentionally **not**
implemented here — this command is the bounded one-shot indicator (option 1). Track the watch
mode as a follow-up.

## Notes

- The reader depends on the marker being refreshed per-iteration (reliable after the
  BUG-181/182 conductor fixes). If the marker is stale but commits are recent, the commit
  signal keeps the verdict honest.
- PID liveness is best-effort: it uses a recorded `conductor_pid`/`pid` if present, otherwise
  reports `in-session` (when the marker mode indicates an in-session coordinator) or `unknown`.
  It never fails the verdict on a missing PID.
