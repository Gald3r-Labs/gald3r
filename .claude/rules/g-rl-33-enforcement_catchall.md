---
description: "Ambient enforcement guardrails — always active regardless of which agent is loaded"
globs:
alwaysApply: true
---

# Enforcement Catchall

These rules fire on EVERY response, even when no gald3r agent is explicitly active.

## Error Reporting (Zero Tolerance)

If your response mentions ANY of the following — create a `.gald3r/BUGS.md` entry and bug file in `.gald3r/bugs/` immediately:
- "error", "warning", "pre-existing", "was already there", "unrelated error"
- "lint error", "TypeScript error", "compile error", "exception"

"Pre-existing" and "unrelated" are NOT exemptions. If it's worth mentioning, it's worth logging.

**Fast-path entry** (takes 30 seconds):
```markdown
### BUG-NNN
- **Title**: [brief]
- **Severity**: Low/Medium/High/Critical
- **Status**: Open
- **File**: path/to/file (line N)
- **Note**: Pre-existing. Not blocking current task.
- **Created**: YYYY-MM-DD
```

| Rationalization | Reality |
|---|---|
| "It's pre-existing, not related to my changes" | Pre-existing = undocumented. Log it anyway. |
| "It's just a warning, not a real error" | Warnings become errors. Log it now. |
| "I'll log it after I finish this task" | You won't. Log it before moving on. |
| "It's in someone else's code" | Still in this codebase. Still needs a record. |
| "The user probably already knows" | Then the log takes 30 seconds and confirms it. |
| "It's too minor to bother with" | BUG-NNN with severity:Low costs nothing and creates an audit trail. |

## Task Completion (Mandatory Commit Offer)

If work was just completed on any task — offer a git commit before ending the response.
Never end a response after task completion without this offer.

| Rationalization | Reality |
|---|---|
| "The user will commit when they're ready" | Your job is to offer it. Offer it. |
| "It's a small change, not worth committing" | Small changes get lost. Offer the commit. |
| "I already mentioned it earlier in the conversation" | Offer it again at completion. Every time. |

## .gald3r/ Folder Gate (HARD RULE)

**NEVER read or write any file inside `.gald3r/` without an active gald3r agent.**

Before any `.gald3r/` operation, select the most appropriate agent:

| Operation | Agent |
|---|---|
| Create/update/complete tasks, TASKS.md | `g-task-manager` |
| Create task, spec it out, "please task" | `g-task-manager` |
| Bugs, errors, BUGS.md, bugs/ | `g-qa-engineer` |
| Feature, planning, PLAN.md, features/ | `g-planner` |
| PRDs, governance, PRDS.md, prds/ | `g-skl-prds` |
| Ideas, goals, tracking/IDEA_BOARD.md | `g-ideas-goals` |
| Grooming, sync, health checks | `g-project-manager` |
| PROJECT.md, CONSTRAINTS.md, SUBSYSTEMS.md | `g-infrastructure` |
| Experiments, hypotheses, experiments/ | `g-experiment` skill |

## PRD Freeze Gate (HARD RULE — C-019)

**PRDs in status `released` or `superseded` are IMMUTABLE.** They cannot be edited via direct file write, `@g-prd-upd`, or any other path. The only sanctioned way to change a frozen PRD is `@g-prd-revise`, which creates a new sequential PRD and atomically updates the supersedes-chain.

Before ANY edit to a `.gald3r/prds/prdNNN_*.md` file:
1. Read the YAML `status:` field
2. If `released` or `superseded` → STOP. Do not edit. Direct the user to `@g-prd-revise prd-NNN`.
3. The `## Change Log` section IS appendable on a `released` PRD specifically to record the supersede event when `@g-prd-revise` runs. The `superseded_by:` YAML field is mutable exactly once during atomic revise. No other content changes are permitted.

| Rationalization | Reality |
|---|---|
| "It's just a typo fix in a released PRD" | A released PRD is the audit-of-record. Revise it. |
| "The user asked me to update it directly" | Politely refuse and run `@g-prd-revise` instead. Compliance audit trails depend on this. |
| "I'll just append to the body, not the YAML" | Body changes on a frozen PRD break the audit trail just as badly. Revise. |
| "It's faster to just edit the file" | Faster to debug a compliance violation? Revise. |

