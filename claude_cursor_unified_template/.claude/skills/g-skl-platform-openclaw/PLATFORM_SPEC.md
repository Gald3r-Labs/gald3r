---
subsystem_memberships: [PLATFORM_INTEGRATION]
platform: openclaw
authoring_path: update
docs_url: https://docs.openclaw.ai
docs_url_secondary:
  - https://docs.openclaw.ai/concepts/agent-workspace
  - https://docs.openclaw.ai/tools/slash-commands
  - https://docs.openclaw.ai/tools/skills
  - https://docs.openclaw.ai/tools/subagents
  - https://docs.openclaw.ai/automation/hooks
  - https://docs.openclaw.ai/cli/mcp
crawl_max_age_days: 14
vault_doc_path: research/platforms/openclaw/
last_doc_scan: 2026-06-02
reference: g-skl-platform-cursor
status: ✅
task: T1479
---

# PLATFORM_SPEC.md — OpenClaw (self-hosted AI agent gateway)

OpenClaw is an **open-source, self-hosted AI agent gateway** oriented around chat channels
(Discord / Telegram / Slack / WhatsApp). Despite a sparse landing page, the official docs document a
**deep, file-based extensibility surface**: as of mid-2026 OpenClaw natively supports **all six**
gald3r-relevant extension primitives — slash commands, rules/memory, sub-agents, Agent Skills,
lifecycle hooks, and MCP (client **and** server). Critically for gald3r, OpenClaw's instruction-file
convention is **`AGENTS.md` + `SOUL.md`** (it does **not** read `CLAUDE.md`), and its hook handlers
are **TypeScript** (`HOOK.md` + `handler.ts`), so gald3r's PowerShell `g-hk-*.ps1` hooks are **not
drop-in portable** even though the hook mechanism itself is native.

**Authoring path**: UPDATE. **Verified 2026-06-02** against https://docs.openclaw.ai (see
Verification Evidence). This **supersedes** the prior spec (`last_doc_scan: never` / `status: ⚠️`)
which marked hooks/skills/commands/MCP as merely ⚠️ partial and rules as ❌ — the 2026-06-02 crawl
confirms all five mechanisms plus sub-agents are **NATIVE**. The honest residual caveats (TypeScript
hook handlers, workspace-relative install path, depth-limited sub-agents, prose-only rules) are
documented inline.

> **Surface split:** OpenClaw is a **single runtime** (the gateway), not an IDE/CLI pair. The full
> extensibility (commands/rules/agents/skills/hooks/MCP) lives in the gateway and its file-based
> agent **workspace** (default `~/.openclaw/workspace`); config lives at `~/.openclaw/openclaw.json`.
> Where a feature is workspace-path-dependent or has a TypeScript-only caveat it is noted inline.

---

## 1. Folder Hierarchy

```
~/.openclaw/
├── openclaw.json                  ← primary config (mcp.servers, bindings, model registry, hooks)
└── workspace/                     ← agent workspace (default; per-persona scope)
    ├── AGENTS.md                  ← primary operating contract (loaded every session)
    ├── SOUL.md                    ← persona / voice / hard "never do X" rules
    ├── TOOLS.md / IDENTITY.md / USER.md / HEARTBEAT.md / MEMORY.md   ← workspace files (all load)
    ├── memory/   YYYY-MM-DD-HHMM.md  ← auto-written by session-memory hook on /new, /reset
    ├── skills/   <name>/SKILL.md  ← Agent Skills (YAML frontmatter + markdown body)
    └── hooks/    <name>/HOOK.md + handler.ts   ← event-driven TypeScript hooks
```

Skills are resolved by **precedence** across multiple sources — workspace, `.agents/skills`,
`~/.agents/skills`, `~/.openclaw/skills`, bundled, and plugin sources — and the **highest source
wins** on a name collision. Starter `AGENTS.md`, `SOUL.md`, `TOOLS.md`, `IDENTITY.md`, `USER.md`,
`HEARTBEAT.md` are created automatically on first run.

