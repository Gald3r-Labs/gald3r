---
subsystem_memberships: [PLATFORM_INTEGRATION]
platform: mistral
authoring_path: update
docs_url: https://docs.mistral.ai/mistral-vibe/terminal
docs_url_secondary:
  - https://docs.mistral.ai/mistral-vibe/terminal/configuration
  - https://docs.mistral.ai/mistral-vibe/agents-skills
  - https://github.com/mistralai/mistral-vibe
  - https://docs.mistral.ai/le-chat/knowledge-integrations/connectors/mcp-connectors
crawl_max_age_days: 14
vault_doc_path: research/platforms/mistral/
last_doc_scan: 2026-05-26
reference: g-skl-platform-cursor
status: ⚠️
---

# PLATFORM_SPEC.md — Mistral (Mistral Vibe CLI / Mistral Code / Le Chat)

The "Mistral" coding surface is **three distinct products**, and gald3r integration targets the
config-driven one:

| Surface | What it is | Config-driven? |
|---|---|---|
| **Mistral Vibe CLI** | Open-source terminal coding agent (`mistral-vibe` on PyPI), powered by Devstral 2 / Codestral | ✅ Yes — `.vibe/` tree + `config.toml` |
| **Mistral Code** | In-IDE plugin for JetBrains + VSCode (enterprise bundle) | ❌ Closed IDE plugin; no gald3r config files |
| **Le Chat** | Web/app chat with MCP connectors + memories | ⚠️ MCP connectors only; not a file-config surface |

**gald3r targets Mistral Vibe CLI** — it is the only Mistral surface that reads project-level
config files (`.vibe/`, `AGENTS.md`). Mistral Code (IDE plugin) and Le Chat are documented here
for honesty but are **not** gald3r config targets.

> **Authoring path: UPDATE** — `g-skl-platform-mistral/SKILL.md` already shipped, but its prior
> body was largely fabricated (it described a `.mistral/config.yaml` YAML scheme that does not
> exist). This spec corrects the record against the verified `.vibe/` + `config.toml` reality
> confirmed by a 2026-05-26 doc scan of docs.mistral.ai and github.com/mistralai/mistral-vibe.

---

## 1. Folder Hierarchy

Mistral Vibe reads config from a **`.vibe/`** directory (NOT `.mistral/`), at both user and
project scope. Project-scoped config layers over user-scoped (closer paths override). Verified
layout (from docs.mistral.ai/mistral-vibe/terminal/configuration + agents-skills):

```
~/.vibe/                      ← user-global config
├── config.toml               ← main config (models, providers, tools, MCP servers)
├── .env                      ← API keys / provider credentials
├── AGENTS.md                 ← user-level instructions (all projects)
├── agents/<name>.toml        ← custom agent / subagent profiles
├── prompts/<id>.md           ← custom system prompts (referenced by system_prompt_id)
├── skills/<name>/SKILL.md    ← user-level skills (Agent Skills spec)
└── trusted_folders.toml      ← trusted-execution allowlist

<project-root>/
├── AGENTS.md                 ← project instructions (overrides user-level)
└── .vibe/
    ├── config.toml           ← project config overlay
    ├── skills/<name>/SKILL.md ← project skills
    ├── agents/<name>.toml    ← project agent/subagent profiles
    ├── prompts/<id>.md       ← project prompts
    └── (hooks)               ← docs list "hooks" as a .vibe/ contribution; format undocumented
```

- **gald3r would write** (project scope): `AGENTS.md`, `.vibe/skills/<name>/SKILL.md`,
  optionally `.vibe/agents/*.toml`, and `.vibe/config.toml` MCP entries.
- **Vibe owns**: the `.vibe/` namespace, `config.toml` schema, the trusted-folders mechanism.
- **Correction vs. prior SKILL.md**: there is **no** `.mistral/`, **no** `config.yaml`, and
  **no** `mistral.yaml`. The prior skill body was fabricated. Config is **TOML** under `.vibe/`.

---

## 2. AI Instruction File

