---
subsystem_memberships: [PLATFORM_INTEGRATION]
platform: mistral
authoring_path: update
docs_url: https://docs.mistral.ai/mistral-vibe/terminal
docs_url_secondary:
  - https://docs.mistral.ai/vibe/code/cli/configuration
  - https://docs.mistral.ai/vibe/code/cli/skills
  - https://docs.mistral.ai/vibe/code/cli/agents
  - https://docs.mistral.ai/vibe/code/cli/mcp-servers
  - https://github.com/mistralai/mistral-vibe
  - https://github.com/mistralai/mistral-vibe/blob/main/CHANGELOG.md
crawl_max_age_days: 14
vault_doc_path: research/platforms/mistral/
last_doc_scan: 2026-06-02
reference: g-skl-platform-cursor
status: ⚠️
---

# PLATFORM_SPEC.md — Mistral Vibe CLI (`mistral-vibe`)

The "Mistral" coding surface is **three distinct products**, and gald3r integration targets the
config-driven one — the **Mistral Vibe CLI** (`mistral-vibe`), an open-source terminal coding agent:

| Surface | What it is | Config-driven? |
|---|---|---|
| **Mistral Vibe CLI** | Open-source terminal coding agent (`mistral-vibe`); `.vibe/` tree + `config.toml` | ✅ Yes — the only gald3r-relevant surface |
| **Mistral Code** | Closed in-IDE plugin (JetBrains + VSCode, enterprise bundle) | ❌ No project config files |
| **Le Chat** | Web/app chat with MCP connectors + memories | ❌ Not a file-config surface |

**gald3r targets Mistral Vibe CLI** — it is the only Mistral surface that reads project-level config
files (`.vibe/` + `AGENTS.md`). Mistral Code (IDE plugin) and Le Chat are documented here for honesty
but are **not** gald3r config targets.

**Authoring path**: UPDATE. **Verified 2026-06-02** against https://docs.mistral.ai/mistral-vibe/terminal
+ github.com/mistralai/mistral-vibe (see Verification Evidence). Latest version observed **2.13.0
(2026-05-29)**. This **upgrades** the prior spec: **Agents are now NATIVE** (custom agents + subagents),
and **Hooks moved from ❓ to ⚠️** (an experimental post-agent-turn lifecycle shipped v2.9.0, Apr 2026).

> **Instruction-file convention (platform-specific truth):** Mistral Vibe reads **`AGENTS.md`**, NOT
> `CLAUDE.md`. There is **no `.mistral/` directory** and **no YAML config** — config is **TOML** under
> `.vibe/`. Any prior body describing a `.mistral/config.yaml` scheme was fabricated; corrected here.

> **Docs-URL migration note:** doc paths are migrating from `/mistral-vibe/*` to `/vibe/code/cli/*`;
> both resolve as of the 2026-06-02 scan.

---

## 1. Folder Hierarchy

Mistral Vibe reads config from a **`.vibe/`** directory (NOT `.mistral/`), at both user and project
scope. Project config layers over user config and **only loads when the working directory is a trusted
folder**. Verified layout (configuration + skills + agents docs):

```
~/.vibe/                       ← user-global config
├── config.toml                ← main config (TOML): models, providers, tools, [[mcp_servers]]
├── .env                       ← API keys / provider credentials
├── AGENTS.md                  ← user-level instructions (all projects)
├── agents/<name>.toml         ← custom agent / subagent profiles (TOML)
├── prompts/<id>.md            ← custom system prompts (referenced by system_prompt_id)
├── skills/<name>/SKILL.md     ← user-level skills (Agent Skills spec)
└── trusted_folders.toml       ← trusted-execution allowlist (gates project .vibe/ loading)

<project-root>/
├── AGENTS.md                  ← project instructions (overrides user-level; closer files win)
└── .vibe/
    ├── config.toml            ← project config overlay
    ├── skills/<name>/SKILL.md ← project skills (also ./.agents/skills/)
    ├── agents/<name>.toml     ← project agent / subagent profiles
    ├── prompts/<id>.md        ← project prompts
    └── (hooks)                ← experimental post-agent-turn lifecycle; file location/schema undocumented
```

