---
name: g-skl-platform-pi
description: Authoritative reference for Pi (badlogic/pi-mono terminal coding-agent harness) customization in gald3r projects. Covers hierarchical AGENTS.md/CLAUDE.md instructions, native Agent Skills (SKILL.md), native prompt-template slash commands, TypeScript-extension lifecycle hooks (pi.on events), the absent MCP surface, and gald3r install verification.
crawl_max_age_days: 14
vault_doc_path: research/platforms/pi/
vault_docs_url: https://pi.dev/docs/latest/usage
docs_url: https://pi.dev/docs/latest/usage
docs_url_secondary:
  - https://pi.dev/docs/latest/skills
  - https://pi.dev/docs/latest/prompt-templates
  - https://pi.dev/docs/latest/extensions
  - https://pi.dev/docs/latest/settings
  - https://github.com/badlogic/pi-mono/blob/main/packages/coding-agent/README.md
last_doc_scan: 2026-07-03
capability_status:
  hooks: "✅ native TypeScript extension event handlers (pi.on(event, handler)); no JSON config"
  rules: "✅ hierarchical AGENTS.md/CLAUDE.md concat (global ~/.pi/agent/AGENTS.md + walk-up); flat body, no glob scoping"
  skills: "✅ native Agent Skills (SKILL.md) in .pi/skills/ + .agents/skills/, name+description frontmatter, /skill:name invocation"
  commands: "✅ native prompt templates .pi/prompts/<name>.md (or global ~/.pi/agent/prompts/), /name invocation"
  agents: "❌ no project-level agents/*.md roster convention; only imperative extension session-spawning"
  mcp: "❌ explicitly unsupported by design — \"No MCP\" per the coding-agent README"
token_budget: low
subsystem_memberships: [PLATFORM_INTEGRATION]
---

# g-skl-platform-pi

Activate for: setting up gald3r with Pi (badlogic/pi-mono coding-agent CLI), authoring
skills/prompts/AGENTS.md/hooks for Pi, or verifying the Pi gald3r install.

---

> Full 9-section breakdown + evidence URLs in `PLATFORM_SPEC.md` (this folder). **Status: ⚠️
> partial parity** — Pi natively supports rules (hierarchical `AGENTS.md`), Agent Skills, prompt-
> template slash commands, and TypeScript-extension lifecycle hooks. There is **no** project-level
> subagent-roster convention and **no MCP support** (explicit design choice, not a gap). (Verified
> 2026-07-03 against https://pi.dev/docs/latest/usage and the linked docs pages.)

## 1. Platform Overview

**Pi** (`badlogic/pi-mono`, package `packages/coding-agent`) — a minimal, open-source terminal
coding-agent harness: "AI agent toolkit: unified LLM API, agent loop, TUI, coding agent CLI"
(67.5k+ GitHub stars). It is a bare CLI/TUI with **no GUI, no Settings panels, no marketplace** —
everything is files-on-disk plus TypeScript extensions.

## 2. Config Layout

```
<project-root>/
├── AGENTS.md                        ← project instructions (CLAUDE.md accepted as alias)
└── .pi/
    ├── skills/   <name>/SKILL.md    ← Agent Skills (name/description frontmatter + body)
    ├── prompts/  <name>.md          ← prompt templates == slash commands (/name)
    ├── extensions/ gald3r-hooks.ts  ← TypeScript lifecycle-hook extension
    └── settings.json                ← project settings (merges over global)

~/.pi/agent/                         ← global config root (override: $PI_CODING_AGENT_DIR)
├── AGENTS.md / SYSTEM.md / APPEND_SYSTEM.md
├── skills/ <name>/SKILL.md
├── prompts/ <name>.md
├── extensions/ <name>.ts
└── settings.json
```

> **Correction (vs. naive assumption):** Pi's `AGENTS.md` merge is a genuine **hierarchical
> directory-walk concatenation** (global + every parent dir + cwd) — NOT a flat two-scope append
> like ZCode. Hooks are **TypeScript code** (`pi.on(event, handler)`), not a `hooks.json` data
> file. There is **no MCP support** at all (explicit, per the README).

## 3. gald3r Integration

**Cheapest high-parity install:** ship gald3r's rule content in the project-root `AGENTS.md`
(hierarchical concat is compatible with a single-file install), the `.pi/skills/` tree for
gald3r's `g-skl-*/SKILL.md` files (drop-in, agentskills.io-compatible), `.pi/prompts/` for simple
`@g-*` prompt-template commands, and a single `.pi/extensions/gald3r-hooks.ts` TypeScript
extension for lifecycle hooks.

### Verify
```powershell
Test-Path AGENTS.md              # project instructions (hierarchical concat with ~/.pi/agent/AGENTS.md)
Test-Path .pi/skills             # Agent Skills tree
Test-Path .pi/prompts            # prompt-template commands
Test-Path .pi/extensions/gald3r-hooks.ts   # lifecycle-hook extension
```

## 4. Common Pitfalls

- `AGENTS.md` merge is **hierarchical** (global + walk-up + cwd, all concatenated) — do NOT apply
  ZCode's flat two-scope "inline everything into one file" caveat as strictly, though a single
  project-root file remains the simplest install.
- There is **no project-level `agents/*.md` roster** — do not fabricate one. Session-spawning is
  imperative extension code (`ctx.newSession()`, `ctx.fork()`), not a declarative file gald3r can
  drop in.
- **No MCP** — explicit design choice per the README ("No MCP. Build CLI tools with READMEs ...").
  Do not fabricate an `mcp.json`/`.mcp.json` file.
- **Hooks are TypeScript, not JSON** — the gald3r hook surface ships as a single `.ts` extension
  file registering multiple `pi.on(...)` handlers, not a `hooks.json` config.
- Pi is an actively developed OSS project (67.5k+ stars, frequent releases) — re-check docs on the
  next `@g-platform-scan-docs pi` (crawl_max_age_days: 14) for MCP or agents-roster additions.

## 5. Capability Summary

| Feature | Status | Notes |
|---|---|---|
| Hooks (`g-hk-*`) | ✅ | native TypeScript extension event handlers (`pi.on(...)`); no JSON config, code IS the hook |
| Skills (`g-skl-*/SKILL.md`) | ✅ | native Agent Skills (`SKILL.md`) in `.pi/skills/` + `.agents/skills/`; `name`/`description` frontmatter; `/skill:name` invocation |
| Agents (`g-agnt-*.md`) | ❌ | no project-level `agents/*.md` roster convention; only imperative extension session-spawning |
| Commands (`@g-*`) | ✅ | `.pi/prompts/*.md` (User or Workspace scope); `/name` invocation |
| Rules (`g-rl-*`) | ✅ | hierarchical `AGENTS.md`/`CLAUDE.md` concat (global `~/.pi/agent/AGENTS.md` + walk-up); flat body, no glob scoping |
| MCP | ❌ | explicitly unsupported by design ("No MCP" per README) |

Full assessment + evidence in `PLATFORM_SPEC.md`. Re-verify on the next `@g-platform-scan-docs pi` (crawl_max_age_days: 14).
