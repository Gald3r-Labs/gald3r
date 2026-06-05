---
name: gald3r-code-reviewer
description: Use when reviewing code, performing security audits, checking code quality, running @g-code-review, or after any significant implementation. Activate proactively after completing features or when the user says "review this", "check for security issues", or "is this code good?".
model: inherit
tools: Read, Write, Edit, Bash, Glob, Grep
subsystem_memberships: [BUG_AND_QUALITY]
---

<!-- gald3r-thinned-shim -->
# g-agnt-code-reviewer — thinned agent (prompt-layer)

> This agent's role brief is now a centralized prompt asset (`role.code_reviewer`) served by the bundled
> engine. For installs without the engine, read the full brief directly at
> `.gald3r_sys/engine/src/gald3r/prompts/assets/role.code_reviewer.md`.

## Load the role brief
`uv run --project .gald3r_sys/engine gald3r prompt get role.code_reviewer`   ·   MCP `gald3r_prompt_get id=role.code_reviewer`

Then act as that role. Deterministic data operations route through the engine's tools
(`gald3r_*` MCP / `Gald3r(...)` facade), not hand-edited `.gald3r/` files.
