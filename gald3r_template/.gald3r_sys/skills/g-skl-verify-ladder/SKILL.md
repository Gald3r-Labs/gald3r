---
name: g-skl-verify-ladder
description: >-
  Multi-level verification gates for autonomous task completion. Configurable
  levels from minimal (lint) to thorough (tests + acceptance + hallucination guard).
---

# g-verify-ladder

Configurable verification ladder that autonomous agents must pass before a task is marked complete.

## When to Use

- After implementing a task autonomously
- When manually verifying a task (`@g-verify-ladder <task_id>`)
- When a task has `verification_level` set in its YAML frontmatter

## When NOT to Use

- **During `g-setup` / project initialization** — no code exists yet, nothing to verify
- **During planning, spec-writing, or PRD creation** — doc-only work does not need lint/test verification
- **Before a task is `[🔄]` in-progress** — do not pre-emptively write evidence logs

## Verification Levels

| Level | When Used | What's Checked |
|-------|-----------|----------------|
| **minimal** | `blast_radius: low`, simple tasks | Lint/compile only |
| **standard** | Default for most tasks | Lint + tests + acceptance criteria |
| **thorough** | `blast_radius: medium/high` | Standard + artifact verification + hallucination guard |
| **manual** | `requires_verification: true` | All of thorough + human review required |

## Task YAML Configuration

Tasks can specify verification settings in their frontmatter:

```yaml
verification_level: standard
verification_commands:
  - "uv run python -m py_compile {changed_files}"
  - "uv run pytest tests/ -x --tb=short"
verification_artifacts:
  - path: "src/new_module.py"
    check: exists
  - path: ".gald3r/logs/task{id}_evidence.log"
    check: exists
max_fix_attempts: 3
```

If `verification_level` is not set, it's derived from `blast_radius`:
- `blast_radius: low` -> `minimal`
- `blast_radius: medium` -> `standard`
- `blast_radius: high` -> `thorough`
- `requires_verification: true` -> `manual`

## Verification Ladder (executed in order)

### Level 1: Syntax & Lint
- Run linter on changed files (detect language, use appropriate linter)
- Check for compile/parse errors
- On FAIL: auto-fix attempt (up to `max_fix_attempts`)

### Level 2: Tests
- Run `verification_commands` from task YAML
- Parse exit codes (0 = pass)
- On FAIL: auto-fix attempt, then escalate

### Level 3: Acceptance Criteria
- Read task file acceptance criteria (`- [ ]` items)
- Agent self-checks each criterion against actual changes
- Verify no unchecked items remain
- On FAIL: agent must address or explain

### Level 4: Artifact Verification
- Check `verification_artifacts` exist
- Validate files are not empty
- Check evidence log is populated
- On FAIL: agent must create missing artifacts

### Level 5: Hallucination Guard
- Check agent actually made file changes (`git diff --stat`)
- Verify tool calls were made (not just chat)
- Compare claimed changes to actual changes
- On FAIL: reject completion, log as hallucination

### Level 6: Human Review (manual level only)
- Set status to `awaiting-verification` [🔍]
- Different agent or human must verify
- PASS -> [✅], FAIL -> back to [🔄] with notes

## Auto-Fix Retry Loop

```
Verification failed at Level N
|
+-- Attempts remaining? (check max_fix_attempts)
|   YES -> Agent gets error output + "fix this and retry"
|          Agent makes changes
|          Re-run verification from Level N
|          Decrement attempts
|   NO  -> Escalate
|         +-- blast_radius: low -> mark failed, log reason
|         +-- blast_radius: medium -> add to WAKEUP_QUEUE for user
|         +-- blast_radius: high -> mark failed, block further work
```

## Verification Report

Written to `.gald3r/logs/task{id}_verification.md`:

```markdown
---
task_id: {id}
verification_level: standard
started: {ISO8601}
completed: {ISO8601}
result: passed|failed
attempts: N
---

# Verification Report: Task {id}

## Level 1: Syntax & Lint {pass/fail}
- Ran: {command}
- Result: {output}

## Level 2: Tests {pass/fail}
- Ran: {command}
- Result: {output}

## Level 3: Acceptance Criteria {pass/fail}
- [x] Criterion 1
- [x] Criterion 2

## Level 4: Artifacts {pass/fail}
- {path}: exists ({lines} lines)

## Level 5: Hallucination Guard {pass/fail}
- Files changed: N
- Tool calls made: N
```

## Integration Points

| System | How |
|--------|-----|
| g-verifier | Manual level triggers existing verification workflow |
| Heartbeat | Verification results feed into KPI metrics |
| WAKEUP_QUEUE | Failed thorough/high tasks create wakeup entries |

## Workflow for Agents

1. Read the task file to determine `verification_level` (or derive from `blast_radius`)
2. Execute levels in order, stopping at the level matching `verification_level`
3. For each level: run checks, capture output
4. On failure: attempt auto-fix up to `max_fix_attempts`
5. Write verification report to `.gald3r/logs/`
6. If all levels pass: mark task complete
7. If manual level: set to [🔍] for human review
