---
name: g-skl-platform-windsurf
description: Authoritative reference for Windsurf (Cascade IDE, by Cognition / Windsurf) customization in gald3r projects. Covers .windsurf/ rules/workflows/skills/hooks + ~/.codeium/windsurf MCP, AGENTS.md/.windsurfrules instruction files, .claude/.agents skill reuse, and gald3r install verification.
crawl_max_age_days: 14
vault_doc_path: research/platforms/windsurf/
vault_docs_url: https://docs.windsurf.com
docs_url: https://docs.windsurf.com
docs_url_secondary:
  - https://docs.windsurf.com/windsurf/cascade/skills
  - https://docs.windsurf.com/windsurf/cascade/hooks
  - https://docs.windsurf.com/windsurf/cascade/workflows
  - https://docs.windsurf.com/windsurf/cascade/memories
  - https://docs.windsurf.com/windsurf/cascade/mcp
last_doc_scan: 2026-06-02
capability_status:
  hooks: "✅ native Cascade Hooks (hooks.json; 12 events incl. pre_user_prompt/pre_write_code/post_setup_worktree; powershell key supported; pre-hooks block on exit 2)"
  rules: "✅ .windsurf/rules/*.md (always_on/model_decision/glob/manual, 12,000-char) + AGENTS.md + legacy .windsurfrules + global_rules.md"
  skills: "✅ Cascade Skills (SKILL.md) in .windsurf / .claude / .agents skills dirs; progressive disclosure"
  commands: "✅ Workflows (.windsurf/workflows/*.md, /[name] slash, manual-only, 12,000-char)"
  agents: "⚠️ Cascade modes + Plan Mode + planning agent + Wave 13 parallel agents (≤5); NO named sub-agent config file"
  mcp: "✅ native — ~/.codeium/windsurf/mcp_config.json + Marketplace; stdio + Streamable HTTP; 100-tool cap"
token_budget: low
subsystem_memberships: [PLATFORM_INTEGRATION]
---

# g-skl-platform-windsurf

Activate for: setting up gald3r with Windsurf (Cascade IDE), authoring rules/workflows/skills/hooks, understanding the `.windsurf/` + `~/.codeium/windsurf/` layout, or verifying the Windsurf gald3r install.

---

