---
name: g-skl-tasks
maturity: production
description: Own and manage all task data — TASKS.md index, tasks/ individual files, status transitions, sync validation, complexity scoring, and sprint planning. Single source of truth for everything task-related.
token_budget: low
subsystem_memberships: [TASK_MANAGEMENT]
---
# g-tasks

**Files Owned**: `.gald3r/TASKS.md`, `.gald3r/tasks/**/*.md` (status subfolders), `.gald3r/archive/archive_tasks_*.md`, `.gald3r/archive/tasks/**`

**Status Subfolder Layout** (T1025):
| Subfolder | Status values |
|---|---|
| `tasks/open/` | `pending`, `ready` |
| `tasks/in-progress/` | `in-progress`, `speccing`, `verification-in-progress` |
| `tasks/awaiting-verification/` | `awaiting-verification` |
| `tasks/completed/YYYY/MM/DD/` | `completed`, `verified` (partitioned by `completed_date`) |
| `tasks/paused/` | `paused` |
| `tasks/cancelled/` | `cancelled` |
| `tasks/failed/` | `failed`, `resource-gated` (other terminal states) |

> **Discovery pattern**: `Get-ChildItem .gald3r/tasks -Recurse -Filter "*.md"` (NOT `tasks/*.md`)

**Activate for**: create task, update task status, archive completed tasks, sync check, complexity score, sprint plan, task dependencies, "phantom" or "orphan" issues.

---

## MCP-First Loop (optional acceleration — guarded until T493 passes)

When `mcp_url` is set in `.gald3r/.identity` or the `GALD3R_MCP_URL` environment variable, and the project has a gald3r MCP server running, agents **may prefer** MCP tool calls over direct file reads. This reduces prompt token load because `get_next_task` + `get_task_context` deliver ~60 tokens vs. reading the full TASKS.md index.

**Six-step MCP-first task loop:**
```python
from src.gald3r_integration.ops import make_adapter, AdapterConfig
from pathlib import Path

cfg = AdapterConfig(gald3r_root=Path("."), mcp_url="http://localhost:8092")
adapter = make_adapter(cfg)         # McpAdapter if mcp_url set; else LocalFileAdapter

task   = await adapter.get_next_task()          # replaces reading TASKS.md
ctx    = await adapter.get_task_context(task.task_id)  # replaces reading task file
ok     = await adapter.claim_task(task.task_id, agent_id="agent-001", ttl_hours=2)
# … implement …
done   = await adapter.complete_task(task.task_id, summary="Done")
# or: await adapter.fail_task(task.task_id, reason="…")
```

**MCP tool → file operation mapping:**

| File Operation | MCP Tool |
|---|---|
| Read TASKS.md + task file | `get_next_task` + `get_task_context` |
| Claim (write in-progress YAML) | `claim_task` |
| Complete (write awaiting-verification) | `complete_task` |
| Fail (write failed) | `fail_task` |
| Create task file + TASKS.md row | `create_task` |
| Report bug | `report_bug` |
| Capture idea | `capture_idea` |

**Fallback (always required):** When MCP is not configured, unavailable, or returns `Unavailable`, use the direct file operations documented in the sections below. No skill or command should require MCP; file-first workflows must remain fully functional.

**Gate:** Until T493 passes the compatibility matrix and go/no-go gate, do NOT treat MCP as the normal/default path. Use the wording "prefer when configured and enabled" — not "use by default" or "require".

---

## Workspace Routing Metadata (T175)

Optional task frontmatter fields for Workspace-Control Mode:

```yaml
workspace_repos:
  - <gald3r_source>
workspace_touch_policy: source_only
```

- When `.gald3r/linking/workspace_manifest.yaml` exists, validate `workspace_repos` against manifest `repositories[].id`; unknown repo IDs are invalid.
- Omit `workspace_repos` for current-repository-only work. Existing tasks do not require migration and default to the manifest owner repository.
- Validate `workspace_touch_policy` against manifest `routing_policy.workspace_touch_policy_values` (`source_only`, `generated_output`, `multi_repo`, `docs_only` in the bootstrap manifest).
- If omitted, `workspace_touch_policy` defaults to normal current-repo source work. Any task that names a controlled member repo must set it explicitly.
- `workspace_repos` is an allow-list for inspection/modification scope, not write permission; actual writes must also satisfy task acceptance criteria, `g-skl-workspace` ENFORCE_SCOPE, and each repository's manifest `allowed_write_policy`.
- Member repo writes require explicit member IDs, a compatible touch policy, task text authorizing member writes or generated output, reviewed member git status, and manifest write permission or a task-specific override. During bootstrap, planned member repos with `write_allowed: false` are blocked.
- Widening a task from current-repo-only to member repos, or changing policy to `generated_output`/`multi_repo`, requires a Status History note or equivalent explicit instruction explaining the scope change.
- `TASKS.md` should omit these fields for current-repo-only tasks. For workspace-scoped tasks, add at most a short suffix such as `workspace: <gald3r_source>+<template_full>; policy: generated_output`; the task file remains the source of truth.
- These fields complement `cross_project_ref`: workspace routing controls filesystem scope; `cross_project_ref` tracks PCAC orders, dependencies, and shared logical work.

---

## Operation: CREATE TASK

> **During an active agent run (T585 inbox-during-run):** do **not** hand-pick the next id and
> write `tasks/open/` directly. When `.gald3r/logs/ggo_run_state.json` is `active: true` (or
> `GALD3R_AGENT_RUN=1`), drop the new-task draft (id-less, uuid-suffixed) into `tasks/inbox/`
> instead — the hot-inbox **intake** is the single ID-assigning authority and assigns the id
> atomically at the next iteration boundary, so concurrent agents never collide on the next id.
> The numbered steps below apply unchanged when idle (no run).


1. **Determine next ID**: read `TASKS.md`, find highest task ID across ALL sections → next = highest + 1

2. **Score complexity** (1-10+):
   ```
   Estimated effort > 2-3 days          +4
   Affects multiple subsystems           +3
   Changes across unrelated modules      +3
   Requirements unclear/uncertain        +2
   Multiple distinct verifiable outcomes +2
   Blocks many subsequent tasks          +2
   Long acceptance criteria              +1
   ```
   Score ≥7: STOP — expand to sub-tasks first (see EXPAND below)

   **EARS requirements gate**: If score ≥5 OR the task has ambiguous/prose acceptance criteria, add `## Requirements (EARS Format)` section to the task file (between `## Objective` and `## Acceptance Criteria`). EARS patterns:
   ```
   Ubiquitous:   The system SHALL <action>
   Event-driven: WHEN <trigger> THE system SHALL <action>
   Conditional:  IF <condition> THE system SHALL <action>
   State-driven: WHILE <state> THE system SHALL <action>
   Optional:     WHERE <feature> IS included THE system SHALL <action>
   ```
   Skip the EARS section for simple/low-complexity tasks (score <5 with clear ACs).

3. **Create task file** at the correct status subfolder (T1025):
   - New tasks start as `pending` → `tasks/open/taskNNN_descriptive_name.md`
   - PCAC-derived critical tasks start as `in-progress` if a claim fires immediately → `tasks/in-progress/`
   - File naming: `task{id:03d}_{slug}.md` (slug = title lowercased, spaces→underscores, max 50 chars)

   **Path formula**:
   ```powershell
   $subfolder = switch ($status) {
       "pending"                  { "open" }
       "ready"                    { "open" }
       "in-progress"              { "in-progress" }
       "speccing"                 { "in-progress" }
       "verification-in-progress" { "in-progress" }
       "awaiting-verification"    { "awaiting-verification" }
       "completed"                { "completed/$($completedDate.Substring(0,4))/$($completedDate.Substring(5,2))/$($completedDate.Substring(8,2))" }
       "verified"                 { "completed/$($completedDate.Substring(0,4))/$($completedDate.Substring(5,2))/$($completedDate.Substring(8,2))" }
       "paused"                   { "paused" }
       "cancelled"                { "cancelled" }
       default                    { "done" }
   }
   $taskPath = ".gald3r/tasks/$subfolder/task{0:D3}_{1}.md" -f $id, $slug
   ```

   **PCAC-derived priority floor (T166)** — applies BEFORE the task file is written:
   - If the caller passes a `pcac_source: { type, source_project, inbox_ref }` block (callers: `g-skl-pcac-read` accept-and-spawn, `g-skl-pcac-order` receiving-side, `g-skl-pcac-ask` receiving-side, conflict resolution flow):
     - Priority floor = `high` by default
     - Priority floor = `critical` when `type: conflict` OR the source PCAC item carried an explicit urgency flag (e.g., `urgent: true`)
     - When `priority: critical`, force `requires_verification: true` (cross-project critical work cannot skip verification)
     - Write the `pcac_source:` block verbatim into the task frontmatter (audit trail — never strip on later status changes)
     - In TASKS.md, render the row with a `[PCAC]` prefix: `- [PCAC][📋] **Task NNN**: ...`. The prefix is render-only, regenerated from frontmatter on TASKS.md regen — never hand-edit.
     - Humans MAY manually downgrade priority after creation; agents MUST NOT auto-downgrade.
   - "PCAC-derived" is detected by the presence of `pcac_source:` in the create-task call payload — not by inferring from titles. Bare `g-task-add` calls without this block remain at the user's specified priority (default medium).

   **Anti-pattern guard (T167)** — reject tasks whose title or objective is purely:
   - Pattern `/^Send (PCAC|order|broadcast|notify|ask|sync) to/i`
   - Pattern `/await.*responses?.*(child|children|peer|sibling)/i`
   - Pattern `/^PCAC\s+(send|broadcast|notify|order|ask)/i`

   With error: `❌ PCAC sends are immediate operations and outbound state lives on the .gald3r/linking/sent_orders/ ledger — no local task should mirror this. Use the appropriate g-skl-pcac-* skill directly.` This guard runs before the task file is written and before any TASKS.md write.

   **Cross-project dependency prompt** (interactive, before writing the file):
   - Ask: `"Does this task depend on a cross-project order? [order_id or 'skip']"`
   - If user supplies an `order_id` (e.g., `ord-abc123`):
     - Read `.gald3r/linking/sent_orders/` and locate the matching record
     - If found: capture `sent_to` (project), `remote_task_title`, current `status`, current date as `last_synced` — populate the `cross_project_ref:` field below
     - Also append this new task's ID to that order record's `local_depends:` array
     - If not found: warn `"⚠️ No matching order in linking/sent_orders/ — proceeding without cross_project_ref"` and continue
   - If user says `skip` (or anything not matching `ord-*`): omit the `cross_project_ref:` field entirely

   **Workspace routing prompt** (optional, before writing the file):
   - Ask only when the task may inspect or modify workspace members: `Which workspace repos may this task touch? [comma list or 'current']`
   - If `.gald3r/linking/workspace_manifest.yaml` exists, parse it with `g-skl-workspace` PARSE_MANIFEST and validate repo IDs against `repositories[].id`
   - If the answer is `current`, omit `workspace_repos` and `workspace_touch_policy`; omitted metadata means current/owner repository only
   - If any controlled member repo is listed, require `workspace_touch_policy` from manifest `routing_policy.workspace_touch_policy_values` and record why member scope is needed in the task body or Status History
   - Reject or clearly flag unknown repo IDs and member writes that the manifest `allowed_write_policy` does not allow

