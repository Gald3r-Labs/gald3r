# Kiro IDE Platform — gald3r Configuration Guide

**Platform**: Kiro (Amazon's spec-driven AI IDE, built on VS Code)
**Config Folder**: `.kiro/`
**gald3r Version**: 1.0.0
**Official Docs**: https://kiro.dev/docs
**Config Surface**: `.kiro/steering/` (always-injected), `.kiro/specs/`, `.kiro/hooks/`
**Authoritative skill**: `g-skl-platform-kiro`

---

## Folder Layout

```
.kiro/
├── steering/                   # Always-injected context files
│   ├── gald3r.md               # gald3r task management context
│   └── product.md              # Product context (maps to .gald3r/PROJECT.md)
├── specs/                      # Feature specifications (requirements.md, design.md)
└── hooks/                      # Automation hooks (triggered on file changes)
```

**What Kiro maps differently:**
- Steering files replace a `rules/` folder — they are injected automatically
- Specs map naturally to gald3r PRDs (requirements → AC, design → technical design)
- Hooks exist but trigger on file changes, not the gald3r session lifecycle

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

| Component | Surface |
|-----------|---------|
| Skills | served from root `skills/` |
| Agents | (none — Kiro's agent reads steering + specs) |
| Commands | (none) |
| Rules | `.kiro/steering/*.md` |

---

## Config Files Shipped

- **`.kiro/steering/gald3r.md`** — gald3r task management context.
- **`.kiro/steering/product.md`** — product context placeholder (maps to PROJECT.md).

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
