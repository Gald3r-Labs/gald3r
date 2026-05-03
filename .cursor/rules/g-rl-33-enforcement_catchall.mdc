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

Before task claiming, implementation, verification, planning, status work, or swarm partitioning, first determine whether the current project is a **PCAC participant**. PCAC is active only when `.gald3r/linking/link_topology.md` exists and declares at least one non-empty parent, child, or sibling relationship, or when `.gald3r/PROJECT.md` explicitly declares PCAC project linking relationships. A Workspace-Control manifest (`.gald3r/linking/workspace_manifest.yaml`) and a local `INBOX.md` alone do **not** make a project part of a PCAC group.

If and only if the current project is a PCAC participant, run the re-callable `g-hk-pcac-inbox-check.ps1 -BlockOnConflict` hook when present. If it reports `INBOX CONFLICT GATE` or exits with code `2`, stop and run `@g-pcac-read` before continuing. Exception: `g-medic` L1 triage runs the hook without `-BlockOnConflict`, completes health scoring, records the PCAC conflict severity, then blocks L2-L4 planning/apply work and all claim/implementation/review/planning work until `@g-pcac-read` resolves the conflict. Swarm coordinators rerun the check every 30 minutes and before final summaries only while PCAC is active.

If the project is not a PCAC participant, skip the PCAC hook and report `PCAC: not configured / skipped` when status or medic output includes gate state.

## Gald3r Housekeeping Commit Gate (T531 — `g-go*` only, controller-only)

Sits between the **PCAC INBOX Gate** and the **Clean Controller Gate** on the `g-go`, `g-go-code`, `g-go-review`, `g-go-swarm`, `g-go-code-swarm`, and `g-go-review-swarm` paths. It runs at two points: (a) **preflight** — before claims, worktrees, coding, review, or swarm partitioning; and (b) **post-coordinator-write** — immediately after `g-go*` coordinator-owned shared `.gald3r` writes (task/bug status updates, review-result writes, sent_orders ledger updates, safe report/log outputs) and before the next major phase.

Behavior at each invocation:

1. Run `scripts/gald3r_housekeeping_commit.ps1` against the orchestration git root. The helper reads `git status --porcelain=v1 -uall`, classifies every dirty path against an explicit allowlist of safe controller `.gald3r/` coordination paths and a deny list of sensitive/identity/config paths, and returns one of: `clean`, `safe-gald3r-housekeeping`, `safe-gald3r-coordination`, `unsafe-gald3r`, `mixed-dirty`, `conflict`, `drift-detected`, or `committed-*` (when `-Apply`).
2. If `clean` → continue without writing.
3. If `safe-gald3r-housekeeping` (preflight) or `safe-gald3r-coordination` (post-write) → invoke the helper with `-Apply`. The helper stages **only** the classified-safe paths via explicit `git add -- <paths>`, re-checks for drift, then commits with one of:
   - `chore(gald3r): preflight gald3r housekeeping`
   - `chore(gald3r): commit g-go coordination state`
   Include `Task: #<id>` / `Bug: BUG-<id>` in the body when ownership is clear (the helper accepts `-TaskId` / `-BugId`). `git add .` is **never** used.
4. If `unsafe-gald3r`, `mixed-dirty`, `conflict`, or `drift-detected` → preserve the existing **Clean Controller Gate** hard-block. Do not auto-commit. Report the exact unsafe paths and reasons; user action required.
5. Member-repo targets (marker-only `.gald3r/` with `.identity` but no manifest and no `TASKS.md`) are refused with `config-fault`. The helper never writes member repository `.gald3r/` content.

Concurrency / drift protection: in `--swarm` flows only the coordinator runs this gate, and the helper re-checks `git status` immediately before staging and again immediately after committing; if another writer altered the tree between classify and stage, the helper aborts the staging and exits non-zero with `drift-detected` so the coordinator falls back to the hard-gate path.

This gate is **controller-only `g-go*` behavior**. It is not a global rule for every gald3r command. Member repositories' marker-only `.gald3r/` policy is unchanged.

## Clean Controller Gate (orchestration repo)

After the PCAC gate passes and **before** task or bug claims, T170 worktree allocation (`gald3r_worktree.ps1 -Action Create`), swarm partitioning, or any coordinator-owned write to shared `.gald3r` ledgers (for example `.gald3r/TASKS.md`, `.gald3r/BUGS.md`, task/bug files when acting as coordination surfaces), `CHANGELOG.md`, generated Copilot instructions, or parity output, agents MUST verify the **orchestration git root** is clean enough to land the required checkpoint or review-result commit.

- The **Gald3r Housekeeping Commit Gate** runs first (see the section directly above). It may auto-commit dirty paths that are exclusively safe controller `.gald3r/` housekeeping; only paths it classifies as unsafe / mixed / unknown reach this gate as blockers.
- Run `git status --short` at the repository root from which `g-go*`, `g-go-code*`, or `g-go-review*` is executed (Workspace-Control owner when a manifest is active).
- Any path **outside** this run's explicit coordinator staging allowlist for the active task and bug IDs is a **blocker**: stop before those mutations; commit, stash, or split unrelated work first. Preserve any bucket handoff artifacts already produced and list the paths that blocked progress.
- Do **not** pass `gald3r_worktree.ps1 -AllowDirty` for `g-go*`, `g-go-code*`, `g-go-review*`, or `--swarm` flows unless every dirty path is owned exclusively by the active task/bug scope and a `## Status History` row documents that override.

