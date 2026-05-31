---
name: g-skl-platform-aider
description: Authoritative reference for Aider (terminal AI coding tool) customization in gald3r projects. Covers .aider.conf.yml, CONVENTIONS.md, model config, and gald3r install verification.
crawl_max_age_days: 14
vault_doc_path: research/platforms/aider/
vault_docs_url: https://aider.chat/docs
docs_url: https://aider.chat/docs
token_budget: low
capability_status:
  hooks: ❌      # no lifecycle-event system; lint-cmd/test-cmd/auto-commit are not a hook bus
  rules: ⚠️      # no rules folder; always-apply guidance via CONVENTIONS.md pinned read-only
  skills: ❌     # no SKILL.md discovery/loading/invocation mechanism
  commands: ❌   # fixed built-in /commands only; no extensible g-* registration
  mcp: ❌        # not native (RFC #4506 open, no shipped client as of ~v0.86.x)
subsystem_memberships: [PLATFORM_INTEGRATION]
---

# g-skl-platform-aider

Activate for: setting up gald3r with Aider, authoring `.aider.conf.yml`, configuring read-only files, or verifying Aider gald3r integration.

---

## 1. Platform Overview

**Aider** is a popular terminal-based AI coding tool that makes git commits automatically. It reads a configuration file and can be pointed at "read-only" context files for persistent project context.

- **Config**: `.aider.conf.yml` or `~/.aider.conf.yml` (global)
- **Read-only files**: Files Aider reads for context but won't edit
- **CONVENTIONS.md**: Project conventions file that Aider reads at session start
- **Git integration**: Auto-commits after each accepted edit

**gald3r target tier**: CLI tool. Config via `.aider.conf.yml` + read-only context files.

---

## 2. Config File Layout

```
<project-root>/
├── .aider.conf.yml         ← Aider configuration
├── CONVENTIONS.md          ← Project conventions (Aider reads this automatically if present)
└── .aiderignore            ← Files to exclude from Aider's context (like .gitignore)
```

**`.aider.conf.yml` format:**
```yaml
model: <your-model>          # set to a current model; aider validates against its model registry
auto-commits: false          # disable to defer to gald3r task-scoped commit discipline (see §5)
read:                        # files pinned as read-only context (CONVENTIONS.md is NOT auto-discovered)
  - CONVENTIONS.md
  - .gald3r/PROJECT.md
  - .gald3r/CONSTRAINTS.md
```

> Note: aider does NOT auto-load `CONVENTIONS.md` by filename — it must be in `read:` (or loaded
> with `/read-only CONVENTIONS.md` / `aider --read CONVENTIONS.md`). `read:` files consume the
> context budget every turn, so pin selectively.

---

## 3. gald3r Integration

### Install

```bash
node bin/install.js --only aider
```

Creates `.aider.conf.yml` pointing at gald3r context files as read-only inputs.

### CONVENTIONS.md

Create `CONVENTIONS.md` at project root — Aider reads this automatically:

```markdown
# Development Conventions

## Task References
Always reference active task: feat(T{id}): ...
Tasks tracked in .gald3r/TASKS.md

## Commit Style
feat(T{id}): description
fix(BUG-{id}): description

## Code Standards
- No bare TODO comments
- Read .gald3r/CONSTRAINTS.md before architecture changes
```

### Read-Only Context

Add gald3r files as read-only so Aider uses them for context without editing:
```bash
aider --read .gald3r/PROJECT.md --read .gald3r/CONSTRAINTS.md
```

---

## 4. Verification

```bash
Test-Path .aider.conf.yml
aider --config .aider.conf.yml --version
```

---

## 5. Common Pitfalls

- Aider auto-commits can conflict with gald3r's task-scoped commit discipline — disable `auto-commits: true` or audit commits
- Read-only files are included in context token budget — be selective (don't include TASKS.md if large)
- `.aiderignore` should exclude `.gald3r/` task files to avoid Aider modifying them

---

## 6. Known Gaps (features that do NOT work on Aider)

Aider is a minimal terminal pair-programmer. Most gald3r primitives have **no runtime home** here.
This is the honest assessment (see `PLATFORM_SPEC.md` §9 for the full decision-tree mapping):

| Capability | Status | Reality on Aider |
|---|---|---|
| Hooks (sessionStart/stop/preToolUse/beforeShellExecution) | ❌ | No lifecycle-event system, no `hooks.json`. `lint-cmd`/`test-cmd`/auto-commit are edit-cycle automations, not a hook bus. Run gald3r `.ps1` hooks manually via `/run`. |
| Rules folder (`.mdc`/`.md` always-apply) | ⚠️ | No rules dir. Always-apply guidance lives in `CONVENTIONS.md` pinned read-only — the only persistent surface. |
| Skills (`g-skl-*/SKILL.md`) | ❌ | No `SKILL.md` discovery/loading/invocation. Skill instructions only reach aider if copied into a `read:` file. |
| Agents (`g-agnt-*.md`) | ❌ | No agent concept/roster. Only chat modes (`/chat-mode code\|ask\|help`, `architect`). |
| Commands (`@g-*` / `/g-*` palette) | ❌ | Only fixed built-in `/commands` (`/add`, `/read-only`, `/run`, `/web`, `/map`, …). No custom command registration. |
| MCP servers | ❌ | Not natively supported (RFC #4506 open; no shipped client as of ~v0.86.x). Substitutes: `/web`, `/run`, `/read-only`. |
| AGENTS.md / CLAUDE.md auto-read | ❌ | Aider does not read these. Fold enforcement into `CONVENTIONS.md` + `read:` files. |

**What DOES work well**: read-only context pinning (`read:` / `/read-only`) and the repo map.
gald3r delivers `CONVENTIONS.md` + pinned `.gald3r/` context files — aider's intended mechanism.

`capability_status:` in the frontmatter above is the machine-readable summary of this table.
`docs_url: https://aider.chat/docs` is the SCAN_DOCS crawl target.
