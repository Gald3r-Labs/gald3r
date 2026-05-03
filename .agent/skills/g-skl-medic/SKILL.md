---
name: g-skl-medic
version: 2.0.0
description: >
  Tiered .gald3r/ health and intervention system. L1=triage (structural), L2=diagnosis
  (plan coherence), L3=surgery (cross-subsystem interface audit), L4=ecosystem
  (linked project negotiation). Replaces g-skl-medic.
triggers:
  - "@g-medic"
  - "fix gald3r"
  - "health check"
  - "upgrade gald3r"
  - "project is out of sync"
  - "placeholders"
  - broken TASKS.md
  - missing files
  - version mismatch
  - "medic"
---

# g-medic

**Replaces**: `g-medic` (deprecated — delegates to `g-medic`)

**Files Touched**: `.gald3r/` (all files and folders), optionally linked project folders at L4

**Authorization rule**: `g-medic` and `g-setup` are the ONLY things that may write `gald3r_version` to `.gald3r/.identity`. No other skill, agent, hook, or command may touch that field.

---

## Command Interface

```bash
@g-medic                      # L1 triage only (safe default, always applies)
@g-medic --level 2            # L1 + L2 (report generated; --apply to execute fixes)
@g-medic --level 3            # L1 + L2 + L3 (requires --apply to write fixes)
@g-medic --level 4            # L1 + L2 + L3 + L4 (Workspace-Control plus optional PCAC)
@g-medic --ecosystem          # alias for --level 4
@g-medic --dry-run            # any level: report only, no writes
@g-medic --level 2 --apply   # apply L2 fixes after generating report
@g-medic --curate             # feature/subsystem fragmentation analysis (dry-run; no moves)
@g-medic --curate --apply -ProposalJson .gald3r/reports/medic_curate_proposal_*.json  # git mv from approved JSON only
```

### Dry-Run and Output Contract

- `@g-medic --dry-run` is strictly read-only for L1-L4: no task status changes, no TTL resets, no identity/version writes, no backlog regeneration, no report files, and no member-repo changes. It may read `.gald3r/` and print findings only.
- L1 "auto-applies" only when `--dry-run` is absent. If `--dry-run` is present, L1 must report what it would create/update/reset instead of writing.
- If a report finds material drift, blockers, high/critical bugs, phantoms/orphans, stale claims, parser skips, or workspace/member risks, surface the full operational findings to the user. Do not hide them behind a short summary. Summaries may be added after the full findings.
- For any count above 25, include either the complete ID/file list inline or a named report artifact path containing the complete list. Compressed ranges are acceptable only as an additional convenience, never as the only evidence.
- `--curate` is a special curation workflow: by default it writes gitignored proposal/report files for human review; pass the script-level `-NoReportFiles` option when the user requests a no-disk-side-effect dry run.

### Curation mode (`--curate`, Task 517)

**Default (dry-run)**: runs `scripts/gald3r_medic_curate.ps1` — counts feature/subsystem sprawl (recursive subsystem count), runs hierarchy sync helpers with `-WarnOnly`, adds a **fragmentation** section (duplicate `feat-NNN` hits in `FEATURES.md`, subsystem specs on disk not indexed in `SUBSYSTEMS.md` via sync JSON), and writes a human report plus `medic_curate_proposal_<stamp>.json` under `.gald3r/reports/` (gitignored). The proposal keeps top-level `moves` empty for safety, but now includes non-binding `suggested_moves` and `index_candidates` with source, target, risk/confidence, and rationale so the reviewer has concrete candidates to approve/edit/reject.

**No report files (CI / no disk side effects)**: pass `-NoReportFiles` to `gald3r_medic_curate.ps1` — prints the same report + proposal JSON to stdout only (no `medic_curate_*.md` / proposal files / `medic_curate_latest.json`).

