---
name: g-skl-platform-replit
description: Authoritative reference for Replit Agent (cloud IDE) customization in gald3r projects. Covers replit.md Agent instructions, .replit/replit.nix env config, MCP integration, and cloud-IDE constraints for web-based development.
crawl_max_age_days: 14
vault_doc_path: research/platforms/replit/
vault_docs_url: https://docs.replit.com/replitai/replit-dot-md
docs_url: https://docs.replit.com/replitai/replit-dot-md
capability_status:
  hooks: ❌      # no native lifecycle-hook config; Linux container + g-hk-*.ps1 PowerShell mismatch
  rules: ⚠️      # replit.md single instruction blob; no .mdc / no glob scoping; Agent self-rewrites it
  skills: ❌     # no SKILL.md folder discovery; gald3r skills have no auto-load path
  commands: ❌   # no user-authored slash-command registry; native slash commands are Replit-owned
  mcp: ✅         # first-class — Agent is an MCP client; custom servers via Integrations pane
token_budget: low
subsystem_memberships: [PLATFORM_INTEGRATION]
---

# g-skl-platform-replit

Activate for: setting up gald3r on Replit, configuring Replit Agent, understanding Replit's cloud environment constraints, or verifying Replit gald3r integration.

---

## 1. Platform Overview

**Replit Agent** is an AI coding agent built into the Replit cloud IDE. It can build, run, and deploy applications within Replit's containerized environment. It reads project configuration from `.replit` and accepts natural language instructions.

- **Config**: `.replit` file controls run commands, nix environment, language
- **Agent**: Natural language task execution within the Replit cloud
- **Deployment**: Built-in Replit hosting and deployment
- **Environment**: Nix-based containerized development

**gald3r target tier**: Cloud IDE. Integration via `replit.md` instructions + MCP server (the
`.replit` / `replit.nix` files are environment config, not the AI-instruction surface).

---

## 2. Config File Layout

```
<repl-root>/
├── replit.md               ← Agent instructions + memory (auto-created, auto-read, self-updated)
├── AGENTS.md               ← also honored (cross-tool instruction convention)
├── .replit                 ← Replit project config (run command, language, env) — NOT AI instructions
├── replit.nix              ← Nix environment definition
└── .env                    ← Replaced by Replit Secrets
```

**`replit.md` is the AI-instruction surface** (see §3). `.replit` / `replit.nix` are
**environment/run config only** — Replit owns the run-command machinery; do not treat `.replit`
as an Agent instruction file.

**`.replit` format:**
```toml
run = "node bin/install.js && npm start"
language = "nodejs"
entrypoint = "index.js"

[nix]
channel = "stable-24_05"

[deployment]
run = ["sh", "-c", "npm start"]
deploymentTarget = "cloudrun"
```

---

## 3. gald3r Integration

### Install

Replit Agent is cloud-based — install via npm/node from the Replit shell:
```bash
node bin/install.js --only replit
```

### Limitations in Replit Environment

- `.gald3r/` directory works on disk in the container, but git operations go through Replit's
  separate git integration — Agent commits may not surface in gald3r task tracking
- Replit Secrets replace `.env` files — configure the gald3r MCP server URL as a Secret
- gald3r's PowerShell hooks are not compatible with Replit's Linux container (PowerShell absent by
  default) AND Replit has no native hook-wiring surface — hooks do not auto-fire at all
- Container restarts reset uncommitted state — commit `.gald3r/` task files frequently

### Agent Instructions — `replit.md` (primary)

Replit Agent **auto-creates `replit.md`** at the repl root and **auto-reads it on every request**.
gald3r conventions go into `replit.md` (and/or `AGENTS.md`). Prime it with:
```
This project uses gald3r for task management. Tasks are in .gald3r/TASKS.md.
Always reference the active task ID in commits: feat(T{id}): ...
Read .gald3r/CONSTRAINTS.md before making architecture changes.
Read .gald3r/learned-facts.md for durable project facts.
```

> **Durability caveat**: Agent may **self-update `replit.md`** as it learns the project, which can
> trim or overwrite gald3r conventions. Re-assert the block at session start if it goes missing.

### MCP (recommended integration surface)

Replit Agent is a **first-class MCP client**. Add the gald3r MCP server as a **custom MCP server**
via the **Integrations pane** (one-click install → automatic tool discovery; traffic is security
scanned). The server must be reachable by a **remote URL** — the container cannot reach `localhost`
of a different machine, so host the gald3r MCP endpoint at a reachable URL and store it as a Secret.

---

## 4. Verification

```bash
Test-Path .replit
node --version
node bin/install.js --list --target .
```

---

## 5. Common Pitfalls

- Replit's git integration is separate from the Replit Agent — commits made by Agent may not surface in gald3r task tracking
- PowerShell scripts not available — use bash equivalents for any gald3r automation
- Replit's container restarts reset uncommitted state — commit gald3r task files frequently
- MCP server must be a reachable remote URL (the container can't connect to localhost of a different machine) — but MCP itself is fully supported
- Treating `.replit` as an instruction file — it is NOT; instructions go in `replit.md`

---

## 6. Known Gaps (Cloud IDE Constraints)

Replit is a **cloud IDE**, not a local config-file IDE. Most Cursor-reference primitives have no
native load path. See `PLATFORM_SPEC.md` (this folder) for the full §9 analysis and evidence.

| Capability | Status | Why |
|---|---|---|
| Hooks | ❌ | No native hook-wiring surface; Linux container has no PowerShell — `g-hk-*.ps1` never auto-fire |
| Rules | ⚠️ | Only `replit.md` (single blob); no `.mdc`, no `alwaysApply:`/`globs:` scoping; Agent self-rewrites the file |
| Skills | ❌ | No `SKILL.md` folder discovery; gald3r skills are reference-only prose |
| Commands | ❌ | No user-authored slash-command registry; native slash commands are Replit-owned (connection selection) |
| Agents | ❌ | No agent-definition file format; `g-agnt-*.md` has no load path — degrade to `replit.md` prose |
| MCP | ✅ | First-class MCP client; custom servers via Integrations pane (remote URL only) |

**Net**: on Replit, gald3r is delivered primarily through `replit.md` instructions + the MCP server.
The rules/skills/commands/agents/hooks layers that work on local config-file IDEs do not apply.
