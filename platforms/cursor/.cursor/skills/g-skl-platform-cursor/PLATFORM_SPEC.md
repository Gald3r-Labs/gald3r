---
subsystem_memberships: [PLATFORM_INTEGRATION]
platform: cursor
authoring_path: update
docs_url: https://cursor.com/docs
docs_url_secondary:
  - https://cursor.com/docs/context/rules
  - https://cursor.com/docs/subagents.md
  - https://cursor.com/help/customization/skills
  - https://cursor.com/changelog/1-6
  - https://cursor.com/docs/hooks
  - https://cursor.com/docs/context/mcp
crawl_max_age_days: 7
vault_doc_path: research/platforms/cursor/
last_doc_scan: 2026-06-02
reference: g-skl-platform-cursor
status: ✅
task: T1462
---

# PLATFORM_SPEC.md — Cursor (reference implementation)

Cursor is the **reference platform** for gald3r. All gald3r primitives originate in the Cursor
(`.cursor/`) tree and propagate to every other platform via
`custom_scripts/platform_parity_sync.ps1`. As of mid-2026 Cursor natively supports **all six**
gald3r-relevant extension primitives — custom slash commands, always-on rules (plus `AGENTS.md`),
specialized subagents, Agent Skills (`SKILL.md`), a rich lifecycle hooks system, and MCP — each with
its own `.cursor/` path. Notably, Cursor has adopted cross-tool conventions: it natively reads
**`.claude/agents/`** and **`.codex/agents/`** for subagents and **`.agents/skills/`** for skills, so
gald3r assets authored to those open conventions are reused without a Cursor-specific copy.

**Authoring path**: UPDATE. **Verified 2026-06-02** against https://cursor.com/docs (see Verification
Evidence). This **supersedes** the prior spec (`last_doc_scan: never`) which described the
filesystem-counted reference layout but had not been confirmed against live docs — all six mechanisms
are now confirmed NATIVE from the official docs crawl.

> **Surface split:** the full extensibility (commands/rules/agents/skills/hooks/MCP) lives in the
> **Cursor IDE** (desktop app, VS Code fork). A separate **Cursor CLI** (`agent`) exposes its own
> slash-commands reference and Cloud Agent handoff, and a **TypeScript SDK** builds programmatic
> agents. Where a feature is IDE-only or has a CLI/SDK caveat it is noted inline.

---

## 1. Folder Hierarchy

gald3r writes everything under the repo-root `.cursor/` folder. Verified layout:

```
<project-root>/
├── AGENTS.md                     ← instruction file Cursor reads natively (root + nested dirs)
├── .cursorrules                  ← legacy single-file instructions (still recognized)
└── .cursor/
    ├── rules/        *.mdc        ← always-apply / on-demand rules (Cursor-specific .mdc)
    ├── commands/     *.md         ← custom slash commands (Cursor 1.6)
    ├── agents/       *.md         ← subagents (markdown + YAML frontmatter; Cursor 2.4)
    ├── skills/       <name>/SKILL.md  ← Agent Skills (SKILL.md standard; Cursor 2.4)
    ├── hooks.json                 ← TOP-LEVEL hook wiring (NOT .cursor/hooks/hooks.json)
    └── mcp.json                   ← MCP server config (or ~/.cursor/mcp.json / Cursor settings)
```

Cursor **also** discovers `.claude/agents/` and `.codex/agents/` (subagents) and `.agents/skills/`
(skills), workspace or `~/`. gald3r's `.claude/`-style agent/skill trees therefore work on Cursor with
**no Cursor-specific port**.

**gald3r writes**: `rules/` (`.mdc`), `commands/`, `agents/`, `skills/`, `hooks.json`, `mcp.json`.
**Cursor owns**: the `.cursor/` namespace, the `hooks.json` / `mcp.json` schema, Cursor settings, and
the rule auto-load mechanism.

**Verified note:** `hooks.json` lives at **`.cursor/hooks.json`** (repo `.cursor/` root), not inside
`.cursor/hooks/`; companion `_hook_md` fields point at `.md` files inside `.cursor/hooks/`.

---

## 2. AI Instruction File

