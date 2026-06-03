---
name: g-skl-platform-roo
description: Authoritative reference for Roo Code (VS Code extension; formerly Roo Cline) customization in gald3r projects. Covers .roo/rules/, custom modes (.roomodes), slash commands, Agent Skills (.roo/skills + .agents/skills), MCP, AGENTS.md, and gald3r install verification. NOTE — Roo Code was discontinued 2026-05-15.
crawl_max_age_days: 14
vault_doc_path: research/platforms/roo/
vault_docs_url: https://docs.roocode.com
docs_url: https://docs.roocode.com
docs_url_secondary:
  - https://docs.roocode.com/features/slash-commands
  - https://docs.roocode.com/features/custom-instructions
  - https://docs.roocode.com/features/custom-modes
  - https://docs.roocode.com/features/skills
  - https://docs.roocode.com/features/mcp/using-mcp-in-roo
last_doc_scan: 2026-06-02
capability_status:
  hooks: "❌ none — Roo has no native lifecycle hook system; gald3r g-hk-*.ps1 run manually / via git core.hooksPath / VS Code tasks"
  rules: "✅ .roo/rules/ + .roo/rules-{slug}/ (recursive, alphabetical) + legacy .roorules/.clinerules fallback; workspace wins over global"
  skills: "✅ Agent Skills (SKILL.md) in .roo/skills/ + .roo/skills-{mode}/ + .agents/skills/ — auto-discovered, progressive disclosure"
  commands: "✅ slash commands .roo/commands/*.md (filename=command; run_slash_command tool; optional mode frontmatter)"
  agents: "✅ modes are the agent analog — built-in + custom modes in .roomodes (slug/roleDefinition/groups/whenToUse; Orchestrator/boomerang)"
  mcp: "✅ native — project .roo/mcp.json (precedence over global) + use_mcp_tool/access_mcp_resource; STDIO + SSE/HTTP"
token_budget: low
subsystem_memberships: [PLATFORM_INTEGRATION]
---

# g-skl-platform-roo

Activate for: setting up gald3r with Roo Code, authoring `.roo/rules/` / `.roomodes` / `.roo/skills/`
/ `.roo/commands/`, understanding Roo's mode system, or verifying the Roo gald3r install.

---

