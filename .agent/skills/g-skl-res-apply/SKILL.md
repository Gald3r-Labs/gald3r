---
name: g-skl-res-apply
version: 1.1.0
description: >
  Convert a reverse-spec FEATURES.md (produced by g-skl-res-deep) into gald3r
  artifacts: project goals, PRDs, subsystem specs (merge or create), and tasks.
  Vault-aware — reads from {vault}/research/recon/{slug}/FEATURES.md when a
  shared vault is configured, else falls back to local research/harvests/{slug}/FEATURES.md.
  This is the "Execute" layer in the Discover → Curate → Execute harvest pipeline.
triggers:
  - g-res-apply
  - g-harvest-intake
  - "harvest intake"
  - "apply harvest"
  - "apply recon"
  - "convert features"
  - "intake reverse-spec"
input: "{recon_base}/{slug}/FEATURES.md"   # vault-aware — see Path Resolution below
outputs:
  - .gald3r/PROJECT.md (goals section appended)
  - .gald3r/features/prdNNN_*.md (one per category)
  - .gald3r/FEATURES.md (updated index)
  - .gald3r/SUBSYSTEMS.md (new or merged rows)
  - .gald3r/subsystems/{name}.md (new spec files)
  - .gald3r/TASKS.md (new task rows)
  - .gald3r/tasks/taskNNN_*.md (one per feature group)
---

# g-skl-res-apply (harvest-intake)

## Purpose

`g-skl-res-apply` is the **companion execution skill** to `g-skl-res-deep`.

`g-skl-res-deep` writes nothing to `.gald3r/` — it produces structured `FEATURES.md` reports for human review.

`g-skl-res-apply` is the **execution layer**: it reads a `FEATURES.md`, groups features into coherent gald3r artifacts, and writes them to the project. It is called after the human has reviewed and approved features (changing their status to `[✅]`).

It can also run in `--mode=all` to intake every feature regardless of approval status — useful when doing a first-pass intake of a freshly-generated report.

---

## Vault-Aware Input Path (T081)

Like `g-skl-res-deep` and `g-skl-res-review`, this skill resolves the recon base path from `.gald3r/.identity` before reading input.

### Path resolution (per C-003)

```
1. Read .gald3r/.identity (key=value, no quotes)
2. Extract vault_location=
3. If vault_location is {LOCAL} or missing:
     recon_base  = "research/harvests/"
     index_path  = "research/harvests/_recon_index.yaml"
4. Else:
     recon_base  = f"{vault_location}/research/recon/"
     index_path  = f"{vault_location}/research/recon/_recon_index.yaml"
5. input_path = f"{recon_base}{slug}/FEATURES.md"
```

### Dedup pre-flight

Before doing expensive work, consult `_recon_index.yaml`:

```
1. Resolve index_path
2. If entry for {slug} exists and status == complete and
   (today - last_run) <= max_age_days (default 30):
     proceed — the recon is known-good and current
3. Else if entry exists but is stale:
     warn: "[STALE: {slug}] — recon is older than {max_age_days} days; continue anyway? (y/N)"
     user confirms or bail
4. Else (no entry found):
     warn: "No dedup entry for {slug}. FEATURES.md may be ad-hoc. Continue? (y/N)"
     user confirms or bail
```

`--max-age-days N` overrides the staleness threshold (default 30). `--force` skips the dedup check entirely.

### Updating the dedup index

After APPLY completes, update the existing `_recon_index.yaml` entry with `status: applied` and the most recent `last_run` unchanged (applying does not invalidate the recon). If `features_approved` is tracked per entry, update the count.

---

## Core Rules

1. **Never overwrite** — always append. Existing PRDs, tasks, and subsystems are never modified.
2. **Detect before creating** — check SUBSYSTEMS.md before creating a new subsystem spec. If an existing subsystem is 70%+ overlapping in scope, merge the new features into it.
3. **Group features into tasks** — do NOT create one task per feature. Group related features within a category into a single coherent task (aim for 3-8 features per task).
4. **Extract goals from `enables:`** — the `enables:` array in each feature often contains project-level goal language. Distill these into goal entries.
5. **PRD per category** — create one PRD file per feature category.
6. **Never filter** — if a feature is approved, intake it exactly as specified.
7. **Source references** — every task file must include the `source_files:` from the feature's `FEATURES.md` entry.
8. **Vault-first reads** (T081) — respect `vault_location`; never hardcode `research/harvests/` when a shared vault is configured.

