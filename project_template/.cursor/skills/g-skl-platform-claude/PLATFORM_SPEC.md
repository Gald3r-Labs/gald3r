---
subsystem_memberships: [PLATFORM_INTEGRATION]
platform: claude
authoring_path: update
docs_url: https://code.claude.com/docs/en/overview
docs_url_secondary:
  - https://code.claude.com/docs/en/memory
  - https://code.claude.com/docs/en/skills
  - https://code.claude.com/docs/en/sub-agents
  - https://code.claude.com/docs/en/hooks
  - https://code.claude.com/docs/en/mcp
  - https://code.claude.com/docs/en/plugins
  - https://code.claude.com/docs/en/agent-sdk/overview
crawl_max_age_days: 7
vault_doc_path: research/platforms/claude-code/
last_doc_scan: 2026-06-02
reference: g-skl-platform-cursor
status: ✅
task: T1474
---

# PLATFORM_SPEC.md — Claude Code (Anthropic)

**Claude Code** is Anthropic's agentic coding tool — the same engine across the Terminal CLI
(`claude`), VS Code, JetBrains, the Desktop app, Web (`claude.ai/code`), iOS, Slack (`@Claude`), and
Chrome. As of **June 2026** Claude Code natively supports **all six** gald3r-relevant extension
primitives — custom slash commands, rules/memory, subagents, Agent Skills, lifecycle hooks, and MCP —
plus Plugins, the Agent SDK, Routines (scheduling), and Channels. Every core mechanism is **NATIVE**;
there are **no gaps in the six core mechanisms**.

**Authoring path**: UPDATE. **Verified 2026-06-02** against https://code.claude.com/docs (see
Verification Evidence). This **supersedes** the prior spec (`last_doc_scan: never`, `status: ⚠️`),
which marked Hooks ⚠️ over a lowercase-`hooks.json` config-shape inconsistency and cited the retired
`docs.anthropic.com/en/docs/claude-code` URLs. Both issues are resolved here:

> **Docs moved:** the documentation relocated from `docs.anthropic.com/en/docs/claude-code` to
> **`code.claude.com/docs`** (301 redirect). All `source_url`s below use the new host.
>
> **Hook config corrected:** the canonical, supported hook surface is **`settings.json`** (key
> `"hooks"`) with **PascalCase** event names and a matcher-grouped shape — **not** a lowercase
> top-level `hooks.json`. gald3r hook wiring must target `settings.json`.

> **Platform truth — instruction file:** Claude Code reads **`CLAUDE.md`, NOT `AGENTS.md`**. If a
> repo already uses `AGENTS.md`, create a `CLAUDE.md` that imports it (`@AGENTS.md`) or symlink it;
> `/init` also reads an existing `AGENTS.md` and incorporates it. This is the one structural
> difference from `AGENTS.md`-native platforms (Amp, Aider, etc.) and is handled in gald3r by the
> `.claude/CLAUDE.md` → `@AGENTS.md` import the framework already ships.

---

## 1. Folder Hierarchy

```
<project-root>/
├── CLAUDE.md                     ← instruction file Claude reads (imports @AGENTS.md); also ./.claude/CLAUDE.md
├── CLAUDE.local.md               ← personal project-specific overrides (gitignored)
├── .mcp.json                     ← project-scoped MCP servers (committable, shareable)
└── .claude/
    ├── CLAUDE.md                 ← project, team-shared instructions (alt location)
    ├── settings.json             ← permissions, env, hooks, MCP (committable, official schema)
    ├── settings.local.json       ← user-local overrides (gitignored)
    ├── rules/        *.md         ← path-scoped modular rules (optional `paths:` glob frontmatter)
    ├── commands/     *.md         ← custom slash commands (legacy, still supported; merged into Skills)
    ├── agents/       *.md         ← subagents (markdown + YAML frontmatter)
    ├── skills/       <name>/SKILL.md  ← Agent Skills (agentskills.io standard); each = /<name>
    └── hooks/        *.ps1/.sh    ← hook scripts referenced from settings.json
```

Claude Code also reads a **user-global** tree at `~/.claude/` (`CLAUDE.md`, `settings.json`,
`agents/`, `skills/`, `commands/`) and **managed/enterprise policy** settings. Auto memory lives at
`~/.claude/projects/<project>/memory/MEMORY.md` (first 200 lines / 25 KB loaded each session).

