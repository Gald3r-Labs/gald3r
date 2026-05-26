# OpenClaw Platform — gald3r Configuration Guide

**Platform**: OpenClaw (caveman-ecosystem-compatible AI coding agent)
**Config Folder**: root `SOUL.md` + root `skills/`
**gald3r Version**: 1.0.0
**Official Docs**: https://github.com/openclaw/openclaw
**Config File**: `SOUL.md` (project root)
**Authoritative skill**: `g-skl-platform-openclaw`

---

## Folder Layout

```
<project-root>/
├── SOUL.md                 # Project identity + context (primary config)
└── skills/                 # Canonical skill source — OpenClaw reads this directly
    └── {skill-name}/
        └── SKILL.md
```

**What OpenClaw does NOT have:**
- No `agents/` folder — context comes from `SOUL.md`
- No `commands/` folder — invocation is via the OpenClaw CLI
- No `rules/` folder — behavioral guidance lives in `SOUL.md`
- No `hooks/` folder — minimal config by design

---

## What Makes OpenClaw Unique

### SOUL.md Is the Identity File
OpenClaw uses `SOUL.md` as the project's AI identity document — analogous to AGENTS.md /
CLAUDE.md but specific to OpenClaw. Do not confuse it with AGENTS.md (gald3r ships both).

### Reads Root `skills/` Directly
Post-T1042, gald3r's canonical source IS the root `skills/` directory, which is exactly
what OpenClaw reads. **No extra wiring is needed** — the root `skills/` dir is the OpenClaw
integration. Platform-specific dirs (`.cursor/skills/`) are not read by OpenClaw.

---

## gald3r Naming Conventions

| Component | Surface |
|-----------|---------|
| Skills | root `skills/{name}/SKILL.md` (read natively) |
| Agents | (none) |
| Commands | (none) |
| Rules | embedded in `SOUL.md` |

---

## Config Files Shipped

- **`SOUL.md`** — gald3r project identity, context pointers, and commit convention.

(No skills are shipped under `.openclaw/` — OpenClaw reads the canonical root `skills/`.)

---

## gitignore Decision (T1277 AC6)

`SOUL.md` is **source** — keep it tracked. OpenClaw reads the root `skills/` directory and
writes no generated output directory of its own, so no gitignore entry is needed in
installed projects.

---

## Verification

```powershell
Test-Path SOUL.md
Test-Path skills/g-skl-tasks/SKILL.md
```

---

## Common Pitfalls

- `SOUL.md` is the primary identity file — do not confuse it with AGENTS.md.
- OpenClaw reads root `skills/` directly; platform-specific skill dirs are ignored.
- The T1042 root `skills/` dir IS the OpenClaw integration — no extra install step.
