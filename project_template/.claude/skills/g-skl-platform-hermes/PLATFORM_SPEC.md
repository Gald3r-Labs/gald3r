---
subsystem_memberships: [PLATFORM_INTEGRATION]
platform: hermes
authoring_path: update
docs_url: https://hermes-agent.nousresearch.com/docs
docs_url_secondary:
  - https://hermes-agent.nousresearch.com/docs/user-guide/configuration
  - https://hermes-agent.nousresearch.com/docs/user-guide/features/skills
  - https://hermes-agent.nousresearch.com/docs/developer-guide/creating-skills
  - https://hermes-agent.nousresearch.com/docs/user-guide/features/hooks
  - https://github.com/NousResearch/hermes-agent/blob/main/website/docs/user-guide/features/hooks.md
  - https://hermes-agent.nousresearch.com/docs/user-guide/features/mcp
  - https://github.com/NousResearch/hermes-agent/blob/main/website/docs/reference/mcp-config-reference.md
  - https://github.com/NousResearch/hermes-agent
crawl_max_age_days: 14
vault_doc_path: research/platforms/hermes/
last_doc_scan: 2026-06-20
reference: g-skl-platform-cursor
status: ✅
task: T614
---

# PLATFORM_SPEC.md — Hermes Agent (Nous Research)

**Hermes Agent** is Nous Research's self-improving, channel-native AI agent — a CLI plus a
multi-platform **gateway** (Telegram, Discord, Slack, WhatsApp, Signal, Email). Its headline traits
are an autonomous learning loop, **agent-curated Skills** created from experience, and persistent
memory across sessions. All state lives under **`~/.hermes/`** (or `$HERMES_HOME`;
`%LOCALAPPDATA%\hermes` on native Windows). As of **June 2026** Hermes natively supports **five** of
the six gald3r-relevant primitives — **Skills** (agentskills.io-compatible `SKILL.md`), **Rules /
instruction files** (it auto-loads `AGENTS.md` / `CLAUDE.md` / `SOUL.md` into the system prompt),
**MCP**, **Hooks** (a native shell-hook block in `config.yaml` with 17+ lifecycle events, plus gateway
+ plugin hook systems), and native **subagents** (the `delegate_task` model). **Commands** are the
only partial primitive (built-in slash commands + skills-as-`/skill-name`; no user-authored non-skill
command file). This is **near-full parity** with the Cursor reference.

**Authoring path**: UPDATE. **Verified 2026-06-20** against the live GitHub repo + hosted docs (see
Verification Evidence). This **supersedes** the T516 stub (`last_doc_scan: never`, `status: ❓`, all
cells `❓`, wrong `docs_url: https://hermes.dev`), which made no capability claims. The correct docs
host is **`hermes-agent.nousresearch.com/docs`** + the **`NousResearch/hermes-agent`** GitHub repo.

> **Correction (2026-06-20 re-verify):** an earlier pass of this spec claimed Hooks were "not
> documented (the one real gap)" and told users to fold SessionStart guardrails into `AGENTS.md`
> because there was no hook. **That was wrong.** Hermes ships a **native hooks system** —
> documented at `…/docs/user-guide/features/hooks` — including a **shell-hook block in
> `~/.hermes/config.yaml`** with **17+ lifecycle events** and **`pre_tool_call` tool-call blocking**.
> The Hooks cell is now **✅ NATIVE** and the tier is re-derived to near-full parity (see below).

> **Distribution opportunity (headline):** Hermes Skills use the **agentskills.io open `SKILL.md`
> standard** in a **folder-per-skill** layout (`<skill>/SKILL.md` + optional scripts/references) —
> the **same standard gald3r already ships** (`g-skl-*/SKILL.md`). gald3r's skills are **structurally
> portable** onto Hermes: drop them under `~/.hermes/skills/<category>/<name>/SKILL.md` and they
> appear in the skills index and as `/<name>` slash commands. Hermes adds **optional** `metadata.hermes.*`
> frontmatter fields (tags, requires_toolsets, config, …) on top of the `name`/`description` baseline,
> so a baseline `SKILL.md` loads unchanged; only Hermes-specific tuning needs the extra keys.