```yaml
---
id: NNN
title: 'Task Title'
type: feature | bug_fix | refactor | documentation
status: pending
priority: critical | high | medium | low
prd: null
subsystems: [component1, component2]
project_context: 'Why this task matters to project goals'
dependencies: []
blast_radius: low | medium | high
requires_verification: false
requires_verified_dependencies: false # optional strict gate; true blocks rolling-pipeline coding until dependencies are [✅]
# Optional Definition-of-Done gate (T1168) — per-task opt-in.
# When `true`: g-go-code Step b3.5 runs a per-criterion cheap-model PASS/FAIL/UNSURE eval
#   against every `- [ ]` row in `## Acceptance Criteria` before marking `[🔍]`. Any FAIL blocks
#   the [🔍] transition; UNSURE surfaces to the coordinator with evidence.
# When `false`: gate is explicitly suppressed for this task, even if AGENT_CONFIG.md sets
#   `dod_gate_enabled: always`.
# When omitted (null): gate decision falls back to AGENT_CONFIG.md `dod_gate_enabled`
#   (default `auto` — runs only when `requires_verification: true`).
# Gate verdicts are appended to `## Status History` with format
#   `dod_gate: PASS|FAIL|UNSURE|SKIPPED — {N PASS / M FAIL / K UNSURE | reason}`.
requires_dod_gate: null
ai_safe: true
release_id: null              # optional: release ID this task is scheduled for (e.g. 3)
created_date: 'YYYY-MM-DD'
completed_date: ''
# Written by g-go-code at [🔍] transition — read by g-go-review for branch pre-flight (BUG-095 fix):
implementation_branch: ''   # git branch name where implementation was committed
implementation_sha: ''       # full 40-char git commit SHA of the implementation checkpoint
# Optional model-tier preference (T1166) — overrides session --mode for this task only.
# Accepted values: haiku | sonnet | opus | fast | standard
#   haiku   = haiku-class (same tier as --mode fast)
#   sonnet  = sonnet-class (same tier as --mode standard)
#   opus    = opus-class (no --mode equivalent — task-only escalation)
#   fast    = alias for haiku
#   standard = alias for sonnet
# When omitted, the task inherits the session's --mode flag (or IDE default if no flag).
# When present, agents log the resolved mode in the claim's Status History row as
# `mode=<tier>` (e.g. `mode=opus — Claimed for implementation`).
preferred_model: null
# Optional retry budget (T1100). Integer; when FAIL cycles reach it, g-go transitions the
# task to [❌] instead of escalating to [🚨]. Omitted = default ([🚨] at >=3 FAIL cycles).
# See "Durability Patterns (Hermes Tenacity)" for semantics.
max_retries: null
# Optional workspace-control routing; omit for current-repo-only work:
workspace_repos:
  - <gald3r_source>
workspace_touch_policy: source_only
# Optional — only present when this task gates on a cross-project order:
cross_project_ref:
  - order_id: "ord-abc123"
    project: "child_project_id"
    remote_task_title: "Implement JWT auth endpoint"
    status: in-progress        # cached from last sync; updated by g-skl-pcac-read
    last_synced: "YYYY-MM-DD"
# Optional — only present when this task was spawned from an inbound PCAC item (T166):
pcac_source:
  type: order                  # order | ask | broadcast | sync | conflict
  source_project: "child_or_parent_project_id"
  inbox_ref: "REQ-123"         # cross-link to the originating INBOX entry
# Optional — GitHub Integration Bundle fields (T1285); null when github_integration disabled:
project_type_scope: null       # scope this task to a project type; default software_development
integration_scope: null        # e.g. github, youtube — which integration bundle owns this task
issue_ref: null                # GitHub issue number, e.g. "#1234"; written by g-issue-open
pr_url: null                   # full GitHub PR URL; written by g-pr-open
pr_status: null                # null | draft | ready | merged | closed; updated by g-pr-* commands
---

# Task NNN: [Title]

## Objective
[Clear, actionable goal — done when this is complete]

## Requirements (EARS Format)
<!-- Optional. Use for complex tasks where ambiguous ACs cause rework. Skip for simple tasks. -->
<!-- EARS patterns (Easy Approach to Requirements Syntax):
     Ubiquitous:   The system SHALL <action>
     Event-driven: WHEN <trigger> THE system SHALL <action>
     Conditional:  IF <condition> THE system SHALL <action>
     State-driven: WHILE <state> THE system SHALL <action>
     Optional:     WHERE <feature> IS included THE system SHALL <action>
-->

<!-- Example (replace with real requirements or delete section entirely):
- WHEN a bug is reported with severity: high THE system SHALL create a fix task automatically
- IF the --no-task flag is passed THE system SHALL skip task creation regardless of severity
- WHILE the task is in awaiting-verification status THE system SHALL prevent direct edits to status
- The system SHALL generate sequential task IDs with no gaps
-->

## Acceptance Criteria
- [ ] [Specific measurable outcome 1]
- [ ] [Specific measurable outcome 2]

## Implementation Notes
[Technical approach, constraints, dependencies]

## Verification
- [ ] No lint errors
- [ ] Acceptance criteria tested
- [ ] Docs updated if needed

## Status History

| Timestamp | From | To | Message |
|-----------|------|----|---------|
| YYYY-MM-DD | — | pending | Task created |

## Handoff Report
<!-- Filled by the implementing agent before marking [🔍] awaiting-verification. -->
<!-- Gives g-go-review the context it needs without reading the full session history. -->

**Files Changed:**
<!-- List every file created, modified, or deleted. One path per line. -->

**Commands Run:**
<!-- List key commands with their exit codes. e.g. `uv run pytest` → exit 0 -->

**Issues Discovered:**
<!-- Pre-existing bugs found, unexpected blockers, architectural surprises. -->
<!-- Log any pre-existing bugs in BUGS.md using g-skl-bugs if significant. -->

**Left Undone (TODOs/Stubs):**
<!-- Anything deferred, stubbed, or explicitly out of scope for this task. -->
<!-- Reference TODO[TASK-NNN→TASK-YYY] annotations in code if applicable. -->

**Procedure Compliance:**
<!-- Yes / Partial / No — did the implementation follow the g-go-code flow? -->
<!-- Note any deviations (worktree skipped, clean-gate bypassed, etc.) -->