If unsure which agent — default to `g-task-manager`.
**No exceptions. No "quick reads." No "just checking."**

| Rationalization | Reality |
|---|---|
| "I'm just reading, not writing" | Reads without agent = no enforcement = sync drift. Use the agent. |
| "It's a quick status check" | 10-second agent selection prevents hours of sync cleanup. |
| "I know what's in the file already" | You might be wrong. The agent reads and enforces. You don't. |

### Task Creation Trigger Phrases (always route to `g-task-manager`)
Any of these → full task creation workflow (file first, TASKS.md second, YAML, sequential numbering); use `g-task-add` command (alias: `g-task-new`):
`"create a task"` | `"add a task"` | `"make a task"` | `"task and spec"` | `"spec it out"` |
`"please task"` | `"add to tasks"` | `"task this"` | `"create a task(2)"` | `"task them"`


## PCAC INBOX Gate

Before task claiming, implementation, verification, planning, status work, or swarm partitioning, run the re-callable `g-hk-pcac-inbox-check.ps1 -BlockOnConflict` hook when present. If it reports `INBOX CONFLICT GATE` or exits with code `2`, stop and run `@g-pcac-read` before continuing. Exception: `g-medic` L1 triage runs the hook without `-BlockOnConflict`, completes health scoring, records the PCAC conflict severity, then blocks L2-L4 planning/apply work and all claim/implementation/review/planning work until `@g-pcac-read` resolves the conflict. Swarm coordinators rerun the check every 30 minutes and before final summaries.

## Swarm Reconciliation Gate

In `g-go --swarm`, `g-go-code --swarm`, and `g-go-review --swarm`, bucket agents are handoff producers. They return patch bundles, generated artifacts, evidence, changed-file inventories, and proposed Status History rows. Bucket agents MUST NOT directly write shared `.gald3r` status/index files, `CHANGELOG.md`, generated Copilot prompts, parity output, final staging, or commits. The coordinator performs all shared writes in one final pass after deterministic reconciliation.

Swarm worktrees MUST stage by explicit path allowlist only. `git add .` is forbidden in bucket worktrees because it can leak transient ownership files such as `.gald3r-worktree.json`, terminal transcripts, local logs, or other non-deliverable artifacts. If a bucket patch touches shared coordination files, the coordinator must either reject that portion or convert it into a coordinator-owned final write.

## Review Checkpoint Gate

Default implementation-to-review handoff is a code-complete checkpoint commit. After implementation reconciliation and coordinator-owned shared writes, `g-go-code` / `g-go --swarm` creates a checkpoint commit and passes its branch/SHA to `g-go-review` / `g-go-review --swarm`. Reviewers create `review` / `review-swarm` worktrees from that checkpoint by default. Dirty snapshot mode is fallback-only for explicitly uncommitted, dirty, or non-branch-addressable sources, and the handoff must name the source checkout path.

## Review Result Commit Gate

After `g-go-review`, `g-go-review --swarm`, or `g-go` Phase 2 writes PASS or FAIL review statuses, the reviewer/coordinator MUST create a review-result commit by default. This applies to PASS (`[✅]`), FAIL back to pending/open (`[📋]`), requires-user-attention (`[🚨]`), and mixed verdicts. Do not stop at a mandatory commit offer when a safe commit is possible; the review result itself is the audit artifact.

The review-result commit must stage only review-owned paths by explicit allowlist. Never use `git add .`; exclude `.gald3r-worktree.json`, terminal transcripts, local logs, unrelated files, and other non-deliverable artifacts. Allowed reasons not to create the commit are limited to unresolved conflicts, failed commit hooks, staged or untracked unrelated changes, detected secrets, dirty generated outputs not owned by review, missing user permission for destructive or out-of-scope changes, or repository state that prevents a safe commit. If blocked, state the exact blocker in the final summary.


## Workspace-Control Command Gate