**gald3r writes**: `skills/<name>/SKILL.md` (folder-per-skill — matches gald3r exactly), plus
`AGENTS.md` / `SOUL.md` prose for rules. **OpenClaw owns**: the `openclaw.json` schema
(`mcp.servers`, `bindings`, `hooks`), the workspace directory contract, and the hook handler runtime
(TypeScript).

> **Correction vs. prior spec:** OpenClaw's canonical surface is the per-user
> `~/.openclaw/workspace/`, **not** the project repo root. gald3r skills are reachable either by
> pointing the workspace at the repo or by installing them into `~/.openclaw/workspace/skills/`.
> There is no documented project-local `.openclaw/` override.

---

## 2. AI Instruction File

OpenClaw's instruction-file convention is **`AGENTS.md` (primary operating contract) + `SOUL.md`
(persona + hard rules)**. `AGENTS.md` is **loaded at the start of every session** and injected
directly into the agent context on the first turn of a new session. `SOUL.md`, `USER.md`,
`IDENTITY.md`, `TOOLS.md`, `HEARTBEAT.md`, and `MEMORY.md` **all load every time** as well.

> **Instruction-file truth (differs from Claude Code):** OpenClaw reads **`AGENTS.md`**, not
> `CLAUDE.md`. gald3r's `AGENTS.md` is a first-class input; ship gald3r rule prose into `AGENTS.md`
> (operating rules) and `SOUL.md` (hard "never do X" guardrails). No `OPENCLAW.md` exists. Do not
> confuse `SOUL.md` with `AGENTS.md` — OpenClaw reads both, for different purposes.

- Source: https://docs.openclaw.ai/concepts/agent-workspace

---

## 3. Agents Support — ✅ NATIVE

- **Two layers.** (1) **Multi-agent routing** via `bindings` mapping channel accounts to isolated
  per-persona agents — each agent is the full per-persona scope (workspace files, auth profiles,
  model registry, session store). (2) **Sub-agents** spawned at runtime via the **`sessions_spawn`
  tool** — background agent runs in their own session (`agent:<agentId>:subagent:<uuid>`).
- `sessions_spawn` is **non-blocking** (returns a run id immediately). Sub-agents run under
  **restricted tool policies** (no message/session/system tools by default) and are **depth-limited**
  via `maxSpawnDepth` (default **1**). The `/subagents` slash command is **inspection / listing
  only**, not the spawn mechanism.
- gald3r `g-agnt-*` roles map to per-persona agents (`bindings`) or to runtime `sessions_spawn` runs.
- Source: https://docs.openclaw.ai/tools/subagents

## 4. Skills Support — ✅ NATIVE

- **Agent Skills**: a directory containing `SKILL.md` (YAML frontmatter + markdown body). Minimum
  frontmatter: `name` + `description`. Additional keys: `user-invocable`, `disable-model-invocation`,
  `command-dispatch`, `command-tool`, and `metadata.openclaw` (gating). Discovered by **precedence**
  across workspace / `.agents/skills` / `~/.agents/skills` / `~/.openclaw/skills` / bundled / plugin —
  highest source wins on a name collision.
- **Skills double as slash commands** (see §5): a `user-invocable: true` skill is exposed as
  `/skill <name>`.
- gald3r `g-skl-*/SKILL.md` load natively — the folder-per-skill layout is identical. (Install path
  is the OpenClaw **workspace** `skills/` dir, not the repo root automatically.)
- Source: https://docs.openclaw.ai/tools/skills

## 5. Commands / Workflows — ✅ NATIVE

- **Slash commands** come from user-invocable **Skills** (`user-invocable: true`): the generic
  `/skill <name> [input]` entrypoint **always works**; a skill may also register as a **direct
  command** (e.g. `/prose`) via `command-dispatch` / `registerCommand()`. Built-ins come from the
  core registry, generated dock commands, and plugin `registerCommand()` calls — including **native
  registration to Discord/Telegram** interfaces (noted around **v2026.2.23**).
