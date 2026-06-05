---
name: g-skl-platform-replit
description: Authoritative reference for Replit Agent (cloud IDE) customization in gald3r projects. Covers replit.md Agent instructions, Agent Skills in /.agents/skills, Plan/Build modes + effort tiers, MCP (client + hosted server), and cloud-IDE constraints (no hooks, no commands).
crawl_max_age_days: 14
vault_doc_path: research/platforms/replit/
vault_docs_url: https://docs.replit.com/replitai/replit-dot-md
docs_url: https://docs.replit.com/replitai/replit-dot-md
docs_url_secondary:
  - https://docs.replit.com/replitai/skills
  - https://docs.replit.com/replitai/agent
  - https://docs.replit.com/learn/model-context-protocol
  - https://docs.replit.com/references/agent/task-lifecycle
  - https://blog.replit.com/introducing-workflows
last_doc_scan: 2026-06-02
capability_status:
  hooks: "❌ no native lifecycle hooks; task lifecycle is observational; Linux container + g-hk-*.ps1 PowerShell mismatch"
  rules: "✅ replit.md single instruction/memory blob (auto-read, self-updated); no .mdc / no glob scoping"
  skills: "✅ Agent Skills (agentskills.io SKILL.md) in /.agents/skills — lazy-loaded, Project/User/Enterprise scopes"
  commands: "❌ no user-authored slash-command registry; Workflows are shell-command runners, not agent commands"
  agents: "⚠️ native Plan/Build modes + effort tiers; no user-definable custom-agent file format"
  mcp: "✅ native — Agent is an MCP client (cloud UI); Replit also ships a hosted MCP server"
token_budget: low
subsystem_memberships: [PLATFORM_INTEGRATION]
---

# g-skl-platform-replit

Activate for: setting up gald3r on Replit, shipping Agent Skills to `/.agents/skills`, priming
`replit.md`, configuring MCP, understanding Replit's cloud constraints, or verifying the Replit
gald3r install.

---

> Full 8-section breakdown + evidence URLs in `PLATFORM_SPEC.md` (this folder). **Status: ⚠️ partial
> parity** — native **skills** (`/.agents/skills` SKILL.md), **rules** (`replit.md`), and **MCP**;
> **partial agents** (Plan/Build modes + effort tiers, no custom-agent files); **no hooks, no
> commands**. Instruction file is **`replit.md`**, NOT AGENTS.md/CLAUDE.md. (Verified 2026-06-02
> against https://docs.replit.com.)

## 1. Platform Overview

**Replit Agent** is an AI coding agent built into the Replit cloud IDE — it builds, runs, and deploys
apps inside a **Nix-based, Linux container**. It is **not** a local config-file IDE: there is no
on-disk rules tree, no lifecycle-hook config, and no slash-command registry. gald3r maps onto Replit
through **Agent Skills** (`/.agents/skills`), the **`replit.md`** instruction/memory file, and
**MCP** — plus native **Plan/Build modes + effort tiers** (Lite/Economy/Power/Turbo) as agent controls.

**gald3r target tier**: Cloud IDE. Primary delivery = Agent Skills + `replit.md` + MCP server.

## 2. Config Layout

```
<repl-root>/
├── replit.md                     ← Agent instructions + memory (auto-created, auto-read, self-updated)
├── .agents/
│   └── skills/  <name>/SKILL.md   ← Agent Skills (agentskills.io standard) — NATIVE, lazy-loaded
├── .replit                       ← Repl config (run command, language, [nix], [deployment]) — NOT AI instructions
├── replit.nix                    ← Nix environment definition
└── .gald3r/                      ← gald3r project state (commit often — restarts reset uncommitted state)
```

**`replit.md` is the AI-instruction surface** (§3) — **not** `AGENTS.md`/`CLAUDE.md` (community-only).
`.replit`/`replit.nix` are **environment/run config only**.

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

## 3. gald3r Integration

**Cheapest high-value install: ship gald3r's skill tree into `/.agents/skills/`** (agentskills.io
`SKILL.md`, Project scope, versioned in the repo) — Agent discovers them natively and lazy-loads by
name+description via the **"Use a skill"** picker. Then prime **`replit.md`** with `.gald3r/`
conventions, and add the gald3r **MCP server** (custom, remote URL) in the cloud UI.

