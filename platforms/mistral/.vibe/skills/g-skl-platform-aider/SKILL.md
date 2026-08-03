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
  - https://aider.chat/docs/config/aider_conf.html
  - https://github.com/Aider-AI/aider/issues/4506
  - https://github.com/Aider-AI/aider/issues/4363
last_doc_scan: 2026-07-18
capability_status:
  hooks: "⚠️ partial — auto-lint/auto-test post-edit trigger (--auto-lint/--lint-cmd, --auto-test/--test-cmd) + git auto-commit; NO general event hooks (FR #2045)"
  rules: "✅ native — CONVENTIONS.md pinned read-only via --read / .aider.conf.yml read: (arbitrary filename; no rules folder); gald3r's own `gald3r platform install aider` now writes BOTH files automatically (T407)"
  skills: "❌ not native — no SKILL.md discovery/activation; community aider-skills PyPI injects externally"
  commands: "⚠️ partial — 40+ built-in slash commands (/add /architect /run /load …); NO user-defined custom commands"
  agents: "⚠️ partial — fixed chat modes (code/architect/ask/help); architect = architect-model + --editor-model; NO sub-agent files"
  mcp: "❌ not native — core CLI has none (FR #4506 open); only AiderDesk / mcpm-aider bridges"
token_budget: low
subsystem_memberships: [PLATFORM_INTEGRATION]
---

## HELP CONTRACT (T442 — cross-platform, non-substitutable)

If the invoking command's arguments are EXACTLY `-h`, `--help`, or `help` (one
token, nothing else): do NOT run any operation of this skill. Respond ONLY with a
compact usage card — the command's name, its one-line purpose, each documented
argument/option on its own line (or "none"), and the path to its command file —
then STOP. Read-only: no `.gald3r/` writes, no state changes, no task/bug
creation. This block lives in the SKILL (not a rule) because skills are the
execution layer on every supported platform; rules are optional context on most.

# g-skl-platform-aider

Activate for: setting up gald3r with Aider (terminal CLI), authoring `.aider.conf.yml` + `CONVENTIONS.md`, configuring read-only context / model roles, or verifying the Aider gald3r install.

---

> Full 9-section breakdown + evidence URLs in `PLATFORM_SPEC.md` (this folder). **Status: ⚠️ partial
> parity** — only **rules** are native (read-only `CONVENTIONS.md`); **commands/agents/hooks** are
> partial (built-in slash commands, fixed chat modes, auto-lint/test trigger only); **skills/MCP**
> are not native. Aider does **NOT** read `CLAUDE.md`/`AGENTS.md` or `.claude/`/`.agents/` trees, so
> gald3r's Claude-Code artifacts are **not reusable** — fold guidance into a pinned `CONVENTIONS.md`.
> **`gald3r platform install aider` now does this automatically** (T407): it writes a real
> `CONVENTIONS.md` AND a companion `.aider.conf.yml` pinning it via `read:`, so a fresh install is
> genuinely consumed by aider, not dropped on disk and ignored — see section 3 below.
> (Re-verified 2026-07-18 against https://aider.chat/docs — CONVENTIONS.md is still NOT
> auto-discovered by filename, and aider still has no native AGENTS.md support: issue #4363 remains
> open/unimplemented.)

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

**`gald3r platform install aider` automates the wiring (T407).** A fresh install writes a real,
non-stub `CONVENTIONS.md` (the same generic gald3r instructions body every `root_instructions`
platform shares) AND a companion `.aider.conf.yml` with a `read:` key pinning it — so the file is
genuinely consumed, not dropped on disk and silently ignored. This is a distinct mechanism from the
generic `root_instructions` layout entry other platforms get (see `layout_map.yaml`'s
`conventions_file` entry): aider's convention file is NOT natively auto-discovered by filename, so
the companion config write is required, not optional.

Manual customization still applies on top: fold additional project-specific `g-rl-*` guidance into
`CONVENTIONS.md`, and pin more `.gald3r/` context (`.gald3r/PROJECT.md`, `.gald3r/CONSTRAINTS.md`,
...) via more `read:` entries — that remains aider's only persistent always-apply surface. Set
`auto-commits: false` so aider does not race gald3r's task-scoped commit flow. Optionally wire
`lint-cmd`/`test-cmd` to a gald3r verification script for a post-edit gate, and route
pre-commit/pre-push `g-hk-*.py` (via `python <path>`) through git `core.hooksPath`.

### Verify
```powershell
Test-Path .aider.conf.yml             # config present (gald3r-managed `read:` key, T407)
Test-Path CONVENTIONS.md              # real gald3r guidance (T407), not a stub
Select-String -Path .aider.conf.yml -Pattern "CONVENTIONS.md"   # confirm the pin is present
aider --config .aider.conf.yml --version
```

## 4. Common Pitfalls

- **No `.claude/` reuse** — aider does not read `CLAUDE.md`/`AGENTS.md` or discover `.claude/`/
  `.agents/`. Skills, agents, custom commands, and MCP have **no runtime home**; do not ship the
  Claude-Code tree expecting it to load.
- **`CONVENTIONS.md` is not auto-loaded by name** — it must be in `read:` (or loaded via
  `/read-only CONVENTIONS.md` / `aider --read CONVENTIONS.md`). `gald3r platform install aider`
  writes this pin automatically (T407); a hand-authored `CONVENTIONS.md` that skips the `read:`
  wiring is silently never read.
- **Auto-commit collision** — aider auto-commits each accepted edit; disable (`auto-commits: false`)
  or audit, to keep gald3r's commit discipline intact.
- **Read-only files cost context every turn** — pin selectively (don't pin a large `TASKS.md`).
- **`lint-cmd`/`test-cmd` are edit-cycle triggers, not a hook bus** — they cannot fire gald3r `.py`
  hooks (`python <path>`) on session/tool boundaries; general event hooks are open feature request #2045.

## 5. Capability Summary

| Feature | Status | Notes |
|---|---|---|
| Rules (`g-rl-*`) | ✅ | native — `CONVENTIONS.md` pinned read-only via `--read` / `.aider.conf.yml read:` (arbitrary filename; no rules folder; no `AGENTS.md`/`CLAUDE.md` auto-discovery) |
| Commands (`@g-*`) | ⚠️ | 40+ built-in slash commands (`/add`, `/architect`, `/run`, `/load`, `/web`, …); `/load` replays built-ins; **no** user-defined custom commands |
| Agents (`g-agnt-*.md`) | ⚠️ | fixed chat modes (`code`/`architect`/`ask`/`help`); architect = architect-model + `--editor-model` two-LLM split; **no** sub-agent files |
| Hooks (`g-hk-*.py`) | ⚠️ | auto-lint/auto-test post-edit trigger (`--auto-lint`/`--lint-cmd`, `--auto-test`/`--test-cmd`) + git auto-commit; **no** SessionStart/Stop/PreToolUse event bus (FR #2045) |
| Skills (`g-skl-*/SKILL.md`) | ❌ | no native `SKILL.md` discovery/activation; community `aider-skills` PyPI injects externally |
| MCP | ❌ | core CLI has none (issue #4506 open, no maintainer roadmap); only AiderDesk / `mcpm-aider` bridges |

Full assessment + evidence in `PLATFORM_SPEC.md`. Re-verify on the next `@g-platform-scan-docs aider` (crawl_max_age_days: 14).
