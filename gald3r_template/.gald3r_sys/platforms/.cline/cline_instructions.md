# Cline Platform — gald3r Configuration Guide

**Platform**: Cline (formerly Claude Dev — VS Code extension, agentic)
**Config Folder**: root `.clinerules` + optional `memory-bank/`
**gald3r Version**: 1.0.0
**Official Docs**: https://github.com/clinebot/cline
**Config File**: `.clinerules` (project root)
**Authoritative skill**: `g-skl-platform-cline`

---

## Folder Layout

```
<project-root>/
├── .clinerules             # Project-level instructions, auto-injected at session start
└── memory-bank/            # Optional persistent context files
    ├── projectbrief.md
    ├── activeContext.md
    └── progress.md
```

**What Cline does NOT have:**
- No project `agents/` folder — Cline is a single agentic assistant
- No `commands/` folder — invocation is via chat in the VS Code panel
- No `hooks/` folder — no lifecycle hook system (MCP is supported via settings)

---

## What Makes Cline Unique

### Single Rules File
`.clinerules` must live in the project root (subdirectory rules are not supported). It is
auto-injected at session start. gald3r writes its always-apply rule subset here. Keep it
under ~4K tokens — large rule files may be truncated.

### Memory Bank
Cline reads `memory-bank/*.md` for persistent cross-session context, but does **not**
auto-write them — you maintain them. Surface the gald3r mission in
`memory-bank/projectbrief.md`.

### Full Agentic Tool Use
Cline can read/write files, run commands, and browse. Because it acts autonomously,
the gald3r enforcement rules in `.clinerules` (task gate, bug protocol, commit format)
are the primary guardrail.

---

## gald3r Naming Conventions

| Component | Surface |
|-----------|---------|
| Skills | served from root `skills/` (reference by name in chat) |
| Agents | (none) |
| Commands | (none) |
| Rules | `.clinerules` (project root) |

---

## Config Files Shipped

- **`.clinerules`** — gald3r always-apply rule subset (task gate, commit format, bug protocol).
- **`memory-bank/projectbrief.md`** — gald3r mission surface for persistent context.

---

## gitignore Decision (T1277 AC6)

`.clinerules` and `memory-bank/*.md` are **source** — keep them tracked. Cline writes no
generated output directory of its own, so no gitignore entry is needed in installed projects.

---

## Verification

```powershell
Test-Path .clinerules
```

Expected: `.clinerules` present.

---

## Common Pitfalls

- `.clinerules` must be in the project root — subdirectory rules are ignored.
- Memory bank files are read-only to Cline — you must update them manually.
- Keep `.clinerules` concise (>8K tokens may be truncated in Cline's context).
