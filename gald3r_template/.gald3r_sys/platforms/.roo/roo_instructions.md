# Roo Code Platform — gald3r Configuration Guide

**Platform**: Roo Code (formerly Roo Cline — VS Code extension, multi-mode agentic)
**Config Folder**: root `.roorules` (+ mode-specific `.roorules-*`)
**gald3r Version**: 1.0.0
**Official Docs**: https://github.com/RooVetGit/Roo-Code
**Config File**: `.roorules` (project root; `.clinerules` is the fallback)
**Authoritative skill**: `g-skl-platform-roo`

---

## Folder Layout

```
<project-root>/
├── .roorules               # Global project rules (all modes)
├── .roorules-architect     # Architect-mode rules (planning/design)
├── .clinerules             # Fallback — Roo reads this if .roorules is absent
└── memory-bank/            # Persistent memory (Cline-compatible)
```

**What Roo does NOT have:**
- No project `agents/` folder — Roo uses built-in modes (Code, Architect, Debug, Test, Ask)
- No `commands/` folder — invocation is via the VS Code panel
- No `hooks/` folder — MCP is supported via settings

---

## What Makes Roo Unique

### Mode System
Roo has built-in modes (Code, Architect, Debug, Test, Ask), each able to carry separate
rules. `.roorules` applies to all modes; `.roorules-architect` adds gald3r architecture
context (read PLAN.md and CONSTRAINTS.md) for design work. In some versions mode-specific
files override the global file rather than adding to it — test cross-mode behavior.

### Rules Precedence
Roo reads `.roorules` first, then `.clinerules` as a fallback. gald3r writes `.roorules` as
primary and also writes `.clinerules` for Cline compatibility.

### Boomerang Orchestration
Roo can spawn sub-tasks in different modes. Sub-tasks may not inherit rules — verify
cross-mode rule loading.

---

## gald3r Naming Conventions

| Component | Surface |
|-----------|---------|
| Skills | served from root `skills/` (reference by name) |
| Agents | Roo modes (built-in) |
| Commands | (none) |
| Rules | `.roorules` (+ `.roorules-architect`), `.clinerules` fallback |

---

## Config Files Shipped

- **`.roorules`** — gald3r always-apply rule subset (task gate, commit format, bug protocol).
- **`.roorules-architect`** — gald3r architecture context for Architect mode.

---

## gitignore Decision (T1277 AC6)

`.roorules`, `.roorules-architect`, and `memory-bank/*.md` are **source** — keep them
tracked. Roo writes no generated project output directory of its own, so no gitignore entry
is needed in installed projects.

---

## Verification

```powershell
Test-Path .roorules
```

---

## Common Pitfalls

- Roo reads `.roorules` first, then `.clinerules` — set `.roorules` as primary.
- Mode-specific files may override the global `.roorules` (not additive in some versions).
- Boomerang sub-tasks may use different modes — test cross-mode rule loading.
