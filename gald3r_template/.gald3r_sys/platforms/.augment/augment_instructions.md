# Augment Code Platform — gald3r Configuration Guide

**Platform**: Augment Code (VS Code extension + JetBrains plugin)
**Config Folder**: `.augment/`
**gald3r Version**: 1.0.0
**Official Docs**: https://docs.augmentcode.com
**Config File**: `.augment/guidelines.md`
**Authoritative skill**: `g-skl-platform-augment`

---

## Folder Layout

```
.augment/
└── guidelines.md       # Workspace-level instructions, auto-injected into every session
```

**What Augment does NOT have:**
- No `agents/` folder — Augment is a single assistant with a context engine
- No `commands/` folder — invocation is via chat / completions in the IDE
- No `rules/` folder — behavioral guidance lives entirely in `guidelines.md`
- No `hooks/` folder — no lifecycle hook system

---

## What Makes Augment Unique

### Codebase Context Engine
Augment indexes the entire codebase for semantic search. The `guidelines.md` file is
**separate** from that index — guidelines carry behavioral instructions, the index
carries code knowledge. gald3r task context belongs in `guidelines.md`.

### Single Guidelines File
Everything gald3r needs Augment to know goes in `.augment/guidelines.md`: task workflow,
commit format, bug protocol, and architecture references. Keep it focused — it is injected
on every session.

### IDE Parity
The VS Code extension and JetBrains plugin share the same `.augment/guidelines.md` path.
A JetBrains variant may also read `~/.augment/` (global) — project guidelines take
precedence for workspace-scoped behavior.

---

## gald3r Naming Conventions

| Component | Surface |
|-----------|---------|
| Skills | served from root `skills/` (reference by name in chat) |
| Agents | (none) |
| Commands | (none) |
| Rules | embedded in `.augment/guidelines.md` |

---

## Config Files Shipped

- **`.augment/guidelines.md`** — gald3r task management, commit, and bug-protocol guidance.

---

## gitignore Decision (T1277 AC6)

`.augment/guidelines.md` is **source** — keep it tracked. Augment writes no generated
output directory in the project root, so no gitignore entry is needed in installed projects.

---

## Verification

```powershell
Test-Path .augment/guidelines.md
```

---

## Common Pitfalls

- The codebase index is not the guidelines file — behavioral rules must be in `guidelines.md`.
- JetBrains may read a different path (`~/.augment/`) — verify with your IDE version.
- Enterprise team guidelines can override workspace guidelines depending on tier.
