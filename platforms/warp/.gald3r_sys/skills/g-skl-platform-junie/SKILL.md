---
name: g-skl-platform-junie
description: Authoritative reference for JetBrains Junie (AI coding plugin) customization in gald3r projects. Covers .junie/guidelines.md, custom instructions, and gald3r install verification.
crawl_max_age_days: 14
vault_doc_path: research/platforms/junie/
vault_docs_url: https://junie.jetbrains.com/docs
docs_url: https://junie.jetbrains.com/docs
last_doc_scan: never
capability_status:
  hooks: "❌ no lifecycle-hook system; Action Allowlist is approval gating, not a hook bus"
  rules: "⚠️ no rules folder; always-apply via .junie/AGENTS.md guidelines (legacy .junie/guidelines.md), injected into every task"
  skills: "❌ no SKILL.md discovery/loading; extend via MCP tools instead"
  commands: "❌ no custom slash-command framework; conversational + MCP tools only"
  mcp: "✅ native .junie/mcp/mcp.json (project) + global config + IDE MCP Settings; server set per-machine (❓ in CI)"
token_budget: low
subsystem_memberships: [PLATFORM_INTEGRATION]
---

# g-skl-platform-junie

Activate for: setting up gald3r with JetBrains Junie, authoring `.junie/guidelines.md`, or verifying Junie gald3r integration in IntelliJ/PyCharm/WebStorm.

---

## 1. Platform Overview

**JetBrains Junie** is JetBrains' agentic AI coding assistant. It runs as a **plugin inside the IntelliJ platform** (IntelliJ IDEA, PyCharm, WebStorm, GoLand, RubyMine, Rider, etc.) and also offers a **terminal/CLI mode**. It is **not** a VS Code fork — it is hosted by the JetBrains IDE. It reads project-level **guidelines** (preferred `.junie/AGENTS.md`; legacy `.junie/guidelines.md`) and requires a JetBrains AI subscription.

- **Guidelines**: searched in order — IDE custom path → `.junie/AGENTS.md` (preferred) → root `AGENTS.md` → legacy `.junie/guidelines.md` / `.junie/guidelines/`. Injected into every task's context.
- **Agent mode**: Multi-step task execution within the JetBrains IDE (single agentic assistant; no file-defined agent roster)
- **Context**: Uses IDE's code intelligence (PSI) for deep code understanding
- **MCP**: Native — `.junie/mcp/mcp.json` (project) + global config + in-IDE MCP Settings panel
- **Action Allowlist**: governs which commands/MCP tools run without confirmation (approval gating, not a hook system)
- **Run configurations**: Junie can execute run configs defined in the IDE

**gald3r target tier**: JetBrains IDEs. Persistent context via `.junie/AGENTS.md` guidelines; extensibility via MCP. See companion [`PLATFORM_SPEC.md`](./PLATFORM_SPEC.md) for the full capability assessment (T1476).

---

## 2. Config File Layout

```
<project-root>/
├── .junie/
│   ├── AGENTS.md           ← preferred guidelines file (auto-injected into every task)
│   ├── guidelines.md       ← LEGACY guidelines (still supported); .junie/guidelines/ folder also legacy
│   └── mcp/
│       └── mcp.json        ← project-level MCP server config (commit & share across the team)
└── AGENTS.md               ← root AGENTS.md is also honored (search-order fallback)
```

**Format**: Plain markdown (open `AGENTS.md` format). Junie injects the guidelines content into every task's prompt context. There is **no** rules/skills/agents/commands/hooks directory under `.junie/` — only guidelines and MCP config.

**Guidelines search order**: IDE custom path → `.junie/AGENTS.md` → root `AGENTS.md` → legacy `.junie/guidelines.md` (or `.junie/guidelines/` folder). gald3r should write `.junie/AGENTS.md` as the canonical surface and may keep `.junie/guidelines.md` for older builds.

---

## 3. gald3r Integration

### Install

```bash
node bin/install.js --only junie
```

Creates `.junie/AGENTS.md` (preferred) with gald3r task-management context; may also write a legacy `.junie/guidelines.md` for older Junie builds.

