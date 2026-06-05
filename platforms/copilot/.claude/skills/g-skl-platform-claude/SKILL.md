---
name: g-skl-platform-claude
description: Authoritative reference for Claude Code (Anthropic) customization in gald3r projects. Covers .claude/ commands/agents/skills/hooks/rules + settings.json hooks/MCP, CLAUDE.md (imports @AGENTS.md, NOT AGENTS.md-native), plugins/Agent SDK/Routines/Channels, and gald3r install verification.
crawl_max_age_days: 7
vault_doc_path: research/platforms/claude-code/
vault_docs_url: https://code.claude.com/docs/en/overview
docs_url: https://code.claude.com/docs/en/overview
docs_url_secondary:
  - https://code.claude.com/docs/en/hooks
  - https://code.claude.com/docs/en/sub-agents
  - https://code.claude.com/docs/en/skills
  - https://code.claude.com/docs/en/memory
  - https://code.claude.com/docs/en/mcp
  - https://code.claude.com/docs/en/plugins
last_doc_scan: 2026-06-02
capability_status:
  hooks: "✅ native lifecycle hooks in settings.json '\"hooks\"' (PascalCase: SessionStart/PreToolUse/PostToolUse/Stop/…; PreToolUse blocks; .ps1 supported) — NOT lowercase hooks.json"
  rules: "✅ CLAUDE.md persistent instructions + .claude/rules/*.md (paths: glob) + auto memory MEMORY.md — advisory, use PreToolUse hook for hard enforcement"
  skills: "✅ Agent Skills (agentskills.io SKILL.md) in .claude/skills/<name>/SKILL.md — progressive disclosure"
  commands: "✅ native slash commands .claude/commands/*.md (legacy) OR .claude/skills/<name>/SKILL.md → /<name> (merged into Skills)"
  agents: "✅ native subagents .claude/agents/*.md (md + YAML; built-in Explore/Plan/general-purpose; ~7 parallel)"
  mcp: "✅ native — .mcp.json + settings.json mcpServers + claude mcp add (stdio/http/sse/ws)"
token_budget: low
subsystem_memberships: [PLATFORM_INTEGRATION]
---

# g-skl-platform-claude

Activate for: setting up gald3r with Claude Code (Terminal CLI / VS Code / JetBrains / Desktop / Web), authoring commands/agents/skills/hooks/rules, wiring hooks via `settings.json`, or verifying the Claude Code gald3r install.

---

> Full 9-section breakdown + evidence URLs in `PLATFORM_SPEC.md` (this folder). **Status: ✅ full
> parity** — Claude Code natively supports commands, rules, agents, skills, hooks, and MCP (plus
> Plugins, Agent SDK, Routines, Channels), with native subagents + Agent Skills as strengths over the
> Cursor reference. Two platform truths: it reads **`CLAUDE.md`, NOT `AGENTS.md`** (import `@AGENTS.md`),
> and hooks live in **`settings.json`** with **PascalCase** events (NOT a lowercase `hooks.json`).
> (Verified 2026-06-02 against https://code.claude.com/docs.)

## 1. Platform Overview

**Claude Code** — Anthropic's agentic coding tool. The **same engine** runs across the Terminal CLI
(`claude`), VS Code, JetBrains, the Desktop app, Web (`claude.ai/code`), iOS, Slack (`@Claude`), and
Chrome; `CLAUDE.md`, settings, and MCP servers carry across all surfaces. Headless `claude -p`, session
continuation (`--continue`/`--resume`), and the Agent SDK (TS/Python) cover scripted and multi-agent use.

## 2. Config Layout

```
<project-root>/
├── CLAUDE.md                      ← read by Claude (imports @AGENTS.md); also ./.claude/CLAUDE.md
├── CLAUDE.local.md                ← personal overrides (gitignored)
├── .mcp.json                      ← project-scoped MCP servers (committable)
└── .claude/
    ├── settings.json              ← hooks ("hooks") + MCP ("mcpServers") + permissions
    ├── settings.local.json        ← user-local overrides (gitignored)
    ├── rules/    *.md             ← path-scoped modular rules (optional paths: glob)
    ├── commands/ *.md             ← custom slash commands (legacy; merged into Skills)
    ├── agents/   *.md             ← subagents (markdown + YAML)
    ├── skills/   <name>/SKILL.md  ← Agent Skills (agentskills.io standard) → /<name>
    └── hooks/    *.ps1            ← hook scripts referenced from settings.json
```

User-global tree at `~/.claude/` (CLAUDE.md, settings.json, agents/skills/commands); auto memory at
`~/.claude/projects/<project>/memory/MEMORY.md`. `.claude/skills/` is also consumed by OpenCode and
Copilot → keep skill content platform-neutral.

## 3. gald3r Integration

**Cheapest full-parity install: ship gald3r's `.claude/` tree (+ `.claude/CLAUDE.md` importing
`@AGENTS.md`)** — Claude Code loads it natively. Or package a Claude-Code-format **plugin bundle**
(skills + agents + hooks + MCP) and publish via a marketplace (`/plugin install`). Wire hooks under
`settings.json` `"hooks"` with **PascalCase** events; reserve `PreToolUse` for the `.gald3r/`
agent-required guard and any hard-enforcement constraint a rules file cannot guarantee.

