---
subsystem_memberships: [PLATFORM_INTEGRATION]
platform: hermes
authoring_path: update
docs_url: https://hermes-agent.nousresearch.com/docs/
docs_url_secondary:
  - https://hermes-agent.nousresearch.com/docs/user-guide/features/skills
  - https://hermes-agent.nousresearch.com/docs/user-guide/features/hooks
  - https://hermes-agent.nousresearch.com/docs/user-guide/features/overview
  - https://hermes-agent.nousresearch.com/docs/user-guide/configuration
  - https://hermes-agent.nousresearch.com/docs/reference/cli-commands
crawl_max_age_days: 14
vault_doc_path: research/platforms/hermes/
last_doc_scan: 2026-06-02
reference: g-skl-platform-cursor
status: ✅
task: T1474
---

# PLATFORM_SPEC.md — Hermes Agent (Nous Research)

Hermes Agent is a **self-improving CLI/TUI coding agent** from Nous Research, built around a
**closed learning loop**: the agent autonomously authors its own skills from experience (the
`skill_manage` tool) rather than relying solely on static, human-written rules. As of mid-2026
Hermes natively supports **all six** gald3r-relevant extension primitives — slash commands,
rules/memory, subagents, Agent Skills, event hooks, and MCP. Critically for gald3r, Hermes
**auto-discovers and reads `AGENTS.md` *and* `CLAUDE.md`** (alongside its own `.hermes.md` /
`SOUL.md`), so gald3r's standard instruction file is honored **without translation**.

**Authoring path**: UPDATE. **Verified 2026-06-02** against
https://hermes-agent.nousresearch.com/docs/ (see Verification Evidence). The Hooks event system
was completed by **v0.5.0** — `pre_llm_call` / `post_llm_call` / `on_session_start` /
`on_session_end` plus gateway+plugin hooks are recent additions; this spec reflects the current
(June 2026) docs.

> **Native skill format:** Hermes Skills are SKILL.md folders following the **agentskills.io** open
> standard — the **same format gald3r already ships**. gald3r `g-skl-*/SKILL.md` therefore load
> natively. The home-rooted skill tree (`~/.hermes/skills/`) is the canonical install location.

---

## 1. Folder Hierarchy

```
~/.hermes/                              ← global Hermes config root
├── config.yaml                         ← hooks, quick_commands, mcp_servers, agent limits, skills.config
├── shell-hooks-allowlist.json          ← persisted TTY consent for shell hooks
└── skills/                             ← Agent Skills (agentskills.io standard)
    └── <category>/<name>/SKILL.md       ← one folder per skill (often nested by category)
        ├── references/  templates/  scripts/  assets/   ← optional progressive-disclosure dirs

<project-root>/
├── .hermes.md                          ← native project instruction file
├── SOUL.md                             ← identity file (top of system prompt)
├── AGENTS.md / CLAUDE.md               ← auto-read as context files (Claude/agents compatible)
└── .cursorrules                        ← also auto-read as a context file
```

Global config and the skill library live under **`~/.hermes/`**, not in the repo. Hermes
auto-discovers project instruction files (`.hermes.md`, `AGENTS.md`, `CLAUDE.md`, `SOUL.md`,
`.cursorrules`) from the workspace.

**gald3r writes**: `~/.hermes/skills/<…>/SKILL.md` (skills) + project `AGENTS.md` / `CLAUDE.md`
(instructions); hooks/MCP/quick_commands declared in `~/.hermes/config.yaml`.
**Hermes owns**: the `~/.hermes/` namespace, `config.yaml` schema, the built-in Memory store
(`MEMORY.md` / `USER.md`, FTS5-indexed), the toolset registry (60+ built-in tools), and the
self-improvement loop (`skill_manage`, `hermes curator`).

---

## 2. AI Instruction File

Hermes uses **multi-format auto-discovery**. Native files are **`.hermes.md`** and **`SOUL.md`**
(SOUL.md is "the primary identity file — the first thing in the system prompt"). In addition,
Hermes auto-reads **`AGENTS.md`**, **`CLAUDE.md`**, and **`.cursorrules`** as context files. No
dedicated `HERMES.md` is required — gald3r's `AGENTS.md` / `CLAUDE.md` are **first-class inputs**
and are honored without any Hermes-specific port.

