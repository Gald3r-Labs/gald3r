---
name: g-skl-platform-opencode
description: Authoritative reference for OpenCode (sst/opencode) customization in gald3r projects. Covers .opencode/ folder layout, opencode.json config, native skills discovery (.opencode/skills/ + .claude/skills/ + .agents/skills/), AGENTS.md/CLAUDE.md instructions, JS/TS plugin hooks, MCP, and gald3r install verification.
crawl_max_age_days: 7
vault_doc_path: research/platforms/opencode/
vault_docs_url: https://opencode.ai/docs
docs_url: https://opencode.ai/docs
docs_url_secondary:
  - https://opencode.ai/docs/plugins/
  - https://opencode.ai/docs/agents/
  - https://opencode.ai/docs/skills/
  - https://opencode.ai/docs/commands/
  - https://opencode.ai/docs/rules/
  - https://opencode.ai/docs/mcp-servers/
last_doc_scan: 2026-06-02
capability_status:
  hooks: "✅ native lifecycle hooks via JS/TS plugins in .opencode/plugins/ (20 events incl. tool.execute.before/after, session.created, file.edited); gald3r .ps1 need a JS/TS shim; no first-class git pre-commit event"
  rules: "✅ AGENTS.md primary (CLAUDE.md fallback; AGENTS.md wins if both local) + opencode.json instructions array; no .mdc glob-scoped rule engine"
  skills: "✅ Agent Skills (SKILL.md) loaded on-demand via native skill tool; discovered in .opencode/skills / .claude/skills / .agents/skills"
  commands: "✅ custom commands .opencode/commands/*.md ($ARGUMENTS/$1 + !bash; frontmatter description/agent/model/subtask)"
  agents: "✅ native primary agents (Build/Plan) + subagents (General/Explore/Scout) in .opencode/agents/ or opencode.json; @mention + Task tool"
  mcp: "✅ native — mcp field in opencode.json (local + remote), {env:}/{file:} substitution"
token_budget: low
subsystem_memberships: [PLATFORM_INTEGRATION]
---

# g-skl-platform-opencode

Activate for: setting up gald3r with OpenCode (`sst/opencode`), authoring `.opencode/` configs and `opencode.json`, writing commands/agents/skills/plugin-hooks, or verifying the OpenCode gald3r install.

---

