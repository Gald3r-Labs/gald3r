# Aider Platform — gald3r Configuration Guide

**Platform**: Aider (terminal AI coding tool, auto-commits)
**Config Folder**: `.aider/` (scaffold) + root `.aider.conf.yml`
**gald3r Version**: 1.0.0
**Official Docs**: https://aider.chat/docs
**Config File**: `.aider.conf.yml` (project root)
**Authoritative skill**: `g-skl-platform-aider`
**Platform capability spec**: `PLATFORM_SPEC.md` (this directory) — honest per-capability status

---

## Capability Summary (from PLATFORM_SPEC.md)

| Hooks | Rules | Skills | Commands | MCP |
|---|---|---|---|---|
| ❌ | ⚠️ | ❌ | ❌ | ❌ |

Legend: ✅ verified working · ⚠️ partial / Cursor-generic · ❌ not supported · ❓ untested.

Aider is the most minimal gald3r target: a single-assistant terminal REPL with no
agents, no skill discovery, no rules folder, no lifecycle-hook system, and no native
MCP client (RFC open). The one capability that maps cleanly is **read-only context
pinning** (`read:` / `/read-only` + repo map) — gald3r delivers `CONVENTIONS.md` plus
pinned `.gald3r/` files through it. The many `❌` marks are honest assessments of a
minimal CLI, not deploy failures. See `PLATFORM_SPEC.md` §9 (Known Gaps) for detail.

---

## Folder Layout

```
<project-root>/
├── .aider.conf.yml         # Aider configuration (model, auto-commits, read-only context)
├── CONVENTIONS.md          # Project conventions — pinned read-only via `read:` (NOT auto-discovered by name)
└── .aiderignore            # Files excluded from Aider context (like .gitignore)
```

**What Aider does NOT have:**
- No `agents/` folder — Aider is a single-agent CLI tool
- No `commands/` folder — invocation is via the `aider` CLI and chat
- No `rules/` folder — behavioral guidance lives in `CONVENTIONS.md`
- No `hooks/` folder — Aider has no lifecycle hook system

---

## What Makes Aider Unique

### Auto-Commits
Aider creates a git commit after every accepted edit. This can conflict with gald3r's
task-scoped commit discipline (one logical commit per task, `feat(T{id}): ...`). Either:
- Set `auto-commits: false` in `.aider.conf.yml` and commit manually with gald3r conventions, OR
- Keep auto-commits on and squash/audit before pushing.

### Read-Only Context Files
Aider reads "read-only" files for persistent context without editing them. Point Aider at
gald3r control-plane files so it always has task and constraint context:

```yaml
# .aider.conf.yml
model: <your-model>     # set to a current model; aider validates against its model registry
auto-commits: false
read:
  - CONVENTIONS.md
  - .gald3r/PROJECT.md
  - .gald3r/CONSTRAINTS.md
```

### CONVENTIONS.md
`CONVENTIONS.md` is the gald3r behavioral surface for Aider — task references, commit
format, and code standards live here. Aider does **not** auto-discover it by filename;
it must be pinned via `read:` in `.aider.conf.yml` (or `/read-only CONVENTIONS.md`, or
`aider --read CONVENTIONS.md` at launch). The shipped `.aider.conf.yml` already lists it.

---

## gald3r Naming Conventions

| Component | Surface |
|-----------|---------|
| Skills | none — no `SKILL.md` discovery/loading mechanism (spec §4); skill *instructions* reach Aider only if copied into a `read:` file |
| Agents | none — single conversational assistant; closest analogue is aider chat modes (`/chat-mode code\|ask\|help`, `architect`), not gald3r agents (spec §3) |
| Commands | none — fixed built-in `/commands` only (`/add`, `/run`, `/web`, …); no extensible `g-*` registration (spec §5) |
| Rules | no rules folder; always-apply guidance lives in `CONVENTIONS.md` + other `read:` files (spec §7) |
| Hooks | none — no lifecycle-event system; `lint-cmd`/`test-cmd`/auto-commit are edit-cycle automations, not a hook bus (spec §6) |
| MCP | not native (RFC #4506 open); `/web` and `/run` are manual substitutes (spec §8) |

---

## Config Files Shipped

- **`.aider.conf.yml`** — Aider config with gald3r read-only context and auto-commits disabled.
- **`CONVENTIONS.md`** — gald3r task/commit/code conventions, pinned read-only via `read:`.

These are installed to the project root (not into `.aider/`), because Aider reads them
from root by convention.

---

## gitignore Decision (T1277 AC6)

Aider's config files (`.aider.conf.yml`, `CONVENTIONS.md`) are **source** — keep them tracked.
`.aiderignore` is also source. Aider does not generate a root output directory of its own,
so there is nothing to gitignore for this platform in an installed project.

---

## Verification

```powershell
Test-Path .aider.conf.yml
Test-Path CONVENTIONS.md
aider --config .aider.conf.yml --version
```

---

## Common Pitfalls

- Auto-commits conflict with task-scoped commits — disable or audit (see above).
- Read-only files count against the context token budget — do not add large `TASKS.md`.
- `.aiderignore` should exclude `.gald3r/` task files so Aider never edits coordination state.