- **Inline built-in directives** (`/think`, `/fast`, `/verbose`, `/trace`, `/reasoning`, `/elevated`,
  `/exec`, `/model`, `/queue`, plus `/help`, `/commands`, `/status`, `/whoami`) are **stripped before
  the model sees the remaining text**.
- gald3r `@g-*` / `/g-*` commands map to user-invocable skills (each becomes `/skill <name>`).
- **Workflows (Lobster):** OpenClaw lists "Skills, plugins, and workflow **pipelines (Lobster)**" as
  a first-class multi-step orchestration layer — adoptable for gald3r `g-go`-style pipelines.
- Source: https://docs.openclaw.ai/tools/slash-commands

## 6. Hooks System — ✅ NATIVE (TypeScript handlers)

- **Event-driven hooks**: a directory with **`HOOK.md`** (YAML frontmatter declaring
  `metadata.openclaw.events`) + **`handler.ts`** (an **async TypeScript** handler). Hooks are for
  operator-managed side effects and command/lifecycle automation.
- **Event taxonomy** (OpenClaw-specific, broad): `command:new` / `command:reset` / `command:stop`,
  `session:compact:before` / `session:compact:after`, `agent:bootstrap`,
  `gateway:startup` / `gateway:shutdown` / `gateway:pre-restart`,
  `message:received` / `message:transcribed` / `message:preprocessed` / `message:sent`.
- **Built-ins**: `session-memory`, `command-logger`, `compaction-notifier`, `bootstrap-extra-files`,
  `boot-md` (runs `BOOT.md` when the gateway starts).
- **gald3r caveat (honest):** the mechanism is native, but handlers are **TypeScript** (`handler.ts`),
  and the event names differ from gald3r's (`gateway:startup` / `agent:bootstrap` / `command:new` vs
  gald3r `SessionStart` / `Stop` / `PreToolUse`). gald3r's PowerShell `g-hk-*.ps1` hooks are therefore
  **not drop-in portable** — they must be re-expressed as `handler.ts` (or invoked as a child process
  from one), and the gald3r event→hook mapping for OpenClaw is **[STUB] / unverified**. Do not
  fabricate an event-to-hook mapping.
- Source: https://docs.openclaw.ai/automation/hooks

## 7. Rules / Memory — ✅ NATIVE

- **Instruction/memory files** are the rules mechanism: `AGENTS.md` (operating rules) + `SOUL.md`
  (persona + hard "never do X" rules) + `MEMORY.md`, all **injected into agent context every
  session**. Explicit "never do X" rules in `SOUL.md` are described as a **last line of defense
  against prompt injection**.
- **Memory automation**: the built-in `session-memory` hook **auto-extracts the last 15 messages** to
  `<workspace>/memory/YYYY-MM-DD-HHMM.md` on `/new` and `/reset` — a ready-made persistence pattern,
  conceptually aligned with gald3r `.gald3r/learned-facts.md`.
- **gald3r note (honest):** there is **no Cursor-style `rules/*.mdc` or per-glob rule scoping**. gald3r
  `g-rl-*` rules fold into `AGENTS.md` / `SOUL.md` prose (no `alwaysApply` / `globs` frontmatter
  analog). The mechanism is native and always-loaded, but it is file-prose, not a typed rule registry.
- Source: https://docs.openclaw.ai/concepts/agent-workspace

## 8. MCP Support — ✅ NATIVE (client + server)

- **Client**: saved server definitions under **`mcp.servers`** in `openclaw.json`; managed via
  `openclaw mcp add` / `set` / `configure` (Control UI editor at `/mcp`). Transports: **stdio**
  (command/args/env/cwd), **HTTP/SSE** (url/headers/timeout/auth: oauth), and **streamable-http**.