> **Reads CLAUDE.md *and* AGENTS.md** (unlike platforms that read only one). gald3r's standard
> instruction file drops in directly.

---

## 3. Agents Support — ✅ NATIVE

- **Subagent delegation** via the **`delegate_task`** tool: spawns child agent instances with
  **isolated contexts and restricted toolsets**. Concurrency/depth controlled in `config.yaml`:
  `max_concurrent_children: 3` (parallel children per batch; floor 1, no ceiling),
  `max_spawn_depth: 1` (delegation-tree depth cap, clamped 1–3). The **`subagent_stop`** hook
  fires on child completion. Swappable **`/personality`** presets per session.
- gald3r `g-agnt-*` roles map to Hermes delegated subagents (isolated-context tasks).
- Source: https://hermes-agent.nousresearch.com/docs/user-guide/configuration

## 4. Skills Support — ✅ NATIVE

- **Skills System** — `SKILL.md` folders with YAML frontmatter, one folder per skill under
  **`~/.hermes/skills/`** (often nested under category dirs), with optional
  `references/` `templates/` `scripts/` `assets/` subdirs. Follows the **progressive-disclosure /
  agentskills.io** open standard.
- **Agent-authored** (procedural memory): the agent creates/updates/deletes its own skills via the
  **`skill_manage`** tool — the core of Hermes's closed learning loop. Public **Skills Hub** has
  600+ skills across registries; `external_dirs` in `config.yaml` lets teams share skill libraries;
  `skills.config` stores per-skill settings.
- gald3r `g-skl-*/SKILL.md` load natively — **same format**, drop into `~/.hermes/skills/`.
- Source: https://hermes-agent.nousresearch.com/docs/user-guide/features/skills

## 5. Commands / Workflows — ✅ NATIVE

- **Slash commands** (in-session): `/model`, `/stop`, `/skills`, `/kanban`, `/bundles`,
  `/personality`, etc. (Slash Commands Reference).
- **Bundles**: `hermes bundles` groups multiple skills under a single **`/<bundle-name>`** command
  — a useful packaging primitive for shipping a set of gald3r skills behind one command.
- **quick_commands**: `config.yaml` block supporting `type: exec` and `type: alias` shortcuts.
- Plugins can register slash commands and extend the TUI.
- gald3r `@g-*` / `/g-*` commands map to slash commands / bundles.
- Source: https://hermes-agent.nousresearch.com/docs/reference/cli-commands

## 6. Hooks System — ✅ NATIVE

- **Event Hooks** — shell-script hooks declared in **`~/.hermes/config.yaml`** under `hooks:`
  (plus plugin hooks registered via `ctx.register_hook()`); managed by **`hermes hooks`**
  (`list` / `test` / `revoke` / `doctor`).
- **Valid events (11)**: `pre_tool_call`, `post_tool_call`, `pre_llm_call`, `post_llm_call`,
  `pre_api_request`, `post_api_request`, `on_session_start`, `on_session_end`,
  `on_session_finalize`, `on_session_reset`, `subagent_stop`.
- Each hook: `event_name`, optional `matcher` (for `pre/post_tool_call`), **required `command`**,
  `timeout` (default 60s, cap 300). `pre_llm_call` can **inject context** (git status, retrieved
  docs) into the next turn — a natural fit for gald3r session-start `.gald3r/` context injection.
- **Consent model**: first-use TTY consent persisted to `~/.hermes/shell-hooks-allowlist.json`;
  non-interactive runs need `--accept-hooks` / `HERMES_ACCEPT_HOOKS=1` / `hooks_auto_accept`.
- **Shell-command hooks** (not OS-locked): gald3r `g-hk-*.ps1` wire as the hook `command` on
  Windows; POSIX hosts use `.sh`. `on_session_start` context injection + `pre_tool_call` guards +
  `subagent_stop` map to the gald3r hook set.