## Member touch-set clean gate (v1 — `workspace_repos`)

The orchestration git root is **always** in the clean gate's touch set. When the active task or bug declares **`workspace_repos:`** naming one or more manifest `repository.id` values, extend the **Clean Controller Gate** and **Pre-Reconciliation Clean Gate** to each **additional** repository root resolved from those IDs (blast radius follows declared cross-repo scope).

- If `.gald3r/linking/workspace_manifest.yaml` exists, map each listed ID (deduplicated) to `repositories[?].local_path`. For each path that exists on disk, resolve the git root with `git -C "<path>" rev-parse --show-toplevel` (PowerShell quoting as needed). Run `git status --short` at that root. Apply the same **explicit coordinator staging allowlist** rule per root: unrelated dirty paths are **blockers** for claims, worktrees, coordinator shared writes, and checkpoint/review-result commits until committed, stashed, split, or documented per-root in the owning task or bug `## Status History` when policy permits the same `-AllowDirty` discipline as the orchestration root.
- Skip member IDs whose `local_path` is missing while `lifecycle_status` is a planned/bootstrap gap (report per `g-skl-workspace`); those do **not** expand the touch set until paths exist.
- If the manifest is missing while `workspace_repos` is non-empty, or a listed ID is unknown under `repositories:`, treat that as a **blocker** for coordinator writes that depend on workspace routing until the manifest or frontmatter is repaired (single-repo-only work queued to the orchestration root alone may still run if `workspace_repos` lists only the owner id and resolves).

## Touch-set expansion (v2 — optional blast-radius signals)

Union the following extra repository roots into the touch set (same `git status --short` + allowlist rules as v1), **in addition to** the orchestration root and any `workspace_repos` members:

1. **`extended_touch_repos:`** — optional task/bug YAML list of additional `repository.id` values present in the workspace manifest (identical resolution rules as v1). Use when planners know the operation spans repos beyond `workspace_repos`.
2. **`touch_repos:` (swarm handoff)** — In `--swarm` runs, when bucket work edits roots not already covered by `workspace_repos` + `extended_touch_repos:`, bucket summaries and the coordinator reconciliation block MUST list those ids under `touch_repos:` so the union is gated before shared writes.
3. **Subsystem `locations:` absolute paths** — When the active item declares **`subsystems:`**, read each `.gald3r/subsystems/{name}.md` frontmatter **`locations:`** (all nested list items and string values). For every value that matches a host **absolute** path (`^[A-Za-z]:[/\\]` on Windows, or POSIX `/` rooted at `/` for non-Windows), if that path exists, resolve `git -C <dir> rev-parse --show-toplevel` using the path's directory when the path is a file. Each distinct git root **other than** the orchestration root joins the touch set. Pure relative entries (`.gald3r/...`, `skills/...`) do not expand the set. **Non-goal:** never require every manifest member to be clean for every `g-go` run.

## Pre-Reconciliation Clean Gate (`--swarm`)

Immediately **before** the coordinator applies bucket handoffs to the primary checkout, updates shared `.gald3r` indexes, touches `CHANGELOG.md`, or creates checkpoint / review-result commits, **re-run** `git status --short` on the **orchestration root and every other repository root in the computed touch set** (orchestration + v1 `workspace_repos` members + v2 expansions). If unrelated dirty paths appeared during parallel bucket work in **any** of those roots, **fail closed**: do not write shared ledgers or docs; keep patches, artifacts, and evidence; report **per-root** blockers using the same narrow non-commit reasons as the Review Result Commit gate.

The orchestration root may also be passed through the **Gald3r Housekeeping Commit Gate (post-write mode)** between major phases (after task/bug status writes, after review-result writes, after sent_orders ledger updates, after safe report/log outputs). In post-write mode, when the dirty set is exclusively safe controller `.gald3r/` coordination, the coordinator creates a focused `chore(gald3r): commit g-go coordination state` commit and continues; otherwise the standard fail-closed behavior above applies.

## Swarm Reconciliation Gate

In `g-go --swarm`, `g-go-code --swarm`, and `g-go-review --swarm`, bucket agents are handoff producers. They return patch bundles, generated artifacts, evidence, changed-file inventories, and proposed Status History rows. When v2 applies, handoffs and coordinator summaries MUST include `touch_repos:` listing any additional manifest `repository.id` values whose git roots were edited whenever that set is not already covered by the claimed task's `workspace_repos` + `extended_touch_repos:`. Bucket agents MUST NOT directly write shared `.gald3r` status/index files, `CHANGELOG.md`, generated Copilot prompts, parity output, final staging, or commits. The coordinator performs all shared writes in one final pass after deterministic reconciliation **only after** the Pre-Reconciliation Clean Gate passes.

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
