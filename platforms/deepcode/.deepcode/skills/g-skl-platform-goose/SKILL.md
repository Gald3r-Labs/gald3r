---
name: g-skl-platform-goose
description: Authoritative reference for Goose (Block) AI agent customization in gald3r projects. Covers .goosehints + AGENTS.md instructions, ~/.config/goose/config.yaml MCP extensions, Recipes/Subrecipes as slash commands, native subagents, Agent Skills (SKILL.md, shared via ~/.claude/skills/), lifecycle hooks (hooks.json), and gald3r install verification.
crawl_max_age_days: 14
vault_doc_path: research/platforms/goose/
vault_docs_url: https://block.github.io/goose/docs
docs_url: https://block.github.io/goose/docs
docs_url_secondary:
  - https://goose-docs.ai/docs
  - https://goose-docs.ai/blog/2026/05/14/goose-hooks/
  - https://goose-docs.ai/docs/guides/subagents/
  - https://goose-docs.ai/docs/guides/context-engineering/using-skills/
  - https://block.github.io/goose/docs/guides/recipes/
  - https://block.github.io/goose/docs/getting-started/using-extensions/
last_doc_scan: 2026-06-02
capability_status:
  hooks: "✅ native lifecycle hooks (hooks.json in .agents/plugins/<name>/hooks/; 11 events SessionStart..AfterShellExecution; shell scripts; announced 2026-05-14)"
  rules: "✅ .goosehints static always-on (global + project; every line sent every request) + Memory Extension (dynamic MCP memory)"
  skills: "✅ Agent Skills (SKILL.md) auto-discovered from ~/.config/goose/skills/ OR ~/.claude/skills/ (shared with Claude)"
  commands: "✅ custom slash commands for Recipes (Desktop + CLI) + built-in /plan,/mode,/prompts,/builtin,/clear"
  agents: "✅ native subagents (auto-spawned, parallel up to 10) + Subrecipes (typed reusable recipe files)"
  mcp: "✅ native — extensions ARE MCP servers; extensions: in ~/.config/goose/config.yaml; 70+ extensions"
token_budget: low
subsystem_memberships: [PLATFORM_INTEGRATION]
---

# g-skl-platform-goose

Activate for: setting up gald3r with Goose (goose CLI / goose Desktop), authoring
recipes/subagents/skills/hooks/rules, or verifying the Goose gald3r install.

---

