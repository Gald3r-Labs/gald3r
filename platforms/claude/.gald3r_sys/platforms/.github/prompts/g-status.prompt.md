Generate project status overview: $ARGUMENTS


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
- Tasks by status: `[ ]` Pending, `[📋]` Ready, `[🔄]` In-Progress, `[✅]` Completed, `[❌]` Failed
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

### 📋 Task Summary
- Total tasks: X (Y pending, Z in-progress, W completed)
- Completion rate: X%
- Recent completions: [List]

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
