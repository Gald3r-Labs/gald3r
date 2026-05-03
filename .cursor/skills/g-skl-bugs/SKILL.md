---
name: g-skl-bugs
description: Own and manage all bug data — BUGS.md index, bugs/ individual files, bug fixes, quality metrics. Single source of truth for everything bug and quality related.
---
# g-bugs

**Files Owned**: `.gald3r/BUGS.md`, `.gald3r/bugs/bugNNN_*.md`, `.gald3r/archive/archive_bugs_*.md`, `.gald3r/archive/bugs/**`

**Activate for**: report bug, fix bug, archive resolved bugs, quality metrics, "BUG-NNN", any mention of error/defect/warning.

**Auto-trigger (mandatory — no exceptions):**
- A task is moved back to `[📋]` by `@g-go-review` → immediately file a bug for each failing criterion
- A fix is applied in a session without a prior bug report → retroactively file the bug before the response ends
- Any error, warning, or "pre-existing" mention appears in a response → file a bug (g-rl-33)

**Zero tolerance rule**: if you mention it, you log it. Pre-existing and unrelated bugs still get logged.

---

## Workspace Routing Metadata (T175)

Optional bug frontmatter fields for Workspace-Control Mode:

```yaml
workspace_repos:
  - gald3r_dev
workspace_touch_policy: source_only
```

- When `.gald3r/linking/workspace_manifest.yaml` exists, validate `workspace_repos` against manifest `repositories[].id`; unknown repo IDs are invalid.
- Omit `workspace_repos` for current-repository-only bugs. Existing bug records do not require migration and default to the manifest owner repository.
- Validate `workspace_touch_policy` against manifest `routing_policy.workspace_touch_policy_values` (`source_only`, `generated_output`, `multi_repo`, `docs_only` in the bootstrap manifest).
- If omitted, `workspace_touch_policy` defaults to normal current-repo source work. Workspace-control bugs that name member repos must set it explicitly.
- `workspace_repos` defines where the bug may be inspected or fixed, not write permission; writes still must satisfy the bug record, linked task, `g-skl-workspace` ENFORCE_SCOPE, and the manifest allowed-write policy.
- Member repo fixes require explicit member IDs, compatible touch policy, bug or linked-task text authorizing member writes or generated output, reviewed member git status, and manifest write permission or a task-specific override. During bootstrap, planned member repos with `write_allowed: false` are blocked.
- Widening a bug from current-repo-only to member repos, or changing policy to `generated_output`/`multi_repo`, requires a Status History note or equivalent explicit instruction explaining the scope change.
- `BUGS.md` should omit these fields for current-repo-only bugs. For workspace-scoped bugs, add only a compact suffix when useful, for example `workspace: gald3r_template_full; policy: generated_output`.
- These fields complement `cross_project_ref`: workspace routing controls filesystem scope; `cross_project_ref` tracks PCAC coordination state.

---

## Operation: REPORT BUG

1. **Determine next ID**: read `BUGS.md`, find highest BUG-NNN → increment by 1

2. **Classify severity**:
   - **Critical**: crash, data loss, security vulnerability
   - **High**: major feature failure, >50% perf regression
   - **Medium**: minor feature issue, usability problem
   - **Low**: cosmetic, pre-existing, out-of-scope

2a. **Workspace routing classification** (optional):
   - If the bug is current-repo-only, omit `workspace_repos` and `workspace_touch_policy`; omitted metadata means current/owner repository only
   - If it involves workspace members, parse `.gald3r/linking/workspace_manifest.yaml` and validate repo IDs against manifest `repositories[].id`
   - Reject or clearly flag unknown repo IDs when the manifest exists
   - Require `workspace_touch_policy` from manifest `routing_policy.workspace_touch_policy_values` when a member repo is listed; use `generated_output` for generated or mirrored member artifacts unless the member repo is explicitly hand-maintained source
   - Record member-scope rationale in the bug body or Status History before widening an existing bug to member repos

