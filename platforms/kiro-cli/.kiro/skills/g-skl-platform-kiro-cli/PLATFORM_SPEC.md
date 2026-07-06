---
subsystem_memberships: [PLATFORM_INTEGRATION]
platform: kiro-cli
authoring_path: update
docs_url: https://kiro.dev/docs/cli
docs_url_secondary:
  - https://kiro.dev/docs/cli/skills/
  - https://kiro.dev/docs/cli/steering/
  - https://kiro.dev/docs/cli/custom-agents/configuration-reference/
  - https://kiro.dev/docs/cli/chat/subagents/
  - https://kiro.dev/docs/cli/hooks/
  - https://kiro.dev/docs/cli/mcp/
  - https://kiro.dev/docs/cli/reference/slash-commands/
crawl_max_age_days: 7
vault_doc_path: research/platforms/kiro-cli/
last_doc_scan: 2026-06-02
reference: g-skl-platform-cursor
status: ✅
---

# PLATFORM_SPEC.md — Kiro CLI (Amazon)

Kiro CLI is Amazon's **terminal-based agentic coding assistant** — the rebrand/successor of the
**Amazon Q Developer CLI** (the `q` / `q chat` entry points are preserved for backward
compatibility). It is spec-driven and agent-centric, with a full extensibility surface configured
under the **`.kiro/`** directory tree. As of mid-2026 Kiro CLI natively supports **all six**
gald3r-relevant extension primitives — custom slash commands, rules/steering, custom agents +
subagents, Agent Skills, lifecycle hooks, and MCP. Critically for gald3r, Kiro CLI's native
instruction surface is **`.kiro/steering/`** and it honors the **`AGENTS.md`** standard (it does
**not** read `CLAUDE.md`), and it discovers **Agent Skills (`SKILL.md`)** from `.kiro/skills/`, so
gald3r's `SKILL.md` artifacts are **drop-in compatible**.

**Authoring path**: UPDATE. **Verified 2026-06-02** against https://kiro.dev/docs/cli (see
Verification Evidence). This **supersedes** the prior spec (`last_doc_scan: never` / `2026-05-20`)
which marked skills as ❌ and hooks/rules/commands as ⚠️ — Agent Skills are now **NATIVE** (each
discovered skill also becomes a `/skill-name` slash command, CLI v2.1, 2026-04-24), and the
lifecycle hook + custom-agent surface is fully native.

> **Distinct from Kiro IDE.** Kiro CLI and Kiro IDE share the `.kiro/` namespace and the **steering**
> context mechanism, but the CLI has a **richer agent/hook/command/skills surface** than the IDE. Do
> **not** copy the IDE spec's "no agents / no commands / file-event hooks" conclusions onto the CLI
> (Kiro IDE is covered by `g-skl-platform-kiro`, T1472). Where a feature is CLI-specific it is noted
> inline.

---

## 1. Folder Hierarchy

Kiro CLI reads project-scope config under repo-root `.kiro/`, and user/global-scope config under
`~/.kiro/`. Doc-verified layout:

```
<project-root>/
├── AGENTS.md                       ← instruction file Kiro CLI reads (AGENTS.md standard; NOT CLAUDE.md)
└── .kiro/
    ├── steering/    *.md           ← always-on context (product.md/tech.md/structure.md auto-loaded)
    ├── skills/      <name>/SKILL.md ← Agent Skills (YAML frontmatter: name, description)
    ├── settings/
    │   └── mcp.json                ← workspace-scope MCP config (mcpServers object)
    └── (custom-agent JSON configs — filename without .json = agent name)

~/.kiro/                            ← USER/GLOBAL tree (migrated from ~/.aws/amazonq/)
├── steering/    *.md               ← global steering (also picks up a global AGENTS.md)
├── skills/      <name>/SKILL.md    ← global Agent Skills
└── settings/
    └── mcp.json                    ← global MCP config
```

