---
description: "Initialize the gald3r vNext system with project type selection"
---

Initialize the gald3r system: $ARGUMENTS

## What This Command Does

Initializes or reinitializes the gald3r vNext task management system in the current project.

---

## Step 1: Project Type Selection (MANDATORY FIRST QUESTION)

**Ask the user:**

> "What type of project is this?
> 1. **delivery** — building a defined product with features and milestones
> 2. **research** — exploring unknown solutions, running experiments, testing hypotheses
>
> (Default: delivery)"

Set `Project Type` in `PROJECT_CONTEXT.md` based on their answer. This affects:
- Whether `HYPOTHESIS.md` is created (research only)
- Whether phase templates use milestone or experiment format
- Whether SPRINT.md excludes unvalidated experiment phases

---

## Step 2: Create Directory Structure

Create these folders if they don't exist:
- `.gald3r/` - Main working directory
- `.gald3r/tasks/` - Individual task files
- `.gald3r/phases/` - Phase documentation
- `.gald3r/experiments/` - Research experiments (research projects only)
- `.gald3r/logs/` - Evidence files for task completion
- `.gald3r/templates/` - task_template.md, phase_template.md
- `docs/` - Project documentation
- `temp_scripts/` - Test scripts

---

## Step 3: Create Core Files (vNext)

Create these template files:
- `.gald3r/PRD.md` - Product Requirements Document
- `.gald3r/TASKS.md` - Master task checklist (with subsystem headers)
- `.gald3r/tracking/BUGS.md` - Bug tracking
- `.gald3r/project/PROJECT_CONTEXT.md` - Mission + health score + autonomous agent config
- `.gald3r/project/PROJECT_CONSTRAINTS.md` - Non-negotiable constraints (populate with user input)
- `.gald3r/SUBSYSTEMS.md` - Component registry
- `.gald3r/config/SPRINT.md` - Active sprint queue (cleanup-agent-generated placeholder)
- `.gald3r/reports/CLEANUP_REPORT.md` - Nightly report placeholder
- `.gald3r/experiments/SELF_EVOLUTION.md` - System evolution log
- `.gald3r/IDEA_BOARD.md` - Ideas parking lot (human + AI sections)
- `.gald3r/project/PROJECT_GOALS.md` - Strategic goals
- `.gald3r/templates/task_template.md` - Full vNext task YAML schema
- `.gald3r/templates/phase_template.md` - Phase schema

**Research projects also get:**
- `.gald3r/experiments/HYPOTHESIS.md` - Hypothesis tracker

---

## Step 4: Gather Architecture Constraints

Ask the user:
> "Are there any non-negotiable technical constraints? (e.g., database technology, deployment target, public API stability, cost limits)
> I'll document these in PROJECT_CONSTRAINTS.md so every agent session loads them automatically."

Add each constraint as a `C-NNN` entry.

---

## Step 5: Verify MCP Tools

Check available MCP tools and note key ones in PROJECT_CONTEXT.md.

---

## Step 6: Scan Existing Codebase (if applicable)

For existing projects:
- Analyze current file structure
- Identify existing components/subsystems
- Document in SUBSYSTEMS.md

---

## Phase-Based Task Organization
- **Phase 0** (Task IDs: 1-99): Setup & Infrastructure
- **Phase 1** (Task IDs: 100-199): Foundation
- **Phase 2** (Task IDs: 200-299): Core Development
- **Phase N** (Task IDs: N×100 to N×100+99): Additional phases

---

## Task Status Indicators (vNext)
- `[ ]` - Pending (no file created yet)
- `[📝]` - Spec being written (TTL: 1 hour)
- `[📋]` - Ready (task file created)
- `[🔄]` - In Progress (claimed, has TTL)
- `[🔍]` - Awaiting Verification (different agent required)
- `[⏳]` - Resource-Gated
- `[✅]` - Completed (verified by different agent)
- `[❌]` - Failed/Cancelled
- `[🌾]` - Harvested (approach superseded, kept as reference)

---

## When to Use
- Starting a new project
- Adding gald3r to an existing project
- Reinitializing after major changes

Let me set up the gald3r vNext system for you!