> **Platform truth — instruction file:** Hermes auto-injects a set of context files into the system
> prompt at session start — **`SOUL.md`, `.hermes.md`, `AGENTS.md`, `CLAUDE.md`, and `.cursorrules`**.
> gald3r's `AGENTS.md` is therefore read **natively** (no migration step required), which makes Hermes
> an `AGENTS.md`-first-class platform like Codex/Cursor — not a `CLAUDE.md`-only platform like Claude
> Code. `SOUL.md` is the persona slot (#1 in the system prompt).

---

## 1. Folder Hierarchy

```
~/.hermes/                          ← all state (or $HERMES_HOME; %LOCALAPPDATA%\hermes on Windows)
├── config.yaml                     ← main config (model, toolsets, memory, compression, MCP)
├── .env                            ← secrets only (API keys, bot tokens, passwords)
├── auth.json                       ← OAuth provider creds (Nous Portal, etc.)
├── SOUL.md                         ← persona / agent identity (system-prompt slot #1, auto-loaded)
├── memories/
│   ├── MEMORY.md                   ← session memories (auto-loaded)
│   └── USER.md                     ← user profile (auto-loaded)
├── skills/                         ← Agent Skills, organized by category
│   ├── <category>/<name>/SKILL.md  ←   e.g. devops/deploy-k8s/SKILL.md, research/arxiv/SKILL.md
│   └── openclaw-imports/           ←   skills migrated from OpenClaw
└── hermes-agent/                   ← git checkout (source install)

<project-root>/                     ← project-local context files Hermes auto-injects (if present)
├── AGENTS.md                       ← auto-loaded into system prompt (NATIVE — no migration needed)
├── .hermes.md / CLAUDE.md / .cursorrules  ← also auto-injected context files
```

Hermes resolves a **bundled** skills set (in the repo `skills/`) plus an **optional** set
(`optional-skills/`, same structure) and the user `~/.hermes/skills/` tree. **External skills** added
as *taps* (`hermes skills tap add owner/repo`) appear in the index identically to local skills.

**gald3r writes**: project `AGENTS.md`; skills under `~/.hermes/skills/<category>/g-skl-*/SKILL.md`
(user-global) or a project skills tree published as a tap; optionally `SOUL.md` for persona.
**Hermes owns**: `config.yaml` / `.env` / `auth.json` schemas, the `~/.hermes/` memory store, the
skill index + security scanning, and gateway state.

---

## 2. AI Instruction File — ✅ NATIVE (AGENTS.md auto-loaded)

Hermes auto-injects **automatic context files** into the system prompt at session start:
**`SOUL.md`, `.hermes.md`, `AGENTS.md`, `CLAUDE.md`, and `.cursorrules`**. gald3r's shared
cross-platform **`AGENTS.md` is read natively** — no `CLAUDE.md` import shim and no migration command
required (this corrects the README's "migration flag" phrasing, which refers to *importing OpenClaw
state*, not to whether `AGENTS.md` is read). `SOUL.md` is the dedicated **persona** slot (#1).
Context files are subject to truncation limits (`config.yaml` memory settings).
Source: https://github.com/NousResearch/hermes-agent/blob/main/website/docs/user-guide/configuration.md

---

## 3. Agents Support — ✅ NATIVE (subagents via `delegate_task`)

- Hermes spawns subagents through the documented **`delegate_task`** tool (`tools/delegate_tool.py`):
  it creates a subagent with an **isolated context + terminal session**, and the parent waits
  synchronously for the child's summary before continuing its loop. **Single** mode passes `goal`
  (+ optional `context`, `toolsets`); **batch/parallel** mode passes **`tasks: [...]`**, each
  task getting its own concurrent subagent.
- Concurrency and depth are bounded in `config.yaml`: **`delegation.max_concurrent_children`**
  (default 3), **`delegation.max_spawn_depth`** (default 2), plus `delegation.child_timeout_seconds`,
  `delegation.orchestrator_enabled` (default true), and `delegation.inherit_mcp_toolsets`. Subagents
  carry a **role**: `leaf` (default focused worker, cannot itself call `delegate_task`) or
  `orchestrator` (retains `delegate_task`).
- No documented standalone *agent-definition file* (no `.hermes/agents/*.md|toml`) — subagents are
  **spawned on demand via `delegate_task`**, not declared as gald3r-style `g-agnt-*` markdown files.
  gald3r `g-agnt-*` definitions have **no direct file mapping**; their behavior is best delivered as
  **Skills** (which a `delegate_task` subagent can invoke) rather than as declared agent files.
- Sources: https://github.com/NousResearch/hermes-agent/blob/main/AGENTS.md (`delegate_task` /
  `delegation.*` config) · https://github.com/NousResearch/hermes-agent (README — subagents)

## 4. Skills Support — ✅ NATIVE (agentskills.io standard) — **gald3r distribution opportunity**

- **A skill is a directory containing a `SKILL.md`** with YAML frontmatter — the **agentskills.io
  open standard** (folder-per-skill, optional `scripts/` `references/` `assets/`). Hermes loads skill
  bodies **on demand** (progressive disclosure), keeping token use low; names+descriptions index at
  startup.
- **Location**: `~/.hermes/skills/<category>/<name>/SKILL.md` (user), bundled `skills/` (repo),
  `optional-skills/` (same structure). External taps (`hermes skills tap add owner/repo`) merge in.
- **Frontmatter**: only **`name` + `description` are required** (matching the agentskills.io
  baseline). `version`, `author`, `license` are **optional / recommended** (best-practice for
  published/tapped skills, not mandatory to load). Also optional: `platforms`,
  `metadata.hermes.{tags,related_skills,requires_toolsets,requires_tools,fallback_for_*,config,
  blueprint}`, `required_environment_variables`, `required_credential_files`. A gald3r baseline
  `g-skl-*/SKILL.md` (which already carries `name`+`description`) therefore **loads as-is**; adding
  `version`/`author`/`license` is recommended polish for distribution, not a requirement.
- **Invocation**: every skill is exposed as a `/skill-name` slash command and via the system-prompt
  `skills_list` / `skill_view` index — **identical for local, optional, and tapped skills**.
- **Publishing**: `hermes skills publish skills/my-skill --to github --repo owner/repo`; consumers add
  with `hermes skills tap add owner/repo`. Hub-installed skills are **security-scanned** before use.
- **gald3r impact**: `g-skl-*/SKILL.md` are **directly portable** (same folder-per-skill + `SKILL.md`
  standard already used by Claude/Codex/OpenCode/Cursor). A gald3r **tap** (`hermes skills tap add
  <gald3r-skills-repo>`) is the natural distribution channel onto Hermes.
- Sources: https://hermes-agent.nousresearch.com/docs/user-guide/features/skills ·
  https://hermes-agent.nousresearch.com/docs/developer-guide/creating-skills ·
  https://github.com/NousResearch/hermes-agent/blob/main/skills/research/arxiv/SKILL.md (live example)

## 5. Commands / Workflows — ⚠️ PARTIAL (built-in slash commands + skills-as-commands)

- **Built-in slash commands** (CLI + messaging): `/new`, `/reset`, `/model [provider:model]`,
  `/personality [name]`, `/retry`, `/undo`, `/compress`, `/usage`, `/insights [--days N]`, `/skills`,
  `/stop`, `/platforms`, `/status`, `/sethome`.
- **User-defined invocable workflows** are delivered as **Skills** — each skill is automatically a
  `/skill-name` command. There is **no separate user-authored command file** (no `.hermes/commands/`,
  no prompt-template directory).
- **gald3r impact**: `@g-*` / `/g-*` workflows map to **Skills** (preferred and only) path — they
  surface as `/<name>` once installed as skills. No 1:1 command-file analog → mark **⚠️ partial**
  (works, but only via the skills route, not a dedicated command primitive).
- Source: https://github.com/NousResearch/hermes-agent (README — slash command list) + skills docs

## 6. Hooks System — ✅ NATIVE (config.yaml `hooks:` shell hooks, 17+ events, blocking)

- **Hermes ships a native hooks system** — three coordinated subsystems: **shell hooks** (declared in
  `~/.hermes/config.yaml` under a `hooks:` block), **gateway hooks** (`~/.hermes/hooks/<name>/` with
  `HOOK.yaml` + `handler.py`), and **plugin hooks** (`ctx.register_hook()` in a plugin's `register()`).
  For gald3r, the **shell-hook block** is the relevant surface.
- **Shell-hook config** (`~/.hermes/config.yaml`):
  ```yaml
  hooks:
    pre_tool_call:
      - matcher: "terminal"          # regex against tool name
        command: "/path/to/guard.sh" # receives JSON payload on stdin
        timeout: 10                   # seconds
  ```
- **Payload**: JSON over **stdin**, e.g.
  `{"hook_event_name":"pre_tool_call","tool_name":"terminal","tool_input":{...},"session_id":"…","cwd":"…"}`.
- **17+ lifecycle events**: `pre_tool_call`, `post_tool_call`, `pre_llm_call`, `post_llm_call`,
  `on_session_start`, `on_session_end`, `on_session_finalize`, `on_session_reset`, `subagent_stop`,
  `pre_gateway_dispatch`, `pre_approval_request`, `post_approval_response`, `transform_tool_result`,
  `transform_terminal_output`, `transform_llm_output`, plus gateway-only events `gateway:startup`,
  `session:start`/`:end`/`:reset`, `agent:start`/`:step`/`:end`, and `command:*` (wildcard per slash
  command).
- **Tool-call blocking**: only **`pre_tool_call`** can block — return `{"action":"block","message":"…"}`
  (equivalently `{"decision":"block","reason":"…"}`) and Hermes short-circuits the tool, returning
  `message` to the model as the tool error. This is a **real PreToolUse-equivalent gate**.
- **Reliability caveat (honest):** all hook subsystems are **non-blocking on error** — malformed JSON,
  non-zero exit, or timeout in a shell hook is **caught and logged, never aborting the agent loop**.
  So a hook that *fails* (vs. one that explicitly returns `block`) does **not** halt the tool; a
  guardrail must succeed and explicitly emit the block action to enforce. (Community issues also
  report hooks not always firing in some builds — treat hard enforcement as best-effort and verify
  with an install test.)
- **gald3r impact**: `g-hk-*.ps1` lifecycle hooks **do map** onto Hermes via the `config.yaml`
  `hooks:` block — wire a SessionStart-style `.gald3r/` context injector onto **`on_session_start`**
  and a PreToolUse-style guardrail onto **`pre_tool_call`** (returning the `block` action for hard
  gating). Because Hermes shell hooks run an arbitrary command, point them at a small shell wrapper
  that invokes the gald3r hook logic (PowerShell via `pwsh` or a `.sh` shim). Folding guardrails into
  `AGENTS.md` (§2) remains a useful belt-and-suspenders layer, but is **no longer the only option** —
  native `pre_tool_call` blocking is available.
- Sources: https://hermes-agent.nousresearch.com/docs/user-guide/features/hooks ·
  https://github.com/NousResearch/hermes-agent/blob/main/website/docs/user-guide/features/hooks.md

## 7. Rules / Memory — ✅ NATIVE

- **Rules/instructions**: carried by the auto-loaded context files (`AGENTS.md`, `SOUL.md`,
  `.hermes.md`, `CLAUDE.md`, `.cursorrules` — §2). gald3r `g-rl-*` always-apply rules fold into
  `AGENTS.md` and load natively each session.
- **Memory**: persistent **`~/.hermes/memories/MEMORY.md`** + **`USER.md`**, auto-loaded; plus the
  self-improving loop that **writes new skills** from experience. Memory limits / context truncation
  are tuned in `config.yaml`.
- **Enforcement caveat (platform truth):** like every prose-instruction surface, `AGENTS.md`/`SOUL.md`
  are **advisory context, not hard enforcement** on their own. Unlike the earlier (incorrect)
  assessment, Hermes **does** have a `pre_tool_call` hook (§6) that can upgrade a constraint to a
  hard, blocking gate — but the hook must succeed and explicitly emit `{"action":"block",…}`, and
  hook errors are swallowed (non-blocking-on-failure). So treat prose constraints as best-effort, and
  add a `pre_tool_call` shell hook when a constraint must be hard-enforced.
- Source: https://github.com/NousResearch/hermes-agent/blob/main/website/docs/user-guide/configuration.md

## 8. MCP Support — ✅ NATIVE

- **Model Context Protocol client** — **"connect any MCP server for extended capabilities."** Config
  lives under the **`mcp_servers:`** key (YAML, in `config.yaml`): per-server **stdio** (`command`,
  `args`, `env`) **or HTTP** (`url`, `headers`), plus `enabled`, `timeout`, `connect_timeout`, and
  tool-filtering / utility-tool-policy options.
- MCP ships with the standard install; the optional extra is `uv pip install -e ".[mcp]"`. **Node.js /
  npx required** for npm-based MCP servers.
- gald3r MCP servers (e.g. `gald3r_docker` stdio/HTTP tools) wire via `mcp_servers:` in
  `~/.hermes/config.yaml`.
- Sources: https://github.com/NousResearch/hermes-agent/blob/main/website/docs/reference/mcp-config-reference.md ·
  https://hermes-agent.nousresearch.com/docs/user-guide/features/mcp

## 9. Gateways / Surfaces — channel-native multi-platform

- **Gateway**: `hermes gateway setup` (interactive wizard) + `hermes gateway start` / `run` /
  `install`. Surfaces: **Telegram, Discord, Slack, WhatsApp, Signal, Email** ("20+ platforms" claimed),
  with streaming tool output and cross-platform conversation continuity.
- **gald3r impact (Q5):** gald3r's status outputs (`TASKS.md`, `/g-status`) are **markdown**, which
  renders fine in CLI and degrades acceptably in chat surfaces (Telegram/Slack render a markdown
  subset; long tables truncate). For chat gateways, prefer the **summarized** status forms over raw
  `TASKS.md` table dumps; the `--json`/`--toon` output skills (g-skl-json-output / g-skl-toon-output)
  are better suited to gateway/agent-to-agent handoff than wide markdown tables. **No hard
  reformatting is required for CLI**; chat surfaces benefit from summarization.
- Source: https://github.com/NousResearch/hermes-agent (README — gateway) + gateway docs

---

## Parity vs. Cursor Reference

Hermes reaches **near-full parity** with the Cursor reference (`g-skl-platform-cursor`): native
**Skills, Rules/memory, MCP, and Hooks**, plus native subagents (the `delegate_task` model) and an
`AGENTS.md`-native instruction file. **Commands are the only partial primitive** (skills-as-commands
only, no separate command-file primitive). Hermes's distinctive strengths are the
**agentskills.io-standard Skills** (directly reusing gald3r's `SKILL.md` artifacts), the
**self-improving skill-creation loop**, and the **channel-native gateway** (Telegram/Discord/Slack/…).

**Platform-specific truths to honor:**
- Instruction file is **`AGENTS.md`-native** (auto-injected alongside `SOUL.md`/`CLAUDE.md`/
  `.cursorrules`) — ship `AGENTS.md`; optionally add `SOUL.md` for the gald3r persona.
- **Hooks are native** — wire `g-hk-*` SessionStart/PreToolUse logic onto the `config.yaml` `hooks:`
  block (`on_session_start`, `pre_tool_call`, …); `pre_tool_call` can hard-**block** a tool via
  `{"action":"block",…}`. Hook *failures* are swallowed (non-blocking-on-error), so a guardrail must
  succeed and explicitly emit the block action to enforce.
- Skills need only `name`+`description`; `version`/`author`/`license` are **optional/recommended**
  (a baseline gald3r `SKILL.md` loads as-is — adding the three is distribution polish).
- Distribute gald3r skills as a **tap** (`hermes skills tap add owner/repo`); state lives in
  `~/.hermes/` (`config.yaml` + `.env`, **not** a `.hermes/` project tree).

## Hook System

- **Type**: ✅ native — shell hooks (`config.yaml` `hooks:` block) + gateway hooks
  (`~/.hermes/hooks/<name>/` `HOOK.yaml`+`handler.py`) + plugin hooks (`ctx.register_hook()`)
- **Config file**: `~/.hermes/config.yaml` (shell hooks, under `hooks:`)
- **Events available**: 17+ — incl. `pre_tool_call`, `post_tool_call`, `pre_llm_call`,
  `post_llm_call`, `on_session_start`, `on_session_end`, `on_session_finalize`, `on_session_reset`,
  `subagent_stop`, `transform_*`, plus gateway `session:*`/`agent:*`/`command:*`
- **Event payload format**: JSON over **stdin** (`hook_event_name`, `tool_name`, `tool_input`,
  `session_id`, `cwd`, …)
- **Blocking**: `pre_tool_call` may return `{"action":"block","message":"…"}` to short-circuit a tool
- **Reliability caveat**: hooks are **non-blocking on error** — a failing hook is logged, not enforced;
  only an explicit `block` action gates a tool (verify firing with an install test)
- **gald3r hook files**: `g-hk-*.ps1` **map natively** — wire SessionStart logic onto
  `on_session_start` and PreToolUse logic onto `pre_tool_call` via a shell wrapper (`pwsh`/`.sh` shim)

## Atypical Handling

- **No `.hermes/` project config tree** — all state is **user-global** under `~/.hermes/`
  (`config.yaml` + `.env` + `auth.json` + `skills/` + `memories/`). Project-local influence is via the
  auto-injected context files (`AGENTS.md`/`.hermes.md`/`CLAUDE.md`/`.cursorrules`) only.
- **Skills ARE the command system** — there is no separate command-file primitive; every skill is a
  `/skill-name`. Distribute and update via **taps** + `hermes skills publish/tap add`.
- **Lean skill frontmatter** — only `name`+`description` are required (agentskills.io baseline);
  `version`/`author`/`license`/`platforms`/`metadata.hermes.*` are optional/recommended.
- **Hooks live in `config.yaml`** — not in a per-IDE hooks directory; the gald3r `g-hk-*` logic is
  wired via the `hooks:` block (shell command + JSON-stdin), with `pre_tool_call` blocking.
  Deterministic control is via **hooks + `delegate_task` subagents**.
- **Gateway-first** — the same agent runs in Telegram/Discord/Slack/WhatsApp/Signal/Email; prefer
  summarized status output (or `--json`/`--toon`) over wide markdown tables in chat surfaces.

## gald3r Integration Notes

- **Ship `AGENTS.md`** as the instruction surface — Hermes auto-injects it (no `CLAUDE.md` shim, no
  migration step). Fold `g-rl-*` always-apply rules into it.
- **Wire `g-hk-*` hooks via `config.yaml`**: map SessionStart `.gald3r/` injection onto
  `on_session_start` and PreToolUse guardrails onto `pre_tool_call` (return `{"action":"block",…}` to
  hard-gate). Use a shell wrapper (`pwsh`/`.sh`) to invoke the gald3r hook logic; remember hook
  *failures* are swallowed, so the guardrail must succeed and emit the block action to enforce.
- **Distribute gald3r Skills as a Hermes tap**: publish `g-skl-*/SKILL.md` to a repo, then
  `hermes skills tap add <repo>`; they index + surface as `/<name>` natively. A baseline `SKILL.md`
  (`name`+`description`) loads as-is; `version`/`author`/`license` are optional distribution polish.
- **MCP** wires via `mcp_servers:` in `~/.hermes/config.yaml` (stdio/HTTP).
- **Subagents** spawn via `delegate_task` (`goal`/`tasks:[...]`, bounded by `delegation.*`); there are
  **no declared subagent files** — deliver `g-agnt-*` behaviors as Skills.
- **Do NOT expect**: a `.hermes/` project tree or declared subagent/agent files.
- Re-verify on the next `@g-platform-scan-docs hermes` (crawl_max_age_days: 14;
  docs `https://hermes-agent.nousresearch.com/docs` + `github.com/NousResearch/hermes-agent`).

---

## Capability Summary (copy into PLATFORM_STATUS.md row)

| Hooks | Rules | Skills | Commands | MCP | Docs Fresh |
|---|---|---|---|---|---|
| ✅ | ✅ | ✅ | ⚠️ | ✅ | ✅ |

Legend: ✅ verified working · ⚠️ partial / Cursor-generic · ❌ not supported · ❓ untested.

Overall platform `status: ✅` — **near-full parity** (T614). Five of six primitives native —
Hooks/Rules/Skills/MCP (+ `delegate_task` subagents, `AGENTS.md`-native instruction file); **Commands**
is the only partial primitive (skills-as-`/skill-name`, no command-file). This corrects an earlier
pass that wrongly marked Hooks absent. Honest, re-verified state as of the 2026-06-20 live docs crawl
(hooks + skills-frontmatter facts re-fetched).

---

## Verification Evidence (live crawl 2026-06-20)

| Capability | How verified | Source |
|---|---|---|
| Instruction file | Auto-loaded context files incl. `AGENTS.md`/`SOUL.md`/`CLAUDE.md`/`.cursorrules` injected into system prompt at start; `SOUL.md` = persona slot #1 | github.com/NousResearch/hermes-agent .../user-guide/configuration.md |
| Skills | Folder-per-skill `SKILL.md` (agentskills.io), `~/.hermes/skills/<cat>/<name>/`; on-demand load; `/skill-name`; taps; security-scanned | hermes-agent.nousresearch.com/docs/user-guide/features/skills + /developer-guide/creating-skills |
| Skill frontmatter | **only `name`+`description` required**; `version`/`author`/`license`/`platforms`/`metadata.hermes.*` optional/recommended | hermes-agent.nousresearch.com/docs/developer-guide/creating-skills + /user-guide/features/skills (re-fetched 2026-06-20) |
| Commands | built-in slash set (`/new`,`/model`,`/skills`,`/personality`,…) + every skill = `/skill-name`; no user command-file primitive | github.com/NousResearch/hermes-agent (README slash-command list) |
| Agents | `delegate_task` tool (isolated context+terminal; `goal` or batch `tasks:[...]` concurrent); config `delegation.max_concurrent_children`/`max_spawn_depth`; roles leaf/orchestrator; no declared agent file | github.com/NousResearch/hermes-agent/blob/main/AGENTS.md |
| Hooks | **Native**: `config.yaml` `hooks:` shell hooks (JSON-stdin) + gateway + plugin hooks; 17+ events; `pre_tool_call` blocks via `{"action":"block",…}`; non-blocking on hook error | hermes-agent.nousresearch.com/docs/user-guide/features/hooks + .../website/docs/user-guide/features/hooks.md (re-fetched 2026-06-20) |
| Rules / Memory | `AGENTS.md`/`SOUL.md` rules (auto-injected) + `~/.hermes/memories/MEMORY.md`+`USER.md`; self-writes skills | .../user-guide/configuration.md |
| MCP | `mcp_servers:` (YAML, in config.yaml) — stdio (`command`/`args`/`env`) or HTTP (`url`/`headers`) + `enabled`/`timeout`; `.[mcp]` extra; npx for npm servers | .../reference/mcp-config-reference.md + /user-guide/features/mcp |
| Config files | `~/.hermes/config.yaml` (settings) + `~/.hermes/.env` (secrets) + `auth.json`; `$HERMES_HOME`/`%LOCALAPPDATA%\hermes` | .../user-guide/configuration.md + README |
| Gateways | `hermes gateway setup`/`start`; Telegram/Discord/Slack/WhatsApp/Signal/Email | github.com/NousResearch/hermes-agent (README) |
| Docs host | Correct host is `hermes-agent.nousresearch.com/docs` + `github.com/NousResearch/hermes-agent` (stub's `https://hermes.dev` was wrong) | live fetch 2026-06-20 |
