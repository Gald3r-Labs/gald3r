---
subsystem_memberships: [PLATFORM_INTEGRATION]
platform: roo
authoring_path: update
docs_url: https://docs.roocode.com
docs_url_secondary:
  - https://docs.roocode.com/features/custom-instructions
  - https://docs.roocode.com/features/custom-modes
  - https://docs.roocode.com/features/slash-commands
  - https://docs.roocode.com/features/mcp/using-mcp-in-roo
crawl_max_age_days: 14
vault_doc_path: research/platforms/roo/
last_doc_scan: never
reference: g-skl-platform-cursor
status: ⚠️
---

# PLATFORM_SPEC.md — Roo Code

**Roo Code** (formerly Roo Cline) is an open-source agentic coding extension for **VS Code**,
forked from Cline. It diverges from Cline most visibly in its **mode system** (built-in + custom
modes), its **directory-based rules** (`.roo/rules/` and `.roo/rules-{slug}/`), **project-level
slash commands** (`.roo/commands/`), and **project-level MCP config** (`.roo/mcp.json`).

> **Authoring path: UPDATE** — `g-skl-platform-roo/SKILL.md` already ships. This spec records the
> verified findings against the official docs (docs.roocode.com, crawled 2026-05-26 via WebFetch /
> WebSearch — NOT a `@g-platform-scan-docs` run, so `last_doc_scan: never` until that runs).

> **Honesty note**: This spec is grounded in current Roo Code documentation, NOT in a live install
> test inside this repo (there is no `.roo/` checkout here). Capabilities confirmed by docs are
> marked ⚠️ ("doc-confirmed, install-untested") rather than ✅. No claim is fabricated; untested
> items are ❓.

---

## 1. Folder Hierarchy

Roo Code reads configuration from a repo-root `.roo/` directory (modern, directory-based) with
legacy single-file fallbacks at the repo root. Doc-confirmed layout:

```
<project-root>/
├── .roo/
│   ├── rules/                  ← general rules, ALL modes (recursive, alphabetical) — modern form
│   │   └── g-rl-*.md
│   ├── rules-{slug}/           ← mode-specific rules (e.g. rules-code/, rules-architect/)
│   │   └── *.md
│   ├── commands/               ← project slash commands (filename = command name) — *.md
│   │   └── g-*.md
│   └── mcp.json                ← project-level MCP server config (team-shareable)
├── .roomodes                   ← custom mode definitions (YAML preferred; JSON accepted)
├── AGENTS.md                   ← auto-loaded agent rules (unless roo-cline.useAgentRules:false)
│
│  ── legacy single-file fallbacks (used only when .roo/ dirs are empty/missing) ──
├── .roorules                   ← general rules fallback (≈ .roo/rules/)
├── .roorules-{slug}            ← mode-specific rules fallback (≈ .roo/rules-{slug}/)
├── .clinerules                 ← Cline-compatibility fallback (Roo can read it)
└── memory-bank/                ← optional Cline-style persistent memory (convention, not native)
```

**Global (per-user) equivalents** live under `~/.roo/rules/`, `~/.roo/rules-{slug}/`,
`~/.roo/commands/`, and `custom_modes.yaml`. Project config takes precedence over global on conflict.

**gald3r writes** (recommended modern targets): `.roo/rules/` (general gald3r rule subset),
`.roo/rules-architect/` (architecture context), `.roo/commands/` (gald3r `@g-*` commands as slash
commands), `.roo/mcp.json` (if MCP servers are shared), and `AGENTS.md` at root.
**Current gald3r deploy scaffold** (`.gald3r_sys/platforms/.roo/`) ships the **legacy** form only:
`.roorules`, `.roorules-architect`, with `.clinerules` fallback — see §9 Known Gaps.
**Roo owns**: the `.roo/` namespace, the rules load order, the `.roomodes` schema, and mode
selection.

## 2. AI Instruction File

Roo auto-loads **`AGENTS.md`** (or fallback `AGENT.md`) from the workspace root unless
`"roo-cline.useAgentRules": false` is set. It loads after mode-specific rules but before generic
rules. This makes `AGENTS.md` the natural canonical gald3r instruction file for Roo — consistent
with the gald3r ecosystem default. Roo does not use a `CLAUDE.md`/`GEMINI.md` variant; the legacy
single-file `.roorules` is the rules surface (§7), distinct from the `AGENTS.md` agent-rules surface.

gald3r generates/merges `AGENTS.md` via the setup + parity pipeline.

## 3. Agents Support

