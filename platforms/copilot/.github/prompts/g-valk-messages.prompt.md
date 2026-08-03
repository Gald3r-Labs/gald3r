---
description: 'List the durable Valkyrie events ledger (notifications, asks, inquiries) via gald3r valk messages'
argument-hint: '[--all] [--limit N] [--mark-read] [--json]'
subsystem_memberships: [WORKSPACE_COORDINATION]
execution_tier: orchestration
---
List the durable Valkyrie events ledger — notifications, inbound asks, and inquiries: $ARGUMENTS

## What This Command Does

Runs `gald3r valk messages` to list entries from the durable events ledger
(`.gald3r/valkyrie/messages/<date>.jsonl`) — every non-delegation world_tree event the resident
connector durably recorded. Defaults to unread-only, oldest-first. Safe no-op on an
empty/missing ledger. Uses `g-skl-valk`.

## Workflow

### 1. Determine Scope
- Unread-only (default) or `--all` (include already-read entries)
- Optional `--limit N` cap (applied after the unread filter, oldest-first)
- `--mark-read` to advance the durable read cursor for exactly the entries listed

### 2. Run
```bash
gald3r valk messages [--all] [--limit N] [--mark-read] [--json]
```

### 3. Report
List the events with timestamp, type, and source project. If `--mark-read` was used, confirm
how many entries advanced the read cursor.

## Usage Examples

```
@g-valk-messages --limit 5 --mark-read
@g-valk-messages --all
```

## Delegates To
`g-skl-valk`