- Source: https://hermes-agent.nousresearch.com/docs/user-guide/features/hooks

## 7. Rules / Memory — ✅ NATIVE

- **Context Files** (auto-discovered): `.hermes.md`, `AGENTS.md`, `CLAUDE.md`, `SOUL.md`,
  `.cursorrules`. **SOUL.md** is the primary identity file (top of system prompt).
- **Built-in Memory**: `MEMORY.md` / `USER.md` files with cross-session recall (FTS5 indexing).
  `hermes memory` configures **external providers** (`honcho`, `mem0`, `openviking`).
- gald3r rule content rides in `AGENTS.md` / `CLAUDE.md` (both read); persistent project facts can
  also live in the Memory store.
- Source: https://hermes-agent.nousresearch.com/docs/user-guide/features/overview

## 8. MCP Support — ✅ NATIVE

- **Native MCP client** with **stdio + HTTP** transports; selective tool loading with utility
  policies; **sampling** (server-initiated LLM requests); auto-reload when `mcp_servers` config
  changes. MCP servers are exposed as standalone **toolsets** (the unit plugins/servers plug into).
- CLI: `hermes mcp add/remove/list/test/configure/install/picker/catalog`. Hermes can also **act as
  an MCP server** via `hermes mcp serve`. Config under `mcp_servers` in `config.yaml`.
- Source: https://hermes-agent.nousresearch.com/docs/reference/cli-commands

## 9. Plugins / Distribution — distribution channel

- **Plugin system** with three categories: **general plugins** (tools/hooks), **memory providers**,
  and **context engines**; managed via **`hermes plugins`**. Plugins register slash commands, hooks
  (`ctx.register_hook()`), and toolsets.
- **`hermes curator`** runs automated review cycles over agent-created skills
  (`status` / `run` / `backup` / `rollback` / `pause` / `pin` / `archive`) — directly relevant to
  gald3r **skill-library hygiene**.
- **`hermes bundles`** packages a set of gald3r skills behind a single slash command.
- **Output / automation**: **gateway mode + cron** support non-interactive runs — relevant to
  gald3r scheduled / headless workflows.
- Source: https://hermes-agent.nousresearch.com/docs/user-guide/features/overview

---

## Parity vs. Cursor Reference

Hermes reaches **full parity** with the Cursor reference (`g-skl-platform-cursor`): native
**commands, rules, agents, skills, hooks, and MCP**. Distinguishing Hermes traits with no Cursor
analog: the **self-improving closed learning loop** (agent authors its own skills via
`skill_manage`, curated by `hermes curator`), built-in **FTS5 Memory** with pluggable external
providers, and **Hermes-as-MCP-server** (`hermes mcp serve`).

**Reuse note (important):** because Hermes reads **both `AGENTS.md` and `CLAUDE.md`** and consumes
**agentskills.io `SKILL.md`** natively, gald3r's instruction file and `g-skl-*` skill folders are
**directly reusable on Hermes without a separate port**. The cheapest high-parity install is to
drop gald3r's `g-skl-*/SKILL.md` tree into `~/.hermes/skills/` and keep `AGENTS.md` in the repo.

## Hook System

- **Type**: native (config.yaml shell hooks + plugin `ctx.register_hook()`)
- **Config file**: `~/.hermes/config.yaml` (`hooks:` block); managed via `hermes hooks`
- **Events available**: pre_tool_call, post_tool_call, pre_llm_call, post_llm_call,
  pre_api_request, post_api_request, on_session_start, on_session_end, on_session_finalize,
  on_session_reset, subagent_stop (11 total)
- **Hook fields**: `event_name`, optional `matcher`, required `command`, `timeout` (default 60s, cap 300)
- **Consent**: first-use TTY consent → `~/.hermes/shell-hooks-allowlist.json`; non-interactive via
  `--accept-hooks` / `HERMES_ACCEPT_HOOKS=1` / `hooks_auto_accept`
