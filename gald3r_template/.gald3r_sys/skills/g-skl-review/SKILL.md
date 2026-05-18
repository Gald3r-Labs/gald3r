---
name: g-skl-review
description: Code review for security, quality, performance, reusability; structured report with severity and actions.
---
# gald3r-review

## When to Use
@g-code-review or after significant code changes. Reviews files changed in the current session or specified files.

## Steps

1. **Determine scope**:
   - Recent changes: `git diff --name-only HEAD~1` or `git status`
   - Specified files: review those directly
   - Determine review depth by total lines changed

2. **Security scan** (ALWAYS FIRST):
   - SQL: look for f-strings or `.format()` in database queries
   - XSS: look for `innerHTML =` with user data
   - Auth: routes/functions missing auth decorators
   - Secrets: hardcoded strings matching API key patterns
   - Input validation: user input used directly without sanitization

3. **Quality analysis**:
   - File size violations (> 800 lines → must flag)
   - Function length (> 100 lines → flag)
   - Naming conventions (snake_case Python, camelCase JS)
   - Error handling (bare `except:` → flag)

4. **Reusability check** (HIGH priority):
   - Is any logic duplicated 3+ times across files? → extract to `lib/`
   - Are utility functions defined inline? → move to `lib/utils/`
   - Are magic numbers hardcoded? → extract to `lib/config/constants`
   - Does new code use existing shared modules?

5. **Performance scan**:
   - N+1 query patterns in loops
   - Unbounded DB queries (no LIMIT)
   - Missing indexes on frequently-filtered columns
   - Synchronous operations that should be async

6. **Generate review report**:
```markdown
# Code Review: [Feature/Change Name]
**Date**: YYYY-MM-DD
**Recommendation**: Approve | Request Changes | Comment

## 🔴 Security (CRITICAL — Must Fix)
- [Issue]: [Fix]

## 🟡 Quality Issues
- [File] is NNN lines — consider refactoring
- [Function] is NNN lines — break into smaller functions

## 🔵 Performance
- [Pattern]: [Recommendation]

## 🟢 Reusability
- [Logic] duplicated in [file1] and [file2] — extract to lib/utils/
- [Constant] hardcoded — move to lib/config/constants

## Action Items
1. [ ] Fix CRITICAL: [issue]
2. [ ] Refactor: [what]
3. [ ] Extract: [what → where]
```

7. **Create tasks for critical findings**:
   - 🔴 CRITICAL security → immediate task (`priority: critical`)
   - Files > 800 lines → refactoring task