**gald3r writes** (project scope): `AGENTS.md`, `.vibe/skills/<name>/SKILL.md`, optionally
`.vibe/agents/*.toml`, and `.vibe/config.toml` `[[mcp_servers]]` entries.
**Vibe owns**: the `.vibe/` namespace, the `config.toml` (TOML) schema, and the trusted-folders
mechanism (`trusted_folders.toml` decides whether project `.vibe/` — and its skills/agents/prompts/
hooks — loads at all).

---

## 2. AI Instruction File

Vibe reads **`AGENTS.md`** — the same cross-platform standard gald3r already uses as its primary
instruction file (✅ direct parity). **It does NOT read `CLAUDE.md`.**

- **Resolution order**: `~/.vibe/AGENTS.md` (user-global) → project `AGENTS.md` files; files **closer
  to the working directory override** more distant ones. Instructions augment/override the default
  system prompt.
- **gald3r fit**: gald3r already generates/merges `AGENTS.md`; Vibe consumes it directly with **no
  transformation needed** — the strongest parity point for this platform.
- No `.cursorrules`-style legacy file; no `.mistral`-prefixed instruction file.
- Source: https://github.com/mistralai/mistral-vibe

---

## 3. Agents Support — ✅ NATIVE

- **Built-in agents**: `default`, `plan`, `accept-edits`, `auto-approve`, `lean`.
- **Custom agents**: `.toml` files in `~/.vibe/agents/` or `./.vibe/agents/`, selected via
  `vibe --agent <name>`. Format keys: `display_name`, `description`, `safety`, `active_model`,
  `system_prompt_id`, `enabled_tools` / `disabled_tools`, per-tool `permission = ask|always`.
- **Subagents**: set `agent_type = "subagent"`; spawned by the model through the `task` tool, return
  **text-only** results to the parent, and **cannot ask the user questions**.
- **Format mismatch vs gald3r**: Vibe agents are **TOML behavior profiles**; gald3r agents
  (`g-agnt-*.md`) are markdown — a real port requires markdown→TOML conversion (not done by the parity
  pipeline). `safety` (`safe`/`neutral`/`destructive`/`yolo`) is a **visual hint only, not enforcement**.
- Source: https://docs.mistral.ai/vibe/code/cli/agents

## 4. Skills Support — ✅ NATIVE

- **Agent Skills** (agentskills.io specification) — the *same* spec gald3r skills target, making
  skills portable across conforming agents. CHANGELOG confirms agentskills.io support added **v1.3.0
  (2025-12-23)**.
- **Discovery**: `~/.vibe/skills/<name>/SKILL.md` (user), `./.vibe/skills/<name>/SKILL.md` (project),
  `./.agents/skills/`, plus `skill_paths` in `config.toml`. Folder-per-skill `SKILL.md` ✅ matches
  gald3r exactly.
- **Frontmatter** keys: `name`, `description`, `license`, `compatibility`, `user-invocable`,
  `allowed-tools`. Differs slightly from gald3r's `subsystem_memberships` / `token_budget` (a superset;
  Vibe **ignores unknown keys** but expects `allowed-tools` / `user-invocable`).
- **Management**: `enabled_skills` / `disabled_skills` glob patterns in `config.toml`.
- Source: https://docs.mistral.ai/vibe/code/cli/skills

## 5. Commands / Workflows — ⚠️ PARTIAL

- **No standalone command-file directory** equivalent to `.cursor/commands/*.md` or
  `.claude/commands/`. Slash commands exist but only **via the skills mechanism**: set
  `user-invocable: true` in a skill's frontmatter and the skill name becomes available with
  `/skill-name` autocompletion in the CLI prompt.
- **gald3r gap**: gald3r's command files have **no native 1:1 landing zone**; each would need wrapping
  as a skill (heavy) or describing in `AGENTS.md` (lossy — no executable invocation). A built-in
  `/loop` command (v2.9.5, 2026-05-06) exists for recurring prompt execution, but that is a shipped
  built-in, not a user-command-file surface.