- **Server**: **`openclaw mcp serve`** starts a **stdio MCP server** exposing channel conversations.
  Built on `@modelcontextprotocol/sdk`.
- **gald3r note**: gald3r MCP server definitions are not auto-imported — re-declare each under
  `mcp.servers` via `openclaw mcp set`. The capability is fully present (both directions).
- Source: https://docs.openclaw.ai/cli/mcp

## 9. Plugins / Lobster Workflows — distribution + orchestration channels

- **Plugin system** ("dock" / plugin channels) extends channels, tools, and commands; plugins can
  call `registerCommand()` and **ship skills/hooks** — the natural distribution channel for a gald3r
  OpenClaw bundle.
- **Lobster workflow pipelines** are a first-class multi-step orchestration capability alongside
  skills/plugins — adoptable for gald3r `g-go`-style pipelines.
- **Scheduling**: the `HEARTBEAT.md` workspace file supports **scheduled/recurring agent behavior**
  (cron-like heartbeat) — adoptable for gald3r heartbeat tasks.

---

## Parity vs. Cursor Reference

OpenClaw reaches **full parity** with the Cursor reference (`g-skl-platform-cursor`): native
**commands, rules, agents, skills, hooks, and MCP**, plus native MCP **server** mode, Lobster workflow
pipelines, and a built-in memory hook as bonuses with no Cursor analog. Honest caveats: (1) hook
handlers are **TypeScript** (`handler.ts`) with an OpenClaw-specific event taxonomy, so gald3r `.ps1`
hooks are not directly portable; (2) rules are **prose** in `AGENTS.md` / `SOUL.md` (no `.mdc` typed
rules or per-glob scoping); (3) skills install into the **workspace** dir (`~/.openclaw/workspace/
skills/` by default), not the repo root automatically; (4) recursive sub-agent nesting is gated by
`maxSpawnDepth` (default 1).

**Reuse note:** because OpenClaw reads **`AGENTS.md`** and discovers folder-per-skill `SKILL.md`,
gald3r's `AGENTS.md` + `g-skl-*/SKILL.md` artifacts are largely reusable. The one real porting cost is
**hooks** (rewrite `.ps1` → `handler.ts`) and pointing the workspace at the gald3r skills source.

## Hook System

- **Type**: native (file-based, TypeScript handlers)
- **Config / declaration**: per-hook directory with `HOOK.md` (YAML frontmatter,
  `metadata.openclaw.events`) + `handler.ts`; hooks referenced from `~/.openclaw/openclaw.json`
- **Events available**: `command:new`, `command:reset`, `command:stop`, `session:compact:before`,
  `session:compact:after`, `agent:bootstrap`, `gateway:startup`, `gateway:shutdown`,
  `gateway:pre-restart`, `message:received`, `message:transcribed`, `message:preprocessed`,
  `message:sent`
- **Event payload format**: async TypeScript handler (`handler.ts`) receives the event object; this
  is **not** a stdin-JSON / exit-code contract
- **Command extensions**: `.ts` (TypeScript) — **not** `.ps1` / `.sh`. PowerShell hooks must be
  re-expressed as `handler.ts` or shelled out from one.
- **gald3r hook files**: gald3r `g-hk-*.ps1` are **[STUB] / unverified** for OpenClaw — the
  event→hook mapping is **not** fabricated here. Re-verify on the next `@g-platform-scan-docs openclaw`.

## Atypical Handling

- **Single runtime, file workspace**: full extensibility lives in the gateway + `~/.openclaw/
  workspace/`; config is `~/.openclaw/openclaw.json`. There is no documented project-local `.openclaw/`
  override — the workspace must be **pointed at the repo**, or gald3r skills installed into the
  workspace.
- **Skills == commands**: a `user-invocable: true` skill is automatically a `/skill <name>` slash
  command; no separate command-file system is required.
