---
description: 'Initialize or reinitialize the gald3r v3 task-management system in this project via g-skl-setup.'
argument-hint: '[--autonomy full]'
subsystem_memberships: [PROJECT_IDENTITY_SETUP]
execution_tier: orchestration
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
gald3r platform install <platform> --into . --generated
```
This regenerates the current platform's dirs straight from the neutral component set embedded
in the `gald3r` engine binary (self-contained, T177 — no `.gald3r_sys/` checkout needed to read
from). Proceed to Step 1.

### Case B: `.gald3r_sys/` is MISSING (first-time setup / fresh clone)
The user needs the `gald3r` engine binary, then the self-contained platform installer:
```
1. Install the gald3r engine if not already present: run g-install-agent
   (/g-install-agent in Claude Code, @g-install-agent in Cursor), or verify with
   `gald3r --version`
2. Run: gald3r platform install <platform> --into <target_path> --generated
   (writes that platform's IDE dirs straight from the engine's embedded neutral
   component set — asks/accepts an explicit platform id, e.g. cursor, claude)
3. START A NEW SESSION after installation completes so skills/rules load
4. Then re-run @g-setup (or /g-setup) in the new session
```

If the `gald3r` engine binary is not yet installed, advise the user:
> "To set up gald3r for the first time, install the gald3r engine binary via
> g-install-agent, then run `gald3r platform install <platform> --into <target_path>
> --generated` from your project directory (no template download needed — the
> component set ships inside the engine binary).
> Then start a new IDE session so the skills and rules load into context."

### Determining which platform to install
Ask the user which IDE they primarily use if it cannot be auto-detected:
1. **Cursor IDE** → `cursor`
2. **Claude Code** (CLI) → `claude`
3. **Antigravity** → `antigravity` (T454: `gemini` platform retired 2026-07-23, EOL 2026-06-18)
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

## Step 4b: Public-Publish History Mode (T423 — OFF by default)

Ask **only** if the project may publish to a public repo (multi-tier graduation, or the user
wants a public sibling). Skip silently otherwise — the safe default needs no prompt. Also offered
on `@g-setup --autonomy full` (the file top-up path for an already-scaffolded project — see
`--upgrade-existing` deprecation, T364).

```
Public publish: how should git history be handled when you publish to a public repo?
  1. carry (default) — keep full git history (non-destructive, safe)
  2. scrub (Mode A)  — publish with ZERO git history for IP protection
                       (DESTRUCTIVE: public history replaced; requires -ConfirmScrub at publish)
[1]
```

- Enter / decline / no answer = **`carry`** (never scrub by default).
- Write to `.gald3r/.identity` as `publish_history_mode=<carry|scrub>` (lowercase). Absent = `carry`.
- `scrub` here only records the intent; publish still requires explicit `-ConfirmScrub`.

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