**gald3r writes**: `.claude/CLAUDE.md` (+ root `CLAUDE.md` importing `@AGENTS.md`), `.claude/rules/`,
`.claude/commands/`, `.claude/agents/`, `.claude/skills/`, `.claude/hooks/`, and seeds
`.claude/settings.json` (`"hooks"` + `"mcpServers"`) / `.mcp.json`.
**Claude Code owns**: the `settings.json` schema, the auto-memory `MEMORY.md` store, and the
user-global `~/.claude/` tree (gald3r does not write the user-global tree).

---

## 2. AI Instruction File

Claude Code's instruction file is **`CLAUDE.md`** (project `./CLAUDE.md` or `./.claude/CLAUDE.md`,
team-shared; `~/.claude/CLAUDE.md` user-global; `./CLAUDE.local.md` personal/gitignored; managed
policy paths per OS). It loads at the start of **every** session as persistent context.

- **`AGENTS.md` is NOT read directly** — support is **partial via import only**. gald3r's
  `.claude/CLAUDE.md` does `@AGENTS.md`, making the shared cross-platform `AGENTS.md` first-class.
- **Import syntax**: `@path/to/import` (relative or absolute, **max depth 4 hops**).
- **Managed policy locations**: `/Library/Application Support/ClaudeCode/CLAUDE.md` (macOS),
  `/etc/claude-code/CLAUDE.md` (Linux/WSL), `C:\Program Files\ClaudeCode\CLAUDE.md` (Windows).
- Source: https://code.claude.com/docs/en/memory

---

## 3. Agents Support — ✅ NATIVE

- **Subagents**: specialized assistants, each in its own context window with a custom system prompt,
  specific tool access, and independent permissions. Markdown + YAML frontmatter (`name`,
  `description`, `tools`, `model`, …) in `./.claude/agents/<name>.md` (project) or
  `~/.claude/agents/<name>.md` (user); create manually or via `/agents`. Also bundleable via plugins.
- **Built-in subagents**: Explore (Haiku, read-only), Plan (read-only, plan mode), general-purpose
  (all tools). Subagents can carry their own hooks, skills, tool restrictions, permission modes, and
  persistent memory. Up to ~7 parallel agents; subagents cannot spawn other subagents. Separate
  features exist for background agents (agent-view) and agent teams.
- gald3r `g-agnt-*.md` map directly to `.claude/agents/` subagent files (auto-delegated when their
  `description` matches, or invoked via `@g-agnt-<name>`).
- Source: https://code.claude.com/docs/en/sub-agents

## 4. Skills Support — ✅ NATIVE

- **Agent Skills** (agentskills.io `SKILL.md` open standard): create a `SKILL.md` with instructions
  and Claude adds it to its toolkit. Used automatically when relevant, or invoked directly with
  `/skill-name`. **Progressive disclosure** — the body loads only when used.
- **Locations**: Personal `~/.claude/skills/<name>/SKILL.md`; Project `.claude/skills/<name>/SKILL.md`;
  Plugin `<plugin>/skills/<name>/SKILL.md`; Enterprise via managed settings. Frontmatter: `name`
  (optional — defaults to dir name), `description`.
- Claude Code **extends** the standard with invocation control (frontmatter), subagent execution, and
  dynamic context injection (`` !`cmd` `` inlines command output). Supporting files allowed in the
  skill dir; live change detection within a session.
- gald3r `g-skl-*/SKILL.md` load natively (folder-per-skill). `.claude/skills/` is also consumed by
  OpenCode and Copilot installs — keep content platform-neutral.
- Source: https://code.claude.com/docs/en/skills

## 5. Commands / Workflows — ✅ NATIVE

- **Custom slash commands** have been **merged into Skills**. A file at `.claude/commands/deploy.md`
  and a skill at `.claude/skills/deploy/SKILL.md` both create `/deploy` and work the same way.
  Existing `.claude/commands/*.md` files keep working (legacy, still supported).
- **File convention**: `.claude/commands/<name>.md` (legacy) **OR** `.claude/skills/<name>/SKILL.md`
  (current path; invoke via `/<name>`). Markdown body is the prompt; subdirectories namespace commands.
