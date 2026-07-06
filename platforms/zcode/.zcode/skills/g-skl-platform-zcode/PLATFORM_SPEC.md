---
subsystem_memberships: [PLATFORM_INTEGRATION]
platform: zcode
authoring_path: new
docs_url: https://zcode.z.ai/en/docs/agents
docs_url_secondary:
  - https://zcode.z.ai/en/docs/welcome
  - https://zcode.z.ai/en/docs/mcp-services
  - https://zcode.z.ai/en/docs/subagents
  - https://zcode.z.ai/en/docs/skill
  - https://zcode.z.ai/en/docs/commands
  - https://zcode.z.ai/en/docs/plugin
  - https://zcode.z.ai/en/docs/configuration
crawl_max_age_days: 14
vault_doc_path: research/platforms/zcode/
last_doc_scan: 2026-07-03
reference: g-skl-platform-cursor
status: ⚠️
task: platform-ZCode
---

# PLATFORM_SPEC.md — ZCode (Z.ai / Zhipu)

**ZCode** (`zcode.z.ai`) is Z.ai's free, cross-platform **Agentic Development Environment (ADE)**
built around the **GLM-5.2** model, explicitly positioned to challenge Cursor, Claude Code, and
GitHub Copilot. It supports **BYOK** (bring-your-own-key) for other model providers alongside
Z.ai/BigModel accounts. ZCode is a desktop app (not a bare CLI) with a chat-first UI, Settings
panels for MCP/Skills/Commands/Subagents, and a Plugin marketplace.

**Authoring path**: NEW. **Verified 2026-07-03** against https://zcode.z.ai/en/docs/agents and the
docs pages listed above (see Verification Evidence). No prior gald3r spec existed for this platform.

> **Instruction-file truth (read carefully):** ZCode reads a **global `~/.zcode/AGENTS.md`** plus a
> **workspace-root `AGENTS.md`**, and **appends the global instructions first, then the workspace
> instructions** — it does **not** merge hierarchically (no per-subdirectory scan) and does **not**
> support `@import`/`@include` expansion. This is a flatter, simpler model than Cursor/Claude
> Code/Qwen/Gemini. ZCode does **not** read `CLAUDE.md`.

---

## 1. Folder Hierarchy

```
<project-root>/
├── AGENTS.md                        ← workspace instructions (appended AFTER global ~/.zcode/AGENTS.md)
└── .zcode/
    └── skills/   <name>/SKILL.md    ← Agent Skills (YAML frontmatter: name, description + body)

~/.zcode/
├── AGENTS.md                        ← global/user instructions — read FIRST
├── agents/   <name>.md              ← subagents (Beta) — GLOBAL/USER-LEVEL ONLY
├── commands/ <name>.md              ← custom slash commands (global scope)
└── skills/   <name>/SKILL.md        ← user-level skills

(MCP servers)                        ← configured via Settings → MCP Servers (Form or Full-config
                                        JSON), persisted to a `.zcode` config file at User or
                                        Workspace scope — exact on-disk filename not published.
```

**gald3r writes**: workspace `AGENTS.md` and `.zcode/skills/<name>/SKILL.md`. **ZCode owns**: the
`.zcode` namespace, the MCP config file schema/location (UI-managed, exact path undocumented), and
the global `~/.zcode/` tree.

---

## 2. AI Instruction File

ZCode reads **`AGENTS.md`** at two fixed scopes — **not** a hierarchical directory walk:

1. `~/.zcode/AGENTS.md` (global/user-level, read first)
2. `<workspace-root>/AGENTS.md` (appended after the global file)