Cursor reads, in precedence order: **`AGENTS.md`** (plain markdown, no frontmatter required, at the
project root **and** in nested subdirectories — more specific files take precedence) → legacy
`.cursorrules` → `.cursor/rules/*.mdc` (§7). **Cursor's primary cross-tool instruction file is
`AGENTS.md`, not `CLAUDE.md`** — unlike Auggie/Claude Code, Cursor does **not** treat `CLAUDE.md` as a
first-class input. gald3r's `AGENTS.md` (root) is the canonical instruction file; `CLAUDE.md` /
`GEMINI.md` are platform-personalized variants for their respective tools.

gald3r **generates/merges** these via the setup + parity pipeline; they are personalized per user and
gitignored (see `g-rl-02` protected files).

---

## 3. Agents Support — ✅ NATIVE

- **Subagents**: specialized AI assistants, each in its own context window, delegated to by the parent
  agent and runnable **in parallel**. Defined as markdown + YAML frontmatter (`name`, `description`,
  `model` [`inherit` | a specific id e.g. `composer-2`], `readonly`, `is_background`) in
  `.cursor/agents/*.md` (project) or `~/.cursor/agents/*.md` (global). Cursor **also natively reads
  `.claude/agents/` and `.codex/agents/`**. Shipped in **Cursor 2.4**.
- gald3r `g-agnt-*` definitions map directly to Cursor subagent files — including straight from
  `.claude/agents/`.
- Source: https://cursor.com/docs/subagents.md

## 4. Skills Support — ✅ NATIVE

- **Agent Skills** (`SKILL.md` with optional YAML frontmatter; `paths:` field for glob scoping) teach
  the Agent multi-step workflows. Auto-loaded from `.cursor/skills/<name>/SKILL.md`,
  **`.agents/skills/`**, and user-level `~/.cursor/skills/` and `~/.agents/skills/`; supports
  nested/monorepo dirs. Invoked on-demand via `/skill-name` or `@skill-name`. Existing commands convert
  via `/migrate-to-skills`. Shipped in **Cursor 2.4**.
- **Folder-per-skill**: a loose `.md` directly in `skills/` root is NOT picked up.
- gald3r `g-skl-*/SKILL.md` load natively — including from `.agents/skills/`.
- Source: https://cursor.com/help/customization/skills

## 5. Commands / Workflows — ✅ NATIVE

- **Custom slash commands**: reusable AI prompts saved as markdown in `.cursor/commands/<name>.md`
  (project) or `~/.cursor/commands/<name>.md` (global); the filename becomes the slash command, run by
  typing `/` in the Agent input. Introduced in **Cursor 1.6**.
- gald3r `@g-*` / `/g-*` commands map directly.
- Source: https://cursor.com/changelog/1-6

## 6. Hooks System — ✅ NATIVE

- **Agent lifecycle hooks**: spawned processes that communicate over **stdio using JSON in both
  directions**; they run before/after stages of the agent loop and can **observe, block, or modify**
  behavior. Configured in `hooks.json` at `.cursor/hooks.json` (project), `~/.cursor/hooks.json`
  (user), or enterprise/team locations (Windows system path `C:\ProgramData\Cursor\hooks.json`).
  Added in **Cursor 1.7**.
- **Events** (large surface): `sessionStart` / `sessionEnd`, `preToolUse` / `postToolUse` /
  `postToolUseFailure`, `subagentStart` / `subagentStop`, `beforeShellExecution` /
  `afterShellExecution`, `beforeMCPExecution` / `afterMCPExecution`, `beforeReadFile` /
  `afterFileEdit`, `beforeSubmitPrompt`, `preCompact`, `stop`, `afterAgentResponse` /
  `afterAgentThought`, plus Tab hooks (`beforeTabFileRead` / `afterTabFileEdit`) and app lifecycle
  (`workspaceOpen`).
- gald3r `g-hk-*.ps1` hooks wire natively via these events (e.g. `g-hk-session-start.py` →
  `sessionStart`; `g-hk-validate-shell.py` → `beforeShellExecution`; `g-hk-pre-tool-call-*.ps1` →
  `preToolUse`; session-end hooks → `stop`). Each entry: `command` (full PowerShell invocation),
  optional `matcher` (regex over tool names), optional `_hook_md` (companion doc, T1171).
- Source: https://cursor.com/docs/hooks

## 7. Rules / Memory — ✅ NATIVE

