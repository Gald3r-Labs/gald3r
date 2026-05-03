---
name: g-skl-features
description: Own and manage all feature data — FEATURES.md index, features/ individual files, staging lifecycle (staging→specced→committed→shipped), harvest source collection, and feature promotion. Single source of truth for everything feature-related.
---
# g-features

**Files Owned**: `.gald3r/FEATURES.md`, `.gald3r/features/**/*.md` (flat `featNNN_*.md` and nested `.../featNNN_*.md`)

**Activate for**: "stage a feature", "new feature", "collect approach", "promote feature", "rename feature", "feature status", "spec this feature", "what features do we have", "harvest collected approaches".

**Hierarchy**: `FEATURES.md` is the index. Each feature file moves through: `staging → specced → committed → shipped`.

**Path resolver**: treat any `.md` under `.gald3r/features/` whose basename matches `feat-\d+` as a feature file. Do not assume only `.gald3r/features/featNNN_slug.md`.

---

## Feature YAML Schema

```yaml
---
id: feat-NNN
title: 'Feature Title'
status: staging          # staging | specced | committed | shipped
goal: ''                 # optional: G-NN from PROJECT.md goals
min_tier: slim           # slim | full | adv
subsystems: []           # list of subsystem names this feature touches
harvest_sources: []      # source slugs/paths that contributed approaches
created_date: 'YYYY-MM-DD'
promoted_date: ''        # date moved from staging → specced
committed_date: ''       # date first task created (specced → committed)
completed_date: ''       # date last task verified (committed → shipped)
# Optional hierarchy (Task 514) — flat files without these fields remain valid:
parent_feature: ''      # feat-NNN id of parent capability (must exist when set)
feature_area: ''        # logical grouping (e.g. platform, gald3r_backend); may mirror folder prefix
depth: 0                # optional path depth under features/; when set, must match folder depth
children: []            # explicit child feat- ids (auditability; do not infer only from folders)
# Optional — only present when this feature gates on a cross-project order:
cross_project_ref:
  - order_id: "ord-abc123"          # links to .gald3r/linking/sent_orders/order_*.md
    project: "child_project_id"
    remote_task_title: "Implement JWT auth endpoint"
    status: in-progress             # cached from last sync; updated by g-skl-pcac-read
    last_synced: "YYYY-MM-DD"
---
```

**`cross_project_ref:` semantics**:
- Optional field. Missing or empty list = no cross-project dependency.
- Populated when the feature requires work in a child/sibling project that was dispatched via `@g-pcac-order`.
- Each entry's `status` is a cached snapshot — the authoritative status lives in the matching `.gald3r/linking/sent_orders/order_*.md` ledger record.
- `g-skl-pcac-read` updates the cached `status` and `last_synced` automatically when a `broadcast_completion` ping arrives from the remote project.
- Session start (`g-rl-25`) and `@g-pcac-status` surface features with at least one entry where `status` is not `completed` as externally-gated.

### Hierarchy validation (dry-run, no writes)

Run from repo root:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/gald3r_feature_hierarchy_sync.ps1 -ProjectRoot .
```

Detects duplicate `id:` values, missing `parent_feature` targets, stale `children:` entries, and `depth:` vs folder mismatches. Use `-WarnOnly` for advisory exit code 0; `-Json` for machine-readable output.

### Migration: flat → nested (non-destructive)

1. Prefer `git mv` so history follows the file: e.g. `.gald3r/features/featNNN_x.md` → `.gald3r/features/<area>/featNNN_x.md`.
2. Set optional `feature_area`, `parent_feature`, `children`, and `depth` in frontmatter after the move.
3. Update `FEATURES.md` link column to the new relative path (ID `feat-NNN` stays stable).
4. Do not delete superseded paths; if splitting one feature into two files, keep provenance in the child `## Summary` and optionally leave a one-line stub file at the old path pointing to the successor (human decision — not required for `git mv`).