- gald3r `@g-*` / `/g-*` commands map directly.
- Source: https://code.claude.com/docs/en/skills

## 6. Hooks System — ✅ NATIVE

- **Lifecycle hooks** are user-defined **shell commands, HTTP endpoints, or LLM prompts** that execute
  automatically at specific points in Claude Code's lifecycle, giving **deterministic** control.
- **Config surface (canonical)**: `settings.json` under a `"hooks"` key — `~/.claude/settings.json`
  (user), `.claude/settings.json` (project, committable), `.claude/settings.local.json` (gitignored),
  managed policy settings, plugin `hooks/hooks.json`, or skill/agent frontmatter. Config uses
  **three-level nesting** (event → matcher → `hooks[]`).
- **Events** (PascalCase): `SessionStart`, `SessionEnd`, `Setup`, `UserPromptSubmit`,
  `UserPromptExpansion`, `Stop`, `StopFailure`, `PreToolUse`, `PostToolUse`, `PostToolUseFailure`,
  `PostToolBatch`, `PermissionRequest`, `PermissionDenied`, `SubagentStart`, `SubagentStop`,
  `TaskCreated`, `TaskCompleted`, `TeammateIdle`, `CwdChanged`, `FileChanged`, `ConfigChange`,
  `InstructionsLoaded`, `PreCompact`, `PostCompact`, `Elicitation`, `ElicitationResult`,
  `MessageDisplay`, `WorktreeCreate`, `WorktreeRemove`, `Notification`.
- **PreToolUse can block a tool call.** Covers session start, pre/post tool, pre-commit-style gating
  (via `PostToolUse`/`Stop`), and file-watch (`FileChanged`). `InstructionsLoaded` logs which
  instruction files loaded.
- **gald3r wiring**: `g-hk-*.ps1` invoked via `{ "type": "command", "command": "powershell.exe -File
  .claude/hooks/g-hk-...ps1" }` under the matching PascalCase event in `settings.json`. SessionStart
  context injection, `PreToolUse` `.gald3r/` guards, and `Stop`/`PostToolUse` gates all wire natively.
  **Migrate any legacy lowercase `hooks.json` entries (`sessionStart`/`stop`/`beforeShellExecution`)
  to PascalCase events in `settings.json`** — `beforeShellExecution` is a Cursor-era name with no
  Claude Code equivalent (use `PreToolUse` with a `Bash` matcher instead).
- Source: https://code.claude.com/docs/en/hooks

## 7. Rules / Memory — ✅ NATIVE

