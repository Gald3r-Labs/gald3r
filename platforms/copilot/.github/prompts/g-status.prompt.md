---
description: 'Generate a project status report — tasks, bugs, phase progress, blockers, Workspace-Control snapshot.'
argument-hint: '[--pr-detail] [--json|--toon|--md]'
subsystem_memberships: [PROJECT_IDENTITY_SETUP]
execution_tier: orchestration
---
Generate project status overview: $ARGUMENTS

### Compiled Retrieval (T494)

**Run `gald3r status` (or `gald3r status --json` for machine-parseable output) FIRST, before doing anything else in this command.** It is a real, deterministic, DB-backed engine verb (`cli/commands/project_status_cmd.py`) — not something to re-derive with ad-hoc SQL or a hand-rolled frontmatter parser in-session. It replaces this command's RETRIEVAL, not its judgment: everything below that references "from `gald3r status`" is now sourced from that verb's output; everything else in this file (spec_task_reqs resolution, the WPAC hook invocation, Workspace-Control member detail, project type/workflow resolution, the PR column, phase progress, next priorities) is judgment this compiled verb deliberately does not attempt, and stays here.

`gald3r status --json` returns: `tasks.by_status` / `tasks.total` / `tasks.completed` / `tasks.completion_pct`, `pending_breakdown` (runnable/gated/blocked/below_value_floor counts), `bugs.by_status` / `bugs.open_total` / `bugs.open_by_severity` (respects `--min-severity`), `awaiting_verification.groups` (pre-grouped by `release_hold`: `ready_for_staging` / `held_manual` / `held_sync_required` / `held_other`), `dependency_blocked` (blocked task rows with `open_dependencies`), `active_milestone`, and `wpac.configured` (+ `parent`/`children`/`siblings` counts or a `reason`). If `.gald3r/gald3r.db` does not exist yet, it reports that plainly rather than crashing — run `gald3r db backfill` first for a fully populated report.

### Waiting Task Specable Check

Before completing the status report, scan `.gald3r/tasks/**/*.md` for any task with `status: waiting`. For each:

1. **Read `spec_task_reqs:`** — check whether all listed task IDs are `status: completed` in their task files.
2. **Report specable tasks** (all spec_task_reqs satisfied):
   ```
   ⌛ Specable now: T1239 (all spec_task_reqs satisfied — string reqs remain for human review)
   ```
3. **Report orphaned waiters** (a dep task is `[❌]` cancelled or `[⏸️]` paused AND `waiting_since` > 24h):
   ```
   ⚠️ Orphaned waiter: T1239 — dep T1238 was cancelled 2d ago. Use @g-task-upd --demote with a new plan or @g-task-upd --promote if requirements changed.
   ```
4. **Report specable soon** (some but not all spec_task_reqs satisfied):
   ```
   ⌛ Specable soon: T1240 (T1239 ✅, T1238 still in-progress)
   ```

This check runs on every `@g-status` call. Results appear in the **Blockers & Risks** section. This is NOT covered by `gald3r status` — resolving `spec_task_reqs:` needs a fan-out check against an arbitrary per-task id list no compiled helper covers yet.


### WPAC Inbox Gate (Only When WPAC Is Configured)

`gald3r status`'s `wpac.configured` field already tells you whether this project is a WPAC participant (same link_topology.md parent/child/sibling check the rule below describes) — use it instead of re-deriving the check. What it does NOT do is run the inbox hook itself (that has real side effects — blocking on conflict — so it stays an explicit prompt-layer action):

Before task claiming, implementation, verification, planning, or swarm partitioning, if `wpac.configured` is `true`, run the re-callable inbox check when the hook exists:

```powershell
$hook = @( ".cursor\hooks\g-hk-wpac-inbox-check.py", ".claude\hooks\g-hk-wpac-inbox-check.py", ".agent\hooks\g-hk-wpac-inbox-check.py", ".codex\hooks\g-hk-wpac-inbox-check.py", ".opencode\hooks\g-hk-wpac-inbox-check.py" ) | Where-Object { Test-Path $_ } | Select-Object -First 1
if ($hook) { python $hook -ProjectRoot . -BlockOnConflict }
```