> Full 9-section breakdown + evidence URLs in `PLATFORM_SPEC.md` (this folder). **Status: ✅ full
> parity** — Goose natively supports commands (Recipes), rules (`.goosehints` + Memory Extension),
> agents (subagents/Subrecipes), skills (`SKILL.md`), lifecycle hooks, and MCP, and discovers Agent
> Skills from `~/.claude/skills/`, so gald3r's Claude `SKILL.md` assets are reusable. Instruction
> file is `.goosehints` (+ `AGENTS.md`), **not** `CLAUDE.md`. (Verified 2026-06-02 against
> https://block.github.io/goose/docs + goose-docs.ai mirror.)

## 1. Platform Overview

**Goose** — Block's open-source, on-machine AI developer agent, available as the **goose CLI**
(headless/CI-friendly) and **goose Desktop** (one-click recipe launch). It is **global-config-first**:
the primary config (`config.yaml`, global skills, global `.goosehints`) lives under
`~/.config/goose/`, with project scope layered on top. Its defining trait is the deepest, oldest MCP
integration of any agent — **extensions ARE MCP servers**.

## 2. Config Layout

```
~/.config/goose/
├── config.yaml            ← provider, model, enabled extensions (MCP servers)
├── .goosehints            ← GLOBAL static always-on rules
└── skills/  <name>/SKILL.md   ← GLOBAL Agent Skills (auto-discovered)

~/.claude/skills/ <name>/SKILL.md   ← ALSO discovered (shared with Claude)
~/.agents/plugins/<name>/hooks/hooks.json   ← USER lifecycle hooks

<project-root>/
├── .goosehints            ← PROJECT static always-on rules (every line sent every request)
├── AGENTS.md              ← read/supported (Agent Context); NOT CLAUDE.md
└── .agents/plugins/<name>/hooks/hooks.json   ← PROJECT lifecycle hooks
```

Goose discovers Agent Skills from **`~/.claude/skills/`** → **gald3r's Claude `SKILL.md` tree works
as-is on Goose.** Recipes/Subrecipes (portable YAML) are the command/workflow primitive.

## 3. gald3r Integration

**Cheapest high-parity install: point Goose at the shared `~/.claude/skills/` tree** (or copy into
`~/.config/goose/skills/`) so gald3r `g-skl-*` load natively. Then add `.goosehints` (rules), recipe
YAML surfaced as custom slash commands (commands/workflows), a `hooks.json` plugin (hooks), and an
MCP `extensions:` entry in `~/.config/goose/config.yaml`. Map `g-agnt-*` to **Subrecipes** (typed,
reusable). Goose Desktop / CLI also support scheduled/headless task execution for unattended runs.

### config.yaml MCP extension example
```yaml
extensions:
  gald3r:
    type: stdio          # or "sse"/remote with a `uri:` for a URL-based MCP server
    cmd: <gald3r-mcp-command>
    enabled: true
```
> Manage extensions interactively with `goose configure`. The Developer + Memory extensions ship
> enabled by default.

### Verify
```powershell
Test-Path $HOME/.config/goose/config.yaml        # provider + MCP extensions
Test-Path $HOME/.config/goose/skills ; Test-Path $HOME/.claude/skills   # skill discovery dirs
Test-Path .goosehints                            # project rules
Test-Path .agents/plugins                        # lifecycle hook plugins
```

## 4. Common Pitfalls

- **Global-config-first**: `config.yaml`, global skills, and global `.goosehints` live under
  `~/.config/goose/`, not the repo. Don't expect a `.goose/config.yaml` project file (it doesn't
  exist) — the old `GOOSE.md` / `.goose/config.yaml` convention was wrong.
- **Instruction file is `.goosehints`** (+ `AGENTS.md`). Goose does **not** read `CLAUDE.md` as
  instructions — only Agent Skills are shared from `~/.claude/skills/`.
- **Rules are a single always-on `.goosehints` blob** — no `.mdc`, no `alwaysApply:`/`globs:`
  per-file scoping. Concatenate `g-rl-*` into `.goosehints`; use the Memory Extension for dynamic
  recall.
- **Hooks are new (announced 2026-05-14)** and run **shell scripts** — on Windows invoke PowerShell
  explicitly (`pwsh -File g-hk-*.ps1`); a bare `.ps1` is not a POSIX shell script. Re-verify the
  young hook surface on the next crawl.
- **Two reusable-workflow primitives** overlap: Recipes (YAML → slash commands) and Subrecipes
  (typed, parallelizable) vs one-off natural-language subagents — pick the right one per gald3r need.

## 5. Capability Summary

| Feature | Status | Notes |
|---|---|---|
| Hooks (`g-hk-*`) | ✅ | `hooks.json` in `.agents/plugins/<name>/hooks/`; 11 events; shell scripts (invoke `pwsh` on Windows); announced 2026-05-14 |
| Skills (`g-skl-*/SKILL.md`) | ✅ | auto-discovered from `~/.config/goose/skills/` **or `~/.claude/skills/`** (shared w/ Claude); Skills Marketplace |
| Agents (`g-agnt-*`) | ✅ | native subagents (auto-spawned, parallel up to 10) + **Subrecipes** (typed reusable recipe files) |
| Commands (`@g-*`) | ✅ | custom slash commands for **Recipes** (Desktop + CLI) + built-in `/plan`,`/mode`,`/prompts`,`/builtin`,`/clear` |
| Rules (`g-rl-*`) | ✅ | `.goosehints` static always-on (global + project) + Memory Extension (dynamic) — single blob, no glob scoping |
| MCP | ✅ | extensions ARE MCP servers; `extensions:` in `~/.config/goose/config.yaml`; 70+ extensions; built-in Developer/Memory |

Full assessment + evidence in `PLATFORM_SPEC.md`. Re-verify on the next `@g-platform-scan-docs goose` (crawl_max_age_days: 14).