### Agent Instructions — `replit.md` (primary)

Replit Agent **auto-creates `replit.md`** at the repl root and **auto-reads it on every request**.
Prime it with:
```
This project uses gald3r for task management. Tasks are in .gald3r/TASKS.md.
Always reference the active task ID in commits: feat(T{id}): ...
Read .gald3r/CONSTRAINTS.md before making architecture changes.
Read .gald3r/learned-facts.md for durable project facts.
```

> **Durability caveat**: Agent may **self-update `replit.md`** as it learns the project, which can
> trim or overwrite gald3r conventions. Re-assert the block at session start if it goes missing.

### MCP (recommended integration surface)

Replit Agent is a **first-class MCP client**. Add the gald3r MCP server as a **custom MCP server** in
the cloud UI (auto tool discovery). It must be a **reachable remote URL** (the container can't reach a
different machine's `localhost`) — host it and store the URL as a **Replit Secret**. Replit also ships
a **hosted MCP server** (`replit-mcp.com`, OAuth on first connect) that lets an external gald3r host
orchestrate Replit projects.

### Verify
```powershell
Test-Path replit.md                 # Agent instructions + memory
Test-Path .agents/skills            # native Agent Skills surface
node --version                      # cloud shell is Linux/Node
```

## 4. Common Pitfalls

- **Instruction file is `replit.md`, not AGENTS.md/CLAUDE.md** — `AGENTS.md` is community-only; Replit
  standardizes on `replit.md` (root-only; "doesn't automatically apply to other AI tools").
- Treating `.replit` as an instruction file — it is NOT; it is run/env config. Instructions → `replit.md`.
- **No hooks**: `g-hk-*.ps1` never auto-fire (no hook surface) AND PowerShell is absent in the Linux
  container — use `replit.md` prose, git `core.hooksPath` bash, or Plan mode for review gates.
- **No agent commands**: Workflows are shell-command Run buttons (build/test), not gald3r `/g-*`
  commands — trigger gald3r flows via the matching Agent Skill or chat intent.
- **No custom-agent files**: `g-agnt-*.md` has no load path — use Plan/Build modes + effort tiers, or
  express roles as Agent Skills.
- Container restarts reset uncommitted state — commit `.gald3r/` task files frequently.
- MCP endpoint must be a reachable remote URL (no cross-machine localhost) — but MCP itself is fully supported.

## 5. Capability Summary

| Feature | Status | Notes |
|---|---|---|
| Hooks (`g-hk-*.ps1`) | ❌ | No hook surface; task lifecycle is observational; Linux container has no PowerShell |
| Skills (`g-skl-*/SKILL.md`) | ✅ | agentskills.io `SKILL.md` in **`/.agents/skills`**; lazy-loaded; Project/User/Enterprise scopes (~Apr 2026) |
| Agents (`g-agnt-*.md`) | ⚠️ | Native Plan/Build modes + effort tiers (Lite/Economy/Power/Turbo); no user-definable custom-agent file format |
| Commands (`@g-*`) | ❌ | No slash-command registry; Workflows are shell runners, not agent commands |
| Rules (`g-rl-*`) | ✅ | `replit.md` single instruction/memory blob (auto-read, self-updated); no `.mdc`, no glob scoping |
| MCP | ✅ | Agent is an MCP client (cloud UI, custom remote URL); Replit also ships a hosted MCP server (`replit-mcp.com`) |

Full assessment + evidence in `PLATFORM_SPEC.md`. Re-verify on the next `@g-platform-scan-docs replit` (crawl_max_age_days: 14).