- **Canonical file**: **`AGENTS.md`** — the same cross-platform standard gald3r already uses as
  its primary instruction file (✅ direct parity with the AGENTS.md convention).
- **Resolution order**: `~/.vibe/AGENTS.md` (user) → project `AGENTS.md` files; files closer to
  the current working directory override more distant ones (verified, docs + GitHub README).
- **gald3r fit**: gald3r already generates/merges `AGENTS.md`; Mistral Vibe consumes it directly
  with **no transformation needed**. This is the strongest parity point for this platform.
- **No `.cursorrules`-style legacy file** and **no `.mistral`-prefixed instruction file**.

---

## 3. Agents Support

- **Native concept**: ✅ Yes. Vibe has built-in agent profiles (`default`, `plan`,
  `accept-edits`, `auto-approve`) and supports **custom agents + subagents**.
- **Discovery**: `~/.vibe/agents/<name>.toml` (user) and `.vibe/agents/<name>.toml` (project).
- **Format**: TOML, e.g.:
  ```toml
  display_name = "Custom Agent"
  description  = "Description"
  safety       = "neutral"      # safe | neutral | destructive | yolo (visual only, no enforcement)
  auto_approve = true
  enabled_tools = ["read_file", "grep"]
  ```
- **Subagents**: add `agent_type = "subagent"`. Limitation: subagents cannot ask questions and
  return text-only results.
- **Selection**: `--agent <name>` flag or `Shift+Tab` in interactive mode.
- **gald3r gap**: gald3r agents are **markdown** (`g-agnt-*.md`); Vibe agents are **TOML**
  behavior profiles, not the same shape. A real port would require converting gald3r agent
  markdown into Vibe `.toml` profiles — **not currently done** by the parity pipeline.
- **Status**: ⚠️ — native agent system exists but uses an incompatible (TOML) format.

---

## 4. Skills Support

- **Native concept**: ✅ Yes — Vibe implements the **Agent Skills specification**, the *same*
  spec gald3r skills target. This is the second strongest parity point.
- **Discovery**: `~/.vibe/skills/<name>/SKILL.md` (user), `.vibe/skills/<name>/SKILL.md`
  (project), `.agents/skills/` (standard), plus custom `skill_paths` in `config.toml`.
- **Format**: folder-per-skill with `SKILL.md` YAML frontmatter. Verified frontmatter keys differ
  from gald3r's:
  ```yaml
  ---
  name: skill-name
  description: ...
  license: MIT
  compatibility: Python 3.12+
  user-invocable: true
  allowed-tools: [read_file, grep]
  ---
  ```
- **Capabilities**: skills can add **new tools, slash commands, and behaviors** — this is how
  slash commands enter Vibe (see §5).
- **Management**: `enabled_skills` / `disabled_skills` glob patterns in `config.toml`.
- **gald3r gap**: gald3r's `SKILL.md` frontmatter (`subsystem_memberships`, `token_budget`,
  `crawl_max_age_days`) is a superset — Vibe ignores unknown keys but expects `allowed-tools` /
  `user-invocable` which gald3r skills do not currently emit. Folder-per-skill structure ✅
  matches; frontmatter would need light adaptation.
- **Status**: ✅ for the discovery/loading mechanism (same spec); ⚠️ on frontmatter parity.

---

## 5. Commands / Workflows

- **No standalone command-file format** equivalent to `.cursor/commands/g-*.md`.
- **Slash commands exist** (`/` autocompletion in the interactive TUI) but they are
  **skill-provided** — a skill registers slash commands; there is no flat directory of
  command `.md` files that Vibe scans the way Cursor scans `.cursor/commands/`.
- Community reports (Medium "Recreating a Claude command in Mistral Vibe", 2026-04) confirm the
  workaround is to **wrap a command as a skill** rather than drop a command file.
- **gald3r gap**: gald3r's 174 `g-*` command files do not map to a native Vibe command directory.
  Exposing them would require generating one skill per command (heavy) or relying on `AGENTS.md`
  to describe them as prompt patterns (lossy — no executable invocation).
