# Kiro IDE Platform — gald3r Configuration Guide

**Platform**: Kiro (Amazon's spec-driven AI IDE, built on VS Code)
**Config Folder**: `.kiro/`
**gald3r Version**: 1.0.0
**Official Docs**: https://kiro.dev/docs
**Config Surface**: `.kiro/steering/` (always-injected), `.kiro/specs/`, `.kiro/hooks/` (JSON), `.kiro/settings/mcp.json`
**Authoritative skill**: `g-skl-platform-kiro`

---

## Folder Layout

```
.kiro/
├── steering/                   # Always-injected context files (.md)
│   ├── gald3r.md               # gald3r task management context
│   ├── product.md              # Product context (maps to .gald3r/PROJECT.md)
│   ├── structure.md            # Codebase structure (Kiro convention; optional)
│   └── tech.md                 # Tech-stack guidance (Kiro convention; optional)
├── specs/                      # Feature specifications
│   └── {feature}/              #   requirements.md, design.md, tasks.md
├── hooks/                      # Native agent hooks — JSON files, NOT .md
│   └── {hook-name}.json        #   schema: name / version / when / then
└── settings/
    └── mcp.json                # Workspace MCP config (~/.kiro/settings/mcp.json = global)
```

**What Kiro maps differently:**
- Steering files replace a `rules/` folder — they are injected automatically (no `alwaysApply`/`globs`)
- Specs map naturally to gald3r PRDs (requirements → AC, design → technical design); a spec
  also has its own `tasks.md` distinct from `.gald3r/tasks/`
- Hooks are **JSON** (`when`/`then` schema), trigger on **file events** (`fileEdited` + glob
  patterns), NOT the gald3r session/tool lifecycle — see Hooks section below

---

## What Makes Kiro Unique

### Spec-Driven Development
Kiro works from structured specs. These are **additive** with gald3r tasks: use Kiro specs
for the Kiro UI and gald3r tasks for tracking. Map `requirements.md` to PRD acceptance
criteria and `design.md` to the PRD technical design.

### Steering Files Are Always Injected
Every file in `.kiro/steering/` is injected into every session. Keep each under ~2K tokens.
`gald3r.md` carries task context; `product.md` mirrors the project mission.

---

## gald3r Naming Conventions

| Component | Kiro surface | Status |
|-----------|--------------|--------|
| Rules | `.kiro/steering/*.md` (always-injected; no per-rule glob scoping) | ⚠️ partial |
| Skills | none — no `SKILL.md` discovery on the IDE; skill knowledge folds into steering | ❌ |
| Agents | none — no agent-file discovery on the IDE; agent roles described in steering | ❌ |
| Commands | none — no `@g-*`/`/g-*` files; document in steering or wire as hook `runCommand` | ⚠️ partial |
| Hooks | `.kiro/hooks/*.json` (file-event driven, not lifecycle) | ⚠️ partial |
| MCP | `.kiro/settings/mcp.json` (workspace) / `~/.kiro/settings/mcp.json` (global) | ✅ |

> Kiro IDE has **no SKILL.md, agent-file, or command-file discovery** (see PLATFORM_SPEC.md
> sections 3–5). Earlier scaffold text describing skills "served from root `skills/`" was
> Cursor-generic and has been corrected. (Kiro **CLI** does support custom agents — see
> `g-skl-platform-kiro-cli` — but that is out of scope for the IDE.)

---

## Hooks (native JSON, file-event)

Kiro hooks are individual JSON files in `.kiro/hooks/` (no central `hooks.json` index). Schema:

```json
{
  "name": "Lint on Save",
  "version": "1.0.0",
  "when": { "type": "fileEdited", "patterns": ["*.py"] },
  "then": { "type": "runCommand", "command": "python3 -m pylint ${file}" }
}
```

- Triggers are **file/save events** (`when.type: fileEdited` + glob `patterns`), supporting
  template vars like `${file}`. The full `when.type` taxonomy beyond `fileEdited` is not yet
  doc-verified (`@g-platform-scan-docs kiro` pending).
- gald3r's PowerShell lifecycle hooks (`sessionStart`/`stop`/`preToolUse`/`beforeShellExecution`)
  have **no native Kiro equivalent** and must run manually. gald3r hooks that map to a
  `fileEdited` trigger CAN be expressed as Kiro hooks, but no `.json` hook is shipped by default.

## MCP

MCP is supported (doc-verified). Config is standard `mcpServers` JSON at `.kiro/settings/mcp.json`
(workspace) or `~/.kiro/settings/mcp.json` (global), with `command`/`args`/`env`/`disabled`/
`autoApprove` fields. No `mcp.json` is shipped by default — add servers via the JSON or the IDE.

---

## Config Files Shipped

- **`.kiro/steering/gald3r.md`** — gald3r task management context.
- **`.kiro/steering/product.md`** — product context placeholder (maps to PROJECT.md).

No `.kiro/hooks/*.json` or `.kiro/settings/mcp.json` is shipped by default — these are
optional, user-authored surfaces documented above.

---

## gitignore Decision (T1277 AC6)

`.kiro/steering/*.md` are **source** — keep them tracked. `.kiro/specs/` authored by hand
are also source. If Kiro generates throwaway spec scratch under `.kiro/specs/`, those may be
gitignored at the user's discretion, but the default install keeps `.kiro/` tracked.

---

## Verification

```powershell
Test-Path .kiro/steering
```

---

## Common Pitfalls

- Steering files are injected in full — keep each under 2K tokens.
- `.kiro/` is shared with Kiro-CLI (see `g-skl-platform-kiro-cli`) — installing for one
  configures the other.
- Kiro specs are additive with gald3r tasks — use both, do not duplicate tracking.
