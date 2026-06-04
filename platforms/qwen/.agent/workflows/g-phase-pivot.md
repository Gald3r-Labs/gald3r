---
description: "Pivot the project to a new phase direction"
---

Pivot to a new direction: $ARGUMENTS

## What This Command Does

Pivots the project to a new phase direction while preserving completed work. Uses **atomic synchronization** to update all files together.

## What is a Pivot?

A **pivot** means changing project direction while:
- Preserving completed work
- Creating a new phase (potentially with gap in numbering)
- Documenting why the change occurred
- Linking the new phase to the old one

## Pivot Workflow

### 1. Current State Assessment
I'll review:
- Current active phase and its tasks
- Completed vs incomplete tasks
- Dependencies that would be affected
- Work that carries forward

### 2. Pivot Decision
I'll ask you:
- **Reason for Pivot**: Why is direction changing?
- **What to Keep**: Which completed work carries forward?
- **What to Pause**: Which tasks are paused (not cancelled)?
- **What to Cancel**: Which tasks are no longer relevant?
- **New Direction**: What's the new focus?
- **Subsystems**: Which subsystems does the new phase affect?

### 3. ATOMIC: Execute Pivot (All Updates Together)

**🚨 CRITICAL**: All updates MUST happen in the same response!

#### A. Update Old Phase File
```yaml
---
status: paused  # or cancelled
completed_date: '{today}'
---
```

#### B. Update TASKS.md Old Phase Header
```markdown
### Phase {N}: Old Name [⏸️]  # or [❌] for cancelled
```

#### C. Create New Phase File
```yaml
---
phase: {M}
name: '{New Phase Name}'
status: in_progress
subsystems: [{affected_subsystems}]
task_range: '{M*100}-{M*100+99}'
prerequisites: [{completed_phases}]
pivoted_from: {N}
pivot_reason: '{Why the pivot occurred}'
---
```

#### D. Add New Phase Header to TASKS.md
```markdown
### Phase {M}: New Name [🔄]
- [ ] Task {M×100}: {First task}
```

### 4. Update Project Files (If Exists)

**Update CLAUDE.md** (if present):
```markdown
## Current Phase
- **Phase {M}**: {New Phase Name}
- **Status**: In Progress
- **Pivoted From**: Phase {N} - {Old Name}
- **Pivot Reason**: {Why the pivot occurred}
- **New Objectives**: {Key objectives from new phase file}
- **Subsystems**: {Affected subsystems}
```

**Consider agents.md update** if pivot significantly changes:
- Project direction or purpose
- Available features or capabilities
- Development workflow

### 5. Confirm Synchronization
```markdown
---
**Pivot Sync Confirmation:**
- Old phase {N}: [⏸️] paused ✅
- Old phase file: status: paused ✅
- New phase {M}: header added ✅
- New phase file: created with pivoted_from: {N} ✅
- CLAUDE.md: {updated/not present}
- agents.md: {updated/not needed}
- Sync verified: ✅
---
```

## Pivot Types

### Type A: Direction Change
```
Phase 2: Building Feature X [⏸️]
    ↓ (pivot - user needs changed)
Phase 3: Building Feature Y [🔄]
    pivoted_from: 2
```

### Type B: Strategic Skip
```
Phase 1: Foundation [✅]
Phase 2: Original Plan [❌]
    ↓ (pivot - found better approach)
Phase 5: New Approach [🔄]
    pivoted_from: 2
```

### Type C: Scope Reduction
```
Phase 2: Full Enterprise System [⏸️]
    ↓ (pivot - MVP first)
Phase 3: MVP Only [🔄]
    pivoted_from: 2
```

## Status Indicators
- `[⏸️]` / `paused` - Work stopped but may resume later
- `[❌]` / `cancelled` - Work abandoned, won't resume
- `[🔄]` / `in_progress` - New phase actively being worked

## What I Need From You
- Why are we pivoting?
- What completed work should we keep?
- What's the new direction?
- Which subsystems are affected?
- New phase number (can skip numbers)

Let's plan this pivot!