**Workspace overrides global** for identically-named skills (`.kiro/skills/` wins over
`~/.kiro/skills/`). Foundation steering files (`product.md`, `tech.md`, `structure.md`) are included
in **every interaction by default**; other steering files can be scoped/conditionally included via
agent config.

**gald3r writes**: `AGENTS.md` (canonical instruction file, auto-picked-up); always-on rules as
individual files under `.kiro/steering/`; `g-skl-*/SKILL.md` skills under `.kiro/skills/`; a gald3r
custom-agent JSON config; and `.kiro/settings/mcp.json` for MCP servers.
**Kiro CLI owns**: the `.kiro/` namespace, steering auto-injection, the agent-config JSON schema,
the lifecycle hook engine, slash-command resolution, and MCP connection lifecycle.

---

## 2. AI Instruction File

Kiro CLI's native instruction surface is **markdown files under `.kiro/steering/`** (workspace) and
`~/.kiro/steering/` (global), with `product.md` / `tech.md` / `structure.md` auto-loaded into every
interaction. It **additionally honors the `AGENTS.md` standard** placed in the workspace root or
`~/.kiro/steering/` — that file is picked up automatically. There is **no `CLAUDE.md` or `GEMINI.md`
convention**. For gald3r the canonical instruction file is **`AGENTS.md`** (auto-read), and
additional always-on rules live as individual files under `.kiro/steering/`.

- Source: https://kiro.dev/docs/cli/steering/

## 3. Agents Support — ✅ NATIVE

- **Custom agents**: defined as **JSON configuration files** — *the filename (without `.json`)
  becomes the agent's name*. Created interactively via `/agent create` (AI-assisted scaffold) or
  hand-authored. Config fields include `tools`, `allowedTools`, `resources`
  (e.g. `"file://.kiro/steering/**/*.md"`), and a `hooks` field (see §6).
- **Subagents**: run in their own **isolated context**; the main agent can spawn **up to four
  subagents at once**, monitor them live (Ctrl+G), and combine results. An agent must include
  `subagent` in its `tools` array to delegate.
- **gald3r mapping**: gald3r `g-agnt-*` definitions map onto Kiro CLI custom agents, **but the format
  differs** — Kiro CLI agents are **JSON, not markdown+frontmatter**, so gald3r's markdown agent
  files require a translation step (role intent → agent JSON, pinning steering via `resources`)
  rather than a file drop. The mechanism itself is fully native.
- Source: https://kiro.dev/docs/cli/custom-agents/configuration-reference/ ·
  https://kiro.dev/docs/cli/chat/subagents/

## 4. Skills Support — ✅ NATIVE

- **Agent Skills** (open Agent-Skills standard): *"Skills are directories containing a `SKILL.md`
  file with YAML frontmatter"* (required: `name`, `description`). The default agent **automatically
  loads skills from `.kiro/skills/` and `~/.kiro/skills/` — no configuration needed.** Skills are
  **progressively loaded** — only metadata at startup, full content on demand.
- Frontmatter: `name` (lowercase alphanumeric/hyphens, max 64 chars) and `description` (max 1024
  chars, drives activation). Optional supporting files in a `references/` subdirectory. Workspace
  skills (`.kiro/skills/`) override identically-named global skills.
- Each discovered skill **doubles as a `/skill-name` slash command** (v2.1, 2026-04-24).
- **gald3r mapping**: directly compatible with the gald3r `SKILL.md` format — `g-skl-*/SKILL.md` load
  **natively** from `.kiro/skills/`. This is the cheapest high-parity install path.
- Source: https://kiro.dev/docs/cli/skills/ (docs updated 2026-05-12)

## 5. Commands / Workflows — ✅ NATIVE

- **Skills-as-slash-commands**: a skill named `pr-review` becomes the `/pr-review` slash command —
  user-extensible slash commands flow primarily through the **Skills** directory (each skill name
  becomes `/skill-name`). Introduced in CLI v2.1 (2026-04-24).
