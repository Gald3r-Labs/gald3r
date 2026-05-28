Activate quality assurance system: $ARGUMENTS

## What This Command Does

Activates the quality assurance system for bug tracking, quality management, and fix documentation.

## QA Features

### 1. Bug Tracking System
I'll manage bugs in `.gald3r/BUGS.md` with:
- **Bug Classification**:
  - Critical: System crashes, data loss, security vulnerabilities
  - High: Major feature failures, >50% performance loss
  - Medium: Minor feature issues, usability problems
  - Low: Cosmetic issues, enhancement requests
- **Source Attribution**: User Reported, Development, Testing, Production
- **Status Tracking**: Open → Investigating → Fixing → Testing → Closed

### 2. Bug-Task Integration
When bugs are reported, I'll:
- Create entry in BUGS.md
- Create corresponding task file with `[BUG]` prefix
- Set priority based on severity
- Link bug to affected phases
- Track resolution through task completion

### 3. Retroactive Fix Documentation
For fixes completed during chat, I'll:
- Assess if work merits task documentation
- Generate retroactive task entry
- Update TASKS.md with completed status
- Capture lessons learned

**Document as retroactive task if:**
- ✅ Fix required >15 minutes of work
- ✅ Solution affects multiple files or subsystems
- ✅ Fix provides value for future reference
- ✅ Resolution required technical analysis

### 4. Quality Metrics
I track:
- Bug Discovery Rate: Bugs found per development cycle
- Bug Resolution Time: Average time from discovery to fix
- Severity Distribution: Breakdown by severity level
- Phase Impact: Which phases have most bugs
- Regression Rate: Fixes that introduce new bugs

### 5. Quality Gates
I verify:
- Code Review: All changes reviewed
- Testing Requirements: Unit, integration, manual tests
- Documentation: Code comments, API docs
- Performance: No regression in benchmarks
- Security: Vulnerability scanning

## When to Use
- Reporting bugs or issues
- Documenting fixes completed in chat
- Setting up quality processes
- Managing bug lifecycle
- Generating quality reports

## What I Need From You
- Bug description or quality concern
- Severity assessment (if bug)
- Affected areas or phases

Let's ensure quality!