> Full 9-section breakdown + evidence URLs in `PLATFORM_SPEC.md` (this folder). **Status: ⚠️ near-full
> parity but DISCONTINUED** — Roo natively supports commands, rules, modes (agents), skills, and MCP
> (only **hooks** are missing), and reads `AGENTS.md` + the `.roo/` tree. **BUT Roo Code was shut down
> 2026-05-15** (migrate to Cline / Kilo Code); the tool is frozen/archived. (Verified 2026-06-02
> against https://docs.roocode.com.)

## 1. Platform Overview

**Roo Code** (formerly Roo Cline) — an open-source agentic coding **VS Code extension** forked from
Cline, with custom AI **modes** (Code, Architect, Debug, Ask, Orchestrator), boomerang task
orchestration, project slash commands, Agent Skills, and first-class MCP. Five of six gald3r
mechanisms are native; only lifecycle hooks are absent.

- **Modes**: built-in + custom modes in `.roomodes` — the agent/sub-agent analog; each can have
  separate rules
- **Rules (modern)**: `.roo/rules/` (all modes) + `.roo/rules-{slug}/` (per-mode) — directories, read
  recursively & alphabetically
- **Rules (legacy fallback)**: `.roorules` / `.roorules-{slug}`; `.clinerules` also read
- **Skills**: `SKILL.md` packages in `.roo/skills/` + `.roo/skills-{mode}/` + `.agents/skills/` —
  auto-discovered, progressive disclosure
- **Commands**: `.roo/commands/*.md` slash commands (filename = command name) + `run_slash_command`
- **MCP**: project `.roo/mcp.json` (team-shareable, precedence over global)
- **AGENTS.md**: auto-loaded from repo root (unless `roo-cline.useAgentRules:false`) — **not**
  `CLAUDE.md`
- **Hooks**: ❌ none — no native lifecycle hook system

> **⚠️ DISCONTINUED (2026-05-15):** Roo Code (extension, Cloud, Router) was officially shut down;
> docs/repos are archived and the extension still runs, but it is unmaintained. Treat any gald3r
> `roo` target as **legacy**. See `PLATFORM_SPEC.md` for the full 9-section spec.

## 2. Config Layout

```
<project-root>/
├── AGENTS.md                ← auto-loaded agent rules (unless roo-cline.useAgentRules:false)
├── .roomodes                ← custom mode definitions (YAML preferred; JSON accepted)
├── .rooignore               ← gitignore-style agent file-access control
└── .roo/
    ├── rules/        *.md    ← general rules, ALL modes (recursive, alphabetical)
    ├── rules-{slug}/ *.md    ← mode-specific rules (rules-code/, rules-architect/)
    ├── commands/     *.md    ← project slash commands (filename = command name)
    ├── skills/   <name>/SKILL.md   ← Agent Skills (progressive disclosure)
    └── mcp.json             ← project-level MCP server config (team-shareable)
  ── cross-agent + legacy fallbacks ──
├── .agents/skills/ <name>/SKILL.md  ← cross-agent Skills path
├── .roorules                ← general rules fallback (≈ .roo/rules/)
└── .clinerules              ← Cline-compatibility fallback (Roo reads it)
```

**Format**: plain `.md` (NOT Cursor's `.mdc` — parity sync swaps the extension).
**Precedence**: directory form (`.roo/rules/`) over single-file legacy; **project (`.roo/`) over
global (`~/.roo/`)** — workspace wins on conflict.

## 3. gald3r Integration

**High-parity install: ship `AGENTS.md` + the `.roo/` tree** (`rules/`, `skills/`, `commands/`,
`mcp.json`) **+ `.roomodes`** — Roo discovers all of them natively. gald3r `g-skl-*/SKILL.md` load via
`.roo/skills/` (auto-relevance honored); `g-agnt-*` personas become `.roomodes` custom modes;
`g-rl-*` map to `.roo/rules/`; `@g-*` commands become `.roo/commands/g-*.md`.

### Mode-Specific Rules
For Architect mode (planning/design), add gald3r architecture context in `.roo/rules-architect/`:
```markdown
Always read .gald3r/PLAN.md and .gald3r/CONSTRAINTS.md before architecture decisions.
Subsystem changes require reading .gald3r/subsystems/{name}.md.
```

### Verify
```powershell
Test-Path AGENTS.md
Test-Path .roo/rules ; Test-Path .roo/skills ; Test-Path .roo/commands ; Test-Path .roo/mcp.json
Test-Path .roomodes
```

## 4. Common Pitfalls

- **DISCONTINUED** — Roo Code shut down 2026-05-15; the platform is frozen. Prefer Cline / Kilo Code
  for active work; only target `roo` for legacy installs.
- **Hooks don't exist** — gald3r `g-hk-*.ps1` cannot auto-fire. Use git `core.hooksPath` for
  commit/push gates; express the rest as rule text, custom modes, or VS Code tasks. Experimental
  Custom Tools are **model-invoked tools, not deterministic hooks**.
- Modern Roo prefers the **directory** rules form over single-file `.roorules`; dir form wins when
  both exist. Within a dir, files load **recursively and alphabetically** — name files to order them.
  Mode-specific rules (`.roo/rules-{slug}/`) appear **before** general rules.
- `AGENTS.md` is auto-loaded unless `roo-cline.useAgentRules:false` — don't duplicate rules content
  between `AGENTS.md` and `.roo/rules/`.
- Agents are **modes** (`.roomodes`), not files — there is no `agents/` folder.
- `docs.roocode.com` 301-redirects to `roocodeinc.github.io/Roo-Code/`.

## 5. Capability Summary

| Feature | Status | Notes |
|---|---|---|
| Hooks (`g-hk-*.ps1`) | ❌ | no native lifecycle hook system; run via git `core.hooksPath` / VS Code tasks. Custom Tools are model-invoked, not hooks |
| Skills (`g-skl-*/SKILL.md`) | ✅ | Agent Skills in `.roo/skills/` + `.roo/skills-{mode}/` + `.agents/skills/`; auto-discovered, progressive disclosure |
| Agents (`g-agnt-*`) | ✅ | modes are the analog — built-in + custom modes in `.roomodes` (slug/roleDefinition/groups/whenToUse; Orchestrator/boomerang) |
| Commands (`@g-*`) | ✅ | `.roo/commands/*.md` (filename = command); `run_slash_command` tool; optional `mode` frontmatter |
| Rules (`g-rl-*`) | ✅ | `.roo/rules/` + `.roo/rules-{slug}/` (recursive, alphabetical); `.roorules`/`.clinerules` fallback; workspace wins |
| MCP | ✅ | project `.roo/mcp.json` (precedence over global); `use_mcp_tool`/`access_mcp_resource`; STDIO + SSE/HTTP |

Full assessment + evidence in `PLATFORM_SPEC.md`. Re-verify on the next `@g-platform-scan-docs roo`
(crawl_max_age_days: 14) — but note the platform is discontinued, so docs are unlikely to change.