- **Local prompts**: reusable local prompt templates managed via `/prompts create my-prompt` and the
  `/prompts` command, stored as config files under `.kiro/`.
- Built-in slash commands (`/agent`, `/context`, `/model`, `/load`, `/save`, `/prompts`, `/guide`,
  `/settings`, …) are fixed.
- **gald3r mapping**: gald3r `@g-*` / `/g-*` commands map onto **Skills** (`/skill-name`) or local
  prompts — there is **no separate arbitrary custom-command file format** beyond skills and prompts,
  so a gald3r command-per-file model maps onto **skills** rather than a dedicated `commands/`
  directory.
- Source: https://kiro.dev/docs/cli/reference/slash-commands/

## 6. Hooks System — ✅ NATIVE

- **Lifecycle hooks** declared in the **agent configuration file** (`hooks` field, JSON) — *not*
  standalone `.kiro/hooks/*.json` IDE files. Five lifecycle events: **`agentSpawn`**,
  **`userPromptSubmit`**, **`preToolUse`**, **`postToolUse`**, **`stop`**.
- **Control flow via exit codes**: `0` = success; **`2` = block tool execution (PreToolUse only)** —
  STDERR is returned to the LLM; any other code = failure with STDERR surfaced as a warning.
- **Event payload**: events receive **JSON via STDIN**. A `matcher` field scopes pre/postToolUse to
  internal tool names (`fs_read`, `fs_write`, `execute_bash`, `use_aws`).
- **gald3r mapping**: strong conceptual mapping — `g-hk-session-start` → `agentSpawn`;
  `g-hk-agent-complete`/`g-hk-session-end` → `stop`; preToolUse guards → `preToolUse`. The hook
  scripts are reusable (they read STDIN / env), but **wiring is per-agent-config JSON** (replicated
  per agent for cross-agent automation) and the STDIN-JSON shape differs from Cursor's PowerShell
  `{ continue = true }` envelope — so gald3r `g-hk-*.ps1` must read `$input` / stdin, and an adapter
  pass is required.
- Source: https://kiro.dev/docs/cli/hooks/ ·
  https://kiro.dev/docs/cli/custom-agents/configuration-reference/#hooks-field

## 7. Rules / Memory — ✅ NATIVE

- **Steering files** — markdown in `.kiro/steering/` (workspace) and `~/.kiro/steering/` (global),
  auto-loaded as passive context. *"Steering files reside in your workspace root folder under
  `.kiro/steering/`."* Foundation files (`product.md`, `tech.md`, `structure.md`) are included in
  every interaction by default; the `AGENTS.md` standard is honored here too.
- Plain **`.md`** (no `.mdc`). Non-foundation steering files require explicit inclusion (scoped via
  agent config / `resources` glob) rather than being always-on, and there is **no per-rule
  `alwaysApply`/`globs` frontmatter** like Cursor's `.mdc`.
- **gald3r mapping**: gald3r `g-rl-*` rules consolidate into steering `.md` file(s) — always-on rules
  as foundation/auto-loaded steering; scoped rules approximated via an agent `resources` glob
  (per-agent, not per-rule). Slightly lossy (no per-rule glob scoping).
- Source: https://kiro.dev/docs/cli/steering/

## 8. MCP Support — ✅ NATIVE

- MCP servers loaded from `<project-root>/.kiro/settings/mcp.json` (workspace) or
  `~/.kiro/settings/mcp.json` (user/global). Format uses an **`mcpServers`** object with `command`,
  `args`, `env`, and an optional `disabled` field — matching the common Claude/Cline convention, so
  gald3r MCP server definitions **port directly**. (On migration from the Q Developer CLI,
  `~/.aws/amazonq/mcp.json` is copied to `~/.kiro/settings/mcp.json`.)
