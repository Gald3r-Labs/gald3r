---
subsystem_memberships: [PLATFORM_INTEGRATION]
platform: roo
authoring_path: update
docs_url: https://docs.roocode.com
docs_url_secondary:
  - https://docs.roocode.com/features/slash-commands
  - https://docs.roocode.com/features/custom-instructions
  - https://docs.roocode.com/features/custom-modes
  - https://docs.roocode.com/features/skills
  - https://docs.roocode.com/features/experimental/custom-tools
  - https://docs.roocode.com/features/mcp/using-mcp-in-roo
crawl_max_age_days: 14
vault_doc_path: research/platforms/roo/
last_doc_scan: 2026-06-02
reference: g-skl-platform-cursor
status: ⚠️
task: T1474
---

# PLATFORM_SPEC.md — Roo Code (formerly Roo Cline)

Roo Code is an open-source agentic coding extension for **VS Code**, forked from Cline. As of its
final documented state it natively supports **five of the six** gald3r-relevant extension primitives —
custom slash commands, rules/memory, modes (the agent/sub-agent analog), Agent Skills, and MCP —
making it one of the most gald3r-aligned platforms **by documented capability**. The only missing
mechanism is **lifecycle hooks**. For gald3r, Roo auto-loads **`AGENTS.md`** (not `CLAUDE.md`) from
the workspace root and discovers commands/rules/skills/modes from the **`.roo/`** tree, with a
cross-agent **`.agents/skills/`** path for Skills.

> **⚠️ PRIMARY CAVEAT — DISCONTINUED.** Roo Code (VS Code extension, Roo Code Cloud, and Roo Code
> Router) was officially **shut down on 2026-05-15** (announced 2026-04-21 by Matt Rubens). The
> company pivoted to a cloud product (Roomote), concluding "IDEs are not the future of coding."
> Docs and the open-source GitHub repos remain available and the archived extension still functions,
> but the tool is **no longer actively developed**; migration is directed to **Cline / Kilo Code**.
> Capability is rated on documented features; the shutdown is the dominant practical caveat. Treat
> any gald3r `roo` platform target as **legacy/frozen**.

**Authoring path**: UPDATE. **Verified 2026-06-02** against https://docs.roocode.com (see
Verification Evidence). This **supersedes** the prior spec (`last_doc_scan: 2026-05-20`) which marked
skills/commands/agents/mcp as ⚠️ — they are now confirmed **NATIVE** (Skills shipped ~v3.38; the
official Skills feature page is dated 2026-05-15).

> **Docs host note:** `docs.roocode.com` 301-redirects to
> `https://roocodeinc.github.io/Roo-Code/`; canonical `/features/*` paths still resolve to live
> content.

---

## 1. Folder Hierarchy

```
<project-root>/
├── AGENTS.md                     ← auto-loaded agent rules (unless roo-cline.useAgentRules:false)
├── .roomodes                     ← custom mode definitions (YAML preferred; JSON accepted)
├── .rooignore                    ← gitignore-style agent file-access control
└── .roo/
    ├── rules/        *.md        ← general rules, ALL modes (recursive, alphabetical)
    ├── rules-{slug}/ *.md        ← mode-specific rules (e.g. rules-code/, rules-architect/)
    ├── commands/     *.md        ← project slash commands (filename = command name)
    ├── skills/       <name>/SKILL.md     ← Agent Skills (progressive disclosure)
    ├── skills-{mode}/<name>/SKILL.md     ← mode-specific Agent Skills
    └── mcp.json                  ← project-level MCP server config (team-shareable)

  ── cross-agent + legacy fallbacks ──
├── .agents/skills/   <name>/SKILL.md     ← cross-agent Skills path (shared standard)
├── .roorules                     ← general rules fallback (≈ .roo/rules/)
├── .roorules-{slug}              ← mode-specific rules fallback
└── .clinerules                   ← Cline-compatibility fallback (Roo reads it)
```

**Global (per-user) equivalents** live under `~/.roo/rules/`, `~/.roo/commands/`, `~/.roo/skills/`,
`~/.agents/skills/`, and `custom_modes.yaml`. **Project config takes precedence over global** on
conflict (workspace wins).

