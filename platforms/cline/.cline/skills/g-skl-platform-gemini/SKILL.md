---
name: g-skl-platform-gemini
description: Authoritative reference for Gemini CLI (Google) customization in gald3r projects. Covers .gemini/ native config — settings.json hooks + MCP, TOML commands, markdown subagents, SKILL.md Agent Skills — GEMINI.md hierarchical memory (AGENTS.md-capable via context.fileName), and gald3r install verification.
crawl_max_age_days: 7
vault_doc_path: research/platforms/gemini/
vault_docs_url: https://github.com/google-gemini/gemini-cli
docs_url: https://github.com/google-gemini/gemini-cli
docs_url_secondary:
  - https://geminicli.com/docs/
  - https://geminicli.com/docs/hooks/
  - https://geminicli.com/docs/core/subagents/
  - https://geminicli.com/docs/cli/skills/
  - https://geminicli.com/docs/cli/custom-commands/
  - https://geminicli.com/docs/cli/gemini-md/
  - https://geminicli.com/docs/tools/mcp-server/
last_doc_scan: 2026-06-02
capability_status:
  hooks: "✅ native lifecycle hooks in .gemini/settings.json (11 events SessionStart…Notification; synchronous; added ~Jan 2026, default v0.26.0+)"
  rules: "✅ hierarchical GEMINI.md memory (@file.md imports; /memory add|show|refresh); context.fileName makes AGENTS.md a native context file"
  skills: "✅ Agent Skills (SKILL.md) in .gemini/skills/ or .agents/skills/; activate_skill; /skills list|link|enable|disable|reload"
  commands: "✅ native TOML slash commands .gemini/commands/*.toml (/name, /dir:name; prompt key + {{args}} + shell)"
  agents: "✅ native subagents .gemini/agents/*.md (md + YAML; @name; parallel; added ~Apr 2026)"
  mcp: "✅ native — mcpServers in .gemini/settings.json (@-prefixed tools; per-subagent scoping; /mcp)"
token_budget: low
subsystem_memberships: [PLATFORM_INTEGRATION]
---

# g-skl-platform-gemini

Activate for: setting up gald3r with Gemini CLI, authoring commands/agents/skills/hooks/rules, or verifying the Gemini gald3r install.

---

