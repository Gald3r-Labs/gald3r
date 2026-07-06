---
name: g-skl-platform-zcode
description: Authoritative reference for ZCode (Z.ai / Zhipu, GLM-5.2 Agentic Development Environment) customization in gald3r projects. Covers the two-scope AGENTS.md convention (global-then-workspace, no imports/hierarchy), native Agent Skills (SKILL.md), native slash commands, Beta global-only subagents, native MCP, the absent hooks surface, and gald3r install verification.
crawl_max_age_days: 14
vault_doc_path: research/platforms/zcode/
vault_docs_url: https://zcode.z.ai/en/docs/welcome
docs_url: https://zcode.z.ai/en/docs/agents
docs_url_secondary:
  - https://zcode.z.ai/en/docs/mcp-services
  - https://zcode.z.ai/en/docs/subagents
  - https://zcode.z.ai/en/docs/skill
  - https://zcode.z.ai/en/docs/commands
  - https://zcode.z.ai/en/docs/plugin
last_doc_scan: 2026-07-03
capability_status:
  hooks: "❌ no published event taxonomy/schema for hand-authored hooks (plugin-bundled hooks only, undocumented)"
  rules: "✅ two-scope AGENTS.md (global ~/.zcode/AGENTS.md appended by workspace AGENTS.md); flat, no imports"
  skills: "✅ native Agent Skills (SKILL.md) in .zcode/skills/, name+description frontmatter, $name invocation"
  commands: "✅ native slash commands .zcode/commands or workspace dir (.md prompt files), /name invocation"
  agents: "⚠️ Beta subagents ~/.zcode/agents/*.md — global/user-level ONLY, no project-level roster yet"
  mcp: "✅ native MCP via Settings UI (Form/Full-config JSON), stdio/HTTP/SSE, import from Claude Code/Codex/OpenCode"
token_budget: low
subsystem_memberships: [PLATFORM_INTEGRATION]
---

# g-skl-platform-zcode

Activate for: setting up gald3r with ZCode (Z.ai / Zhipu ADE), authoring commands/skills/AGENTS.md for ZCode, or verifying the ZCode gald3r install.

---

> Full 9-section breakdown + evidence URLs in `PLATFORM_SPEC.md` (this folder). **Status: ⚠️
> partial parity** — ZCode natively supports rules (AGENTS.md), Agent Skills, slash commands, and
> MCP. Subagents are Beta and **global/user-level only** (no project-level roster). There is **no**
> published hooks/lifecycle-event system for hand-authored hooks. (Verified 2026-07-03 against
> https://zcode.z.ai/en/docs/agents and the ZCode docs nav.)

## 1. Platform Overview

**ZCode** (`zcode.z.ai`) — Z.ai's free, cross-platform **Agentic Development Environment** built
around **GLM-5.2**, with **BYOK** support for other model providers. Positioned to challenge Cursor,
Claude Code, and GitHub Copilot. It is a desktop app with Settings panels (not a bare CLI config
file) for MCP, Skills, Commands, and Subagents, plus a Plugin marketplace.

## 2. Config Layout

```
<project-root>/
├── AGENTS.md                        ← workspace instructions (appended AFTER global ~/.zcode/AGENTS.md)
└── .zcode/
    └── skills/   <name>/SKILL.md    ← Agent Skills (name/description frontmatter + body)

~/.zcode/
├── AGENTS.md                        ← global/user instructions — read FIRST
├── agents/   <name>.md              ← subagents (Beta) — GLOBAL/USER-LEVEL ONLY
├── commands/ <name>.md              ← custom slash commands (global scope)
└── skills/   <name>/SKILL.md        ← user-level skills

(MCP servers)                        ← Settings → MCP Servers (Form or Full-config JSON);
                                        persisted to a `.zcode` config file, exact path undocumented
```

> **Correction (vs. naive assumption):** ZCode does **not** hierarchically merge `AGENTS.md` the way
> Cursor/Qwen/Gemini do. It reads exactly two files — global then workspace — and **appends** them;
> there is no `@import`/`@include` and no per-subdirectory scan. Do not author a thin overlay that
> `@AGENTS.md`-imports the real rule set; inline the content directly into the workspace `AGENTS.md`.

## 3. gald3r Integration

**Cheapest high-parity install:** write gald3r's rule content directly into the workspace-root
`AGENTS.md` (no import mechanism to defer to), plus the `.zcode/skills/` tree for gald3r's
`g-skl-*/SKILL.md` files (drop-in, agentskills.io-compatible) and `.zcode/commands/` for simple
`@g-*` prompt-file commands.

### Verify
```powershell
Test-Path AGENTS.md              # workspace instructions (appended after ~/.zcode/AGENTS.md)
Test-Path .zcode/skills          # Agent Skills tree
```

## 4. Common Pitfalls

- `AGENTS.md` merge is **append-only, two-scope, no imports** — do not assume `@AGENTS.md` overlay
  patterns from Qwen/Gemini/Antigravity apply here.
- Subagents are **Beta and global/user-level only** — there is no project-level `agents/` folder to
  populate in a per-project overlay.
- There is **no** documented hooks/lifecycle-event system for hand-authored hooks — do not fabricate
  a `hooks.json`/settings-driven hook file. Plugin-bundled hooks exist but publish no schema.
- The MCP server config file's exact on-disk path/name is not published — servers are managed via
  Settings UI (Form mode or Full-configuration JSON paste).
- ZCode is a brand-new 2026 entrant — re-check docs on the next `@g-platform-scan-docs zcode`
  (crawl_max_age_days: 14) for project-level agents, hooks, and the MCP config path.

## 5. Capability Summary

| Feature | Status | Notes |
|---|---|---|
| Hooks (`g-hk-*.ps1`) | ❌ | no published event taxonomy/schema for hand-authored hooks; plugin-bundled hooks only, undocumented |
| Skills (`g-skl-*/SKILL.md`) | ✅ | native Agent Skills (`SKILL.md`) in `.zcode/skills/`, `name`/`description` frontmatter; `$name` chat invocation |
| Agents (`g-agnt-*.md`) | ⚠️ | Beta subagents `~/.zcode/agents/*.md` — global/user-level ONLY, no project-level roster |
| Commands (`@g-*`) | ✅ | `.zcode/commands/*.md` (User or Workspace scope); `/name` invocation; no `{{args}}` templating |
| Rules (`g-rl-*`) | ✅ | two-scope `AGENTS.md` (global `~/.zcode/AGENTS.md` appended by workspace `AGENTS.md`); flat, no imports |
| MCP | ✅ | Settings → MCP Servers (Form/Full-config JSON); stdio/HTTP/SSE; import from Claude Code/Codex/OpenCode |

Full assessment + evidence in `PLATFORM_SPEC.md`. Re-verify on the next `@g-platform-scan-docs zcode` (crawl_max_age_days: 14).
