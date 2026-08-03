---
description: 'Chat-native recall over vault notes and scoped memory records, merged and scope-ordered (T557 P4)'
argument-hint: '<query>'
subsystem_memberships: [MEMORY_AND_KNOWLEDGE]
execution_tier: orchestration
---
Recall memory: $ARGUMENTS

## What This Command Does

Runs `gald3r memory recall` -- a single, on-demand query over BOTH the
file-first vault (`.gald3r/vault/`) and the T557 scoped memory record store
(`.gald3r/memory/records/**`), merged into one scope-ordered
(most-specific-wins: user > project > workspace > team > company),
token-budgeted result. `client` scope is never included unless explicitly
requested.

## Workflow

1. Run `gald3r memory recall "$ARGUMENTS" --json` (omit `$ARGUMENTS` to
   browse everything in scope instead of matching a keyword).
2. Read the returned items: each carries `source` (`memory_record` or
   `vault_note`), `scope`, `confidence`, `relevance`, and a body `preview`.
3. Answer from the returned items directly.
4. If the result reports `"truncated": true`, note that lower-ranked
   matches exist but were dropped for the token budget -- rerun with
   `--budget N` for a larger budget if more detail is needed.
5. If a durable new fact emerges from this conversation, offer to save it
   back via `gald3r memory` (once a write verb lands, T557 P2) or
   `gald3r vault ingest`.