- Source: https://docs.mistral.ai/vibe/code/cli/skills

## 6. Hooks System — ⚠️ PARTIAL (experimental, minimal)

- **Experimental hooks** shipped **v2.9.0 (2026-04-28)**: "Experimental hooks system with
  **post-agent-turn lifecycle**." The configuration docs list `hooks` among what each `.vibe/` path
  contributes to a session, but publish **NO event taxonomy, file location, or schema**. The README
  does not mention hooks and the dedicated `/cli/hooks` doc page 404s.
- **Only a single lifecycle point shipped** (post-agent-turn), with no later CHANGELOG refinement
  through v2.13.0. Broader event hooks remain **unshipped**: issue #250 ("feat: Hooks" — before/after
  shell-command hooks, modeled on Claude Code) is **CLOSED** with no implementation; issue #531
  ("feat: add BeforeTool hook") is still **OPEN**.
- **gald3r gap**: gald3r's PowerShell pre-tool / session-start / pre-commit hooks have **no verified
  wiring target** — the one shipped event (post-agent-turn) does not cover them and its config schema
  is undocumented. Tool *permissions* (`[tools.bash] permission = "ask"|"always"`) and agent `safety`
  levels cover *some* guardrail ground hooks would otherwise serve, but they are not an event-hook
  system. **Do NOT fabricate a `hooks.json` equivalent.**
- Source: https://github.com/mistralai/mistral-vibe/blob/main/CHANGELOG.md

## 7. Rules / Memory — ⚠️ PARTIAL

- **No scoped/glob rule auto-loader** (no `.cursor/rules/*.mdc` equivalent). Persistent project
  instructions are injected via **`AGENTS.md` resolution** (closer files override) — a single layered
  instruction file, not per-file globbed or on-demand rules.
- **Custom system prompt**: a file under `~/.vibe/prompts/<id>.md` can **replace** the default system
  prompt via `system_prompt_id` in `config.toml` — another instruction-injection lever.
- **Custom compaction prompts** (v2.11.1, 2026-05-27): user-definable context-compaction prompts.
- **Memory**: Le Chat (the chat product) has a "Memories" feature, but that is the chat surface, **not**
  Vibe CLI project config — not a gald3r file target.
- **gald3r gap**: gald3r's scoped `g-rl-*` rules (alwaysApply / globs / on-demand) collapse into a
  single `AGENTS.md` blob on Vibe — no per-file `globs` scoping, no per-rule on-demand loading.
- Source: https://github.com/mistralai/mistral-vibe

## 8. MCP Support — ✅ NATIVE

- MCP servers configured as `[[mcp_servers]]` entries in `config.toml`. Transports: **http**,
  **streamable-http**, **stdio**. Keys: `name`, `transport`, `url` (http), `command`/`args` (stdio),
  `headers`, `api_key_env`, `env`, `startup_timeout_sec`, `tool_timeout_sec`.
- **Tool namespacing/filtering**: tools are namespaced `{server_name}_{tool_name}` and filtered via
  `enabled_tools` / `disabled_tools` (exact, glob, or regex with `re:` prefix).
- **Limitation**: "The CLI does not yet support MCP servers that require **OAuth** authentication."
  v2.13.0 (2026-05-29) improved MCP HTTP transport.
- **Le Chat** separately offers MCP connectors invoked via `/Connector_Name` — that is the chat
  product, not Vibe CLI file config.
- Source: https://docs.mistral.ai/vibe/code/cli/mcp-servers

```toml
[[mcp_servers]]
name = "my_http_server"
transport = "http"            # http | streamable-http | stdio
url = "http://localhost:8000"
headers = { "Authorization" = "Bearer my_token" }
api_key_env = "MY_API_KEY_ENV_VAR"
startup_timeout_sec = 15
tool_timeout_sec = 120
```

## 9. Other Extensibility

- **Trusted folders** (`trusted_folders.toml`) gate whether project `.vibe/` config (and its skills/
  agents/prompts/hooks) loads at all.
- **Remote agents** (powered by Mistral Medium 3.5) + a **Vibe Code Web** surface — orchestration
  features, not file-config primitives.