There is **no** per-subdirectory `AGENTS.md` discovery, and **no** `@file.md`-style import/include
expansion (confirmed against docs/agents: "does not scan child directories, expand @import /
@include, or choose rule files automatically by task type"). Whatever gald3r wants ZCode to see must
be written directly into the workspace-root `AGENTS.md` body — the `@AGENTS.md`-import overlay
pattern gald3r uses for Qwen/Gemini/Antigravity (`QWEN.md` / `GEMINI.md` importing `@AGENTS.md`) does
**not** apply here, because ZCode has no import mechanism to resolve the `@` reference.

- ZCode does **not** read `CLAUDE.md`.
- Docs guidance for `AGENTS.md` content: document project stack/structure/key modules, code style
  and validation steps, high-risk files, and team collaboration preferences.
- Source: https://zcode.z.ai/en/docs/agents

---

## 3. Agents Support — ⚠️ PARTIAL (Beta, global-level only)

- **Subagents** are stored as Markdown files under `~/.zcode/agents/<name>.md`. The current Beta
  manages **global/user-level** subagents only — **no project-level agent roster exists yet**.
- Configuration fields (captured via the Settings creation form): `name`, `color` (visual only),
  `model` (inherit default or specific), `description` (guides auto-invocation), `available tools`
  (all by default, or a custom read-only/writable subset), `system prompt`.
- **Invocation**: automatic (primary Agent decides when to delegate) or manual via `@name` in chat.
- Two **built-in subagents** ship pre-configured, cannot be edited/deleted, and their names cannot be
  reused for custom subagents.
- **gald3r gap**: gald3r's `g-agnt-*.md` set has no project-scoped landing zone on ZCode today — a
  real install would need to write into the user's global `~/.zcode/agents/`, which is
  machine-specific and out of scope for a per-project overlay. Document this as a manual step rather
  than fabricating a project-level `agents/` folder that ZCode does not read.
- Source: https://zcode.z.ai/en/docs/subagents

## 4. Skills Support — ✅ NATIVE

- **Agent Skills**: a `SKILL.md` file inside a per-skill directory; the directory name is the skill
  identifier used in chat. YAML frontmatter carries `name` and `description`; the body is Markdown
  guidance on when/how to use the skill.
- **Locations**: `~/.zcode/skills/<name>/SKILL.md` (global/user-level) and project-scoped skills
  within a workspace (exact project-level path mirrors the global one: `.zcode/skills/<name>/`).
- **Discovery/management**: Settings → Skills (search, enable/disable, create with agent guidance,
  refresh after edits). **Invocation**: type `$` in chat and select, e.g. `$code-review-checklist
  review my current changes`.
- **Import**: skills can be imported from other AI tools (Claude Code, Codex CLI, etc.) via symlink
  or copy — gald3r's `g-skl-*/SKILL.md` files are drop-in compatible (same `name`/`description`
  frontmatter shape as agentskills.io).
- Source: https://zcode.z.ai/en/docs/skill

## 5. Commands / Workflows — ✅ NATIVE

- **Custom commands** are `.md` files stored at **User scope** (`~/.zcode/commands`) or **Workspace
  scope** (project directory). Created via the Commands settings panel with fields: `Scope`
  (User/Workspace), `Name` (invoked as `/name`), `Description` (optional, shown in the picker),
  `Argument hint` (optional, e.g. `<file-path>`), `Prompt` (the content sent to the agent).
- **Invocation**: type `/` to open the command panel, filter by name, supply arguments.
  Two **built-in commands** ship: `/goal` (manage session objectives) and `/compact` (condense
  context).
- **Import**: commands can be imported from other AI agents via the Commands settings page and
  remain fully editable afterward.
- gald3r `@g-*` commands map to `.zcode/commands/<name>.md` (workspace scope) as simple prompt files
  — there is no argument-injection templating beyond the free-text `Prompt` field and an
  `Argument hint` label (no `{{args}}`-style substitution documented).
- Source: https://zcode.z.ai/en/docs/commands

## 6. Hooks System — ❌ NOT SUPPORTED (for hand-authored hooks)

- No dedicated hooks/lifecycle-events documentation page exists for ZCode (the docs site lists
  Agent, Goal Mode, Remote Control, Task & File Management, Bot Channel, Edit History, Subagents,
  Skill, MCP Servers, Plugin, Command, Usage Stats — no "Hooks" entry).
- The **Plugin** system's capability list does mention "Hooks — automation triggered by specific
  events" as something a plugin **can** bundle, but there is **no published event taxonomy, file
  format, or schema** for a project to author its own hooks the way gald3r's `g-hk-*.ps1` files do.
  This mirrors the Mistral Vibe CLI precedent (`g-skl-platform-mistral`): a hook *concept* exists at
  the plugin-bundling level, but with no documented contract for hand-authored hooks — **do not
  fabricate a `hooks.json`/settings-driven hook file**.
- ZCode's closest analogs to hook-like automation are **Goal Mode** (session-objective tracking) and
  permission/confirmation gating (Safety Confirmation), neither of which is an event-hook bus.
