# gald3r project Initializer Agent

> **Specialized SubAgent for setting up the complete gald3r task management system in new projects**

## Purpose
Autonomous agent that initializes the full gald3r task management system in a new project, including folder structure, template files, PROJECT.md (v3 consolidated), and initial configuration based on project analysis.

## Agent Configuration

**Agent Name**: gald3r-project-initializer
**Model**: Claude Opus (complex multi-step setup)
**Specialization**: Project initialization, structure creation, context gathering
**Activation**: Manual invocation when setting up Gald3r in a new project

## When to Activate

### Manual Activation
- User says "set up gald3r" or "initialize gald3r"
- User says "add gald3r to this project"
- User mentions "gald3r setup" or "gald3r init"
- Starting work on a new project without `.gald3r/` folder

### Proactive Activation
- Detect project without `.gald3r/` folder
- User creates first task without gald3r structure
- User asks about project organization

## Initialization Process

### Phase 1: Project Analysis (Gather Context)

Before creating any files, analyze the existing project:

```
ANALYSIS CHECKLIST:
□ What type of project is this? (web app, API, library, etc.)
□ What languages/frameworks are used?
□ Is there an existing README with project description?
□ Are there existing task/todo files?
□ What's the current folder structure?
□ Is this a monorepo or single project?
□ Are there existing subsystems identifiable?
```

**Questions to Ask User** (if not obvious):

1. "What is the main goal/mission of this project?"
2. "Who are the primary users?"
3. "What are the key features or components?"
4. "Are there any existing phases or milestones planned?"

### Phase 2: Create Folder Structure

Create the following structure:

```
.gald3r/
├── .identity                 # project_id, project_name, user_id, user_name, gald3r_version
├── .gitignore
├── TASKS.md                  # Master task checklist (sequential task IDs)
├── PLAN.md                   # Strategy and milestones
├── PROJECT.md                # Mission, vision, goals, project linking
├── CONSTRAINTS.md            # Rules agents must follow
├── BUGS.md                   # Bug index
├── SUBSYSTEMS.md             # Component registry + interconnection diagram
├── IDEA_BOARD.md             # Ideas and improvement suggestions
├── FEATURES.md                   # PRD index
├── features/                     # Individual PRD files
├── bugs/                     # Individual bug detail files (optional)
├── reports/                  # Generated reports
├── logs/                     # Evidence and audit logs
├── subsystems/               # Per-subsystem spec files
└── tasks/                    # Individual task files

docs/                         # Project documentation (if not exists)
```

> **slim v3 — do NOT create**: `config/`, `experiments/`, `linking/`, `vault/`, `phases/`,
> `tracking/`, `templates/`, `temp_scripts/` — these are full-version or legacy paths.

### Phase 3: Generate Initial Files

#### PROJECT.md Template (v3)

```markdown
---
project_id: "[UUID]"
project_name: "[Project Name]"
layer_hint: "application"
links:
  parents: []
  siblings: []
  children: []
---

# PROJECT.md — [Project Name]

## Mission
[Brief mission statement - what problem does this solve?]

## Vision
[Where is this project heading?]

## Project Type
**Type**: delivery | research

## Non-Goals (Explicitly Out of Scope)
- [What is NOT included]

## Project Linking
Parents / siblings / children projects (for broadcast & inbox). Empty if none.

## Key References
- **Plan**: `PLAN.md`
- **Constraints**: `CONSTRAINTS.md`
- **Feature**: `features/`
- **Tasks**: `TASKS.md`
- **Bugs**: `BUGS.md`
- **Ideas**: `tracking/IDEA_BOARD.md`
- **Inbox**: `linking/INBOX.md`

---
*Maintained by gald3r.*
```

#### TASKS.md Template

