# Roo Code -- gald3r Deploy Scaffold

**Config folder**: `.roo/` (modern, directory-based) with root single-file legacy fallbacks (`.roorules`).

Authoritative install + customization guide: **`g-skl-platform-roo`** (.gald3r_sys/skills/g-skl-platform-roo/SKILL.md).

See **`PLATFORM_SPEC.md`** in this directory for verified platform capability details (Phase 1 research, T1469).
Deploy artifact modernization (legacy `.roorules` -> `.roo/rules/` + `.roo/commands/` + `.roo/mcp.json` + `.roomodes`): T1510.

## Scaffold contents

| File | Purpose | Form |
|---|---|---|
| `roo_instructions.md` | gald3r setup/configuration guide for Roo Code. | doc |
| `PLATFORM_SPEC.md` | Verified capability matrix and Known Gaps (Phase 1). | doc |
| `.roo/rules/g-rl-gald3r.md` | gald3r always-apply rule subset, all modes. | **modern** |
| `.roo/rules-architect/g-rl-architect.md` | Architect-mode rule subset. | **modern** |
| `.roo/commands/g-*.md` | gald3r `g-*` commands as Roo slash commands (`/g-*`). | **modern** |
| `.roo/mcp.json` | Project MCP config — annotated REFERENCE TEMPLATE (all servers `disabled: true`). | **modern** |
| `.roomodes` | gald3r agent roles (`g-agnt-*`) as Roo custom modes (YAML). | **modern** |
| `.roorules` | gald3r always-apply rule subset (LEGACY single-file fallback for older Roo). | legacy |
| `.roorules-architect` | Architect-mode rule subset (LEGACY single-file fallback). | legacy |

> **Modern vs. legacy**: Roo reads the modern `.roo/rules/` directory and ignores the legacy
> `.roorules` single file when the dir is populated. The legacy single files are retained as a
> fallback for older Roo Code versions whose `.roo/` rule-dir reader is absent/incomplete. New
> installs should rely on the `.roo/` directory form.

## Slash commands shipped (`.roo/commands/`)

Representative subset (filename = command name -> `/g-*`). Each is a `.md` file with verified
frontmatter (`description`, `argument-hint`, optional `mode`):

| Command | Purpose |
|---|---|
| `/g-status` | Read-only gald3r project status overview. |
| `/g-task-new` | Create a gald3r task (file first, then TASKS.md, sequential ID). |
| `/g-bug-report` | Log a gald3r bug (BUGS.md + bug detail file). |
| `/g-plan` | Create/update PLAN.md (switches to Architect mode). |
| `/g-git-commit` | Structured conventional commit with task reference. |
| `/g-code-review` | Comprehensive code review against gald3r standards. |

The full gald3r `g-*` catalog is not mapped 1:1 — this is a sensible starter set. Add more by
dropping additional `.roo/commands/g-*.md` files.

## Custom modes shipped (`.roomodes`)

gald3r agent roles expressed as Roo custom modes (Roo has no `agents/` folder). Schema doc-verified
(slug / name / description / roleDefinition / whenToUse / groups / customInstructions). Conservative
`groups` + `fileRegex` scoping; tighten per project:

| Mode slug | gald3r agent analog |
|---|---|
| `g-task-manager` | Task lifecycle |
| `g-qa-engineer` | Bug tracking / QA |
| `g-code-reviewer` | Code review (read-only) |
| `g-infrastructure` | PROJECT/CONSTRAINTS/SUBSYSTEMS |

## Key platform facts (from PLATFORM_SPEC.md)

- **Instruction file**: root `AGENTS.md` (auto-loaded unless `roo-cline.useAgentRules: false`) -- consistent with the gald3r ecosystem default.
- **Rules (modern)**: `.roo/rules/` (all modes) + `.roo/rules-{slug}/` (per-mode), read recursively + alphabetically; mode-specific before general. Extension is **`.md`**, NOT Cursor's `.mdc`. **This scaffold now ships the modern directory form** (legacy single files retained as fallback).
- **No native hooks** -- no `hooks.json` / `sessionStart` / `stop` / `beforeShellExecution` lifecycle events; PowerShell `g-hk-*.ps1` hooks do not auto-fire (run via git `core.hooksPath` or VS Code tasks).
- **Agents = modes** -- no `agents/` folder; gald3r `g-agnt-*` ship as Roo custom modes in `.roomodes`.
- **Commands = slash commands** -- `.roo/commands/g-*.md` (filename = command); a representative gald3r subset is now shipped.
- **MCP supported** -- project-level `.roo/mcp.json` (team-shareable, precedence over global); shipped as a disabled annotated reference template.

Run `@g-platform-scan-docs roo` to refresh docs freshness (`last_doc_scan: never`).