Roo has **no `agents/` folder concept** like Cursor's `.cursor/agents/g-agnt-*.md`. Its analog is
the **mode system**: built-in modes (Code, Architect, Debug, Ask, Orchestrator) plus **custom
modes** defined in `.roomodes` (project) or `custom_modes.yaml` (global).

- A custom mode has: `slug`, `name`, `description`, `roleDefinition`, `groups` (allowed toolsets /
  file-access perms: read, edit, command, mcp — `edit` supports regex `fileRegex`), optional
  `customInstructions`, and `whenToUse` (for automated orchestration).
- gald3r `g-agnt-*.md` agent personas **do not map 1:1**. They could be expressed as custom modes
  (each `g-agnt-*` → a `.roomodes` entry with `roleDefinition` from the agent body), but the
  current gald3r Roo scaffold does NOT generate `.roomodes` — agents are documented only.
- **Status**: ⚠️ partial — mode mechanism is doc-confirmed; gald3r-agent-to-mode generation is not
  implemented (Known Gap §9).

## 4. Skills Support

Roo Code has **no native folder-per-skill discovery** equivalent to Cursor's `.cursor/skills/<name>/SKILL.md`
auto-relevance loading. There is no `skills/` directory that Roo scans and auto-loads by relevance.

- Practical gald3r mapping: skills are surfaced as **slash commands** (`.roo/commands/g-skl-*.md`)
  or referenced by name from rules. A skill's behavior must be invoked explicitly, not auto-loaded
  on model-judged relevance.
- **Status**: ❌/⚠️ — no native skill auto-load; the closest working surface is `.roo/commands/`.
  Marked ⚠️ because skills can be reached via commands, but the Cursor auto-relevance contract is
  not honored.

## 5. Commands / Workflows

Roo Code supports **project-level slash commands** (doc-confirmed, current docs + 3.x release notes):

- **Location**: `.roo/commands/` (project) or `~/.roo/commands/` (global). **Filename = command
  name** (e.g. `.roo/commands/deploy.md` → `/deploy`).
- **Format**: markdown files. Roo ships a UI for create/edit/delete with fuzzy search.
- **Invocation**: `/command-name` in the chat; also invokable by the agent via the
  `run_slash_command` tool.
- gald3r `@g-*` commands map cleanly to `.roo/commands/g-*.md` (the `/g-*` form). The current Roo
  scaffold does NOT yet ship a `.roo/commands/` payload (Known Gap §9).
- **Status**: ⚠️ — slash-command mechanism is doc-confirmed; gald3r command propagation to
  `.roo/commands/` is not yet wired.

## 6. Hooks System

Roo Code has **NO native lifecycle hook system**. There is no `hooks.json`, no `sessionStart` /
`stop` / `preToolUse` / `beforeShellExecution` event wiring comparable to Cursor's `.cursor/hooks.json`.

- gald3r's PowerShell hooks (`g-hk-*.ps1`) **cannot be auto-fired** by Roo. They must be run
  manually, via VS Code tasks, or via git hooks (`core.hooksPath`) for the commit/push subset.
- The closest in-product automation is **custom modes + boomerang/Orchestrator** task spawning and
  the `run_slash_command` tool — but these are model-driven, not deterministic lifecycle events.
- **Status**: ❌ — no native hooks. This is the largest gap vs. the Cursor reference.

## 7. Rules / Memory

- **Modern form**: `.roo/rules/` (all modes) and `.roo/rules-{slug}/` (per-mode). Files are read
  **recursively, sorted alphabetically (case-insensitive)**, with cache/temp files excluded
  (`.DS_Store`, `*.bak`, `*.log`, …). Mode-specific rules appear **before** general rules in the
  system prompt.
- **Legacy fallback**: single files `.roorules` and `.roorules-{slug}` at repo root, used only when
  the corresponding `.roo/` directories are empty/missing. Roo also reads `.clinerules` (Cline
  compatibility).