- **Plugin support** is requested (Discussion #497) but **not yet a shipped extensibility surface**.

---

## Known Gaps vs. Cursor Reference

| # | Gap | Severity |
|---|---|---|
| 1 | **Three products, one config-driven** — only Vibe CLI reads config files. Mistral Code (IDE plugin) and Le Chat are not gald3r config targets. | High (scope) |
| 2 | **Hooks experimental & minimal** — only a single post-agent-turn lifecycle point (v2.9.0), no published schema, no before-tool/session-start/pre-commit events; gald3r `g-hk-*.ps1` have no verified wiring target. (§6) | High |
| 3 | **No command-file directory** — slash commands are skill-provided only; gald3r's command files have no native 1:1 landing zone. (§5) | High |
| 4 | **No scoped/glob rules** — persistent instructions collapse into a single layered `AGENTS.md` (+ optional custom system prompt); no per-file `globs` or on-demand loading. (§7) | Medium |
| 5 | **Agent format mismatch** — Vibe agents are TOML behavior profiles; gald3r agents are markdown. No automatic conversion. `safety` is visual-only, not enforcement. (§3) | Medium |
| 6 | **Skill frontmatter mismatch** — folder-per-skill ✅ matches, but Vibe expects `allowed-tools` / `user-invocable`; gald3r skills emit `subsystem_memberships` / `token_budget`. Light adaptation needed. (§4) | Low |
| 7 | **Config is TOML, not YAML** — the real surface is `.vibe/config.toml`; there is no `.mistral/` and no `config.yaml`. | (corrected) |
| 8 | **MCP OAuth unsupported** — the CLI does not yet support MCP servers requiring OAuth. (§8) | Low |
| 9 | **Parity pipeline does NOT target `.vibe/`** — `platform_parity_sync.ps1` has no `.vibe/` writer. Any real install support is future work. | Medium |

**Strongest parity points** (not gaps): `AGENTS.md` is consumed directly (✅), and the Agent Skills
`SKILL.md` folder-per-skill convention is shared (✅). Agents/subagents are now native (✅) but require
markdown→TOML conversion.

## Hook System

- **Type**: experimental (single post-agent-turn lifecycle; file location/schema undocumented) ⚠️
- **Config file**: `.vibe/` (each trusted path contributes its `AGENTS.md` and `.vibe/` config — tools,
  skills, agents, prompts, **hooks** — to the session); exact hook file/location NOT published as of
  the 2026-06-02 scan
- **Events available**: **post-agent-turn** only (shipped v2.9.0, 2026-04-28). No before-tool /
  session-start / pre-commit events. [STUB — payload/schema undocumented]
- **Event payload format**: [STUB] — undocumented
- **Limitations**: tool *permissions* (`[tools.bash] permission = "ask"|"always"`) and agent `safety`
  levels cover some hook-like ground but are NOT an event-hook system; broader hooks unshipped
  (issue #250 CLOSED unimplemented; issue #531 OPEN)
- **gald3r hook files**: none verified — gald3r `g-hk-*.ps1` (pre-tool / session-start / pre-commit)
  have no confirmed target on Vibe; the one shipped event does not cover them [STUB]

## Atypical Handling

- Config tree is `.vibe/` with `config.toml` (**TOML**, not YAML); **`AGENTS.md`** is the instruction
  file (NOT `CLAUDE.md`); Agent-Skills via `SKILL.md`.
- **Trusted-folders gate**: project `.vibe/` config (skills/agents/prompts/hooks) loads only when the
  working directory is trusted (`trusted_folders.toml`).
- Hooks are **experimental** — a single post-agent-turn event exists, but the file location and schema
  are unpublished; existence without a usable contract for gald3r's hook needs.
- Tool permissions + agent `safety` levels are the only verified gating mechanism for guardrails.

## gald3r Integration Notes

- Ship gald3r's **`AGENTS.md`** — Vibe consumes it directly (no transformation). This is the cheapest
  high-value install footprint today.
- gald3r skills (`g-skl-*/SKILL.md`) load natively (agentskills.io); frontmatter needs light adaptation
  (`allowed-tools` / `user-invocable`).
- gald3r hooks have **no verified wiring target** — the only shipped event (post-agent-turn) does not
  cover pre-tool / session-start / pre-commit, and the schema is undocumented. Do NOT assume
  `.vibe/hooks/` works.
- Re-crawl Mistral Vibe docs on the next `@g-platform-scan-docs mistral` specifically for a hook event
  list + file location; until then Hooks stays ⚠️ (crawl_max_age_days: 14).

---

## Capability Summary (copy into PLATFORM_STATUS.md row)

| Hooks | Rules | Skills | Commands | MCP | Docs Fresh |
|---|---|---|---|---|---|
| ⚠️ | ⚠️ | ✅ | ⚠️ | ✅ | ✅ |

Legend: ✅ verified working · ⚠️ partial / format-mismatch · ❌ not supported · ❓ untested.

- **Hooks ⚠️**: experimental post-agent-turn lifecycle only (v2.9.0); no schema, no pre-tool/
  session-start/pre-commit — cannot wire gald3r hooks.
- **Rules ⚠️**: `AGENTS.md` injection (+ optional custom system prompt); no scoped `.mdc` rule system.
- **Skills ✅**: native Agent Skills spec (agentskills.io), folder-per-skill `SKILL.md` (frontmatter
  needs light adaptation).
- **Commands ⚠️**: slash commands exist but only via the skill mechanism (`user-invocable: true`); no
  command-file directory.
- **MCP ✅**: `.vibe/config.toml` `[[mcp_servers]]` (http / streamable-http / stdio); no OAuth yet.
- **Agents ✅** (not in 5-col summary): native custom agents + subagents (`.vibe/agents/*.toml`).
- **Docs Fresh ✅**: doc scan performed 2026-06-02 (docs.mistral.ai + GitHub README + CHANGELOG).

---

## Verification Evidence (docs crawl 2026-06-02, docs.mistral.ai + github.com/mistralai/mistral-vibe)

| Capability | How verified |
|---|---|
| `.vibe/` + `config.toml` (not `.mistral/`/YAML) | /vibe/code/cli/configuration — `.vibe/` (user `~/.vibe/`, project `./.vibe/`); project layers over user; loads only in trusted folders |
| `AGENTS.md` instruction file + resolution (NOT `CLAUDE.md`) | GitHub README — `AGENTS.md` files; closer-to-cwd overrides; `~/.vibe/AGENTS.md` user-global; augments/overrides system prompt |
| Agents/subagents (TOML profiles) | /vibe/code/cli/agents — built-ins default/plan/accept-edits/auto-approve/lean; custom `.toml`; `vibe --agent`; `agent_type="subagent"` via `task` tool, text-only |
| Skills (Agent Skills, SKILL.md) | /vibe/code/cli/skills — agentskills.io spec; `~/.vibe/skills`, `./.vibe/skills`, `./.agents/skills`, `skill_paths`; CHANGELOG v1.3.0 (2025-12-23) |
| Slash commands = skill-provided | /vibe/code/cli/skills — `user-invocable: true` → `/skill-name` autocompletion; no standalone command-file directory |
| Hooks experimental (post-agent-turn) | CHANGELOG v2.9.0 (2026-04-28) "experimental hooks, post-agent-turn lifecycle"; no schema; /cli/hooks 404s; issue #250 CLOSED, #531 OPEN |
| MCP `[[mcp_servers]]` (TOML) | /vibe/code/cli/mcp-servers — http/streamable-http/stdio; `{server}_{tool}` namespacing; `enabled_tools`/`disabled_tools`; no OAuth; v2.13.0 HTTP improvements |
| Le Chat MCP connectors (separate surface) | Le Chat connectors invoked via `/Connector_Name` — chat product, not Vibe CLI file config |
| Mistral Code = closed IDE plugin | JetBrains/VSCode enterprise plugin; no project config files |
| No `.vibe/` writer in parity pipeline | Verified absence — `platform_parity_sync.ps1` targets `.cursor/`/`.claude/` family, not `.vibe/` |
