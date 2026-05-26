# Goose Platform — gald3r Configuration Guide

**Platform**: Goose (by Block — open-source terminal AI agent)
**Config Folder**: `.goose/` + root `GOOSE.md`
**gald3r Version**: 1.0.0
**Official Docs**: https://block.github.io/goose/docs
**Config File**: `.goose/config.yaml` (project) / `~/.config/goose/config.yaml` (global)
**Authoritative skill**: `g-skl-platform-goose`

---

## Folder Layout

```
<project-root>/
├── GOOSE.md                # Project-level instructions, read at session start
└── .goose/
    └── config.yaml         # Project Goose config (overrides global), MCP extensions, profiles
```

Global config lives at `~/.config/goose/config.yaml`.

**What Goose does NOT have:**
- No project `agents/` folder — Goose uses profiles + extensions, not file-based agents
- No `commands/` folder — invocation is via the `goose` CLI
- No `rules/` folder — behavioral guidance lives in `GOOSE.md`
- No `hooks/` folder — extension-driven, not lifecycle-hook driven

---

## What Makes Goose Unique

### Extensions (MCP + Built-in)
Goose's capabilities come from extensions — MCP servers and built-in tools (browser, code
execution). The gald3r Docker MCP server can be wired in as an extension so Goose can drive
task/bug/vault operations directly.

### Profiles
Named profiles select model + instructions per task type. The default profile points at
`GOOSE.md` for gald3r context.

### GOOSE.md
Project context is read from `GOOSE.md` at session start (community convention). It carries
the gald3r task workflow, commit format, and optional MCP pointer.

---

## gald3r Naming Conventions

| Component | Surface |
|-----------|---------|
| Skills | served from root `skills/` (reference by name; MCP exposes gald3r ops) |
| Agents | Goose profiles (`.goose/config.yaml`) |
| Commands | (none — `goose` CLI) |
| Rules | embedded in `GOOSE.md` |

---

## Config Files Shipped

- **`GOOSE.md`** — gald3r task context, commit convention, MCP pointer.
- **`.goose/config.yaml`** — default profile + optional gald3r MCP extension.

---

## gitignore Decision (T1277 AC6)

`GOOSE.md` and `.goose/config.yaml` are **source** — keep them tracked. If `config.yaml`
ever holds an API key, move the key to an environment variable rather than gitignoring the
config. Goose writes session state outside the project (`~/.config/goose/`), so no
generated project output dir needs gitignoring.

---

## Verification

```powershell
Test-Path GOOSE.md
goose version
```

---

## Common Pitfalls

- Extensions (MCP) must be running before the Goose session starts.
- `GOOSE.md` is a community convention — Goose reads it only if the active profile loads it.
- Session state persists in `~/.config/goose/` between sessions; instructions reload per session.
