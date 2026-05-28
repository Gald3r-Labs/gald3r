---
description: "Validate TASKS.md phase headers vs phase files synchronization"
---

# gald3r-phase-sync-check Command

Validate synchronization between TASKS.md phase headers and phase files.

## Usage

```
@g-phase-sync-check
```

## What This Command Does

1. **Reads TASKS.md** to find all phase headers (e.g., `### Phase 0: Setup`)
2. **Scans .gald3r/phases/** to find all phase files
3. **Compares** each phase header against its corresponding file
4. **Reports** any mismatches, orphans, or phantoms
5. **Offers to fix** any synchronization issues found

## Expected Output

### All Synced
```markdown
📋 PHASE SYNCHRONIZATION REPORT

## Validation Results

| Phase | TASKS.md Header | Phase File | Status Match |
|-------|-----------------|------------|--------------|
| 0 | Setup [🔄] | phase0_setup.md (in_progress) | ✅ SYNCED |
| 1 | Foundation | phase1_foundation.md (planning) | ✅ SYNCED |
| 2 | Core Dev [✅] | phase2_core-dev.md (completed) | ✅ SYNCED |

**Summary**: 3/3 phases synchronized ✅
**Orphan Files**: None
**Phantom Headers**: None

All phases are properly synchronized!
```

### With Issues
```markdown
📋 PHASE SYNCHRONIZATION REPORT

## Validation Results

| Phase | TASKS.md Header | Phase File | Status Match |
|-------|-----------------|------------|--------------|
| 0 | Setup [🔄] | phase0_setup.md (in_progress) | ✅ SYNCED |
| 1 | Foundation | (NO FILE) | ⚠️ MISSING |
| 2 | Core Dev [✅] | phase2_core-dev.md (in_progress) | ⚠️ STATUS MISMATCH |

**Summary**: 1/3 phases synchronized
**Issues Found**: 2

### Missing Phase Files (Phantoms)
- **Phase 1: Foundation** - Header exists but no file
  - Action: Create `.gald3r/phases/phase1_foundation.md`

### Status Mismatches
- **Phase 2**: TASKS.md shows [✅] but file has `status: in_progress`
  - Action: Update file to `status: completed`

### Orphan Files (in .gald3r/phases/ but no TASKS.md header)
- phase5_experimental.md

---
**Fix these issues?** Reply "fix" to auto-correct all issues.
```

## Status Mapping Reference

| TASKS.md Header | Phase File YAML Status |
|-----------------|------------------------|
| `### Phase N: Name` | `status: planning` |
| `### Phase N: Name [🔄]` | `status: in_progress` |
| `### Phase N: Name [✅]` | `status: completed` |
| `### Phase N: Name [❌]` | `status: cancelled` |
| `### Phase N: Name [⏸️]` | `status: paused` |

## Auto-Fix Behavior

When user replies "fix":
1. **Missing files**: Create phase file from template using header info
2. **Status mismatches**: Update phase file status to match TASKS.md (TASKS.md is source of truth)
3. **Orphan files**: Report for user decision (add header or delete file)

## When to Run This Command

- At the start of a work session
- Before generating project status reports
- After adding or modifying phases
- Before phase completion reviews
- When phase status seems inconsistent

## Implementation Notes

This command should:
1. Parse TASKS.md for lines matching `### Phase \d+:` pattern
2. Extract phase number, name, and status indicator from header
3. List all `phase*.md` files in `.gald3r/phases/`
4. Parse YAML frontmatter from each phase file
5. Compare and report differences
6. Offer atomic fixes that update both locations together