---

## When to Use

Use `g-skl-res-apply` when:

- You have a completed `FEATURES.md` from `g-skl-res-deep` and want to generate tasks/PRDs
- A reverse-spec analysis has been reviewed and features have been approved
- You want to do a full intake of ALL features from a harvest (no approval filter)
- You want a dry-run preview of what would be created before committing

---

## Operations

### REVIEW

```
g-res-apply REVIEW {slug}
```

Reads `{recon_base}{slug}/FEATURES.md` (vault-aware) and outputs a structured summary:

- Feature count by category and approval status (`[ ]`, `[✅]`, `[❌]`)
- Subsystem candidates and whether they exist in SUBSYSTEMS.md (MERGE vs NEW)
- PRDs that would be created
- Estimated task count
- Goals that would be extracted (preview only)
- **Dedup status** of `{slug}` in `_recon_index.yaml`

Does NOT write anything.

---

### APPLY

```
g-res-apply APPLY {slug} [--mode=approved|all|category:{cat}] [--max-age-days N] [--force]
```

Full intake. Creates all gald3r artifacts for the selected features.

**Mode options:**
- `--mode=approved` (default) — only features with `status: "[✅]"`
- `--mode=all` — all features regardless of status
- `--mode=category:CHARACTER_SYSTEM` — only features in a specific category

**Steps (in order):**

#### Step 1 — Dedup pre-flight + Read FEATURES.md
- Resolve `{recon_base}` and `input_path` (see Path Resolution above)
- Consult `_recon_index.yaml` for the slug (see Dedup pre-flight above)
- Load `input_path`
- Parse frontmatter YAML: target_name, features[], subsystem_candidates
- Filter features by mode

#### Step 2 — Extract Project Goals
- For each feature, read `enables:` array
- Identify enables entries that describe project-level outcomes
- Group by theme → propose 1-3 new project goals
- Append to `PROJECT.md` under `## Goals` only if not already present (fuzzy match)

#### Step 3 — Subsystem Detection and Creation
For each `subsystem_candidates` entry in FEATURES.md frontmatter:
1. Read `.gald3r/SUBSYSTEMS.md`
2. Check existing subsystems for name, description, and location overlap
3. **If 70%+ overlap** → mark as MERGE (add `## Absorbed From` entry)
4. **If <30% overlap** → create NEW subsystem spec at `.gald3r/subsystems/{slug}.md`
5. **If 30-70% overlap** → flag for human review

New subsystem spec format:
```markdown
---
name: "{subsystem-name}"
status: planned
description: "{from subsystem_candidates}"
source: "recon/{slug}"
created_date: YYYY-MM-DD
dependencies: []
dependents: []
locations:
  skills: []
  services: []
  data_stores: []
  files: []
---

# {Subsystem Name}

## Description
{from subsystem_candidates}

## Features Mapped
{list of feature IDs from this subsystem's category}

## Absorbed From
*(none)*

## Activity Log

| Date | Action | Agent | Notes |
|------|--------|-------|-------|
| YYYY-MM-DD | Created | res-apply | Source: {slug} |
```

Update SUBSYSTEMS.md registry row for each new subsystem.

#### Step 4 — Create PRDs
Group features by `category`. For each category with ≥2 approved features:

1. Assign next available Feature ID
2. Create `features/prd{NNN}_{slug}_{category_slug}.md`
3. Update FEATURES.md index

PRD file format:
```markdown
---
id: prd{NNN}
title: '{Target} — {Category} Integration'
source: recon/{slug}
category: {category}
status: draft
created_date: YYYY-MM-DD
feature_ids: [F-001, F-002, ...]
---

# PRD: {Target} — {Category} Integration

## Source
Harvested from `{target_name}` via `g-skl-res-deep` analysis.
Feature IDs: {comma-separated list}

## Problem Statement
{Synthesized from feature descriptions}

## Proposed Features
...

## Acceptance Criteria
{Generated from enables[] across all features in this category}

## Out of Scope
{Features marked [❌] in this category}
```

