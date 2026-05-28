# Cline Platform — gald3r Configuration Guide

**Platform**: Cline (formerly Claude Dev — VS Code extension, agentic)
**Config Folder**: root `.clinerules/` directory (or legacy `.clinerules` file) + optional `memory-bank/`
**gald3r Version**: 1.0.0
**Official Docs**: https://docs.cline.bot
**Authoritative skill**: `g-skl-platform-cline`
**Capability spec**: see `PLATFORM_SPEC.md` in this directory (T1468) — read it before relying on any capability claim below.

---

## Folder Layout

```
<project-root>/
├── .clinerules/            # (modern) rules DIRECTORY — every .md inside is auto-injected
│   ├── gald3r-rules.md     #   gald3r always-apply rule subset
│   └── workflows/          #   workflow files invoked as /<name> (see Commands below)
│       └── *.md
├── .clinerules             # (legacy) single rules FILE — directory form above is preferred
└── memory-bank/            # gald3r/Cline CONVENTION — persistent context (NOT auto-written)
    ├── projectbrief.md
    ├── activeContext.md
    └── progress.md
```

**What Cline does NOT have** (see PLATFORM_SPEC.md sections 3, 4, 6):
- No project `agents/` folder — Cline is a single agentic assistant, no persona registry.
- No skills primitive — gald3r `SKILL.md` files are not auto-discovered.
- No lifecycle `hooks/` system — no `hooks.json`, no sessionStart/preToolUse events.
  Any hook-driven gald3r behavior must become rules text or run out-of-band.

---

## What Makes Cline Unique

### Rules: directory OR single file
Cline reads rules from a **`.clinerules/` directory** (modern, recommended — every `.md`
inside is concatenated and auto-injected) or a single legacy **`.clinerules` file**.
The directory form lets gald3r ship multiple focused rule files. Cline has **no per-rule
glob scoping** (`alwaysApply`/`globs` frontmatter) — all rules in `.clinerules/` are
effectively always-apply. Keep injected content lean (under ~4-8K tokens — large rule
files compete for the model's context window).

### Memory Bank
Cline reads `memory-bank/*.md` for persistent cross-session context, but does **not**
auto-write them — you maintain them. Surface the gald3r mission in
`memory-bank/projectbrief.md`. This is a prompted convention, not a Cline-native store.

### Full Agentic Tool Use
Cline can read/write files, run commands, and browse. Because it acts autonomously,
the gald3r enforcement rules in `.clinerules/` (task gate, bug protocol, commit format)
are the primary guardrail — there is no hook layer to enforce them mechanically.

---

## gald3r Naming Conventions

| Component | Cline surface | Status (see PLATFORM_SPEC.md) |
|-----------|---------------|-------------------------------|
| Rules | `.clinerules/` dir (or legacy `.clinerules` file) | supported (no glob scoping) |
| Commands | `.clinerules/workflows/*.md` invoked as `/<name>` | partial — manual port of a curated subset only |
| Skills | (none — manual port to a workflow only) | gap |
| Agents | (none — single agent, no persona registry) | gap |
| Hooks | (none — no lifecycle hook system) | gap |
| MCP | `cline_mcp_settings.json` + in-editor MCP Marketplace | strong (Cline's standout strength) |

---

## Commands / Workflows

Cline's only user-extensible command-like primitive is **Workflows**: place a Markdown
file at `.clinerules/workflows/<name>.md` and invoke it by typing `/<name>` in the Cline
chat input. Cline also has a few built-in slash controls (`/newtask`, `/smol`, `/reportbug`)
that operate on Cline itself and are NOT user-extensible.

gald3r's `@g-*` / `/g-*` command library is **not** natively executable on Cline. Individual
commands can be hand-ported to `workflows/*.md`; the full namespace cannot be auto-mounted.

---

## MCP Support

MCP is Cline's strongest capability — it ships an in-editor **MCP Marketplace** for
one-click server installs. Servers are configured in `cline_mcp_settings.json` under the
VS Code extension's `globalStorage` (exact path is OS/VS-Code-version-dependent — manage it
via the extension's "Edit MCP Settings" / marketplace UI rather than hand-editing). The
live server set is per-machine and not committed. See PLATFORM_SPEC.md section 8.

---

## Config Files Shipped

- **`.clinerules`** (or a `.clinerules/` directory) — gald3r always-apply rule subset
  (task gate, commit format, bug protocol).
- **`memory-bank/projectbrief.md`** — gald3r mission surface for persistent context.

---

## gitignore Decision (T1277 AC6)

`.clinerules` (file or directory) and `memory-bank/*.md` are **source** — keep them tracked.
Cline writes no generated output directory of its own, so no gitignore entry is needed in
installed projects.

---

## Verification

```powershell
Test-Path .clinerules        # legacy single-file form
Test-Path .clinerules/       # modern directory form
```

Expected: one of the two `.clinerules` forms present.

---

## Common Pitfalls

- Rules live at the project root — either a `.clinerules/` directory or a `.clinerules` file.
- `.clinerules/` has no per-rule glob scoping — every rule file is always-apply.
- Memory bank files are read-only to Cline — you must update them manually.
- Keep rule content concise (large files compete for context window space).
- gald3r hooks, skills, and agent personas do NOT auto-load on Cline (see PLATFORM_SPEC.md
  sections 3, 4, 6) — express required behavior as rules text instead.