Installed templates may call the equivalent hook from the active IDE folder. If the check reports `INBOX CONFLICT GATE` or exits with code `2`, stop immediately and run `@g-wpac-read`; do not claim tasks, create worktrees, spawn reviewers, or continue planning until conflicts are resolved. Non-conflict requests, broadcasts, and syncs are advisory and should be surfaced in the session summary. If `wpac.configured` is `false`, skip this gate and report `WPAC: not configured / skipped` (or reuse `gald3r status`'s own WPAC line verbatim).

## What This Command Does

Provides a comprehensive status update for your gald3r project.

## Status Analysis

### 1. Task Analysis (from `gald3r status` + TASKS.md)
`gald3r status` supplies the deterministic counts: total tasks by status (`tasks.by_status`), completion rate (`tasks.completion_pct`), the pending-queue breakdown (`pending_breakdown`), and the dependency-blocked list (`dependency_blocked`). Layer judgment on top:
- Tasks by phase, and status LABELS/symbols from the **active workflow profile's**
  `task_statuses[]` (T1239 AC2), not hardcoded. For the default `software_dev`
  profile this is `[📋]` Ready, `[🔄]` In-Progress, `[🔍]` Awaiting-Verification,
  `[✅]` Done, `[❌]` Failed; a `content_creation` project shows its own
  vocabulary (`[✍️]` Scripting, `[🎬]` In Production, `[✅]` Published, …)
- Tasks by priority: Critical, High, Medium, Low (read from task files — not part of `gald3r status`'s output)
- Recently completed tasks, task completion velocity (needs `created_date`/`completed_date` inspection — agent judgment)
- Blocked or stalled tasks: use `gald3r status`'s `dependency_blocked` list directly rather than re-deriving it

### 2. Bug Analysis (from `gald3r status` + BUGS.md)
`gald3r status`'s `bugs.open_total` / `bugs.open_by_severity` (respects `--min-severity`) give the deterministic counts. Layer judgment on top:
- Critical/High priority bugs requiring attention: read the `critical`/`high` buckets in `bugs.open_by_severity`
- Bug resolution rate, recently closed bugs, long-standing bugs (needs per-bug date inspection — agent judgment)

### 3. Phase Progress
I'll check:
- Current active phase
- Phase completion percentage
- Remaining work in phase
- Dependencies blocking progress

### 4. Issue Identification
I'll highlight:
- **Blockers**: `gald3r status`'s `dependency_blocked` list (tasks waiting on dependencies)
- **Risks**: High-priority tasks not started
- **Delays**: Tasks taking longer than estimated
- **Critical Bugs**: `gald3r status`'s `bugs.open_by_severity.critical`/`.high` buckets

### 5. Workspace-Control Snapshot (only when configured)
If `.gald3r/linking/workspace_manifest.yaml` exists, I'll include a compact Workspace-Control section using `g-skl-workspace` status semantics — this is a DIFFERENT, wider concept than `gald3r status`'s WPAC topology line (member registry/lifecycle/git-cleanliness detail vs. the narrower parent/child/sibling gate), deliberately not duplicated into the compiled verb:
- Active manifest path, workspace ID/name, owner repo ID, controlled member count, and member IDs
- Member lifecycle status, path reachability, write policy summary, and per-member git cleanliness when paths are reachable
- Current task/bug `workspace_repos` and `workspace_touch_policy` routing metadata when present
- A clear distinction between WPAC topology/INBOX/order state and Workspace-Control member registry state
- Task 177 deferral reminder when backend, UI, Docker/Kubernetes/MCP, Valhalla, Yggdrasil, or control-plane status would otherwise be implied

If the manifest is absent, workspace output stays quiet unless you explicitly ask for workspace details.

## Status Report Format

### 🧩 Project Type (T1283)
- Project type: `{project_type}` (from `.gald3r/.identity`; default `software_development` if absent)
- Workflow profile: `{project_type}.yaml` (`.gald3r/config/workflow_profiles/`)
- GitHub integration: `{enabled|disabled}` (enabled only when `project_type=software_development`)
- Show this line near the top of the report; no-op silently when invoked outside a gald3r project.

### 🔀 Workflow (T1239)
- Resolve the active profile via `gald3r project-type resolve` (active skill folder; hybrid
  activation chain) and display: `Workflow: {profile.name} ({profile.id}.yaml)`,
  e.g. `Workflow: Content Creation (content_creation.yaml)`.
- This is the session-start workflow header (T1239 AC5). Skip silently when
  `.gald3r/config/workflow_profiles/` is absent (pre-T1238 installs).
- All status labels/badges below come from the active profile's `task_statuses[]`
  (`symbol` + label), **not** hardcoded strings (T1239 AC2). `software_dev`
  resolves to the legacy labels, so code repos render unchanged.

### 📋 Task Summary
- Total tasks: X (Y pending, Z in-progress, W completed) — from `gald3r status`'s `tasks.by_status` / `tasks.total`
- Completion rate: X% — from `gald3r status`'s `tasks.completion_pct`
- Recent completions: [List]
- **Active milestone (g-rl-40 rule 6)**: `gald3r status`'s `active_milestone` line — steer task selection toward it when set, per that rule.
- **PR column (T1293)**: when at least one task has a `pr_url`, show a compact `PR` column
  per task line — `#1234 (ready)` / `#1234 (merged)` from the task's `pr_url` + `pr_status`
  frontmatter. **Omit the column entirely** when no task has a `pr_url` (keeps non-software /
  integration-off projects clean). This is a **pure display read** — never makes a GitHub API
  call. `@g-status --pr-detail` shows full URLs and (if cached) check status.

### 🚀 Release Pipeline (T419 — only when `tasks/awaiting-verification/` has content)
- Shown only when there are awaiting-verification tasks (`gald3r status`'s `awaiting_verification.total` > 0).
- `gald3r status`'s `awaiting_verification.groups` already groups by the task's `release_hold` frontmatter field (synced to `.gald3r/gald3r.db` on every write-through) — use it directly instead of re-deriving:
  - **Ready for staging**: `groups.ready_for_staging` (`release_hold: none`/omitted)
  - **Held — manual**: `groups.held_manual` (with `release_hold_reason` — read the task file directly; not a DB column, so not in the verb's output)
  - **Held — sync_required**: `groups.held_sync_required` (with `sync_with` partner — same caveat, read the task file)
- **Nudge**: when `groups.ready_for_staging` is non-empty, add `💡 N task(s) ready to ship — run @g-ship`.
- Read-only display; set/clear holds with `@g-task set-release-hold` / `@g-task clear-release-hold`.

### 🐛 Bug Summary
- Open bugs: X (Y critical, Z high) — from `gald3r status`'s `bugs.open_total` / `bugs.open_by_severity`
- Resolution rate: X bugs/week
- Critical issues: [List]

### 📊 Phase Progress
- Current Phase: [Name]
- Progress: X% complete
- Remaining: Y tasks

### ⚠️ Blockers & Risks
- Blocked tasks: `gald3r status`'s `dependency_blocked` list (id, title, and what each is blocked on)
- High-priority delays: [List]
- Critical bugs: `gald3r status`'s `bugs.open_by_severity.critical` bucket

### 🧭 Workspace-Control (if configured)
- Manifest: `.gald3r/linking/workspace_manifest.yaml`
- Owner: `{repo_id}` | Controlled members: `{count}` (`{ids}`)
- Members: `{id}` `{lifecycle}` `{path present/missing}` `{clean/dirty/missing}` `{writes allowed/blocked}`
- Routing: active task/bug scope `{workspace_repos}` with policy `{workspace_touch_policy}`
- Boundary: report-only; Task 177 defers backend/UI/control-plane systems

### 🚀 Next Priorities
1. [Priority 1]
2. [Priority 2]
3. [Priority 3]

## When to Use
- Daily standup preparation
- Weekly status reviews
- Sprint retrospectives
- Stakeholder updates

## What I Need From You
- Specific areas to focus on (optional)
- Time period for "recent" (default: last 7 days)

Let's see where your project stands!


## Structured output (`--json` / `--toon`) — T1381 / T1382

This command supports machine-readable output in addition to its default text/markdown:

- `--json` → structured JSON envelope via **g-skl-json-output** (`{ gald3r_version, generated_at, command, schema, data }`), wrapping `gald3r status --json`'s output as the `data` payload rather than an agent-composed dict. For scripting, CI gates, dashboards.
- `--toon` → **g-skl-toon-output** TOON: compact, lossless, LLM-friendly (tabular arrays state keys once; ~20% smaller than JSON). For agent handoff / context injection / vault ingestion.
- `--md` forces markdown. With no flag, AGENT_CONFIG `output_format` decides (default `markdown`, unchanged).

Output is saved to `html_output_dir` (default `docs/`) as `YYYYMMDD_HHMMSS_<IDE>_<TOPIC>.json|.toon` per g-rl-01.