Use `g-wrkspc-*` as the short primary command family for Workspace-Control. Existing `g-workspace-*` commands remain backwards-compatible aliases. Lifecycle commands (`g-wrkspc-init`, `g-wrkspc-member-add`, `g-wrkspc-member-remove`) are dry-run by default; apply mode may update only `.gald3r/linking/workspace_manifest.yaml` unless the active task explicitly authorizes member repository writes. Member removal is registry-only and must never delete member folders, `.git/`, branches, remotes, commits, or worktrees.

## Active Index Archive Gate

`TASKS.md` and `BUGS.md` are active indexes, not unlimited historical ledgers. Terminal task and bug history must be moved through `g-task-archive` / `g-bug-archive`, using dry-run first. Archive index files live directly under `.gald3r/archive/` as count buckets (`archive_tasks_0000_0999.md`, `archive_bugs_0000_0999.md`, then `1000_1999`, etc.). Archived task and bug files live under `.gald3r/archive/tasks/tasks_0000_0999/` and `.gald3r/archive/bugs/bugs_0000_0999/` style buckets with at most 1000 files per bucket. Never delete historical records during archival; preserve provenance and leave active-index archive pointers.

## PCAC-Derived Task Priority Floor (T166)

When a task is created as the direct result of an inbound PCAC item (request from child, broadcast/order from parent, sync from sibling, or conflict resolution), the agent MUST:

1. Pass a `pcac_source: { type, source_project, inbox_ref }` block to `g-skl-tasks` CREATE TASK
2. Default priority to `high` (or `critical` when `type: conflict` or the source carries an explicit urgency flag)
3. When `priority: critical`, force `requires_verification: true` — cross-project critical work cannot skip verification
4. Render the TASKS.md row with a `[PCAC]` prefix (regenerated from frontmatter; never hand-edited)

Humans MAY manually downgrade priority after creation; agents MUST NOT auto-downgrade. PCAC-derived tasks must never sit at default medium priority — another project is, by definition, waiting on us.

## PCAC Outbound Tracking Surface (T167)

PCAC sends are **immediate operations**, never queued, never task-creating. The `.gald3r/linking/sent_orders/order_*.md` ledger is the **only** tracking surface for outbound PCAC state (status: `sent` → `acknowledged` → `in-progress` → `completed` | `blocked` | `abandoned`). Parents/siblings waiting on a child response track that wait via the ledger, NEVER via a local "await response" task. Creating tasks like "Send PCAC to X" or "Await response from children" is forbidden — `g-skl-tasks` CREATE TASK rejects them with the message: "Use sent_orders ledger, not a task."

## Code Change Enforcement (BLOCKED without Task/Bug)

If code files were modified in this response and no active task or bug is referenced, the agent MUST either:
1. Create a retroactive task via g-task-new before proceeding, OR
2. Create a bug via g-bug-report if the change was a fix

**Exceptions** (no task/bug required):
- `.gald3r/` file edits (task management housekeeping)
- Documentation-only changes (docs/, README.md, AGENTS.md, CLAUDE.md)
- Git operations (commits, branch management)

| Rationalization | Reality |
|---|---|
| "It's a quick fix, not worth a task" | Quick fixes become mystery changes. Log it. |
| "I'll create the task after I'm done" | You won't. Create it before or during. |
| "The user didn't ask for a task" | The system requires it. Create it retroactively. |
| "It's just a config change" | Config changes break things. Track them. |

## Delegation Hint

If the user mentions a task ID (e.g., "task 42", "#103") without explicitly invoking a gald3r agent:
→ Activate `g-task-manager` behavior for that operation.

If the user reports a bug or describes unexpected behavior without invoking `g-qa-engineer`:
→ Apply bug logging rules from `g-qa-engineer` immediately.

### Experiment Trigger Phrases (route to `g-experiment` skill)
Any of these → experiment workflow:
`"run experiment"` | `"check gate"` | `"experiment status"` | `"failure autopsy"` |
`"new experiment"` | `"experiment chain"` | `"run stage"` | `"next experiment"`