## Agent Notes
<!-- Optional. Append-only cross-session handoff notes. Do not edit prior entries. -->
<!-- Format: [AGENT:{platform}-{role}] [ISO-8601 timestamp] Note content here  -->
```

4. **Subsystem guard** (subsystem integrity check — do before TASKS.md):
   - For each name in the task's `subsystems:` field:
     - Read `.gald3r/SUBSYSTEMS.md` — is the name listed?
     - **If NOT listed**: create a stub spec at `.gald3r/subsystems/{name}.md` using the CREATE SUBSYSTEM SPEC template from `g-skl-subsystems`, set `status: planned`. Add a `planned` entry row to SUBSYSTEMS.md index. This keeps the registry in sync from the moment the task is specced.
     - **If listed as `planned`**: no action — it's already tracked.
     - **If listed as `active`**: no action — read its spec before modifying.
   - ⚠️ Never leave a task referencing a subsystem that has no SUBSYSTEMS.md entry.

5. **Add to TASKS.md** (atomic — same response):
   - Find the subsystem section (or create one)
   - Derive tier badge from `subsystems:` list:
     - For each name in `subsystems:`, read `.gald3r/subsystems/{name}.md` frontmatter `min_tier:` field
     - Badge = highest tier found: `slim` < `full` < `adv`
     - If no subsystems or no specs have `min_tier:` → default to `[slim]`
     - If `.gald3r/release_profiles/` exists, use the configured tier names from profile `name:` fields
   - Add: `- [📋] **Task NNN**: Title `[{tier_badge}]` — brief acceptance summary`
   - If tier is `[slim]`, the badge may be omitted to reduce noise (display preference)

6. **Confirm**:
   ```
   ✅ Task NNN created
   File: .gald3r/tasks/open/taskNNN_name.md
   TASKS.md: [📋] added under Subsystem: {name}
   ```

---

## Operation: SPEC AUTHORING FLOW (T164)

`[📝]` is an active speccing claim. It prevents multiple agents from creating or rewriting the same task spec at the same time.

### CLAIM-FOR-SPEC

Use this before turning a bare `[ ]` task row into a task file, or before materially rewriting an incomplete task spec.

1. Read `TASKS.md` and any existing task file (search `.gald3r/tasks/**/*taskNNN_*.md` across subfolders — open/, in-progress/, awaiting-verification/, completed/).
2. If the task is already `[📝]` / `status: speccing` with a future `spec_claim_expires_at`, skip it and report the current `spec_owner`.
3. If the `[📝]` claim is expired or missing `spec_claim_expires_at`, take it over and append a Status History row naming the previous `spec_owner`.
4. Atomically set the task row and YAML to `[📝]` / `status: speccing`. If no task file exists yet, create it immediately with the standard task template and `status: speccing`.
5. Add speccing claim metadata:
   ```yaml
   spec_owner: "{platform_or_agent_slug}"
   spec_claimed_at: "{ISO-8601 timestamp}"
   spec_claim_expires_at: "{ISO-8601 timestamp}"  # default 60 minutes
   ```
6. Append Status History: `[ ] -> [📝]` or `pending -> speccing`.

### WRITE-SPEC

While a task is `[📝]`:

1. Write or refine Objective, Acceptance Criteria, Implementation Notes, Verification, dependencies, subsystem list, routing metadata, and risk notes.
2. Keep the spec implementation-ready: no placeholders, no ambiguous ACs, and no missing subsystem references.
3. Extend `spec_claim_expires_at` with a Status History row if spec work legitimately needs more than the default TTL.
4. Other agents must not edit the same task spec while the claim is live.

### PROMOTE-SPEC

When the spec is ready for implementation:

1. Validate that the task file has objective, ACs, subsystem metadata, dependencies, and Status History.
2. Change YAML `status: pending` and `TASKS.md` `[📝] -> [📋]`.
3. Clear or leave historical speccing metadata as audit data; do not use a live future `spec_claim_expires_at` after promotion.
4. Append Status History: `[📝] -> [📋]` with a summary of what was specified.

If speccing fails or the task is cancelled, move `[📝] -> [❌]` and append a Status History row explaining why.

---

## Operation: UPDATE STATUS

**Status transitions**:
```
[ ] → [📝] → [📋] → [🔄] → [🔍] → [✅]
       ↓       ↓       ↓       ↓
      [❌]    [❌]    [⏸️]    [❌] (verification failed → reset to [📋])
                      [🚫]
```

1. **Read both**: task file YAML (search `.gald3r/tasks/**/*taskNNN_*.md` across open/, in-progress/, awaiting-verification/, completed/ subfolders) and TASKS.md indicator — fix mismatch first (file is source of truth)

   **Archive lookup guard (T204)**:
   - If no active task file exists in any subfolder, search `.gald3r/archive/archive_tasks_*.md` for `Task NNN`.
   - If found, read the archived file path from the archive index.
   - Archived terminal tasks are read-only by default. Refuse status mutations with: `Task NNN is archived at {path}; restore/unarchive is required before status changes.`
   - Do not recreate an archived task in `.gald3r/tasks/` unless a future explicit restore operation exists and the user requested it.

2. **Apply transition**:

| Action | File YAML | TASKS.md |
|---|---|---|
| Claim for speccing | `status: speccing` | `[📝]` |
| Promote spec | `status: pending` | `[📋]` |
| Start working | `status: in-progress` | `[🔄]` |
| Submit for verification | `status: awaiting-verification` | `[🔍]` |
| Mark complete (verifier) | `status: completed` | `[✅]` |
| Pause | `status: paused` | `[⏸️]` |
| Cancel | `status: cancelled` | `[🚫]` |
| Fail | `status: failed` | `[❌]` |

2a0. **Alignment Check (paused → pending unpause)**: When `from_status = paused` AND `to_status = pending`, run the ALIGNMENT CHECK sub-operation (see below) BEFORE writing the status change. If the check surfaces a prompt, block the status write until the user responds A/B/C.

2a1. **Workspace scope update check**: When updating `workspace_repos` or `workspace_touch_policy`, parse `.gald3r/linking/workspace_manifest.yaml` if present. Unknown repository IDs or touch policies are blocking findings. Widening from omitted/current-only to controlled members, adding any member repo, or changing policy to `generated_output`/`multi_repo` requires a Status History row or explicit instruction explaining the widened scope before writing the update.

2a. **Before → `[🔍]` (AC gate)**: Walk every `- [ ]` acceptance criterion in the task file.
   - Each criterion confirmed met in actual files/code? → proceed to mark `[🔍]`
   - Any unmet → **do not mark `[🔍]`**; resolve the gap or log as a Blocker
   - Partial work is not `[🔍]`-eligible; task stays `[🔄]` until all ACs pass
   - **Stub/TODO scan**: search files modified for this task for bare stubs without `[TASK-X→TASK-Y]` annotation (`# TODO`, `pass`, `raise NotImplementedError`, etc.) — each unannotated stub is an unmet criterion; annotate per `g-rl-34` before marking `[🔍]`
   - **Bug-discovery gate**: any pre-existing bug encountered must have a `BUG[BUG-{id}]` comment and a `.gald3r/bugs/` entry before `[🔍]`; bugs introduced by this task must be fixed inline (see `g-rl-35`)
   - **Workspace routing gate**: run `g-skl-workspace` ENFORCE_SCOPE against modified paths and task frontmatter; omitted metadata is current-repo-only, unknown manifest repo IDs block, docs-only tasks must remain documentation/metadata-only, generated-output tasks must identify canonical source, multi-repo tasks must list every touched workspace repo, and member repo writes require explicit authorization plus manifest write permission
   - **Status History append** (REQUIRED before `[🔍]`): append a row to `## Status History` at the bottom of the task file:
     ```
     | YYYY-MM-DD | {previous_status} | awaiting-verification | Implementation complete; {brief summary of what was done} |
     ```

2b. **Before → `[✅]` (docs + CHANGELOG check)**: After all ACs verified, write a CHANGELOG entry:

   **Step 1 — Determine category:**
   | Category | When |
   |---|---|
   | `### Added` | New skill, command, agent, hook, rule, subsystem, feature |
   | `### Changed` | Existing behavior changed, renamed, restructured |
   | `### Fixed` | Bug fix (use g-skl-bugs FIX instead for formal bugs) |
   | `### Removed` | Deprecated or deleted capability |

   **Step 2 — Decide if entry is needed:**
   - **YES** (needs entry): task adds/removes/changes user-facing behavior — skills, commands, agents, hooks, rules, conventions visible to developers using gald3r
   - **NO** (skip): purely internal refactor, `.gald3r/` housekeeping, task file updates only, private implementation changes with no developer-visible surface change

   **Step 3 — Write the entry (if YES):**
   Ask the user: *"CHANGELOG entry for this task? Suggest: '- {one-line user-facing description}' under ### {category}. Confirm or edit:"*
   Then append the confirmed entry to `CHANGELOG.md` under `## [Unreleased]` → `### {category}`:
   ```markdown
   ### Added
   - Brief past-tense description of what developers now have access to
   ```
   Rules:
   - One line. Past tense. User-facing language (not implementation details).
   - No internal task IDs in the entry text.
   - Append under the correct `###` subsection; create the subsection if missing.

   **Step 4 — README update:**
   - If the task adds/renames something documented in `README.md` (command table, skills list, feature count), update the relevant section.
   - See `g-rl-26-readme-changelog.mdc` for full qualifying criteria.

   **Reference**: `g-skl-ship` CHANGELOG-ENTRY operation for the full entry format and file-write steps.

2c. **When returning to `[📋]` / `pending` after a FAIL (g-go-review or agent rejection)**:
   - **Status History append is REQUIRED** — message must name the specific failing ACs:
     ```
     | YYYY-MM-DD | awaiting-verification | pending | FAIL: {AC-NNN, AC-NNN} not met — {brief reason} |
     ```
   - Message must not be empty; "FAIL" alone is not acceptable
   - **🚨 STUCK LOOP CHECK** — before writing `[📋]`, count `FAIL:` rows in the Status History:
     ```
     Count all rows where the Message column contains "FAIL:"
     If count ≥ 3 → mark [🚨] (requires-user-attention) instead of [📋]
     ```
     When marking `[🚨]`, append a `## [🚨] Requires User Attention` block to the task file (see template below) and log in the session summary. **Agents must NEVER autonomously reset `[🚨]` back to `[📋]` — only a human can do this.**

3. **For in-progress** — also set:
```yaml
claimed_by: "{agent_id}"
claimed_at: "YYYY-MM-DDTHH:MM:SSZ"
claim_ttl_minutes: {estimated * 1.5}
claim_expires_at: "YYYY-MM-DDTHH:MM:SSZ"
```

3a. **Optional worktree claim metadata (T170)**:
When a task is claimed from an isolated gald3r-owned worktree, also set:
```yaml
worktree_path: "{absolute_path_to_worktree}"
worktree_branch: "gald3r/{task_id}/{role}/{repo_slug}/{owner}-{suffix}"
worktree_created_at: "YYYY-MM-DDTHH:MM:SSZ"
worktree_owner: "{agent_id_or_platform_slug}"
```

- Worktree metadata is optional for legacy/direct-root work and required only when a workflow actually creates or reuses a worktree.
- `worktree_path` must resolve outside the active repository checkout; nested worktrees inside the primary working tree are invalid.
- Worktrees must be created/reported/removed through `scripts/gald3r_worktree.py` so cleanup can prove ownership with `.gald3r-worktree.json`.
- Stale cleanup is report-only by default and may remove only worktrees with gald3r ownership metadata plus explicit apply confirmation.

