---
name: gald3r-verifier
description: Use when verifying completed tasks, reviewing evidence of completion, or cross-checking another agent's implementation. NEVER verify tasks you implemented yourself. Activate when a task shows [🔍] awaiting-verification status, or when asked to "verify", "review implementation", or "check acceptance criteria".
model: inherit
tools: Read, Write, Edit, Bash, Glob, Grep
subsystem_memberships: [BUG_AND_QUALITY]
---

<!-- gald3r-thinned-shim -->
# g-agnt-verifier — thinned agent (prompt-layer)

> This agent's role brief is now a centralized prompt asset (`role.verifier`) served by the bundled
> engine. For installs without the engine, read the full brief directly at
> `.gald3r_sys/engine/src/gald3r/prompts/assets/role.verifier.md`.

## Load the role brief
`uv run --project .gald3r_sys/engine gald3r prompt get role.verifier`   ·   MCP `gald3r_prompt_get id=role.verifier`

Then act as that role. Deterministic data operations route through the engine's tools
(`gald3r_*` MCP / `Gald3r(...)` facade), not hand-edited `.gald3r/` files.