**Feature body sections**:
- `## Summary` — 1-3 sentences: what user-visible capability this delivers
- `## Collected Approaches` — table of approaches gathered from harvest tools, research, discussions
- `## Potential Deliverables` — bullet list of candidate outputs (filled during staging)
- `## Draft Tasks` — task stubs (NOT in TASKS.md yet — populated when promoting to specced)
- `## Acceptance Criteria` — formal ACs (filled when status moves to specced)
- `## Design Session Notes` — optional: key decisions, architecture notes, conversation references

---

## Operation: STAGE (create new staging feature)

**Usage**: `STAGE "Feature Title" [--goal G-NN] [--tier slim|full|adv] [--from-harvest path] [--area kebab/sub/path]`

1. **Determine next feat ID**: scan **all** `.gald3r/features/**/*.md` matching `feat-\d+` in the basename — highest `feat-NNN` wins → next = highest + 1 (do not read only the flat folder).

2. **Scope check** (ask unless `--from-harvest` provided):
   - What user-visible capability does this enable?
   - Which goal does this connect to? (optional)
   - Any approaches already identified?

3. **Create feature file** at `.gald3r/features/featNNN_descriptive_slug.md` **or**, when `--area platform/onboarding` (example) is supplied, `.gald3r/features/platform/onboarding/featNNN_descriptive_slug.md` (create intermediate directories). Set YAML `feature_area:` to the area string and `depth:` to the number of path segments under `features/`.
   ```yaml
   ---
   id: feat-NNN
   title: 'Feature Title'
   status: staging
   goal: ''
   min_tier: slim
   subsystems: []
   harvest_sources: []
   created_date: 'YYYY-MM-DD'
   promoted_date: ''
   committed_date: ''
   completed_date: ''
   ---

   # Feature: {title}

   ## Summary
   [1-3 sentence description]

   ## Collected Approaches
   <!-- populated by COLLECT operation and harvest tools -->

   | Source | Approach | Complexity | Notes |
   |--------|----------|------------|-------|

   ## Potential Deliverables
   - (none yet)

   ## Draft Tasks
   <!-- populated manually during spec review — NOT in TASKS.md until PROMOTE -->
   - [ ] Task: description

   ## Acceptance Criteria
   <!-- filled in when status moves to specced -->
   ```

4. **Add to FEATURES.md** index under `### Staging` section:
   ```
   | [feat-NNN](features/featNNN_slug.md) | Title | staging | — | Notes |
   ```

5. **Output**: confirm `feat-NNN created: .gald3r/features/featNNN_slug.md`

---

## Operation: COLLECT (append approach to staging feature)

**Usage**: `COLLECT feat-NNN --source "Source Name" --approach "description" [--complexity low|medium|high] [--harvest-path path/to/harvest]`

Appends a new row to the feature's `## Collected Approaches` table. Does NOT create tasks. Does NOT overwrite existing rows.

1. Read the target feature file — confirm `status: staging` (warn if specced/committed, but still allow)
2. Append to the `## Collected Approaches` table:
   ```
   | Source Name | Approach description | medium | Optional notes |
   ```
3. If `--harvest-path` provided AND not already in `harvest_sources:` YAML array → append it
4. Write updated file
5. Output: `Added approach to feat-NNN: "Source Name — Approach description"`

**Fuzzy match** (used by harvest tools): when a harvest discovers a capability, call COLLECT with a candidate feature name. If `name similarity ≥ 70%` to an existing staging feature, prompt: `"This looks like feat-NNN '{{title}}' — add as approach? [y/n]"`. If no match, suggest STAGE instead.

---

## Operation: SPEC (staging → specced)

**Usage**: `SPEC feat-NNN`

Promotes a staging feature to specced status — formalizes requirements.

1. Read the feature file
2. Review `## Collected Approaches` with user — confirm direction
3. **Fill in**:
   - `## Acceptance Criteria` (formal, measurable ACs)
   - Update `## Draft Tasks` with refined task list
   - Update `subsystems:` YAML field