4. **For completed** — also set `completed_date: "YYYY-MM-DD"` and update subsystem Activity Logs (see g-subsystems)

   **Release guard**: Before marking any task `[🔄]` (in-progress):
   - If the task has a `release_id:` field that is not null:
     - Read `.gald3r/releases/release{NNN}_*.md` for that release ID
     - If release `status: released` → warn: `⚠️ Task {id} is assigned to already-released release {name}. Proceed? [y/n]`
     - If release not found → warn: `⚠️ release_id: {value} not found in .gald3r/releases/. Proceeding without release guard.`
   - If `release_id: null` or absent → no guard needed

   **Broadcast completion ping** (if applicable):
   If the task has `delegation_type: broadcast` and `task_source` is set in its YAML frontmatter:
   - Prompt: "This task was received as a broadcast from [task_source]. Notify the source project of completion? [y/n] (default: y)"
   - If yes: invoke `g-skl-pcac-notify` with routing `--project [task_source_path]`, subject "Broadcast task completed: [title]", subtype `broadcast_completion`; include original task title and completion date in the detail
   - If no or source path unknown: skip silently — completion pings are always optional

   **Capability update check** (for [✅] completions):
   After marking a task complete, check if any subsystem in the task's `subsystems:` field maps to a capability in `.gald3r/linking/capabilities.md`:
   - Read the task's `subsystems:` list
   - Read `.gald3r/linking/capabilities.md` (if it exists)
   - If any subsystem name matches a capability `Name` column value:
     - Display: "📡 This task affected subsystem(s): [{subsystem_names}]. Check capabilities.md — should any status change?"
     - Show the current status of matching capabilities
     - Prompt: "Update capability status? [enter changes or press Enter to skip]"
     - If updated: write change to `capabilities.md` and optionally trigger `g-skl-pcac-notify --capability-update`
   - If no match or capabilities.md missing: skip silently

4d. **Lifecycle activity emit (T826, contract: T818)** — fire-and-forget POST to `example_app` `/v1/activity/emit` after the Status History row is written for these five lifecycle transitions:

   | Transition | `event_type` | When |
   |---|---|---|
   | `[ ]`/`[📋]` → `[🔄]` (claim) | `claim` | After `pending → in-progress` row |
   | Mid-task heartbeat while `[🔄]` | `in-progress` | Optional periodic ping (g-go-code idle gate) |
   | `[🔄]` → `[🔍]` (impl done) | `awaiting-verification` | After `in-progress → awaiting-verification` row |
   | `[🔍]` → `[✅]` (PASS) | `complete` | After `verification-in-progress → completed` row |
   | `[🔍]` → `[📋]`/`[🚨]` (FAIL) | `fail` | After FAIL row |

   **Wire format**:
   ```http
   POST /v1/activity/emit  Content-Type: application/json
   {
     "session_id": "<workflow-session-id>",
     "event_type": "<claim|in-progress|awaiting-verification|complete|fail>",
     "payload": { "task_id": <int>, "agent_role": "<role>", "owner": "<owner>" },
     "timestamp": <unix-epoch-seconds>
   }
   ```

   **Endpoint resolution**: read `valhalla_url` from `.gald3r/.identity` if present; else default to `http://localhost:8092`.

   **PowerShell pattern (fire-and-forget)**:
   ```powershell
   try {
     $body = @{
       session_id = $sid; event_type = $evt
       payload = @{ task_id = $tid; agent_role = $role; owner = $own }
       timestamp = [int64]([DateTimeOffset]::UtcNow.ToUnixTimeSeconds())
     } | ConvertTo-Json -Compress
     Invoke-WebRequest -Uri "$valhalla/v1/activity/emit" -Method POST -Body $body `
       -ContentType "application/json" -UseBasicParsing -TimeoutSec 2 | Out-Null
   } catch { }
   ```

   **Bash pattern (fire-and-forget)**:
   ```bash
   curl -fsS -X POST "$VALHALLA_URL/v1/activity/emit" \
     -H 'Content-Type: application/json' -d "$payload" \
     --max-time 2 >/dev/null 2>&1 || true
   ```

   **Hard contract** (per T818 §"Failure semantics"):
   - Emit failure MUST NOT block the status write or surface errors to the user.
   - Transport failures are silent at debug level only — no retries, no escalation, no bug filing.
   - If `example_app` is unreachable, the lifecycle transition still succeeds.
   - Avatar animation is a best-effort UI surface, not a correctness-critical signal.

   See `docs/20260506_152259_Cursor_T818_LIFECYCLE_BINDING_CONTRACT.md` for the full schema and verification checklist.

5. **Confirm**:
   ```
   ✅ Task NNN → {new_status}
   File YAML: updated | TASKS.md: updated | Sync: verified
   Release: {release name} (target: {date}) — {days} days away    ← if release_id is set
   ```

---

## Operation: WRITE_NOTES (T850)

Append a structured note to the task file's `## Agent Notes` section. Used for cross-session handoffs between parallel or sequential agent sessions.

**Format** (append-only — never overwrite prior entries):
```
[AGENT:{platform}-{role}] [ISO-8601 timestamp] Note content here
```

**Rules**:
- Notes are append-only. Never edit or delete existing entries.
- Notes must survive worktree cleanup — commit the task file before worktree removal.
- `g-go` coordinator reads existing Agent Notes when claiming a task and injects them into agent context.
- If `## Agent Notes` section does not yet exist, create it at the end of the task file before appending.

**Example notes**:
```
[AGENT:cursor-g-go-code] [2026-05-09T10:30:00Z] Migrated auth module from bcrypt v2.1 to v4.x. test_auth.py needs updating.
[AGENT:claude-g-go-review] [2026-05-09T11:45:00Z] Reviewed auth migration — bcrypt v4 compat confirmed. test_auth.py fixes still outstanding.
```

**PowerShell append pattern**:
```powershell
$ts   = Get-Date -Format 'yyyy-MM-ddTHH:mm:ssZ'
$line = "[AGENT:$platform-$role] [$ts] $noteText"
$raw  = Get-Content $taskFile -Raw
if ($raw -notmatch '## Agent Notes') {
    Add-Content $taskFile "`n## Agent Notes`n<!-- Append-only cross-session handoff notes -->"
}
Add-Content $taskFile $line
```

---

## Operation: ARCHIVE TASKS (T204)

**Usage**: `@g-task-archive --dry-run` or `@g-task-archive --apply`

Archives completed/failed/cancelled task history so `TASKS.md` stays an active working index instead of a giant historical ledger.

### Archive Layout

- Active index: `.gald3r/TASKS.md`
  - Keep open, speccing, ready, in-progress, awaiting-verification, verification-in-progress, paused, requires-user-attention, blocked, and recently completed tasks.
  - Do not keep the full historical backlog in this file once items are archived.
- Archive index files live directly under `.gald3r/archive/`:
  - `.gald3r/archive/archive_tasks_0000_0999.md`
  - `.gald3r/archive/archive_tasks_1000_1999.md`
  - Continue in 1000-entry buckets as needed.
- Archived task files live under bucketed subfolders:
  - `.gald3r/archive/tasks/tasks_0000_0999/`
  - `.gald3r/archive/tasks/tasks_1000_1999/`
  - Continue in 1000-file buckets as needed.
- Bucket ranges are based on archive entry ordinal, not original task ID. Tasks may complete out of order; archive placement follows the next archive slot.

### Eligibility

Archive candidates:

- `status: completed` / `[✅]`
- `status: failed` / `[❌]`
- `status: cancelled` / `[🚫]`
- Cancelled terminal tasks if represented as failed/cancelled in the task body or history

Do not archive:

- `[ ]`, `[📝]`, `[📋]`, `[🔄]`, `[🔍]`, `[🕵️]`, `[⏸️]`, `[🚨]`
- Tasks referenced by active tasks as dependencies unless the archive index records the dependency target and the active task remains resolvable.
- Recently completed tasks when the command is run without an explicit `--include-recent` flag. Default recent window: 14 days.

### Archive Index Entry

Each archived task gets one compact entry in the current archive index:

```markdown
| Archive Slot | Task | Title | Final Status | Completed/Closed | Source Project | Workspace Repos | Archived File |
|--------------|------|-------|--------------|------------------|----------------|-----------------|---------------|
| 0000 | Task 123 | Example | completed | 2026-04-25 | <gald3r_source> | <gald3r_source> | archive/tasks/tasks_0000_0999/task123_example.md |
```

### Archived Task File Metadata

When moving a task file into the archive bucket, preserve the original frontmatter and add archive provenance:

```yaml
archive:
  archived: true
  archive_slot: 0
  archive_index: ".gald3r/archive/archive_tasks_0000_0999.md"
  archived_path: ".gald3r/archive/tasks/tasks_0000_0999/task123_example.md"
  archived_at: "YYYY-MM-DD"
  source_project: "<gald3r_source>"
  original_task_id: 123
