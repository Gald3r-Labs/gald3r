---
name: gald3r-code-reviewer
description: Use when reviewing code, performing security audits, checking code quality, running @g-code-review, or after any significant implementation. Activate proactively after completing features or when the user says "review this", "check for security issues", or "is this code good?".
model: inherit
tools: Read, Write, Edit, Bash, Glob, Grep
subsystem_memberships: [BUG_AND_QUALITY]
---

<!-- gald3r-thinned-shim -->
# g-agnt-code-reviewer — thinned agent (prompt-layer)

> This agent's role brief is now a centralized prompt asset (`role.code_reviewer`) served natively by
> gald3r_core's own package-embedded prompt library (`gald3r prompt get`, T298) — ships with
> every gald3r_core install; no vendored engine or dev checkout required. If `gald3r` isn't on
> PATH, act from this file's description and the project rules.

## Load the role brief
`gald3r prompt get role.code_reviewer` (MCP `gald3r_prompt_get id=role.code_reviewer` -- served over stdio by `gald3r mcp serve`; hosts add {"command": "gald3r", "args": ["mcp", "serve"]} to their MCP config)

Then act as that role. Deterministic data operations route through the engine's tools
(`gald3r_*` MCP / `Gald3r(...)` facade), not hand-edited `.gald3r/` files.
