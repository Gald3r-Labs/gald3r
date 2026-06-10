---
subsystem_memberships: [PLATFORM_INTEGRATION]
platform: astrbot
authoring_path: rewrite
docs_url: https://docs.astrbot.app/en/what-is-astrbot.html
docs_url_secondary:
  - https://docs.astrbot.app/en/dev/star/guides/listen-message-event.html
  - https://github.com/AstrBotDevs/AstrBot/wiki/en-use-custom-rules
  - https://docs.astrbot.app/en/use/agent-runner.html
  - https://docs.astrbot.app/en/use/skills.html
  - https://docs.astrbot.app/use/mcp.html
crawl_max_age_days: 14
vault_doc_path: research/platforms/astrbot/
last_doc_scan: 2026-06-02
reference: g-skl-platform-cursor
status: ⚠️
task: T1474
---

# PLATFORM_SPEC.md — AstrBot (AstrBotDevs Agentic IM Assistant)

AstrBot is an open-source, all-in-one **Agentic AI assistant and development framework** for
personal and group chats — it connects many IM platforms (QQ, Telegram, WeCom, Lark, DingTalk,
Slack, Discord, etc.) to LLMs, with a built-in **Agent Runner**, a **Star** plugin system, MCP, a
knowledge base, web search, and long-term memory. As of mid-2026 AstrBot's extension surface
natively exposes **all six** gald3r-relevant mechanisms — commands, rules (personas), agents,
skills, hooks, and MCP — but they target an **IM-chat runtime**, not a repo/file workflow.

**Authoring path**: REWRITE (created from a stale prior note). **Verified 2026-06-02** against
https://docs.astrbot.app (see Verification Evidence). This **supersedes** the prior skill note,
which (a) misattributed AstrBot to the "Nous Research community" — it is in fact maintained by the
**AstrBotDevs** open-source org under **AGPL-v3** — and (b) marked rules/hooks as ⚠️ partial when
both are now NATIVE plugin/runtime mechanisms.

> **Critical gald3r-fit caveat (why overall status is ⚠️, not ✅):** AstrBot is an **IM
> chatbot/agent runtime, NOT a code-editor/IDE coding agent**. Its command/hook/skill/MCP
> extension points are real and native, but gald3r's **file-first model** (`.gald3r/`,
> `AGENTS.md`/`CLAUDE.md`, git/pre-commit hooks) does **not** map onto AstrBot natively — there is
> **no repo instruction-file convention**, and its "hooks" are **LLM / message-pipeline runtime
> events**, not filesystem/VCS events. Skills are the one clean drop-in: gald3r `SKILL.md`
> packages are directly adoptable IF zipped and uploaded via the WebUI (admin-gated).

---

## 1. Folder Hierarchy

AstrBot has **no project-root config tree** like an IDE coding agent. Extensibility lives inside
**Star plugin packages** plus the WebUI / config / DB. There is **no `.astrbot/` repo namespace**
that gald3r writes.

```
<astrbot-data-dir>/              ← server data dir (Docker: mounted volume)
├── cmd_config.json              ← runtime config (providers, personas, etc.)
├── (DB-stored personas / rules / memory)
└── plugins/  (Star packages)
    └── <plugin-name>/           ← a "Star" plugin
        ├── metadata.yaml        ← plugin id/name/version/author (NOT an agent instruction file)
        ├── main.py              ← @register Star class; @filter.* command + lifecycle hooks
        ├── requirements.txt
        └── skills/              ← (optional) bundled Anthropic Skill folders
            └── <name>/SKILL.md
```

Skills may **also** be uploaded standalone as a `.zip` via **WebUI > Plugins > Skills** (no plugin
required).

**gald3r writes**: an AstrBot **Star plugin** (to bundle commands/hooks/skills) and/or a
standalone skill `.zip`.
**AstrBot owns**: the WebUI, `cmd_config.json`, the persona/rules/memory DB, the Agent Runner, and
the knowledge-base index — none are gald3r-writable repo files.

