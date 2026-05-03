---
name: g-skl-release
description: Own and manage all release data — RELEASES.md index and releases/ individual files. Operations: CREATE new release, ASSIGN tasks to a release, STATUS summary, PUBLISH ROADMAP.md, ACCELERATE target dates with cascading shift to subsequent planned releases.
---
# g-release

**Files Owned**: `.gald3r/RELEASES.md`, `.gald3r/releases/release{NNN}_*.md`

**Activate for**: "create release", "new release", "assign to release", "release status", "publish roadmap", "accelerate release", "pull release forward", "ship status", "release target date".

**Hierarchy**: `RELEASES.md` is the index. Each `releases/release{NNN}_{slug}.md` moves through: `planned → in_progress → released` (or `→ deferred`).

**Tier**: Ships in `gald3r_template_full/` and `gald3r_template_adv/` — slim projects do not manage release scheduling.

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

## File Placement (10-target propagation)

Per C-009, this skill exists in all 10 IDE targets:
- `.cursor/skills/g-skl-release/SKILL.md`
- `.claude/skills/g-skl-release/SKILL.md`
- `.agent/skills/g-skl-release/SKILL.md`
- `.codex/skills/g-skl-release/SKILL.md`
- `.opencode/skills/g-skl-release/SKILL.md`
- `gald3r_template_full/.cursor/skills/g-skl-release/SKILL.md` ← canonical source
- `gald3r_template_full/.claude/skills/g-skl-release/SKILL.md`
- `gald3r_template_full/.agent/skills/g-skl-release/SKILL.md`
- `gald3r_template_full/.codex/skills/g-skl-release/SKILL.md`
- `gald3r_template_full/.opencode/skills/g-skl-release/SKILL.md`

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

---

## Related Skills

- `g-skl-tasks` — task creation + release_id backlink when ASSIGN runs
- `g-skl-features` — features referenced in release `features:` field
- `g-skl-project` — reads project identity + tier config from `.gald3r/.identity`
- `g-skl-medic` — L2 diagnosis may surface releases whose `tasks:` point to missing task files
