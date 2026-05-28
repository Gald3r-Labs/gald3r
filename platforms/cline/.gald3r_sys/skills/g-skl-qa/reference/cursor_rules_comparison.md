# Cursor Rules and Skills Integration - QA

## Overview

This document describes how the gald3r QA system integrates with Cursor's rules and skills architecture for bug tracking and quality management.

## Cursor Features Used

### Rules (`.cursor/rules/`)
- **Location**: `.cursor/rules/gald3r/rules/qa.mdc`
- **Activation**: Always active for QA operations

### Skills (`.cursor/skills/`)
- **Location**: `.cursor/skills/g-qa/SKILL.md`
- **Activation**: Mentions of "bug", "issue", "quality", "fix"

### Commands (`.cursor/commands/`)
- **Commands**: `@g-qa`, `@g-bug-report`, `@g-bug-fix`
- **Purpose**: Guided bug reporting and fixing

## File Format Standards

### BUGS.md Structure
```markdown
# Bug Tracking

## Active Bugs

### Bug ID: BUG-001
- **Title**: [Brief description]
- **Severity**: [Critical/High/Medium/Low]
- **Source**: [User Reported/Development/Testing/Production]
- **Phase Impact**: [Affected phases]
- **Status**: [Open/Investigating/Fixing/Testing/Closed]
- **Task Reference**: Task 015
- **Created**: 2025-10-19
- **Assigned**: Developer Name
```

### Bug Task File
```yaml
---
id: 15
title: '[BUG] Description'
type: bug_fix
status: pending
priority: critical
phase: 1
bug_reference: BUG-001
severity: critical
source: production
---
```

## Workflow Integration

### Reporting a Bug
1. User: "Report a bug - login button not working"
2. Skill activates and gathers bug details
3. Creates BUGS.md entry
4. Creates bug fix task
5. Updates TASKS.md

### Using Commands
1. User: `@g-bug-report`
2. Command guides bug reporting
3. Creates structured bug documentation

## Feature Matrix

| Feature | Supported | Notes |
|---------|-----------|-------|
| Bug Classification (4 levels) | ✅ | Critical/High/Medium/Low |
| Source Attribution (4 types) | ✅ | User/Dev/Testing/Production |
| BUGS.md Format | ✅ | Structured markdown |
| Bug Task Integration | ✅ | Auto-creates task |
| Bug Lifecycle Tracking | ✅ | Status transitions |
| Retroactive Documentation | ✅ | Document past fixes |
| Quality Metrics | ✅ | Bug tracking stats |
| Quality Gates | ✅ | Review requirements |

## Best Practices

### 1. Shared Bug Tracking
- Keep `.gald3r/tracking/BUGS.md` in version control
- Bug tasks in `.gald3r/tasks/`

### 2. Use Commands for Quick Access
- `@g-bug-report` for new bugs
- `@g-bug-fix` for fixing bugs
- `@g-qa` for QA overview

### 3. Skill Activation
- Mention "bug", "issue", "fix" for natural activation

## Summary

the gald3r QA system provides structured bug tracking and quality management through Cursor's rules, skills, and commands.
