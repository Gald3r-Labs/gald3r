---
name: g-skl-platform-openhands
description: Authoritative reference for OpenHands (All Hands AI, formerly OpenDevin) AI agent customization in gald3r projects. Covers AGENTS.md context, .agents/skills + .agents/agents File-Based Agents, .openhands/hooks.json lifecycle hooks, config.toml MCP, Plugins bundle, and gald3r install verification.
crawl_max_age_days: 14
vault_doc_path: research/platforms/openhands/
vault_docs_url: https://docs.openhands.dev
docs_url: https://docs.openhands.dev
docs_url_secondary:
  - https://docs.openhands.dev/sdk/guides/plugins
  - https://docs.openhands.dev/sdk/guides/skill.md
  - https://docs.openhands.dev/sdk/guides/agent-file-based.md
  - https://docs.openhands.dev/openhands/usage/customization/hooks
  - https://docs.openhands.dev/openhands/usage/settings/mcp-settings
  - https://docs.openhands.dev/overview/skills/repo.md
last_doc_scan: 2026-06-02
capability_status:
  hooks: "✅ native lifecycle hooks in .openhands/hooks.json (PreToolUse/PostToolUse/UserPromptSubmit/Stop/SessionStart/SessionEnd; stdin JSON; deny decisions)"
  rules: "✅ AGENTS.md always-on (injected at conversation start) + General Skills; CLAUDE.md/GEMINI.md variants"
  skills: "✅ Agent Skills (extended AgentSkills SKILL.md) in .agents/skills (> deprecated .openhands/skills/microagents); .claude/skills accepted"
  commands: "✅ Plugin commands/*.md + Agent Skills as /skill-name (no standalone per-repo command file)"
  agents: "✅ File-Based Agents .agents/agents/*.md (md + YAML) + DelegateTool sub-agents; advanced via SDK register_agent()"
  mcp: "✅ native — config.toml [mcp] stdio/SSE/SHTTP + Settings UI + plugin .mcp.json"
token_budget: low
subsystem_memberships: [PLATFORM_INTEGRATION]
---

# g-skl-platform-openhands

Activate for: setting up gald3r with OpenHands (SDK / CLI / GUI / Cloud), authoring File-Based Agents / Agent Skills / lifecycle hooks / MCP / Plugins, or verifying the OpenHands gald3r install.

---

