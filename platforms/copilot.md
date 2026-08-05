---
subsystem_memberships: [PLATFORM_INTEGRATION]
platform: copilot
authoring_path: update
docs_url: https://docs.github.com/en/copilot/reference/customization-cheat-sheet
docs_url_secondary:
  - https://docs.github.com/en/copilot/concepts/agents/about-agent-skills
  - https://docs.github.com/en/copilot/reference/hooks-configuration
  - https://docs.github.com/en/copilot/concepts/context/mcp
crawl_max_age_days: 7
vault_doc_path: research/platforms/github_copilot/
last_doc_scan: 2026-06-02
reference: g-skl-platform-cursor
status: ✅
task: T1463
---

# PLATFORM_SPEC.md — GitHub Copilot

GitHub Copilot is GitHub's AI coding assistant. It runs across multiple **surfaces** (VS Code,
Visual Studio 2026 18.4+, JetBrains, the Copilot CLI, and the Copilot coding agent on
GitHub.com), and as of mid-2026 the customization stack natively supports **all six**
gald3r-relevant extension primitives — **prompt-file slash commands, custom instructions (rules),
custom agents + subagents, Agent Skills, lifecycle hooks, and MCP**. Critically for gald3r, Copilot
reads the cross-tool **`AGENTS.md`** instruction convention *and* discovers Agent Skills from
**`.github/skills/`, `.claude/skills/`, and `.agents/skills/`**, so gald3r's Claude-Code skill tree
is **largely drop-in reusable** on Copilot.

**Authoring path**: UPDATE. **Verified 2026-06-02** against
https://docs.github.com/en/copilot/reference/customization-cheat-sheet (see Verification Evidence).
This **supersedes** the prior spec (`last_doc_scan: never`) which marked skills as `❓`, commands as
`❌`, and hooks/MCP as `⚠️` — Copilot's customization surface has since matured and all six
primitives are now **NATIVE** (`overall_readiness: full`).

