---
name: g-skl-platform-junie
description: Authoritative reference for JetBrains Junie (IDE plugin + Junie CLI) customization in gald3r projects. Covers .junie/ commands/agents/skills + AGENTS.md guidelines + mcp.json + EAP SessionStart hooks, the extension bundle, and gald3r install verification.
crawl_max_age_days: 14
vault_doc_path: research/platforms/junie/
vault_docs_url: https://junie.jetbrains.com/docs
docs_url: https://junie.jetbrains.com/docs
docs_url_secondary:
  - https://junie.jetbrains.com/docs/custom-slash-commands.html
  - https://junie.jetbrains.com/docs/guidelines-and-memory.html
  - https://junie.jetbrains.com/docs/junie-cli-subagents.html
  - https://junie.jetbrains.com/docs/agent-skills.html
  - https://junie.jetbrains.com/docs/junie-cli-hooks.html
  - https://junie.jetbrains.com/docs/junie-cli-mcp-configuration.html
last_doc_scan: 2026-06-02
capability_status:
  hooks: "⚠️ EAP SessionStart-only hooks in config.json (personal ~/.junie/config.json; project hooks ignored); no PreToolUse/PostToolUse/pre-commit; JUNIE-1961 tracks more"
  rules: "✅ guidelines/memory via AGENTS.md (project > global ~/.junie/AGENTS.md; legacy .junie/guidelines.md still read); injected into every task"
  skills: "✅ Agent Skills (agentskills.io SKILL.md) in .junie/skills/ user+project; progressive disclosure; JetBrains IDEs + CLI"
  commands: "✅ custom slash commands .junie/commands/*.md (/name, $arg named args) — CLI"
  agents: "✅ native subagents .junie/agents/ (md + YAML; auto-delegated by name/description) — CLI"
  mcp: "✅ native — .junie/mcp/mcp.json (shared CLI + IDE), local + remote servers"
token_budget: low
subsystem_memberships: [PLATFORM_INTEGRATION]
---

# g-skl-platform-junie

Activate for: setting up gald3r with JetBrains Junie (IDE plugin or Junie CLI), authoring commands/agents/skills + `AGENTS.md` guidelines + MCP, or verifying the Junie gald3r install.

---

> Full 9-section breakdown + evidence URLs in `PLATFORM_SPEC.md` (this folder). **Status: ✅ near-full
> parity** — the **Junie CLI** natively supports commands, rules (`AGENTS.md`), subagents, Agent
> Skills, and MCP; **hooks are ⚠️ PARTIAL** (SessionStart-only, Early Access). Instruction convention
> is **`AGENTS.md`** (NOT `CLAUDE.md`). (Verified 2026-06-02 against https://junie.jetbrains.com/docs.)

## 1. Platform Overview

**JetBrains Junie** — JetBrains' agentic AI coding assistant, delivered as **two surfaces**: a
**Junie IDE plugin** (IntelliJ IDEA, PyCharm, WebStorm, GoLand, RubyMine, Rider, …) and a standalone
**Junie CLI** (cross-platform, **BYO-LLM / model-agnostic**). The **CLI** is the full-extensibility
surface; the **IDE plugin** is narrower (`AGENTS.md` guidelines + Agent Skills + MCP). Subagents,
custom slash commands, and hooks are CLI features. Junie uses the IDE's PSI index for context and runs
in CI/CD via the `junie-on-github` GitHub Action.

## 2. Config Layout

```
<project-root>/
├── AGENTS.md                       ← root guidelines (always-on; CLI + IDE) — NOT CLAUDE.md
└── .junie/
    ├── AGENTS.md                   ← preferred project guidelines (injected into every task)
    ├── guidelines.md               ← LEGACY guidelines (deprecated, still read)
    ├── commands/ *.md              ← custom slash commands (/name, $arg) — CLI
    ├── agents/   *.md              ← subagents (md + YAML; auto-delegated) — CLI (.agents/ also read)
    ├── skills/   <name>/SKILL.md   ← Agent Skills (agentskills.io standard)
    ├── mcp/mcp.json                ← MCP servers (shared CLI + IDE format)
    └── config.json                 ← CLI settings (model/provider, *-locations, hooks block)
```

User scope (`~/.junie/`) mirrors all of the above; **project `AGENTS.md` wins over global**, and
**project `config.json` hooks are ignored** — personal hooks live in `~/.junie/config.json`.

## 3. gald3r Integration

**Cheapest high-parity install: ship gald3r's `.junie/` tree** (commands + agents + skills + MCP) +
`AGENTS.md`. Or package everything as a single Junie **extension** (skills + subagents + commands +
guidelines + MCP — note: **extensions exclude hooks**) for one-artifact team distribution. Subagents
are **auto-delegated** by `name`/`description`, so author `g-agnt-*` files with strong descriptions.

### Verify
```powershell
Test-Path .junie/AGENTS.md ; Test-Path AGENTS.md      # guidelines (AGENTS.md, not CLAUDE.md)
Test-Path .junie/commands ; Test-Path .junie/agents ; Test-Path .junie/skills
Test-Path .junie/mcp/mcp.json                          # MCP servers
```

## 4. Common Pitfalls

- **Instruction file is `AGENTS.md`** — Junie does NOT read `CLAUDE.md` / `GEMINI.md`. Project
  `.junie/AGENTS.md` / root `AGENTS.md` > global `~/.junie/AGENTS.md`; legacy `.junie/guidelines.md`
  still read.
- **Two surfaces**: full extensibility is **CLI-only**; the IDE plugin is narrower (guidelines +
  skills + MCP). Subagents / slash commands / hooks are CLI features.
- **Hooks are ⚠️ EAP + SessionStart-only**: no PreToolUse/PostToolUse/pre-commit/file-watch; project
  `config.json` hooks are ignored (use personal `~/.junie/config.json`); the **extension** bundle
  excludes hooks. Degrade pre-commit / pre-tool gates to git `core.hooksPath` or manual runs.
- **Subagents are auto-delegated only** — they cannot be invoked manually via slash commands.
- **BYO-LLM**: switching models mid-session can reset accumulated agent context/memory.

## 5. Capability Summary

| Feature | Status | Notes |
|---|---|---|
| Hooks (`g-hk-*.ps1`) | ⚠️ | `config.json` `hooks` **SessionStart-only**, **Early Access**; personal `~/.junie/config.json` (project hooks ignored); no pre-tool/pre-commit/file-watch; JUNIE-1961 tracks more |
| Skills (`g-skl-*/SKILL.md`) | ✅ | agentskills.io Agent Skills; `.junie/skills/` user+project; progressive disclosure; JetBrains IDEs + CLI |
| Agents (`g-agnt-*.md`) | ✅ | native subagents `.junie/agents/` (md + YAML); auto-delegated by name/description (CLI) |
| Commands (`@g-*`) | ✅ | custom slash commands `.junie/commands/*.md` (`/name`, `$arg` named args) (CLI) |
| Rules (`g-rl-*`) | ✅ | guidelines via `AGENTS.md` (project > global; legacy `.junie/guidelines.md`); injected into every task |
| MCP | ✅ | `.junie/mcp/mcp.json` (shared CLI + IDE), local + remote servers, MCP Installation Assistant |

Full assessment + evidence in `PLATFORM_SPEC.md`. Re-verify on the next `@g-platform-scan-docs junie` (crawl_max_age_days: 14) — confirm whether hooks exit EAP / gain new events (JUNIE-1961).
