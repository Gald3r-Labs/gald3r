---
name: g-skl-platform-qwen
description: Authoritative reference for Qwen Code (Alibaba CLI coding agent, a Gemini CLI fork) customization in gald3r projects. Covers .qwen/settings.json hooks+MCP, QWEN.md context (NOT AGENTS.md by default), custom commands, subagents, Agent Skills (SKILL.md), and gald3r install verification.
crawl_max_age_days: 14
vault_doc_path: research/platforms/qwen/
vault_docs_url: https://qwenlm.github.io/qwen-code-docs/
docs_url: https://qwenlm.github.io/qwen-code-docs/
docs_url_secondary:
  - https://qwenlm.github.io/qwen-code-docs/en/users/features/hooks/
  - https://qwenlm.github.io/qwen-code-docs/en/users/features/sub-agents/
  - https://qwenlm.github.io/qwen-code-docs/en/users/features/skills/
  - https://qwenlm.github.io/qwen-code-docs/en/users/features/commands/
  - https://qwenlm.github.io/qwen-code-docs/en/core/memport/
  - https://qwenlm.github.io/qwen-code-docs/en/users/features/mcp/
last_doc_scan: 2026-06-02
capability_status:
  hooks: "✅ native 14-event lifecycle hooks in .qwen/settings.json (command incl. PowerShell / http; matcher, timeouts)"
  rules: "✅ hierarchical QWEN.md context/memory with @file.md imports (/memory show|refresh)"
  skills: "✅ Agent Skills (SKILL.md) in .qwen/skills/, model-invoked; GA 2026-02-09"
  commands: "✅ native slash commands .qwen/commands/ (Markdown+YAML; TOML back-compat; /dir:name)"
  agents: "✅ native subagents .qwen/agents/ (md + YAML; /agents, approvalMode, tools allowlist)"
  mcp: "✅ first-class mcpServers in .qwen/settings.json (stdio/SSE/HTTP, OAuth) + qwen mcp add + /mcp"
token_budget: low
subsystem_memberships: [PLATFORM_INTEGRATION]
---

# g-skl-platform-qwen

Activate for: setting up gald3r with Qwen Code CLI, authoring commands/agents/skills/hooks/QWEN.md, or verifying the Qwen gald3r install.

---

> Full 9-section breakdown + evidence URLs in `PLATFORM_SPEC.md` (this folder). **Status: ✅ full
> parity** — Qwen Code natively supports commands, rules/memory, agents, skills, hooks (14 events),
> and MCP. As a Gemini CLI fork it inherits commands/memory/MCP and adds Claude-Code-style
> hooks/subagents/skills. Default context file is **`QWEN.md`, not `AGENTS.md`**. (Verified
> 2026-06-02 against https://qwenlm.github.io/qwen-code-docs/.)

## 1. Platform Overview

**Qwen Code** (`qwen` command, Alibaba / `QwenLM/qwen-code`) — an open-source terminal AI coding
agent, an **adapted fork of Google's Gemini CLI** optimized for Qwen3-Coder models. Config is
`.qwen/settings.json` (JSON, **NOT** `config.yaml`); context/memory is `QWEN.md`. Agent Skills reached
GA (flag removed) in the 2026-02-09 v0.9.x release.

## 2. Config Layout

```
<project-root>/
├── QWEN.md                          ← default context/memory Qwen reads (NOT AGENTS.md)
└── .qwen/
    ├── settings.json                ← hooks + mcpServers + model providers + context
    ├── commands/ *.md | *.toml      ← custom slash commands (Markdown+YAML; TOML back-compat)
    ├── agents/   *.md               ← subagents (markdown + YAML)
    └── skills/   <name>/SKILL.md    ← Agent Skills (model-invoked)

~/.qwen/                             ← user-global mirror (settings.json, commands/, agents/, skills/, QWEN.md)
```

Qwen Code also has a first-class **Extensions** mechanism that bundles commands + subagents + MCP +
context for one-click distribution.

> **Correction (vs. earlier scaffold):** Qwen Code uses **`.qwen/settings.json`** (JSON) + **`QWEN.md`**,
> NOT a `config.yaml` + `instructions.md` pair. The legacy deploy scaffold under
> `project_template/.gald3r_sys/platforms/.qwen/` still ships the old format and is slated for
> regeneration.

## 3. gald3r Integration

**Cheapest high-parity install:** ship a thin `QWEN.md` overlay that `@AGENTS.md`-imports the gald3r
instruction set, plus the `.qwen/` commands/agents/skills trees and a `.qwen/settings.json` carrying
hooks + MCP. (To make `AGENTS.md` itself the native context file, set `context.fileName` to include
it — but it is **not** a built-in default; open issue #2006.) Or package everything as a Qwen
**Extension** for one-click distribution.

### QWEN.md overlay
```markdown
# QWEN.md — gald3r overlay
@AGENTS.md
```
Keep imported content lean — `QWEN.md` and its `@`-imports are concatenated into every prompt
(`token_budget: low`).

### Verify
```powershell
Test-Path .qwen/settings.json    # hooks + MCP config
Test-Path QWEN.md                # native context file
Test-Path .qwen/commands ; Test-Path .qwen/agents ; Test-Path .qwen/skills
qwen --version                   # confirm Qwen Code (and that it exposes hooks/subagents/skills)
```

## 4. Common Pitfalls

- Default context file is **`QWEN.md`, not `AGENTS.md`** — use `context.fileName` or a `@AGENTS.md`
  overlay to reuse the gald3r instruction set.
- Config is **JSON `settings.json`**, NOT `config.yaml` — do not author the old scaffold format.
- Hooks + MCP are **settings-driven** (`.qwen/settings.json`), not standalone committed files.
- Custom commands are **Markdown+YAML** (TOML deprecated but still accepted) in `.qwen/commands/`;
  subdirectories namespace via `:` (`git/commit.md` → `/git:commit`).
- Subagents, hooks, and GA-skills are **recent 2026 additions** (skills GA 2026-02-09) — a rapidly
  evolving fork; confirm the installed CLI version exposes them and re-check on SCAN_DOCS.

## 5. Capability Summary

| Feature | Status | Notes |
|---|---|---|
| Hooks (`g-hk-*.ps1`) | ✅ | `.qwen/settings.json` `"hooks"`; 14 events; `command` (PowerShell ok) / `http`; matcher, timeouts |
| Skills (`g-skl-*/SKILL.md`) | ✅ | Agent Skills (`SKILL.md`) in `.qwen/skills/`, model-invoked; GA 2026-02-09 |
| Agents (`g-agnt-*.md`) | ✅ | native subagents `.qwen/agents/` (md + YAML); `/agents`, `approvalMode`, `tools` allowlist |
| Commands (`@g-*`) | ✅ | `.qwen/commands/*.md` (Markdown+YAML; TOML back-compat); `/dir:name`, `{{args}}` |
| Rules (`g-rl-*`) | ✅ | hierarchical `QWEN.md` context/memory + `@file.md` imports; `/memory show`/`refresh` |
| MCP | ✅ | `mcpServers` in `.qwen/settings.json` (stdio/SSE/HTTP, OAuth); `qwen mcp add`; `/mcp` |

Full assessment + evidence in `PLATFORM_SPEC.md`. Re-verify on the next `@g-platform-scan-docs qwen` (crawl_max_age_days: 14).
