# JetBrains Junie Platform — gald3r Configuration Guide

**Platform**: JetBrains Junie (AI assistant in IntelliJ / PyCharm / WebStorm / GoLand)
**Config Folder**: `.junie/`
**gald3r Version**: 1.0.0
**Official Docs**: https://www.jetbrains.com/junie/docs
**Config File**: `.junie/guidelines.md`
**Authoritative skill**: `g-skl-platform-junie`

---

## Folder Layout

```
.junie/
└── guidelines.md       # Project-level instructions, auto-injected into every Junie session
```

**What Junie does NOT have:**
- No project `agents/` folder — Junie is a single agent inside the JetBrains IDE
- No `commands/` folder — invocation is via the Junie panel
- No `rules/` folder — behavioral guidance lives in `guidelines.md`
- No `hooks/` folder — no lifecycle hook system

---

## What Makes Junie Unique

### PSI-Backed Code Intelligence
Junie uses the JetBrains Program Structure Interface (PSI) for deep code navigation.
Path-based gald3r references generally work, but if a rule assumes a shell-relative path,
prefer IDE-relative paths in `guidelines.md`.

### Single Guidelines File
`.junie/guidelines.md` is read in full at session start. It is the only behavioral surface
for Junie — task workflow, commit format, and bug protocol all live there.

### Agent Mode + Run Configurations
Junie can execute multi-step tasks and run IDE run-configurations. Keep guidelines focused
so the injected context budget stays small.

---

## gald3r Naming Conventions

| Component | Surface |
|-----------|---------|
| Skills | served from root `skills/` (reference by name in the Junie panel) |
| Agents | (none) |
| Commands | (none) |
| Rules | `.junie/guidelines.md` |

---

## Config Files Shipped

- **`.junie/guidelines.md`** — gald3r task workflow, commit format, bug protocol.

---

## gitignore Decision (T1277 AC6)

`.junie/guidelines.md` is **source** — keep it tracked. Junie writes no generated output
directory in the project root, so no gitignore entry is needed in installed projects.

---

## Verification

```powershell
Test-Path .junie/guidelines.md
```

---

## Common Pitfalls

- Junie requires an active JetBrains AI subscription.
- Guidelines are read at session start — changes take effect on next Junie activation.
- PSI-based navigation may need IDE-relative paths where shell-relative paths are assumed.