---

## 2. AI Instruction File — ❌ NONE (no AGENTS.md / CLAUDE.md convention)

AstrBot has **no repo-root instruction-file convention** — it does **not** read `AGENTS.md`,
`CLAUDE.md`, or `GEMINI.md`. It is a server/chatbot runtime configured through its **WebUI** and
config (`cmd_config.json` / DB-stored personas), not a project-file-driven coding agent. The
"always-on instruction" equivalent is the **Persona `system_prompt`** managed in the WebUI (see
§7). For plugin **development**, metadata lives in `metadata.yaml` / `requirements.txt` inside the
Star package — that is plugin manifest data, not an agent instruction file.

> gald3r's `AGENTS.md`/`CLAUDE.md` therefore have **no native loading path** on AstrBot. The
> closest mapping is to inject gald3r system instructions into a Persona `system_prompt`.

---

## 3. Agents Support — ✅ NATIVE

- **Agent Runner**: a powerful built-in runner doing **perceive → plan → execute → observe →
  re-plan** loops. Pluggable third-party runners: **Dify, Coze, Alibaba Bailian, DeerFlow**, or a
  custom runner.
- Docs feature list explicitly names **"SubAgent Orchestration"** — Sub-Agents, complex workflows,
  tool calls, and context management.
- gald3r `g-agnt-*` roles have **no 1:1 file mapping** (no `.agents/` tree); they would be realized
  as Agent-Runner behaviors / sub-agents, not dropped-in markdown.
- Source: https://docs.astrbot.app/en/use/agent-runner.html

## 4. Skills Support — ✅ NATIVE (cleanest gald3r drop-in)

- **Anthropic Skills (`SKILL.md`)**, added in **v4.13.0**. Uploaded as a **`.zip` containing a
  single Skill folder** via **WebUI > Plugins > Skills**, or **bundled inside a Star plugin's
  `skills/` directory**.
- Contents "should preferably follow the Anthropic Skills specification" — i.e. gald3r
  `g-skl-*/SKILL.md` load **as-is**.
- Two execution environments: **Local** (AstrBot runtime; admin-only trigger) and **Sandbox**
  (isolated) — prefer **Sandbox** for gald3r skills carrying scripts.
- Source: https://docs.astrbot.app/en/use/skills.html

## 5. Commands / Workflows — ✅ NATIVE

- **`@filter.command()`** / **`@filter.command_group()`** plugin decorators register slash-style
  commands; built-in admin commands also exist (e.g. `/persona`, `/help`). Supports **parameters,
  aliases** (`alias={...}`), and **priority**; command groups **nest** via
  `@filter.command_group()`.
- gald3r `@g-*` / `/g-*` commands map to `@filter.command()` registrations **inside a Star plugin**
  (no standalone `.md` command files).
- Source: https://docs.astrbot.app/en/dev/star/guides/listen-message-event.html

## 6. Hooks System — ✅ NATIVE (runtime IM/LLM events, NOT git/file hooks)

- **Plugin lifecycle / event hooks** via `@filter` decorators, with **priority ordering**. They
  cover framework lifecycle, the LLM request/response cycle, the agent loop, and the message
  pipeline:
  - `@filter.on_astrbot_loaded()`, `on_waiting_llm_request()`, **`on_llm_request()`** (modify
    `ProviderRequest`, incl. `system_prompt`), `on_llm_response()`, `on_decorating_result()`,
    `after_message_sent()`.
  - Agent-loop hooks **`on_agent_begin()`, `on_using_llm_tool()`, `on_llm_tool_respond()`,
    `on_agent_done()`** require **v4.23.1+**.
- **These are runtime IM/LLM-pipeline hooks, not git/file-watch dev hooks.** gald3r
  `g-hk-*.ps1` (SessionStart context injection, PreToolUse `.gald3r/` guards, pre-commit gates) have
  **no native analog** — AstrBot fires Python event handlers on chat/LLM events, not OS shell hooks
  on filesystem/VCS events.
