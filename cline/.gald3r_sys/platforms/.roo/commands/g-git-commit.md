---
description: Structured gald3r git commit (conventional format + task reference)
argument-hint: [scope/summary]
---

# gald3r Git Commit

Create a structured gald3r commit:

1. Run a pre-commit sanity check: no secrets/keys/`.env` values staged; no protected
   gitignored paths (`.gald3r/`, `.env`, `.mcp.json`, personalized `AGENTS.md`/`CLAUDE.md`).
2. Use the conventional format: `{type}({scope}): {brief description}` where type is one of
   feat | fix | refactor | docs | test | chore | phase.
3. Reference the task in the body: `Task: #{id}` (or `Bug: BUG-{id}`).
4. Subject line <= 72 chars, imperative mood.
5. NEVER push automatically — offer the push and wait for confirmation.

Scope/summary: $ARGUMENTS