> Full 9-section breakdown + evidence URLs in `PLATFORM_SPEC.md` (this folder). **Status: ✅ near-full
> parity** — Cascade natively supports commands (Workflows), rules, skills, hooks, and MCP, and
> discovers `.claude/skills/` + `.agents/skills/` and reads `AGENTS.md`, so gald3r's skill artifacts
> are largely reusable. Only **agents** is partial (⚠️ — no named sub-agent file). (Verified
> 2026-06-02 against https://docs.windsurf.com.)

## 1. Platform Overview

**Windsurf** (by Cognition / Windsurf) — a VS Code-based AI-first IDE built around the **Cascade**
agentic assistant. Cascade reads Rules (incl. `AGENTS.md`) automatically, auto-invokes Skills,
runs `/`-invoked Workflows, fires lifecycle Hooks, and connects MCP servers. Cascade maintains an
auto-generated, machine-local **Memories** store (does not sync — not a gald3r surface).

## 2. Config Layout

```
<project-root>/
├── AGENTS.md                        ← read by Cascade as Rules (root = always-on; NOT CLAUDE.md)
├── .windsurfrules                   ← legacy single-file root rules (still honored)
└── .windsurf/
    ├── rules/     *.md              ← always_on | model_decision | glob | manual (12,000-char)
    ├── workflows/ *.md              ← Workflows = /slash commands (manual, 12,000-char)
    ├── skills/    <name>/SKILL.md   ← Cascade Skills (auto-invokable, progressive disclosure)
    └── hooks.json                   ← lifecycle hooks (12 events; bash + powershell keys)

~/.codeium/windsurf/                  ← user/global: global_workflows/, memories/global_rules.md,
                                        skills/, hooks.json, mcp_config.json
```

Cascade **also** discovers skills in `.claude/skills/` and `.agents/skills/` (workspace or `~/`) →
**gald3r's Claude-Code / agents skill packs work as-is on Windsurf.** Note: Windsurf reads
**`AGENTS.md`**, not `CLAUDE.md`.

## 3. gald3r Integration

**Cheapest high-parity install: ship gald3r's `.claude/skills/` tree (+ `AGENTS.md`)** — Cascade loads
it natively — then add `.windsurf/workflows/` for commands and `.windsurf/hooks.json` (with
`powershell` keys) for hooks. `g-agnt-*` personas have no native agent file; express them as
Skills/Rules.

### Verify
```powershell
Test-Path .windsurf/hooks.json       # native Cascade hooks (12 events; powershell key)
Test-Path .windsurf/workflows ; Test-Path .windsurf/skills ; Test-Path .windsurf/rules
Test-Path .claude/skills             # Cascade discovers these too
Test-Path AGENTS.md                  # instruction file (NOT CLAUDE.md)
```

## 4. Common Pitfalls

- Instruction file is **`AGENTS.md`** / `.windsurfrules`, **not** `CLAUDE.md` — Cascade ignores
  `CLAUDE.md`. Root `AGENTS.md` = always-on; subdir = auto-glob.
- **Memories** (`~/.codeium/windsurf/memories/`) are auto-generated, machine-local, and do **not**
  sync — never ship them as gald3r state; put durable context in `AGENTS.md` / `.windsurf/rules/`.
- **Workflows ≠ Skills**: Workflows are manual `/`-invoked (commands); Skills auto-invoke. Map gald3r
  commands → Workflows, gald3r skills → Skills.
- **Agents are partial**: no named sub-agent config file. Cascade has modes / Plan Mode / planning
  agent / Wave 13 parallel agents (≤5) — but `g-agnt-*` collapse to Skill/Rule content.
- Use `.md` (not Cursor's `.mdc`) for rule files — parity sync swaps the extension. MCP config path
  (`~/.codeium/windsurf/mcp_config.json`) is Windsurf-specific (not portable from `.cursor/mcp.json`).
- Hooks `pre-`events **block** on **exit code 2**; each hook supports a `powershell` key (PowerShell
  hooks fire natively); MCP has a hard **100-tool** cap.

## 5. Capability Summary

| Feature | Status | Notes |
|---|---|---|
| Hooks (`g-hk-*.ps1`) | ✅ | `hooks.json`; 12 events (pre_user_prompt/pre_write_code/pre_run_command/post_setup_worktree…); `powershell` key; pre-hooks block on exit 2 |
| Skills (`g-skl-*/SKILL.md`) | ✅ | Cascade Skills; discovered in `.windsurf` / `.claude` / `.agents` skills dirs; progressive disclosure |
| Commands (`@g-*` / `/g-*`) | ✅ | Workflows `.windsurf/workflows/*.md`, `/[name]` slash, manual-only, 12,000-char |
| Rules (`g-rl-*`) | ✅ | `.windsurf/rules/*.md` (4 activation modes, 12,000-char) + `AGENTS.md` + `.windsurfrules` + global_rules.md |
| Agents (`g-agnt-*.md`) | ⚠️ | modes + Plan Mode + planning agent + Wave 13 parallel agents (≤5); **no** named sub-agent config file |
| MCP | ✅ | `~/.codeium/windsurf/mcp_config.json` + Marketplace; stdio + Streamable HTTP; 100-tool cap |

**Windsurf-only superset**: Cascade maintains an auto-generated **Memories** store under
`~/.codeium/windsurf/memories/` that Cursor lacks — machine-local, does not sync, Cascade-managed
(not gald3r-authored).

Full assessment + evidence in `PLATFORM_SPEC.md`. Re-verify on the next `@g-platform-scan-docs windsurf` (crawl_max_age_days: 14).
