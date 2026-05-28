---
name: g-skl-platform-openhands
description: Authoritative reference for OpenHands (All Hands AI, formerly OpenDevin) AI agent customization in gald3r projects. Covers AGENTS.md context, .agents/skills/ + .openhands/microagents, MCP via mcp_tools, Docker sandbox integration, and gald3r install verification.
docs_url: https://docs.openhands.dev
crawl_max_age_days: 7
vault_doc_path: research/platforms/openhands/
vault_docs_url: https://docs.openhands.dev
last_doc_scan: 2026-05-26
token_budget: low
capability_status:
  hooks: "❌ not supported — no native hook system; Docker sandbox blocks host .ps1 hooks"
  rules: "⚠️ content via AGENTS.md/CLAUDE.md (always-on); no .mdc glob scoping"
  skills: "⚠️ native skills (folder-per-skill SKILL.md); gald3r frontmatter tolerance untested"
  commands: "❌ no native command/slash surface; portable only as keyword skills"
  mcp: "⚠️ skill-scoped mcp_tools + global config (doc-verified, not install-tested)"
subsystem_memberships: [PLATFORM_INTEGRATION]
---

# g-skl-platform-openhands

Activate for: setting up gald3r with OpenHands, authoring microagent instructions, configuring OpenHands sandbox, or verifying OpenHands gald3r integration.

---

## 1. Platform Overview

**OpenHands** (All Hands AI, formerly OpenDevin) is a powerful open-source AI software development
agent. It runs the agent loop inside a **Docker sandbox** with full filesystem access, web browsing,
and code execution, driven from a web UI / REST API / CLI (not an editor).

- **Always-on context**: auto-discovered repo-root **`AGENTS.md`** (primary), with `CLAUDE.md` /
  `GEMINI.md` model-specific variants — injected into the system prompt at conversation start.
- **Skills**: folder-per-skill `SKILL.md`, loading precedence `.agents/skills/` (recommended) →
  `.openhands/skills/` (deprecated) → `.openhands/microagents/` (legacy backward-compat).
- **Microagents** (legacy): `repo.md` (always-on repository microagent) + keyword-triggered
  knowledge microagents in `.openhands/microagents/`.
- **MCP**: skill-scoped `mcp_tools` (spins up an MCP server when a skill activates) + global config.
- **Sandbox**: Docker-based isolated execution environment (host paths/hooks not reachable).
- **GitHub integration**: auto-raises PRs, pushes commits.

**gald3r target tier**: Open-source agentic CLI/server. Instructions via `AGENTS.md`; skills via
`.agents/skills/`. (No Cursor-style hooks, `.mdc` rules, or slash commands — see Known Gaps.)

---

## 2. Config File Layout

```
<project-root>/
├── AGENTS.md                      ← always-on context (primary, recommended)
├── CLAUDE.md / GEMINI.md          ← model-specific always-on variants
├── .agents/
│   └── skills/<name>/SKILL.md     ← RECOMMENDED skills location (current)
└── .openhands/
    ├── skills/<name>/SKILL.md     ← skills (deprecated, still loaded)
    └── microagents/
        ├── repo.md                ← repository microagent (always-on, legacy)
        └── <name>.md              ← keyword-triggered knowledge microagent (legacy)
```

**Skill-location precedence (verified, docs 2026-05-26)**: `.agents/skills/` (recommended) →
`.openhands/skills/` (deprecated) → `.openhands/microagents/` (legacy backward-compat).

**`AGENTS.md` format**: plain markdown injected into the system prompt at conversation start —
the always-on repository context. This (not `repo.md`) is the current primary instruction surface.

**Knowledge skill/microagent frontmatter** (keyword-triggered): YAML with `name`, `trigger_type`,
`keywords`, and an optional `mcp_tools` / `mcp_location` block (see MCP section).

---

## 3. gald3r Integration

### Install

```bash
node bin/install.js --only openhands
```