4. Update YAML: `status: specced`, `promoted_date: YYYY-MM-DD`
5. Update FEATURES.md: move row from `### Staging` → `### Specced` section
6. Output: `feat-NNN promoted to specced: ready for PROMOTE when tasks are confirmed`

---

## Operation: PROMOTE (specced → committed, interactive task creation)

**Usage**: `PROMOTE feat-NNN`

Converts a specced feature into active TASKS.md work. Human-driven — does NOT auto-generate tasks.

1. Read feature file — must be `status: specced`
2. Display `## Draft Tasks` list as starting suggestions
3. For each draft task, ask: `"Create task for: '{{description}}'? [y/n/edit]"`
   - `y` → create task via `g-skl-tasks CREATE TASK` (gets a TASK-NNN ID)
   - `edit` → prompt for revised description before creating
   - `n` → skip (task stays in Draft Tasks as a note)
4. Update YAML: `status: committed`, `committed_date: YYYY-MM-DD`
5. Add `features: [feat-NNN]` to each created task's YAML
6. Update FEATURES.md: move row from `### Specced` → `### Committed`; populate Tasks column
7. Output: `feat-NNN committed: N tasks created (TASK-X, TASK-Y, ...)`

---

## Operation: RENAME (rename slug + title)

**Usage**: `RENAME feat-NNN "New Title"`

Safe rename — preserves all data, updates all references.

1. Read feature file — resolve by **ID** using the hierarchy resolver (nested or flat path)
2. Derive new slug: lowercase, hyphens, max 40 chars (e.g., `feat-036_new_feature_name.md`)
3. Rename file: `git mv` from old slug to new slug
4. Update YAML `title:` field
5. Update `FEATURES.md` index: find `feat-NNN` row → update title + link
6. Scan `tasks/` files for `features: [feat-NNN]` — the ID is stable, only the path changes; update path references if any
7. Output: `feat-NNN renamed: 'Old Title' → 'New Title' (featNNN_new_slug.md)`

---

## Operation: STATUS (list features by status)

**Usage**: `STATUS [--status staging|specced|committed|shipped] [--tier slim|full|adv] [--goal G-NN]`

Reads `FEATURES.md` and outputs a summary.

```
FEATURES STATUS
───────────────────────────────────────
Staging (N)
  feat-NNN  Title                  [slim] → G-01
  ...

Specced (N)
  feat-NNN  Title                  [full]
  ...

Committed (N)
  feat-NNN  Title                  [adv]  → TASK-X, TASK-Y
  ...

Shipped (N)
  feat-NNN  Title
  ...
───────────────────────────────────────
Total: N features | N staging | N specced | N committed | N shipped
Next feat ID: feat-NNN
```

Filters apply to limit output. `--status staging` shows only staging features.

---

## FEATURES.md Index Structure

Maintain a **Feature hierarchy** section (after lifecycle tables) that groups rows by top-level folder under `features/` (use `_flat_root` for files sitting directly in `features/`) and by `status`. Nested and flat files use the same row shape: `| [feat-NNN](relative/path/from/features/) | ... |`.

```markdown
# FEATURES.md — {project_name} Feature Registry

## Overview
Features are user-visible capabilities moving through the staging pipeline.

### Feature Lifecycle
IDEA → [staging] → [specced] → [committed] → [shipped]

| Status   | Meaning |
|----------|---------|
| staging  | Research phase — collecting approaches, ideas, potential deliverables |
| specced  | Formal requirements written — acceptance criteria defined |
| committed| Active tasks created in TASKS.md — being coded |
| shipped  | Fully implemented and verified |

## Features Index

### Shipped
| ID | Title | Status | Tasks | Notes |

### Committed
| ID | Title | Status | Tasks | Notes |

### Specced
| ID | Title | Status | Notes |

### Staging
| ID | Title | Status | Notes |

---
**Last Updated**: YYYY-MM-DD
**Next feat ID**: feat-NNN
```

---

## ID Sequencing Rules

