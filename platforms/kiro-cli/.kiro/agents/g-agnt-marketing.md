---
name: gald3r-marketing
description: Marketing voice and copy for gald3r projects - draft launch posts, announcements, and landing copy. Loads the voice.marketing prompt asset; activate when asked to write marketing or promotional content.
subsystem_memberships: [AGENT_ORCHESTRATION]
---

<!-- gald3r-thinned-shim -->
# g-agnt-marketing — thinned agent (prompt-layer)

> This agent's role brief is now a centralized prompt asset (`voice.marketing`) served by the bundled
> engine. For installs without the engine, read the full brief directly at
> `.gald3r_sys/engine/src/gald3r/prompts/assets/voice.marketing.md`.

## Load the role brief
`uv run --project .gald3r_sys/engine gald3r prompt get voice.marketing`   ·   MCP `gald3r_prompt_get id=voice.marketing`

Then act as that role. Deterministic data operations route through the engine's tools
(`gald3r_*` MCP / `Gald3r(...)` facade), not hand-edited `.gald3r/` files.
