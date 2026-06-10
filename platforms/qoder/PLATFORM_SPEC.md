---
subsystem_memberships: [PLATFORM_INTEGRATION]
platform: qoder
authoring_path: update
docs_url: https://docs.qoder.com
docs_url_secondary:
  - https://docs.qoder.com/user-guide/commands
  - https://docs.qoder.com/user-guide/rules
  - https://docs.qoder.com/extensions/subagent
  - https://docs.qoder.com/extensions/skills
  - https://docs.qoder.com/extensions/hooks
  - https://docs.qoder.com/user-guide/chat/model-context-protocol
crawl_max_age_days: 14
vault_doc_path: research/platforms/qoder/
last_doc_scan: 2026-06-02
reference: g-skl-platform-cursor
status: ✅
task: T1474
---

# PLATFORM_SPEC.md — Qoder (Alibaba agentic coding platform)

Qoder ships as a **standalone IDE** (macOS/Windows), a **JetBrains plugin**, a **CLI** (with a
Python + TypeScript SDK), and **Cloud Agents** (REST API). As of mid-2026 the platform natively
supports **all six** gald3r-relevant extension primitives — custom slash commands, rules/memory,
subagents (Custom Agents), Agent Skills, lifecycle hooks, and MCP. The docs have expanded well
beyond the Aug-2025 launch state: dedicated `/extensions/` pages now exist for **Skills**, **Hooks**,
and **Subagents** in addition to the previously-documented Rules, Commands, Memory, and MCP. The same
primitives are mirrored across the IDE/plugin, the CLI+SDK, and the Cloud Agents API.

**Authoring path**: UPDATE. **Verified 2026-06-02** against https://docs.qoder.com (see Verification
Evidence). This **supersedes** the prior spec, which incorrectly recorded **Skills = none** and
**Hooks = none** — both are now NATIVE per the current `/extensions/` docs.

> **Instruction-file convention:** Qoder's native instruction surface is **`.qoder/rules/`** (4 modes)
> plus a separate persistent **Memory** system. **`AGENTS.md` is explicitly supported** for cross-tool
> portability, but on conflict **`.qoder/rules` takes precedence**. Qoder does **not** read `CLAUDE.md`.

> **Surface split:** the full extensibility (commands/rules/agents/skills/hooks/MCP) lives in the
> **IDE + JetBrains plugin**; a **CLI+SDK** and a **Cloud Agents REST API** re-expose the same
> primitives for headless/scripted automation. Where a feature is surface-scoped it is noted inline.

---

## 1. Folder Hierarchy

```
<project-root>/
├── AGENTS.md                         ← instruction file Qoder reads (.qoder/rules wins on conflict)
└── .qoder/
    ├── rules/        *.md            ← Always Apply / Model Decision / Specific Files / Apply Manually
    ├── commands/     *.md            ← custom slash commands (invoke with /)
    ├── agents/       <name>.md       ← Custom Agents / subagents (markdown + YAML frontmatter)
    ├── skills/       <name>/SKILL.md ← Agent Skills (SKILL.md / agentskills.io standard)
    ├── settings.json                 ← hooks + MCP configuration
    └── settings.local.json           ← machine-local hook/MCP overrides (gitignored)
```

User-level (`~/.qoder/…`) and project-level (`<project>/.qoder/…`) variants exist for commands,
rules, agents, and skills. **Memory** is a separate UI/Knowledge-Center-managed persistent store
(global + project-specific), **not** a flat editable file.

**gald3r writes**: `.qoder/rules`, `.qoder/commands`, `.qoder/agents`, `.qoder/skills`, and the hook +
MCP blocks in `.qoder/settings.json`; `AGENTS.md` at root.
**Qoder owns**: the Memory store, the **Repo Wiki** / Knowledge Engine index, and **Quest Mode**
orchestration — Qoder-managed surfaces, not gald3r-writable files.

---

## 2. AI Instruction File

Qoder reads **`AGENTS.md`** (explicitly supported for cross-tool portability). The **primary native**
instruction surface is **`.qoder/rules/`** (4 modes), with a separate persistent **Memory** system
layered on top. On any conflict between `AGENTS.md` and a `.qoder/rules` entry, **`.qoder/rules`
takes precedence**. There is **no `CLAUDE.md` support** — gald3r's Claude-Code instruction file is
ignored on Qoder; ship `AGENTS.md` + `.qoder/rules/` instead.

---

