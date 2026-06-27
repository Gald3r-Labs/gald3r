# gald3r — Combined Platform Readiness (all 34 platforms)

> One consolidated view of every platform's gald3r readiness, generated from the single source
> `strategy/PLATFORM_DATA.json`. Per-platform long-form: each `gald3r_platform_<name>/READINESS.md`.
> Capability columns + matrix: `PLATFORM_CAPABILITY_MATRIX.md` (same source).

## Summary
- **32/34 platforms are MCP-native (Engine Level 2)** — the engine's 37 tools reach them directly.
  aider is CLI (L1); subq is files-only (L0).
- **5/34 ship a full native tree** (skills+commands+agents); the rest are thin/MCP — the
  build-out target (they support more than they currently ship).
- **The engine raises effective readiness everywhere:** where a native C.R.A.S.H. layer is ⚠️/❌, the
  deterministic behavior is delivered as engine tools (MCP/CLI), independent of the host. Every platform
  keeps a files-only `SKILL.full.md` floor.

## Per-platform readiness (sorted by engine tier)

### aider — ⚠️ Partial · Engine: CLI (L1)
`C ⚠ · R ✅ · A ⚠ · S ❌ · H ⚠ · MCP ❌` · rules `.md`

- **Gaps:** Skills(❌)
- **Engine lift:** the engine supplies the deterministic ops via CLI despite the gap above.
- **Beyond the guest layer:** → gald3r_agent (the native build).
### amp — ✅ Full · Engine: MCP (L2)
`C ✅ · R ✅ · A ⚠ · S ✅ · H ✅ · MCP ✅` · rules `.md`

- **Gaps:** none — native across the board
- **Engine lift:** every layer native — the engine consolidates (one core, not N copies).
- **Beyond the guest layer:** → gald3r_agent (the native build).
### antigravity — ✅ Full · Engine: MCP (L2)
`C ✅ · R ✅ · A ⚠ · S ✅ · H ✅ · MCP ✅` · rules `.md`

- **Gaps:** none — native across the board
- **Engine lift:** every layer native — the engine consolidates (one core, not N copies).
- **Beyond the guest layer:** → gald3r_agent (the native build).
### astrbot — ✅ Full · Engine: MCP (L2)
`C ✅ · R ✅ · A ✅ · S ✅ · H ✅ · MCP ✅` · rules `—`

- **Gaps:** none — native across the board
- **Engine lift:** every layer native — the engine consolidates (one core, not N copies).
- **Beyond the guest layer:** → gald3r_agent (the native build).
### augment — ✅ Full · Engine: MCP (L2)
`C ✅ · R ✅ · A ✅ · S ✅ · H ✅ · MCP ✅` · rules `.md`

- **Gaps:** none — native across the board
- **Engine lift:** every layer native — the engine consolidates (one core, not N copies).
- **Beyond the guest layer:** → gald3r_agent (the native build).
### claude — ✅ Full · Engine: MCP (L2)
`C ✅ · R ✅ · A ✅ · S ✅ · H ✅ · MCP ✅` · rules `.md`

- **Gaps:** none — native across the board
- **Engine lift:** every layer native — the engine consolidates (one core, not N copies).
- **Beyond the guest layer:** → gald3r_agent (the native build).
### cline — ✅ Full · Engine: MCP (L2)
`C ✅ · R ✅ · A ✅ · S ✅ · H ✅ · MCP ✅` · rules `.md`

- **Gaps:** none — native across the board
- **Engine lift:** every layer native — the engine consolidates (one core, not N copies).
- **Beyond the guest layer:** → gald3r_agent (the native build).
### codebuddy — ✅ Full · Engine: MCP (L2)
`C ✅ · R ✅ · A ✅ · S ✅ · H ✅ · MCP ✅` · rules `rules.md`

- **Gaps:** none — native across the board
- **Engine lift:** every layer native — the engine consolidates (one core, not N copies).
- **Beyond the guest layer:** → gald3r_agent (the native build).
### codex — ✅ Full · Engine: MCP (L2)
`C ✅ · R ✅ · A ✅ · S ✅ · H ✅ · MCP ✅` · rules `.md`

- **Gaps:** none — native across the board
- **Engine lift:** every layer native — the engine consolidates (one core, not N copies).
- **Beyond the guest layer:** → gald3r_agent (the native build).
### continue — ✅ Full · Engine: MCP (L2)
`C ✅ · R ✅ · A ⚠ · S ⚠ · H ✅ · MCP ✅` · rules `.md`