> **Surface split (the central caveat):** features land at **different times across surfaces**. The
> richest surface varies per primitive — e.g. prompt-file slash commands work in the **VS Code**
> extension but **NOT** the Copilot CLI (built-in commands only; issues #618/#1113); custom agents
> require **VS 2026 v18.4+**; hooks are GA on the Copilot **CLI** and in **preview** for VS Code.
> Where a feature is surface-limited it is noted inline.

---

## 1. Folder Hierarchy

Copilot customization spans GitHub's native `.github/` tree plus cross-tool discovery paths, and a
gald3r convention folder:

```
<project-root>/
├── AGENTS.md                         ← cross-tool instruction file Copilot reads (nearest in tree wins)
├── CLAUDE.md / GEMINI.md             ← also natively read (cross-tool instruction conventions)
└── .github/
    ├── copilot-instructions.md       ← repo-wide always-on custom instructions (auto-loaded)
    ├── instructions/  *.instructions.md  ← path-scoped instructions (frontmatter applyTo: "glob")
    ├── prompts/       *.prompt.md     ← reusable slash commands (YAML frontmatter; /command-name)
    ├── agents/        AGENT-NAME.md   ← custom agents (specialist persona; tool restrictions)
    ├── skills/        <name>/SKILL.md ← Agent Skills (YAML frontmatter: name + description)
    └── hooks/         *.json          ← Copilot CLI lifecycle hooks (bash variant runs gald3r `g-hk-*.py` via `python <path>`)

.claude/skills/<name>/SKILL.md        ← Copilot ALSO discovers Agent Skills here  (cross-tool)
.agents/skills/<name>/SKILL.md        ← Copilot ALSO discovers Agent Skills here  (cross-tool)

mcp.json                              ← MCP config (VS Code / JetBrains / Xcode)
~/.copilot/mcp-config.json            ← MCP config (Copilot CLI)
(repo/org settings)                   ← MCP config (cloud coding agent)

.copilot/                             ← gald3r CONVENTION folder — NOT a Copilot-native path
├── README.md                         ← platform orientation for gald3r users
└── commands/  g-*.md                 ← gald3r command reference docs (human/agent reference only)
```

Copilot **also** discovers Agent Skills from `.claude/skills/` and `.agents/skills/` (not just
`.github/skills/`), so gald3r's `.claude/`-style skill tree works on Copilot with **no
Copilot-specific port**.

**gald3r writes**: `.github/copilot-instructions.md` (generated from always-apply rules),
`.github/instructions/` (adv-tier optional), `.github/prompts/`, `.github/agents/`,
`.github/hooks/*.json`, plus the `.copilot/` convention folder; gald3r's `.claude/skills/` tree is
loaded as-is.
**Copilot owns**: the *meaning* of `.github/copilot-instructions.md`, `.github/instructions/`,
`.github/prompts/`, MCP config, and the **Agentic Memory** store (agent-authored repo/user facts —
Copilot-managed, not a gald3r-writable surface). `.copilot/` is purely a gald3r invention; Copilot
does not read it.

---

## 2. AI Instruction File

Copilot reads the cross-tool **`AGENTS.md`** convention (root **or nested**; the **nearest in the
directory tree takes precedence**). It additionally natively reads GitHub's own
**`.github/copilot-instructions.md`** (repo-wide, auto-loaded) and **`.github/instructions/**.instructions.md`**
(path-scoped via `applyTo:` glob), plus the cross-tool **`CLAUDE.md`** and **`GEMINI.md`**. No
dedicated `COPILOT.md` is required — gald3r's `AGENTS.md` is a first-class input.

> **Instruction-convention truth:** unlike Claude Code (which reads `CLAUDE.md`, importing
> `@AGENTS.md`), Copilot reads **`AGENTS.md` directly** as its primary cross-tool instruction file,
> while still honoring its GitHub-native `.github/copilot-instructions.md`. gald3r generates
> `copilot-instructions.md` from always-apply rules via `generate_copilot_instructions.py`; keep
> consumer installs lean (large instruction files compete for context window — under ~500 lines).

---

## 3. Agents Support — ✅ NATIVE

- **Custom agents** (formerly "custom chat modes"; terminology updated, functionality unchanged):
  a "specialist persona with its own instructions, tool restrictions, and context" stored as
  `.github/agents/AGENT-NAME.md`. **Subagents** are "a separate agent spawned by the main agent to
  handle delegated work in an isolated context." Custom agents, sub-agents, and the plan agent are
  **GA in Copilot for JetBrains (2026)**; custom agents in the VS family require **VS 2026 v18.4+**.
- Org/enterprise scope: agents (and instructions) can be distributed centrally via a
  **`.github-private`** repository (`agents/AGENT-NAME.md`).
- gald3r `g-agnt-*` definitions map directly to `.github/agents/AGENT-NAME.md` files.
- Source: https://docs.github.com/en/copilot/reference/customization-cheat-sheet

## 4. Skills Support — ✅ NATIVE

- **Agent Skills** (`SKILL.md` open standard) — "a folder of instructions, scripts, and resources
  that Copilot loads when relevant to a task." `SKILL.md` uses YAML frontmatter (`name` +
  `description` required). Added **April 2026**; the **same SKILL.md format works across Claude Code,
  Cursor, Codex, and 20+ agents**.
- **Multi-path discovery**: Copilot reads `.github/skills/<name>/SKILL.md` **and** `.claude/skills/`
  **and** `.agents/skills/` — favorable for a single gald3r skill tree shared across tools.
- gald3r `g-skl-*/SKILL.md` load natively — including straight from `.claude/skills/`.
- Source: https://docs.github.com/en/copilot/concepts/agents/about-agent-skills

## 5. Commands / Workflows — ✅ NATIVE (surface-limited)

- **Prompt files** (`.github/prompts/*.prompt.md`) "turn repeated Copilot chat requests into slash
  commands"; create with YAML frontmatter and invoke via `/command-name`.
