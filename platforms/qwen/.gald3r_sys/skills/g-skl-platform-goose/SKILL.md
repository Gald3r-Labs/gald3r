---
name: g-skl-platform-goose
description: Authoritative reference for Goose (Block) AI agent customization in gald3r projects. Covers .goose/ config, instructions files, extensions, and gald3r install verification.
crawl_max_age_days: 14
vault_doc_path: research/platforms/goose/
vault_docs_url: https://block.github.io/goose/docs
docs_url: https://block.github.io/goose/docs
capability_status:
  hooks: ❌      # no native lifecycle-hook config; g-hk-*.ps1 do not auto-fire
  rules: ⚠️      # .goosehints single instruction blob; no .mdc / no glob scoping
  skills: ⚠️     # native Skills extension (same SKILL.md format) but discovers .agents/skills/, gated on extension
  commands: ⚠️   # no slash-command registry; native equivalent = recipes (YAML), no auto-port
  mcp: ✅         # first-class — extensions ARE MCP servers; ~/.config/goose/config.yaml
token_budget: low
subsystem_memberships: [PLATFORM_INTEGRATION]
---

# g-skl-platform-goose

Activate for: setting up gald3r with Goose (Block's open source AI agent), authoring Goose instructions, configuring extensions, or verifying Goose gald3r integration.

---

## 1. Platform Overview

**Goose** (by Block, fka Square — "codename goose") is an open-source, local-first AI developer
agent that runs in the terminal (CLI) and a desktop app. Its core trait is a **first-class MCP
story**: every capability beyond built-in tools is an **extension**, and every extension is an MCP
server. See `PLATFORM_SPEC.md` (this folder) for the full per-section capability assessment.

- **Config**: `~/.config/goose/config.yaml` (global) — provider, model, and enabled extensions.
  There is **no** standard `GOOSE.md` / `.goose/config.yaml` project convention.
- **Instructions/rules**: `.goosehints` (project root) — Goose-specific instruction file.
- **Extensions**: MCP servers (stdio + remote) and built-in tools (Developer extension enabled by
  default). Governed by an optional Extension Allowlist.
- **Recipes**: reusable/shareable YAML workflow templates (+ sub-recipes) — the native
  command/workflow primitive.
- **Skills**: optional Skills extension auto-discovers folder-per-`SKILL.md` from `.agents/skills/`
  (project) + `~/.config/agents/skills/` (global).
- **Subagents**: experimental, platform-spawned/auto-managed (no user-authored agent file format).

**gald3r target tier**: Open-source CLI agent. Instructions via `.goosehints`; MCP via
`~/.config/goose/config.yaml` extensions.

---

## 2. Config File Layout

```
~/.config/goose/
└── config.yaml             ← GLOBAL config: provider, model, enabled extensions (MCP servers)

~/.config/agents/skills/    ← GLOBAL skills (Skills extension)

<project-root>/
├── .goosehints             ← project instructions/rules (gald3r writes this)
└── .agents/skills/         ← PROJECT skills discovered by the Skills extension
    └── <name>/SKILL.md
```

**Global config**: `~/.config/goose/config.yaml` (machine-specific — extensions declared here).

**`.goosehints` format**: project-specific instructions Goose loads as context (markdown content).

**`~/.config/goose/config.yaml` extension example:**
```yaml
extensions:
  gald3r:
    type: stdio          # or "sse"/remote for a URL-based MCP server
    cmd: <gald3r-mcp-command>
    enabled: true
```
> Manage extensions interactively with `goose configure`. The Developer MCP extension is enabled by
> default on install.

---

## 3. gald3r Integration

### Install

```bash
node bin/install.js --only goose
```

Creates `.goosehints` (project instructions/rules) with gald3r task context. MCP is added as a
Goose extension in the **global** `~/.config/goose/config.yaml` (machine-specific), not per-project.

### .goosehints Content

```markdown
# Project Context — gald3r

## Task Management
All tasks tracked in .gald3r/TASKS.md. Reference task ID in all work.
Active task details: .gald3r/tasks/task{id}_*.md

## Commit Convention
feat(T{id}): description

## gald3r MCP
If the gald3r MCP extension is enabled, use it for task/bug/vault operations.
```

### MCP Integration (primary surface)

Goose's strongest gald3r surface — extensions ARE MCP servers. Add the gald3r MCP server as an
extension in `~/.config/goose/config.yaml` (or via `goose configure`):
```yaml
extensions:
  gald3r:
    type: stdio          # use "sse"/remote with a `uri:` for a URL-based MCP server
    cmd: <gald3r-mcp-command>
    enabled: true
```

---

## 4. Verification

```powershell
Test-Path .goosehints
goose --version
goose configure        # inspect/enable extensions interactively
node bin/install.js --list --target .
```

---

## 5. Common Pitfalls

- Goose is session-based; `.goosehints` is loaded as context per session, MCP/extension state is
  configured globally in `~/.config/goose/config.yaml`.
- `.goosehints` is the project instruction file — **not** `GOOSE.md` (which is not a Goose
  convention; the old skill text was wrong).
- Extensions (MCP servers) must be enabled in config before the Goose session starts; an Extension
  Allowlist may restrict which can be installed.
- The **Skills extension** must be enabled for `.agents/skills/` discovery — it is not on by
  default, and the discovery path differs from gald3r's canonical `skills/`.

---

## 6. Known Gaps

| Capability | Status | Gap / Note |
|---|---|---|
| Hooks | ❌ | No native lifecycle-hook config (no `hooks.json` analogue). gald3r `g-hk-*.ps1` do not auto-fire — run manually or wrap in a recipe. |
| Agents | ⚠️ | No user-authored agent file format. Goose **subagents** are experimental + platform-spawned; gald3r `g-agnt-*.md` have no load path. Map to recipes or `.goosehints`. |
| Commands | ⚠️ | No slash-command registry. Native equivalent = **recipes** (YAML). gald3r `g-*` markdown commands do not auto-port. |
| Rules | ⚠️ | No `.mdc`, no `alwaysApply:`/`globs:` scoping. Rules collapse into one `.goosehints` blob (all-or-nothing). |
| Skills | ⚠️ | Native Skills extension uses the same `SKILL.md` format ✅ but discovers `.agents/skills/` (not gald3r's `skills/`) and is gated on the extension being enabled. ❓ not install-tested. |
| MCP | ✅ | First-class — extensions ARE MCP servers; `~/.config/goose/config.yaml`. Strongest gald3r surface. |
| Docs freshness | ❓ | `last_doc_scan: never` — run `@g-platform-scan-docs goose`. |

See `PLATFORM_SPEC.md` (this folder) for the full 9-section assessment and verification evidence.
