---
description: 'Ask another project a grounded, cited question via Valkyrie (gald3r valk ask), queuing if offline'
argument-hint: '<question> [--project-id <id>] [--context-budget <n>] [--json]'
subsystem_memberships: [WORKSPACE_COORDINATION]
execution_tier: guarded_prompt
---
Ask another project a realtime peer-to-peer question via Valkyrie: $ARGUMENTS

## What This Command Does

Runs `gald3r valk ask` (`POST /api/v1/ask`) to get a grounded answer — with citations — from
another project's own state (task/bug status, PROJECT.md/PLAN.md, constraints, vault snippets)
without creating a WPAC request/task record. Write-ahead queued: if world_tree is unreachable,
the question is queued and retried on the next `@g-valk-sync`. Uses `g-skl-valk`.

## Workflow

### 1. Collect the Question
- **Question**: the natural-language question (required)
- **Target project** (`--project-id`): which project's context to ground the answer in
  (default: the answering server's own default project)
- **Context budget** (`--context-budget`): optional token cap on assembled context

### 2. Run
```bash
gald3r valk ask "<question>" [--project-id <id>] [--context-budget <n>] [--json]
```

### 3. Report
Print the answer and its citations. If the call queued instead of delivering (offline), say so
explicitly and note it will retry via `@g-valk-sync` / `gald3r workspace outbox flush`. If the
response is HTTP 409 `no_provider_available`, this is the known BUG-235 account-side
provider/entitlement gap — do not treat it as a transport failure.

## Usage Examples

```
@g-valk-ask "Is the auth endpoint task still blocked?" --project-id gald3r_agent_dev
```

## Delegates To
`g-skl-valk`