- **Project rules** in `.cursor/rules/*.mdc` with frontmatter (`alwaysApply`, `globs`, `description`)
  and four application types: **Always Apply**, **Apply Intelligently** (`description`-scoped),
  **Apply to Specific Files** (`globs`), **Apply Manually**. **`AGENTS.md`** (plain markdown at root /
  nested dirs) is supported as an alternative. **User rules** set global preferences via Settings;
  **Team rules** (Team/Enterprise) take top precedence.
- **`.mdc` is Cursor-specific** — all other platforms use plain `.md`; the parity sync maps the
  extension automatically.
- **Memories caveat**: per-project auto-generated **Memories** shipped in v1.0 (June 2025) but were
  reported removed / folded into **Rules** starting v2.1.x; the dedicated memories doc page now
  resolves to Rules content. **Rules** remains the durable always-on mechanism (gald3r also uses
  `.gald3r/learned-facts.md` for durable project facts, surfaced at session start by `g-rl-25`).
- gald3r `g-rl-*` map to **Always Apply** (for `alwaysApply: true`) or **Apply Intelligently** (for
  `description:`-scoped).
- Source: https://cursor.com/docs/context/rules

## 8. MCP Support — ✅ NATIVE

- MCP servers via JSON config at `.cursor/mcp.json` (project) or `~/.cursor/mcp.json` (global), or via
  Cursor Settings → MCP. Supports **stdio** (Cursor-managed local), **SSE**, and **Streamable HTTP**
  transports; remote servers support **OAuth and multi-user access**. Cursor auto-connects to
  configured servers on startup.
- **Timeout**: default MCP timeout is 60s; for long-running tools set `mcp.server.timeout: 600000` in
  Cursor settings.json.
- Source: https://cursor.com/docs/context/mcp

## 9. SDK / CLI & Governance — distribution channels

- **Cursor CLI** (`agent`): provides its own slash-commands reference
  (`cursor.com/docs/cli/reference/slash-commands`) plus **Cloud Agent** handoff.
- **Cursor SDK** (TypeScript): build programmatic agents against Cursor.
- **Enterprise/team governance**: hooks, **Team rules**, and MCP can be centrally managed via the web
  dashboard and system-level config paths (Enterprise) — e.g. `C:\ProgramData\Cursor\hooks.json` on
  Windows.

---

## Parity vs. Cursor Reference

Cursor **is** the reference, so there are no "gaps vs. another platform." All six gald3r-relevant
primitives are native: **commands, rules, agents, skills, hooks, and MCP**. The honest baseline items
within the Cursor implementation itself: `.mdc` rules and `hooks.json` wiring are correctly classified
as **platform-specific** (live in the Cursor tree, not common `.gald3r_sys/`); per-machine MCP server
sets are not committed; and the **Memories** primitive was folded into Rules in v2.1.x (no action
needed — Rules is the durable surface).