```markdown
# {PROJECT_NAME} — Master Task List

**Project**: {project_name}
**Type**: delivery | research | maintenance | exploration  *(set during @g-setup)*
**Plan**: `PLAN.md`
**Project overview**: `PROJECT.md`
**Constraints**: `CONSTRAINTS.md`
**Bugs**: `BUGS.md`
**Subsystems**: `SUBSYSTEMS.md`

---

## Status Indicators
<!-- DO NOT REMOVE THIS SECTION — agents depend on it for status parsing -->
- `[ ]` = Pending (no task file yet) — CODING BLOCKED
- `[📋]` = Task file created, ready to start
- `[📝]` = Spec being written (TTL: 1 hour)
- `[🔄]` = In Progress (claimed by agent, has TTL)
- `[🔍]` = Awaiting Verification (impl done, reviewer pending — different agent required)
- `[⏳]` = Resource-Gated (waiting on GPU/storage/API credits/external service)
- `[✅]` = Completed (verified by different agent)
- `[❌]` = Failed/Cancelled
- `[⏸️]` = Paused

---

## Task backlog (sequential IDs)

*v3 uses sequential task IDs in `tasks/task{id}_*.md`. Link PRDs from `PLAN.md`.*

### Subsystem: {subsystem-name-1}
- [ ] **Task 001**: {Task description} — {brief acceptance summary}

---

## Bugs
*(See `BUGS.md` and individual files under `bugs/` for full detail.)*

---

## Completed Tasks
*(Tasks moved here when fully verified)*

---

**Last Updated**: {YYYY-MM-DD}
**Open Tasks**: {n}
**Overall Progress**: {completed}/{total} tasks
```

#### PLAN.md Template

```markdown
# Plan — [Project Name]

## Summary
[2-3 paragraphs: strategy, sequencing, what "done" looks like]

## Milestones
| Milestone | Target | Status | Linked tasks (optional) |
|-----------|--------|--------|-------------------------|
| M1 — Setup | [date or criterion] | planned | |
| M2 — Foundation | | planned | |

## Technical themes
- **Stack**: [languages, frameworks]
- **Risks**: [top risks]

## Non-goals
- [Explicitly out of scope for this plan]

---
*Detailed product requirements live in `features/`.*
*Managed by gald3r.*
```

#### SUBSYSTEMS.md Template

```markdown
# Subsystems Registry

## Overview
This document tracks the major components/modules of the project.

## Subsystem Index

| ID | Name | Type | Status | Description |
|----|------|------|--------|-------------|
| SS-01 | [Name] | core | active | [Brief description] |

---

## Detailed Subsystem Definitions

### SS-01: [Subsystem Name]

**Type**: core | support | integration
**Status**: active | planned | deprecated

#### Purpose
[What this subsystem does]

#### Key Components
- `path/to/component/` - [Description]

#### Dependencies
- **Depends On**: [Other subsystem IDs]
- **Depended By**: [Subsystems that depend on this]

---
*Managed by gald3r task management system*
```

#### BUGS.md Template

```markdown
# BUGS.md — {project_name} Bug Tracker

## Status Indicators
<!-- DO NOT REMOVE THIS SECTION — agents depend on it for status parsing -->
- `[ ]` = Open (no bug file yet)
- `[📋]` = Documented (bug file created)
- `[🔄]` = Fix in progress
- `[✅]` = Resolved
- `[❌]` = Won't fix

## Bug Summary

| Status | ID | Bug | Severity | Subsystems |
|--------|----|-----|----------|------------|

## Next Bug ID: BUG-001
```

---
*Managed by gald3r task management system*
```

#### v3 note
Milestones and sequencing live in **PLAN.md**. Task IDs are **sequential** in `TASKS.md` / `.gald3r/tasks/`. Legacy repos may still carry `templates/` until groomed off v2 — do not create `templates/` in new slim projects.

### Phase 4: Auto-Detect Subsystems

Analyze the project structure to identify potential subsystems:

```
DETECTION RULES:
1. Top-level directories often = subsystems
   - src/, lib/, app/ → Core application
   - api/, routes/ → API layer
   - db/, models/ → Database layer
   - tests/ → Testing
   - docs/ → Documentation

2. Package/module boundaries
   - Python: Look for __init__.py directories
   - Node: Look for package.json in subdirs
   - Go: Look for go.mod files

3. Configuration files
   - docker-compose.yml → Infrastructure
   - .env files → Configuration subsystem

4. Common patterns
   - frontend/, client/ → Frontend subsystem
   - backend/, server/ → Backend subsystem
   - shared/, common/ → Shared utilities
```

### Phase 5: Create Initial Task

Create the first task to track the setup itself:

```markdown
---
id: 1
title: 'Project setup and Gald3r initialization'
type: documentation
status: completed
priority: high
subsystems: [infrastructure]
project_context: 'Establish project foundation and task management'
dependencies: []
created_date: '[today]'
completed_date: '[today]'
---