- Source: absence confirmed against the full docs nav (https://zcode.z.ai/en/docs/welcome) and
  https://zcode.z.ai/en/docs/plugin.

## 7. Rules / Memory — ✅ NATIVE (flat, append-only)

- Persistent instructions are the two-scope `AGENTS.md` file described in §2: global
  `~/.zcode/AGENTS.md` appended by workspace-root `AGENTS.md`. There is **no** scoped/glob rule
  system (no `.mdc`-equivalent, no `alwaysApply`/`globs` frontmatter semantics) — everything is one
  flat instruction body per scope.
- gald3r `g-rl-*` rules must be **flattened/inlined** into the workspace `AGENTS.md` body; there is
  no import mechanism to pull in a separate rules directory the way Qwen/Gemini's `@AGENTS.md`
  overlay does.
- Source: https://zcode.z.ai/en/docs/agents

## 8. MCP Support — ✅ NATIVE

- MCP servers are configured via **Settings → MCP Servers**, either through a **Form mode** (name,
  command, args, env vars for stdio servers; URL + optional auth headers for HTTP/SSE) or a **Full
  configuration** mode accepting pasted JSON. Both `{"server-name": {...}}` and `{"mcpServers":
  {...}}` shapes are accepted.
- **Transports**: stdio (local command execution), HTTP, and SSE (remote).
- **Scopes**: User (global, all workspaces) and Workspace (current project only); imported/added
  servers are persisted to a `.zcode` configuration file at the chosen scope — the exact on-disk
  filename/path is not published in the docs.
- **One-click import** from other tools' existing MCP configs: Claude Code (`~/.claude/settings.json`),
  Codex CLI (`~/.codex/config.toml`), OpenCode, and a generic `~/.agents/mcp.json` — originals are
  left untouched.
- **First-party recommended servers**: `zai-mcp-server` (visual/image understanding),
  `web-search-prime` (real-time web search), `web-reader` (webpage parsing) — these require a Zhipu
  API token.
- Source: https://zcode.z.ai/en/docs/mcp-services

## 9. Plugin System — distribution channel

- A single **Plugin** can bundle: Skills, Commands, Subagents, MCP servers, Hooks, and Language
  servers. Installed via Settings → Plugins → Marketplace (built-in catalog, or a custom source —
  GitHub repo / Git URL / local path). Newly installed plugins are enabled by default.
- Built-in examples: `document-skills` (enabled by default), `skill-creator`, `android-emulator`,
  `ios-simulator`.
- This is the natural packaging channel for a future gald3r ZCode plugin bundle, but the docs do not
  publish a plugin manifest schema — treat as a distribution avenue, not a file-format target today.
- Source: https://zcode.z.ai/en/docs/plugin

---

## Known Gaps vs. Cursor Reference

| # | Gap | Severity |
|---|---|---|
| 1 | **No project-level agents** — subagents are Beta and global/user-level only (`~/.zcode/agents/`); gald3r's `g-agnt-*.md` roster has no per-project landing zone. (§3) | High |
| 2 | **No hand-authored hooks** — no published event taxonomy/schema; only plugin-bundled hooks are mentioned, with no user-authoring contract. gald3r `g-hk-*.ps1` have no verified wiring target. (§6) | High |
| 3 | **Flat AGENTS.md, no imports** — no `@file.md` import/include, no per-subdirectory scan; gald3r's `g-rl-*` rule set must be flattened into one workspace `AGENTS.md` body. (§2, §7) | Medium |
| 4 | **MCP config file location undocumented** — servers are UI-managed (Form or Full-config JSON) and persisted to an unspecified `.zcode` config path; no confirmed direct-file-write target for a gald3r installer. (§8) | Medium |
| 5 | **Commands have no argument templating** beyond a free-text `Argument hint` label — no `{{args}}`-style substitution documented. (§5) | Low |

**Strongest parity points** (not gaps): Skills (§4) are a drop-in match for gald3r's `SKILL.md`
convention, and Commands (§5) map cleanly to simple `@g-*` prompt files. MCP (§8) is fully native
with a documented import path from Claude Code/Codex/OpenCode configs.

## Hook System

- **Type**: not supported for hand-authored hooks ❌
- **Config file**: none published for user-authored hooks
- **Events available**: none documented (Plugin bundling can include "Hooks" but with no published
  event taxonomy)
- **Event payload format**: [STUB] — undocumented
- **gald3r hook files**: none verified — `g-hk-*.ps1` have no confirmed wiring target on ZCode

## Atypical Handling

- **Append-only two-scope `AGENTS.md`** (global then workspace) is the defining quirk — no
  hierarchical merge, no imports. Do not reuse the `@AGENTS.md`-overlay pattern used for
  Qwen/Gemini/Antigravity; inline gald3r's rule content directly.
- **Agents are Beta and global-only** — there is no project-level `agents/` folder to ship in a
  per-project overlay; document the manual `~/.zcode/agents/` step instead of fabricating one.
- **MCP is UI/settings-managed** — the exact on-disk config path is not published; Full-configuration
  JSON paste is the most portable installer target once the path is confirmed by hands-on testing.
- **No hooks surface** — do not fabricate a `hooks.json`/settings-driven hook file.

## gald3r Integration Notes

- Ship gald3r's rule content **inlined** into the workspace-root `AGENTS.md` (no `@import` support) —
  keep it lean since there is no glob-scoped loading to defer less-relevant rules.
- gald3r skills (`g-skl-*/SKILL.md`) load natively under `.zcode/skills/`; no adaptation needed.
- gald3r commands (`@g-*`) map to `.zcode/commands/<name>.md` (or `~/.zcode/commands/` for global
  scope) as simple prompt files.
- Do not ship a project-level `agents/` folder or a hooks config — neither has a project-scoped
  landing zone on ZCode today per the docs.
- Re-check on the next `@g-platform-scan-docs zcode` (crawl_max_age_days: 14) — ZCode is a brand-new
  2026 entrant and its docs are actively expanding (e.g. MCP config file path, project-level agents).

---

## Capability Summary (copy into PLATFORM_STATUS.md row)

| Hooks | Rules | Skills | Commands | MCP | Docs Fresh |
|---|---|---|---|---|---|
| ❌ | ✅ | ✅ | ✅ | ✅ | ✅ |

Legend: ✅ verified working · ⚠️ partial / Cursor-generic · ❌ not supported · ❓ untested.

- **Hooks ❌** — no published event taxonomy/schema for hand-authored hooks; only plugin-internal
  hook bundling is mentioned.
- **Rules ✅** — two-scope `AGENTS.md` (global `~/.zcode/AGENTS.md` appended by workspace
  `AGENTS.md`); flat, no imports, no per-directory scan.
- **Skills ✅** — native Agent Skills (`SKILL.md`, `name`/`description` frontmatter) in
  `.zcode/skills/`, agentskills.io-compatible.
- **Commands ✅** — native slash commands (`.md` prompt files) at User or Workspace scope, invoked
  `/name`.
- **MCP ✅** — native `mcpServers`/per-server JSON via Settings UI (Form or Full-config), stdio/
  HTTP/SSE, one-click import from Claude Code/Codex/OpenCode.
- **Docs Fresh ✅** — `last_doc_scan: 2026-07-03`.

(Agents are ⚠️ partial — Beta, global/user-level only — and are not one of the 5 summary columns
tracked in `PLATFORM_STATUS.md`, consistent with other specs.)

---

## Verification Evidence (docs crawl 2026-07-03, https://zcode.z.ai/en/docs/*)

| Capability | How verified |
|---|---|
| AGENTS.md two-scope append (not hierarchical, no imports) | /docs/agents — "reads a global ~/.zcode/AGENTS.md plus a workspace-root AGENTS.md, appending global then workspace"; "does not scan child directories, expand @import / @include, or choose rule files automatically by task type" |
| Skills (SKILL.md, `$name` invocation) | /docs/skill — `~/.zcode/skills/<name>/SKILL.md`, YAML `name`/`description` frontmatter, Settings → Skills, `$skill-name` chat invocation, import via symlink/copy |
| Commands (`.md`, `/name` invocation) | /docs/commands — `~/.zcode/commands` (User) or workspace dir; fields Scope/Name/Description/Argument hint/Prompt; built-ins `/goal`, `/compact`; import supported |
| Subagents (Beta, global-only) | /docs/subagents — `~/.zcode/agents/<name>.md`; "current Beta manages global / user-level subagents... Project or workspace-level subagents are not yet supported"; fields name/color/model/description/tools/system prompt; `@name` manual invocation |
| MCP (Form/Full-config, stdio/HTTP/SSE) | /docs/mcp-services — Settings → MCP Servers; Form mode vs Full-configuration JSON paste; `{"server-name":{...}}` or `{"mcpServers":{...}}`; stdio/HTTP/SSE; import from Claude Code/Codex/OpenCode/`~/.agents/mcp.json`; first-party `zai-mcp-server`/`web-search-prime`/`web-reader` |
| Plugin bundling (incl. Hooks mention, no schema) | /docs/plugin — "A single plugin can bundle several capabilities" incl. Skills/Commands/Subagents/MCP servers/Hooks/Language servers; Settings → Plugins → Marketplace; built-ins `document-skills`, `skill-creator`, `android-emulator`, `ios-simulator` |
| No dedicated hooks/lifecycle-events docs page | Full docs nav from /docs/welcome — Get Started / Core Features (Agent, Goal Mode, Remote Control, Task & File Management, Bot Channel, Edit History, Subagents, Skill, MCP Servers, Plugin, Command, Usage Stats) / Integration / Support — no "Hooks" entry |
| Product positioning / GLM-5.2 / BYOK | https://venturebeat.com/technology/z-ai-launches-zcode-to-challenge-cursor-claude-code-and-github-copilot-in-ai-coding — free cross-platform ADE around GLM-5.2, BYOK support, challenges Cursor/Claude Code/Copilot |
