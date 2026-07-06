---
name: g-skl-release
description: Own and manage all release data — RELEASES.md index and releases/ individual files. Operations: CREATE new release, ASSIGN tasks to a release, STATUS summary, PUBLISH ROADMAP.md, ACCELERATE target dates with cascading shift to subsequent planned releases, SYNC reconcile CHANGELOG entries against release records (C-023).
token_budget: medium
subsystem_memberships: [RELEASE_AND_VERSIONING]
---
# g-release

**Files Owned**: `.gald3r/RELEASES.md`, `.gald3r/releases/release{NNN}_*.md`

**Activate for**: "create release", "new release", "assign to release", "release status", "publish roadmap", "accelerate release", "pull release forward", "ship status", "release target date".

**Hierarchy**: `RELEASES.md` is the index. Each `releases/release{NNN}_{slug}.md` moves through: `planned → in_progress → released` (or `→ deferred`).

**Tier**: Ships in `<template_full>` and `<template_adv>` external repos — slim projects do not manage release scheduling.

---

## Release YAML Schema

```yaml
---
id: 1                         # Sequential release ID (integer)
name: 'v1.1 — Spring Drop'    # Human-readable release name
version: '1.4'              # SemVer version string
target_date: '2026-04-23'     # Planned ship date (YYYY-MM-DD)
status: planned                # planned | in_progress | released | deferred
cadence_days: 14               # Days between releases (default: 14)
features: []                   # Feature IDs or descriptions in this release
tasks: []                      # Task IDs assigned (e.g., [42, 55, 61])
notes: ''                      # Freeform notes
created_date: '2026-04-19'
released_date: ''              # Filled when shipped
---
```

**Body sections** (after frontmatter):
- `## Included Features` — bullets referencing `feat-NNN` IDs
- `## Included Tasks` — bullets referencing task IDs
- `## Release Notes` — freeform copy that feeds CHANGELOG.md on ship
- `## Blockers` — known risks or dependencies

---

## Operation: CREATE (new release)

**Usage**: `CREATE "Release Name" [--version X.Y.Z] [--target YYYY-MM-DD] [--cadence N]`

1. **Determine next release ID**: read `RELEASES.md` index — find highest `id` → next = highest + 1
2. **Determine target_date**:
   - If `--target` provided → use that
   - Else → find most-recent `target_date` in `RELEASES.md` → next = that + `cadence_days` (default 14)
   - If no prior release exists → next = today + `cadence_days`
3. **Determine cadence**: use `--cadence` if provided, else inherit project default (14)
4. **Slug**: lowercase, hyphen-separated short version of name (first 3-4 words)
5. **Write file** at `.gald3r/releases/release{NNN:03d}_{slug}.md` (zero-padded ID) with full frontmatter and body skeleton
6. **Append index row** to `RELEASES.md` table:
   ```
   | NNN | {name} | {version} | {target_date} | planned | [] |
   ```
7. **Confirm**: `✅ Release {NNN} created — target {target_date} (cadence {N}d)`

---

## Operation: ASSIGN (add tasks to a release)

**Usage**: `ASSIGN <release_id> <task_id>[,<task_id>...]`

1. **Locate release file**: `releases/release{NNN:03d}_*.md`
2. **Parse task IDs**: comma-separated list, trim whitespace, skip duplicates
3. **Update frontmatter**: merge new IDs into `tasks:` list (de-duplicated, sorted numerically)
4. **Update body**: refresh `## Included Tasks` bullets from the new `tasks:` list
   - For each task ID, read `.gald3r/tasks/task{id}_*.md` → extract title from frontmatter `title:` field
   - Render bullet: `- Task {id}: {title}`
5. **Update RELEASES.md row**: refresh the `Tasks` column with the comma-separated ID list
6. **Reverse link**: write `release_id: {NNN}` to each task file's frontmatter — skip silently if already set or if task file not found
7. **Confirm**: `✅ Assigned {N} task(s) to release {NNN} — total {M} tasks`

---