- **Status**: ⚠️ — slash commands work, but only via the skill mechanism; no direct command-file
  parity.

---

## 6. Hooks System

- **Documented existence, undocumented format**: the configuration docs state that each trusted
  path "contributes its `AGENTS.md` and `.vibe/` configuration (tools, skills, agents, prompts,
  **hooks**) to the session." So `.vibe/` **does** contribute hooks — but the official docs do
  **not** publish a hook event list, file location, or wiring schema as of the 2026-05-26 scan.
- **No verified event taxonomy**: there is no confirmed `sessionStart` / `stop` /
  `beforeShellExecution` / `preToolUse` mapping comparable to Cursor's `hooks.json`. Tool
  *permissions* (`[tools.bash] permission = "always"`) and agent `safety` levels cover some of
  the same ground Cursor uses hooks for, but they are not an event-hook system.
- **gald3r gap**: gald3r's PowerShell hooks (`g-hk-*.ps1` + `hooks.json` wiring) have **no
  verified target** on Vibe. Until Mistral publishes the hook schema, gald3r hooks cannot be
  ported.
- **Status**: ❓ → recorded as ⚠️ (mechanism referenced in docs but unspecified; cannot wire
  gald3r hooks without the schema). **Do not fabricate a hooks.json equivalent.**

---

## 7. Rules / Memory

- **No `.mdc` rules directory** and **no always-apply rule auto-loader** like Cursor's
  `.cursor/rules/*.mdc`.
- **Rules mechanism = `AGENTS.md`** (§2): persistent project instructions are injected via
  `AGENTS.md` resolution. This is closer to a single layered-instruction file than to scoped,
  glob-targeted rule files.
- **Memory**: Le Chat (the chat product) has a "Memories" feature (2026 release), but that is the
  **chat surface**, not Vibe CLI project config — not a gald3r file target.
- **Custom system prompt**: `~/.vibe/prompts/<id>.md` referenced via `system_prompt_id` in
  `config.toml` replaces the default system prompt — another instruction-injection lever.
- **gald3r gap**: gald3r's 38 scoped `g-rl-*` rules (alwaysApply/globs/on-demand) collapse into a
  single `AGENTS.md` blob on Vibe — no per-file `globs` scoping, no per-rule on-demand loading.
- **Status**: ⚠️ — instruction injection works via `AGENTS.md` + custom prompt, but there is no
  scoped/glob rule system.

---

## 8. MCP Support

- **Supported**: ✅ Yes (Vibe CLI). Configured in `.vibe/config.toml`:
  ```toml
  [[mcp_servers]]
  name = "my_http_server"
  transport = "http"            # http transport verified; stdio likely but unconfirmed here
  url = "http://localhost:8000"
  headers = { "Authorization" = "Bearer my_token" }
  api_key_env = "MY_API_KEY_ENV_VAR"
  startup_timeout_sec = 15
  tool_timeout_sec = 120
  env = { "DEBUG" = "1" }
  ```
- **Tool filtering**: `enabled_tools` / `disabled_tools` (e.g. `disabled_tools = ["mcp_*"]`)
  gate MCP-provided tools.
- **Le Chat MCP connectors**: separately, **Le Chat** supports MCP connectors invoked via
  `/Connector_Name` (2026 release) — but that is the chat product's connector store, not a
  file-config surface and not a gald3r target.
- **Status**: ✅ verified config mechanism for Vibe CLI (TOML `[[mcp_servers]]`).

---

## 9. Known Gaps vs. Cursor Reference