#### Step 5 — Create Tasks
Group features within each category into task clusters (3-8 features per task).

For each task cluster:
1. Assign next sequential task ID
2. Create `tasks/task{NNN}_{slug}_{group_slug}.md`
3. Add row to TASKS.md under appropriate subsystem header

#### Step 6 — Update `_recon_index.yaml`
- Change entry's `status` to `applied`
- Update `features_approved` count if tracked

#### Step 7 — Write Intake Report
Create `{recon_base}{slug}/INTAKE_REPORT.md`:

```markdown
# Recon Intake Report — {target_name}

**Date**: YYYY-MM-DD
**Mode**: {approved|all|category:X}
**Features processed**: N / total
**Source path**: {input_path}
**Vault mode**: shared | local

## Created

### Goals Added: N
{list}

### PRDs Created: N
{list}

### Subsystems
- **New**: {list}
- **Merge**: {list with → target subsystem}
- **Flagged for review**: {list}

### Tasks Created: N
{list with feature IDs}

## Skipped
{features with [❌] status and reason}

## Manual Review Required
{subsystems with 30-70% overlap that weren't auto-resolved}
```

#### Step 8 — Log
Append to `{vault}/log.md` (or `research/log.md`):
```
| {YYYY-MM-DD} | recon-applied | {slug} | g-skl-res-apply (features={N_approved}, tasks={N_tasks}) |
```

---

### DRY-RUN

```
g-res-apply DRY-RUN {slug} [--mode=approved|all]
```

Runs the full APPLY logic but writes nothing. Outputs only the INTAKE_REPORT.md preview to stdout.

---

## Subsystem Merge Detection

Before creating a new subsystem, run this check against SUBSYSTEMS.md:

```
For each candidate subsystem (from FEATURES.md subsystem_candidates):
  1. Extract key terms from slug + description
  2. For each existing subsystem row in SUBSYSTEMS.md:
     a. Count term overlap
     b. Check if candidate features' source_files overlap with subsystem's locations:
  3. Score:
     - Slug match (exact or root): +40
     - Description term overlap ≥3 terms: +30
     - source_files overlap with subsystem locations: +20 per overlapping path
     - Same category prefix: +10
  4. Score ≥70 → MERGE recommendation
     Score 30-69 → flag for human review
     Score <30 → create new
```

---

## Task Grouping Algorithm

1. Sort features by category
2. Within each category, cluster by:
   - Shared `source_files` prefix (same module → same cluster)
   - Shared subsystem slug
   - Sequential pipeline stages
3. Target cluster size: 3-8 features
4. Max cluster size: 10 (split if exceeded)
5. Single-feature categories → standalone task

---

## Large Harvest Handling (>50 features)

For harvests with >50 approved features:
1. Process categories in alphabetical order
2. Create all subsystems first, then PRDs, then tasks
3. Write TASKS.md entries only after ALL task files are created
4. Write INTAKE_REPORT.md last
5. Log progress every 10 tasks

---

## Integration with g-skl-res-deep

The full harvest pipeline is:

```
g-res-deep ANALYZE {path} --depth thorough
    → {recon_base}{slug}/FEATURES.md (features all [ ])
    → _recon_index.yaml entry (status: complete)

[Human reviews FEATURES.md, sets [✅]/[❌] on features]

g-res-apply REVIEW {slug}
    → preview of what would be created

g-res-apply APPLY {slug} --mode=approved
    → .gald3r/ artifacts created
    → {recon_base}{slug}/INTAKE_REPORT.md
    → _recon_index.yaml entry (status: applied)
```

---

## Examples

```
# Review what would be created from maestro2 recon (uses vault path if configured)
g-res-apply REVIEW maestro2

# Dry-run all features
g-res-apply DRY-RUN maestro2 --mode=all

# Apply only approved features
g-res-apply APPLY maestro2 --mode=approved

# Force apply even if recon is stale
g-res-apply APPLY maestro2 --max-age-days 0
```

---

