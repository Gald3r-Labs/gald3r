---
name: g-skl-code-review
description: Code review — security, quality, performance, reusability. Structured report with severity ratings and action items. Scales from quick scan to comprehensive architecture review.
---
# g-skl-code-review

**Activate for**: `@g-code-review`, `@g-code-review`, "review this code", "check before commit", "PR review", security scan, quality assessment.

---

## Step 1: Determine Scope and Depth

```
Recent changes: git diff --name-only HEAD~1
Specified files: review those directly

< 100 lines  → Quick Review  (~5 min)
100-500 lines → Standard Review (~15 min)
> 500 lines   → Comprehensive Review (~45 min)
```

---

## Step 2: Security Scan (ALWAYS FIRST)

- **SQL injection**: f-strings or `.format()` in DB queries
- **XSS**: `innerHTML =` with user-controlled data
- **Auth**: routes/functions missing auth decorators or guards
- **Secrets**: hardcoded strings matching API key/token patterns
- **Input validation**: user input used directly without sanitization
- **Sensitive data**: PII logged, stored unencrypted, or in URLs

---

## Step 3: Code Quality

- File size > 800 lines → must flag for extraction
- Function/method > 100 lines → flag, suggest decomposition
- Naming: snake_case (Python), camelCase (JS/TS), PascalCase (classes)
- Error handling: bare `except:` or empty `catch {}` → flag
- Cyclomatic complexity: deeply nested blocks (> 4 levels) → flag

---

## Step 4: Reusability (HIGH priority)

- Logic duplicated 3+ times across files → extract to `lib/`
- Utility functions defined inline in multiple places → move to `lib/utils/`
- Magic numbers hardcoded → extract to `lib/config/constants`
- Does new code use existing shared modules, or re-implement them?

---

## Step 5: Performance

- N+1 query patterns in loops
- Unbounded DB queries (no LIMIT/pagination)
- Missing indexes on frequently-filtered columns
- Synchronous operations that should be async
- Unnecessary re-computation inside loops
- Missing caching on expensive repeated calls

---

## Step 6: Maintainability (Comprehensive only)

- Architecture alignment with SUBSYSTEMS.md boundaries
- Test coverage for changed code
- Documentation completeness (public API, complex logic)
- Technical debt introduced vs. resolved
- SOLID principle violations

---

## Step 7: Generate Review Report

```markdown
# Code Review: [Feature/Change Name]
**Date**: YYYY-MM-DD
**Scope**: N files, N lines changed
**Depth**: Quick | Standard | Comprehensive
**Recommendation**: Approve | Request Changes | Comment

## 🔴 Security (CRITICAL — block merge)
- [Issue]: [File:line] — [Fix]

## 🟠 Quality Issues (should fix)
- [File] is NNN lines — extract [what] to [where]
- [Function] is NNN lines — decompose into [names]

## 🔵 Performance (consider fixing)
- [Pattern]: [Recommendation]

## 🟢 Reusability
- [Logic] duplicated in [file1] and [file2] — extract to lib/utils/
- [Constant] hardcoded — move to lib/config/constants

## ✅ Looks Good
- [What was done well]

## Action Items
- [ ] CRITICAL: [fix]
- [ ] Refactor: [what → where]
- [ ] Extract: [what → where]
```

---

## Step 8: Create Tasks for Critical Findings

- 🔴 Security CRITICAL → activate **g-skl-tasks CREATE** with `priority: critical`
- 🟠 File > 800 lines → activate **g-skl-tasks CREATE** as refactoring task
- 🟠 Duplicate logic (3-strike) → activate **g-skl-tasks CREATE** for extraction
