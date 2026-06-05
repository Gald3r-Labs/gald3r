---
name: g-skl-platform-cline
description: Authoritative reference for Cline (VS Code / JetBrains extension + CLI + SDK) customization in gald3r projects. Covers .clinerules rules + workflows-as-slash-commands, .cline/skills SKILL.md, lifecycle hooks (macOS/Linux only), SDK subagents/teams, MCP marketplace, AGENTS.md (not CLAUDE.md), and gald3r install verification.
crawl_max_age_days: 14
vault_doc_path: research/platforms/cline/
vault_docs_url: https://docs.cline.bot
docs_url: https://docs.cline.bot
docs_url_secondary:
  - https://docs.cline.bot/features/slash-commands/workflows
  - https://docs.cline.bot/customization/cline-rules
  - https://docs.cline.bot/sdk/guides/multi-agent-teams
  - https://docs.cline.bot/features/skills
  - https://cline.bot/blog/cline-v3-36-hooks
  - https://docs.cline.bot/mcp/mcp-overview
last_doc_scan: 2026-06-02
capability_status:
  hooks: "✅ native lifecycle hooks (PreToolUse/PostToolUse/UserPromptSubmit/TaskStart/TaskResume/TaskCancel) — executable scripts, JSON stdin/stdout — BUT macOS/Linux only (no Windows yet)"
  rules: "✅ .clinerules file or folder (all .md/.txt combined); toggleable per-file (v3.13); YAML frontmatter path-scoping; reads AGENTS.md (NOT CLAUDE.md)"
  skills: "✅ Agent Skills SKILL.md (3-tier progressive disclosure) in .cline/skills/ or ~/.cline/skills/; use_skill tool"
  commands: "✅ Workflows = custom slash commands in .clinerules/workflows/*.md (/<filename>) + built-ins"
  agents: "✅ native subagents + multi-agent teams via the Cline SDK / CLI runtime (own model/tools/prompt, shared task board) — not the bare IDE chat"
  mcp: "✅ native — STDIO + Remote HTTP/SSE; MCP Marketplace; cline_mcp_settings.json (IDE) / ~/.cline/mcp.json (CLI)"
token_budget: low
subsystem_memberships: [PLATFORM_INTEGRATION]
---

# g-skl-platform-cline

Activate for: setting up gald3r with Cline (VS Code / JetBrains / CLI / SDK), authoring rules/workflows/skills/hooks, configuring MCP, or verifying the Cline gald3r install.

---

> Full 9-section breakdown + evidence URLs in `PLATFORM_SPEC.md` (this folder). **Status: ✅ full
> parity** — Cline natively supports commands (Workflows), rules, agents (SDK subagents/teams),
> skills (`SKILL.md`), hooks, and MCP. **Two caveats**: **hooks are macOS/Linux only** (no Windows
> yet — matters for the Windows dev env) and **subagents/teams need the Cline SDK / CLI runtime**
> (not the bare IDE chat). Cline reads **`AGENTS.md`, not `CLAUDE.md`**, and discovers
> **`.cline/skills/`, not `.claude/skills/`**. (Verified 2026-06-02 against https://docs.cline.bot.)

## 1. Platform Overview

**Cline** — an open-source autonomous coding agent shipped as a **VS Code / JetBrains extension**, a
**CLI**, and a public **SDK / agent runtime** (open-sourced ~May 2026, powers the CLI + Kanban board).
The IDE chat is single-agent; the **SDK / CLI** surface adds subagents, multi-agent teams, and
cron-able coordinators.

## 2. Config Layout

```
<project-root>/
├── AGENTS.md                       ← read by Cline (cross-tool standard; NOT CLAUDE.md)
├── .clinerules                     ← (legacy) single always-on rules FILE
└── .clinerules/                    ← (modern) rules DIRECTORY — all .md/.txt auto-injected
    ├── gald3r-rules.md             ← gald3r always-on rules (toggleable per-file, v3.13)
    ├── workflows/   *.md           ← custom slash commands (/<filename>)
    └── hooks/       <hooktype>     ← project lifecycle hooks (executable; macOS/Linux only)

<workspace-or-home>/
├── .cline/skills/  <name>/SKILL.md ← Agent Skills (workspace)  | ~/.cline/skills/ (global)
└── .cline/mcp.json                 ← MCP (CLI)  | cline_mcp_settings.json (IDE) | MCP Marketplace
```

Cline also auto-detects `.cursorrules` / `.windsurfrules` and reads `~/.agents/AGENTS.md` →
**cross-tool reuse**, but skills live under `.cline/skills/` (not `.claude/skills/`).

## 3. gald3r Integration

**Ship `AGENTS.md` + the `.cline*` trees** — rules → `.clinerules/`, commands →
`.clinerules/workflows/*.md`, skills → `.cline/skills/<name>/SKILL.md`, MCP →
`cline_mcp_settings.json` / `~/.cline/mcp.json`. Subagents/teams are authored against the **Cline SDK**
(CLI surface). Optionally publish to the community **github.com/cline/clinerules** library.

### Verify
```powershell
Test-Path AGENTS.md                      # instruction file Cline reads (not CLAUDE.md)
Test-Path .clinerules ; Test-Path .clinerules/workflows
Test-Path .cline/skills                  # Agent Skills dir (NOT .claude/skills)
# Hooks: macOS/Linux only — on Windows verify support before relying on g-hk-*
```

## 4. Common Pitfalls

- **Hooks are macOS/Linux only** at time of research (v3.36). On **Windows** (the <gald3r_source>
  dev env) `g-hk-*.ps1` do **not** wire natively — use git `core.hooksPath` or manual invocation for
  session-start / pre-tool gating until Windows hook support lands.
- **Subagents/teams need the Cline SDK / CLI runtime**, not the bare IDE chat — don't expect
  `g-agnt-*` orchestration from the extension chat alone.
- **Instruction file is `AGENTS.md`, not `CLAUDE.md`** — Cline does not auto-load `CLAUDE.md`.
- **Skills go in `.cline/skills/`, not `.claude/skills/`** — Cline does not discover the Claude tree.
- Workflows inject on-demand (`<explicit_instructions>` wrapper); rules append to every prompt — pick
  the right surface (token-efficient commands vs always-on rules).

## 5. Capability Summary

| Feature | Status | Notes |
|---|---|---|
| Hooks (`g-hk-*.ps1`) | ✅ | 6 events (PreToolUse/PostToolUse/UserPromptSubmit/TaskStart/TaskResume/TaskCancel); executable scripts, JSON stdin/stdout — **macOS/Linux only, no Windows** |
| Skills (`g-skl-*/SKILL.md`) | ✅ | Agent Skills, 3-tier progressive disclosure; `.cline/skills/` or `~/.cline/skills/`; `use_skill` tool |
| Agents (`g-agnt-*.md`) | ✅ | SDK subagents + teams (own model/tools/prompt, shared task board) — **SDK / CLI runtime, not bare IDE chat** |
| Commands (`@g-*`) | ✅ | Workflows = slash commands `.clinerules/workflows/*.md` (`/<filename>`) + built-ins |
| Rules (`g-rl-*`) | ✅ | `.clinerules` file or folder (all `.md`/`.txt`); toggleable (v3.13); frontmatter path-scoping; reads `AGENTS.md` |
| MCP | ✅ | STDIO + Remote HTTP/SSE; MCP Marketplace; `cline_mcp_settings.json` / `~/.cline/mcp.json` |

Full assessment + evidence in `PLATFORM_SPEC.md`. Re-verify on the next `@g-platform-scan-docs cline` (crawl_max_age_days: 14) — confirm Windows hook support status.
