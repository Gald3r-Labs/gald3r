---
subsystem_memberships: [PLATFORM_INTEGRATION]
platform: cline
authoring_path: update
docs_url: https://docs.cline.bot
docs_url_secondary:
  - https://docs.cline.bot/features/slash-commands/workflows
  - https://docs.cline.bot/customization/cline-rules
  - https://docs.cline.bot/sdk/guides/multi-agent-teams
  - https://docs.cline.bot/features/skills
  - https://cline.bot/blog/cline-v3-36-hooks
  - https://docs.cline.bot/mcp/mcp-overview
crawl_max_age_days: 14
vault_doc_path: research/platforms/cline/
last_doc_scan: 2026-06-02
reference: g-skl-platform-cursor
status: ✅
task: T1474
---

# PLATFORM_SPEC.md — Cline (VS Code / JetBrains extension + CLI + SDK)

Cline is an **open-source autonomous coding agent** shipped as a VS Code / JetBrains extension, a
**CLI**, and a public **SDK / agent runtime**. As of mid-2026 it natively supports **all six**
gald3r-relevant extension primitives — custom slash commands (**Workflows**), always-on rules
(`.clinerules`) plus cross-tool `AGENTS.md`, native **subagents / multi-agent teams** (via the Cline
SDK), **Agent Skills** (`SKILL.md`, progressive disclosure), lifecycle **Hooks** (6 event types,
executable scripts), and full **MCP** with a marketplace. Skills, Workflows, and Hooks all accept an
optional `scripts/` directory — genuine script-execution extensibility beyond pure-prompt injection.

**Authoring path**: UPDATE. **Verified 2026-06-02** against https://docs.cline.bot (see Verification
Evidence). This **supersedes** the prior spec (`last_doc_scan: never`, `status: ⚠️`) which incorrectly
marked hooks/skills/agents as ❌ and commands as ⚠️ — they are now all **NATIVE**. The prior
"`.clinerules` + memory-bank only" model is obsolete.

> **Two platform-specific caveats (do not drop on re-sync):**
> 1. **Hooks are macOS/Linux only** at time of research (v3.36, Nov 2025) — **no Windows support yet**.
>    The <gald3r_source> dev environment is Windows, so verify Windows hook support before relying
>    on `g-hk-*` file-watch / pre-tool gating in Cline installs.
> 2. **Native subagents / teams require the Cline SDK or CLI runtime**, not the bare IDE chat.
>
> **Instruction-file convention:** Cline reads **`.clinerules` and `AGENTS.md`** (plus `.cursorrules`
> / `.windsurfrules` for cross-tool compat). It does **NOT** read `CLAUDE.md`. gald3r's `AGENTS.md` is
> the first-class input on Cline; `CLAUDE.md` is not auto-loaded.

---

## 1. Folder Hierarchy

```
<project-root>/
├── AGENTS.md                       ← instruction file Cline reads (cross-tool standard; NOT CLAUDE.md)
├── .clinerules                     ← (legacy) single always-on rules FILE
└── .clinerules/                    ← (modern) rules DIRECTORY — every .md/.txt auto-injected
    ├── gald3r-rules.md             ← gald3r always-on rules (toggleable per-file, v3.13)
    ├── workflows/   *.md           ← custom slash commands (/<filename>)
    └── hooks/       <hooktype>     ← project lifecycle hooks (executable, no extension)

<workspace-or-home>/
├── .cline/skills/    <name>/SKILL.md   ← Agent Skills (workspace)  | ~/.cline/skills/ (global)
├── .cline/mcp.json                     ← MCP config (CLI)          | cline_mcp_settings.json (IDE)
└── ~/Documents/Cline/Rules/Hooks/      ← global hooks dir          | + global rules dir
```

Cline **also** auto-detects `.cursorrules` and `.windsurfrules` for cross-tool compatibility, and
reads `~/.agents/AGENTS.md`. The bare project-root `AGENTS.md` is now a listed supported source.

