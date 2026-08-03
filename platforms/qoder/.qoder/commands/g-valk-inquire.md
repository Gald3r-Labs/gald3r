---
description: 'Stream a grounded, cited answer from a project''s context via Valkyrie SSE ask/stream route'
argument-hint: '<question> [--project-id <id>] [--context-budget <n>] [--json]'
subsystem_memberships: [WORKSPACE_COORDINATION]
execution_tier: guarded_prompt
---
Typed, answerable Q&A against a project's grounded context via the streamed Valkyrie route: $ARGUMENTS

## What This Command Does

Runs `gald3r valk inquire` (`POST /api/v1/ask/stream`, SSE) — the same grounded-answer contract
as `@g-valk-ask` but over the streamed route. **Not** write-ahead queued: a live stream has no
sensible replay-later semantics, so an offline world_tree is reported directly rather than
deferred. Uses `g-skl-valk`.

## Workflow

### 1. Collect the Question
- **Question**: the natural-language question (required)
- **Target project** (`--project-id`): which project's context to ground the answer in
- **Context budget** (`--context-budget`): optional token cap on assembled context

### 2. Run
```bash
gald3r valk inquire "<question>" [--project-id <id>] [--context-budget <n>] [--json]
```

### 3. Report
Print the streamed answer. If world_tree is offline, report that directly — do not tell the
user to wait for a sync/flush retry (this verb has no queue). If the response is HTTP 409
`no_provider_available`, this is the known BUG-235 account-side gap, not a transport failure —
recommend `@g-valk-ask` only if the queued-retry semantics are acceptable for this question.

## Usage Examples

```
@g-valk-inquire "What is the current release version?" --context-budget 4000
```

## Delegates To
`g-skl-valk`