### Recommended guidelines (.junie/AGENTS.md)

```markdown
# gald3r Development Guidelines

## Before Starting Any Task
1. Read `.gald3r/TASKS.md` for current task list
2. Read active task file in `.gald3r/tasks/task{id}_*.md`
3. Check `.gald3r/CONSTRAINTS.md` for architectural limits

## Commit Format
feat(T{id}): description of change
fix(BUG-{id}): description of fix

## Bug Discovery
When encountering bugs: do NOT silently ignore.
Pre-existing bugs → create entry in `.gald3r/BUGS.md`.

## Task Completion
Update task status in `.gald3r/tasks/task{id}_*.md` and `.gald3r/TASKS.md`.
```

---

## 4. Verification

```powershell
Test-Path .junie/AGENTS.md       # preferred guidelines surface
Test-Path .junie/guidelines.md   # legacy compatibility (optional)
Test-Path .junie/mcp/mcp.json    # if using MCP servers
node bin/install.js --list --target .
```

---

## 5. MCP Support

Junie has **native MCP support** (✅ mechanism):

- **Project config**: `.junie/mcp/mcp.json` at the project root — checked into version control and shared across the team.
- **Global config**: user/IDE scope (`~/.junie/` / IDE settings) for personal servers.
- **MCP Settings panel**: in-IDE configuration UI.
- **Action Allowlist**: adding an MCP-rule allowlist item authorizes Junie to run MCP tools without per-call confirmation. (You cannot yet scope the allowlist to *specific* MCP servers/tools — it is an all-MCP grant.)

The concrete server set is machine/team-specific (no `mcp.json` is committed in this template), so end-to-end server behavior is ❓ untested in CI. Junie has **no skill/command registry** — runtime extensibility goes through MCP tools, not gald3r skills.

---

## 6. Common Pitfalls

- Junie requires a **JetBrains AI subscription** — ensure subscription is active.
- **Use `.junie/AGENTS.md`** as the canonical guidelines surface — `.junie/guidelines.md` is the legacy format (still supported). The IDE custom-path setting overrides both.
- Guidelines are injected into every task's context; changes take effect on the next Junie activation.
- Junie uses JetBrains' **PSI** for code navigation — gald3r rules that assume literal file paths may need IDE-relative adjustments.
- **No hooks**: gald3r's session-start / inbox-check / pre-commit `.ps1` hooks do **not** auto-fire on Junie. The Action Allowlist is approval gating, not a hook bus.

---

## 7. Known Gaps

Honest capability assessment (full detail in [`PLATFORM_SPEC.md`](./PLATFORM_SPEC.md) §9). Per the
decision tree in `g-skl-platform-cursor/SKILL.md`, each capability is (a) common, (b) platform-specific, or (c) a documented gap:

| Cursor-reference capability | Junie | Disposition |
|---|---|---|
| `.cursor/rules/*.mdc` always-apply rules | ⚠️ no rules folder | (c) folded into `.junie/AGENTS.md` guidelines |
| `agents/g-agnt-*.md` discovery | ❌ no agent files | (c) hard gap — single assistant; roles described in guidelines |
| `skills/g-skl-*/SKILL.md` discovery + auto-load | ❌ no skill mechanism | (c) hard gap — extend via MCP tools |
| `commands/` slash-command palette (`@g-*`) | ❌ no command framework | (c) hard gap — conversational + MCP tools |
| Lifecycle hooks (`hooks.json`, sessionStart, …) | ❌ none | (c) hard gap — Action Allowlist ≠ hook bus |
| MCP servers | ✅ native `.junie/mcp/mcp.json` | (a)/(b) strong fit |
| Persistent guidelines / memory | ⚠️ single guidelines file | (a)/(b) strong fit, injected into every task |

**Strong fits**: MCP and persistent guidelines. **Hard gaps**: rules folder, file-defined agents, skill discovery, extensible commands, lifecycle hooks. `last_doc_scan: never` — run `@g-platform-scan-docs junie` to verify on the current Junie release.