- **gald3r hook files**: `g-hk-*.ps1` wire as the hook `command` (Windows); `pre_llm_call` /
  `on_session_start` inject `.gald3r/` context; `pre_tool_call` guards `.gald3r/`

## Atypical Handling

- **Home-rooted config**: global state lives at `~/.hermes/` (`config.yaml`, `skills/`,
  `shell-hooks-allowlist.json`) — not in the repo. Skills install to `~/.hermes/skills/`, not a
  project `.hermes/` dir.
- **Self-improving loop**: Hermes autonomously authors/updates skills (`skill_manage`) and curates
  them (`hermes curator`) — differs from purely static rule-based extensibility. gald3r should
  treat its shipped skills as the seed library and let `hermes curator` manage hygiene.
- **Dual instruction read**: reads both `AGENTS.md` *and* `CLAUDE.md` (plus `.hermes.md`/`SOUL.md`)
  — no single-file translation needed.
- **Hook consent**: shell hooks require one-time TTY approval; headless/cron runs must pass
  `--accept-hooks` / `HERMES_ACCEPT_HOOKS=1`.

## gald3r Integration Notes

- Drop gald3r's `g-skl-*/SKILL.md` tree into `~/.hermes/skills/` — agentskills.io format loads
  natively. Keep `AGENTS.md` (and/or `CLAUDE.md`) in the repo for instructions.
- Declare gald3r hooks in `~/.hermes/config.yaml` (`g-hk-*.ps1` as `command`); use
  `on_session_start` / `pre_llm_call` for `.gald3r/` context injection. Pre-approve for headless.
- Package gald3r skill sets behind a single `/<bundle-name>` via `hermes bundles`; use
  `hermes curator` for library hygiene; `gateway mode + cron` for scheduled gald3r runs.
- Re-verify on the next `@g-platform-scan-docs hermes` (crawl_max_age_days: 14).

---

## Capability Summary (copy into PLATFORM_STATUS.md row)

| Hooks | Rules | Skills | Commands | MCP | Docs Fresh |
|---|---|---|---|---|---|
| ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |

Legend: ✅ verified working · ⚠️ partial / Cursor-generic · ❌ not supported · ❓ untested.

---

## Verification Evidence (docs crawl 2026-06-02, https://hermes-agent.nousresearch.com/docs/)

| Capability | How verified |
|---|---|
| Commands | /reference/cli-commands — slash commands (/model, /stop, /skills, /kanban, /bundles); `hermes bundles` → `/<bundle-name>`; `config.yaml` quick_commands (exec/alias) |
| Rules | /user-guide/features/overview — auto-reads `.hermes.md`/`SOUL.md` + `AGENTS.md` + `CLAUDE.md` + `.cursorrules`; built-in Memory `MEMORY.md`/`USER.md` (FTS5); external providers via `hermes memory` |
| Agents | /user-guide/configuration — `delegate_task` (isolated context, restricted toolset); `max_concurrent_children: 3`, `max_spawn_depth: 1`; `subagent_stop` hook; `/personality` presets |
| Skills | /user-guide/features/skills — agentskills.io `SKILL.md` under `~/.hermes/skills/`; agent-authored via `skill_manage`; Skills Hub (600+); `external_dirs` + `skills.config` |
| Hooks | /user-guide/features/hooks — `config.yaml` `hooks:` + plugin `ctx.register_hook()`; 11 events; `command`+`timeout` (60s/cap 300); TTY allowlist → `~/.hermes/shell-hooks-allowlist.json`; `hermes hooks` |
| MCP | /reference/cli-commands — native client (stdio+HTTP), sampling, auto-reload; `hermes mcp add/remove/list/test/configure/install/picker/catalog`; `hermes mcp serve` (Hermes as MCP server) |
| Plugins | /user-guide/features/overview — `hermes plugins` (general/memory/context-engine); `hermes curator` skill-review cycles; gateway mode + cron for non-interactive runs |
| Cross-compat | Hermes reads `AGENTS.md` + `CLAUDE.md` and consumes agentskills.io `SKILL.md` → gald3r instruction file + `g-skl-*` skills reusable |