**Reuse note (important):** because Cursor discovers `.claude/agents/` + `.codex/agents/` (subagents)
and `.agents/skills/` (skills), gald3r's **Claude-Code-format agent/skill artifacts are reusable on
Cursor without a separate port**. (Unlike Auggie, Cursor's primary instruction file is `AGENTS.md`,
**not** `CLAUDE.md` — keep gald3r's `AGENTS.md` authoritative.)

## Hook System

- **Type**: native (json_config — stdio JSON, bidirectional)
- **Config file**: `.cursor/hooks.json` (repo-root `.cursor/`, version 1 — NOT inside `.cursor/hooks/`)
- **Events available**: `sessionStart`/`sessionEnd`, `preToolUse`/`postToolUse`/`postToolUseFailure`,
  `subagentStart`/`subagentStop`, `beforeShellExecution`/`afterShellExecution`,
  `beforeMCPExecution`/`afterMCPExecution`, `beforeReadFile`/`afterFileEdit`, `beforeSubmitPrompt`,
  `preCompact`, `stop`, `afterAgentResponse`/`afterAgentThought`, Tab hooks
  (`beforeTabFileRead`/`afterTabFileEdit`), `workspaceOpen`
- **Event payload format**: JSON over stdio in **both directions** (hooks observe/block/modify; return
  the standard `{ continue = true }` envelope or block via exit code / verdict)
- **Command extensions**: full PowerShell invocation; optional `matcher` regex over tool names;
  `_hook_md` companion-doc path (T1171)
- **gald3r hook files**: `g-hk-session-start.py` (sessionStart); `g-hk-agent-complete.py`,
  `g-hk-nightly-learn.ps1`, `g-hk-session-end.py` (stop); `g-hk-validate-shell.py`
  (beforeShellExecution); `g-hk-pre-tool-call-gald3r-guard.py`, `g-hk-pre-tool-call-prd-freeze.py`,
  `g-hk-pre-tool-call-member-gald3r-guard.py` (preToolUse)

## Atypical Handling

- Rules use the Cursor-only `.mdc` extension (all other platforms use `.md`); parity sync maps the
  extension automatically.
- `hooks.json` lives at `.cursor/hooks.json` (repo `.cursor/` root), not inside `.cursor/hooks/`;
  `_hook_md` fields point at companion `.md` files inside `.cursor/hooks/`.
- Primary instruction file is **`AGENTS.md`** (root + nested), NOT `CLAUDE.md`. Always-apply behavior
  comes from `.cursor/rules/*.mdc` (`alwaysApply: true`).
- Cross-tool discovery: `.claude/agents/` + `.codex/agents/` (subagents) and `.agents/skills/`
  (skills) are read directly — prefer reusing them.
- Hook execution: PowerShell on Windows; cross-platform invocation must be honored for Unix users.
  Enterprise hook path on Windows is `C:\ProgramData\Cursor\hooks.json`.
- MCP may be configured via `.cursor/mcp.json`, `~/.cursor/mcp.json`, or Cursor settings; concrete
  server set is per-machine.

## gald3r Integration Notes

- Cursor is the **reference platform**: this is the canonical hook/rule/skill/command/agent layout
  other platforms mirror. There are no "gaps vs another platform."
- Ship gald3r's `AGENTS.md` + `.cursor/` tree; Cursor also discovers `.claude/agents/` +
  `.codex/agents/` + `.agents/skills/` so Claude-format agent/skill artifacts are reused as-is.
- Hooks fire natively (`.ps1` supported via full PowerShell invocation); session-start / pre-commit /
  pre-tool guards wire without degrading to manual.
- Re-verify on the next `@g-platform-scan-docs cursor` (crawl_max_age_days: 7) against
  https://cursor.com/docs — watch for new hook events and Rules/Memories changes.

---

## Capability Summary (copy into PLATFORM_STATUS.md row)

| Hooks | Rules | Skills | Commands | MCP | Docs Fresh |
|---|---|---|---|---|---|
| ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |

Legend: ✅ verified working · ⚠️ partial / Cursor-generic · ❌ not supported · ❓ untested.

---

## Verification Evidence (docs crawl 2026-06-02, https://cursor.com/docs)

| Capability | How verified |
|---|---|
| Commands | /changelog/1-6 — reusable prompts in `.cursor/commands/<name>.md` (or `~/.cursor/commands/`); filename = slash command; Cursor 1.6 |
| Rules | /docs/context/rules — `.cursor/rules/*.mdc` (alwaysApply/globs/description; 4 application types) + `AGENTS.md` + User/Team rules; Memories folded into Rules v2.1.x |
| Agents | /docs/subagents.md — `.cursor/agents/*.md` md+YAML, parallel subagents; also reads `.claude/agents/` + `.codex/agents/`; Cursor 2.4 |
| Skills | /help/customization/skills — `SKILL.md` in `.cursor/skills/<name>/` + `.agents/skills/` (+ `~/`); `/skill-name` or `@skill-name`; Cursor 2.4 |
| Hooks | /docs/hooks — `.cursor/hooks.json`; stdio JSON bidirectional; large event surface (sessionStart…afterAgentThought + Tab/workspaceOpen); Cursor 1.7 |
| MCP | /docs/context/mcp — `.cursor/mcp.json` / `~/.cursor/mcp.json` / Settings; stdio + SSE + Streamable HTTP; OAuth + multi-user |
| Instruction file | /docs/context/rules — `AGENTS.md` native (root + nested, no frontmatter); legacy `.cursorrules`; native rules format `.cursor/rules/*.mdc` |
| Cross-compat | Cursor discovers `.claude/agents/` + `.codex/agents/` (subagents) and `.agents/skills/` (skills) → gald3r Claude/codex artifacts reusable |
