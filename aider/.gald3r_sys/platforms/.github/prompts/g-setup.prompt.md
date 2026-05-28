Initialize the gald3r system: $ARGUMENTS

## What This Command Does

Initializes or reinitializes the gald3r v3 task management system in the current project.
Activates the **g-skl-setup** skill which handles the full initialization workflow.

> **This is the slim gald3r version.** Experiments, linking, vault, config, and phases
> are full-version features only and must not be created here.

---

## Step 1: Check for Existing Installation

```
□ .gald3r/TASKS.md exists AND > 20 lines?
□ .gald3r/tasks/ has > 5 files?
□ PROJECT.md has non-template content?
→ YES: EXISTING project → ask: Merge / Skip / Reset (DESTRUCTIVE)
→ NO: FRESH install → proceed
```

---

## Step 2: Create Directory Structure (slim v3 Layout)

Create these folders if they don't exist:
- `.gald3r/` — Main working directory
- `.gald3r/tasks/` — Individual task files (sequential IDs)
- `.gald3r/features/` — PRD files
- `.gald3r/bugs/` — Individual bug detail files
- `.gald3r/subsystems/` — Per-subsystem spec files
- `.gald3r/logs/` — Evidence and audit logs
- `.gald3r/reports/` — Cleanup and health reports
- `docs/` — Project documentation

**Do NOT create**: `config/`, `experiments/`, `linking/`, `vault/`, `phases/`, `tracking/`, `project/`, `temp_scripts/` — these are full-version or legacy paths.

---

## Step 3: Create Core Files (slim v3)

Create these template files:
- `.gald3r/TASKS.md` — Master task checklist (sequential task IDs)
- `.gald3r/PLAN.md` — Master strategy and PRD index
- `.gald3r/PROJECT.md` — Mission, vision, goals, project linking
- `.gald3r/CONSTRAINTS.md` — Non-negotiable architectural constraints
- `.gald3r/BUGS.md` — Bug index (root level)
- `.gald3r/SUBSYSTEMS.md` — Component registry with mermaid graph
- `.gald3r/IDEA_BOARD.md` — Ideas parking lot
- `.gald3r/FEATURES.md` — PRD index
- `.gald3r/.identity` — Project and user identity

> **PRD FOLLOW-THROUGH RULE**: If PLAN.md is written with any PRD entries in its
> Deliverable Index, you MUST create those Feature files under `features/` AND add them to
> `FEATURES.md` in the same response. Do not defer. A PLAN.md that references PRD-001
> through PRD-009 with no corresponding files is a broken state.

---

## Step 4: Generate .identity

```
project_id={new-uuid}
project_name={project_name}
user_id={user_id_from_appdata_or_ask}
user_name={user_name}
gald3r_version=1.4
vault_location={LOCAL}
```

---

## Step 5: Gather Architecture Constraints

Ask the user:
> "Are there any non-negotiable technical constraints? (e.g., database technology, deployment target, public API stability, cost limits)
> I'll document these in CONSTRAINTS.md so every agent session loads them automatically."

Add each constraint as a `C-NNN` entry in `.gald3r/CONSTRAINTS.md`.

---

## Step 6: Scan Existing Codebase (if applicable)

For existing projects:
- Analyze current file structure
- Identify existing components/subsystems
- Create spec files in `.gald3r/subsystems/`
- Populate SUBSYSTEMS.md with index and mermaid graph

---

## Task Status Indicators (v3)
- `[ ]` — Pending (no task file yet)
- `[📋]` — Ready (task file created, spec written)
- `[🔄]` — In Progress (claimed by agent, has TTL)
- `[🔍]` — Awaiting Verification (different agent required)
- `[✅]` — Completed (verified by different agent)
- `[❌]` — Failed/Cancelled
- `[⏸️]` — Paused

---

## When to Use
- Starting a new project
- Adding gald3r to an existing project
- Reinitializing after major structural changes

Let me set up the gald3r v3 system for you!
