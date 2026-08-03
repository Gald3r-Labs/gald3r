---
name: g-skl-platform-mimo
description: Authoritative reference for Xiaomi MiMo-Code (terminal-native AI coding agent, a fork of OpenCode with persistent cross-session memory) customization in gald3r projects. Covers AGENTS.md + CLAUDE.md dual instruction files, MEMORY.md persistent memory, .mimocode/agents custom agents, MCP in mimocode.json, Compose-mode/Distill skills equivalents, and the partial/inherited hook surface pending verification.
crawl_max_age_days: 7
vault_doc_path: research/platforms/mimo/
vault_docs_url: https://mimo.xiaomi.com/mimocode
docs_url: https://mimo.xiaomi.com/mimocode
docs_url_secondary:
  - https://github.com/XiaomiMiMo/MiMo-Code
  - https://mimo.xiaomi.com/mimocode/agents
  - https://mimo.xiaomi.com/mimocode/start
last_doc_scan: 2026-06-13
capability_status:
  hooks: "⚠️ inherited from OpenCode; session hooks exist but lifecycle events need verification — target .mimocode/hooks.json once confirmed"
  rules: "✅ native — AGENTS.md at project root read natively; also reads CLAUDE.md"
  skills: "⚠️ via Compose mode workflows (equivalent, not SKILL.md-native); /distill auto-generates reusable skills into .mimocode/agents/{name}.md"
  commands: "✅ native — /goal, /dream, /distill, /voice, plus custom slash commands via Compose workflows in mimocode.json"
  agents: "✅ native — .mimocode/agents/*.md (project) or ~/.config/mimocode/agents/ (global)"
  mcp: "✅ native — mcp section in mimocode.json; inherits the full OpenCode MCP layer"
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

# g-skl-platform-mimo

Activate for: setting up gald3r with Xiaomi MiMo-Code, authoring agents/MCP, priming `AGENTS.md`
+ `CLAUDE.md` + `MEMORY.md`, or verifying the MiMo-Code gald3r install.

---

> Full 12-section breakdown + evidence URLs in `PLATFORM_SPEC.md` (this folder). **Status: ⚠️
> partial parity** — MiMo-Code (a fork of OpenCode, launched June 2026) natively supports
> **rules** (both `AGENTS.md` and `CLAUDE.md`), **commands**, **agents**, and **MCP**; **Skills**
> are approximated via Compose-mode workflows + `/distill` (not a `SKILL.md`-native mechanism);
> **hooks are inherited from OpenCode but unverified**. Adds persistent cross-session **memory**
> (`MEMORY.md`) with no direct OpenCode analog. (Verified 2026-06-13 against GitHub README +
> `mimo.xiaomi.com/mimocode` docs.)

## 1. Platform Overview

**MiMo-Code** is a terminal-native AI coding assistant built by Xiaomi as a fork of OpenCode. It
inherits OpenCode's core capabilities (TUI, LSP, MCP, providers, plugins) and adds persistent
cross-session memory, subagent orchestration, goal-driven autonomous loops (`/goal`), and a
Compose mode for specs-driven development. Reads **both** `AGENTS.md` and `CLAUDE.md` natively.

## 2. Config Layout

```
<project-root>/
├── AGENTS.md                          ← primary instruction file (read natively)
├── CLAUDE.md                          ← Claude Code compat file (also read)
├── MEMORY.md                          ← persistent project knowledge (auto-maintained via /dream)
├── checkpoint.md                      ← session state snapshot (auto)
└── .mimocode/
    ├── mimocode.json                  ← primary config (project-level); mcp key for MCP servers
    └── agents/  <name>.md             ← custom agent definitions (YAML frontmatter + prompt)

~/.config/mimocode/mimocode.json       ← global config
```

## 3. gald3r Integration

Write **`AGENTS.md`** (instruction file) at project root; add the gald3r MCP endpoint to
**`.mimocode/mimocode.json`**'s `mcp` key; place adapted gald3r agents in
**`.mimocode/agents/`**. Consider wiring `MEMORY.md` alongside `.gald3r/vault/` as a
memory-synergy target (MiMo-Code's persistent-memory differentiator).

```bash
gald3r platform install mimo --into <target-dir>
```

### Verify
```powershell
Test-Path AGENTS.md ; Test-Path CLAUDE.md
Select-String '"mcp"' .mimocode/mimocode.json
Test-Path .mimocode/agents
```

## 4. Common Pitfalls

- **Skills are NOT `SKILL.md`-native** — Compose-mode workflows + `/distill` are the closest
  equivalent (auto-packages repeated session traces into `.mimocode/agents/{name}.md`); gald3r
  `g-skl-*/SKILL.md` needs a thin frontmatter wrapper (`mode: subagent`) to adapt, not a direct
  drop-in.
- **Hooks are unverified** — inherited from OpenCode's architecture but the exact lifecycle
  events and `.mimocode/hooks.json` schema are pending confirmation; do not assume parity with
  OpenCode's hook surface until re-scanned.
- **Dual instruction files** — both `AGENTS.md` and `CLAUDE.md` are read; keep gald3r content
  consistent across both if both are present.
- **`MEMORY.md` can drift** — it is auto-maintained via `/dream`; re-assert gald3r conventions if
  they get trimmed during automatic knowledge extraction.
- **Relationship to OpenCode**: `g-skl-platform-opencode` is the architectural starting point —
  MiMo-Code gains the OpenCode parity tier plus the memory/agent/goal additions above.

## 5. Capability Summary

| Feature | Status | Notes |
|---|---|---|
| Hooks (`g-hk-*.py`) | ⚠️ | Inherited from OpenCode; lifecycle events unverified — target `.mimocode/hooks.json` pending confirmation |
| Skills (`g-skl-*/SKILL.md`) | ⚠️ | Via Compose mode + `/distill`; not a native `SKILL.md` mechanism |
| Agents (`g-agnt-*.md`) | ✅ | `.mimocode/agents/*.md` (project) or `~/.config/mimocode/agents/` (global) |
| Commands (`@g-*`) | ✅ | `/goal`, `/dream`, `/distill`, `/voice`, plus custom Compose workflows |
| Rules (`g-rl-*`) | ✅ | `AGENTS.md` + `CLAUDE.md` at project root, both read natively |
| MCP | ✅ | `mcp` key in `mimocode.json`; inherits the full OpenCode MCP layer |

Full assessment + evidence in `PLATFORM_SPEC.md`. Re-verify on the next
`@g-platform-scan-docs mimo` (crawl_max_age_days: 7) — confirm the hooks schema and
Skills/Compose auto-discovery.
