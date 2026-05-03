---
name: g-skl-test
description: Create, maintain, and run multi-level test plans (fast, comprehensive, regression) for gald3r systems and features. Use when creating test plans, running tests, checking test coverage gaps, doing code review, verification, or when preparing a release. Enforces C-013/C-014/C-015 constraints. Triggered by @g-test command and g-agnt-test agent.
---
# g-skl-test — Test Plan Management

**Files Owned**: `.gald3r/test-plans/`, `.gald3r/TEST_PLANS.md`

**Activate for**: create test plan, run tests, check test coverage, code review gate, verification gate, release gate, `@g-test`.

---

## Test Plan Levels

| Level | Name | When Required | Scope | Max Duration |
|-------|------|---------------|-------|--------------|
| L1 | **Fast** | Every PR / code review / verification gate | Unit tests, smoke tests, happy-path | < 5 min |
| L2 | **Comprehensive** | Feature completion, sprint closure | Integration, edge cases, error paths | < 30 min |
| L3 | **Regression** | Before any release / version bump | Full suite, previous bug scenarios, cross-subsystem | Unrestricted |

---

## Operations

### CREATE — Generate test plans for a subsystem or feature

**Steps**:

1. **Identify scope** — determine subsystem name or feature ID from context
2. **Derive test plan file path**: `.gald3r/test-plans/{scope}_L{1|2|3}.md`
3. **Check what exists**: scan `.gald3r/test-plans/` for matching files
4. **Create missing plans** using the template below (one file per level)
5. **Register in TEST_PLANS.md** — add rows for each new plan
6. **If called from code review / verification**: also run AUDIT (see below)

**File naming convention**:
```
.gald3r/test-plans/{subsystem-or-feature-slug}_L1_fast.md
.gald3r/test-plans/{subsystem-or-feature-slug}_L2_comprehensive.md
.gald3r/test-plans/{subsystem-or-feature-slug}_L3_regression.md
```

**Test Plan File Template**:
```markdown
---
scope: "{subsystem_or_feature}"
level: L1 | L2 | L3
level_name: fast | comprehensive | regression
status: draft | active | passing | failing
last_run: null
created: YYYY-MM-DD
---

# Test Plan — {scope} — {Level Name}

## Objective
[What this test level verifies]

## Test Cases

| ID | Description | Type | Expected Result | Status |
|----|-------------|------|-----------------|--------|
| T-001 | [test description] | unit/integration/e2e/manual | [expected] | pending |

## Setup / Teardown
[Any environment setup needed]

## Pass Criteria
- [ ] All test cases pass
- [ ] No regressions introduced
- [L2+] [ ] Edge cases covered
- [L3 only] [ ] All previous bug scenarios pass

## Notes
```

---

### AUDIT — Check for missing test plans (called during review/verification)

**Steps**:

1. Read `.gald3r/SUBSYSTEMS.md` — get all `active` subsystems
2. Read `.gald3r/TASKS.md` — get all `completed` and `in-progress` tasks to find features/subsystems under test
3. For each active subsystem, check if all 3 test plan files exist in `.gald3r/test-plans/`
4. For each gap found, **create a task** via `g-skl-tasks` CREATE TASK:
   - Title: `Create {Level} test plan for {scope}`
   - Type: `documentation`
   - Priority: `high` (L1 missing) | `medium` (L2/L3 missing)
   - Subsystems: `[testing, {scope}]`
5. Report:

```
TEST PLAN AUDIT:
  auth (L1 fast):           ✅ EXISTS
  auth (L2 comprehensive):  ✅ EXISTS
  auth (L3 regression):     ⚠️ MISSING — Task NNN created
  api (L1 fast):            ⚠️ MISSING — Task NNN created
  ...
  Gaps found: N | Tasks created: N
```

---

### RUN — Execute tests for a specific level

**Steps**:

1. Read the test plan file for the specified scope + level
2. For each test case, determine if it's automatable or manual
3. For automated tests: look for test files in the project (e.g. `tests/`, `__tests__/`, `spec/`)
4. Run automated tests via shell if test runner available
5. For manual tests: print checklist for human verification
6. Update `status` and `last_run` in the test plan file frontmatter
7. Report pass/fail per test case

---

### RELEASE-GATE — Pre-release check (enforces C-015)

**Called before any version bump or release tag.**

1. Run AUDIT across all active subsystems
2. Verify L2 (comprehensive) exists and has `status: passing` for all subsystems in scope
3. Verify L3 (regression) exists and has `status: passing` for all subsystems in scope
4. Any missing or non-passing L2/L3 plan → **BLOCK RELEASE** with list of gaps
5. Report:

```
RELEASE GATE:
  L2 comprehensive — auth:    ✅ passing (last run: YYYY-MM-DD)
  L2 comprehensive — api:     ❌ MISSING — RELEASE BLOCKED
  L3 regression — auth:       ✅ passing (last run: YYYY-MM-DD)
  L3 regression — api:        ⚠️ never run — RELEASE BLOCKED
  ...
  VERDICT: BLOCKED — fix 2 gaps before releasing
```

---

### VERIFICATION-GATE — Pre-[🔍] check (enforces C-014)

**Called when a task is submitted for verification.**

1. Determine the subsystem(s) from the task YAML
2. Check that L1 (fast) test plan exists for each subsystem
3. If L1 exists: confirm it has been run (`last_run` is not null and `status: passing`)
4. If L1 missing → AUDIT creates task, BLOCK verification
5. Report:

```
VERIFICATION GATE:
  auth (L1 fast): ✅ passing — proceed to [🔍]
  api (L1 fast):  ❌ not run — mark as failing, block [🔍]
```

---

## TEST_PLANS.md Index Format

```markdown
# TEST_PLANS.md — {project_name}

| Scope | Level | File | Status | Last Run |
|-------|-------|------|--------|----------|
| auth | L1 fast | test-plans/auth_L1_fast.md | passing | 2026-04-10 |
| auth | L2 comprehensive | test-plans/auth_L2_comprehensive.md | draft | — |
```

---

## Integration Points

- **g-skl-review / g-skl-code-review**: call AUDIT at end of review pass
- **g-skl-tasks → `[🔍]` gate**: call VERIFICATION-GATE before marking awaiting-verification
- **Release process**: call RELEASE-GATE before any version bump
- **g-agnt-test**: autonomous agent that runs this skill's operations on schedule or trigger
