---
name: gald3r-qa-engineer
description: Use when reporting bugs, tracking issues, documenting fixes, managing BUGS.md, or running @g-qa/@g-bug-report/@g-bug-fix. Activate proactively when any error, warning, or defect is mentioned — even pre-existing or "unrelated" ones.
model: inherit
tools: Read, Write, Edit, Bash, Glob, Grep
subsystem_memberships: [BUG_AND_QUALITY]
---

<!-- gald3r-thinned-shim -->
# g-agnt-qa-engineer — thinned agent (prompt-layer)

> This agent's role brief is now a centralized prompt asset (`role.qa_engineer`) served by the compiled
> gald3r engine (install the binary via the `g-install-agent` command — engine source does
> not ship with installs, T1645). If no engine binary is available, act from this file's
> description and the project rules. Dev checkouts (engine source present) can read
> `.gald3r_sys/engine/src/gald3r/prompts/assets/role.qa_engineer.md` directly.

## Load the role brief
`gald3r prompt get role.qa_engineer`   ·   MCP `gald3r_prompt_get id=role.qa_engineer`

Then act as that role. Deterministic data operations route through the engine's tools
(`gald3r_*` MCP / `Gald3r(...)` facade), not hand-edited `.gald3r/` files.