- **Sub-agents via tool, not file**: spawn with the `sessions_spawn` **tool** (`/subagents` is
  inspect-only); depth-limited (`maxSpawnDepth` default 1).
- **Chat-channel orientation**: `bindings` map Discord / Telegram / Slack / WhatsApp accounts to
  per-persona agents — multi-agent isolation is a first-class concept.

## gald3r Integration Notes

- Ship gald3r rule prose into **`AGENTS.md`** (operating rules) + **`SOUL.md`** (hard guardrails) —
  OpenClaw reads both every session. Do **not** rely on `CLAUDE.md`.
- Install gald3r `g-skl-*/SKILL.md` into the OpenClaw **workspace** `skills/` dir (or point the
  workspace at the gald3r skills source); folder-per-skill is identical to gald3r.
- Hooks require a **TypeScript rewrite** (`handler.ts`) — do not assume `.ps1` portability. Treat the
  gald3r hook wiring as **[STUB]** until verified on a live install.
- Re-declare MCP servers via `openclaw mcp set` (`mcp.servers` in `openclaw.json`).
- Re-verify on the next `@g-platform-scan-docs openclaw` (crawl_max_age_days: 14).

---

## Capability Summary (copy into PLATFORM_STATUS.md row)

| Hooks | Rules | Skills | Commands | MCP | Docs Fresh |
|---|---|---|---|---|---|
| ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |

Legend: ✅ verified working · ⚠️ partial / Cursor-generic · ❌ not supported · ❓ untested.

> All six mechanisms are **native** per the 2026-06-02 docs crawl. The honest residual caveats
> (TypeScript hook handlers, prose-only rules, workspace-relative skill install, `maxSpawnDepth` 1)
> are documented in the sections above and do not downgrade native availability — but the gald3r
> `.ps1`→`handler.ts` hook wiring itself remains install-unverified.

---

## Verification Evidence (docs crawl 2026-06-02, https://docs.openclaw.ai)

| Capability | How verified |
|---|---|
| Commands | /tools/slash-commands — `/skill <name>` generic entrypoint; direct command registration (`/prose`, `registerCommand()`); native Discord/Telegram registration (~v2026.2.23); inline directives stripped pre-model |
| Rules | /concepts/agent-workspace — `AGENTS.md` (operating rules) + `SOUL.md` ("never do X") + `MEMORY.md` injected every session; no `.mdc` typed rules |
| Agents | /tools/subagents — per-persona agents via `bindings`; runtime `sessions_spawn` tool (non-blocking, `agent:<id>:subagent:<uuid>`); restricted tool policy; `maxSpawnDepth` default 1; `/subagents` inspect-only |
| Skills | /tools/skills — `SKILL.md` (YAML frontmatter + body); `name`+`description` minimum; precedence loading (workspace/.agents/~/.openclaw/bundled/plugin); skills double as slash commands |
| Hooks | /automation/hooks — `HOOK.md` + `handler.ts` (async TS); events command:* / session:compact:* / agent:bootstrap / gateway:* / message:*; built-ins session-memory, command-logger, boot-md |
| MCP | /cli/mcp — client `mcp.servers` in `openclaw.json` (`openclaw mcp add/set/configure`, /mcp UI); stdio / HTTP-SSE / streamable-http; server `openclaw mcp serve`; `@modelcontextprotocol/sdk` |
| Instruction file | /concepts/agent-workspace — reads `AGENTS.md` + `SOUL.md` (NOT `CLAUDE.md`); both injected on first turn of a new session |
| Workflows | /tools/slash-commands + overview — Lobster workflow pipelines first-class alongside skills/plugins; `HEARTBEAT.md` cron-like scheduling |
| Caveats | Hook handlers TypeScript-only (`handler.ts`); rules prose-only (no `.mdc`); skills install to `~/.openclaw/workspace/skills/`; gald3r `.ps1` hook wiring [STUB] / unverified |