- **Gaps:** none — native across the board
- **Engine lift:** every layer native — the engine consolidates (one core, not N copies).
- **Beyond the guest layer:** → gald3r_agent (the native build).
### copilot — ✅ Full · Engine: MCP (L2)
`C ✅ · R ✅ · A ✅ · S ✅ · H ✅ · MCP ✅` · rules `.md`

- **Gaps:** none — native across the board
- **Engine lift:** every layer native — the engine consolidates (one core, not N copies).
- **Beyond the guest layer:** → gald3r_agent (the native build).
### cursor — ✅ Full · Engine: MCP (L2)
`C ✅ · R ✅ · A ✅ · S ✅ · H ✅ · MCP ✅` · rules `.mdc`

- **Gaps:** none — native across the board
- **Engine lift:** every layer native — the engine consolidates (one core, not N copies).
- **Beyond the guest layer:** → gald3r_agent (the native build).
### deepcode — ⚠️ Partial · Engine: MCP (L2)
`C ⚠ · R ✅ · A ❌ · S ✅ · H ❌ · MCP ✅` · rules `rules.md`

- **Gaps:** Agents(❌), Hooks(❌)
- **Engine lift:** the engine supplies the deterministic ops via MCP despite the gap above.
- **Beyond the guest layer:** → gald3r_agent (the native build).
### gemini — ✅ Full · Engine: MCP (L2)
`C ✅ · R ✅ · A ✅ · S ✅ · H ✅ · MCP ✅` · rules `.md`

- **Gaps:** none — native across the board
- **Engine lift:** every layer native — the engine consolidates (one core, not N copies).
- **Beyond the guest layer:** → gald3r_agent (the native build).
### goose — ✅ Full · Engine: MCP (L2)
`C ✅ · R ✅ · A ✅ · S ✅ · H ✅ · MCP ✅` · rules `.md`

- **Gaps:** none — native across the board
- **Engine lift:** every layer native — the engine consolidates (one core, not N copies).
- **Beyond the guest layer:** → gald3r_agent (the native build).
### hermes — ✅ Full · Engine: MCP (L2)
`C ✅ · R ✅ · A ✅ · S ✅ · H ✅ · MCP ✅` · rules `—`

- **Gaps:** none — native across the board
- **Engine lift:** every layer native — the engine consolidates (one core, not N copies).
- **Beyond the guest layer:** → gald3r_agent (the native build).
### junie — ⚠️ Partial · Engine: MCP (L2)
`C ✅ · R ✅ · A ✅ · S ✅ · H ⚠ · MCP ✅` · rules `.md`

- **Gaps:** none — native across the board
- **Engine lift:** every layer native — the engine consolidates (one core, not N copies).
- **Beyond the guest layer:** → gald3r_agent (the native build).
### kilo_code — ⚠️ Partial · Engine: MCP (L2)
`C ✅ · R ✅ · A ✅ · S ✅ · H ❌ · MCP ✅` · rules `—`

- **Gaps:** Hooks(❌)
- **Engine lift:** the engine supplies the deterministic ops via MCP despite the gap above.
- **Beyond the guest layer:** → gald3r_agent (the native build).
### kimi — ✅ Full · Engine: MCP (L2)
`C ✅ · R ✅ · A ✅ · S ✅ · H ✅ · MCP ✅` · rules `—`

- **Gaps:** none — native across the board
- **Engine lift:** every layer native — the engine consolidates (one core, not N copies).
- **Beyond the guest layer:** → gald3r_agent (the native build).
### kiro — ✅ Full · Engine: MCP (L2)
`C ✅ · R ✅ · A ✅ · S ✅ · H ✅ · MCP ✅` · rules `.md`

- **Gaps:** none — native across the board
- **Engine lift:** every layer native — the engine consolidates (one core, not N copies).
- **Beyond the guest layer:** → gald3r_agent (the native build).
### kiro_cli — ✅ Full · Engine: MCP (L2)
`C ✅ · R ✅ · A ✅ · S ✅ · H ✅ · MCP ✅` · rules `—`

- **Gaps:** none — native across the board
- **Engine lift:** every layer native — the engine consolidates (one core, not N copies).
- **Beyond the guest layer:** → gald3r_agent (the native build).
### mistral — ⚠️ Partial · Engine: MCP (L2)
`C ⚠ · R ⚠ · A ✅ · S ✅ · H ⚠ · MCP ✅` · rules `rules.md`

- **Gaps:** none — native across the board
- **Engine lift:** every layer native — the engine consolidates (one core, not N copies).
- **Beyond the guest layer:** → gald3r_agent (the native build).
### openclaw — ✅ Full · Engine: MCP (L2)
`C ✅ · R ✅ · A ✅ · S ✅ · H ✅ · MCP ✅` · rules `.md`

