# JetBrains Junie Platform — gald3r Configuration Guide

**Platform**: JetBrains Junie (AI assistant plugin in IntelliJ / PyCharm / WebStorm / GoLand / etc., plus a terminal/CLI mode)
**Config Folder**: `.junie/`
**gald3r Version**: 1.0.0
**Official Docs**: https://junie.jetbrains.com/docs
**Primary instruction file**: `.junie/AGENTS.md` (preferred); `.junie/guidelines.md` is legacy-but-supported
**Authoritative skill**: `g-skl-platform-junie`
**Verified findings**: see `PLATFORM_SPEC.md` in this folder (read §9 Known Gaps first)

---

## Folder Layout

```
.junie/
├── AGENTS.md          # PREFERRED guidelines file, auto-injected into every task
├── guidelines.md      # LEGACY guidelines (still supported by older Junie builds)
└── mcp/
    └── mcp.json       # project-level MCP server config (commit & share with team)

AGENTS.md              # root AGENTS.md is also honored (search-order fallback)

(platform-owned, not gald3r-authored)
~/.junie/              # user/global config incl. global MCP
IDE settings           # custom guidelines path, Action Allowlist, subscription
```

Junie guidelines search order: custom IDE-settings path -> `.junie/AGENTS.md` -> root
`AGENTS.md` -> legacy `.junie/guidelines.md` (or `.junie/guidelines/`).

**What Junie does NOT have:**
- No project `agents/` folder — Junie is a single agentic assistant; describe gald3r roles inside `AGENTS.md`.
- No `commands/` folder — no custom slash-command framework; interaction is conversational + MCP tools.
- No `rules/` folder — no `.mdc` / `alwaysApply` / `globs` discovery; behavioral guidance lives in `AGENTS.md` (single-file).
- No `skills/` discovery — no `SKILL.md` mechanism; extensibility goes through MCP tools, not skills.
- No `hooks/` folder — no lifecycle-event system; the Action Allowlist is an approval gate, NOT a hook bus, and cannot run gald3r `.ps1` hooks.

---

## What Makes Junie Unique

### MCP (strong fit)
Junie connects to Model Context Protocol servers natively. Project-level config lives at
`.junie/mcp/mcp.json` (commit & share); personal servers go in `~/.junie/` / the IDE MCP
Settings panel. The Action Allowlist authorizes Junie to run MCP tools without per-call
confirmation (currently an all-MCP grant — you cannot yet scope it to specific servers).
See `mcp/mcp.json` in this folder for a reference template.

### Persistent guidelines / memory (the other strong fit)
`.junie/AGENTS.md` is read in full and injected into every task's prompt context. It is the
gald3r always-apply analogue — task workflow, commit format, bug protocol, and role
descriptions all live there. It is single-file (no glob-scoped rule set).

### PSI-Backed Code Intelligence
Junie uses the JetBrains Program Structure Interface (PSI) for deep code navigation. Path-based
gald3r references generally work; prefer IDE-relative paths where a rule assumes a shell-relative path.

### Agent Mode + Run Configurations
Junie can execute multi-step tasks and trigger IDE run-configurations. Keep `AGENTS.md` focused so the injected context budget stays small.

---

## gald3r Naming Conventions

| Component | Surface on Junie |
|-----------|------------------|
| Instructions/Rules | `.junie/AGENTS.md` (preferred) / `.junie/guidelines.md` (legacy) — single-file, no glob scoping |
| Skills | (none) — no `SKILL.md` discovery; extend via MCP tools |
| Agents | (none) — single assistant; describe roles in `AGENTS.md` |
| Commands | (none) — conversational + MCP tools |
| Hooks | (none) — Action Allowlist is approval gating, not a hook bus |
| MCP | `.junie/mcp/mcp.json` (project) + `~/.junie/` / IDE MCP Settings (global) — strongest surface |

---

## Config Files Shipped

- **`.junie/AGENTS.md`** — preferred gald3r guidelines (task workflow, commit format, bug protocol, role notes).
- **`.junie/guidelines.md`** — legacy mirror for older Junie builds.
- **`.junie/mcp/mcp.json`** — REFERENCE TEMPLATE for project-level MCP servers (edit before use; no server wired by default).

---

## gitignore Decision (T1277 AC6)

`.junie/AGENTS.md` and `.junie/guidelines.md` are **source** — keep them tracked.
`.junie/mcp/mcp.json` is meant to be committed & shared (it carries no secrets in the template).
Junie writes no generated output directory in the project root, so no gitignore entry is needed.

---

## Verification

```powershell
Test-Path .junie/AGENTS.md
Test-Path .junie/mcp/mcp.json
```

---

## Common Pitfalls

- Junie requires an active JetBrains AI subscription.
- Guidelines are read at task start — changes take effect on next Junie activation.
- PSI-based navigation may need IDE-relative paths where shell-relative paths are assumed.
- The MCP config is a TEMPLATE — Junie does nothing with it until you supply real server commands.

> **SCAN_DOCS not yet run** (`last_doc_scan: never`). Confirm the exact guidelines search-order,
> Action-Allowlist/MCP scoping, and any 2026 additions via `@g-platform-scan-docs junie` against
> https://junie.jetbrains.com/docs and the JetBrains help pages.