**gald3r writes**: `.clinerules/` (rules), `.clinerules/workflows/` (commands), `.cline/skills/`
(skills), `.clinerules/hooks/` (hooks, non-Windows), MCP via `cline_mcp_settings.json` / `~/.cline/mcp.json`.
**Cline owns**: the Workflow `<explicit_instructions>` wrapping, the 3-tier Skill loader, and the
MCP Marketplace catalog (Cline-managed, not a gald3r-writable surface).

---

## 2. AI Instruction File

Cline's rules table recognizes, in addition to `.clinerules`: **`AGENTS.md`** (project root and
`~/.agents/AGENTS.md`, "standard format for cross-tool compatibility"), `.cursorrules`, and
`.windsurfrules`, plus a global `~/Documents/Cline/Rules` store. **No `CLAUDE.md`** — gald3r ships
its instruction content as `AGENTS.md` for Cline. (Community issues #5033/#7062/#6162 historically
requested project-root `AGENTS.md` auto-loading; the current docs page now lists bare `AGENTS.md` as
a supported source.)

---

## 3. Agents Support — ✅ NATIVE (SDK / CLI runtime)

- **Subagents + Multi-Agent Teams** via the **Cline SDK** (open-sourced ~May 2026, powers the CLI
  and Kanban board). "The SDK includes agent teams and subagents natively, so a session can delegate
  to specialists, track progress, and exchange handoff notes, all inside the same core runtime."
- Each subagent gets its own `Agent` instance with a dedicated **model, tool set, and system prompt**;
  teams coordinate through a **shared task board** with one coordinator delegating to specialists.
- **Caveat**: requires the **Cline SDK / CLI runtime**, not the bare IDE chat. Coordinator agents can
  be run on **cron** for recurring automations (relevant to gald3r scheduled / heartbeat workflows).
- gald3r `g-agnt-*` definitions map to SDK subagent definitions (CLI surface).
- Source: https://docs.cline.bot/sdk/guides/multi-agent-teams

## 4. Skills Support — ✅ NATIVE