- Source: https://kiro.dev/docs/cli/mcp/

## 9. Other Extensibility

- **Spec-driven development**: Kiro's signature workflow — structured specs (requirements / design /
  tasks) drive multi-step implementation.
- **Agent output side channels** (CLI v2.3, 2026-05-12): `$AGENT_DISPLAY_OUT` and
  `$AGENT_CONTEXT_OUT` let shell commands / hooks stream output into the display vs. the agent
  context separately — useful for hook-driven context injection.
- **Interactive authoring**: `/agent create` (AI-assisted) generates full agent JSON; the `/guide`
  agent can scaffold agents, prompts, and steering files into `.kiro/`.
- **Context rules**: runtime context inclusion controlled via `/context show | add | remove`
  (glob-based file context rules).

---

## Parity vs. Cursor Reference

Kiro CLI reaches **full parity** with the Cursor reference (`g-skl-platform-cursor`): native
**commands, rules, agents, skills, hooks, and MCP** (`overall_readiness: full`). Caveats are
*format*, not *capability*:

1. **Commands** — no first-class standalone custom-slash-command file format; custom commands are
   expressed indirectly as **Skills** (`/skill-name`) or local **prompts**, so gald3r's
   command-per-file model maps onto skills rather than a dedicated `commands/` directory.
2. **Hooks / Rules** are bound to **per-agent JSON config** rather than a standalone global hooks
   file — hooks live inside each agent's JSON `hooks` field, so cross-agent/global lifecycle
   automation must be replicated per agent (non-foundation steering also requires explicit
   inclusion).
3. **Agents** are **JSON-only** (no markdown agent files) — custom agents must be authored as JSON,
   adding a translation step for gald3r's markdown-centric `g-agnt-*` authoring.

**Reuse note (important):** because Kiro CLI reads **`AGENTS.md`** and discovers **`SKILL.md`** under
`.kiro/skills/`, gald3r's `AGENTS.md` + `g-skl-*/SKILL.md` artifacts are **drop-in reusable** — the
cheapest high-parity Kiro CLI install ships those plus steering rules, a gald3r custom-agent JSON,
and `.kiro/settings/mcp.json`.

## Hook System

- **Type**: native (lifecycle hooks declared in the agent JSON config `hooks` field)
- **Config file**: agent JSON config (`hooks` field/array) — NOT standalone `.kiro/hooks/*.json` IDE files
- **Events available**: `agentSpawn` (≈ sessionStart), `userPromptSubmit`, `preToolUse`, `postToolUse`, `stop` (≈ session end)
- **Event payload format**: JSON via STDIN (fields include `hook_event_name`, `cwd`, `session_id`); `matcher` scopes pre/postToolUse to internal tools (`fs_read`/`fs_write`/`execute_bash`/`use_aws`)
- **Blocking semantics**: exit code `2` (PreToolUse only) blocks tool execution and returns STDERR to the LLM; other non-zero = failure warning
- **gald3r hook files**: `.kiro/hooks/g-hk-on-<event>.py` map to `agentSpawn`/`stop`/`preToolUse`/`postToolUse`/`userPromptSubmit` via direct `python <path>` command entries in the agent JSON (T1601, PS1-KILL epic T667 — no PowerShell shim needed since the `command` field accepts an arbitrary command string). Each entrypoint's `g_hk_core.dispatch(<event>)` reads stdin directly.

## Atypical Handling

- Hooks live in the **agent config file** (`hooks` array), not a standalone hooks file — different
  from both Cursor (`hooks.json`) and Kiro IDE (`.kiro/hooks/*.json`).
- Event payload arrives as **JSON on STDIN**, not env vars — gald3r `.ps1` hooks must read stdin.
- Custom agents are **JSON** (filename-without-`.json` = agent name), not markdown.
- Instruction surface is **`.kiro/steering/` + `AGENTS.md`** — Kiro CLI does **not** read `CLAUDE.md`.