- Feature IDs are globally sequential: `feat-001`, `feat-002`, ... `feat-NNN`
- Never reuse a retired ID
- Old PRD files migrated to features retain high-range IDs (e.g., `feat-001` through `feat-035` were migrated PRDs)
- New features created post-migration start at `feat-036` (or next available after highest in FEATURES.md)
- Harvest consolidation features use `feat-101` through `feat-119` range (reserved for Maestro2/gald3r_forge)
- Tier/release architecture features use `feat-120`–`feat-129` range (reserved for tier/release work)

---

## Integration Points

**With `g-skl-harvest`**: harvest APPLY calls `COLLECT` on matching staging features instead of creating tasks directly.

**With `g-skl-reverse-spec`**: APPLY operation calls `COLLECT` or `STAGE` depending on whether a matching staging feature exists.

**With `g-skl-tasks`**: PROMOTE calls `CREATE TASK` for each confirmed task; tasks get `features: [feat-NNN]` back-reference.

**With `g-skl-plan`**: PLAN.md Deliverable Index references feat-NNN IDs for strategic features.

**With `g-skl-medic`**: upgrade detection — finds projects with `prds/` folder and no `features/` → offers migration.

---

## Cross-Project Split Check on STAGE (T119)

When **STAGE** is invoked (after step 2 scope check, before writing the file), perform a topology split check identical to the one in `g-skl-tasks` CREATE — but applied to the feature being staged.

### Split Check Steps

```
1. Load topology from .gald3r/linking/link_topology.md (if exists)
2. Extract domain tags from feature title + summary
3. Cross-check domains against peer capabilities
4. If a domain belongs to another project → suggest split or cross-project staging
5. If a domain has no owner → suggest spawn
```

### Feature Split Suggestion Format

```
⚡ TOPOLOGY CHECK: This feature spans domains that may belong elsewhere:

  Domain "frontend" → gald3r_frontend owns this capability
  Domain "real-time" → no project owns this — consider spawning

Options:
  [1] Stage here (single-project feature)
  [2] Stage as cross-project feature with cross_project_ref slug
  [3] Stage cross-project + spawn new project for unowned capability
  [s] Skip topology check

Choice [1/2/3/s]:
```

### Cross-Project Feature Staging (Option 2 or 3)

When user confirms cross-project staging, add `cross_project_ref:` to the feature YAML:

```yaml
---
id: feat-NNN
title: 'Feature Title'
status: staging
goal: ''
min_tier: slim
subsystems: []
harvest_sources: []
cross_project_ref: "domain-feature-slug"   # shared canonical name across participating projects
participating_projects:
  - "this-project-slug"
  - "gald3r_frontend"
created_date: 'YYYY-MM-DD'
promoted_date: ''
committed_date: ''
completed_date: ''
---
```

Then send a **`[BROADCAST]` INBOX notification** to each participating peer project:

```
[BROADCAST] New cross-project feature staged: "{title}"
cross_project_ref: "domain-feature-slug"
This project is co-owner. Stage your slice in your features/ to track progress.
Originator: {this-project-slug}
```

### `cross_project_ref` Slug Convention

- Format: `{primary-domain}-{short-description}` (kebab-case, max 40 chars)
- Examples: `auth-unified-login`, `data-pipeline-etl`, `frontend-dashboard-v2`
- ALL participating projects must use the **identical** slug string
- `g-pcac-status` displays cross-project features grouped by their `cross_project_ref` slug

### `cross_project_ref` Status Tracking

When `g-skl-features STATUS` is called and any features have `cross_project_ref`:

```
📡 Cross-Project Features:
  "auth-unified-login"
    → gald3r_dev:     [committed] feat-090
    → gald3r_frontend: [staging]   feat-012 (last sync: 2026-04-18)
    → gald3r_valhalla: [specced]   feat-047 (last sync: 2026-04-20)
```

Peer statuses are cached from the last PCAC sync; `[unknown]` if never synced.