- **Surface caveat**: prompt-file slash commands work in the **VS Code extension** but **NOT** the
  Copilot **CLI** (the CLI recognizes built-in commands only — issues #618/#1113). gald3r's 90+
  `g-*` commands additionally ship to `.copilot/commands/*.md` as reference docs (not executed).
- gald3r `@g-*` / `/g-*` commands map to prompt files for the VS Code surface.
- Source: https://docs.github.com/en/copilot/reference/customization-cheat-sheet

## 6. Hooks System — ✅ NATIVE (CLI GA; VS Code preview)

- **Copilot CLI hooks** are "custom shell commands that execute deterministically at specific points
  in an agent's workflow." Events: **sessionStart**, **userPromptSubmitted**, **preToolUse**,
  **postToolUse**, **sessionEnd**, **errorOccurred**. For **preToolUse**, a hook returning **`deny`
  blocks the tool**. Configured in **`.github/hooks/*.json`** with **bash / any-executable variants**
  — so gald3r `g-hk-*.py` hooks wire via the bash variant running `python <path>` (post-T1584 Python
  port; no PowerShell involved; sessionStart context injection,
  preToolUse `.gald3r/` guards, etc.).
- **Surface caveat**: hooks are GA on the **Copilot CLI**; **Agent hooks are also in preview for
  VS Code**.
- **Scope note**: Copilot hooks fire only during an **active agent session** (CLI / cloud) — they
  are NOT git hooks, CI scripts, or GitHub Actions; normal commits/pushes are unaffected.
- Source: https://docs.github.com/en/copilot/reference/hooks-configuration

## 7. Rules / Memory — ✅ NATIVE

- **Custom instructions (always-on)** = "always-on context that automatically applies to every
  interaction within its defined scope" via `.github/copilot-instructions.md` (repo-wide),
  `.github/instructions/*.instructions.md` (path-specific via `applyTo:` glob), and
  `AGENTS.md`/`CLAUDE.md`/`GEMINI.md`. Plain `.md` (not Cursor's `.mdc` — parity sync swaps the
  extension). gald3r flattens always-apply rules into the single `copilot-instructions.md`.
- **Agentic Memory (Copilot Memory)** is a **distinct dynamic-context primitive** beyond static
  instruction files — agents **self-author** repo- and user-level facts. **On by default for
  Pro/Pro+ in public preview.** This is a Copilot-managed store, not a gald3r-writable surface.
- gald3r `g-rl-*` map to `.github/copilot-instructions.md` (always-apply) or
  `.github/instructions/` (path-scoped, adv tier).
- Source: https://docs.github.com/en/copilot/reference/customization-cheat-sheet

## 8. MCP Support — ✅ NATIVE

- MCP provides "connection to external systems, APIs, and databases" and "works across all major
  Copilot surfaces — IDE, CLI, or coding agent on GitHub.com." Configured via an `mcpServers` object;
  **STDIO, HTTP, and SSE** transports supported. The **GitHub MCP Registry (public preview)** lists
  curated servers.
- **Per-surface config paths**: `mcp.json` (VS Code / JetBrains / Xcode),
  `~/.copilot/mcp-config.json` (CLI), repo/org settings (cloud agent). Fully supported but **not
  single-path portable** — gald3r cannot ship one `mcp.json` that every surface reads.
- Source: https://docs.github.com/en/copilot/concepts/context/mcp

## 9. Distribution / Catalog

- Org/enterprise: custom **agents and instructions** distribute centrally via a **`.github-private`**
  repository.
- **`github/awesome-copilot`** is the official community catalog of instructions, agents, skills,
  and hooks — the natural distribution/discovery channel for a gald3r Copilot bundle.
- Output formats: prompt files and custom agents use **YAML frontmatter**; hooks use **JSON** config;
  MCP uses **JSON** (`mcpServers` object).

---

## Parity vs. Cursor Reference

Copilot now reaches **near-full parity** with the Cursor reference (`g-skl-platform-cursor`): native
**commands, rules, agents, skills, hooks, and MCP**. Caveats: **surface fragmentation** (prompt-file
slash commands are VS Code-only; custom agents need VS 2026 v18.4+; hooks are CLI-GA / VS Code-preview)
and **per-surface MCP config paths**. The **Agentic Memory** store is a Copilot-native bonus with no
Cursor analog (agent-authored facts, not a gald3r-writable surface). Path-scoped instructions
(`.github/instructions/` with `applyTo:`) are a Copilot superset with no Cursor equivalent.

**Reuse note (important):** because Copilot reads `AGENTS.md` and discovers `.claude/skills/` +
`.agents/skills/`, gald3r's **Claude-Code skill artifacts are largely reusable on Copilot without a
separate port** — the cheapest path to a high-parity Copilot install is to ship the gald3r
`.claude/skills/` tree plus a generated `.github/copilot-instructions.md` and `AGENTS.md`.

## Hook System

- **Type**: native (Copilot CLI lifecycle hooks; JSON config) — agent-session only (NOT git hooks / CI / Actions)
- **Config file**: `.github/hooks/*.json`
- **Events available**: sessionStart, userPromptSubmitted, preToolUse (returning `deny` blocks the tool), postToolUse, sessionEnd, errorOccurred
- **Event payload format**: JSON config; hook objects carry **bash** command variants (any executable)
- **Command extensions**: `.sh` (bash variant) running any executable, incl. gald3r's `g-hk-*.py` via `python <path>`
- **Surface limit**: GA on the Copilot **CLI**; **preview** in VS Code
- **gald3r hook files**: `g-hk-*.py` wire via the bash variant running `python <path>` across the events above (agent-session scope only)

## Atypical Handling

- **Surface fragmentation** is the defining trait: a capability that is GA on one surface may be
  preview/absent on another. Always state the surface (VS Code vs CLI vs JetBrains vs cloud agent).
- Instruction convention: Copilot reads **`AGENTS.md`** directly (nearest-in-tree wins), plus its
  GitHub-native `.github/copilot-instructions.md` — it does **not** require a `CLAUDE.md` import.
- **Agentic Memory** is a dynamic, agent-authored context store distinct from static instruction
  files — do not conflate it with `copilot-instructions.md`.
- Skill discovery is multi-path (`.github/skills/` + `.claude/skills/` + `.agents/skills/`) — reuse
  the existing gald3r `.claude/skills/` tree rather than duplicating into `.github/skills/`.
- MCP config path differs per surface; ship the right one for the target surface.

## gald3r Integration Notes

- Ship gald3r's `.claude/skills/` tree — Copilot discovers it; generate
  `.github/copilot-instructions.md` (from always-apply rules) and `AGENTS.md`.
- Hooks wire on the Copilot **CLI** via the bash variant running `python <path>`; VS Code hook support is **preview**
  — do not assume session-start/pre-commit hooks fire in the VS Code surface yet.
- Prompt-file slash commands are **VS Code-only** — gald3r commands are not executable on the CLI.
- Re-verify on the next `@g-platform-scan-docs copilot` (crawl_max_age_days: 7).

---

## Capability Summary (copy into PLATFORM_STATUS.md row)

| Hooks | Rules | Skills | Commands | MCP | Docs Fresh |
|---|---|---|---|---|---|
| ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |

Legend: ✅ verified working · ⚠️ partial / Cursor-generic · ❌ not supported · ❓ untested.

Rationale (honest, surface-aware):
- **Hooks ✅** — native Copilot CLI lifecycle hooks (`.github/hooks/*.json`; 6 events; preToolUse `deny` blocks). VS Code support is preview.
- **Rules ✅** — `.github/copilot-instructions.md` (always-on) + `.github/instructions/` (path-scoped) + reads `AGENTS.md`; plus Agentic Memory.
- **Skills ✅** — Agent Skills `SKILL.md` discovered in `.github/.claude/.agents` skills dirs (cross-tool standard).
- **Commands ✅** — prompt-file slash commands (`.github/prompts/*.prompt.md`); VS Code-only (not the CLI).
- **MCP ✅** — native across IDE/CLI/cloud (STDIO/HTTP/SSE); config path differs per surface.
- **Docs Fresh ✅** — `last_doc_scan: 2026-06-02` against the customization cheat sheet.

---

## Verification Evidence (docs crawl 2026-06-02, https://docs.github.com/en/copilot/reference/customization-cheat-sheet)

| Capability | How verified |
|---|---|
| Commands | Cheat sheet — prompt files `.github/prompts/*.prompt.md` become `/command-name` slash commands; VS Code only (CLI = built-in commands, issues #618/#1113) |
| Rules | Cheat sheet — custom instructions `.github/copilot-instructions.md` (repo) + `.github/instructions/*.instructions.md` (`applyTo:`) + `AGENTS.md`/`CLAUDE.md`/`GEMINI.md`; plus Agentic Memory (Pro/Pro+ preview) |
| Agents | Cheat sheet — custom agents `.github/agents/AGENT-NAME.md` (specialist persona, tool restrictions) + subagents; GA in JetBrains 2026; VS 2026 v18.4+; org via `.github-private` |
| Skills | /concepts/agents/about-agent-skills — Agent Skills `SKILL.md` (name+description); discovered in `.github/skills/`, `.claude/skills/`, `.agents/skills/`; added Apr 2026; cross-tool standard |
| Hooks | /reference/hooks-configuration — `.github/hooks/*.json`; sessionStart/userPromptSubmitted/preToolUse/postToolUse/sessionEnd/errorOccurred; preToolUse `deny` blocks; bash variant runs gald3r `g-hk-*.py` via `python <path>`; CLI GA, VS Code preview |
| MCP | /concepts/context/mcp — `mcpServers` object; STDIO/HTTP/SSE; `mcp.json` (IDE) / `~/.copilot/mcp-config.json` (CLI) / repo settings (cloud); GitHub MCP Registry (preview) |
| Cross-compat | Copilot reads `AGENTS.md` (nearest-in-tree) and discovers `.claude/` + `.agents/` skills → gald3r Claude-Code skill artifacts reusable |


---
*Reference page — canonical source: `g-skl-platform-copilot/PLATFORM_SPEC.md` in the engine repo, generated by `scripts/generate_platform_support_docs.py`. Pages marked *curated* are hand-assessed and not yet live-verified.*
