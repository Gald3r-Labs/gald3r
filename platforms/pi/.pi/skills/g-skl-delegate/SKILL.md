---
name: g-skl-delegate
description: Engineering team delegation workflow skill — delegation patterns adapted for AI agent orchestration. Task briefs, code review request templates, quality gates, and handoff protocols.
token_budget: medium
subsystem_memberships: [AGENT_ORCHESTRATION]
---

# g-skl-delegate — Engineering Team Delegation Workflow

Encodes delegation patterns for treating AI agents as a full engineering team. Pairs with `g-go` (coordinator), `g-go-code` (executor), and `g-go-review` (reviewer).

## When to Use

- Delegating a task to a `g-go-code` executor (write the task brief first)
- Requesting a code review (scope the review to prevent scope creep)
- Coordinating a multi-agent implementation + review cycle
- Doing a quality gate check before marking a task `[🔍]`
- Establishing clear ownership during handoffs between agent sessions

---

## Engineering Team Roles

These roles map to gald3r's `g-go` pipeline:

| Role | gald3r command | Responsibilities |
|------|---------------|-----------------|
| **Planner** | `@g-plan`, `@g-propose` | Defines the work: PRD, task spec, acceptance criteria |
| **Coder** | `@g-go-code` | Pure executor — implements only, never reviews own work |
| **Reviewer** | `@g-go-review` | Independent adversarial review — never reviews work they wrote |
| **Coordinator** | `@g-go` | Routes tasks, reconciles results, writes shared state |

**Hard rule**: Never have the same agent implement AND review. The reviewer must be a fresh session with no implementation context.

---

## Task Brief Template

Use this before delegating any non-trivial task to `@g-go-code`.

```markdown
## Task Brief — T{id}: {title}

### Problem Statement
[One paragraph: what is wrong or missing, and why it matters right now]

### Context
- Codebase area: [which files/subsystems are affected]
- Related tasks: [T{ids} — what was done recently that this builds on]
- Constraints active: [C-{ids} from CONSTRAINTS.md that apply]
- Dependencies: [what must be done first; what cannot change]

### Objective
[One sentence: what does "done" look like from the user's perspective]

### Deliverable Format
- Files changed: [which files should be created/modified/deleted]
- Interface: [what the output looks like — API, UI, file, command]
- Not in scope: [explicit list of things the coder should NOT touch]

### Acceptance Criteria
- [ ] {criterion 1 — observable, testable}
- [ ] {criterion 2}
- [ ] {criterion 3}

### Deadline / Priority
- Priority: [critical / high / medium / low]
- Target: [session / today / sprint]
```

**Tips**:
- "Not in scope" prevents the coder from gold-plating or drifting
- ACs should be verifiable by the reviewer without asking the coder
- If the brief takes longer than 10 minutes to write, the task needs splitting

---

## Code Review Request Template

Use this when requesting a review from `@g-go-review` or a fresh agent session.

```markdown
## Review Request — T{id}: {title}

### What to Review
[Be explicit — vague "look it over" requests produce vague feedback]

- Primary concern: [security / correctness / performance / architecture / all]
- Changed files: [list the specific files that changed]
- Diff context: [what the code did before vs what it does now]

### What to Skip
[Explicit skip list prevents reviewer scope creep]
- Skip: [file X — intentionally deferred to T{follow-up}]
- Skip: [style/formatting — covered by linter]
- Skip: [test coverage — will be added in T{follow-up}]

### Review Depth
- [ ] Quick scan (5 min) — correctness only, no nitpicks
- [ ] Standard review — correctness + style + obvious risks
- [ ] Deep review — full OWASP/STRIDE pass, architecture assessment

### Success Criteria for LGTM
[What must be true for the reviewer to PASS this task]
- No critical/high security findings
- AC items verified as testable
- No scope violations (nothing from "Not in scope" was touched)

### Known Risks
[Tell the reviewer what to watch for — saves time]
- Risk: {area} — [why this is tricky]
```

**Tips**:
- Always include the task spec link so reviewer can check AC alignment
- "What to skip" is as important as "what to review" — scope creep kills reviews
- The reviewer should never need to ask the coder to explain the intent

---

## Quality Gate Checklists

### Feature Gate (before `[🔍]`)