```

For imported project history, also preserve `source_project`, `source_project_id`, `source_task_id`, and `imported_from` when present.

### Dry-Run Behavior

`--dry-run` is the default. It must report:

1. Candidate count by final status.
2. Active tasks blocked from archival and why.
3. Target archive index bucket(s).
4. Target archived file bucket(s).
5. Estimated `TASKS.md` line reduction.

No files are written in dry-run mode.

### Apply Gate

`--apply` may write only when:

1. The active task explicitly authorizes archival work.
2. The dry-run plan has been shown in the same session.
3. `.gald3r/archive/`, `.gald3r/archive/tasks/`, and target buckets can be created safely.
4. Every moved task has a matching archive index entry.
5. `TASKS.md` retains an "Archive Pointers" section linking to archive index files.

Apply output must end with:

```text
Task archive applied. TASKS.md is now an active index; historical task records moved to .gald3r/archive/.
```

### Historical Lookup

When a user or workflow references a task ID that is not present in `.gald3r/TASKS.md` or `.gald3r/tasks/`, search archive indexes before reporting it missing:

1. Search `.gald3r/archive/archive_tasks_*.md` for `Task NNN`.
2. Read the matching `Archived File` path.
3. Return the archived record as historical context only.
4. Report the archive slot, archive index file, archived task file path, final status, source project, and workspace repos.

### Archived Mutation Guard

Archived task files are immutable terminal history unless a future restore/unarchive command explicitly rehydrates them. `UPDATE STATUS`, dependency rewrites, task deletion, and sync repair must not edit archived task files in place. If a workflow tries to mutate an archived task, stop and report the archive location plus the required restore/unarchive next step.

---

## Operation: ALIGNMENT CHECK (UPDATE STATUS sub-operation — unpause only)

Runs exclusively when UPDATE STATUS transitions a task from `paused` (`[⏸️]`) → `pending` (`[📋]`). Fast scan (~30 seconds). Surfaces stale references so the resumed task does not introduce drift. Never rewrites the task spec — only reports.

### 1. Gather inputs

From the task file (search `.gald3r/tasks/**/*taskNNN_*.md` across subfolders):
- `created_date` from YAML
- Most recent `paused` Status History row timestamp (if present) — use this as `paused_since`; else fall back to `created_date`
- `subsystems:` list
- Full task spec body text (for reference scanning)

### 2. Compute age and escalation

```
age_days = today - paused_since
  < 7d   → advisory mode (no prompt, note in history only)
  7–30d  → prompt user IF any stale finding
  > 30d  → always prompt user with full report (even if clean)
```

### 3. Gather "since pause" context

In order:
1. `git log --oneline --since={paused_since}` — list recent commits
2. `.gald3r/TASKS.md` — collect `[✅]` entries whose task file `subsystems:` overlaps this task's `subsystems:`
3. `.gald3r/DECISIONS.md` — collect decision entries with timestamp > `paused_since`

### 4. Scan the spec for stale references

For each reference kind:

| Reference pattern | Check |
|---|---|
| `g-skl-*` (skill name) | Folder `.cursor/skills/{name}/` exists? |
| `@g-*` or `g-*` (command name) | File `.cursor/commands/{name}.md` exists? |
| Path literals | Path still exists on disk, OR has a well-known rename (see table below) |
| Subsystem names | Appears in SUBSYSTEMS.md registry? |

A reference is **stale** when:
- Skill/command folder/file is missing, AND the well-known renames table has a mapping, OR
- Path matches the Old column of the well-known renames table, OR
- Subsystem name is not found in SUBSYSTEMS.md

### 5. Well-known renames table (inline — extend as renames happen)

| Old | New | Source |
|-----|-----|--------|
| g-skl-harvest | g-skl-res-review | T121 (2026-04-18) |
| g-skl-harvest-intake | g-skl-res-apply | T121 |
| g-skl-reverse-spec | g-skl-res-deep | T121 |
| g-skl-ingest-docs | g-skl-recon-docs | T121 |
| g-skl-ingest-url | g-skl-recon-url | T121 |
| g-skl-ingest-youtube | g-skl-recon-yt | T121 |
| `research/harvests/` | `research/recon/` | T121 intent |
| `prds/` | `features/` | T040 / T084-1 |
| `topics:` (frontmatter) | `tags:` (frontmatter) | T039 |

Agents SHOULD append new mappings here when a rename lands (keep this table canonical; no external config file).

### 6. Outcomes

**Clean case (no stale references found)**:
- Proceed with unpause silently
- Append to Status History:
  ```
  | YYYY-MM-DD | paused | pending | Unpaused; alignment check: clean |
  ```

**Advisory case (age < 7d, stale found)**:
- Proceed with unpause — do NOT block
- Append to Status History:
  ```
  | YYYY-MM-DD | paused | pending | Unpaused; alignment check advisory: {count} stale refs noted |
  ```

**Prompt case (age ≥ 7d AND stale found) OR (age > 30d always)**:
- Output the structured report (format below)
- Block the status write until user responds A/B/C
- On response:
  - `A` → route user to spec edit workflow; do NOT write the status change; leave task `[⏸️]` until user re-issues the unpause with an updated spec
  - `B` → proceed with unpause; append Status History row including the stale-ref summary
  - `C` → cancel; task stays `[⏸️]`; no Status History row written

### 7. Report format

```
⚠️ Alignment Check — Task {id}: {title}
Paused: {paused_since}  |  Age: {N} days

Stale References:
- {kind} "{old}" → now "{new}" ({rename source, e.g. T121, 2026-04-18})
- {kind} "{old}" → MISSING ({no mapping found — manual review})

Related work since pause:
- {task-id} [{status}] {title} ({date})
- {decision-id} [Decision] {decision summary}

Recommendation: {Spec refresh recommended | Proceed with caution | Cancel recommended}

