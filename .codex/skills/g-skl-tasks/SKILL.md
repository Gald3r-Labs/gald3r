---
name: g-skl-tasks
description: Own and manage all task data — TASKS.md index, tasks/ individual files, status transitions, sync validation, complexity scoring, and sprint planning. Single source of truth for everything task-related.
---
# g-tasks

**Files Owned**: `.gald3r/TASKS.md`, `.gald3r/tasks/taskNNN_*.md`, `.gald3r/archive/archive_tasks_*.md`, `.gald3r/archive/tasks/**`

**Activate for**: create task, update task status, archive completed tasks, sync check, complexity score, sprint plan, task dependencies, "phantom" or "orphan" issues.

---

## Workspace Routing Metadata (T175)

Optional task frontmatter fields for Workspace-Control Mode:

```yaml
workspace_repos:
  - gald3r_dev
workspace_touch_policy: source_only
```

- When `.gald3r/linking/workspace_manifest.yaml` exists, validate `workspace_repos` against manifest `repositories[].id`; unknown repo IDs are invalid.
- Omit `workspace_repos` for current-repository-only work. Existing tasks do not require migration and default to the manifest owner repository.
- Validate `workspace_touch_policy` against manifest `routing_policy.workspace_touch_policy_values` (`source_only`, `generated_output`, `multi_repo`, `docs_only` in the bootstrap manifest).
- If omitted, `workspace_touch_policy` defaults to normal current-repo source work. Any task that names a controlled member repo must set it explicitly.
- `workspace_repos` is an allow-list for inspection/modification scope, not write permission; actual writes must also satisfy task acceptance criteria, `g-skl-workspace` ENFORCE_SCOPE, and each repository's manifest `allowed_write_policy`.
- Member repo writes require explicit member IDs, a compatible touch policy, task text authorizing member writes or generated output, reviewed member git status, and manifest write permission or a task-specific override. During bootstrap, planned member repos with `write_allowed: false` are blocked.
- Widening a task from current-repo-only to member repos, or changing policy to `generated_output`/`multi_repo`, requires a Status History note or equivalent explicit instruction explaining the scope change.
- `TASKS.md` should omit these fields for current-repo-only tasks. For workspace-scoped tasks, add at most a short suffix such as `workspace: gald3r_dev+gald3r_template_full; policy: generated_output`; the task file remains the source of truth.
- These fields complement `cross_project_ref`: workspace routing controls filesystem scope; `cross_project_ref` tracks PCAC orders, dependencies, and shared logical work.

---

## Operation: CREATE TASK

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

3. **Create task file** at `.gald3r/tasks/taskNNN_descriptive_name.md`:

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
ai_safe: true
release_id: null              # optional: release ID this task is scheduled for (e.g. 3)
created_date: 'YYYY-MM-DD'
completed_date: ''
# Optional workspace-control routing; omit for current-repo-only work:
workspace_repos:
  - gald3r_dev
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
---

# Task NNN: [Title]

## Objective
[Clear, actionable goal — done when this is complete]

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
   File: .gald3r/tasks/taskNNN_name.md
   TASKS.md: [📋] added under Subsystem: {name}
   ```

---

## Operation: SPEC AUTHORING FLOW (T164)

`[📝]` is an active speccing claim. It prevents multiple agents from creating or rewriting the same task spec at the same time.

### CLAIM-FOR-SPEC

Use this before turning a bare `[ ]` task row into a task file, or before materially rewriting an incomplete task spec.

1. Read `TASKS.md` and any existing `.gald3r/tasks/taskNNN_*.md` file.
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
```

1. **Read both**: `.gald3r/tasks/taskNNN_*.md` YAML and TASKS.md indicator — fix mismatch first (file is source of truth)

   **Archive lookup guard (T204)**:
   - If no active `.gald3r/tasks/taskNNN_*.md` file exists, search `.gald3r/archive/archive_tasks_*.md` for `Task NNN`.
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
| Fail/cancel | `status: failed` | `[❌]` |

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

2b. **Before → `[✅]` (docs check)**: After all ACs verified, check user-facing impact:
   - Does this task add/remove/change user-facing behavior? (skills, commands, agents, hooks, rules, conventions)
   - **YES** → append entry to `CHANGELOG.md` under `[Unreleased]`; update `README.md` if a relevant section exists
   - **NO** (internal refactor, task housekeeping, bug fix with no interface change) → skip
   - See `g-rl-26-readme-changelog.mdc` for qualifying criteria and format

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
- Worktrees must be created/reported/removed through `scripts/gald3r_worktree.ps1` so cleanup can prove ownership with `.gald3r-worktree.json`.
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

5. **Confirm**:
   ```
   ✅ Task NNN → {new_status}
   File YAML: updated | TASKS.md: updated | Sync: verified
   Release: {release name} (target: {date}) — {days} days away    ← if release_id is set
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
| 0000 | Task 123 | Example | completed | 2026-04-25 | gald3r_dev | gald3r_dev | archive/tasks/tasks_0000_0999/task123_example.md |
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
  source_project: "gald3r_dev"
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

From `.gald3r/tasks/taskNNN_*.md`:
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

## Operation: SYNC CHECK

Run at session start or when phantom/orphan issues suspected.

1. **Read TASKS.md** — extract all task entries with indicators
2. **List** `.gald3r/tasks/task*.md`
3. **For each TASKS.md entry**:
   ```
   [✅][❌][⏸️] → look in tasks/
   [📝][📋][🔄][🔍][🕵️] → look in tasks/ only
   [ ]           → no file expected (OK)

   ✅ FOUND   = file exists
   ⚠️ PHANTOM = in TASKS.md but no file
   ```
4. **For each task file** — has matching TASKS.md entry? NO → ORPHAN ⚠️
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
| `[📝]` | `speccing` | Claimed for spec authoring; skip unless claim is expired |
| `[📋]` | `pending` | File created, ready to start |
| `[🔄]` | `in-progress` | Being worked on |
| `[🔍]` | `awaiting-verification` | Done, needs different-agent review |
| `[🕵️]` | `verification-in-progress` | Claimed by a verifier; skip unless claim is expired |
| `[✅]` | `completed` | Verified complete |
| `[❌]` | `failed` | Failed or cancelled |
| `[⏸️]` | `paused` | Paused |
| `[🚨]` | `requires-user-attention` | Stuck ≥3 FAIL cycles — **agents must not retry; human-only resolution** |

### [📝] Speccing Claim Rules

`[📝]` prevents multiple agents from writing competing specs for the same task.

When any task-authoring workflow selects a `[ ]` task or incomplete spec:
1. Atomically change `TASKS.md` and task YAML to `[📝]` / `speccing`.
2. Add `spec_owner`, `spec_claimed_at`, and `spec_claim_expires_at` metadata.
3. Append a Status History row for `[ ] -> [📝]` / `pending -> speccing`.
4. Other agents must skip `[📝]` tasks unless `spec_claim_expires_at` is older than the current time.
5. A stale takeover must append a Status History row naming the previous `spec_owner` and new owner.
6. Finished specs move `[📝] -> [📋]`; cancelled specs move `[📝] -> [❌]`.

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