## Operation: STATUS (release summary)

**Usage**: `STATUS [release_id_or_name]`

**With arg** (specific release):
1. Load release file
2. Render table:
   ```
   Release {NNN} — {name} ({version})
   Target: {target_date}    ({days_until} days away | N days overdue)
   Status: {status}
   Cadence: {cadence_days} days
   Tasks: {M} assigned — {completed}/{M} completed
     - Task {id}: {title} [{task_status}]
     ...
   Features: {F} listed
   Blockers: {count from blockers body section}
   ```
3. Task status derived from `.gald3r/tasks/task{id}_*.md` frontmatter `status:`

**Without arg** (all active):
1. Read `RELEASES.md` index
2. Print compact table of all releases with `status ∈ {planned, in_progress}`
3. Highlight overdue releases (target_date < today) with `⚠️`

---

## Operation: PUBLISH (generate ROADMAP.md)

**Usage**: `PUBLISH`

Generates `ROADMAP.md` at the project root. Overwrites cleanly — do not hand-edit; use release files for customization.

1. **Read project name**: from `.gald3r/PROJECT.md` first line or `.gald3r/.identity`
2. **Scan releases/**: collect all `release{NNN:03d}_*.md` files — parse `status`, `target_date`, `name`, `version`, `tasks:` list
3. **Partition**: `planned` → Upcoming; `in_progress` → In Progress; `released` → Released (most recent 3)
4. **Sort**: Upcoming + In Progress by `target_date` ascending; Released by `target_date` descending
5. **For each release**, build section:
   - Header: `### {name} ({version}) — target: {target_date}`
   - Subheader: `*{N} days remaining*` or `*Released {released_date}*`
   - Task table:
     - For each task ID in `tasks:`, read `.gald3r/tasks/task{id}_*.md`:
       - If found: `| {title} | #{id} | {status_emoji} {status} |`
       - If not found: `| Task #{id} | #{id} | Unknown |`
     - Status emoji: ✅ completed, 🔄 in-progress, 📋 pending, ⏸️ paused, ❌ failed

6. **Write output** to `ROADMAP.md` at project root:
   ```markdown
   # Roadmap — {project_name}

   > Generated by gald3r | Last updated: {YYYY-MM-DD} | Run `@g-release-publish` to refresh.

   ---

   ## In Progress

   ### {release_name} ({version}) — target: {target_date}
   *{N} days remaining*

   | Feature / Task | ID | Status |
   |---|---|---|
   | {title} | #{id} | {emoji} {status} |

   ---

   ## Upcoming Releases

   ### {release_name} — target: {target_date}
   ...

   ---

   ## Released

   ### {release_name} ({version}) — released: {released_date}
   ...
   ```

7. **Confirm**: `✅ ROADMAP.md published — {N_in_progress} in progress, {N_upcoming} upcoming, {N_released} released`

---

## Operation: ACCELERATE (pull a release forward, cascade shift)

**Usage**: `ACCELERATE <release_id> (--days N | --date YYYY-MM-DD)`

1. **Load target release**: `releases/release{NNN:03d}_*.md`
2. **Compute new date**:
   - `--date YYYY-MM-DD` → new_date = that date
   - `--days N` → new_date = original_target - N days (positive N = pull forward)
3. **Compute delta**: `delta = new_date - original_target` (negative = acceleration, positive = slip)
4. **Identify cascade scope**: all releases where
   - `status == planned`
   - `target_date > original_target_of_accelerated_release`
5. **Apply cascade**:
   - For each cascaded release → `target_date += delta`
   - Rewrite the release file's frontmatter
   - Update its row in `RELEASES.md` index
6. **Write accelerated release**: update its frontmatter `target_date` and RELEASES.md row
7. **Append cascade note** to the accelerated release's body:
   ```
   ## Schedule Changes

   | Date | Change |
   |------|--------|
   | {today} | Accelerated from {original} to {new} (delta {delta}d); {N} subsequent release(s) shifted. |
   ```
8. **Confirm**:
   ```
   ✅ Release {NNN} accelerated by {abs(delta)} days (→ {new_date})
   Cascaded: {N} subsequent release(s) shifted by the same delta
   ```

**Edge cases**:
- Delta = 0 → no-op, report `Already targeting {date}`
- Accelerated release has status != `planned` → refuse: `Cannot accelerate a release in status '{status}'`
- Cascade would push any release's target_date before `today` → warn but proceed: `⚠️ Release {M} now targets {date} which is in the past — review manually`

---

## Operation: SYNC (reconcile CHANGELOG entries against release records)

**Usage**: `@g-release-sync` or triggered at session start when gap count > 0

**Algorithm**:
1. Read `CHANGELOG.md`, extract all `## [x.x.x]` version headers — skip `## [Unreleased]`
2. Read `.gald3r/RELEASES.md`, collect all `version:` entries from the index table
3. Read `.gald3r/releases/*.md` frontmatter, collect all `version:` fields
4. Report:
   - **Missing release file**: CHANGELOG has `[x.x.x]` but no `.gald3r/releases/` file with matching version
   - **Missing CHANGELOG entry**: `.gald3r/releases/` file exists but CHANGELOG has no matching `## [x.x.x]` header
   - **RELEASES.md gap**: release file exists but `RELEASES.md` index row is missing
5. For each gap, suggest the remediation command:
   - Missing release file → `@g-release-new vX.X.X`
   - Missing CHANGELOG entry → add `## [x.x.x]` section manually or via release publish flow
   - Missing RELEASES.md row → `@g-release-status` to regenerate index

**Output format**:
```
📋 CHANGELOG/Release Sync Check
  ✅ N releases in sync
  ⚠️ M gaps detected:
    - [1.2.0] in CHANGELOG but no .gald3r/releases/ file → run @g-release-new v1.2.0
    - [1.3.1] in .gald3r/releases/ but not in CHANGELOG → add entry manually
    - [1.4.0] release file exists but missing from RELEASES.md → run @g-release-status
```

**Session start surface**: If gap count > 0, g-rl-25 surfaces:
`⚠️ N CHANGELOG version(s) missing release file — run @g-release-sync`

---

## Operation: BACKFILL (create release files for CHANGELOG versions, C-023 / BUG-104)

**Usage**: `@g-release-sync` remediation, `@g-update` upgrade path, or `g-medic --heal-c023`

Where SYNC **reports** the gap, BACKFILL **closes** it: for every `## [X.Y.Z]` CHANGELOG header
that has no matching `.gald3r/releases/` file, create one with `status: released` and the date
parsed from the CHANGELOG header. This is the standard fix for projects that predate the
`releases/` concept (T1416) and therefore see the C-023 warning on every session.

**Script**: `gald3r ship`

```bash
# Dry-run: list which release files would be created
gald3r ship

# Apply: create the missing release files
gald3r ship
```

**Behavior**:
- Backfilled files are named `release{NNN}_v{X}-{Y}-{Z}.md` so the filename contains the version
  (satisfies the g-rl-25 Step 2b "filename contains the version" check) while keeping the
  canonical `release{NNN}_` prefix and a numeric `id:`.
- Sequential `id:` continues from the highest existing release-file id.
- **Idempotent**: a version that already has a release file (by frontmatter `version:`) is skipped.
- Dry-run by default; `-Apply` writes. `-Json` emits a structured result.

---

## Public-Publish History Mode (T423 — carry vs scrub, OFF by default)

When a project publishes/graduates to a **public** repository it must choose how git history is
handled. This is a USER-SAFETY toggle: a destructive history scrub must never be silent or accidental.

| Mode | What it does to history | Default? | Risk |
|------|-------------------------|----------|------|
| `carry` | Keeps full git history on the public repo (incremental commit). | **Yes (safe default)** | None — non-destructive. |
| `scrub` (Mode A) | Publishes with **zero** git history: `git archive` the tree, strip internal dirs, fresh `git init`, single root commit. For IP protection. | No — opt-in only | **DESTRUCTIVE & irreversible** on the public repo: history is replaced and cannot be recovered there. |

**How the mode is chosen (precedence, highest first):**
1. Explicit `-HistoryMode <carry|scrub>` (or engine equivalent) passed to the publish call.
2. `.gald3r/.identity` -> `publish_history_mode=<carry|scrub>` (recorded at `@g-setup` / `--upgrade-existing`, T423 AC2).
3. `agent_config_defaults.publish_history_mode` in the project type (`development.yaml`) — defaults to `carry`.
4. (Deprecated) `test_to_public_history` is read only for back-compat; `publish_history_mode` wins. The
   pre-T423 default of this key was the UNSAFE `scrub`; it is now aligned to `carry`.

**Enforcement contract (publish-time gate — AC3):** the publish/graduation mechanism MUST:
- Print which mode will run and exactly what it does to history **before doing anything** (dry-run states this clearly).
- When the resolved mode is `scrub`, **refuse to proceed without an explicit `-ConfirmScrub`** (or the engine
  equivalent confirmation), and additionally require an interactive `YES` confirmation for a non-dry-run.
- Treat absent/unknown config as `carry` — never default to scrub.

> **Architecture note (T423 / spec_defect):** the historical implementation of this gate lived in
> `g-skl-release/scripts/graduate_to_public.ps1` (Mode A scrub + `-ConfirmScrub`, reading
> `test_to_public_history`). That script is **not present in the live skill tree** (it survives only in
> `._*_bk_20260606` backup dirs), and the bundled gald3r engine exposes **no** `graduate` / `publish-to-public`
> / `scrub` verb (`release.py` is release-records only). So the runtime enforcement point does not currently
> exist live; this section is the authoritative contract any restored or re-implemented publish path MUST
> satisfy. Until then a maintainer publishing publicly does so manually and MUST honor this contract by hand
> (the 2026-05-30 manual `git filter-repo` IP cleanup, BUG-123, is the cautionary precedent).

## File Placement (10-target propagation)

Per C-009, this skill exists in all 10 IDE targets:
- `.cursor/skills/g-skl-release/SKILL.md`
- `.claude/skills/g-skl-release/SKILL.md`
- `.agent/skills/g-skl-release/SKILL.md`
- `.codex/skills/g-skl-release/SKILL.md`
- `.opencode/skills/g-skl-release/SKILL.md`
- `<ECOSYSTEM_ROOT>/<template_full>/.cursor/skills/g-skl-release/SKILL.md` ← canonical source
- `<ECOSYSTEM_ROOT>/<template_full>/.claude/skills/g-skl-release/SKILL.md`
- `<ECOSYSTEM_ROOT>/<template_full>/.agent/skills/g-skl-release/SKILL.md`
- `<ECOSYSTEM_ROOT>/<template_full>/.codex/skills/g-skl-release/SKILL.md`
- `<ECOSYSTEM_ROOT>/<template_full>/.opencode/skills/g-skl-release/SKILL.md`

Propagation: edit canonical copy first, then run `platform_parity_sync.ps1 -Sync` (or copy directly for skill-subdir additions — see D064).

---

## Related Commands

| Command | Operation |
|---------|-----------|
| `@g-release-new` / `/g-release-new` | CREATE |
| `@g-release-assign` / `/g-release-assign` | ASSIGN |
| `@g-release-status` / `/g-release-status` | STATUS |
| `@g-release-publish` / `/g-release-publish` | PUBLISH |
| `@g-release-accelerate` / `/g-release-accelerate` | ACCELERATE |
| `@g-release-sync` / `/g-release-sync` | SYNC |

---

## Related Skills

- `g-skl-tasks` — task creation + release_id backlink when ASSIGN runs
- `g-skl-features` — features referenced in release `features:` field
- `g-skl-project` — reads project identity + tier config from `.gald3r/.identity`
- `g-skl-medic` — L2 diagnosis may surface releases whose `tasks:` point to missing task files
