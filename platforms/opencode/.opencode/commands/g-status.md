---
subsystem_memberships: [PROJECT_IDENTITY_SETUP]
---
Generate project status overview: $ARGUMENTS

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

This check runs on every `@g-status` call. Results appear in the **Blockers & Risks** section.


### PCAC Inbox Gate (Only When PCAC Is Configured)

Before task claiming, implementation, verification, planning, or swarm partitioning, first determine whether this project is a PCAC participant. PCAC is configured only when `.gald3r/linking/link_topology.md` declares at least one parent/child/sibling relationship, or `.gald3r/PROJECT.md` explicitly declares PCAC project linking relationships. A Workspace-Control manifest and local `INBOX.md` alone do not make the project a PCAC group member.

If PCAC is configured, run the re-callable inbox check when the hook exists:

```powershell
$hook = @( ".cursor\hooks\g-hk-pcac-inbox-check.ps1", ".claude\hooks\g-hk-pcac-inbox-check.ps1", ".agent\hooks\g-hk-pcac-inbox-check.ps1", ".codex\hooks\g-hk-pcac-inbox-check.ps1", ".opencode\hooks\g-hk-pcac-inbox-check.ps1" ) | Where-Object { Test-Path $_ } | Select-Object -First 1
if ($hook) { powershell -NoProfile -ExecutionPolicy Bypass -File $hook -ProjectRoot . -BlockOnConflict }
```

Installed templates may call the equivalent hook from the active IDE folder. If the check reports `INBOX CONFLICT GATE` or exits with code `2`, stop immediately and run `@g-pcac-read`; do not claim tasks, create worktrees, spawn reviewers, or continue planning until conflicts are resolved. Non-conflict requests, broadcasts, and syncs are advisory and should be surfaced in the session summary. If PCAC is not configured, skip this gate and report `PCAC: not configured / skipped`.

## What This Command Does

Provides a comprehensive status update for your gald3r project.

## Status Analysis

### 1. Task Analysis (from TASKS.md)
I'll review:
- Total tasks by phase
- Tasks by status — labels and symbols from the **active workflow profile's**
  `task_statuses[]` (T1239 AC2), not hardcoded. For the default `software_dev`
  profile this is `[📋]` Ready, `[🔄]` In-Progress, `[🔍]` Awaiting-Verification,
  `[✅]` Done, `[❌]` Failed; a `content_creation` project shows its own
  vocabulary (`[✍️]` Scripting, `[🎬]` In Production, `[✅]` Published, …)
- Tasks by priority: Critical, High, Medium, Low
- Recently completed tasks
- Blocked or stalled tasks
- Task completion velocity

### 2. Bug Analysis (from BUGS.md)
I'll examine:
- Total open bugs by severity
- Critical/High priority bugs requiring attention
- Bug resolution rate
- Recently closed bugs
- Long-standing bugs

### 3. Phase Progress
I'll check:
- Current active phase
- Phase completion percentage
- Remaining work in phase
- Dependencies blocking progress

### 4. Issue Identification
I'll highlight:
- **Blockers**: Tasks waiting on dependencies
- **Risks**: High-priority tasks not started
- **Delays**: Tasks taking longer than estimated
- **Critical Bugs**: Urgent issues needing attention

### 5. Workspace-Control Snapshot (only when configured)
If `.gald3r/linking/workspace_manifest.yaml` exists, I'll include a compact Workspace-Control section using `g-skl-workspace` status semantics:
- Active manifest path, workspace ID/name, owner repo ID, controlled member count, and member IDs
- Member lifecycle status, path reachability, write policy summary, and per-member git cleanliness when paths are reachable
- Current task/bug `workspace_repos` and `workspace_touch_policy` routing metadata when present
- A clear distinction between PCAC topology/INBOX/order state and Workspace-Control member registry state
- Task 177 deferral reminder when backend, UI, Docker/Kubernetes/MCP, Valhalla, Yggdrasil, or control-plane status would otherwise be implied

If the manifest is absent, workspace output stays quiet unless you explicitly ask for workspace details.

## Status Report Format

### 🧩 Project Type (T1283)
- Project type: `{project_type}` (from `.gald3r/.identity`; default `software_development` if absent)
- Workflow profile: `{project_type}.yaml` (`.gald3r/config/workflow_profiles/`)
- GitHub integration: `{enabled|disabled}` (enabled only when `project_type=software_development`)
- Show this line near the top of the report; no-op silently when invoked outside a gald3r project.

### 🔀 Workflow (T1239)
- Resolve the active profile via `load_profile.py` (active skill folder; hybrid
  activation chain) and display: `Workflow: {profile.name} ({profile.id}.yaml)`,
  e.g. `Workflow: Content Creation (content_creation.yaml)`.
- This is the session-start workflow header (T1239 AC5). Skip silently when
  `.gald3r/config/workflow_profiles/` is absent (pre-T1238 installs).
- All status labels/badges below come from the active profile's `task_statuses[]`
  (`symbol` + label), **not** hardcoded strings (T1239 AC2). `software_dev`
  resolves to the legacy labels, so code repos render unchanged.

### 📋 Task Summary
- Total tasks: X (Y pending, Z in-progress, W completed)
- Completion rate: X%
- Recent completions: [List]
- **PR column (T1293)**: when at least one task has a `pr_url`, show a compact `PR` column
  per task line — `#1234 (ready)` / `#1234 (merged)` from the task's `pr_url` + `pr_status`
  frontmatter. **Omit the column entirely** when no task has a `pr_url` (keeps non-software /
  integration-off projects clean). This is a **pure display read** — never makes a GitHub API
  call. `@g-status --pr-detail` shows full URLs and (if cached) check status.

### 🐛 Bug Summary
- Open bugs: X (Y critical, Z high)
- Resolution rate: X bugs/week
- Critical issues: [List]

### 📊 Phase Progress
- Current Phase: [Name]
- Progress: X% complete
- Remaining: Y tasks

### ⚠️ Blockers & Risks
- Blocked tasks: [List]
- High-priority delays: [List]
- Critical bugs: [List]

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

- `--json` → structured JSON envelope via **g-skl-json-output** (`{ gald3r_version, generated_at, command, schema, data }`). For scripting, CI gates, dashboards.
- `--toon` → **g-skl-toon-output** TOON: compact, lossless, LLM-friendly (tabular arrays state keys once; ~20% smaller than JSON). For agent handoff / context injection / vault ingestion.
- `--md` forces markdown. With no flag, AGENT_CONFIG `output_format` decides (default `markdown`, unchanged).

Output is saved to `html_output_dir` (default `docs/`) as `YYYYMMDD_HHMMSS_<IDE>_<TOPIC>.json|.toon` per g-rl-01.
