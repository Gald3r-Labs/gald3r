---
name: g-skl-platform-qwen
description: Authoritative reference for Qwen Code (Alibaba CLI coding agent, a Gemini CLI fork) customization in gald3r projects. Covers .qwen/settings.json, QWEN.md context, custom commands, MCP, and gald3r install verification.
docs_url: https://qwenlm.github.io/qwen-code-docs/
crawl_max_age_days: 14
vault_doc_path: research/platforms/qwen/
vault_docs_url: https://github.com/QwenLM/qwen-code
token_budget: low
capability_status:
  hooks: "❌ no native hook/event system (Gemini-CLI lineage)"
  rules: "⚠️ no rules folder; only via QWEN.md context/import (@path)"
  skills: "❌ no native skills discovery; instruction-file reference only"
  commands: "⚠️ native custom commands in .qwen/commands/, but gald3r g-* emitted as .md, not executable"
  mcp: "✅ first-class mcpServers in .qwen/settings.json (doc-verified)"
last_doc_scan: never
reference: g-skl-platform-cursor
subsystem_memberships: [PLATFORM_INTEGRATION]
---

# g-skl-platform-qwen

Activate for: setting up gald3r with Qwen Code CLI, authoring Qwen instructions, or verifying Qwen gald3r integration.

---

## 1. Platform Overview

**Qwen Code** is Alibaba's open-source terminal AI coding agent. It is an **adapted fork of
Google's Gemini CLI**, so its customization surface is nearly identical to Gemini CLI
(`g-skl-platform-gemini`) — only the folder name (`.qwen/`), the context filename (`QWEN.md`), and
the default models differ.

- **Config**: `.qwen/settings.json` (project) + `~/.qwen/settings.json` (user) — JSON, NOT YAML
- **Context/memory**: `QWEN.md` (configurable via `context.fileName`); hierarchical, supports
  `@path/to/file.md` imports; managed with the built-in `/memory` command family
- **Custom commands**: `.qwen/commands/` (TOML, or Markdown+YAML frontmatter in newer versions;
  TOML deprecated-but-supported), namespaced via subdirectories (`/dir:name`)
- **MCP**: first-class — `mcpServers` block in `settings.json`; `/mcp` to inspect
- **No native**: rules folder, skills system, sub-agent files, or lifecycle hooks
- **Models**: Qwen3-Coder series and other providers configured under `modelProviders`
- **Session**: interactive or non-interactive (headless) mode

> **See `PLATFORM_SPEC.md` in this skill folder** for the verified 9-section capability spec.

---

## 2. Config File Layout

```
<project-root>/
├── .qwen/
│   ├── settings.json       ← Qwen Code configuration (model providers, env, auth, context, mcpServers)
│   └── commands/           ← custom slash commands (TOML or Markdown+YAML), nestable for namespacing
│       └── <name>.toml | <name>.md   ← invoked as /<name> (or /<dir>:<name>)
└── QWEN.md                 ← project context/memory file (hierarchical; @path imports)

~/.qwen/settings.json       ← user-global settings (modelProviders, auth, mcpServers)
~/.qwen/commands/           ← user-global custom commands
```

> **Correction (vs. earlier scaffold):** Qwen Code uses **`.qwen/settings.json`** (JSON) +
> **`QWEN.md`**, NOT a `config.yaml` + `instructions.md` pair. The legacy deploy scaffold under
> `gald3r_template/.gald3r_sys/platforms/.qwen/` still ships the old `config.yaml`/`instructions.md`
> and is slated for regeneration (see Known Gaps).

**`settings.json` (illustrative — confirm exact keys via SCAN_DOCS):**
```json
{
  "context": { "fileName": "QWEN.md" },
  "mcpServers": {
    "gald3r": { "command": "node", "args": ["path/to/mcp-server.js"] }
  }
}
```

---

## 3. gald3r Integration

### Install

```bash
node bin/install.js --only qwen
```

gald3r writes `QWEN.md` (the only file Qwen natively reads as context) and installs the portable
`.agent/` tree (rules/skills/agents/commands as `.md`). Qwen does **not** auto-discover `.agent/`;
gald3r content is surfaced by **referencing it from `QWEN.md`** (e.g. `@AGENTS.md`, or
`@.agent/rules/g-rl-00-always.md` imports).

### QWEN.md Content (gald3r overlay)

In the gald3r ecosystem the universal instructions live in **`AGENTS.md`**; `QWEN.md` is a thin
Qwen-specific overlay that imports it:

```markdown
# QWEN.md — gald3r overlay

@AGENTS.md

## Task Management
Tasks tracked in .gald3r/TASKS.md.
Before implementing: read active task in .gald3r/tasks/task{id}_*.md.
Commit format: feat(T{id}): description

## Bug Protocol
Never silently ignore bugs. Pre-existing bugs → document in .gald3r/BUGS.md.
```

Keep imported content lean — `QWEN.md` and its `@`-imports are concatenated into every prompt
(`token_budget: low`).

---

## 4. Verification

```powershell
Test-Path .qwen\settings.json   # native config
Test-Path QWEN.md               # native context file
qwen --version                  # confirm Qwen Code installed
```

---

## 5. Common Pitfalls

- Qwen Code is a **Gemini CLI fork** and rapidly evolving — config keys may shift between versions;
  confirm against https://qwenlm.github.io/qwen-code-docs/ (SCAN_DOCS not yet run).
- Config is **JSON `settings.json`**, NOT `config.yaml` — do not author the old scaffold format.
- Model availability depends on the configured `modelProviders` / API key (Alibaba Model Studio or
  compatible provider).
- Custom commands belong in `.qwen/commands/` (TOML or Markdown+YAML); gald3r's `.agent/commands/g-*.md`
  are docs, not executable Qwen slash commands.
- Headless mode useful for CI but requires explicit task scoping.

---

## 6. Known Gaps (features that do NOT work on Qwen Code)

Qwen Code inherits Gemini CLI's capability shape. See `PLATFORM_SPEC.md` §9 for the full list.

| Capability | Status | Note |
|---|---|---|
| Lifecycle hooks | ❌ | No `hooks.json` / event system. PCAC inbox check, session-start injection, pre-commit/push gates do not fire automatically. |
| Always-apply rules folder | ⚠️ | No native `.agent/rules/` loading or `alwaysApply:`/`globs:`. Rules effective only when imported into `QWEN.md`. |
| Skills discovery | ❌ | No native `SKILL.md` model-selection. Reachable only via `QWEN.md` reference/import. |
| Sub-agent files | ⚠️ | No `.cursor/agents/`-style discovery; `g-agnt-*.md` works only as conversational references. |
| Executable gald3r commands | ⚠️ | gald3r `g-*` ship as `.md` under `.agent/commands/`, not emitted into `.qwen/commands/` → not runnable as slash commands. |
| MCP | ✅ | First-class `mcpServers` in `.qwen/settings.json` (mechanism doc-verified; server set ❓ untested). |
| Stale deploy scaffold | ⚠️ | `platforms/.qwen/config.yaml` + `instructions.md` are wrong; regenerate to `settings.json` + `QWEN.md`. |

Legend: ✅ verified · ⚠️ partial / non-native / via QWEN.md only · ❌ not supported · ❓ untested.
