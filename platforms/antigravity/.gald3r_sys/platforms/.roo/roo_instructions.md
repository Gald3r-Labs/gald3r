# Roo Code Platform -- gald3r Configuration Guide

**Platform**: Roo Code (formerly Roo Cline -- open-source VS Code extension, multi-mode agentic, forked from Cline)
**Config Folder**: `.roo/` (modern, directory-based) with root single-file legacy fallbacks
**gald3r Version**: 1.0.0
**Official Docs**: https://docs.roocode.com
**Instruction File**: root `AGENTS.md` (auto-loaded unless `roo-cline.useAgentRules: false`)
**Authoritative skill**: `g-skl-platform-roo`
**Capability detail**: see `PLATFORM_SPEC.md` in this directory (Phase 1, T1469)

---

## Folder Layout

```
<project-root>/
|-- .roo/
|   |-- rules/                  # general rules, ALL modes (recursive, alphabetical) -- MODERN form
|   |   `-- g-rl-*.md
|   |-- rules-{slug}/           # mode-specific rules (e.g. rules-architect/) -- MODERN form
|   |   `-- *.md
|   |-- commands/               # project slash commands (filename = command name) -- *.md
|   |   `-- g-*.md
|   `-- mcp.json                # project-level MCP server config (team-shareable)
|-- .roomodes                   # custom mode definitions (YAML preferred; JSON accepted)
|-- AGENTS.md                   # auto-loaded agent rules (gald3r canonical instruction file)
|
|  -- legacy single-file fallbacks (used only when .roo/ dirs are empty/missing) --
|-- .roorules                   # general rules fallback (~ .roo/rules/)
|-- .roorules-{slug}            # mode-specific rules fallback (~ .roo/rules-{slug}/)
`-- .clinerules                 # Cline-compatibility fallback (Roo can read it)
```

Rules use the plain **`.md`** extension (NOT Cursor's `.mdc`). The parity sync maps `.mdc` -> `.md`.

**What Roo does NOT have:**
- No native lifecycle hooks -- no `hooks.json`, no `sessionStart` / `stop` / `preToolUse` / `beforeShellExecution`. gald3r `g-hk-*.ps1` hooks must be run manually, via VS Code tasks, or via git `core.hooksPath` (commit/push subset only). See PLATFORM_SPEC.md S6/S9.
- No `agents/` folder -- Roo uses the **mode system** (built-in: Code, Architect, Debug, Ask, Orchestrator) plus custom modes in `.roomodes`.
- No native folder-per-skill auto-load -- skills surface as slash commands (`.roo/commands/`) or are referenced by name from rules.

---

## What Makes Roo Unique

### Mode System
Built-in modes are **Code, Architect, Debug, Ask, Orchestrator**. Each can carry mode-specific
rules via `.roo/rules-{slug}/` (modern) or `.roorules-{slug}` (legacy). gald3r ships an Architect
rule subset so design work reads PLAN.md / CONSTRAINTS.md. Mode-specific rules appear **before**
general rules in the system prompt.

### Custom Modes (agents analog)
gald3r `g-agnt-*` personas have no auto-discovered file form on Roo. They could be expressed as
custom modes in `.roomodes` (`slug` / `name` / `roleDefinition` / `groups` / `customInstructions`
/ `whenToUse`). As of T1510 this scaffold SHIPS `.roomodes` with 4 gald3r roles
(g-task-manager, g-qa-engineer, g-code-reviewer, g-infrastructure).

### Rules Load Order
Global (`~/.roo/`) then project (`project/.roo/`, precedence on conflict). Within the prompt:
mode-specific rules, then `AGENTS.md`, then generic rules. The modern `.roo/rules/` dir takes
precedence over the legacy `.roorules` single file when both are present.

### Slash Commands
`.roo/commands/*.md` (filename = command name -> `/command-name`); also invokable by the agent via
the `run_slash_command` tool. gald3r `g-*` commands map to `.roo/commands/g-*.md`.

### Boomerang / Orchestrator Orchestration
Roo can spawn sub-tasks in different modes. Sub-tasks may not inherit rules -- verify cross-mode
rule loading.

---

## gald3r Naming Conventions

| Component | Surface |
|-----------|---------|
| Skills | slash commands (`.roo/commands/g-skl-*.md`) or referenced by name (no native auto-load) |
| Agents | Roo modes (built-in) / custom modes (`.roomodes`, ships 4 gald3r roles as of T1510) |
| Commands | `.roo/commands/g-*.md` (slash commands) |
| Rules | `.roo/rules/` + `.roo/rules-architect/` (modern); `.roorules` + `.roorules-architect` + `.clinerules` (legacy fallback) |

---

## Config Files Shipped (this scaffold)

> **Modernized (T1510):** this scaffold now ships the **modern `.roo/` directory form** alongside
> the legacy single-file fallback. The modern form is the recommended target; the legacy
> `.roorules` files are retained only for older Roo Code versions.

**Modern form (`.roo/` directory):**
- **`.roo/rules/g-rl-gald3r.md`** -- gald3r always-apply rule subset (task gate, commit format, bug protocol), all modes.
- **`.roo/rules-architect/g-rl-architect.md`** -- gald3r architecture context for the built-in Architect mode.
- **`.roo/commands/g-*.md`** -- representative gald3r `g-*` commands as slash commands (`/g-status`, `/g-task-new`, `/g-bug-report`, `/g-plan`, `/g-git-commit`, `/g-code-review`). Filename = command name; frontmatter is `description` / `argument-hint` / optional `mode`.
- **`.roo/mcp.json`** -- project MCP config, shipped as an annotated REFERENCE TEMPLATE with all servers `"disabled": true` (no live endpoints). Top-level key is `mcpServers`.
- **`.roomodes`** -- gald3r agent roles (`g-agnt-*`) as Roo custom modes (YAML), since Roo has no `agents/` folder. Fields: `slug` / `name` / `description` / `roleDefinition` / `whenToUse` / `groups` (read|edit|command|mcp, with `fileRegex` scoping) / `customInstructions`.

**Legacy single-file fallback (retained):**
- **`.roorules`** -- gald3r always-apply rule subset.
- **`.roorules-architect`** -- Architect-mode rule subset.

Roo reads the legacy single files only when the corresponding `.roo/rules/` directories are
empty/missing, so the modern dir form takes precedence automatically. The legacy files are kept
solely as a safety net for older Roo Code builds.

---

## MCP

Roo has first-class MCP (`use_mcp_tool` / `access_mcp_resource`). Project-level config lives in
`.roo/mcp.json` (committable, team-shareable, precedence over the global `mcp_settings.json` on
name collision). The top-level key is `mcpServers`. STDIO servers use `command`/`args`/`env`;
remote servers use `type` (`sse` | `streamable-http`) + `url`/`headers`. This scaffold ships an
**annotated reference template** at `.roo/mcp.json` with every server `"disabled": true` (no live
endpoints) -- fill in real values and flip `disabled` to activate. The active server set is
per-project.

---

## gitignore Decision (T1277 AC6)

`.roorules`, `.roorules-architect`, `.roo/rules/*.md`, and `.roo/commands/*.md` are **source** --
keep them tracked. `.roo/mcp.json` is committable when the server set is team-shared. Roo writes no
generated project output directory of its own, so no gitignore entry is needed in installed projects.

---

## Verification

```powershell
Test-Path .roo/rules            # modern rules dir (now shipped)
Test-Path .roo/rules-architect  # modern architect-mode rules
Test-Path .roo/commands         # slash commands
Test-Path .roo/mcp.json         # MCP reference template
Test-Path .roomodes             # custom modes
Test-Path .roorules             # legacy single-file fallback (retained)
```

---

## Common Pitfalls

- The modern `.roo/rules/` dir takes precedence over the legacy `.roorules` single file -- do not
  expect both to be additive when the dir is populated.
- Mode-specific rules load **before** general rules; do not rely on general rules overriding them.
- Boomerang / Orchestrator sub-tasks may run in a different mode -- test cross-mode rule loading.
- gald3r `g-hk-*.ps1` hooks do NOT auto-fire on Roo (no native hook system) -- wire the commit/push
  subset via git `core.hooksPath` if needed.
