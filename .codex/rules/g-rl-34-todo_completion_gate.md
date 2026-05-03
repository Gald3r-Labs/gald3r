---
description: "Stub/TODO annotation gate — tasks marked complete with stubs, mocks, or TODOs must carry forward-linking comments and spawned follow-up tasks"
globs:
alwaysApply: true
---

# TODO Completion Gate

Fires whenever a task is marked `[✅]` completed. If the implementation contains **any** incomplete element, the agent MUST annotate it AND spawn a follow-up task before the completion is considered valid.

## What Triggers This Rule

Mark the task as incomplete (or add mandatory annotation) when ANY of the following exist in code written for this task:

| Pattern | Examples |
|---|---|
| TODO / FIXME comments | `# TODO`, `// TODO`, `/* FIXME */`, `-- TODO` |
| Stub function bodies | `pass`, `...`, `return None  # stub`, `throw new Error("not implemented")` |
| NotImplementedError | `raise NotImplementedError`, `todo!()` (Rust), `unimplemented!()` |
| Hardcoded / mock data | `FAKE_`, `MOCK_`, `TEST_`, `PLACEHOLDER_`, `"dummy"`, `"example.com"`, `12345` as real IDs |
| Hardcoded credentials or keys | Any literal string that looks like a key, token, password, or secret |
| Commented-out real logic | Sections replaced with `# real logic goes here` or similar |
| Empty except/catch blocks | `except: pass`, `catch (e) {}` with no handling |

## Mandatory Actions (BOTH required — not optional)

### 1. Annotate the code with a TODO comment

**Format** (use the comment syntax of the file's language):

```
TODO[TASK-{original_id}→TASK-{follow_up_id}]: {what is stubbed} — fix in follow-up task
```

**Examples by language:**

```python
# TODO[TASK-42→TASK-67]: Stub — replace with real Stripe payment processor call
def charge_card(amount):
    return {"status": "ok"}  # stub
```

```javascript
// TODO[TASK-15→TASK-23]: Hardcoded user ID — replace with auth context lookup
const userId = "abc-123-fake";
```

```sql
-- TODO[TASK-8→TASK-31]: Stub procedure — implement real balance recalculation logic
```

```typescript
// TODO[TASK-101→TASK-112]: NotImplemented — wire up real notification service
throw new Error("not implemented");
```

The comment MUST appear **on the line directly above or on the same line as** the stub/hardcoded value.

### 2. Spawn a follow-up task via gald3r-task-manager

Activate `g-task-manager` and create a new task that:
- Has a title clearly describing what the stub replaces
- References the original task ID in `dependencies:` field
- Has `type: bug_fix` or `type: feature` as appropriate
- Captures the file path and line number where the stub lives

The new task ID becomes `{follow_up_id}` in the comment above.

## Sequence (Do Not Reorder)

1. Identify all stubs/TODOs in code written for the task
2. Create follow-up task(s) → get new task ID(s)
3. Add `TODO[TASK-X→TASK-Y]` comments to each stub location
4. THEN mark the original task `[✅]` in TASKS.md

**Marking complete BEFORE annotating = violation.**

## Multi-Stub Tasks

If a single completed task has multiple stubs, each stub gets:
- Its own `TODO[TASK-{original}→TASK-{new}]` comment
- Its own follow-up task (or a single consolidated follow-up task if they are closely related, with the same `{new_id}` in multiple comments)

## Rationalization Table

| Rationalization | Reality |
|---|---|
| "It's just a temporary stub, everyone knows" | In 3 weeks nobody knows. The comment costs 5 seconds. |
| "The task is done, the stub is a separate concern" | If you shipped a stub, the task is not done. Annotate it. |
| "I'll remember to fix it later" | You won't. The follow-up task ensures it lives in the backlog. |
| "The TODO is obvious from context" | Context rots. The task ID is permanent. |
| "It's a test/dev stub, not production" | Dev stubs reach production. Every. Single. Time. |
| "Creating a task takes too long" | Fast-path task creation takes 60 seconds. Debugging a mystery stub takes hours. |

## Exemptions (Narrow)

The following do NOT require follow-up tasks or annotation:
- `pass` as the **entire body** of an abstract base class method explicitly declared abstract
- `...` in a `.pyi` stub file (type stubs only)
- Test fixtures with clearly named fake data (e.g., `fake_user = {"name": "Test User"}` inside a test file)

When in doubt — annotate it.