**Apply**: **never** implied. Requires `-ProposalJson` pointing at a proposal JSON that includes non-empty top-level `moves`; dry-run `suggested_moves` are advisory only and must be copied into `moves` after review. Script **backs up** each source under `.gald3r/reports/medic_curate_backup_<stamp>/`, performs `git mv` for each entry (paths must stay under `.gald3r/features/` or `.gald3r/subsystems/`; duplicate from/to rejected), **literal path replace** in `FEATURES.md`, `SUBSYSTEMS.md`, and `.gald3r/tasks/*.md` for moved paths, writes a manifest JSON, then runs `gald3r_subsystem_diagrams_generate.ps1`. Refuses when the working tree has unrelated dirty paths. **Never targets** workspace member marker-only `.gald3r/` trees — pass controller repo root only.

**Default behavior**: `@g-medic` with no args runs L1 only (auto-applies — it's always safe).

---

## PCAC Inbox Health Gate

Before mode detection, determine whether the project is a PCAC participant. PCAC is active only when `.gald3r/linking/link_topology.md` declares at least one parent/child/sibling relationship, or `.gald3r/PROJECT.md` explicitly declares PCAC project linking relationships. A Workspace-Control manifest and local `INBOX.md` alone do not make a project part of a PCAC group.

Only when PCAC is active, call `g-hk-pcac-inbox-check.ps1` without `-BlockOnConflict` when present and capture the result. L1 triage must continue even when `INBOX CONFLICT GATE` is reported so health scoring can surface the conflict. Open PCAC conflicts block L2-L4 planning/apply work, task claiming, implementation, and verification after L1 completes; require `@g-pcac-read` before continuing. Non-conflict requests, broadcasts, and syncs remain advisory and should be surfaced in output. If PCAC is not active, skip the hook and report `PCAC: not configured / skipped`.

## Mode Detection (Run Before Any Level)

Read `.gald3r/.identity`. Based on what you find, select a mode:

```
□ .identity missing entirely?
  → STOP. Invoke g-setup. This is not a repair situation — it's a fresh install.

□ gald3r_version in .identity doesn't match the current gald3r version?
  → MODE: UPGRADE (full structural migration, then continue through all phases)

□ gald3r_version matches, but files/folders are missing or corrupted?
  → MODE: REPAIR (structural fixes + per-file health, skip version bump)

□ gald3r_version matches, structure is intact, just routine maintenance?
  → MODE: MAINTAIN (TTL resets, health score, backlog — skip structural phases)
```

Report selected mode at the start:
```
🩺 g-medic — L{N} | MODE: {UPGRADE | REPAIR | MAINTAIN}
   Project: {project_name} | gald3r v{current} → v{target or "current"}
   Dry-run: YES (pass --apply to execute) | APPLY
```

---

## Level 1 — Triage (Structural Integrity)

*Safe to run any time. Fully autonomous. Blast radius: files and folders only.*
*Applied automatically with no `--apply` needed unless `--dry-run` is present. Runs in all modes.*

### L1-A: Folder Structure

Verify every required `.gald3r/` folder exists. Create missing ones silently:

```
tasks/            individual task files
bugs/             individual bug files
features/         PRD/feature files
subsystems/       per-subsystem spec files
reports/          cleanup and upgrade reports
specifications_collection/   incoming specs/wireframes
linking/          INBOX.md, shared contracts
```

Report any folders created.
In `--dry-run`, report missing folders as `would_create` and do not create them.

### L1-B: Root File Audit

Check each required root file. Create from template if missing:

| File | If Missing | Health Check |
|---|---|---|
| `TASKS.md` | Create empty template | Task Sync (L1-D) |
| `BUGS.md` | Create empty template | Bug Sync (L1-D) |
| `PLAN.md` | Create empty template | Has `## Current Focus`? |
| `FEATURES.md` | Create empty template | Has `## PRD Index` table? |
| `PROJECT.md` | Create empty template | Goals Check (L1-D) |
| `CONSTRAINTS.md` | Create header-only stub | Has `## Architectural Constraints`? |
| `SUBSYSTEMS.md` | Create empty template | Subsystem Sync (L1-D) |
| `IDEA_BOARD.md` | Create empty template | Has `## Active Ideas`? |

In `--dry-run`, report missing files as `would_create` and do not create them.

### L1-C: .identity Integrity

Verify all fields present and valid:
```ini
project_id=     ← UUID format — STOP if missing, invoke g-setup
project_name=   ← warn if doesn't match parent folder name
user_id=        ← fill with "unknown" if missing
user_name=      ← fill with "unknown" if missing
gald3r_version=  ← semver format
vault_location= ← fill with "{LOCAL}" if missing
```

### L1-D: Task / Bug / Feature / Subsystem Sync

- **Tasks**: activate `g-tasks → SYNC CHECK`. Auto-fix status mismatches (file is source of truth). Report phantoms/orphans.
- **Bugs**: for each BUGS.md row: check `bugs/bugNNN_*.md` exists. Missing → PHANTOM ⚠️
- **Features**: same phantom/orphan pattern.
- **Subsystems**: activate `g-subsystems → SYNC CHECK`. Add stub entries for subsystems referenced in tasks but missing from registry.

#### L1-D Parser Contract — Active Index Scope (mandatory)

Medic sync checks MUST distinguish active control-plane records from historical or imported inventory. Do not use recursive file scans for active orphan/phantom counts.

- **Active `TASKS.md` rows**: count every active task row matching a status indicator in either supported index format: bullet rows like `- [✅] **Task 090**: ...` and table rows like `| [📋] | [090](tasks/task090_*.md) | ... |` or `| [🔍] | T123 | ... |`. Normalize Markdown links, optional `Task`/`T` prefixes, leading zeros, and subtask suffixes while preserving the suffix (`052-1` is distinct from `052`). Deduplicate by normalized task ID before computing totals; matching duplicate rows are duplicate inventory findings, while conflicting duplicate statuses are critical parser findings.
- **Active task files**: scan only direct children of `.gald3r/tasks/` matching `task<id>_*.md` or `task<id>-<suffix>_*.md`. Exclude all recursive subdirectories from active orphan math, including `archive/`, `bkup/`, `backup/`, `quarantine/`, `adopted/`, `imports/`, and any future historical bucket.
- **Historical/imported task files**: report separately as archival inventory with their source metadata (`source_harvest`, `adopted_from`, `workspace_repos`, `delegated_to`, `source_quarantine`, etc.). Never call these active orphans unless the file is a direct child of `.gald3r/tasks/`.
- **Phantom** means an active `TASKS.md` row has no matching direct child task file.
- **Orphan** means a direct child task file has no matching active `TASKS.md` row.
- If a diagnostic reports more than 25 IDs, include the full list in the report body or a named report artifact path. Do not only emit compressed ranges when the user asked for operational status.

### L1-E: Sequential ID Integrity

- Tasks: find ID gaps, duplicates, out-of-order entries → report; offer auto-renumber (requires `--apply`)
- Bugs: same
- Features: same

### L1-F: YAML Frontmatter Validation

For each `tasks/*.md`, `bugs/*.md`, `features/*.md`:
- Malformed YAML (fails to parse) → report as critical
- Missing required fields → add with defaults silently
- Status normalization: `in_progress` → `in-progress`

### L1-G: Empty Stub Detection

Tasks or bugs with no `## Objective` or `## Acceptance Criteria` → flag as incomplete stub

### L1-H: BOM / Encoding Audit

Check for BOM (`\xef\xbb\xbf`) at file start in any `.gald3r/**/*.md` → report; remove with `--apply`

### L1-I: Version Bump (UPGRADE mode only, after apply confirmed)

Write new `gald3r_version` to `.gald3r/.identity`. Append to `.gald3r/reports/UPGRADE_LOG.md`.

### L1-J: Maintenance Routines (ALL modes)

- **TTL Check**: for each `in-progress` task: `now > claim_expires_at`? → reset to `pending`
- **Verification Timeout**: `[🔍]` for > 8h → reset to `pending`; > 4h → flag only
- **Health Score**:
  ```
  base  = (completed / total_non_cancelled) × 100
  -5    per stale [🔄]
  -3    per [🔍] > 4h
  -10   per task with failure_history > 2
  -15   per subsystem with no tasks ever
  -20   per open PCAC `INBOX.md` CONFLICT item (L1 continues, L2-L4 blocked until `@g-pcac-read`)
  final = max(0, base − penalties)
  Healthy: ≥80 | Degraded: 50-79 | Critical: <50
  ```
- **ACTIVE_BACKLOG.md Regeneration**: write `.gald3r/ACTIVE_BACKLOG.md`
- **Platform Parity Audit**: compare `.cursor/rules/`, `.claude/rules/`, `.agent/rules/` — report violations (see `PARITY_EXCLUDES.md`)
- **Placeholder Sweep**: scan `.gald3r/**/*.md` for `{project_name}`, `{Goal name}`, `YYYY-MM-DD` (literal) — auto-fill `{project_name}` from `.identity`; report rest

### L1 Output

Full operational report plus optional brief console summary:
```
🩺 g-medic L1 — {project_name} | TRIAGE complete
   ✅ tasks/  ✅ bugs/  ⚠️ features/ CREATED
   Tasks synced: 42  |  Bugs synced: 8  |  0 phantoms
   Health score: 87/100  |  TTL resets: 0
   Report: .gald3r/reports/{YYYYMMDD_HHMMSS}_MEDIC_L1.md
```

---

## Level 2 — Diagnosis (Plan Coherence)

*Requires human review before applying. Blast radius: .gald3r/ data.*
*Run with `--level 2`. Generates `MEDIC_REPORT_L2.md`. Use `--apply` to execute fixes.*

### L2-A: PLAN.md vs TASKS.md Coherence

- Milestones listed as complete in PLAN.md: verify all associated tasks are `[✅]`
- Milestones with no associated tasks: flag
- Tasks in TASKS.md with no milestone parent: flag if >30 days old

### L2-B: Task Dependency DAG Validation

```
□ Circular dependencies (A depends B; B depends A) → CRITICAL flag
□ Dependency on non-existent task ID → ERROR flag
□ Dependency on cancelled/failed task → WARNING flag
□ Tasks blocked > 14 days on unresolved dependency → surface in report
```

### L2-C: Interface Compatibility Check

For tasks with `output_format:` or `input_format:` fields:
- "Task A says it outputs X format; Task B expects Y format — incompatible" → flag

### L2-D: Complexity Audit

Tasks with >8 acceptance criteria OR >3 subsystems: suggest subtask split (write as proposed blocks in report — NOT auto-created)

### L2-E: Feature ↔ Task Linkage

- Features with `status: specced` or `status: committed` but no linked task → flag: "orphaned feature spec"
- Tasks with no feature back-reference AND >2 ACs → flag: "implementation without spec"

### L2-F: SUBSYSTEMS.md ↔ subsystems/ Completeness

- SUBSYSTEMS.md entry with no `subsystems/{name}.md` file → offer to create stub
- `subsystems/*.md` files with missing `locations:` frontmatter → flag incomplete

### L2-G: Missing Cross-Project Ref

Tasks that span >1 subsystem AND those subsystems are owned by different projects (per `capabilities.md`) but have no `cross_project_ref:` → flag: "may need cross-project routing"

### L2-H: Creates Missing Stubs

With `--apply`:
- Creates missing `tasks/taskNNN_*.md` for TASKS.md entries that have no file
- Creates missing `features/featNNN_*.md` for FEATURES.md entries that have no file
- Each created file is a minimal stub with YAML frontmatter + `## Objective` placeholder

### L2 Output

Write `MEDIC_REPORT_L2.md` to `.gald3r/reports/`:
```markdown
# g-medic L2 Diagnosis Report
**Project**: {name} | **Date**: YYYY-MM-DD

## Critical Findings
- [ ] CIRCULAR DEP: Task 42 ↔ Task 43

## Warnings
- [ ] PLAN coherence: Milestone "M3: Auth" shows complete but Task 17 is still pending

## Suggestions
- [ ] Task 95: 11 ACs — consider splitting into 2-3 sub-tasks

## Stubs Created (--apply)
- tasks/task099_placeholder.md
```

---

## Level 3 — Surgery (Cross-Subsystem Interface Audit)

*Requires explicit `--apply` flag. Blast radius: subsystems + schema contracts.*
*Run with `--level 3 --apply`. Generates `MEDIC_REPORT_L3.md`.*

### L3-A: Cross-Subsystem Data Flow Audit

For each pair of subsystems (A writes → B reads):
1. Find all skills/tasks where A produces output consumed by B
2. Compare output format in A's skill/task spec against expected input format in B's skill/task spec
3. Format mismatch → flag as interface violation

### L3-B: Skill Logic Chain Validation

- SKILL.md operations referenced by commands (e.g., `g-task-add` triggers `g-skl-tasks → CREATE`) → verify operation name matches
- Dead references: command references operation that no longer exists in skill → ERROR

### L3-C: Capabilities Gap Detection

- Tasks/features reference a capability (e.g., "vector search", "OAuth") that no subsystem in `capabilities.md` declares as `status: ready`
- Output: `"Capability gap: vector-search — no subsystem owns this in ready state"`

### L3-D: CONSTRAINTS.md Violation Check

For each active constraint in `CONSTRAINTS.md`:
- Scan task/feature specs for planned work that would violate the constraint
- Flag violating tasks with: `"⚠️ Constraint C-{id} violation: {title}"`

### L3-E: Activity Log Audit

Tasks marked `[✅]` that have NOT appended to any subsystem Activity Log in `subsystems/*.md`:
- Flag: "Task {id} completed but subsystem activity log not updated"

### L3-F: Creates / Annotates

With `--apply`:
- Creates missing subsystem spec files for subsystems referenced in tasks but absent from `subsystems/`
- Adds missing capability entries to `capabilities.md` based on subsystem references
- Annotates interface mismatches directly in affected SKILL.md files with:
  ```
  <!-- BUG[MEDIC-L3]: Interface mismatch — A outputs {format}; B expects {format} -->
  ```

### L3 Output

Write `MEDIC_REPORT_L3.md` to `.gald3r/reports/` with full findings + remediation plan.

---

## Level 4 — Ecosystem (Workspace + Optional PCAC)

*Requires `--level 4` or `--ecosystem` flag. Workspace-Control checks run whenever `.gald3r/linking/workspace_manifest.yaml` exists. PCAC-only checks run only when active PCAC topology exists.*
*Blast radius: controller plus manifest-declared workspace members for read-only diagnostics; PCAC-linked projects only when PCAC is active.*
*If Workspace-Control is active and PCAC is inactive, do not skip L4. Print "PCAC: not active; PCAC topology/inbox checks skipped. Workspace-Control: active; L4 workspace checks ran using workspace_manifest.yaml."*

### L4-0: Mode Split (Mandatory)

Before running L4, classify both coordination systems independently:

- **Workspace-Control active**: `.gald3r/linking/workspace_manifest.yaml` exists and parses. Run L4-W checks.
- **PCAC active**: `.gald3r/linking/link_topology.md` exists and declares at least one non-empty parent/child/sibling relationship, or `.gald3r/PROJECT.md` explicitly declares active PCAC relationships. Run L4-P checks.
- **Neither active**: report that L4 has no workspace or PCAC coordination surface.
- **Do not conflate them**: a missing PCAC topology must never suppress Workspace-Control L4 checks.

### L4-W: Workspace-Control Checks

When Workspace-Control is active:

- Parse `.gald3r/linking/workspace_manifest.yaml` as the canonical member registry.
- Validate manifest syntax, repository IDs, roles, lifecycle statuses, local paths, write policies, and routing policy fields.
- Check each existing manifest member's git root, branch, upstream, dirty status, and member `.gald3r/` marker-only compliance.
- Surface missing planned members separately from broken existing members.
- Report Workspace-Control health separately from PCAC health.

### L4-P: PCAC Checks (Only When PCAC Is Active)

Run the following only when PCAC is active:

### L4-P1: Peer Capability Readiness

- Load `.gald3r/linking/peers/*_capabilities.md`
- Find features/tasks this project depends on that a peer hasn't marked `ready`
- Flag: `"Blocked dependency: {this_task} waits on {peer_slug}:{capability} (status: {status})"`

### L4-P2: Cross-Project Constraint Conflicts

- Load peer capability snapshots
- Compare each peer's known constraints against this project's constraints
- Contradictions (Peer A: "no Docker"; this project: "requires Docker for adv tier") → flag

### L4-P3: Cross-Project Feature Contract Validation

- Find features with `cross_project_ref:` slug
- For each: check peer's version of the same feature (via PCAC INFO or snapshot)
- Spec contradictions → flag: "Feature contract mismatch: {slug} — {this_project} spec vs {peer_slug} spec differ"

### L4-P4: Stale Peer Snapshots

- Peer capabilities last synced > N days ago (default 7) → flag: "Stale peer snapshot: {peer_slug} (last sync: {date})"

### L4-P5: Long-Blocked Cross-Project Tasks

- Tasks with `cross_project_ref` blocked on peer completion for > 14 days → surface for human escalation

### L4-P6: Suggested PCAC Actions

For each finding, generate a suggested PCAC coordination message (does NOT send without explicit per-message human approval):
```
Suggested: [SYNC] to gald3r_valhalla — request capability status update for "vector-search"
  → Run: @g-pcac-notify gald3r_valhalla "Requesting capability status update for vector-search"
  Approve? [y/n]
```

### L4 Output

Write `MEDIC_REPORT_L4.md` to `.gald3r/reports/` (workspace findings plus optional affected-peer findings and consolidated ecosystem health score).

```
🌐 Ecosystem Health Score: 72/100 (Degraded)
  gald3r_valhalla:  3 stale capabilities  |  1 contract mismatch
  gald3r_frontend:  snapshot 12d old  |  2 blocked deps > 14d
```

---

## Cumulative Level Summary

Each level is a superset of the previous:

| Level | Name | Blast Radius | `--apply` needed? |
|-------|------|-------------|-------------------|
| L1 | Triage | Files / folders | No (auto) |
| L2 | Diagnosis | `.gald3r/` data | Yes (for fixes) |
| L3 | Surgery | Subsystems + contracts | Yes (required) |
| L4 | Ecosystem | Workspace members + optional PCAC linked projects | Yes for fixes; per-message approval for PCAC sends |

---

## Report File Naming

```
.gald3r/reports/{YYYYMMDD_HHMMSS}_MEDIC_L1.md
.gald3r/reports/{YYYYMMDD_HHMMSS}_MEDIC_L2.md
.gald3r/reports/{YYYYMMDD_HHMMSS}_MEDIC_L3.md
.gald3r/reports/{YYYYMMDD_HHMMSS}_MEDIC_L4.md
```

---

## Parity Exclusion List

See `PARITY_EXCLUDES.md` in this skill's folder for files intentionally excluded from the parity audit.

---

## See Also

- `g-setup` — fresh install; invoked when `.gald3r/.identity` is missing
- `g-skl-tasks` — owns TASKS.md and tasks/
- `g-skl-subsystems` — owns SUBSYSTEMS.md and subsystems/
- `g-skl-constraints` — owns CONSTRAINTS.md
- `g-pcac-status` — PCAC topology view (required for L4)
