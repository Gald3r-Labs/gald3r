# Quality Assurance Rules

> Detailed implementation rules for the gald3r-qa Skill.
> These rules are derived from Cursor's gald3r system.

## Overview

These rules provide comprehensive guidance for quality assurance using the gald3r system. They cover bug tracking, severity classification, retroactive documentation, quality metrics, and integration with the task and planning systems.

## Bug Classification Rules

### Severity Levels

**Critical**: System crashes, data loss, security vulnerabilities
- **Response Time**: Immediate (< 1 hour)

**High**: Major feature failures, performance degradation >50%
- **Response Time**: Same day (< 8 hours)

**Medium**: Minor feature issues, usability problems
- **Response Time**: Within week (< 5 days)

**Low**: Cosmetic issues, enhancement requests
- **Response Time**: Next sprint (< 2 weeks)

### Bug Source Attribution

- **User Reported**: Issues reported by end users or stakeholders
- **Development**: Bugs discovered during feature development
- **Testing**: Issues found during QA or automated testing
- **Production**: Live environment issues requiring immediate attention

## Bug Tracking Rules

### BUGS.md File Format

**Location**: `.gald3r/tracking/BUGS.md`

**Structure**:
```markdown
# Bug Tracking

## Active Bugs

### Bug ID: BUG-001
- **Title**: [Brief description]
- **Severity**: [Critical/High/Medium/Low]
- **Source**: [User Reported/Development/Testing/Production]
- **Phase Impact**: [List affected phases]
- **Status**: [Open/Investigating/Fixing/Testing/Closed]
- **Task Reference**: [Link to task in TASKS.md]
- **Created**: [Date]
- **Assigned**: [Developer/Team]

## Closed Bugs
[Archived resolved bugs]
```

### Bug ID Assignment

**Format**: `BUG-{number}`
- Sequential numbering (BUG-001, BUG-002, etc.)
- Zero-padded to 3 digits
- Never reuse IDs

### Bug Status Lifecycle

```
Open → Investigating → Fixing → Testing → Closed
                                      ↓
                                  Reopened → Investigating
```

### Bug-Task Integration

**When Bug Identified**:
1. Create BUGS.md entry with bug details
2. Create corresponding task in TASKS.md with `[BUG]` prefix
3. Create task file in `tasks/` folder with bug type
4. Link bug to affected phases
5. Track resolution through task completion

**Bug Task YAML Template**:
```yaml
---
id: {next_available_id}
title: '[BUG] {Brief description}'
type: bug_fix
status: pending
priority: {severity_level}
phase: {affected_phase_number}
subsystems: {affected_subsystems}
bug_reference: BUG-{number}
severity: {critical|high|medium|low}
source: {user_reported|development|testing|production}
---
```

**Synchronization Rules**:
- Bug status in BUGS.md = task status in TASKS.md
- Task completion → bug closure
- Keep both files in sync

## Retroactive Documentation Rules

### When to Document Retroactively

**Document as retroactive task if**:
- ✅ Fix required > 15 minutes of work
- ✅ Solution affects multiple files or subsystems
- ✅ Fix provides value for future reference
- ✅ Resolution required technical analysis

**Skip documentation if**:
- ❌ Simple typo corrections
- ❌ Minor formatting adjustments
- ❌ Clarification-only conversations

### Retroactive Task Template

```yaml
---
id: {next_available_id}
title: '[RETROACTIVE] {Description}'
type: retroactive_fix
status: completed
priority: {urgency_level}
phase: {affected_phase_number}
created_date: '{completion_date}'
completed_date: '{completion_date}'
subsystems: {affected_subsystems}
---
```

## Quality Metrics Rules

### Bug Discovery Rate
- Count new bugs per development cycle
- Track by source and phase

### Bug Resolution Time
- Average: (Closed Date - Created Date)
- Targets: Critical < 1 day, High < 3 days, Medium < 1 week

### Phase Impact Analysis
- Count bugs per phase
- Calculate bug density (bugs / phase size)
- Identify high-risk phases

### Regression Rate
- Target: < 10% of fixes introduce new bugs

## Quality Gates Rules

### Code Review Gate
- All code changes require review
- Review checklist completed

### Testing Requirements Gate
- Unit tests for new code
- Integration tests for features
- Manual testing for UI changes

### Documentation Standards Gate
- Code comments for complex logic
- API documentation updated
- User guides updated

## Bug Lifecycle Workflow

1. **Discovery**: Bug identified and reported
2. **Documentation**: Create BUGS.md entry
3. **Task Creation**: Create bug fix task in TASKS.md
4. **Investigation**: Root cause analysis (Status: Investigating)
5. **Fix Implementation**: Solution developed (Status: Fixing)
6. **Verification**: Fix validated (Status: Testing)
7. **Documentation**: Document fix in task file
8. **Closure**: Update status to Closed

## Integration with Cursor

These rules maintain 100% compatibility with Cursor's gald3r system:

- **File Format**: Identical BUGS.md structure and bug task format
- **File Locations**: Same directory structure
- **Bug IDs**: Same numbering scheme
- **Status Flow**: Same lifecycle and transitions
- **Integration**: Same bug-task-phase relationships

**Cursor Rules Source**: `.cursor/rules/gald3r/rules/qa.mdc`

## Cross-References

- **Main Skill**: `SKILL.md` - Complete skill documentation
- **Task Management**: See `g-task-management` Skill
- **Planning Integration**: See `g-planning` Skill

## Best Practices

1. **Report bugs immediately**: Document as soon as found
2. **Provide reproduction steps**: Clear steps help fix faster
3. **Link to phases**: Track phase quality over time
4. **Document retroactively**: Capture unplanned fixes
5. **Track metrics**: Monitor quality trends
6. **Learn from bugs**: Capture lessons to prevent recurrence

---

*These rules ensure consistent, comprehensive quality assurance in Cursor.*