## gald3r Integration Notes

- Ship gald3r's `AGENTS.md` (auto-read) + `g-skl-*/SKILL.md` under `.kiro/skills/` (auto-discovered,
  also exposed as `/skill-name`) — the highest-leverage, lowest-port install.
- Consolidate gald3r rules into `.kiro/steering/` `.md` files; add `.kiro/settings/mcp.json` for MCP.
- Custom agents require markdown→JSON translation; lifecycle hooks require per-agent-JSON wiring with
  STDIN-JSON `.ps1` adapters (genuine `agentSpawn`/`stop`/`preToolUse`/`postToolUse` parity).
- Re-verify on the next `@g-platform-scan-docs kiro-cli` (crawl_max_age_days: 7).

---

## Capability Summary (copy into PLATFORM_STATUS.md row)

| Hooks | Rules | Skills | Commands | MCP | Docs Fresh |
|---|---|---|---|---|---|
| ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |

Legend: ✅ verified working · ⚠️ partial / Cursor-generic · ❌ not supported · ❓ untested.

- **Hooks ✅**: native lifecycle hooks (`agentSpawn`/`userPromptSubmit`/`preToolUse`/`postToolUse`/
  `stop`) in agent JSON; exit-code `2` blocks (PreToolUse); STDIN-JSON payload (per-agent wiring).
- **Rules ✅**: steering files (`.kiro/steering/*.md`) auto-loaded; foundation files always-on; no
  per-rule glob scoping (scope via agent `resources`).
- **Skills ✅**: Agent Skills `SKILL.md` auto-loaded from `.kiro/skills/` + `~/.kiro/skills/`; each
  also a `/skill-name` slash command (v2.1).
- **Commands ✅**: Skills-as-slash-commands + `/prompts create`; no standalone command-file format.
- **MCP ✅**: `mcpServers` JSON at `.kiro/settings/mcp.json` + `~/.kiro/settings/mcp.json`.
- **Docs Fresh ✅**: crawled 2026-06-02 (kiro.dev/docs/cli).

---

## Verification Evidence (docs crawl 2026-06-02, https://kiro.dev/docs/cli)

| Capability | How verified |
|---|---|
| Commands | /reference/slash-commands — Skills become `/skill-name` (v2.1, 2026-04-24); `/prompts create`; no standalone custom-command file format |
| Rules | /steering — `.kiro/steering/*.md` auto-loaded (product/tech/structure always-on); honors `AGENTS.md`; no per-rule glob scoping |
| Agents | /custom-agents/configuration-reference + /chat/subagents — JSON configs (filename = agent name); subagents in isolated context, up to 4 at once; `/agent create` |
| Skills | /skills — Agent Skills `SKILL.md` (YAML name/description) auto-loaded from `.kiro/skills/` + `~/.kiro/skills/`; progressive load; doubles as `/skill-name` (docs updated 2026-05-12) |
| Hooks | /hooks + configuration-reference#hooks-field — agent-config `hooks` field; `agentSpawn`/`userPromptSubmit`/`preToolUse`/`postToolUse`/`stop`; JSON via STDIN; exit `2` blocks (PreToolUse) |
| MCP | /mcp — `mcpServers` JSON at `.kiro/settings/mcp.json` (workspace) + `~/.kiro/settings/mcp.json` (global); Claude/Cline-compatible schema |
| Instruction file | /steering — native `.kiro/steering/` + `AGENTS.md` standard; **no `CLAUDE.md`/`GEMINI.md`** |
| Lineage | Rebrand/successor of Amazon Q Developer CLI; `q`/`q chat` entry points preserved; migrated `~/.aws/amazonq/` → `~/.kiro/` |
| Recency | Skills→slash commands v2.1 (2026-04-24); Agent Skills docs 2026-05-12; Agent Output Side Channels v2.3 (2026-05-12) |
