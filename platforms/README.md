# Platform reference docs — how each of the 38 supported tools actually works

One page per platform: its project structure, config surfaces, native extension
primitives (commands, rules, agents, skills, hooks, MCP), and exactly how gald3r
installs into it. Written for humans reviewing how things fit together — the same
documents the engine's own agents consult before touching a platform.

- Start with **[cursor](cursor.md)** — the reference platform all others derive from.
- The support matrix with per-component ✅/⚠/❌ lives at
  [../PLATFORM_SUPPORT.md](../PLATFORM_SUPPORT.md).
- Canonical source: each platform's `PLATFORM_SPEC.md` in the engine repo
  (`g-skl-platform-<name>/`), refreshed here periodically as the platform-docs
  monitor updates them. Pages marked *curated* are hand-assessed and not yet
  live-verified against the vendor's current docs.