- Source: https://docs.astrbot.app/en/dev/star/guides/listen-message-event.html

## 7. Rules / Memory — ✅ NATIVE (Persona system, NOT a repo rules file)

- **Persona system**: each persona has `id` / `name` / `description` / `system_prompt`, and the
  `system_prompt` is **injected as the first message in every LLM call**; switchable via
  **`/persona`**.
- **Custom Rules** (**v4.7.0**): per-`unified-message-origin` overrides — an admin can "configure a
  specific persona for this unified message origin."
- Built-in **long-term memory / affinity / self-learning / user profiling** so the agent adapts
  over time.
- All **Config / WebUI / DB-stored** — **not** a repo instruction file. gald3r `g-rl-*` rules have
  **no `.md` loading path**; the mapping is to fold rule content into a Persona `system_prompt`.
- Source: https://github.com/AstrBotDevs/AstrBot/wiki/en-use-custom-rules

## 8. MCP Support — ✅ NATIVE

- **MCP (Model Context Protocol) client**: connect external MCP servers to expose function tools to
  the agent; AstrBot can **also expose its own function tools over MCP**. Configured via the
  **WebUI**; Docker installs place MCP servers in the data dir; supports **env-var credential
  passing** (via the `env` command for API URLs / tokens). Example: `arxiv-mcp-server`.
- Source: https://docs.astrbot.app/use/mcp.html

## 9. Plugins ("Star") / Registry — distribution channel

- Extensions are **"Star" plugins** — a full dev framework (message events, configs, WebUI pages,
  i18n, AI integration) with a public registry at **plugins.astrbot.app**. A Star plugin can bundle
  **commands + lifecycle hooks + skills** together — **this is the natural distribution channel for
  a gald3r AstrBot package.**
- Built-in non-plugin capabilities also present: **knowledge base (RAG), web search, TTS/STT,
  Computer Use / Agent Sandbox.**

---

## Parity vs. Cursor Reference

On a **raw mechanism count**, AstrBot reaches all six (commands, rules, agents, skills, hooks, MCP)
that the Cursor reference (`g-skl-platform-cursor`) defines — so the **Capability Summary cells are
✅**. But the **overall platform status is ⚠️** because the surfaces are **semantically different**:

- **No instruction-file convention** — `AGENTS.md`/`CLAUDE.md` do not load; gald3r system
  instructions must be hand-folded into a Persona `system_prompt`.
- **Hooks are LLM/message-pipeline runtime events**, not git/file/session-shell hooks — gald3r's
  `g-hk-*.ps1` do not wire natively.
- **Commands/agents/rules have no drop-in `.md` files** — they are Python `@filter` registrations,
  Agent-Runner config, and DB-stored personas.
- **Skills are the one clean drop-in** (`SKILL.md` via `.zip` upload or Star `skills/` bundle).

**Reuse note:** the cheapest real integration is to **ship gald3r skills as a `.zip` / Star plugin
`skills/` bundle** and inject any must-have gald3r instructions via a Persona `system_prompt`.
Everything else requires authoring AstrBot-native Python plugin code, not reusing gald3r's
Claude-Code artifacts.

## Hook System

- **Type**: native (plugin runtime event hooks — `@filter` decorators)
- **Config file**: none (registered in Star plugin `main.py`, not a JSON/settings file)
- **Events available**: `on_astrbot_loaded`, `on_waiting_llm_request`, `on_llm_request`,
  `on_llm_response`, `on_decorating_result`, `after_message_sent`; agent-loop: `on_agent_begin`,
  `on_using_llm_tool`, `on_llm_tool_respond`, `on_agent_done` (v4.23.1+)
- **Event payload format**: Python objects (e.g. `ProviderRequest`) passed to decorated handlers;
  priority-ordered