**gald3r writes**: `AGENTS.md` (root), `.roo/rules/` (g-rl-*), `.roo/skills/<name>/SKILL.md`
(g-skl-*), `.roo/commands/g-*.md` (g-* slash commands), `.roomodes` (g-agnt-* personas as custom
modes), and `.roo/mcp.json` (if MCP servers are shared).
**Roo owns**: the `.roo/` namespace, the rules/skills load order, the `.roomodes` schema, and mode
selection.

---

## 2. AI Instruction File

Roo auto-loads **`AGENTS.md`** (fallback `AGENT.md`) from the workspace root by default — disable via
`"roo-cline.useAgentRules": false`. It loads **after** mode-specific rules but **before** generic
rule directories. There is **no `CLAUDE.md`/`GEMINI.md` variant**; the legacy single-file `.roorules`
is a separate rules surface. `AGENTS.md` is the natural canonical gald3r instruction file for Roo
(matches the ecosystem default).

gald3r generates/merges `AGENTS.md` via the setup + parity pipeline.

## 3. Agents Support — ✅ NATIVE (modes)

- Roo has **no separate `agents/` folder**; its agent/sub-agent analog is the **mode system** —
  built-in modes (Code, Architect, Debug, Ask, Orchestrator) plus **custom modes** in `.roomodes`
  (project, YAML/JSON) or `custom_modes.yaml` (global).
- A custom mode has: `slug`, `name`, `description`, `roleDefinition`, `groups` (tool/file-access
  perms incl. `fileRegex`), optional `customInstructions`, and `whenToUse` (drives the Orchestrator /
  boomerang auto-delegation).
- The **Orchestrator** mode decomposes complex tasks and delegates subtasks to other modes
  (boomerang) — model-driven workflow orchestration.
- gald3r `g-agnt-*` personas map to `.roomodes` entries (`roleDefinition` from the agent body).
- Source: https://docs.roocode.com/features/custom-modes

## 4. Skills Support — ✅ NATIVE

- **Agent Skills** — `SKILL.md` packages in `.roo/skills/<name>/` and `.roo/skills-{mode}/<name>/`
  (project, Roo-specific), `.agents/skills/<name>/` (cross-agent), and global `~/.roo/skills/` +
  `~/.agents/skills/`. Frontmatter requires `name` + `description`.
- **Auto-discovered at startup** by directory scan with **progressive disclosure** — metadata is
  indexed; the full body loads only when a request matches the skill's `description` ("skills remain
  dormant until activated — they don't bloat your base prompt"). No registration required.
- Priority: project > global, `.roo/` > `.agents/`, mode-specific > generic.
- gald3r `g-skl-*/SKILL.md` load natively — the Cursor auto-relevance contract IS honored here.
- **Recency note**: relatively new — the Skills page is dated **2026-05-15** (introduced ~v3.38, late
  2025, expanded into 2026), the same day the product shut down.
- Source: https://docs.roocode.com/features/skills

## 5. Commands / Workflows — ✅ NATIVE

- **Custom slash commands**: markdown files in `.roo/commands/` (project) or `~/.roo/commands/`
  (global); **filename = command name** (e.g. `.roo/commands/deploy.md` → `/deploy`). Optional
  `mode` frontmatter switches mode. Precedence: project > global > built-in.
- Also invokable **programmatically by the agent** via the `run_slash_command` tool (e.g. chain
  `/init`, `/review` into automated workflows).
- gald3r `@g-*` commands map cleanly to `.roo/commands/g-*.md` (the `/g-*` form).
- Source: https://docs.roocode.com/features/slash-commands

## 6. Hooks System — ❌ NOT SUPPORTED

- Roo has **NO native lifecycle/event hook system**. There is no docs "Hooks" feature page and no
  `sessionStart` / `preToolUse` / `postToolUse` / `beforeShellExecution` / file-watch wiring, and no
  `hooks.json` / `.roo/hooks/` config.