## 3. Agents Support — ✅ NATIVE

- **Custom Agents (subagents)**: markdown + YAML frontmatter (`name`, `description`, `tools`,
  `skills`, `mcpServers`) plus a system prompt, at `~/.qoder/agents/<name>.md` and
  `${project}/.qoder/agents/<name>.md`. Each agent gets **its own independent context window, tool
  permissions, and system prompt**; invoked automatically or via `/<agent-name>`.
- Built-in modes: **Ask**, **Agent**, **Quest** (Code with Spec), plus **Cloud Agents**.
- gald3r `g-agnt-*` definitions map directly to Qoder Custom Agent files.
- Source: https://docs.qoder.com/extensions/subagent

## 4. Skills Support — ✅ NATIVE

- **Agent Skills**: each skill is a directory containing a **`SKILL.md`** at
  `.qoder/skills/{name}/SKILL.md` (user + project level). `SKILL.md` defines the skill's
  `description`, instructions, and optional auxiliary files. The model **auto-invokes** by
  description, or the user runs `/skill-name` manually. Create via the `/create-skill` assistant or
  the `npx skills add` CLI.
- gald3r `g-skl-*/SKILL.md` load natively.
- Source: https://docs.qoder.com/extensions/skills

## 5. Commands / Workflows — ✅ NATIVE

- **Custom Commands (slash commands)**: markdown at `.qoder/commands/*.md` (user-level
  `~/.qoder/commands/` and project-level `<project>/.qoder/commands/`). Encapsulate frequently-used
  prompts/workflows into reusable commands; invoked by typing **`/`** in the Agent dialog.
- gald3r `@g-*` / `/g-*` commands map directly.
- Source: https://docs.qoder.com/user-guide/commands

## 6. Hooks System — ✅ NATIVE

- **Lifecycle hooks** (Qoder IDE + JetBrains plugin) configured in JSON settings —
  `~/.qoder/settings.json`, `.qoder/settings.json`, `.qoder/settings.local.json`. **5 events**:
  **UserPromptSubmit**, **PreToolUse**, **PostToolUse**, **PostToolUseFailure**, **Stop**. Hooks run
  **shell scripts/commands**; event context arrives via **stdin JSON**; **exit 0 = allow, exit 2 =
  block**. "No source code changes required."
- gald3r `g-hk-*` hooks wire via these events (UserPromptSubmit/SessionStart-style context injection,
  PreToolUse `.gald3r/` guards, Stop summaries). **Caveat:** hooks run on shell-script commands —
  on Windows ship `.ps1`/`.cmd` invocations; PowerShell-specific support is not separately documented,
  so confirm the launcher per host.
- Source: https://docs.qoder.com/extensions/hooks

## 7. Rules / Memory — ✅ NATIVE

- `.qoder/rules/*.md` with **4 modes**: **Always Apply**, **Model Decision** (agent-requested),
  **Specific Files** (glob-scoped), and **Apply Manually** (`@rule`). Rule files live in the
  `.qoder/rules` directory and strategically inject predefined context into prompts. A separate
  persistent **Memory** system (global + project-specific) gradually builds a memory base about the
  developer, projects, and encountered issues. **`AGENTS.md`** is also honored (rules win on conflict).
- **Constraint:** rules are capped at **100,000 characters total** across active rule files, **natural
  language only** (no images/links inside rules).
- gald3r `g-rl-*` map to **Always Apply** (for `alwaysApply: true`) or **Model Decision** (for
  `description:`-scoped); per-file `globs:` map to **Specific Files**.
- Source: https://docs.qoder.com/user-guide/rules

## 8. MCP Support — ✅ NATIVE

- **MCP servers** via **Settings > MCP** (custom JSON server config) or the built-in **MCP Square**
  marketplace. **STDIO** (local) and **SSE** (remote) transports. Also exposed in the CLI and the
  Cloud Agents SDK. Add custom servers (name, transport, command/args or URL) or install from MCP
  Square.
- Source: https://docs.qoder.com/user-guide/chat/model-context-protocol

---

## Parity vs. Cursor Reference

Qoder reaches **full parity** with the Cursor reference (`g-skl-platform-cursor`): native
**commands, rules, agents, skills, hooks, and MCP**. Qoder-native bonuses with no Cursor analog:
**Quest Mode** (spec-driven autonomous long-running tasks), the **Repo Wiki** / **Knowledge Engine**
(auto-generated codebase docs + retrieval), **Cloud Agents** (REST CRUD + versioning for agents,
skills, and server-side memory-stores), **Deeplinks**, and team **OpenAPI** — these are
Qoder-managed surfaces, not gald3r-writable stores.

