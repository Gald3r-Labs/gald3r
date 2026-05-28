---
description: "Gald3r Phase Add"
---

Add a new phase: $ARGUMENTS

## What This Command Does

Creates a new phase in the gald3r planning system with **atomic synchronization** (TASKS.md header AND phase file created together).

## Phase Creation Workflow

### 1. Gather Phase Details
I'll ask for:
- **Phase Number**: Next available (or custom for pivots)
- **Phase Name**: Descriptive name (e.g., "Core Development")
- **Subsystems**: Which subsystems this phase affects
- **Objectives**: What this phase accomplishes
- **Prerequisites**: Prior phases that must complete first

### 2. ATOMIC: Create Both Files Together

**🚨 CRITICAL**: Both files MUST be created in the same response!

#### A. Add Phase Header to TASKS.md
```markdown
### Phase {N}: {Phase Name}
- [ ] Task {N×100}: {First task placeholder}
```

#### B. Create Phase File
**Filename**: `.gald3r/phases/phase{N}_{kebab-case-name}.md`

**Content**:
```yaml
---
phase: {N}
name: '{Phase Name}'
status: planning
subsystems: [{subsystem1}, {subsystem2}]
task_range: '{N*100}-{N*100+99}'
prerequisites: [{prior_phase_numbers}]
started_date: ''
completed_date: ''
pivoted_from: null
pivot_reason: ''
---

# Phase {N}: {Phase Name}

## Overview
{Brief description of phase goals and scope}

## Objectives
- {Objective 1}
- {Objective 2}

## Deliverables
- [ ] {Deliverable 1}
- [ ] {Deliverable 2}

## Acceptance Criteria
- [ ] {Criterion 1}
- [ ] {Criterion 2}

## Notes
{Additional context}
```

### 3. Update Project Files (If Exists)

**Update CLAUDE.md** (if present):
```markdown
## Current Phase
- **Phase {N}**: {Phase Name}
- **Status**: Planning → In Progress
- **Objectives**: {Key objectives from phase file}
- **Subsystems**: {Affected subsystems}
```

### 4. Confirm Synchronization
```markdown
---
**Phase Sync Confirmation:**
- TASKS.md header: ### Phase {N}: {Name} ✅
- Phase file: phase{N}_{name}.md ✅
- CLAUDE.md: {updated/not present}
- Sync verified: ✅
---
```

## Phase Numbering
- **Phase 0**: Setup & Infrastructure (Task IDs 1-99)
- **Phase 1**: Foundation (Task IDs 100-199)
- **Phase 2**: Core Development (Task IDs 200-299)
- **Phase N**: Custom scope (Task IDs N×100 to N×100+99)

## Phase Gaps Allowed
You can skip phase numbers for pivots:
- Phase 1 → Phase 2 → Phase 5 (skipping 3, 4) is valid

## What I Need From You
- Phase name and description
- Which subsystems are affected
- Primary objectives for this phase
- Prerequisites (prior phases)
- Key deliverables expected

Let's create this phase!
