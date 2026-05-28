# Goose Platform — gald3r Configuration Guide

**Platform**: Goose (by Block — open-source, local-first terminal/desktop AI agent)
**Instruction File**: `.goosehints` (project root)
**gald3r Version**: 1.0.0
**Official Docs**: https://block.github.io/goose/docs
**Config File**: `~/.config/goose/config.yaml` (GLOBAL — no project-level convention)
**Authoritative skill**: `g-skl-platform-goose`
**Verified findings**: see `PLATFORM_SPEC.md` in this folder (§9 Known Gaps first)

---

## Folder Layout

```
~/.config/goose/
└── config.yaml             # GLOBAL config: provider, model, enabled extensions (MCP servers)

~/.config/agents/skills/    # GLOBAL skills discovered by the Skills extension

<project-root>/
├── .goosehints             # project-scoped instructions/rules (Goose auto-reads as context)
└── .agents/skills/         # PROJECT skills discovered by the Skills extension (if enabled)
    └── <name>/SKILL.md
```

Goose is **global-config-first**: the primary config lives in the user's home directory,
not the repo. There is **no** project `.goose/config.yaml` and **no** `GOOSE.md` convention.

**What Goose does NOT have:**
- No user-authored `agents/` file format — Goose **subagents** are experimental and
  platform-spawned, not gald3r-authored. Map agent behavior to recipes or `.goosehints`.
- No slash-command registry — the native equivalent is **recipes** (reusable YAML
  workflows). gald3r `g-*` markdown commands do not auto-port; manual recipe authoring required.
- No `.mdc` rules / no `alwaysApply:` / `globs:` scoping — rules collapse into one
  `.goosehints` instruction blob (all-or-nothing context).
- No native lifecycle-hook config (no `hooks.json` analogue) — gald3r `g-hk-*.ps1` hooks do
  NOT auto-fire on Goose. Run them manually or wrap into a recipe/extension.

---

## What Makes Goose Unique

### Extensions = MCP servers (first-class)
Goose's strongest gald3r surface. In Goose, **extensions ARE MCP servers** (stdio or
remote SSE/HTTP). A built-in **Developer** MCP extension is enabled by default. Extensions
are declared under `extensions:` in the GLOBAL `~/.config/goose/config.yaml`, or managed via
`goose configure`. An Extension Allowlist can restrict which MCP servers may install. The
gald3r MCP server is added here — see `config.yaml` (this folder) for a copy-paste snippet.

### .goosehints (instructions)
Project instructions Goose loads as context (markdown content). This is the gald3r
instruction target — analogous to `AGENTS.md`/`CLAUDE.md` elsewhere, but Goose-specific.
gald3r writes the task workflow, commit format, and MCP pointer here.

### Recipes (workflows)
Reusable, shareable YAML workflow templates with parameters; sub-recipes compose them. This
is the correct mapping target for gald3r commands/workflows on Goose (manual authoring).

### Skills extension
When enabled, Goose auto-discovers skills at startup from `.agents/skills/` (project) and
`~/.config/agents/skills/` (global). Format is folder-per-`SKILL.md` — the **same convention
gald3r uses** — so `g-skl-*/SKILL.md` is structurally compatible if copied into
`.agents/skills/<name>/`. Gated on the Skills extension being enabled (not on by default).

---

## gald3r Naming Conventions

| Component | Surface on Goose |
|-----------|------------------|
| Instructions/Rules | `.goosehints` (single blob — no glob scoping) |
| Skills | `.agents/skills/<name>/SKILL.md` (requires Skills extension enabled) |
| Agents | recipes or `.goosehints` (no native agent file format) |
| Commands | recipes (YAML) — no auto-port from `g-*` markdown |
| Hooks | none native — run manually or wrap in a recipe/extension |
| MCP | extension entry in `~/.config/goose/config.yaml` (strongest surface) |

---

## Files Shipped in This Scaffold

- **`.goosehints`** — gald3r task context, commit convention, MCP pointer (the real
  Goose instruction file).
- **`config.yaml`** — REFERENCE ONLY copy-paste snippet for the gald3r MCP extension block
  destined for the GLOBAL `~/.config/goose/config.yaml`. Goose does not read it from the project.
- **`PLATFORM_SPEC.md`** — verified per-platform capability findings.
- **`README.md`** — scaffold overview.

---

## gitignore Decision

`.goosehints` is **source** — keep it tracked. The `config.yaml` reference snippet is also
source (no secrets — it is a template). Real provider keys live in the GLOBAL
`~/.config/goose/config.yaml` outside the repo, so no project output dir needs gitignoring.

---

## Verification

```powershell
Test-Path .goosehints
goose --version
```

---

## Common Pitfalls

- The instruction file is `.goosehints`, NOT `GOOSE.md`. `GOOSE.md` is not a Goose convention.
- Goose config is GLOBAL (`~/.config/goose/config.yaml`); there is no project `.goose/config.yaml`.
- Extensions (MCP servers) must be configured/running before the Goose session needs them.
- Skill discovery requires the Skills extension enabled in config — it is not on by default.
- gald3r hooks do not auto-fire on Goose — run them manually or wrap them in a recipe.

> **SCAN_DOCS not yet run** (`last_doc_scan: never`). Confirm exact `.goosehints` load
> precedence, any 2026 hook/event additions, and the Skills-extension discovery contract via
> `@g-platform-scan-docs goose` against https://block.github.io/goose/docs.