```
FEATURE QUALITY GATE — T{id}

Implementation
[ ] All AC items satisfied (each item has evidence, not just "done")
[ ] No scope violations (nothing outside the task spec was changed)
[ ] No new TODO/FIXME without follow-up task (g-rl-34)
[ ] CHANGELOG.md updated if user-facing behavior changed (g-rl-26)

Code Quality
[ ] No new linter errors introduced
[ ] Security: no hardcoded credentials, tokens, or secrets
[ ] No empty catch/except blocks
[ ] Stubs annotated with TODO[TASK-X→TASK-Y] if present

Docs / Tests
[ ] Function-level documentation for public interfaces
[ ] Error messages are user-friendly (not raw stack traces)
[ ] Existing tests still pass (or test failures explained)

Verdict: [ ] LGTM  [ ] FAIL — reason: ________________
```

### Bug Fix Gate (before `[🔍]`)

```
BUG FIX QUALITY GATE — BUG-{id}

[ ] Root cause identified (not just symptom patched)
[ ] Fix is minimal (does not refactor unrelated code)
[ ] Regression test added or existing test now covers the case
[ ] Related code paths reviewed for same bug pattern
[ ] BUGS.md status updated to "fixed" with resolution note

Verdict: [ ] LGTM  [ ] FAIL — reason: ________________
```

### Refactor Gate (before `[🔍]`)

```
REFACTOR QUALITY GATE — T{id}

[ ] Zero behavior changes (same inputs → same outputs)
[ ] All callers of changed interfaces updated
[ ] Impact scan run: `.claude/skills/g-skl-muninn/scripts/graph_impact.py -File <path>` (T921)
[ ] No new public API surface introduced (scope: internal only)
[ ] Performance: refactor does not regress benchmarks

Verdict: [ ] LGTM  [ ] FAIL — reason: ________________
```

---

## Handoff Protocol

The implementation → review → ship sequence with explicit ownership at each step.

### Step 1: Coder Completes Implementation

Coder (g-go-code) must do before `[🔍]`:
1. Self-check each AC item — annotate evidence in task file's `## Agent Notes`
2. Annotate any stubs with `TODO[TASK-X→TASK-Y]` per g-rl-34
3. Update CHANGELOG.md if user-facing
4. Create a code-complete checkpoint commit
5. Write handoff note in task `## Agent Notes`:

```
[AGENT:cursor-coder] [2026-05-09T14:23:00Z]
Implementation complete. Checkpoint commit: abc1234.
AC items verified: all 4 passing.
Known risk: edge case in L142 of payments.py — see TODO comment.
Reviewer should focus on: the new retry logic in src/retry.py.
```

### Step 2: Reviewer Claims and Inspects

Reviewer (g-go-review, fresh session) must:
1. Read the task spec + implementation plan + coder's Agent Notes
2. Create a `review` worktree from the checkpoint commit (never mutate coder's tree)
3. Run quality gate checklist for the task type
4. Write verdict in task `## Status History` + `## Agent Notes`:

```
[AGENT:cursor-reviewer] [2026-05-09T15:05:00Z]
PASS. All 4 AC items verified independently. No security findings.
Retry logic in src/retry.py: correct exponential backoff, max_retries enforced.
One advisory finding: variable name `x` in L88 — suggest renaming (non-blocking).
```

### Step 3: Coordinator Ships

Coordinator (g-go):
1. Reads PASS/FAIL verdict
2. PASS → moves task to `[✅]`, updates TASKS.md
3. FAIL → returns task to `[📋]` with FAIL reason in Status History
4. Creates review-result commit
5. Notifies user with summary

### Ownership Transfer Rules

| Phase | Owner | May write to task file? |
|-------|-------|------------------------|
| `[📋]` → `[🔄]` | Coder | Yes — implementation notes |
| `[🔄]` → `[🔍]` | Coder → Reviewer | Coder writes last Agent Note, then hands off |
| `[🔍]` → `[🕵️]` | Reviewer | Yes — review verdict only |
| `[🕵️]` → `[✅]` | Coordinator | Yes — status, TASKS.md, commit |

**Hard rule**: reviewer never writes to implementation files. Coder never writes review verdicts.

---

## Delegation Anti-Patterns

| Anti-Pattern | Problem | Fix |
|--------------|---------|-----|
| Vague task brief ("make it better") | Coder invents scope, reviewer can't verify | Write explicit ACs |
| Same agent implements + reviews | No adversarial independence | Fresh session for review |
| Review without "what to skip" | Reviewer goes down rabbit holes | Always include skip list |
| Marking `[✅]` without quality gate | Unverified completion | Run gate checklist before `[🔍]` |
| Monolithic task (>5 ACs) | Hard to review, hard to verify | Split into 3–5 AC max per task |
| Implicit deadlines | Reviewer doesn't know urgency | State priority explicitly in brief |

---

## Vault Reference

Session notes from delegation pattern experiments: `{vault_location}/projects/{project}/decisions/`

