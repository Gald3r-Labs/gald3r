Generate project status overview: $ARGUMENTS

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
