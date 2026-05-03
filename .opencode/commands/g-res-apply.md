# g-res-apply

Convert an approved recon report into gald3r artifacts (goals, features, subsystems, tasks).

Activates **g-skl-res-apply** → REVIEW, DRY-RUN, or APPLY operation.

> **Replaces**: `@g-harvest-intake` (deprecated alias — prints warning, then calls this)

## Usage

```
@g-res-apply REVIEW {slug}
@g-res-apply DRY-RUN {slug} [--mode=approved|all|category:{cat}]
@g-res-apply APPLY {slug} [--mode=approved|all|category:{cat}]  # all requires clean-room approval for every selected feature
@g-res-apply APPLY {slug} --target {child_project}   # route to a child project (T118)
```

- `{slug}` — the folder name under `vault/research/recon/`, e.g., `maestro2`, `gald3r_forge`

## Operations

### REVIEW
Show what would be created: goals, features, subsystem candidates (MERGE vs NEW vs FLAGGED), and task groupings. Writes nothing.

### DRY-RUN
Full APPLY simulation — no files written. Outputs INTAKE_REPORT.md preview to console.

### APPLY
Creates all gald3r artifacts:

1. **Goals** — Extracts project-level goals from `enables:` fields → appends to `PROJECT.md`
2. **Feature** — One Feature file per feature category → `features/feat-NNN_{slug}_{category}.md` + FEATURES.md index
3. **Subsystems** — Checks existing SUBSYSTEMS.md; creates new spec or merges into existing
4. **Tasks** — Groups related features (3-8 per task) → `tasks/taskNNN_*.md` + TASKS.md rows
5. **Intake Report** — `vault/research/recon/{slug}/INTAKE_REPORT.md` with full audit trail

## FEATURES.md Approval Status

Before running APPLY, open `FEATURES.md` and set feature statuses:

| Status | Meaning |
|--------|---------|
| `[ ]` | Not yet reviewed |
| `[✅]` | Approved for intake |
| `[❌]` | Rejected (skipped) |
| `[⏸]` | Deferred (skip now, review later) |
| `[🔍]` | Needs clean-room or implementation-detail review (skipped) |

## Mode Options

| Mode | What gets processed |
|------|-------------------|
| `--mode=approved` | Only `[✅]` features |
| `--mode=all` | All clean-room-approved features; refuses unreviewed, `[🔍]`, `[⏸]`, and `[❌]` items unless the user explicitly signs a clean-room exception |
| `--mode=category:{cat}` | Only features in that category |

## Never Overwrites

- Appends to TASKS.md, SUBSYSTEMS.md, FEATURES.md, PROJECT.md
- Never modifies existing task files, feature files, or subsystem specs
- Safe to run multiple times (duplicate detection via feature_ids)

## Subsystem Merge Detection

Automatically detects when a proposed subsystem overlaps with an existing one:
- **MERGE** (≥70% overlap) — adds features to existing subsystem's spec
- **FLAG** (30-69%) — logs for human review, skips auto-creation
- **NEW** (<30%) — creates full new subsystem spec in `subsystems/`

## Examples

```
# Preview maestro2 recon report (nothing written)
@g-res-apply REVIEW maestro2

# Intake all clean-room-approved maestro2 features
@g-res-apply APPLY maestro2 --mode=all

# Only intake approved gald3r_forge features
@g-res-apply APPLY gald3r_forge --mode=approved

# Just the character system from maestro2
@g-res-apply APPLY maestro2 --mode=category:character-system
```

## Input File
`vault/research/recon/{slug}/FEATURES.md` (produced by `@g-res-deep`)

## Clean Room Boundary

These commands support clean-room research and reverse-spec work. Capture/recon may observe and summarize source behavior, interfaces, workflows, data shapes, and architectural patterns; generated gald3r artifacts must use original wording and local architecture terms, not copied source code, docs prose, prompts, tests, or unique strings. Keep source URL, license, and capture provenance in recon notes; treat source file paths as traceability, not implementation instructions. Adoption requires human approval through `@g-res-review` / `@g-res-apply`.

## See Also
- `@g-res-deep` — Analyzes a repo and produces the recon report
- `@g-res-review` — Review and approve features interactively
- `@g-task-add` — Create individual tasks manually