| # | Gap | Severity |
|---|---|---|
| 1 | **Three products, one config-driven** — only Vibe CLI reads config files. Mistral Code (IDE plugin) and Le Chat are not gald3r config targets. | High (scope) |
| 2 | **Hooks schema unpublished** — `.vibe/` "contributes hooks" per docs, but no event list / file format. gald3r hooks **cannot** be ported. (§6) | High |
| 3 | **No command-file directory** — slash commands are skill-provided only; gald3r's 174 command files have no native landing zone. (§5) | High |
| 4 | **No scoped/glob rules** — `.cursor/rules/*.mdc` collapses into a single `AGENTS.md` blob; no per-rule `globs` or on-demand loading. (§7) | Medium |
| 5 | **Agent format mismatch** — Vibe agents are TOML behavior profiles; gald3r agents are markdown. No automatic conversion. (§3) | Medium |
| 6 | **Skill frontmatter mismatch** — folder-per-skill ✅ matches, but Vibe expects `allowed-tools` / `user-invocable`; gald3r skills emit `subsystem_memberships` / `token_budget`. Light adaptation needed. (§4) | Low |
| 7 | **Config is TOML, not YAML** — prior SKILL.md fabricated a `.mistral/config.yaml`; the real surface is `.vibe/config.toml`. Corrected in this spec. | (corrected) |
| 8 | **Parity pipeline does NOT target `.vibe/`** — `platform_parity_sync.ps1` currently has no `.vibe/` writer. Any real install support is future work (not done by T1478). | Medium |

**Strongest parity points** (not gaps): `AGENTS.md` is consumed directly (✅), and the Agent
Skills `SKILL.md` folder-per-skill convention is shared (✅).

---

## Capability Summary (copy into PLATFORM_STATUS.md row)

| Hooks | Rules | Skills | Commands | MCP | Docs Fresh |
|---|---|---|---|---|---|
| ⚠️ | ⚠️ | ✅ | ⚠️ | ✅ | ✅ |

Legend: ✅ verified working · ⚠️ partial / format-mismatch · ❌ not supported · ❓ untested.

- **Hooks ⚠️**: docs reference `.vibe/` hooks but publish no schema — cannot wire gald3r hooks.
- **Rules ⚠️**: `AGENTS.md` injection only; no scoped `.mdc` rule system.
- **Skills ✅**: native Agent Skills spec, folder-per-skill `SKILL.md` (frontmatter needs light adaptation).
- **Commands ⚠️**: slash commands exist but only via the skill mechanism; no command-file dir.
- **MCP ✅**: `.vibe/config.toml` `[[mcp_servers]]` (Vibe CLI); Le Chat connectors separately.
- **Docs Fresh ✅**: doc scan performed 2026-05-26 (docs.mistral.ai + GitHub README).

---

## Verification Evidence

| Capability | How verified |
|---|---|
| `.vibe/` + `config.toml` (not `.mistral/`/YAML) | docs.mistral.ai/mistral-vibe/terminal/configuration; GitHub mistralai/mistral-vibe README (2026-05-26 scan) |
| `AGENTS.md` instruction file + resolution order | configuration docs + GitHub README ("AGENTS.md files closer to cwd override") |
| Agents/subagents TOML profiles | docs.mistral.ai/mistral-vibe/agents-skills (`safety`, `auto_approve`, `agent_type=subagent`) |
| Skills (Agent Skills spec, SKILL.md) | agents-skills docs (`~/.vibe/skills/<name>/SKILL.md`, `enabled_skills` globs) |
| Slash commands = skill-provided | agents-skills docs ("skills can add new tools, slash commands"); Medium 2026-04 community report |
| Hooks referenced but unspecified | configuration docs (".vibe/ configuration (tools, skills, agents, prompts, hooks)") — no schema published |
| MCP `[[mcp_servers]]` TOML | configuration docs (full `[[mcp_servers]]` example with transport/url/headers/timeouts) |
| Le Chat MCP connectors (separate surface) | docs.mistral.ai/le-chat/.../mcp-connectors; mistral.ai/news/le-chat-mcp-connectors-memories |
| Mistral Code = closed IDE plugin | mistral.ai/news/mistral-code; help.mistral.ai JetBrains plugin article |
| No `.vibe/` writer in parity pipeline | Verified absence — `platform_parity_sync.ps1` targets `.cursor/`/`.claude/` family, not `.vibe/` |
