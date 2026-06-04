---
name: g-skl-platform-aider
description: Authoritative reference for Aider (terminal AI pair-programmer) customization in gald3r projects. Covers .aider.conf.yml, CONVENTIONS.md (native rules), built-in slash commands, architect/editor chat modes, auto-lint/test triggers, model roles, and gald3r install verification.
crawl_max_age_days: 14
vault_doc_path: research/platforms/aider/
vault_docs_url: https://aider.chat/docs
docs_url: https://aider.chat/docs
docs_url_secondary:
  - https://aider.chat/docs/usage/conventions.html
  - https://aider.chat/docs/usage/commands.html
  - https://aider.chat/docs/usage/modes.html
  - https://aider.chat/docs/usage/lint-test.html
  - https://aider.chat/docs/config/options.html
  - https://github.com/Aider-AI/aider/issues/4506
last_doc_scan: 2026-06-02
capability_status:
  hooks: "⚠️ partial — auto-lint/auto-test post-edit trigger (--auto-lint/--lint-cmd, --auto-test/--test-cmd) + git auto-commit; NO general event hooks (FR #2045)"
  rules: "✅ native — CONVENTIONS.md pinned read-only via --read / .aider.conf.yml read: (arbitrary filename; no rules folder)"
  skills: "❌ not native — no SKILL.md discovery/activation; community aider-skills PyPI injects externally"
  commands: "⚠️ partial — 40+ built-in slash commands (/add /architect /run /load …); NO user-defined custom commands"
  agents: "⚠️ partial — fixed chat modes (code/architect/ask/help); architect = architect-model + --editor-model; NO sub-agent files"
  mcp: "❌ not native — core CLI has none (FR #4506 open); only AiderDesk / mcpm-aider bridges"
token_budget: low
subsystem_memberships: [PLATFORM_INTEGRATION]
---

# g-skl-platform-aider

Activate for: setting up gald3r with Aider (terminal CLI), authoring `.aider.conf.yml` + `CONVENTIONS.md`, configuring read-only context / model roles, or verifying the Aider gald3r install.

---

> Full 9-section breakdown + evidence URLs in `PLATFORM_SPEC.md` (this folder). **Status: ⚠️ partial
> parity** — only **rules** are native (read-only `CONVENTIONS.md`); **commands/agents/hooks** are
> partial (built-in slash commands, fixed chat modes, auto-lint/test trigger only); **skills/MCP**
> are not native. Aider does **NOT** read `CLAUDE.md`/`AGENTS.md` or `.claude/`/`.agents/` trees, so
> gald3r's Claude-Code artifacts are **not reusable** — fold guidance into a pinned `CONVENTIONS.md`.
> (Verified 2026-06-02 against https://aider.chat/docs.)

## 1. Platform Overview

**Aider** (`aider` command) — an open-source terminal-based AI pair-programmer that edits files in
your local git repo and **auto-commits** each accepted change. It builds a **repo map**
(tree-sitter–derived codebase summary) for context and lets you pin extra files as **read-only**.
The **core CLI** is the gald3r target; **AiderDesk** (GUI wrapper) and third-party bridges add MCP /
skill loading externally and are out of scope for a portable install.

## 2. Config Layout

```
<project-root>/
├── CONVENTIONS.md            ← documented default instruction file (read-only, pinned via config)
├── .aider.conf.yml           ← model roles, read:, auto-lint/test, auto-commits
├── .aider.model.settings.yml / .aider.model.metadata.json  ← custom model definitions
├── .env                      ← API keys
└── .aiderignore              ← excludes paths from aider's context (gitignore syntax)
```

There is **no `.aider/` extension tree** (no `commands/`, `agents/`, `skills/`, `hooks/`). The only
persistent gald3r-writable surface is a markdown convention file referenced from `read:`, plus the
YAML config. **Aider does not read `.claude/`/`.agents/` or `CLAUDE.md`/`AGENTS.md`** → gald3r's
Claude-Code tree does **not** work as-is.

**`.aider.conf.yml` essentials:**
```yaml
model: <your-model>           # validated against aider's model registry
auto-commits: false           # defer to gald3r task-scoped commit discipline
read:                         # read-only context (CONVENTIONS.md is NOT auto-discovered by name)
  - CONVENTIONS.md
  - .gald3r/PROJECT.md
  - .gald3r/CONSTRAINTS.md
```

## 3. gald3r Integration

**Only portable install path: fold gald3r `g-rl-*` guidance into `CONVENTIONS.md` and pin
`.gald3r/` context via `read:`** — that is aider's intended project-context mechanism, and the only
persistent always-apply surface. Set `auto-commits: false` so aider does not race gald3r's
task-scoped commit flow. Optionally wire `lint-cmd`/`test-cmd` to a gald3r verification script for a
post-edit gate, and route pre-commit/pre-push `g-hk-*.ps1` through git `core.hooksPath`.

### Verify
```powershell
Test-Path .aider.conf.yml             # config present
Test-Path CONVENTIONS.md              # folded gald3r guidance
aider --config .aider.conf.yml --version
```

## 4. Common Pitfalls

- **No `.claude/` reuse** — aider does not read `CLAUDE.md`/`AGENTS.md` or discover `.claude/`/
  `.agents/`. Skills, agents, custom commands, and MCP have **no runtime home**; do not ship the
  Claude-Code tree expecting it to load.
- **`CONVENTIONS.md` is not auto-loaded by name** — it must be in `read:` (or loaded via
  `/read-only CONVENTIONS.md` / `aider --read CONVENTIONS.md`).
- **Auto-commit collision** — aider auto-commits each accepted edit; disable (`auto-commits: false`)
  or audit, to keep gald3r's commit discipline intact.
- **Read-only files cost context every turn** — pin selectively (don't pin a large `TASKS.md`).
- **`lint-cmd`/`test-cmd` are edit-cycle triggers, not a hook bus** — they cannot fire gald3r `.ps1`
  on session/tool boundaries; general event hooks are open feature request #2045.

## 5. Capability Summary

| Feature | Status | Notes |
|---|---|---|
| Rules (`g-rl-*`) | ✅ | native — `CONVENTIONS.md` pinned read-only via `--read` / `.aider.conf.yml read:` (arbitrary filename; no rules folder; no `AGENTS.md`/`CLAUDE.md` auto-discovery) |
| Commands (`@g-*`) | ⚠️ | 40+ built-in slash commands (`/add`, `/architect`, `/run`, `/load`, `/web`, …); `/load` replays built-ins; **no** user-defined custom commands |
| Agents (`g-agnt-*.md`) | ⚠️ | fixed chat modes (`code`/`architect`/`ask`/`help`); architect = architect-model + `--editor-model` two-LLM split; **no** sub-agent files |
| Hooks (`g-hk-*.ps1`) | ⚠️ | auto-lint/auto-test post-edit trigger (`--auto-lint`/`--lint-cmd`, `--auto-test`/`--test-cmd`) + git auto-commit; **no** SessionStart/Stop/PreToolUse event bus (FR #2045) |
| Skills (`g-skl-*/SKILL.md`) | ❌ | no native `SKILL.md` discovery/activation; community `aider-skills` PyPI injects externally |
| MCP | ❌ | core CLI has none (issue #4506 open, no maintainer roadmap); only AiderDesk / `mcpm-aider` bridges |

Full assessment + evidence in `PLATFORM_SPEC.md`. Re-verify on the next `@g-platform-scan-docs aider` (crawl_max_age_days: 14).