- **Command extensions**: Python only (no `.sh` / `.ps1` shell hook support)
- **gald3r hook files**: `g-hk-*.ps1` do **NOT** wire — these are chat/LLM-pipeline events, not
  filesystem/VCS/session-shell hooks

## Atypical Handling

- **IM runtime, not an IDE**: install target is a **WebUI plugin upload / Star package**, not a
  repo config folder. Skill trigger is a **chat message / slash command**, not session start.
- **No repo instruction file**: there is no `AGENTS.md`/`CLAUDE.md` path — use a Persona
  `system_prompt` for always-on instructions.
- **Skill execution environment**: prefer **Sandbox** over **Local** for any gald3r skill that runs
  scripts (Local = admin-only, arbitrary code execution in the AstrBot runtime).
- **Recency**: Custom Rules (v4.7.0), Anthropic Skills (v4.13.0), agent-loop hooks (v4.23.1+) are
  all **2026** additions — re-verify on the freshness gate; the extension surface is actively
  expanding.

## gald3r Integration Notes

- **Ship gald3r skills** as a `.zip` (WebUI > Plugins > Skills) or inside a **Star plugin
  `skills/`** directory — this is the only native drop-in.
- **No `g-hk-*.ps1` hooks, no `g-rl-*`/`@g-*` `.md` files** load natively; realize rules via a
  Persona `system_prompt` and commands via `@filter.command()` Python registrations if a fuller
  integration is needed.
- **Correct stored metadata**: AstrBot is maintained by **AstrBotDevs** (AGPL-v3), **not** Nous
  Research; it is an **IM agent runtime**, not a coding IDE.
- Re-verify on the next `@g-platform-scan-docs astrbot` (crawl_max_age_days: 14).

---

## Capability Summary (copy into PLATFORM_STATUS.md row)

| Hooks | Rules | Skills | Commands | MCP | Docs Fresh |
|---|---|---|---|---|---|
| ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |

Legend: ✅ verified working · ⚠️ partial / Cursor-generic · ❌ not supported · ❓ untested.

> Cells are ✅ at the **mechanism** level (all six exist natively). The **overall platform status is
> ⚠️** because the surfaces are IM-runtime-shaped, not file-first: no instruction-file convention,
> hooks are LLM/message events (not git/file), and only skills are a clean gald3r drop-in.

---

## Verification Evidence (docs crawl 2026-06-02, https://docs.astrbot.app)

| Capability | How verified |
|---|---|
| Commands | /en/dev/star/guides/listen-message-event — `@filter.command()` / `@filter.command_group()`; params, `alias={...}`, priority; built-in `/persona`, `/help` |
| Rules | github.com/AstrBotDevs/AstrBot/wiki/en-use-custom-rules — Persona `system_prompt` injected first in every LLM call; Custom Rules per unified-message-origin (v4.7.0); long-term memory/profiling |
| Agents | /en/use/agent-runner — built-in Agent Runner (perceive→plan→execute→observe→re-plan); third-party runners (Dify/Coze/Bailian/DeerFlow); "SubAgent Orchestration" |
| Skills | /en/use/skills — Anthropic `SKILL.md` (v4.13.0) via `.zip` WebUI upload or Star `skills/` bundle; Local vs Sandbox execution envs |
| Hooks | /en/dev/star/guides/listen-message-event — `@filter` lifecycle/LLM/message hooks (`on_llm_request` etc.); agent-loop hooks `on_agent_begin`/`on_agent_done` (v4.23.1+); priority-ordered; Python, not shell |
| MCP | /use/mcp — MCP client (connect external servers) + expose own tools over MCP; WebUI-configured; env-var credentials; e.g. arxiv-mcp-server |
| Instruction file | No AGENTS.md/CLAUDE.md/GEMINI.md convention — WebUI/config/DB-driven; Persona `system_prompt` is the always-on equivalent |
| Provenance | Maintained by AstrBotDevs org under AGPL-v3 (NOT Nous Research); IM chatbot/agent runtime, not an IDE coding agent |
