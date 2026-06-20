---
subsystem_memberships: [PROJECT_IDENTITY_SETUP]
---
Initialize the gald3r system: $ARGUMENTS

## What This Command Does

Initializes or reinitializes the gald3r v3 task management system in the current project.
Activates the **g-skl-setup** skill which handles the full initialization workflow.

> **This is the slim gald3r version.** Experiments, linking, vault, config, and phases
> are full-version features only and must not be created here.

---

## Step 0: First-IDE-Launch Platform Detection

Before doing anything else, detect whether this project has a `.gald3r_sys/` folder.

### Case A: `.gald3r_sys/` EXISTS (gald3r already installed)
```powershell
python setup_gald3r_project.py --platform auto
```
This regenerates the current platform's dirs from `.gald3r_sys/`. Proceed to Step 1.

### Case B: `.gald3r_sys/` is MISSING (first-time setup / fresh clone)
The user needs to run the installer from their `gald3r_template` download:
```
1. Locate your downloaded gald3r_template folder
2. Run: .\setup_gald3r_project.ps1
   (interactive installer — asks for target path and platform selection)
3. START A NEW SESSION after installation completes so skills/rules load
4. Then re-run @g-setup (or /g-setup) in the new session
```

If no template was downloaded, advise the user:
> "To set up gald3r for the first time, clone or download the gald3r template from
> https://github.com/wrc3/<template_adv> (or _full, or _slim) and run
> setup_gald3r_project.ps1 from that folder, pointing it at your project directory.
> Then start a new IDE session so the skills and rules load into context."

### Determining which platform to install
Ask the user which IDE they primarily use if it cannot be auto-detected:
1. **Cursor IDE** → `cursor`
2. **Claude Code** (CLI) → `claude`
3. **Gemini / Antigravity** → `agent`
4. **OpenAI Codex CLI** → `codex`
5. **OpenCode (sst.dev)** → `opencode`
6. **GitHub Copilot** → `copilot`

Most users will use 1–2 platforms. Install only those to keep the project clean.

### After platform dirs are populated
Remind the user:
> **Start a new session** so gald3r rules and skills load into context before continuing.
> Platform dirs are regenerated automatically on each session start via hooks.

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