> Full 9-section breakdown + evidence URLs in `PLATFORM_SPEC.md` (this folder). **Status: ✅ full
> parity** — OpenHands V1 natively supports commands, rules, agents, skills, hooks, and MCP, reads
> **`AGENTS.md`** (not `CLAUDE.md`) as the always-on file, follows the AgentSkills `SKILL.md`
> standard, and accepts `.claude/skills/`, so gald3r's Agent-Skills artifacts are largely reusable.
> (Verified 2026-06-02 against https://docs.openhands.dev.)

## 1. Platform Overview

**OpenHands** (All Hands AI, formerly OpenDevin) is an open-source agentic AI software developer
built on the **Software Agent SDK (V1)** (Apache-2.0, model-agnostic via LiteLLM). The **same
file-based extension config** drives every surface — **CLI, local GUI, Cloud, and Enterprise** — and
OpenHands is also exposed as an **ACP agent** (Zed) and delegatable from other agents (e.g. Hermes).
The deepest extensibility (`register_agent()` factories, custom tools/visualizers, the `AgentFactory`
registry) is **SDK/Python-level**; the file primitives below cover the gald3r-relevant surface.

## 2. Config Layout

```
<project-root>/
├── AGENTS.md                        ← always-on instruction file (NOT CLAUDE.md; injected at start)
│                                       CLAUDE.md / GEMINI.md recognized as variants
├── config.toml                      ← [mcp] sse_servers / shttp_servers (+ stdio)
├── .agents/                         ← RECOMMENDED modern tree
│   ├── skills/  <name>/SKILL.md     ← Agent Skills (extended AgentSkills standard)
│   └── agents/  *.md                ← File-Based Agents (markdown + YAML)
├── .openhands/                      ← legacy / config-side tree (still honored)
│   ├── hooks.json                   ← lifecycle event hooks
│   ├── skills/  …                   ← DEPRECATED skills location
│   ├── agents/  …                   ← agents (priority 2)
│   └── microagents/ repo.md         ← DEPRECATED always-on rules (legacy)
└── .plugin/plugin.json              ← Plugin — bundles skills+hooks+agents+commands+MCP
```

**Directory migration**: target the modern **`.agents/`** tree. `.openhands/skills/` and
`.openhands/microagents/` are **deprecated** (still honored by older versions). `.claude/skills/` is
also accepted → **gald3r's Agent-Skills tree works as-is on OpenHands.**

## 3. gald3r Integration

**Cheapest high-parity install:** write the `.agents/` tree (skills + agents) + **`AGENTS.md`** +
`.openhands/hooks.json` + `config.toml [mcp]` — OpenHands discovers it. Or package a single
**Plugin** bundle (skills + hooks + agents + commands + MCP via `.plugin/plugin.json`) and publish
to the **OpenHands/extensions** registry / Cloud Plugin Launcher.

- **Instruction file is `AGENTS.md`** — unlike Augment, OpenHands does **not** require `CLAUDE.md`.
  Write gald3r's always-on rules into `AGENTS.md` (or modular General Skills).
- **Hooks** fire via `.openhands/hooks.json` (six events, stdin JSON, deny decisions). Wrap gald3r
  `.ps1` hooks in a shell command (`pwsh -File ...`).
- **Commands** ship as Skills-as-commands (`/skill-name`) and/or a Plugin `commands/` dir — there is
  no standalone per-repo command-file format.

### Verify
```powershell
Test-Path AGENTS.md                              # always-on instruction file (canonical)
Test-Path .agents/skills ; Test-Path .agents/agents
Test-Path .openhands/hooks.json                  # lifecycle hooks
Test-Path config.toml                            # [mcp] servers
```

## 4. Common Pitfalls

- **`AGENTS.md`, not `CLAUDE.md`** is the canonical instruction file — `CLAUDE.md` / `GEMINI.md` are
  recognized variants only. Keep always-on context lean (loaded every session).
- **Target `.agents/`, not `.openhands/`** — `.openhands/skills/` and `.openhands/microagents/` are
  deprecated; older OpenHands versions in the wild may still expect the microagents paths.
- **No first-class command file** — deliver `/g-*` via Skills-as-commands or a Plugin `commands/`
  dir; the slash-command menu only landed in the May 2026 update.
- **Advanced agents are code-only** — File-Based Agents (`.agents/agents/*.md`) cover the basics;
  `DelegateTool` parallel orchestration and `register_agent()` factories require Python.
- **MCP over stdio**: prefer a proxy (e.g. SuperGateway) and `config.toml [mcp]` SSE/SHTTP for
  reliability; per-tool timeouts are 1–3600s, with API-key + OAuth (FastMCP) auth.

## 5. Capability Summary

| Feature | Status | Notes |
|---|---|---|
| Hooks (`g-hk-*` via `pwsh`) | ✅ | `.openhands/hooks.json`; PreToolUse/PostToolUse/UserPromptSubmit/Stop/SessionStart/SessionEnd; stdin JSON; `{"decision":"deny"}` |
| Skills (`g-skl-*/SKILL.md`) | ✅ | extended AgentSkills; `.agents/skills` (> deprecated `.openhands/skills`/`microagents`); `.claude/skills` accepted |
| Agents (`g-agnt-*.md`) | ✅ | File-Based Agents `.agents/agents/*.md` (md + YAML) + `DelegateTool`; advanced via SDK `register_agent()` |
| Commands (`@g-*`) | ✅ | Plugin `commands/*.md` + Skills as `/skill-name` (no standalone per-repo command file) |
| Rules (`g-rl-*`) | ✅ | `AGENTS.md` always-on + General Skills; `CLAUDE.md`/`GEMINI.md` variants; no `.mdc` glob engine |
| MCP | ✅ | `config.toml [mcp]` stdio/SSE/SHTTP + Settings UI + plugin `.mcp.json` |

Full assessment + evidence in `PLATFORM_SPEC.md`. Re-verify on the next `@g-platform-scan-docs openhands` (crawl_max_age_days: 14).