- **Gaps:** none — native across the board
- **Engine lift:** every layer native — the engine consolidates (one core, not N copies).
- **Beyond the guest layer:** → gald3r_agent (the native build).
### opencode — ✅ Full · Engine: MCP (L2)
`C ✅ · R ✅ · A ✅ · S ✅ · H ✅ · MCP ✅` · rules `.md`

- **Gaps:** none — native across the board
- **Engine lift:** every layer native — the engine consolidates (one core, not N copies).
- **Beyond the guest layer:** → gald3r_agent (the native build).
### openhands — ✅ Full · Engine: MCP (L2)
`C ✅ · R ✅ · A ✅ · S ✅ · H ✅ · MCP ✅` · rules `.md`

- **Gaps:** none — native across the board
- **Engine lift:** every layer native — the engine consolidates (one core, not N copies).
- **Beyond the guest layer:** → gald3r_agent (the native build).
### qoder — ✅ Full · Engine: MCP (L2)
`C ✅ · R ✅ · A ✅ · S ✅ · H ✅ · MCP ✅` · rules `.md`

- **Gaps:** none — native across the board
- **Engine lift:** every layer native — the engine consolidates (one core, not N copies).
- **Beyond the guest layer:** → gald3r_agent (the native build).
### qwen — ✅ Full · Engine: MCP (L2)
`C ✅ · R ✅ · A ✅ · S ✅ · H ✅ · MCP ✅` · rules `.md`

- **Gaps:** none — native across the board
- **Engine lift:** every layer native — the engine consolidates (one core, not N copies).
- **Beyond the guest layer:** → gald3r_agent (the native build).
### replit — ⚠️ Partial · Engine: MCP (L2)
`C ❌ · R ✅ · A ⚠ · S ✅ · H ❌ · MCP ✅` · rules `.md`

- **Gaps:** Commands(❌), Hooks(❌)
- **Engine lift:** the engine supplies the deterministic ops via MCP despite the gap above.
- **Beyond the guest layer:** → gald3r_agent (the native build).
### roo — ⚠️ Partial · Engine: MCP (L2)
`C ✅ · R ✅ · A ✅ · S ✅ · H ❌ · MCP ✅` · rules `.md`

- **Gaps:** Hooks(❌)
- **Engine lift:** the engine supplies the deterministic ops via MCP despite the gap above.
- **Beyond the guest layer:** → gald3r_agent (the native build).
### trae — ⚠️ Partial · Engine: MCP (L2)
`C ⚠ · R ✅ · A ✅ · S ✅ · H ❌ · MCP ✅` · rules `.md`

- **Gaps:** Hooks(❌)
- **Engine lift:** the engine supplies the deterministic ops via MCP despite the gap above.
- **Beyond the guest layer:** → gald3r_agent (the native build).
### void — ⚠️ Partial · Engine: MCP (L2)
`C ❌ · R ✅ · A ❌ · S ❌ · H ❌ · MCP ✅` · rules `.cursorrules`

- **Gaps:** Commands(❌), Agents(❌), Skills(❌), Hooks(❌)
- **Engine lift:** the engine supplies the deterministic ops via MCP despite the gap above.
- **Beyond the guest layer:** → gald3r_agent (the native build).
### warp — ✅ Full · Engine: MCP (L2)
`C ⚠ · R ✅ · A ✅ · S ✅ · H ❌ · MCP ✅` · rules `.md`

- **Gaps:** Hooks(❌)
- **Engine lift:** the engine supplies the deterministic ops via MCP despite the gap above.
- **Beyond the guest layer:** → gald3r_agent (the native build).
### windsurf — ✅ Full · Engine: MCP (L2)
`C ✅ · R ✅ · A ⚠ · S ✅ · H ✅ · MCP ✅` · rules `.md`

- **Gaps:** none — native across the board
- **Engine lift:** every layer native — the engine consolidates (one core, not N copies).
- **Beyond the guest layer:** → gald3r_agent (the native build).
### subq — ❌ Not a host · Engine: files-only (L0)
`C ❌ · R ❌ · A ❌ · S ❌ · H ❌ · MCP ❌` · rules `.md`

- **Gaps:** Commands(❌), Rules(❌), Agents(❌), Skills(❌), Hooks(❌)
- **Engine lift:** the engine supplies the deterministic ops via files-only despite the gap above.
- **Beyond the guest layer:** → gald3r_agent (the native build).

---
<sub>Generated from `PLATFORM_DATA.json` by `gen_platform_docs.py`. Re-run after a platform-docs crawl
updates the capability data. This merges the former `PLATFORM_MATRIX`/`PLATFORM_ADAPTERS` (capability +
layout) with the canonical `_platform_capabilities.json` (installer rule/skill dirs) into one system.</sub>
