---
subsystem_memberships: [PLATFORM_INTEGRATION]
platform: deepcode
authoring_path: update
docs_url: https://github.com/lessweb/deepcode-cli
docs_url_secondary:
  - https://api-docs.deepseek.com/quick_start/agent_integrations/deepcode
crawl_max_age_days: 14
vault_doc_path: research/platforms/deepcode/
last_doc_scan: 2026-06-02
reference: g-skl-platform-cursor
status: ⚠️
task: T1474
---

# PLATFORM_SPEC.md — Deep Code CLI (lessweb/deepcode-cli)

Deep Code is a **terminal AI coding assistant optimized for the DeepSeek-V4 model**. It supports
deep thinking, reasoning-effort control, and the open **Agent Skills** (`SKILL.md`) standard. As of
mid-2026 Deep Code natively supports **three** of the six gald3r-relevant extension primitives —
**rules** (via an `AGENTS.md` instruction file), **Agent Skills**, and **MCP** — while **custom
commands** are limited to a fixed built-in slash set (partial), and **subagents** and a **lifecycle
hook system** are **absent**. Critically for gald3r, Deep Code reads **`AGENTS.md`** (scaffolded by
`/init`) — **not** `CLAUDE.md` — so gald3r's `AGENTS.md` instruction file is the first-class context
input, and skills load from the **`.agents/skills/`** convention shared with other Agent-Skills tools.

**Authoring path**: UPDATE. **Verified 2026-06-02** against https://github.com/lessweb/deepcode-cli
and https://api-docs.deepseek.com/quick_start/agent_integrations/deepcode (see Verification Evidence).
This **supersedes** the prior spec (`last_doc_scan: 2026-05-28`) which incorrectly marked rules as
`❓` (they are NATIVE via `AGENTS.md` + `/init`), commands as fully `✅` (only a fixed built-in set —
no user-defined commands), and agents/hooks as `❓` (both confirmed **absent** — `none`).