> **Target correction (docs 2026-05-26)**: gald3r's current installer writes
> `.openhands/microagents/repo.md` — the **legacy** path. Current OpenHands docs prefer always-on
> context in **`AGENTS.md`** (root) and skills in **`.agents/skills/`**. gald3r already ships a
> personalized root `AGENTS.md`, so the always-on instruction content reaches OpenHands with no
> extra glue. Re-targeting skills output to `.agents/skills/` is a parity follow-up (T1484).

### AGENTS.md Content (always-on context — current primary)

```markdown
# Repository Context

## Task Management (gald3r)
This project uses gald3r for task tracking.
- Active tasks: .gald3r/TASKS.md
- Task details: .gald3r/tasks/task{id}_*.md
- Constraints: .gald3r/CONSTRAINTS.md

## Development Workflow
1. Read active task before implementing
2. Reference task ID in all commits: feat(T{id}): ...
3. Mark tasks complete by updating task YAML status

## Bug Protocol
Pre-existing bugs → document in .gald3r/BUGS.md, never silently ignore.
```

(The same content is also valid as `.openhands/microagents/repo.md` for the legacy path.)

### MCP Integration

OpenHands supports MCP at two levels:

1. **Skill-scoped `mcp_tools`** — a keyword-triggered skill's YAML frontmatter declares an MCP
   server that is spun up and whose tools are registered when the skill activates.
2. **Global / sandbox MCP config** — e.g. (form from prior versions; exact 2026 key untested):

```toml
[sandbox]
mcp_url = "http://host.docker.internal:8092"
```

⚠️ Sandbox note: the agent runs in Docker, so a host MCP server must be reachable from the
container (`host.docker.internal`). ⚠️ The exact current config key/location was not install-tested.

---

## 4. Verification

```powershell
Test-Path AGENTS.md                          # current primary context surface
Test-Path .openhands/microagents/repo.md     # legacy path (still loaded)
node bin/install.js --list --target .
```

---

## 5. Common Pitfalls

- OpenHands runs in a Docker sandbox — host file paths, host PowerShell hooks, and host-local MCP
  servers are NOT directly reachable from the container (use `host.docker.internal`).
- Always-on context (`AGENTS.md` / `repo.md`) is loaded for ALL sessions; keep it lean.
- OpenHands' GitHub integration commits with its own identity — verify commit author in gald3r task records.
- gald3r's installer still targets the legacy `.openhands/microagents/` path; prefer `AGENTS.md`
  for context and `.agents/skills/` for skills until parity output is re-targeted (T1484).

---

## 6. Known Gaps (Docker Sandbox Constraints + Missing Surfaces)

Honest status — what does NOT work on OpenHands vs. the Cursor reference (see `PLATFORM_SPEC.md` §9
for the full comparison and verification evidence):

| Capability | Status | Reason |
|---|---|---|
| Hooks (`g-hk-*.ps1` + `hooks.json`) | ❌ | No native hook system; the Docker sandbox cannot run host PowerShell lifecycle hooks. |
| Commands (`g-*.md` `/g-*`) | ❌ | No `.openhands/commands/` / slash-command runtime; content portable only as keyword skills. |
| Agent roster (`g-agnt-*` `@agent`) | ⚠️/❌ | Single generalist agent; no selectable named-agent slot. Content portable as skills/context. |
| Rules glob scoping (`.mdc` `globs:`) | ⚠️ | No `.mdc` engine; binary always-on (`AGENTS.md`) vs. keyword-triggered (skills). Content carries; scoping lost. |
| Skills (`g-skl-*/SKILL.md`) | ⚠️ | Native skills exist (doc-verified); gald3r extra frontmatter tolerance + live load untested. |
| MCP | ⚠️ | Skill-scoped `mcp_tools` + global config doc-verified; live gald3r server block + sandbox→host reach untested. |
| Live install verification | ❓ | No `.openhands/`/`.agents/` folder in this repo; no sandbox launched. All ✅-by-docs claims await a real run. |

**Positive parity**: OpenHands natively reads `AGENTS.md`/`CLAUDE.md` (always-on context) and has a
folder-per-skill `SKILL.md` system + MCP — so gald3r rules and skills *content* reach OpenHands with
minimal glue. The losses are hooks, commands, and the multi-agent roster.