> Full 9-section breakdown + evidence URLs in `PLATFORM_SPEC.md` (this folder). **Status: ✅ full
> parity** — OpenCode natively supports commands, rules, agents, skills, hooks (via JS/TS plugins),
> and MCP, and reads `AGENTS.md`/`CLAUDE.md` + discovers `.claude/skills/` + `.agents/skills/`, so
> gald3r's Claude-Code artifacts are largely reusable. The one friction point: hooks are JS/TS
> plugins (no `.ps1`, no first-class git pre-commit). (Verified 2026-06-02 against
> https://opencode.ai/docs.)

## Crawl Freshness Gate

```
1. Read {vault_location}/.crawl_schedule.json
2. Find entry for: https://opencode.ai/docs
3. If entry missing OR (today - last_crawl) > 7 days:
   → Surface: "📚 OpenCode docs overdue for re-crawl — run @g-platform-scan-docs opencode"
4. Else: proceed (cited findings below are current as of last_doc_scan).
```

## 1. Platform Overview

**OpenCode (sst/opencode)** — an open-source, terminal-first AI coding agent (TUI) from the **SST**
team, with multi-provider model support and a JSON/JSONC config (`opencode.json`). Built-in primary
agents **Build** (full access) and **Plan** (read-only/suggest); built-in subagents General, Explore,
Scout. Extensibility is native across all six gald3r primitives.

## 2. Config Layout

```
<project-root>/
├── AGENTS.md / CLAUDE.md            ← read by OpenCode (AGENTS.md wins if BOTH exist locally)
├── opencode.json (or .jsonc)        ← ROOT config — mcp + instructions + plugin (NOT inside .opencode/)
└── .opencode/
    ├── commands/ *.md               ← custom commands ($ARGUMENTS/$1 + !bash)
    ├── agents/   *.md               ← primary agents + subagents (md, or opencode.json inline)
    ├── skills/   <name>/SKILL.md    ← Agent Skills (native skill tool, on-demand)
    └── plugins/  *.{js,ts}          ← JS/TS plugins == OpenCode's hook mechanism
```

OpenCode **also** discovers `.claude/skills/` and `.agents/skills/` (workspace or `~/`) and reads
`~/.claude/CLAUDE.md` → **gald3r's Claude-Code skill tree + instruction files work as-is on
OpenCode.** Global configs live under `~/.config/opencode/`.

## 3. gald3r Integration

**Cheapest high-parity install: ship gald3r's `.claude/skills/` tree + `AGENTS.md`/`CLAUDE.md`** —
OpenCode loads them natively. Put commands in `.opencode/commands/*.md` and agents in
`.opencode/agents/*.md`. Register MCP under `opencode.json -> mcp`. For hooks, author a thin **JS/TS
plugin** in `.opencode/plugins/` that shells out to PowerShell (gald3r `.ps1` hooks do not run as
plugins directly).

### Verify
```powershell
Test-Path opencode.json              # root config (mcp + instructions + plugin)
Test-Path AGENTS.md                  # primary instruction file (CLAUDE.md is the fallback)
Test-Path .claude/skills ; Test-Path .opencode/commands ; Test-Path .opencode/agents
Test-Path .opencode/plugins          # JS/TS hook shim (if hooks are wired)
```

## 4. Common Pitfalls

- **Instruction file is `AGENTS.md`, not `CLAUDE.md`** — and **if both exist locally, only
  `AGENTS.md` is read** (the reverse of Claude Code). Keep gald3r rule content in `AGENTS.md` (or
  the `instructions` array) for OpenCode.
- **Hooks are JS/TS plugins**, not `.ps1` and not a JSON wiring file. gald3r `g-hk-*.ps1` must be
  shelled out from a JS/TS plugin (Bun shell API) on `session.created` / `tool.execute.before` /
  `tool.execute.after`. There is **no first-class git pre-commit / pre-push event** — wire via
  `command.executed` or external git hooks.
- **`opencode.json` lives at the project root**, NOT inside `.opencode/`.
- **No `.mdc` glob-scoped rule engine** — rule *content* transfers via `AGENTS.md`/`CLAUDE.md`;
  Cursor's per-rule `alwaysApply`/`globs` scoping does not.

## 5. Capability Summary

| Feature | Status | Notes |
|---|---|---|
| Hooks (`g-hk-*.ps1`) | ✅ | JS/TS plugins in `.opencode/plugins/` (20 events); `.ps1` need a JS/TS shim; no git pre-commit event |
| Skills (`g-skl-*/SKILL.md`) | ✅ | native `skill` tool, on-demand; discovered in `.opencode/skills/` / `.claude/skills/` / `.agents/skills/` |
| Agents (`g-agnt-*.md`) | ✅ | native primary (Build/Plan) + subagents (General/Explore/Scout) `.opencode/agents/`; `@mention` + Task tool |
| Commands (`@g-*`) | ✅ | `.opencode/commands/*.md`; `$ARGUMENTS`/`$1` + `!bash`; frontmatter description/agent/model/subtask |
| Rules (`g-rl-*`) | ✅ | `AGENTS.md` (CLAUDE.md fallback) + `instructions` array; no `.mdc` glob scoping |
| MCP | ✅ | `opencode.json -> mcp` (local + remote); `{env:}`/`{file:}` substitution |

Full assessment + evidence in `PLATFORM_SPEC.md`. Re-verify on the next `@g-platform-scan-docs opencode` (crawl_max_age_days: 7).