> **Surface split:** the CLI (`deepcode`) is the primary extensibility surface. Deep Code shares its
> **`~/.deepcode/settings.json`** with the **Deep Code VSCode extension** ("configure once, use
> everywhere"), so gald3r-managed settings (model, MCP servers, notify script) apply to **both**
> surfaces. Where a feature is settings-driven it is noted inline.

---

## 1. Folder Hierarchy

```
<project-root>/
├── AGENTS.md                       ← instruction file Deep Code reads (scaffolded via /init)
└── .agents/
    └── skills/  <name>/SKILL.md    ← Agent Skills (project, recommended path)

<project-root>/.deepcode/           ← legacy / project config
├── settings.json                   ← MCP (mcpServers), model, notify, thinking/reasoning
└── skills/      <name>/SKILL.md    ← legacy project skills path (still resolves)

~/                                   (user/home scope)
├── .deepcode/settings.json         ← global config — SHARED with the Deep Code VSCode extension
└── .agents/skills/ <name>/SKILL.md ← user-global Agent Skills
```

Deep Code discovers skills from `~/.agents/skills/` (user), `./.agents/skills/` (project,
**recommended**), and legacy `./.deepcode/skills/` (backward-compatible). gald3r should target
**`./.agents/skills/<name>/SKILL.md`** and **`~/.agents/skills/<name>/SKILL.md`**.

**gald3r writes**: `AGENTS.md`, `.agents/skills/<name>/SKILL.md`, and (only when MCP/model setup is
needed) `.deepcode/settings.json`.
**Deep Code owns**: the `~/.deepcode/settings.json` schema (shared with the VSCode extension), the
built-in slash-command set, and the permissions framework governing shell/file/network access.

---

## 2. AI Instruction File

Deep Code reads **`AGENTS.md`** as the persistent, always-on instruction/context file —
**scaffolded by the `/init` command** (README: `/init 初始化 AGENTS.md 文件` — "the /init command
initializes the AGENTS.md instruction file"). There is **no `CLAUDE.md` read** and **no separate
`rules/` or `memory/` directory** — `AGENTS.md` is the single instruction surface. gald3r's
`AGENTS.md` is therefore a first-class input; gald3r's `CLAUDE.md` is **not** consumed by Deep Code.

---

## 3. Agents Support — ❌ NONE

- Deep Code operates as a **single AI assistant**. No sub-agents, agent roles, or distinct agent
  modes are documented in the README or the DeepSeek integration docs.
- Reasoning-effort / thinking levels (`reasoningEffort`, `thinkingEnabled`) exist but are **model
  settings, not agent roles** — they do not provide gald3r `g-agnt-*` parity.
- gald3r `g-agnt-*` definitions have **no native target** on Deep Code; fold agent behaviour into
  `AGENTS.md` instructions or per-skill `SKILL.md` context instead.
- Source: https://github.com/lessweb/deepcode-cli

## 4. Skills Support — ✅ NATIVE

- **Agent Skills** (open `SKILL.md` standard) discovered in **`~/.agents/skills/<name>/SKILL.md`**
  (user), **`./.agents/skills/<name>/SKILL.md`** (project, **recommended**), and legacy
  **`./.deepcode/skills/<name>/SKILL.md`** (backward-compatible). Activate by pressing **`/`** and
  selecting from the skill picker, or by typing the skill name. Frontmatter follows the Agent Skills
  open standard (`name`, `description`).
- gald3r `g-skl-*/SKILL.md` load natively — target `.agents/skills/` for forward-compatibility.
- Source: https://api-docs.deepseek.com/quick_start/agent_integrations/deepcode

## 5. Commands / Workflows — ⚠️ PARTIAL

- **Built-in slash commands only**: `/new`, `/resume`, `/continue`, `/model`, `/raw`, `/init`,
  `/skills`, `/mcp`, `/undo`, `/exit`; the skill/command picker opens with **`/`**.
- **No mechanism for user-defined custom commands** is documented — there is **no
  `.deepcode/commands/`** (or equivalent) directory. gald3r `@g-*` / `/g-*` commands have **no
  native slash-command target**; surface them as **skills** (each skill is invocable via the `/`
  picker) instead.
- Source: https://github.com/lessweb/deepcode-cli

## 6. Hooks System — ❌ NONE

- **No lifecycle/event hook system** — there is no session-start / pre-tool / pre-commit / file-watch
  hook framework.
- The **only** automation is the **`notify`** field in `settings.json`: DeepSeek docs describe it as
  *"Path to a notification script executed after each model turn"* (used to push results to Slack /
  system notifications). This is a **single post-turn completion notifier**, **not** a configurable
  lifecycle-hook framework — it cannot block tool calls, inject session-start context, or gate
  commits.
- gald3r `g-hk-*.ps1` hooks (SessionStart context injection, PreToolUse `.gald3r/` guards,
  pre-commit gates) have **no native wiring**; the `notify` script can at most fire a post-turn
  side-effect.
- Source: https://api-docs.deepseek.com/quick_start/agent_integrations/deepcode

## 7. Rules / Memory — ✅ NATIVE

- **`AGENTS.md`** is the persistent always-on instruction/context file, **scaffolded via `/init`**.
  It is the single rules surface — there is **no** `.deepcode/rules/`, no `.mdc` rule files, and no
  separate cross-session memory store. `/resume` and `/continue` restore prior session state but are
  **not** a persistent rules/memory file.
- gald3r `g-rl-*` map into the single `AGENTS.md` instruction file (concatenate always-apply rule
  content); there is no per-rule `always_apply` / `agent_requested` typing and no `globs:`
  path-scoping.
- Source: https://github.com/lessweb/deepcode-cli

## 8. MCP Support — ✅ NATIVE

- MCP configured via the **`mcpServers`** field in **`settings.json`**; inspect configured servers
  and their tools with the **`/mcp`** command. Standard **stdio** transport; connects external
  services (GitHub, browsers, databases). Documented in `docs/mcp.md`.
- Because `~/.deepcode/settings.json` is shared with the VSCode extension, MCP servers configured
  once apply to both the CLI and the IDE surface.
- Note: DeepSeek's own integration page omits MCP, but the project README and command set
  (`/mcp`) document it natively — the primary/official sources were trusted.
- Source: https://github.com/lessweb/deepcode-cli

---

## Parity vs. Cursor Reference

Deep Code reaches **partial parity** with the Cursor reference (`g-skl-platform-cursor`): native
**rules** (`AGENTS.md`), **skills** (Agent Skills standard), and **MCP** (`mcpServers`); **partial
commands** (fixed built-in slash set only — no user-defined commands); and **no subagents** and **no
lifecycle hooks**. The biggest gaps vs. the reference are custom commands, subagents, and the hook
system.

**Reuse note (important):** Deep Code reads **`AGENTS.md`** (not `CLAUDE.md`) and discovers
**`.agents/skills/`** (not `.claude/skills/`). gald3r's `AGENTS.md` + `.agents/skills/` artifacts are
**directly reusable**; gald3r's Claude-Code-specific `CLAUDE.md` / `.claude/` tree is **not** consumed
and must not be relied on for Deep Code installs.

## Hook System

- **Type**: none (no lifecycle-hook framework)
- **Config file**: `settings.json` (`notify` field only)
- **Events available**: none — only a single post-turn `notify` callback (after each model turn)
- **Event payload format**: n/a — `notify` is a fire-and-forget script path, no structured event data
- **Command extensions**: any executable script path (e.g. `.sh`); fires **after** a turn, cannot block
- **gald3r hook files**: `g-hk-*.ps1` do **not** wire natively — at most a post-turn side-effect via `notify`

## Atypical Handling

- **Shared config surface**: `~/.deepcode/settings.json` is shared with the **Deep Code VSCode
  extension** — gald3r-managed settings (model, `mcpServers`, `notify`) apply to **both** surfaces.
- **Instruction-file convention**: Deep Code reads **`AGENTS.md`** (via `/init`), **not** `CLAUDE.md`.
  Point gald3r rules/instructions at `AGENTS.md`.
- **Skills path migration**: project skills moved from legacy `./.deepcode/skills/` to
  **`./.agents/skills/`** (the `.agents/skills/` convention shared with other Agent-Skills tools).
  Both still resolve; target `./.agents/skills/` going forward.
- **Source disambiguation**: web searches surface unrelated DeepSeek tools (DeepSeek-Reasonix,
  DeepSeek-TUI, deepseek-as-subagent) that DO have hooks/subagents — these are **different projects**
  and are excluded from this assessment of `lessweb/deepcode-cli`. A third-party Verdent review (2026)
  also wrongly claims `AGENTS.md` and MCP are absent; the README + DeepSeek docs confirm both are
  present, so primary/official sources were trusted over the review.

## gald3r Integration Notes

- Ship gald3r's **`AGENTS.md`** (instruction/rules) + **`.agents/skills/<name>/SKILL.md`** tree —
  Deep Code discovers both natively.
- Surface gald3r commands **as skills** (each skill is invocable via the `/` picker); there is no
  custom-command directory to target.
- Do **not** rely on hooks — degrade SessionStart context injection, PreToolUse guards, and
  pre-commit gates to manual/skill-driven flows; the `notify` script is post-turn only and cannot block.
- Configure MCP via `mcpServers` in `settings.json`; remember it also applies to the VSCode surface.
- Re-verify on the next `@g-platform-scan-docs deepcode` (crawl_max_age_days: 14).

---

## Capability Summary (copy into PLATFORM_STATUS.md row)

| Hooks | Rules | Skills | Commands | MCP | Docs Fresh |
|---|---|---|---|---|---|
| ❌ | ✅ | ✅ | ⚠️ | ✅ | ✅ |

Legend: ✅ verified working · ⚠️ partial / Cursor-generic · ❌ not supported · ❓ untested.

---

## Verification Evidence (docs crawl 2026-06-02, https://github.com/lessweb/deepcode-cli + DeepSeek docs)

| Capability | How verified |
|---|---|
| Commands | README — fixed built-in slash set (`/new /resume /continue /model /raw /init /skills /mcp /undo /exit`); picker via `/`; **no** user-defined custom-command directory → ⚠️ partial |
| Rules | README — `/init` scaffolds **`AGENTS.md`** (always-on instruction file); reads `AGENTS.md` **not** `CLAUDE.md`; no `rules/` dir → ✅ native |
| Agents | README / DeepSeek docs — single assistant; no sub-agents/roles/modes (reasoning-effort is a model setting) → ❌ none |
| Skills | DeepSeek docs — Agent Skills `SKILL.md` in `~/.agents/skills/`, `./.agents/skills/` (recommended), legacy `./.deepcode/skills/`; activate via `/` → ✅ native |
| Hooks | DeepSeek docs — no lifecycle hooks; only `notify` (post-turn script in settings.json), cannot block → ❌ none |
| MCP | README — `mcpServers` field in `settings.json`; `/mcp` to inspect; stdio transport; `docs/mcp.md` → ✅ native |
| Instruction file | README — `AGENTS.md` via `/init` (not `CLAUDE.md`, not `AGENTS.md`-vs-`CLAUDE.md` dual-read) |
| Shared config | `~/.deepcode/settings.json` shared with Deep Code VSCode extension ("configure once, use everywhere") |