- **`CLAUDE.md`** persistent instructions (read at the start of every session) + **`.claude/rules/*.md`**
  path-scoped modular rules (scoped to file paths via a `paths:` YAML glob in frontmatter) + **auto
  memory** (`MEMORY.md`, accumulates learnings across sessions; first 200 lines / 25 KB loaded each
  session). gald3r rules are plain `.md` (NOT Cursor's `.mdc` — parity sync swaps the extension).
- **Enforcement caveat (platform truth):** `CLAUDE.md` / rules / memory are **context (advisory), not
  hard enforcement**. For guaranteed always-on framework constraints, gald3r should use a **`PreToolUse`
  hook** rather than relying on a rules file. Auto memory requires **v2.1.59+** (on by default).
- gald3r `g-rl-*` map to `CLAUDE.md` always-apply context (and optionally `.claude/rules/` with
  `paths:` scoping for path-specific rules).
- Source: https://code.claude.com/docs/en/memory

## 8. MCP Support — ✅ NATIVE

- **Model Context Protocol** client — connects to hundreds of external tools/data sources.
- **Config**: Project `.mcp.json` at project root (committable; `type` accepts the `streamable-http`
  alias); Local/User `~/.claude.json`; CLI `claude mcp add` / `add-json`. Scopes: local (default),
  project, user; plus plugin-provided and claude.ai connectors.
- **Transports**: `stdio`, `http` (streamable-http), `sse` (deprecated), `ws` (WebSocket).
- Supports OAuth 2.0 auth, env-var expansion in `.mcp.json`, dynamic headers (`headersHelper`), MCP
  resources via `@` mentions, MCP prompts as `/mcp__server__prompt` commands, elicitation,
  `list_changed` dynamic tool updates, auto-reconnect, and **MCP Tool Search** (deferred tool loading,
  default on). Claude Code can also run **as** an MCP server via `claude mcp serve`. Managed/enterprise
  control via `managed-mcp.json` (`allowedMcpServers`/`deniedMcpServers`).
- gald3r MCP servers wire via `.claude/settings.json` `"mcpServers"` or `.mcp.json` (e.g.
  `gald3r_docker` streamable-http + stdio tools).
- Source: https://code.claude.com/docs/en/mcp

## 9. Other Extensibility — distribution & surfaces

- **Plugins** (✅): bundle skills, agents, hooks (`hooks/hooks.json`), and MCP servers (`.mcp.json` or
  inline in `plugin.json`). Installable via `/plugin install` from marketplaces (e.g.
  `claude-plugins-official`). A skill folder with `.claude-plugin/plugin.json` loads as a plugin. **This
  is the natural distribution channel for a gald3r Claude Code plugin.**
  (https://code.claude.com/docs/en/plugins)
- **Agent SDK** (✅): TypeScript and Python SDKs to build custom agents powered by Claude Code's tools,
  with full control over orchestration, tool access, and permissions.
  (https://code.claude.com/docs/en/agent-sdk/overview)
- **Routines / scheduling** (✅): cron-scheduled runs on Anthropic-managed infra (also trigger on API
  calls or GitHub events; create via `/schedule`); Desktop scheduled tasks run locally; `/loop` repeats
  a prompt within a CLI session. (https://code.claude.com/docs/en/routines)
- **Channels** (✅): an MCP server declaring the `claude/channel` capability can push external events
  (Telegram, Discord, iMessage, webhooks, CI/monitoring) into a session.
  (https://code.claude.com/docs/en/channels)
- **CLI / CI** (✅): composable Unix-style CLI (headless `-p`/print, pipe input,
  `--append-system-prompt`, `--add-dir`, `--teleport`); GitHub Actions, GitLab CI/CD, GitHub Code
  Review. Same engine + CLAUDE.md + settings + MCP carry across Terminal, VS Code, JetBrains, Desktop,
  Web, iOS, Slack, and Chrome. (https://code.claude.com/docs/en/cli-reference)

---

## Parity vs. Cursor Reference

Claude Code reaches **full parity** with the Cursor reference (`g-skl-platform-cursor`): native
**commands, rules, agents, skills, hooks, and MCP**, with **no gaps in the six core mechanisms**.
**Strengths over Cursor**: first-class native subagents (§3) and native Agent Skills (§4) require no
shimming, and Plugins + Agent SDK + Routines + Channels extend well beyond the Cursor surface.

**Platform-specific truths to honor:**
- Instruction file is **`CLAUDE.md`, not `AGENTS.md`** — ship the `@AGENTS.md` import (or symlink).
- `CLAUDE.md` / rules / memory are **advisory context**, not hard enforcement — use a **`PreToolUse`
  hook** for guaranteed always-on constraints.
- Hook config lives in **`settings.json`** with **PascalCase** events — not a lowercase `hooks.json`.

## Hook System

- **Type**: native (`settings.json` `"hooks"` key)
- **Config file**: `.claude/settings.json` (project) / `~/.claude/settings.json` (user) /
  `.claude/settings.local.json` (gitignored); also plugin `hooks/hooks.json` + skill/agent frontmatter
- **Events available**: SessionStart, SessionEnd, Setup, UserPromptSubmit, UserPromptExpansion, Stop,
  StopFailure, PreToolUse, PostToolUse, PostToolUseFailure, PostToolBatch, PermissionRequest,
  PermissionDenied, SubagentStart, SubagentStop, TaskCreated, TaskCompleted, TeammateIdle, CwdChanged,
  FileChanged, ConfigChange, InstructionsLoaded, PreCompact, PostCompact, Elicitation,
  ElicitationResult, MessageDisplay, WorktreeCreate, WorktreeRemove, Notification
- **Event payload format**: JSON; three-level nesting (event → matcher → `hooks[]`), entries shaped
  `{ "type": "command", "command": "..." }` (also `http` / LLM-prompt hook types)
- **Blocking**: `PreToolUse` can block a tool call
- **gald3r hook files**: `g-hk-*.ps1` wire natively under the matching PascalCase event via
  `powershell.exe -File .claude/hooks/g-hk-*.ps1` (migrate legacy lowercase `hooks.json` entries here)

## Atypical Handling

- **Instruction file is `CLAUDE.md`, not `AGENTS.md`** — `AGENTS.md` is supported only via `@AGENTS.md`
  import or symlink (and `/init` ingestion). The one structural difference vs. AGENTS.md-native tools.
- **Hooks live in `settings.json` (PascalCase events)**, not a lowercase top-level `hooks.json`. The
  prior gald3r `hooks.json` (`sessionStart`/`stop`/`beforeShellExecution`, flat shape) is legacy —
  `beforeShellExecution` has no Claude Code equivalent (use `PreToolUse` + `Bash` matcher).
- **Commands merged into Skills** — `/<name>` resolves from either `.claude/commands/<name>.md` or
  `.claude/skills/<name>/SKILL.md`.
- **Rules/memory are advisory** — for hard enforcement use a `PreToolUse` hook, not a rules file.
- Rules are plain `.md` (NOT `.mdc`).

## gald3r Integration Notes

- Ship `.claude/CLAUDE.md` importing `@AGENTS.md`; gald3r's `.claude/` tree (commands/skills/agents/
  hooks/rules) loads natively. Or package a Claude-Code-format **plugin bundle** and publish via a
  marketplace (`/plugin install`).
- Wire hooks under **`settings.json` `"hooks"`** with PascalCase events; reserve `PreToolUse` for the
  `.gald3r/` agent-required guard and any hard-enforcement constraint that a rules file cannot guarantee.
- Re-verify on the next `@g-platform-scan-docs claude` (crawl_max_age_days: 7); watch the
  `docs.anthropic.com` → `code.claude.com` redirect and the hook-config-in-`settings.json` history.

---

## Capability Summary (copy into PLATFORM_STATUS.md row)

| Hooks | Rules | Skills | Commands | MCP | Docs Fresh |
|---|---|---|---|---|---|
| ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |

Legend: ✅ verified working · ⚠️ partial / Cursor-generic · ❌ not supported · ❓ untested.

---

## Verification Evidence (docs crawl 2026-06-02, https://code.claude.com/docs)

| Capability | How verified |
|---|---|
| Instruction file | /en/memory — reads `CLAUDE.md` (root or `.claude/`), not `AGENTS.md`; `@path` imports (max depth 4); `AGENTS.md` only via `@AGENTS.md`/symlink/`/init` |
| Commands | /en/skills — `.claude/commands/<name>.md` (legacy) OR `.claude/skills/<name>/SKILL.md` → `/<name>`; commands merged into Skills |
| Rules / Memory | /en/memory — `CLAUDE.md` + `.claude/rules/*.md` (`paths:` glob) + auto memory `MEMORY.md` (v2.1.59+); advisory, not enforcement |
| Agents | /en/sub-agents — `.claude/agents/<name>.md` (md+YAML); built-in Explore/Plan/general-purpose; ~7 parallel; own hooks/skills/memory |
| Skills | /en/skills — agentskills.io `SKILL.md` in `~/.claude` / `.claude` / plugin skills dirs; progressive disclosure; `` !`cmd` `` injection |
| Hooks | /en/hooks — `settings.json` `"hooks"` (PascalCase events, event→matcher→hooks[]); shell/HTTP/LLM; `PreToolUse` blocks; NOT lowercase `hooks.json` |
| MCP | /en/mcp — `.mcp.json` + `~/.claude.json` + `claude mcp add`; stdio/http/sse/ws; OAuth, Tool Search, `claude mcp serve` |
| Plugins | /en/plugins — bundle skills+agents+hooks+MCP; `/plugin install` from marketplaces; `.claude-plugin/plugin.json` |
| Agent SDK / Routines / Channels | /en/agent-sdk, /en/routines, /en/channels — TS+Python SDK; cron via `/schedule`; `claude/channel` event push |
| Docs host | /en/overview — docs moved `docs.anthropic.com/en/docs/claude-code` → `code.claude.com/docs` (301); assessment current June 2026 |