### Verify
```powershell
Test-Path .claude/settings.json                              # hooks + MCP config
Test-Path .claude/CLAUDE.md ; Select-String '@AGENTS.md' .claude/CLAUDE.md
Test-Path .claude/commands ; Test-Path .claude/skills ; Test-Path .claude/agents
Test-Path .mcp.json                                          # if using project-scoped MCP
```

## 4. Common Pitfalls

- **Instruction file is `CLAUDE.md`, NOT `AGENTS.md`** — `AGENTS.md` is read only via `@AGENTS.md`
  import or symlink (and `/init` ingestion). Always ship the import.
- **Hooks live in `settings.json` `"hooks"` with PascalCase events** (`SessionStart`, `PreToolUse`,
  `PostToolUse`, `Stop`, …), three-level nesting (event → matcher → `hooks[]`). The legacy lowercase
  `hooks.json` (`sessionStart`/`stop`/`beforeShellExecution`) is the documented gap — migrate it.
  `beforeShellExecution` has **no** Claude Code equivalent → use `PreToolUse` with a `Bash` matcher.
- **Rules/memory are advisory context, not hard enforcement** — for guaranteed always-on constraints
  use a `PreToolUse` hook, not a `CLAUDE.md`/rules file. Auto memory requires v2.1.59+.
- **Commands merged into Skills** — `/<name>` resolves from `.claude/commands/<name>.md` OR
  `.claude/skills/<name>/SKILL.md`.
- Use `.md` (not Cursor's `.mdc`) for rule files — parity sync swaps the extension.

## 5. Capability Summary

| Feature | Status | Notes |
|---|---|---|
| Hooks (`g-hk-*.ps1`) | ✅ | `settings.json` `"hooks"`; PascalCase events (SessionStart/PreToolUse/PostToolUse/Stop/…); `PreToolUse` blocks; `.ps1` supported |
| Skills (`g-skl-*/SKILL.md`) | ✅ | agentskills.io; `.claude/skills/<name>/SKILL.md`; progressive disclosure; also read by OpenCode/Copilot |
| Agents (`g-agnt-*.md`) | ✅ | native subagents `.claude/agents/` (md + YAML); built-in Explore/Plan/general-purpose; ~7 parallel |
| Commands (`@g-*`) | ✅ | `.claude/commands/*.md` (legacy) OR `.claude/skills/<name>/SKILL.md` → `/<name>` |
| Rules (`g-rl-*`) | ✅ | `CLAUDE.md` + `.claude/rules/*.md` (`paths:` glob) + auto memory; advisory (use `PreToolUse` for enforcement) |
| MCP | ✅ | `.mcp.json` + `.claude/settings.json` `"mcpServers"` + `claude mcp add`; stdio/http/sse/ws |

Plus Plugins, Agent SDK (TS/Python), Routines (cron via `/schedule`), and Channels — see
`PLATFORM_SPEC.md` §9.

Full assessment + evidence in `PLATFORM_SPEC.md`. Re-verify on the next `@g-platform-scan-docs claude`
(crawl_max_age_days: 7). Docs moved `docs.anthropic.com/en/docs/claude-code` → `code.claude.com/docs`.
