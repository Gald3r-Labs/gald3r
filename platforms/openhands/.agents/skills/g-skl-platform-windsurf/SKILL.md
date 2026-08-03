---
name: g-skl-platform-windsurf
description: Authoritative reference for Devin Desktop (formerly Windsurf — Cognition renamed the product 2026-06-02 after acquiring it; Cascade IDE) customization in gald3r projects. Covers .windsurf/ rules/workflows/skills/hooks + ~/.codeium/windsurf MCP, AGENTS.md/.windsurfrules instruction files, .claude/.agents skill reuse, and gald3r install verification.
crawl_max_age_days: 14
vault_doc_path: research/platforms/windsurf/
vault_docs_url: https://docs.devin.ai/desktop/getting-started
docs_url: https://docs.devin.ai/desktop/getting-started
docs_url_secondary:
  - https://docs.devin.ai/desktop/cascade/skills
  - https://docs.devin.ai/desktop/cascade/hooks
  - https://docs.devin.ai/desktop/cascade/workflows
  - https://docs.devin.ai/desktop/cascade/memories
  - https://docs.devin.ai/desktop/cascade/mcp
  - https://docs.devin.ai/desktop/devin-desktop-faq
last_doc_scan: 2026-07-18
capability_status:
  hooks: "✅ native Cascade Hooks (hooks.json; 12 events incl. pre_user_prompt/pre_write_code/post_setup_worktree; powershell key supported; pre-hooks block on exit 2)"
  rules: "✅ .windsurf/rules/*.md (always_on/model_decision/glob/manual, 12,000-char) + AGENTS.md + legacy .windsurfrules + global_rules.md"
  skills: "✅ Cascade Skills (SKILL.md) in .windsurf / .claude / .agents skills dirs; progressive disclosure"
  commands: "✅ Workflows (.windsurf/workflows/*.md, /[name] slash, manual-only, 12,000-char)"
  agents: "⚠️ Cascade modes + Plan Mode + planning agent + Wave 13 parallel agents (≤5); NO named sub-agent config file"
  mcp: "✅ native — ~/.codeium/windsurf/mcp_config.json (Devin Desktop path unchanged post-rename, re-verified 2026-07-18) + Marketplace; stdio + Streamable HTTP; 100-tool cap"
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

# g-skl-platform-windsurf

> **Rename note (verified 2026-07-18):** Cognition acquired Windsurf and renamed the standalone IDE
> **Devin Desktop** effective 2026-06-02. `windsurf.com` now redirects to `devin.ai/desktop` and
> `docs.windsurf.com` redirects (two 308 hops) to `https://docs.devin.ai/desktop/getting-started`.
> The internal gald3r platform id stays **`windsurf`** (registry/roster stability — see
> `PLATFORM_SPEC.md` for the full citation trail) and the on-disk `.windsurf/` project folder,
> `~/.codeium/windsurf/` user folder, and `.windsurfrules` filename are all **unchanged** — Cognition
> kept the technical namespace even though the product's display name changed.

Activate for: setting up gald3r with Devin Desktop (formerly Windsurf; Cascade IDE), authoring
rules/workflows/skills/hooks, understanding the `.windsurf/` + `~/.codeium/windsurf/` layout, or
verifying the Devin Desktop gald3r install.

---

> Full 9-section breakdown + evidence URLs in `PLATFORM_SPEC.md` (this folder). **Status: ✅ near-full
> parity** — Cascade natively supports commands (Workflows), rules, skills, hooks, and MCP, and
> discovers `.claude/skills/` + `.agents/skills/` and reads `AGENTS.md`, so gald3r's skill artifacts
> are largely reusable. Only **agents** is partial (⚠️ — no named sub-agent file). (Verified
> 2026-07-18 against https://docs.devin.ai — the current live docs.windsurf.com redirect target.)

## 1. Platform Overview

**Devin Desktop** (formerly **Windsurf**, by Cognition — renamed 2026-06-02) — a VS Code-based
AI-first IDE built around the **Cascade** agentic assistant. Cascade reads Rules (incl.
`AGENTS.md`) automatically, auto-invokes Skills, runs `/`-invoked Workflows, fires lifecycle Hooks,
and connects MCP servers. Cascade maintains an auto-generated, machine-local **Memories** store
(does not sync — not a gald3r surface).

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
**gald3r's Claude-Code / agents skill packs work as-is on Devin Desktop.** Note: Devin Desktop reads
**`AGENTS.md`**, not `CLAUDE.md`.

## 3. gald3r Integration

**Cheapest high-parity install: ship gald3r's `.claude/skills/` tree (+ `AGENTS.md`)** — Cascade loads
it natively — then add `.windsurf/workflows/` for commands and `.windsurf/hooks.json` (gald3r
`g-hk-*.py` hooks wire via the `bash` key running `python <path>`) for hooks. `g-agnt-*` personas
have no native agent file; express them as Skills/Rules.

### Verify
```powershell
Test-Path .windsurf/hooks.json       # native Cascade hooks (12 events; bash key runs python <path>)
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
  (`~/.codeium/windsurf/mcp_config.json`) is Devin Desktop-specific (not portable from
  `.cursor/mcp.json`), and unlike the *JetBrains* Windsurf Plugin (which flattened to
  `~/.codeium/mcp_config.json`), the Desktop app kept the `/windsurf/` subdirectory — see
  `PLATFORM_SPEC.md` §8 for the citation and a noted doc inconsistency worth re-checking.
- Hooks `pre-`events **block** on **exit code 2**; each hook supports a `powershell` key (PowerShell
  hooks fire natively); MCP has a hard **100-tool** cap.

## 5. Capability Summary

| Feature | Status | Notes |
|---|---|---|
| Hooks (`g-hk-*.py`) | ✅ | `hooks.json`; 12 events (pre_user_prompt/pre_write_code/pre_run_command/post_setup_worktree…); `bash` key running `python <path>`; pre-hooks block on exit 2 |
| Skills (`g-skl-*/SKILL.md`) | ✅ | Cascade Skills; discovered in `.windsurf` / `.claude` / `.agents` skills dirs; progressive disclosure |
| Commands (`@g-*` / `/g-*`) | ✅ | Workflows `.windsurf/workflows/*.md`, `/[name]` slash, manual-only, 12,000-char |
| Rules (`g-rl-*`) | ✅ | `.windsurf/rules/*.md` (4 activation modes, 12,000-char) + `AGENTS.md` + `.windsurfrules` + global_rules.md |
| Agents (`g-agnt-*.md`) | ⚠️ | modes + Plan Mode + planning agent + Wave 13 parallel agents (≤5); **no** named sub-agent config file |
| MCP | ✅ | `~/.codeium/windsurf/mcp_config.json` (Devin Desktop; unchanged post-rename) + Marketplace; stdio + Streamable HTTP; 100-tool cap |

**Devin Desktop-only superset** (formerly "Windsurf-only"): Cascade maintains an auto-generated
**Memories** store under `~/.codeium/windsurf/memories/` that Cursor lacks — machine-local, does
not sync, Cascade-managed (not gald3r-authored).

Full assessment + evidence in `PLATFORM_SPEC.md`. Re-verify on the next `@g-platform-scan-docs windsurf` (crawl_max_age_days: 14).