Select: (A) Update spec now  (B) Proceed anyway  (C) Cancel unpause
```

### 8. Idempotency

Cache the alignment scan result keyed on `{task_id, spec_hash}` (spec_hash = hash of the task file body) within the current session to avoid re-scanning if the same task is unpaused twice without edits. Cache does not persist across sessions — first unpause of a session always scans fresh.

### 9. Acceptance criteria coverage

This sub-operation satisfies Task 150 AC-1 through AC-6. AC-7 (propagation to 10 IDE targets) and AC-8 (`g-task-upd` description update) are handled at the skill-deployment level.

---

## Operation: TIER BADGE DERIVATION

Used by CREATE TASK and STATUS display to determine the minimum gald3r tier required for a task.

### Algorithm

1. Read the task's `subsystems:` list from YAML frontmatter
2. For each subsystem name, read `.gald3r/subsystems/{name}.md`:
   - Extract `min_tier:` from YAML frontmatter
   - If spec file missing or `min_tier:` absent → treat as `slim` (default)
3. Badge = highest tier across all subsystems: `slim` < `full` < `adv`
4. If `.gald3r/release_profiles/` exists: validate badge against configured tier names (profile `name:` fields)
5. Return the badge as a display string: `[slim]`, `[full]`, or `[adv]`

### Display Format

```
- [📋] **Task 082** `[full]` Product Tier Architecture — parent task...
- [📋] **Task 007** `[slim]` PCAC topology foundation...
```

The badge is **omitted for slim** in most contexts to reduce visual noise. It appears when:
- The task is explicitly `full` or `adv`
- A release gate check is running (all tasks shown with badges)
- User invokes `@g-task-upd NNN --show-tier`

### SYNC-CHECK Behavior

SYNC-CHECK does **NOT** flag missing tier badges as errors. Badges are derived at display time — they are not stored in task YAML. This section is informational only.

---

## Operation: RESET / RESTORE TASKS.md

When a user asks to "reset TASKS.md", restore it "to default", or TASKS.md is missing/corrupt,
**never reconstruct the file from memory or training knowledge** — the canonical schema lives
in the framework template and changes between releases. Use the canonical restore path:

1. **Preferred (engine):** run the framework restore engine, which sources the pristine copy
   from `.gald3r_sys/template_verification/.gald3r/`:
   ```powershell
   uv run python .gald3r_sys/scripts/migrate_schemas.py -ProjectPath <proj> -RestoreMissing -Apply
   ```
   (omit `-Apply` to see what it would restore). This restores any missing `.gald3r/` root file,
   including `TASKS.md`, with correct `schema_version` / `gald3r_rel_version` frontmatter.
2. **Manual copy (single file):** copy `.gald3r_sys/template_verification/.gald3r/TASKS.md` to
   `.gald3r/TASKS.md`. Resolve the source script-adjacent or project-local; never hardcode a
   dev-machine path.

A reset only replaces the **index** file. If `.gald3r/tasks/**` still holds task files, run
SYNC CHECK afterward to rebuild the summary rows from the surviving task files.

---

## Operation: SYNC CHECK

Run at session start or when phantom/orphan issues suspected.

1. **Read TASKS.md** — extract all task entries with indicators
   > **TASKS.md Dual-Format Parsing (MANDATORY)** — TASKS.md entries appear in two formats.
   > You MUST match BOTH or the sync will silently miss entries.
   >
   > **Format A — Table rows (current standard, ~99% of entries):**
   > ```
   > | [🔍] | [804](tasks/awaiting-verification/task804_foo.md) | Title | type | deps |
   > ```
   > Pattern: `\|\s*\[([^\]]+)\]\s*\|\s*\[(\d+(?:-\d+)?)\]\(tasks/`
   > — Group 1 = status emoji, Group 2 = task ID
   > Note: The link path now includes the status subfolder (e.g. `tasks/open/task001_slug.md`)
   >
   > **Format B — Legacy bullet rows (<1%, historical):**
   > ```
   > - [✅] **Task 014**: Title (tasks/task014_foo.md)
   > ```
   > Pattern: `\[([^\]]+)\]\s+\*\*Task\s+(\d+(?:-\d+)?)\*\*`
   > — Group 1 = status emoji, Group 2 = task ID
   >
   > **PowerShell reference (T1025 — handles status subfolder paths):**
   > ```powershell
   > $c = [IO.File]::ReadAllText($tasksPath)
   > # Format A: links now include subfolder, e.g. (tasks/open/task001_foo.md)
   > $tableIds  = [regex]::Matches($c, '\|\s*\[([^\]]+)\]\s*\|\s*\[(\d+(?:-\d+)?)\]\(tasks/') | % { $_.Groups[2].Value }
   > $bulletIds = [regex]::Matches($c, '\[([^\]]+)\]\s+\*\*Task\s+(\d+(?:-\d+)?)\*\*')        | % { $_.Groups[2].Value }
   > $allIds    = ($tableIds + $bulletIds) | Sort-Object -Unique
   > ```
   > Whichever format is the canonical/preferred going forward: **Format A (table rows)**.
   > Do not remove Format B detection — older or migrating TASKS.md files may still use it.
2. **List all task files recursively** (T1025 status subfolders):
   ```powershell
   # PowerShell — discover across ALL status subfolders
   Get-ChildItem ".gald3r/tasks" -Recurse -Filter "task*.md" | Where-Object { $_.FullName -notmatch "\\archive\\" }
   ```
   This covers `tasks/open/`, `tasks/in-progress/`, `tasks/awaiting-verification/`, `tasks/completed/**`, `tasks/paused/`, `tasks/cancelled/`, `tasks/failed/`
3. **For each TASKS.md entry**:
   ```
   [✅][❌][⏸️][🚫] → look recursively in tasks/**
   [📝][📋][🔄][🔍][🕵️] → look recursively in tasks/**
   [ ]           → no file expected (OK)

   ✅ FOUND   = file exists in any subfolder
   ⚠️ PHANTOM = in TASKS.md but no file in any subfolder
   ⚠️ WRONG_FOLDER = file exists but in wrong subfolder for its status (flag + offer to move)
   ```
4. **For each task file** — has matching TASKS.md entry? NO → ORPHAN ⚠️
5. **Folder mismatch check** — for each found file, verify its parent subfolder matches its `status:` YAML field per the mapping table; flag mismatches as `WRONG_FOLDER` (not errors — task may be mid-transition)
5. **Status mismatch** — file is source of truth, fix TASKS.md
6. **Speccing claim validation** — for every `[📝]` / `status: speccing` task, require `spec_owner`, `spec_claimed_at`, and `spec_claim_expires_at`; missing or malformed metadata is a sync finding, and expired claims are reported as takeover-eligible rather than silently accepted
7. **Report**:
   ```
   📋 TASK SYNC
   Task 001: ✅ FOUND — pending/[📋] match
   Task 003: ⚠️ PHANTOM — in TASKS.md but no file
   Task 099: ⚠️ ORPHAN — file exists, not in TASKS.md
   Synced: 12/13 | Fixed: 0 | Needs action: 1
   ```

---

## Operation: EXPAND (complex tasks)

When complexity score ≥7:
1. Identify logical sub-goals
2. If shared module needed → sub-task 1 = extraction
3. Create sub-task files: `task{parent}-1_name.md`, `task{parent}-2_name.md`
4. Update parent task: `sub_tasks: ["42-1", "42-2"]`
5. Add sub-tasks to TASKS.md under same subsystem section

---

## Operation: INTAKE (T1573 — inbox staging zone)
Processes `.gald3r/tasks/inbox/` and `.gald3r/bugs/inbox/` — gitignored drop zones for
creating tasks/bugs during a live `g-go-go` run without triggering the Housekeeping Commit
Gate hard-block (writing to `TASKS.md`/`BUGS.md` outside the iteration allowlist causes
`mixed-dirty` classification and halts the pipeline).
**Drop zone usage:**
Place a minimal `.md` file in `.gald3r/tasks/inbox/` during a run. Title is the only required
field; all others default. The next iteration's start step ingests it automatically.
```
# .gald3r/tasks/inbox/my-idea.md
title: Fix the UTF-8 guard in regenerate_tasks_index.ps1
priority: medium
type: bug_fix
subsystems: [TASK_MANAGEMENT]
```
**How it runs:**
`custom_scripts/hot_inbox_intake.ps1` is called at the start of each `g-go-go` iteration
(before the PCAC gate, before the claim loop). It:
1. Assigns the next sequential task/bug ID
2. Writes a proper task file to `tasks/open/` with full frontmatter
3. Appends the index row to `TASKS.md` / `BUGS.md`
4. Deletes the inbox draft
5. Commits as `chore(gald3r): intake N task(s) / M bug(s) from inbox`
The intake commit is the **sole writer** of `TASKS.md` / `BUGS.md` in that step — so the
housekeeping gate classifies it as `safe-gald3r-housekeeping` and auto-commits without blocking.
**Manual invocation:**
```powershell
.\custom_scripts\hot_inbox_intake.ps1 -DryRun   # preview
.\custom_scripts\hot_inbox_intake.ps1            # apply
```
**Inbox is empty → exits 0, no commit, no output (use -Quiet).**
---
## Operation: SPRINT PLAN

1. Read all `[📋]` tasks from TASKS.md
2. Score each: priority + dependencies resolved + blast_radius + goal alignment. For rolling implementation pipelines, `[🔍]` dependencies count as implementation-satisfied unless the task declares `requires_verified_dependencies: true`; strict tasks wait for `[✅]`.
3. Output:
   ```
   ## Proposed Sprint
   1. Task 5 — DB Schema (3 SP, no blockers)
   2. Task 6 — API Layer (5 SP, needs Task 5)
   3. Task 7 — Fix lint (1 SP, independent)
   Target: 70% capacity | Grouped by subsystem
   ```

---

## Status Indicators Reference

| Indicator | File YAML | Meaning |
|---|---|---|
| `[ ]` | (no file) | Pending — file not yet created |
| `[⌛]` | `waiting` | Concept recorded; prerequisites not met — skip in g-go/g-mission; stored in `tasks/open/` |
| `[📝]` | `speccing` | Claimed for spec authoring; skip unless claim is expired |
| `[📋]` | `pending` | File created, ready to start |
| `[🔄]` | `in-progress` | Being worked on |
| `[🔍]` | `awaiting-verification` | Done, needs different-agent review |
| `[🕵️]` | `verification-in-progress` | Claimed by a verifier; skip unless claim is expired |
| `[✅]` | `completed` | Verified complete |
| `[❌]` | `failed` | Failed |
| `[⏸️]` | `paused` | Paused — resumes from `tasks/paused/`; run Alignment Check on unpause |
| `[🚫]` | `cancelled` | Cancelled — terminal; stored in `tasks/cancelled/`; archivable |
| `[🚨]` | `requires-user-attention` | Stuck ≥3 FAIL cycles — **agents must not retry; human-only resolution** |

### [⌛] Waiting Status — spec prerequisites not met

`[⌛] waiting` is for tasks where the **concept is recorded but cannot be specced or coded yet**. It sits BEFORE `[ ] pending` in the lifecycle:

```
[⌛] waiting → [ ] pending → [📝] speccing → [📋] ready → [🔄] active → [🔍] awaiting-verification → [✅] done
```

**New frontmatter fields** (all optional, only used with `status: waiting`):

```yaml
spec_task_reqs:           # Machine-checkable: list of task IDs that must be [✅] before speccing
  - 1238                  # T1238 must be completed
  - 1239
spec_reqs:                # Human-checked: string conditions that cannot be auto-evaluated
  - "Decision: cloud provider chosen"
  - "Business: free/paid tier boundaries defined"
waiting_since: '2026-05-18T22:00:00Z'  # ISO-8601; used for TTL stale detection
```

**Specable check** (`can_spec` logic):
- `spec_task_reqs` is empty OR all listed task IDs are `[✅]`
- AND `spec_reqs` is empty OR human has acknowledged them

**TTL stale detection** (fires in `g-status`, `g-go-go` startup, end of `g-go*` runs):
- If a `waiting` task's `spec_task_reqs` dependency is `[❌]` or `[⏸️]` AND `waiting_since` is >24h ago → surface: `⚠️ T1239 has been waiting Xh — dep T1238 is [⏸️] paused. Review required.`

**Promotion**: `g-task-upd --promote <id>` → `waiting` → `pending`; clears TTL; writes Status History row.
**Demotion**: `g-task-upd --demote <id> --reason "..."` → any status → `waiting`; optionally adds `spec_reqs` entries.

**g-go / g-mission skip rule**: `waiting` tasks are NEVER claimed for speccing or implementation. Treat as read-only background context.

### [📝] Speccing Claim Rules

`[📝]` prevents multiple agents from writing competing specs for the same task.

When any task-authoring workflow selects a `[ ]` task or incomplete spec:
1. Atomically change `TASKS.md` and task YAML to `[📝]` / `speccing`.
2. Add `spec_owner`, `spec_claimed_at`, and `spec_claim_expires_at` metadata.
3. Append a Status History row for `[ ] -> [📝]` / `pending -> speccing`.
4. Other agents must skip `[📝]` tasks unless `spec_claim_expires_at` is older than the current time.
5. A stale takeover must append a Status History row naming the previous `spec_owner` and new owner.
6. Finished specs move `[📝] -> [📋]`; cancelled specs move `[📝] -> [❌]`.

### Agent Liveness Heartbeat (T1058)

When `g-go-code` / `g-go` claims a `[📋]` task and moves it to `[🔄]`, write heartbeat metadata:
```yaml
agent_heartbeat: "YYYY-MM-DDTHH:MM:SSZ"       # ISO-8601 timestamp; write at claim + refresh every 5 min
agent_heartbeat_expires: "YYYY-MM-DDTHH:MM:SSZ" # ISO-8601; claim time + 10 min (override via GALD3R_HEARTBEAT_TTL_MINUTES)
```

**Stale heartbeat detection**: if `agent_heartbeat_expires` exists and is in the past:
- Log warning: `⚠️ Task NNN: heartbeat expired ({expires}); treating as abandoned`
- Allow re-claim without waiting for the full TTL
- Append a Status History row naming the previous claim and reason for takeover

**Heartbeat refresh**: `g-go-code` and `g-go` bucket agents update `agent_heartbeat` and `agent_heartbeat_expires` every 5 minutes during active implementation. Lightweight file write — not a full task status update.

**Absence = legacy behavior**: tasks without `agent_heartbeat` fields fall back to TTL-only staleness detection (unchanged).

### Durability Patterns (Hermes Tenacity — T1100)

The Hermes 0.13 "Tenacity" reliability patterns map onto features gald3r already has — only
the per-task **retry budget** is net-new. This table is the canonical mapping; do not
duplicate the referenced mechanisms.

| Hermes pattern | gald3r mechanism | Status |
|---|---|---|
| Heartbeat liveness | `agent_heartbeat` / `agent_heartbeat_expires` (T1058, above) — write at claim, refresh every 5 min, expire +10 min | **Implemented** |
| Zombie detection | Stale-heartbeat detection (above): expired `agent_heartbeat_expires` ⇒ "treating as abandoned"; TTL-only fallback for legacy tasks | **Implemented** |
| Reclaim logic | Expired heartbeat ⇒ re-claim without waiting full TTL, with a Status History takeover row | **Implemented** |
| Hallucination gate | **Definition-of-Done gate (T1168)**: g-go-code Step b3.5 runs a per-criterion PASS/FAIL/UNSURE eval against every `- [ ]` row in `## Acceptance Criteria` before `[🔍]`. Any FAIL blocks the `[🔍]` transition; UNSURE surfaces to the coordinator. This *is* the "board state must match the completion claim" check. | **Implemented** |
| Retry budget | Default: `[🚨]` requires-user-attention after **≥3 FAIL cycles** (human-only, no agent retry). Optional explicit override: `max_retries:` (below). | **Default + new field** |

**Optional `max_retries:` field (net-new).** Add to task YAML to cap retries explicitly:
```yaml
max_retries: 2   # optional; integer. Counts FAIL-cycle Status History rows for this task.
                 # When the count reaches max_retries, g-go-code/g-go-review transition the
                 # task to [❌] (terminal failure) instead of looping or escalating to [🚨].
                 # Omitted (null) = default behavior: escalate to [🚨] at >=3 FAIL cycles.
```
- A "FAIL cycle" = a Status History row whose `To` is `pending`/`open` with a `FAIL:` message.
- `max_retries: 0` means "no retry — first FAIL is terminal `[❌]`".
- The default `[🚨]`-at-3 rule still applies when `max_retries` is absent; an explicit
  `max_retries` overrides it (terminal `[❌]` rather than human-attention `[🚨]`).

**Swarm bucket handoff (g-go-swarm).** When a swarm bucket returns its handoff, the report
SHOULD include a durability line: `heartbeats=<n> retries=<n>/<max|∞> zombie=<none|reclaimed-from:agent> dod_gate=<PASS|FAIL|UNSURE|SKIPPED>`. The coordinator uses it to decide
re-queue vs. `[❌]` vs. `[🚨]` during reconciliation (it never lets a bucket write that status itself).

**Automation deferred.** Heartbeat *emission* and *automated* zombie reclaim run today inside
g-go-code/g-go bucket loops (file writes); a standalone watchdog reclaimer is tracked under
T968 (`no_agent_cron_watchdog_mode`). This section is guidance + the `max_retries` contract;
no separate enforcement script is added here.

### Mode Logging on Claim (T1166)

When `g-go-code` / `g-go` (or any swarm bucket agent) claims a task and writes the initial
Status History row, the `Message` column MUST include the resolved model tier as
`mode=<tier>`. Resolution precedence (highest wins):

1. Task YAML `preferred_model:` field (if set) → `mode=<preferred_model>` (e.g. `mode=opus`).
2. Session `--mode` flag (from `g-go` / `g-go-code` arguments) → `mode=fast` | `mode=standard` | `mode=cheap`.
3. No flag and no preference → `mode=inherit` (the host IDE's current model is unknown to the agent).

**Claim row template:**
```
| YYYY-MM-DD HH:MM | pending | in-progress | {agent} | mode=<tier> — Claimed for implementation |
```

**Implementation-complete row template (when transitioning [🔄] → [🔍]):**
```
| YYYY-MM-DD HH:MM | in-progress | awaiting-verification | {agent} | mode=<tier> — Implementation complete; {1-line summary} |
```

The `mode=<tier>` token is the audit trail. Reviewers, post-mortem analysis, and the
auto-learn extractor (`g-rl-37` / `g-go-code` Step 5a) correlate model-tier choice with
implementation quality and re-work rates. Omitting it on the claim row is a procedural
violation flagged by `g-go-review` and SYNC-CHECK.

Bucket agents in `--swarm` runs each record their own inherited mode independently — the
coordinator does not aggregate or override these per-task rows. Coordinator-owned shared
writes (TASKS.md rollups, CHANGELOG entries, parity sync) are not subject to this rule
because the coordinator does not "claim" individual tasks in the implementing sense.

### GitHub Integration Fields (T1285)

Five optional fields are added to task frontmatter when the GitHub Integration Bundle is active
(`project_type=software_development` AND `github_integration=enabled` in AGENT_CONFIG.md).
They are `null` / absent on non-software projects and on software projects with integration disabled.

| Field | Type | Written by | Values |
|---|---|---|---|
| `project_type_scope` | string or null | task creator | `software_development` (default) or other type slug |
| `integration_scope` | string or null | task creator | `github`, `youtube`, etc., or null |
| `issue_ref` | string or null | `g-issue-open` | `"#1234"` or null |
| `pr_url` | string or null | `g-pr-open` | full GitHub PR URL or null |
| `pr_status` | string or null | `g-pr-*` commands | `null \| draft \| ready \| merged \| closed` |

**Handling rules:**
- UPDATE TASK round-trips all five fields unchanged if present.
- SYNC-CHECK does not flag them as drift.
- TASKS.md regeneration ignores them (no display change).
- Database model holds three nullable columns (`issue_ref`, `pr_url`, `pr_status`); migration is a separate epic.
- Fields stay `null` until populated by their respective GitHub commands (`g-pr-open` → T1287).

### [🕵️] Verification Claim Rules

`[🕵️]` prevents multiple review agents from verifying the same task at once.

When `g-go-review` or `g-go-review --swarm` selects a `[🔍]` task:
1. Atomically change `TASKS.md` and the task YAML from `[🔍]` / `awaiting-verification` to `[🕵️]` / `verification-in-progress`.
2. Add verifier claim metadata in the task YAML:
   ```yaml
   verifier_owner: "{platform_or_agent_slug}"
   verifier_claimed_at: "{ISO-8601 timestamp}"
   verifier_claim_expires_at: "{ISO-8601 timestamp}"  # default 120 minutes
   ```
3. Append a Status History row: `awaiting-verification -> verification-in-progress`.
4. Other review agents must skip `[🕵️]` tasks unless `verifier_claim_expires_at` is older than the current time.
5. A stale takeover must append a Status History row naming the previous `verifier_owner` and new verifier.
6. PASS moves `[🕵️]` → `[✅]`; FAIL moves `[🕵️]` → `[📋]` or `[🚨]` according to the stuck-loop rule.

Review isolation metadata may be added by `g-go-review` / `g-go-review --swarm`:

```yaml
review_isolation_mode: worktree | snapshot
review_worktree_path: null
review_worktree_branch: null
review_worktree_owner: null
review_worktree_created_at: null
review_source_branch: null
review_source_commit: null
review_snapshot_path: null
review_source_dirty: false
```

- Use `worktree` when the review source is branch-addressable and the T170 helper created a `review` or `review-swarm` worktree.
- Use `snapshot` when the candidate changes exist only as uncommitted files in the current checkout or an implementation worktree.
- Snapshot mode is read-only; reviewers must not edit implementation files in the snapshot source.

### [🚨] Stuck Note Template

When triggering `[🚨]`, append this block to the task/bug file:

```markdown
## [🚨] Requires User Attention

This item has failed verification **{N} times**. Automated agents will not retry it.

**Last failure reason**: {last FAIL row message}

**Human actions available**:
- Revise acceptance criteria → add "Human reset: AC revised" to Status History → reset to `[📋]`
- Split into simpler sub-tasks → mark this `[❌]`
- Cancel → mark `[❌]` with reason
- Override as complete → mark `[✅]` with manual sign-off note
```

---

## Workflow Profiles (T1238)

Task lifecycle vocabulary is configurable. The hardcoded software-development
flow (`[ ] → [📋] → [🔄] → [🔍] → [✅]`) is one of three built-in profiles;
content-creation and research profiles ship alongside it for non-code projects.

**Profile selection precedence (highest wins):**

1. Per-task: `workflow_profile: <id>` in the task's YAML frontmatter.
2. Per-project: `workflow_profile: <id>` in `.gald3r/PROJECT.md` frontmatter.
3. Default: `software_dev` (the legacy gald3r behavior — no migration needed).

**Built-in profiles** (stored at `.gald3r/config/workflow_profiles/`):

| id | Use case | Status flow |
|---|---|---|
| `software_dev` | Code repos (default) | `waiting → pending → in-progress → awaiting-verification → done` |
| `content_creation` | Podcasts / video / marketing | `waiting → concept → scripting → in_production → in_review → rendering → published` |
| `research` | Science / academic | `waiting → hypothesis → data_collection → analysis → writing → peer_review → published` |

**Adding a custom profile**: drop a new `<id>.yaml` into
`.gald3r/config/workflow_profiles/`. The schema requires `id`, `name`,
`description`, `task_statuses[]`, `review_gate`, and `task_types[]`. Each
`task_statuses[]` entry has `id`, `symbol`, `description`, and a
`skip_in_pipeline: bool` (controls whether `g-go` / `g-mission` claim it).

**Validation behavior**: unknown status IDs in a task's frontmatter produce a
warning at session start (not a crash). `g-status` reads the active profile and
displays it in the session-context header so operators always see which
vocabulary is in effect.

**Schema version**: 1.0 (T1238). Future versions may add per-status
`requires_review_gate: bool`, `transition_rules`, and `claim_constraints` —
all backwards-compatible additions.

### Reading the active profile (T1239)

Profiles are **operational**, not just descriptive. Before any status transition,
emoji-symbol regeneration, or `--promote`/`--demote`, load the active profile
snapshot once and use it as the source of truth for valid statuses + symbols:

```powershell
# Resolves the hybrid activation chain (task frontmatter > PROJECT.md >
# .identity project_type= > freeform) and prints a JSON snapshot.
# -TaskFile lets a per-task workflow_profile: override win.
uv run python .claude/skills/g-skl-project-types/scripts/load_profile.py `
    -TaskFile .gald3r/tasks/open/task<id>_<slug>.md
```

Installed templates resolve the loader from the active IDE skill folder
(`.claude/skills/...`, `.cursor/skills/...`, etc.). When `powershell-yaml` is not
installed the loader still returns the profile id + raw YAML (`parsed: false`) —
parse `task_statuses[]` from the embedded `raw_yaml` in that case.

**Symbol regeneration (AC3 — TASKS.md emoji from profile, not hardcoded):**
when regenerating TASKS.md rows or status badges, map each task's `status:`
frontmatter value to the `symbol` of the matching `task_statuses[].id` from the
active profile. Do **not** hardcode `[📋]`/`[🔄]`/`[🔍]`/`[✅]`; for the
`software_dev` profile these resolve identically, so legacy code repos are
unchanged, but a `content_creation` project renders `[✍️]` for `scripting`,
`[🎬]` for `in_production`, etc.

**Transition validation (AC4 — `--promote`/`--demote` against the profile DAG):**
the canonical order of a transition is the **declaration order** of
`task_statuses[]` in the active profile. `--promote` advances to the next
non-terminal status in that order; `--demote` moves to the previous one.
A requested target status that is not present in the active profile's
`task_statuses[]` is rejected with
`Invalid transition: '<status>' is not in profile '<id>' (valid: <id list>)`
rather than silently written. Terminal statuses (`skip_in_pipeline: true` AND no
forward neighbour, e.g. `done`/`published`/`cancelled`) cannot be `--promote`d
further. This replaces the hardcoded `[ ] → [📋] → [🔄] → [🔍] → [✅]` ladder
with the profile-defined one while keeping `software_dev` byte-identical.

---

## Mid-Task Checkpoint Protocol (T836)

Implementing agents running under `g-go-code` or `g-go` must pause after every
**N major tool operations** (file reads, shell commands, file writes) for a brief
self-evaluation. The default is **N = 20**; override via
`.gald3r/config/AGENT_CONFIG.md` key `checkpoint_interval`.

### Trigger

After every N major operations within a single task's implementation, **before
continuing**, run the self-evaluation below.

### Self-Evaluation Questions (4 mandatory)

1. **AC alignment** — How many acceptance criteria are satisfied vs. remaining?
   Is current trajectory sufficient to meet all ACs?
2. **Scope check** — Am I within the declared `subsystems:` and `workspace_repos:`
   boundaries? Any scope creep detected?
3. **Blocking obstacles** — Anything discovered that may prevent completing this
   task? (missing files, unclear spec, external dependency, token budget)
4. **Token budget** — Rough estimate of remaining context; flag if >75% consumed
   with significant work still remaining.

### Output Formats

Healthy (no action required, continue):
```
## Mid-Task Checkpoint (operation N/20): HEALTHY
AC progress: {X}/{total} satisfied. No blockers. Continuing.
```

Needs correction (surface before continuing):
```
## Mid-Task Checkpoint (operation N/20): NEEDS_CORRECTION
⚠️ CHECKPOINT: {issue description}
AC progress: {X}/{total} satisfied. Blocker: {description}.
Correction plan: {1-2 sentences}.
```

### Status History Audit Trail

**Before continuing**, append a checkpoint row to the task's `## Status History`:
```
| YYYY-MM-DD | in-progress | in-progress | CHECKPOINT {N}: {1-line summary}. AC: {X}/{total}. Blockers: {none|description}. Continuing. |
```

### Stop vs. Continue Decision

| Result | Action |
|---|---|
| HEALTHY | Continue implementation immediately |
| NEEDS_CORRECTION with resolvable blocker | Apply correction plan, continue |
| NEEDS_CORRECTION with unresolvable blocker | Surface `⚠️ CHECKPOINT: [issue]` in next message; log as Blocked in step 6 of g-go-code |

### Rules

- Checkpoint is **mandatory** — fires every N operations, no exceptions.
- A task marked `[🔍]` that consumed ≥1 checkpoints must show checkpoint rows
  in `## Status History` before the `[🔍]` transition row.
- In `--swarm` mode, each bucket agent runs independent checkpoints; the
  coordinator does not aggregate them.

---

## Cross-Project Split Check (T119)

When **CREATE TASK** is invoked (step 3, before writing the file), perform a topology split check:

### Split Check Algorithm

```
1. Load topology (if available):
   - Read .gald3r/linking/link_topology.md → get children[], parent, siblings[]
   - For each peer: read .gald3r/linking/peers/{slug}_capabilities.md (if exists)

2. Extract domain tags from task title + description:
   - Match against capability domain keywords (e.g. "frontend", "backend", "api", 
     "database", "mobile", "ML", "docker", "UI", "auth", "real-time", "infra")

3. For each domain tag: check if a peer owns it (capability name match)

4. If ANY domain tag belongs to a peer that is NOT the current project:
   → Surface split suggestion (see format below)

5. If ANY domain tag has NO owner in topology at all:
   → Surface spawn suggestion
```

### Split Suggestion Format

```
⚡ TOPOLOGY CHECK: This task touches domains that may belong elsewhere:

  Domain "frontend" → gald3r_frontend owns this capability
  Domain "mobile" → no project owns this — consider spawning

Options:
  [1] Keep entire task here (this-project only)
  [2] Split: create local task (backend slice) + PCAC order to gald3r_frontend (frontend slice)
  [3] Split + spawn: create local + PCAC order + spawn new project for "mobile"
  [s] Skip topology check

Choice [1/2/3/s]:
```

### On Split Confirmed (Option 2 or 3)

1. **Create local task** — description scoped to this-project's domain slice
2. **For each remote domain**: invoke `g-skl-pcac-order` to create a PCAC order to the target project with:
   - `remote_task_title`: full original task title
   - `description`: the remote slice
   - `cross_project_ref`: `{domain}-{task_slug}` (shared canonical name across all participating projects)
3. **Add `cross_project_ref:` field** to the local task YAML:
   ```yaml
   cross_project_ref:
     slug: "{domain}-{task_slug}"      # shared logical feature name
     participating_projects:
       - "{this_project_slug}"
       - "{remote_project_slug}"
     peer_order_ids: ["ord-{id}"]      # order IDs sent to each peer
   ```
4. Print summary:
   ```
   ✅ Split complete:
   → this-project: task{NNN} (backend slice)
   → gald3r_frontend: PCAC order ord-{id} sent (frontend slice)
   cross_project_ref: "auth-unified-login"
   ```

### On Spawn Confirmed (Option 3 with new capability)

1. Immediately after split write: invoke `g-pcac-spawn` with:
   - `--description`: "{capability} capability extracted from task {original_title}"
   - `--capabilities`: [the capability domain]
   - `--parent` or `--sibling` (let user choose)
2. After spawn completes: send the spawn's slice as a PCAC order to the newly created project

### Skip / No Topology

- If `.gald3r/linking/link_topology.md` does not exist or is empty → skip check silently
- If topology exists but no peers own conflicting domains → skip check silently
- User can always choose option `[s]` to skip without penalty

---

## Follow-Up Task Filing Gate

When an agent pipeline (`g-go`, `g-go-code`, `g-go-review`) surfaces follow-up items in a session
summary, each item MUST be created as an actual task file before the summary is written.

**The pattern "named but not filed" is a policy violation.** Slug-style names like
`T1043-followup-template-gitignore` without a real `.gald3r/tasks/` file result in permanent
task loss. This has required manual rescue (T1110–T1113) in practice.

### What triggers the Follow-Up Task Filing Gate

- Reviewer notes flagging deferred sub-features, named gaps, or "non-blocking" items
- Implementer finding something out-of-scope but necessary during a run
- Stub/TODO annotations (`TODO[TASK-X→TASK-Y]`) where Y must be a real task file
- Any item described as "can be done later", "for tracking", or "for a follow-up"

### Required steps for each follow-up item

1. **Call `CREATE TASK`** (this operation, below) with:
   - A proper `title:` describing the work
   - `type: feature | bug_fix | refactor` as appropriate
   - `priority: low` (default; raise only when urgency is clear)
   - An `## Objective` describing what the follow-up must accomplish
   - `dependencies: [T{originating_task_id}]` linking back to the surfacing task

2. **Capture the returned `task_id`** (e.g. `T1110`).

3. **Reference only real task IDs** in the session summary (e.g. `T1110: add .gitignore entry`).
   NEVER use slug-style identifiers — they are not task IDs.

4. **If `CREATE TASK` fails** for any reason: log it as a `BLOCKER` in the session summary.
   Do NOT silently name-only the follow-up.

### Rationalization table

| Rationalization | Reality |
|---|---|
| "It's non-blocking, I'll name it for tracking" | Named-only = lost forever. Create the file or it doesn't exist. |
| "The user can create it later" | The user has moved on. The pipeline IS the filing point. |
| "I'm not sure it's needed" | Create with `priority: low`. User can archive it. Costs 30 seconds. |
| "It's just a minor follow-up" | Minor items get lost too. T1110–T1113 were manually rescued. |
| "I'll use a slug name as a placeholder" | Slugs are not task IDs. There is no partial filing. |