**Reuse note:** unlike Claude-compatible platforms, Qoder does **not** read `CLAUDE.md` and does not
auto-discover `.claude/` trees. The correct gald3r install ships the **`.qoder/`** tree
(rules/commands/agents/skills + `settings.json` hooks+MCP) plus **`AGENTS.md`** at root.

## Hook System

- **Type**: native (settings.json hooks; IDE + JetBrains plugin)
- **Config file**: `~/.qoder/settings.json`, `.qoder/settings.json`, `.qoder/settings.local.json`
- **Events available**: UserPromptSubmit, PreToolUse, PostToolUse, PostToolUseFailure, Stop
- **Event payload format**: JSON via stdin; control via exit codes (0 = allow, 2 = block)
- **Command extensions**: shell scripts/commands (ship `.ps1`/`.cmd` launchers on Windows; confirm
  per host — no PowerShell-specific guarantee is documented)
- **gald3r hook files**: `g-hk-*` wire via the events above

## Atypical Handling

- **Instruction file is `AGENTS.md`, not `CLAUDE.md`** — `.qoder/rules` wins on conflict. Memory is
  a UI-managed store, not a committed file, so gald3r's file-first "always-on rules" map onto
  **`.qoder/rules/` (Always Apply)**, with Memory as auxiliary.
- **Four surfaces**: IDE + JetBrains plugin (full extensibility), CLI+SDK, and Cloud Agents REST API.
- **Hooks are 5 distinct events** (note `PostToolUseFailure`, which most peers lack) and there is **no
  documented `SessionStart`/`SessionEnd`** — approximate session-start context injection via
  `UserPromptSubmit`.
- **Rule cap**: 100,000 chars total, natural-language-only.

## gald3r Integration Notes

- Ship the gald3r **`.qoder/`** tree (rules/commands/agents/skills + `settings.json` hooks+MCP) and
  **`AGENTS.md`** — Qoder does NOT load `.claude/`/`CLAUDE.md`.
- Map session-start context to a `UserPromptSubmit` hook (no `SessionStart` event documented).
- Keep the combined `.qoder/rules/*.md` under the 100k-char cap; strip images/links from rules.
- Re-verify on the next `@g-platform-scan-docs qoder` (crawl_max_age_days: 14).

---

## Capability Summary (copy into PLATFORM_STATUS.md row)

| Hooks | Rules | Skills | Commands | MCP | Docs Fresh |
|---|---|---|---|---|---|
| ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |

Legend: ✅ verified working · ⚠️ partial / Cursor-generic · ❌ not supported · ❓ untested.

---

## Verification Evidence (docs crawl 2026-06-02, https://docs.qoder.com)

| Capability | How verified |
|---|---|
| Commands | /user-guide/commands — `.qoder/commands/*.md` (user `~/.qoder/` + project); "type `/` in the Agent dialog to quickly invoke these commands" |
| Rules | /user-guide/rules — `.qoder/rules` dir, 4 modes (Always Apply / Model Decision / Specific Files / Apply Manually); `AGENTS.md` supported, rules win on conflict; separate Memory store; 100k-char cap |
| Agents | /extensions/subagent — Custom Agent `~/.qoder/agents/<name>.md` + project; md+YAML; own context window, tool permissions, system prompt |
| Skills | /extensions/skills — Agent Skills `.qoder/skills/{name}/SKILL.md`; model auto-invokes by description or `/skill-name`; `/create-skill` or `npx skills add` |
| Hooks | /extensions/hooks — IDE + JetBrains; `settings.json`; UserPromptSubmit/PreToolUse/PostToolUse/PostToolUseFailure/Stop; shell scripts; exit 0=allow, 2=block |
| MCP | /user-guide/chat/model-context-protocol — Settings > MCP custom JSON or MCP Square; STDIO + SSE; also CLI + Cloud Agents SDK |
| Instruction file | /user-guide/rules — `AGENTS.md` honored; `.qoder/rules` precedence; no `CLAUDE.md` support |
| Recency | Skills/Hooks/Subagent are new `/extensions/` pages absent at Aug-2025 launch; prior gald3r spec (Skills=none, Hooks=none) is contradicted by current docs |