3. **Create bug file** at `.gald3r/bugs/bugNNN_descriptive_name.md`:
```yaml
---
id: NNN
title: 'Bug Title'
severity: critical | high | medium | low
status: open
source: development | testing | production | user_reported
subsystems: [affected-subsystems]
file: 'path/to/file.ext'
line: null
task_reference: null
prd_reference: null
# Optional workspace-control routing; omit for current-repo-only bugs:
workspace_repos:
  - gald3r_dev
workspace_touch_policy: source_only
created_date: 'YYYY-MM-DD'
resolved_date: ''
---
# BUG-NNN: Bug Title

## Description
[What's wrong]

## Reproduction
1. Step one
2. Step two

## Expected vs Actual
- **Expected**: [what should happen]
- **Actual**: [what actually happens]

## Root Cause
[Filled in when resolved]

## Fix
[Filled in when resolved]

## Status History

| Timestamp | From | To | Message |
|-----------|------|----|---------|
| YYYY-MM-DD | — | open | Bug filed |
```

4. **Add to BUGS.md** (atomic — same response):
   ```
   | [🔴] | BUG-NNN | Brief description | Critical | subsystem |
   ```
   Update "Next Bug ID" counter at bottom.

5. **Update subsystem Activity Log** for each affected subsystem (see g-subsystems)

6. **Create task for Medium/High/Critical bugs** — activate g-tasks CREATE with `type: bug_fix` and `bug_reference: BUG-NNN`

7. **Confirm**: `✅ Logged as BUG-NNN: {title} [{severity}]`

---

## Operation: VERIFICATION FAILURE → AUTO BUG

Triggered when `@g-go-review` marks a task back to `[📋]` for failing one or more criteria.

1. **For each failing criterion** in the verification result:
   - Classify severity: criterion about core behavior → Medium; cosmetic/doc → Low
   - File a bug using REPORT BUG operation with:
     - `title`: "{task title} — {criterion description} unmet at verification"
     - `source: testing`
     - `task_reference: task{NNN}`
     - `subsystems`: same as the failed task

2. **Link task ↔ bug**: update the task file to include `bug_reference: BUG-NNN`