- **Agent Skills** ("natively integrated into Cline, using a simple directory structure with
  `SKILL.md` files and optional supporting documents or scripts"). Each skill is a folder with
  `SKILL.md` (YAML `name` + `description` ≤1024 chars) plus optional `docs/` / `templates/` /
  `scripts/`.
- Discovered from **`.cline/skills/`** (workspace) or **`~/.cline/skills/`** (global). Loaded in
  **3 tiers** — metadata (~100 tokens, always) → instructions (on trigger) → resources (on demand) —
  and activated via the **`use_skill`** tool. Enabled Skills are also triggerable as slash commands.
- gald3r `g-skl-*/SKILL.md` load natively (folder name = skill id). **Note:** Cline discovers
  `.cline/skills/`, **not** `.claude/skills/` — gald3r must place skills under `.cline/skills/`.
- Source: https://docs.cline.bot/features/skills

## 5. Commands / Workflows — ✅ NATIVE

- **Workflows = custom slash commands.** Any markdown file in **`.clinerules/workflows/`** becomes a
  slash command invoked by typing `/` + the filename (e.g. `/deploy.md`). Built-in commands include
  `/newtask`, `/smol`, `/newrule`, `/deep-planning`.
- Workflows inject **on-demand only when invoked** (token-efficient), wrapped in
  `<explicit_instructions>` tags — distinct from rules, which append to every system prompt.
- gald3r `@g-*` / `/g-*` commands map to `.clinerules/workflows/*.md`.
- Source: https://docs.cline.bot/features/slash-commands/workflows

## 6. Hooks System — ✅ NATIVE (macOS/Linux only)

- **Lifecycle hooks** (v3.36, Nov 2025): "a system for injecting custom logic into the AI workflow at
  critical decision points." **Six hook types**: **PreToolUse, PostToolUse, UserPromptSubmit,
  TaskStart, TaskResume, TaskCancel**.
- Hooks are **executable scripts** (no extension, named after the hook type) in
  **`~/Documents/Cline/Rules/Hooks/`** (global) or **`.clinerules/hooks/`** (project). Each receives
  **JSON via stdin** and returns **JSON** with `cancel` + `contextModification` fields. Lifecycle
  hooks can also be registered programmatically via the **SDK plugin system**.
- **⚠️ OS LIMIT — macOS/Linux only at time of research; Windows NOT yet supported.** gald3r's
  PowerShell `g-hk-*.ps1` hooks therefore do **not** wire natively on Windows Cline. On Windows, hook
  behaviors (SessionStart context injection, PreToolUse `.gald3r/` guards, pre-commit gates) must run
  out-of-band (git `core.hooksPath`, manual invocation) until Windows hook support lands.
- Source: https://cline.bot/blog/cline-v3-36-hooks

## 7. Rules / Memory — ✅ NATIVE

- **`.clinerules`** — single file OR a **`.clinerules/` folder**. "Cline processes all `.md` and
  `.txt` files inside `.clinerules/`, combining them into a unified set of rules" so preferences are
  not repeated each task. A **toggleable popover (v3.13)** enables/disables individual rule files.
- **Conditional rules**: YAML frontmatter scopes rules to **matching file paths** (path-glob scoping
  IS supported via frontmatter — an upgrade over the prior spec's "no glob scoping" claim).
- gald3r `g-rl-*` map to files in `.clinerules/`. Always-on rules → plain files; path-scoped rules →
  frontmatter path conditions.
- Source: https://docs.cline.bot/customization/cline-rules

## 8. MCP Support — ✅ NATIVE

- **Model Context Protocol** servers + a built-in **MCP Marketplace** (one-click install). "MCP lets
  Cline use external tools and data sources through MCP servers." Supports **STDIO** (local process)
  and **Remote HTTP/SSE** transports.
- Config: **`cline_mcp_settings.json`** (IDE) or **`~/.cline/mcp.json`** (CLI).
- Source: https://docs.cline.bot/mcp/mcp-overview

## 9. SDK / Plugins — distribution + code-driven path

- The **Cline SDK** (open-sourced ~May 2026) is the upgraded agent runtime powering the CLI and
  Kanban board. It exposes a **plugin system** where a plugin can register **tools, observe lifecycle
  events, AND add rules and commands programmatically** — a second, code-driven path to all of the
  above primitives.
- Community library **github.com/cline/clinerules** hosts shareable rules, skills, workflows, and
  `AGENTS.md` files — a distribution channel gald3r tiers could publish into.
- Source: https://docs.cline.bot/sdk/guides/multi-agent-teams

---

## Parity vs. Cursor Reference

Cline now reaches **full parity** with the Cursor reference (`g-skl-platform-cursor`): native
**commands, rules, agents, skills, hooks, and MCP**, with MCP a **standout strength** (in-editor
marketplace, STDIO + remote). The two honest caveats are **(a)** hooks are **macOS/Linux only**
(Windows gap — material for the Windows-based <gald3r_source> dev env), and **(b)** native subagents
/ teams require the **Cline SDK / CLI runtime**, not the bare IDE chat.

**Reuse note:** gald3r maps cleanly — rules → `.clinerules/`, commands → `.clinerules/workflows/`,
skills → `.cline/skills/SKILL.md`, hooks → `.clinerules/hooks/` (non-Windows). Cline reads `AGENTS.md`
(not `CLAUDE.md`) and discovers `.cline/skills/` (not `.claude/skills/`), so the Cline install ships
`AGENTS.md` + the `.cline*` trees rather than reusing the Claude-Code `.claude/` tree as-is.

## Hook System

- **Type**: native (executable lifecycle scripts) — **macOS/Linux only (no Windows support yet)**
- **Config dir**: `~/Documents/Cline/Rules/Hooks/` (global) or `.clinerules/hooks/` (project)
- **Events available**: PreToolUse, PostToolUse, UserPromptSubmit, TaskStart, TaskResume, TaskCancel
- **Event payload format**: JSON via stdin; result JSON with `cancel` + `contextModification` fields
- **Script form**: executable, no extension, named after the hook type; SDK plugins may register hooks programmatically
- **gald3r hook files**: `g-hk-*.ps1` do **NOT** wire natively on Windows; on macOS/Linux, adapt to the executable-script-named-after-event convention

## Atypical Handling

- **OS gate on hooks**: Windows is unsupported at time of research — degrade Windows hook behaviors to
  git `core.hooksPath` / manual until Windows support lands.
- **Two agent surfaces**: the **IDE chat** (single-agent) vs the **SDK / CLI runtime** (subagents +
  teams + cron). Target the SDK/CLI for full gald3r multi-agent parity.
- **Instruction file is `AGENTS.md`, not `CLAUDE.md`**; skills live under `.cline/skills/`, not
  `.claude/skills/` — Cline-specific placement, not Claude-Code drop-in.

## gald3r Integration Notes

- Ship `AGENTS.md` + `.clinerules/` (rules) + `.clinerules/workflows/` (commands) + `.cline/skills/`
  (skills) + MCP via `cline_mcp_settings.json` / `~/.cline/mcp.json`.
- Hooks fire natively only on macOS/Linux — on Windows do **not** rely on `g-hk-*` for session-start /
  pre-tool gating; use git hooks or manual invocation.
- Subagents / teams require the Cline SDK or CLI runtime (and can run on cron for heartbeat flows).
- Re-verify on the next `@g-platform-scan-docs cline` (crawl_max_age_days: 14) — confirm Windows hook
  support status.

---

## Capability Summary (copy into PLATFORM_STATUS.md row)

| Hooks | Rules | Skills | Commands | MCP | Docs Fresh |
|---|---|---|---|---|---|
| ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |

Legend: ✅ verified working · ⚠️ partial / Cursor-generic · ❌ not supported · ❓ untested.

Note: ✅ Hooks is **macOS/Linux only** (no Windows support at time of research). ✅ Agents
(subagents/teams) require the **Cline SDK / CLI runtime**, not the bare IDE chat.

---

## Verification Evidence (docs crawl 2026-06-02, https://docs.cline.bot)

| Capability | How verified |
|---|---|
| Commands | /features/slash-commands/workflows — `.clinerules/workflows/*.md` → `/<filename>`; built-ins `/newtask`, `/smol`, `/newrule`, `/deep-planning`; injected in `<explicit_instructions>` |
| Rules | /customization/cline-rules — `.clinerules` file OR `.clinerules/` folder (all `.md`/`.txt` combined); toggleable popover (v3.13); YAML frontmatter path-scoping; reads `AGENTS.md` (NOT `CLAUDE.md`) |
| Agents | /sdk/guides/multi-agent-teams — SDK subagents + teams (own model/tools/prompt, shared task board); CLI/SDK runtime only; cron-able coordinators |
| Skills | /features/skills — `SKILL.md` (YAML name + ≤1024-char description) in `.cline/skills/` or `~/.cline/skills/`; 3-tier progressive disclosure; `use_skill` tool |
| Hooks | /blog/cline-v3-36-hooks — 6 events (PreToolUse/PostToolUse/UserPromptSubmit/TaskStart/TaskResume/TaskCancel); executable scripts; JSON stdin/stdout (`cancel`+`contextModification`); **macOS/Linux only, no Windows** |
| MCP | /mcp/mcp-overview — STDIO + Remote HTTP/SSE; MCP Marketplace; `cline_mcp_settings.json` (IDE) / `~/.cline/mcp.json` (CLI) |
| Cross-compat | Reads `AGENTS.md` + `.cursorrules` + `.windsurfrules`; community `github.com/cline/clinerules` distribution library; SDK plugins add tools/rules/commands programmatically |