> Full 9-section breakdown + evidence URLs in `PLATFORM_SPEC.md` (this folder). **Status: ✅ near-full
> parity** — Gemini CLI natively supports commands (TOML), rules (GEMINI.md memory), subagents,
> Agent Skills, an 11-event hook system, and MCP. (Verified 2026-06-02 against
> https://github.com/google-gemini/gemini-cli + https://geminicli.com/docs/.) This **supersedes** the
> prior assessment, which marked hooks/skills ❌ and agents ⚠️ — subagents (~Apr 2026) and hooks
> (~Jan 2026) are now native.

## 1. Platform Overview

**Gemini CLI** (`gemini` command, `google-gemini/gemini-cli`, Apache-2.0) — Google's open-source
terminal coding agent. Native config lives under **`.gemini/`**; the instruction/memory file is
**`GEMINI.md`** (hierarchical). Among the most fully-featured gald3r targets.

- **Instruction file**: **`GEMINI.md`** by default (NOT `AGENTS.md`) — but `context.fileName` in
  `settings.json` can add `AGENTS.md`/`CONTEXT.md` as native context files
- **Memory**: hierarchical `GEMINI.md` with `@file.md` imports (`/memory show` / `/memory refresh`)
- **Commands**: native **TOML** in `.gemini/commands/*.toml` (`/name`, `/dir:name`)
- **Subagents**: markdown + YAML in `.gemini/agents/*.md` (`@name`, parallel) — added ~Apr 2026
- **Skills**: Agent Skills (`SKILL.md`) in `.gemini/skills/` or `.agents/skills/` (`activate_skill`)
- **Hooks**: 11-event lifecycle hooks in `.gemini/settings.json` (synchronous) — added ~Jan 2026
- **MCP**: first-class `mcpServers` in `.gemini/settings.json` (`@`-prefixed tools; per-subagent)
- **Bonus**: headless/CI mode, checkpointing, Google Search grounding, Extensions distribution

## 2. Config Layout

```
<project-root>/
├── GEMINI.md                       ← native hierarchical memory (AGENTS.md via context.fileName)
└── .gemini/
    ├── settings.json               ← hooks + mcpServers + context.fileName + model/tools
    ├── commands/ <name>.toml        ← custom slash commands (nestable → /dir:name)
    ├── agents/   *.md               ← subagents (markdown + YAML)
    └── skills/   <name>/SKILL.md    ← Agent Skills (SKILL.md standard)
~/.gemini/                          ← user-global mirror
.agents/skills/  /  ~/.agents/skills/   ← alias skill dirs Gemini also discovers
```

Skills load from **both** `.gemini/skills/` and the `.agents/skills/` alias → gald3r `g-skl-*` ship
either way.

## 3. gald3r Integration

**All six gald3r primitives map onto native `.gemini/` folders** — no portability scaffolding needed:
TOML commands (`.gemini/commands/g-*.toml`), markdown subagents (`.gemini/agents/g-agnt-*.md`),
Agent Skills (`.gemini/skills/<name>/SKILL.md`), hooks + MCP (`.gemini/settings.json`), and a
`GEMINI.md` overlay that `@`-imports `AGENTS.md`. Bundle-distribute via `gemini extensions`.

### Verify
```powershell
Test-Path GEMINI.md                 # native hierarchical memory
Test-Path .gemini/settings.json     # hooks + mcpServers
Test-Path .gemini/commands ; Test-Path .gemini/agents ; Test-Path .gemini/skills
gemini --version                    # CLI present (confirm subagent/hook support on this version)
```

## 4. Common Pitfalls

- **Commands are TOML**, not `.md` — gald3r `g-*` commands must be emitted as `.gemini/commands/g-*.toml`
  (required key `prompt`; `{{args}}` + shell exec). A `.md` doc alone is not an executable command.
- **Default instruction file is `GEMINI.md`, not `AGENTS.md`** — to reuse the gald3r universal
  `AGENTS.md`, set `context.fileName` in `settings.json` (e.g. `["AGENTS.md","GEMINI.md"]`) or
  `@`-import it from `GEMINI.md`.
- **GEMINI.md is concatenated into every prompt** — keep inlined rule content lean (context bloat).
  `/memory add` appends to it; guard gald3r-authored sections against memory-injection overwrite.
- **Recency** — subagents (~Apr 2026) and hooks (~Jan 2026, default v0.26.0+) are new; on older CLI
  builds they may be absent. Verify with `gemini --version` before relying on them.
- Hooks + MCP are **settings-driven** (`.gemini/settings.json`), not standalone committed files.

## 5. Capability Summary

| Feature | Status | Notes |
|---|---|---|
| Hooks (`g-hk-*`) | ✅ | `.gemini/settings.json`; 11 events (SessionStart…Notification); synchronous; ~Jan 2026 |
| Skills (`g-skl-*/SKILL.md`) | ✅ | Agent Skills; `.gemini/skills/` or `.agents/skills/`; `activate_skill`; `/skills` |
| Agents (`g-agnt-*.md`) | ✅ | native subagents `.gemini/agents/*.md` (md + YAML; `@name`; parallel; ~Apr 2026) |
| Commands (`@g-*`) | ✅ | native **TOML** `.gemini/commands/*.toml` (`/name`, `/dir:name`; `prompt` + `{{args}}`) |
| Rules (`g-rl-*`) | ✅ | hierarchical `GEMINI.md` memory (`@file.md` imports); `context.fileName` AGENTS.md-capable |
| MCP | ✅ | `mcpServers` in `.gemini/settings.json`; `@`-prefixed tools; per-subagent scoping; `/mcp` |

Full assessment + evidence in `PLATFORM_SPEC.md`. Re-verify on the next `@g-platform-scan-docs gemini` (crawl_max_age_days: 7).