- The closest official automation feature is **experimental Custom Tools** (TypeScript/JavaScript
  tool definitions Roo calls like `read_file()` / `execute_command()`) — but these are
  **model-invoked tools, NOT deterministic event hooks**. Lifecycle/prompt-based hooks and a
  `.roo/hooks/` JSON design exist only as community ENHANCEMENT requests (GitHub issues #11504,
  #12025; discussion #6147) and were **never shipped or documented before shutdown**.
- gald3r's PowerShell hooks (`g-hk-*.ps1`) **cannot be auto-fired** by Roo. They must run manually,
  via VS Code tasks, or via git hooks (`core.hooksPath`) for the commit/push subset. This is the
  largest gap vs. the Cursor reference.
- Source: https://docs.roocode.com/features/experimental/custom-tools

## 7. Rules / Memory — ✅ NATIVE

- **Modern form**: `.roo/rules/` (all modes) and `.roo/rules-{slug}/` (per-mode). Files are read
  **recursively, sorted alphabetically (case-insensitive)**, and appended to the system prompt;
  mode-specific rules appear **before** general rules.
- **Legacy fallback**: single files `.roorules` / `.roorules-{slug}` at repo root (used when the
  `.roo/` dirs are empty/missing). Roo also reads **`.clinerules`** for Cline compatibility.
- **Precedence**: Global (`~/.roo/rules/`) vs Project (`.roo/rules/`) — **workspace rules win on
  conflict** and take precedence over global. Within the prompt: mode-specific rules → `AGENTS.md` →
  generic rules.
- **Extension**: plain **`.md`** (NOT Cursor's `.mdc`) — parity sync maps `.mdc` → `.md`.
- **Memory**: no native "memory bank"; `memory-bank/` is an inherited Cline convention (markdown the
  agent is instructed to read), not Roo-native. gald3r durable facts live in
  `.gald3r/learned-facts.md`, surfaced by `g-rl-25`.
- gald3r `g-rl-*` map to `.roo/rules/` (for `alwaysApply: true`) or mode-scoped `.roo/rules-{slug}/`.
- Source: https://docs.roocode.com/features/custom-instructions

## 8. MCP Support — ✅ NATIVE

- **Model Context Protocol** — first-class support. Project-level **`.roo/mcp.json`** (committable,
  team-shareable, auto-detected) and global `mcp_settings.json`; **project config takes precedence**
  on name collision.
- Agent tools `use_mcp_tool` and `access_mcp_resource`; a server-management UI with per-server
  enable/disable + timeout; **STDIO** and **SSE/streamable-HTTP** transports. Disabling MCP globally
  removes `use_mcp_tool` / `access_mcp_resource`.
- Source: https://docs.roocode.com/features/mcp/using-mcp-in-roo

## 9. Other Extensibility (not hooks)

- **Experimental Custom Tools** — TS/JS tool definitions Roo calls like native tools; ship tool
  schemas alongside the repo so teammates share workflow steps. Experimental, model-invoked.
- **`run_slash_command` tool** — agent-callable execution of slash commands for chained workflows.
- **`.rooignore`** — gitignore-style file controlling which files the agent can access.
- **Settings Management** — Import/Export/Reset of settings for sharing config across machines.
- **Cross-agent `.agents/skills/`** — Skills also resolve from the shared `.agents/` path, in
  addition to the Roo-specific `.roo/skills/`.

---

## Parity vs. Cursor Reference

Roo reaches **near-full parity** with the Cursor reference (`g-skl-platform-cursor`): native
**commands, rules, agents (modes), skills, and MCP**. The single hard gap is **hooks** — no native
lifecycle events, so gald3r `g-hk-*.ps1` must run via git `core.hooksPath` / VS Code tasks. The
Orchestrator/boomerang mode is the nearest analog to deterministic pipelines but is model-driven, not
a hook system.

**gald3r mapping is strong**: `AGENTS.md` (canonical), `.roo/rules/` (g-rl-*), `.roo/skills/`
(g-skl-*/SKILL.md, auto-relevance honored), `.roo/commands/` (g-* slash commands), `.roomodes`
(g-agnt-* personas as custom modes), `.roo/mcp.json`. **Only the PowerShell lifecycle hooks have no
auto-fire host.** The dominant caveat remains that the platform is **discontinued (2026-05-15)** — any
investment targets a frozen tool.

## Hook System

- **Type**: none
- **Config file**: n/a (no `hooks.json`; no `.roo/hooks/`; no event wiring)
- **Events available**: none — no `sessionStart` / `preToolUse` / `postToolUse` /
  `beforeShellExecution` / file-watch
- **Event payload format**: none
- **Command extensions**: n/a
- **Limitations**: closest in-product automation is experimental **Custom Tools** (model-invoked TS/JS
  tools) + **Orchestrator/boomerang** task spawning and the `run_slash_command` tool — model-driven,
  not deterministic lifecycle events. A `.roo/hooks/` design exists only as unshipped community
  proposals (GitHub #11504, #12025, discussion #6147).
- **gald3r hook files**: `g-hk-*.ps1` do **not** auto-fire — run manually, via VS Code tasks, or via
  git hooks (`core.hooksPath`) for the commit/push subset.

## Atypical Handling

- VS Code extension; **discontinued 2026-05-15** — frozen/archived, not maintained. Migration is to
  Cline / Kilo Code.
- Agents are **modes** (`.roomodes`), not files. Rules live in `.roo/rules/` (+ legacy `.roorules*` /
  `.clinerules`). Skills use the `SKILL.md` standard via `.roo/skills/` + `.agents/skills/`.
- `docs.roocode.com` 301-redirects to `roocodeinc.github.io/Roo-Code/`.

## gald3r Integration Notes

- Ship `AGENTS.md` + `.roo/rules/` + `.roo/skills/` + `.roo/commands/` + `.roomodes` + `.roo/mcp.json`
  — Roo discovers all of them natively.
- Hooks cannot be auto-fired: use git `core.hooksPath` for commit/push gates; express the rest as
  rule text, custom modes, or VS Code tasks.
- Re-verify on the next `@g-platform-scan-docs roo` (crawl_max_age_days: 14) — but note the platform
  is discontinued, so the docs are unlikely to change.

---

## Capability Summary (copy into PLATFORM_STATUS.md row)

| Hooks | Rules | Skills | Commands | MCP | Docs Fresh |
|---|---|---|---|---|---|
| ❌ | ✅ | ✅ | ✅ | ✅ | ✅ |

Legend: ✅ verified working · ⚠️ partial / Cursor-generic · ❌ not supported · ❓ untested.

---

## Verification Evidence (docs crawl 2026-06-02, https://docs.roocode.com)

| Capability | How verified |
|---|---|
| Commands | /features/slash-commands — `.roo/commands/*.md` (filename = command), optional `mode` frontmatter, `run_slash_command` tool; project > global > built-in |
| Rules | /features/custom-instructions — `.roo/rules/` + `.roo/rules-{slug}/` (recursive, alphabetical); `.roorules` / `.clinerules` fallback; workspace rules win over global |
| Agents | /features/custom-modes — `.roomodes` (YAML/JSON); slug/name/roleDefinition/groups(fileRegex)/whenToUse; Orchestrator/boomerang delegation |
| Skills | /features/skills — `SKILL.md` in `.roo/skills/` + `.roo/skills-{mode}/` + `.agents/skills/`; auto-discovered, progressive disclosure; page dated 2026-05-15 (~v3.38) |
| Hooks | No "Hooks" feature page — no `hooks.json` / lifecycle events (negative confirmation). Custom Tools (/features/experimental/custom-tools) are model-invoked tools, not hooks; `.roo/hooks/` is unshipped community proposal (#11504, #12025, #6147) |
| MCP | /features/mcp/using-mcp-in-roo — project `.roo/mcp.json` (precedence over global), `use_mcp_tool`/`access_mcp_resource`, STDIO + SSE/HTTP |
| AGENTS.md | /features/custom-instructions — auto-loaded unless `roo-cline.useAgentRules:false`; loads after mode rules before generic |
| Lifecycle | Roo Code **discontinued 2026-05-15** (announced 2026-04-21); docs/repos archived, extension still functions; migrate to Cline / Kilo Code |