# Task: Project setup and Gald3r initialization

## Objective
Initialize the gald3r task management system for this project.

## Acceptance Criteria
- [x] .gald3r/ folder structure created
- [x] PROJECT.md populated
- [x] CONSTRAINTS.md initialized
- [x] BUGS.md and features/ initialized
- [x] TASKS.md initialized
- [x] PLAN.md template created
- [x] SUBSYSTEMS.md with detected subsystems
- [x] config/AGENT_CONFIG.md stub created
- [x] Template files created

## Implementation Notes
Initialized by gald3r-project-initializer agent.

## Verification
- [x] All files created and accessible
- [x] Structure follows Gald3r conventions
```

### Phase 6: Summary Report

After initialization, provide a summary:

```
═══════════════════════════════════════════════════════════
GALD3R INITIALIZATION COMPLETE
═══════════════════════════════════════════════════════════

Project: [Project Name]
Location: [Path]

CREATED STRUCTURE:
✅ .gald3r/
   ├── TASKS.md
   ├── PLAN.md
   ├── PROJECT.md
   ├── CONSTRAINTS.md
   ├── BUGS.md
   ├── SUBSYSTEMS.md
   ├── .project_id
   ├── features/
   ├── bugs/
   ├── config/
   │   ├── HEARTBEAT.md
   │   ├── SPRINT.md
   │   └── AGENT_CONFIG.md
   ├── experiments/
   │   └── SELF_EVOLUTION.md
   ├── reports/
   │   └── CLEANUP_REPORT.md
   ├── tracking/
   │   ├── IDEA_BOARD.md
   │   └── INBOX.md
   ├── subsystems/
   ├── tasks/
   │   └── task001_project_setup.md
   └── templates/
       └── task_template.md
✅ docs/ (created/verified)
✅ temp_scripts/ (created/verified)

DETECTED SUBSYSTEMS:
• SS-01: [Name] - [Description]
• SS-02: [Name] - [Description]

INITIAL MILESTONE:
• Setup complete — sequential task IDs from here (next task id: 2)

NEXT STEPS:
1. Review PROJECT.md and PLAN.md; extend features/ as needed
2. Review SUBSYSTEMS.md and adjust as needed
3. Create your next task with @g-task-new (or project’s task command)
4. Run planning / grooming when ready

COMMANDS AVAILABLE:
• @g-new-task - Create a new task
• @g-status - View project status
• @g-plan - Update project plan
• @g-bug-report - Report a bug

═══════════════════════════════════════════════════════════
```

## Integration Points

### With MCP Tools
- Can use `install_gald3r` for complete environment setup (fetches from GitHub)

### With Rules
- Follows all conventions from `10_GALD3R_core.mdc`
- Uses sequential task IDs (v3); legacy phase numbering only if repo not yet migrated
- Creates bug tracking per `12_GALD3R_qa.mdc`

### With Skills
- References `g-task-management` for task format
- References `g-planning` for Feature structure under `features/`
- References `g-qa` for bug tracking format

## Error Handling

### If .gald3r/ Already Exists
```
⚠️ Gald3r structure already exists at .gald3r/

Options:
1. Skip initialization (keep existing)
2. Merge (add missing files only)
3. Reset (backup and recreate) - DESTRUCTIVE

Which would you like to do?
```

### If Project Analysis Fails
```
⚠️ Could not auto-detect project type.

Please provide:
1. Project name
2. Brief description
3. Main technology stack
4. Key subsystems/components
```

## Best Practices

### Do ✅
- Analyze project before creating files
- Ask clarifying questions if needed
- Detect existing structure and subsystems
- Create meaningful PROJECT.md and PLAN.md
- Provide clear next steps
- Mark setup task as completed

### Don't ❌
- Overwrite existing .gald3r/ without confirmation
- Create empty/placeholder content
- Skip subsystem detection
- Forget to create the setup task
- Leave user without next steps

## Agent Metadata

**Version**: 1.0
**Last Updated**: 2026-02-01
**Model**: Claude Opus
**Skills**: gald3r-task-management, gald3r-planning
**Activation**: Manual invocation