## See Also
- `g-skl-res-deep` — Produces the `FEATURES.md` this skill consumes (vault-aware writer)
- `g-skl-res-review` — Review-style harvests; same vault-aware path + dedup; includes topology routing
- `g-skl-tasks` — Owns TASKS.md and tasks/
- `g-skl-subsystems` — Owns SUBSYSTEMS.md and subsystems/
- `g-skl-plan` — Owns PLAN.md and features/
- `g-skl-project` — Owns PROJECT.md goals

---

## Cross-Project APPLY (T118)

When `g-skl-res-review` has assigned routing suggestions, `g-skl-res-apply` can write artifacts directly to linked projects.

### `--target {project-slug}` Flag

```
g-res-apply APPLY {slug} --target gald3r_valhalla
g-res-apply APPLY {slug} --target gald3r_valhalla --mode=approved
```

**Behavior when `--target` is set:**

1. **Resolve target project path** from `.gald3r/linking/link_topology.md`:
   - Search `children[]` for matching `project_name`
   - If not found: error: `"Unknown target '{slug}' — not in link_topology.md children"`
   - If found but path not accessible: fall back to PCAC INFO notification (see below)

2. **Check target's CONSTRAINTS.md** — read `{target_path}/.gald3r/CONSTRAINTS.md`:
   - If any constraint explicitly prohibits the feature's subsystem → flag as violation: `"⚠️ AC would violate {target_slug} constraint C-{id}: {title}"`
   - User confirms override or skip

3. **Write artifacts to target project** — same as standard APPLY but with all paths prefixed with `{target_path}/`:
   - `{target_path}/.gald3r/PROJECT.md`
   - `{target_path}/.gald3r/features/`
   - `{target_path}/.gald3r/FEATURES.md`
   - `{target_path}/.gald3r/TASKS.md`
   - `{target_path}/.gald3r/tasks/`
   - `{target_path}/.gald3r/SUBSYSTEMS.md`
   - `{target_path}/.gald3r/subsystems/`

4. **Send PCAC INFO notification** to target project INBOX (`{target_path}/.gald3r/linking/INBOX.md`):
   ```
   [INFO] g-res-apply APPLY from gald3r_dev: {N} features applied from {slug} harvest.
   Review: {target_path}/.gald3r/tasks/ for new task files.
   Routing: features in [{domain_tags}] tagged for this project.
   ```

5. **Log to current project** — append to `research/log.md`:
   ```
   | {YYYY-MM-DD} | recon-applied-remote | {slug} → {target_slug} | g-skl-res-apply (features={N}) |
   ```

### `--split` Mode (Interactive Multi-Target)

```
g-res-apply APPLY {slug} --split
```

Interactive routing mode. For each feature group from the harvest:

1. Display the routing suggestion from `g-skl-res-review` (if available)
2. Ask: `"Route [{category}: {N} features] to: (this-project / {peer_slugs} / new-project / skip)"`
3. User types target or presses Enter to accept suggestion
4. After all confirmations, execute APPLY for each target group:
   - Current project features → standard APPLY
   - Remote project features → APPLY --target {slug} per target
5. Summary printed at end:
   ```
   SPLIT APPLY complete:
   → this-project: 5 features (feat-090, feat-091, ...)
   → gald3r_valhalla: 3 features (feat-040, feat-085, ...)
   → gald3r_agent: 2 features (feat-029, ...)
   ⚡ new-project suggested: 1 feature (needs real-time-transport capability)
   ```

### Fallback: Target Not Locally Accessible

If the target project path doesn't exist on disk:

1. Queue the APPLY as a **pending PCAC order** in `.gald3r/linking/pending_orders/`
2. Create `pending_orders/order_{timestamp}_{target_slug}.md` with the full feature list
3. Print: `"⏳ {target_slug} not accessible locally — queued as pending order. Deliver via @g-pcac-order when target is reachable."`

### Examples

```bash
# Apply all approved features to gald3r_valhalla (backend project)
g-res-apply APPLY hermes-agent__nousresearch --target gald3r_valhalla --mode=approved

# Interactive split across multiple projects
g-res-apply APPLY hermes-agent__nousresearch --split

# Dry-run to preview split routing before committing
g-res-apply DRY-RUN hermes-agent__nousresearch --split

# Apply to target with constraint check bypass
g-res-apply APPLY hermes-agent__nousresearch --target gald3r_valhalla --force
```