3. **Note in bug file** whether the root cause is:
   - **Missing implementation** (agent didn't build it) → `type: missed_implementation`
   - **Broken implementation** (built but wrong) → `type: regression`
   - **Process gap** (workflow didn't enforce it) → `type: process_gap`

**This ensures every verification failure leaves a traceable quality record, not just
a task moved silently back to [📋].**

---

## Operation: RETROACTIVE BUG (fix without prior report)

When a fix was applied in this session but no bug was filed before or during the fix:

1. File the bug using REPORT BUG with `status: resolved`, `resolved_date: today`
2. Fill in Root Cause and Fix sections immediately (you just did the fix — document it)
3. Note in bug file: "Retroactively filed — fix applied before bug was logged"
4. Link bug to any associated task via `task_reference`

**Retroactive bugs still count.** The audit trail matters even after the fact.

---

## Operation: FIX BUG

1. **Read** `.gald3r/bugs/bugNNN_*.md` — reproduction steps, expected/actual
   - **Archive lookup guard (T204)**: if no active `.gald3r/bugs/bugNNN_*.md` file exists, search `.gald3r/archive/archive_bugs_*.md` for `BUG-NNN`, read the archived file path from the archive index, and report it as historical/resolved context only.
   - Archived terminal bugs are read-only by default. Refuse fix/status mutations with: `BUG-NNN is archived at {path}; restore/unarchive is required before changes.`
   - Do not recreate an archived bug in `.gald3r/bugs/` unless a future explicit restore operation exists and the user requested it.
2. **Read linked task** (if any) — check acceptance criteria
3. **Implement fix**
   - **Workspace routing check**: run `g-skl-workspace` ENFORCE_SCOPE against modified paths and bug/linked-task frontmatter; omitted metadata is current-repo-only, unknown manifest repo IDs block, generated-output fixes must record canonical source provenance, and member repo writes require explicit authorization plus manifest write permission
4. **Update bug file**:
   ```yaml
   status: resolved
   resolved_date: 'YYYY-MM-DD'
   ```
   Fill in "Root Cause" and "Fix" sections.

5. **Update BUGS.md**: change indicator from `[🔴]` to `[✅]`
6. **Update subsystem Activity Log** — append: `| YYYY-MM-DD | BUG | NNN | Fixed: {brief} |`
7. **Append to Status History** in the bug file (REQUIRED):
   ```
   | YYYY-MM-DD | open | resolved | Fix applied: {brief description of fix} |
   ```
   If bug was reopened: `| YYYY-MM-DD | resolved | open | Reopened: {reason} |`
8. **Update linked task** (if any) → `status: awaiting-verification` via g-tasks UPDATE
9. **Offer git commit**:
   ```
   fix({subsystem}): resolve BUG-NNN — {brief description}
   Bug: BUG-NNN | Root cause: {brief}
   ```

**Fast path (pre-existing/Low severity)**:
- Fix inline, update bug file + BUGS.md status, append Activity Log — no separate task needed

---

## Operation: ARCHIVE BUGS (T204)

**Usage**: `@g-bug-archive --dry-run` or `@g-bug-archive --apply`

Archives resolved/closed bug history so `BUGS.md` remains an active quality index instead of an ever-growing historical ledger.

### Archive Layout

- Active index: `.gald3r/BUGS.md`
  - Keep open, in-progress, awaiting-verification, verification-in-progress, requires-user-attention, blocked, and recently resolved bugs.
  - Do not keep the full historical bug ledger in this file once bugs are archived.
- Archive index files live directly under `.gald3r/archive/`:
  - `.gald3r/archive/archive_bugs_0000_0999.md`
  - `.gald3r/archive/archive_bugs_1000_1999.md`
  - Continue in 1000-entry buckets as needed.
- Archived bug files live under bucketed subfolders:
  - `.gald3r/archive/bugs/bugs_0000_0999/`
  - `.gald3r/archive/bugs/bugs_1000_1999/`
  - Continue in 1000-file buckets as needed.
- Bucket ranges are based on archive entry ordinal, not BUG-NNN. Bugs may close out of order; archive placement follows the next archive slot.

### Eligibility

Archive candidates:

- `status: resolved` / `[✅]`
- `status: closed`, `status: cancelled`, or terminal equivalents in older bug records

Do not archive:

- `[🔴]`, `[🟠]`, `[🟡]`, `[⚪]`, `[🔄]`, `[🔍]`, `[🕵️]`, `[🚨]`
- Bugs referenced by active bug-fix tasks unless the archive index records the link and the active task remains resolvable.
- Recently resolved bugs when the command is run without an explicit `--include-recent` flag. Default recent window: 14 days.

### Archive Index Entry

Each archived bug gets one compact entry in the current archive index:

```markdown
| Archive Slot | Bug | Title | Severity | Final Status | Resolved/Closed | Source Project | Workspace Repos | Archived File |
|--------------|-----|-------|----------|--------------|-----------------|----------------|-----------------|---------------|
| 0000 | BUG-123 | Example | Medium | resolved | 2026-04-25 | gald3r_dev | gald3r_dev | archive/bugs/bugs_0000_0999/bug123_example.md |
```

### Archived Bug File Metadata

When moving a bug file into the archive bucket, preserve the original frontmatter and add archive provenance:

```yaml
archive:
  archived: true
  archive_slot: 0
  archive_index: ".gald3r/archive/archive_bugs_0000_0999.md"
  archived_path: ".gald3r/archive/bugs/bugs_0000_0999/bug123_example.md"
  archived_at: "YYYY-MM-DD"
  source_project: "gald3r_dev"
  original_bug_id: "BUG-123"
```

For imported project history, also preserve `source_project`, `source_project_id`, `source_bug_id`, and `imported_from` when present.

### Dry-Run Behavior

`--dry-run` is the default. It must report:

1. Candidate count by final status and severity.
2. Active bugs blocked from archival and why.
3. Target archive index bucket(s).
4. Target archived file bucket(s).
5. Estimated `BUGS.md` line reduction.

No files are written in dry-run mode.

### Apply Gate

`--apply` may write only when:

1. The active task explicitly authorizes archival work.
2. The dry-run plan has been shown in the same session.
3. `.gald3r/archive/`, `.gald3r/archive/bugs/`, and target buckets can be created safely.
4. Every moved bug has a matching archive index entry.
5. `BUGS.md` retains an "Archive Pointers" section linking to archive index files.

Apply output must end with:

```text
Bug archive applied. BUGS.md is now an active index; historical bug records moved to .gald3r/archive/.
```

### Historical Lookup

When a user or workflow references a bug ID that is not present in `.gald3r/BUGS.md` or `.gald3r/bugs/`, search archive indexes before reporting it missing:

1. Search `.gald3r/archive/archive_bugs_*.md` for `BUG-NNN`.
2. Read the matching `Archived File` path.
3. Return the archived record as historical context only.
4. Report the archive slot, archive index file, archived bug file path, final status, severity, source project, and workspace repos.

### Archived Mutation Guard

Archived bug files are immutable terminal history unless a future restore/unarchive command explicitly rehydrates them. FIX BUG, status updates, bug deletion, and sync repair must not edit archived bug files in place. If a workflow tries to mutate an archived bug, stop and report the archive location plus the required restore/unarchive next step.

---

## Operation: QUALITY REPORT

1. **Read BUGS.md** — parse all entries, group by severity and status
2. **Collect metrics**:
   - Total: open / resolved / in-progress
   - Severity distribution: critical/high/medium/low
   - Resolution rate: resolved / total × 100
   - Average age of open bugs (days since created)
3. **Subsystem impact**: which subsystems have the most open bugs?
4. **Output**:
```markdown
# Quality Metrics
Generated: YYYY-MM-DD

## Bug Summary
| Metric | Value |
|---|---|
| Total | N |
| Open | N |
| Resolved | N |
| Resolution Rate | N% |

## Severity Distribution
| Severity | Open | Resolved |
|---|---|---|
| Critical | N | N |
| High | N | N |
| Medium | N | N |
| Low | N | N |

## Hottest Subsystems
| Subsystem | Open Bugs |
|---|---|
| {name} | N |

## Quality Score: N/100
Healthy (≥80) | Degraded (50-79) | Critical (<50)
```

---

## Severity Indicators Reference

| Indicator | Severity | BUGS.md |
|---|---|---|
| `[🔴]` | Critical | Open |
| `[🟠]` | High | Open |
| `[🟡]` | Medium | Open |
| `[⚪]` | Low | Open |
| `[✅]` | Any | Resolved |
| `[🔄]` | Any | In Progress |
| `[🔍]` | Any | Awaiting Verification |
| `[🕵️]` | Any | Verification In Progress |
| `[🚨]` | Any | Requires User Attention |

---

## Verification Claim Rules

`[🕵️]` prevents multiple review agents from verifying the same bug fix at once.

When `g-go-review` or `g-go-review --swarm` selects a `[🔍]` bug:
1. Atomically change `BUGS.md` and the bug YAML from `[🔍]` / `awaiting-verification` to `[🕵️]` / `verification-in-progress`.
2. Add verifier claim metadata in the bug YAML:
   ```yaml
   verifier_owner: "{platform_or_agent_slug}"
   verifier_claimed_at: "{ISO-8601 timestamp}"
   verifier_claim_expires_at: "{ISO-8601 timestamp}"  # default 120 minutes
   ```
3. Append a Status History row: `awaiting-verification -> verification-in-progress`.
4. Other review agents must skip `[🕵️]` bugs unless `verifier_claim_expires_at` is older than the current time.
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

---

## Circuit-Breaker Rule: Stuck Bug Detection

When any bug fix has been verified and **FAILED 3 or more times**:

1. **Count FAIL rows** in the bug's `## Status History` table (rows where Message contains "FAIL:")
2. **If count ≥ 3** → mark the bug `[🚨]` (requires-user-attention) instead of returning to `[📋]`
3. **Append stuck note** to the bug file:

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

4. **Never autonomously reset** `[🚨]` back to `[📋]` — only a human can do this.

This prevents infinite fix→verify→fail loops from burning agent tokens.
