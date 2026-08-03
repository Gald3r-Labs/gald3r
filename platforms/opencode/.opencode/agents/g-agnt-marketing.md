---
name: gald3r-marketing
description: Marketing voice and copy for gald3r projects - draft launch posts, announcements, and landing copy. Loads the voice.marketing prompt asset; activate when asked to write marketing or promotional content.
subsystem_memberships: [AGENT_ORCHESTRATION]
---

<!-- gald3r-thinned-shim -->
# g-agnt-marketing — thinned agent (prompt-layer)

> This agent's role brief is now a centralized prompt asset (`voice.marketing`) served natively by
> gald3r_core's own package-embedded prompt library (`gald3r prompt get`, T298) — ships with
> every gald3r_core install; no vendored engine or dev checkout required. If `gald3r` isn't on
> PATH, act from this file's description and the project rules.

## Load the role brief
`gald3r prompt get voice.marketing` (MCP `gald3r_prompt_get id=voice.marketing` -- served over stdio by `gald3r mcp serve`; hosts add {"command": "gald3r", "args": ["mcp", "serve"]} to their MCP config)

Then act as that role. Deterministic data operations route through the engine's tools
(`gald3r_*` MCP / `Gald3r(...)` facade), not hand-edited `.gald3r/` files.