- **Extension**: plain **`.md`** (NOT Cursor's `.mdc`). The parity sync maps `.mdc` → `.md`.
- **Load order**: Global (`~/.roo/`) → Project (`project/.roo/`, takes precedence on conflict).
  Within the prompt: mode-specific rules, then `AGENTS.md`, then generic rules.
- **Memory**: no native "memory bank" — `memory-bank/` is an inherited Cline convention (markdown
  files the agent is instructed to read), not a Roo-native feature. gald3r durable facts live in
  `.gald3r/learned-facts.md` and are surfaced by `g-rl-25`.
- **Status**: ✅ doc-confirmed mechanism (rules); ⚠️ for memory-bank (convention only).

## 8. MCP Support

- **Supported**: ✅ Yes (doc-confirmed). Roo has first-class MCP with `use_mcp_tool` /
  `access_mcp_resource` tools and a server-management UI.
- **Config**: **project-level `.roo/mcp.json`** (committable, team-shareable) and a global settings
  file (`mcp_settings.json` via the MCP settings UI). Project config takes precedence over global on
  name collision.
- **Discovery/timeout**: servers are connected on startup; per-server enable/disable and timeout
  controls exist in the MCP UI.
- **Status**: ⚠️ — mechanism doc-confirmed and robust; the concrete gald3r `.roo/mcp.json` payload
  is not shipped by the current scaffold, and the active server set is per-machine (untested here).

## 9. Known Gaps vs. Cursor Reference

Using the Common-vs-Platform-Specific decision tree (`g-skl-platform-cursor/SKILL.md` §4a):

1. **No native hooks** (❌, hard gap). Cursor's `.cursor/hooks.json` (sessionStart/stop/preToolUse/
   beforeShellExecution) has no Roo equivalent. gald3r hooks run manually / via git `core.hooksPath`
   only. → documented gap (cannot live in common `.gald3r_sys/` as auto-fired).
2. **No native skill auto-load** (⚠️). Cursor folder-per-skill auto-relevance is absent; skills must
   be surfaced as `.roo/commands/` or invoked by name. → platform-specific workaround.
3. **Agents ≠ files; agents = modes** (⚠️). `g-agnt-*.md` do not auto-discover; they would need
   generation into `.roomodes` custom modes. Not implemented. → platform-specific config gap.
4. **Scaffold is legacy-form only** (⚠️). `.gald3r_sys/platforms/.roo/` currently ships
   `.roorules` / `.roorules-architect` / `.clinerules` (root single-file legacy form) and does NOT
   ship the modern `.roo/rules/`, `.roo/rules-architect/`, `.roo/commands/`, `.roo/mcp.json`, or
   `.roomodes`. Roo still reads the legacy form, so the deploy WORKS, but it does not use the
   modern directory layout. → follow-up needed to modernize the scaffold.
5. **`.mdc` → `.md` mapping** (handled). Roo uses `.md`; parity sync maps the extension. Correctly
   classified platform-specific.
6. **SCAN_DOCS not yet run** (❓). `last_doc_scan: never`. Claims here are from a manual 2026-05-26
   WebFetch/WebSearch of docs.roocode.com, not a `@g-platform-scan-docs roo` crawl. Flip Docs-Fresh
   to ✅ after the crawl.

---

## Capability Summary (copy into PLATFORM_STATUS.md row)

| Hooks | Rules | Skills | Commands | MCP | Docs Fresh |
|---|---|---|---|---|---|
| ❌ | ✅ | ⚠️ | ⚠️ | ⚠️ | ❓ |

Legend: ✅ verified working · ⚠️ partial / Cursor-generic / doc-confirmed-but-install-untested · ❌ not supported · ❓ untested.

---

## Verification Evidence

| Capability | How verified |
|---|---|
| Folder hierarchy | docs.roocode.com custom-instructions + custom-modes + slash-commands (WebFetch 2026-05-26); local `.gald3r_sys/platforms/.roo/` scaffold inspected (legacy form only) |
| Rules (dirs + precedence) | custom-instructions doc: `.roo/rules/`, `.roo/rules-{slug}/`, recursive + alphabetical load, global→project precedence, mode-specific before general; `.roorules` fallback |
| AGENTS.md | custom-instructions doc: auto-loaded unless `roo-cline.useAgentRules:false`, loads after mode rules before generic |
| Modes (agents analog) | custom-modes doc: `.roomodes` (YAML/JSON), fields slug/name/roleDefinition/groups/customInstructions/whenToUse, `fileRegex` restrictions |
| Commands | slash-commands doc + 3.x release notes: `.roo/commands/*.md`, filename=command, `run_slash_command` tool |
| Hooks | No hooks feature found in docs — Roo has no `hooks.json` / lifecycle events (negative confirmation) |
| MCP | using-mcp-in-roo doc: project `.roo/mcp.json` (team-shareable, precedence over global), `use_mcp_tool`/`access_mcp_resource` |
| Skills | No native folder-per-skill auto-load in docs; closest surface is `.roo/commands/` (negative confirmation) |
| Docs freshness | Manual WebFetch/WebSearch 2026-05-26; NOT a SCAN_DOCS run — `last_doc_scan: never` |
