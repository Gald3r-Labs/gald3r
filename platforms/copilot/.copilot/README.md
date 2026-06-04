# GitHub Copilot — gald3r Deploy Scaffold

**Config folders**: `.github/` (Copilot-native) + `.copilot/` (gald3r convention)

This directory is the gald3r deploy scaffold for **GitHub Copilot**. It is registered in
`.gald3r_sys/_platform_capabilities.json` and recognised by the platform-parity sync tooling.

Authoritative install + customization guide: **`g-skl-platform-copilot`**
(`.gald3r_sys/skills/g-skl-platform-copilot/SKILL.md`).

See **`PLATFORM_SPEC.md`** in this directory for the verified platform capability assessment
(Phase 1 research, T1463). Phase 2 deploy-artifact adaptation: T1488.

---

## Honest Capability Status

Legend: ✅ verified working · ⚠️ partial / surface-dependent · ❌ not supported · ❓ untested.

> **Caveat**: `PLATFORM_SPEC.md` carries `last_doc_scan: never`. Ratings below are authored from
> prior Copilot knowledge and the shipped SKILL.md, NOT from a fresh `@g-platform-scan-docs copilot`
> crawl. GitHub Copilot's customization surface (especially hooks and CLI agents) moves fast.
> Treat `⚠️`/`❓` cells as provisional until a dated crawl records evidence in PLATFORM_SPEC §
> Verification Evidence.

| Feature | Location | Status | Notes |
|---------|----------|--------|-------|
| Always-apply rules | `.github/copilot-instructions.md` | ✅ | Documented, auto-loaded. Generated from gald3r always-apply rules. |
| Path-scoped rules | `.github/instructions/*.instructions.md` | ⚠️ | Copilot-only `applyTo:` glob feature. gald3r does not currently emit these (adv-tier opt-in). |
| Commands (`g-*`) | `.copilot/commands/` | ❌ | **Reference docs only.** Copilot has no `g-*` command runtime. Prompt files (below) are the nearest, manual, VS Code-only analog. |
| Skills | `.claude/skills/` | ❓ | Agent-skills concept exists, but `.claude/skills/` auto-discovery is **unverified** across surfaces (VS Code vs. cloud agent vs. CLI). Do not assume gald3r skills "just work". |
| Agents | `.github/agents/` | ⚠️ | Named, **manually-invoked** agents on the cloud/CLI surface only — NOT ambient persona auto-loading. VS Code uses chat modes instead. Schema is evolving. |
| Hooks | `.github/hooks/gald3r-hooks.json` | ⚠️ | JSON-wrapped (`"type": "command"`), cloud/CLI only, VS Code preview/absent. Fire only **during an active agent session** — NOT git hooks. New and volatile. |
| Prompt files | `.github/prompts/*.prompt.md` | ⚠️ | VS Code "/" picker, manual selection only. Not a programmable command namespace. |
| MCP | per-surface (see below) | ⚠️ | Supported, but config path differs per surface — NOT single-path portable. |

This table mirrors the PLATFORM_SPEC §9 Known Gaps and Capability Summary. Where it once read
"✅ Active" for every row, those claims were Cursor-generic and have been corrected to the
spec-verified status (T1488).

---

## The `.github/` vs `.copilot/` Split

Copilot reads **only** `.github/`. The `.copilot/` folder is a **gald3r convention** that Copilot
itself never reads — it stores command reference docs for human/agent lookup.

```
.github/                          ← Copilot-native (Copilot reads this)
├── copilot-instructions.md       ← Always-apply rules (auto-generated)        ✅
├── instructions/                 ← Path-scoped rules (applyTo: glob)          ⚠️ optional
├── prompts/                      ← Prompt files (VS Code "/" picker)          ⚠️
├── chatmodes/                    ← Custom chat modes (VS Code, newer)         ❓
├── agents/                       ← Named, manual-invoke agents (cloud/CLI)    ⚠️
└── hooks/gald3r-hooks.json       ← Lifecycle hooks JSON (cloud/CLI)           ⚠️

.copilot/                         ← gald3r convention (Copilot does NOT read)
├── README.md                     ← this file
├── PLATFORM_SPEC.md              ← Phase 1 capability assessment (T1463)
└── commands/                     ← gald3r g-* command docs (reference only)   ❌ not executed
```

**Skills note**: the prior README claimed Copilot auto-discovers `.claude/skills/` "natively — no
copy needed". Per PLATFORM_SPEC §4 that auto-discovery is **unverified** (`❓`) and surface-dependent.
Do not rely on it without an install test on your target surface.

### MCP config paths (per surface — not portable)

| Surface | MCP config location |
|---------|---------------------|
| VS Code | `<repo>/.vscode/mcp.json` (or user-level) |
| Copilot CLI | `~/.copilot/mcp-config.json` (manage with `/mcp`) |
| GitHub.com coding agent | repo/org settings (not on-disk) |

---

## Regenerating `.github/` Targets

Run after modifying rules, agents, hooks, or commands:

```powershell
.\.gald3r_sys\skills\g-skl-platform-copilot\scripts\generate_copilot_instructions.ps1
```

What it generates and the **honest** status of each output:

1. `.github/copilot-instructions.md` — from always-apply rules. ✅ works as documented.
2. `.github/agents/` — from gald3r `g-agnt-*.md`. ⚠️ named/manual-invoke, cloud/CLI surface only.
3. `.github/hooks/gald3r-hooks.json` — lifecycle hook JSON wrapper. ⚠️ cloud/CLI only, VS Code
   preview; event names + schema are volatile (see PLATFORM_SPEC §6).
4. `.github/prompts/` — from gald3r command docs. ⚠️ VS Code "/" picker, manual selection only.

> If a generated artifact does not behave as expected on your Copilot surface, that is a known gap,
> not a bug in your install — see PLATFORM_SPEC §9 and please open a GitHub issue with your surface
> (VS Code / cloud agent / CLI) and Copilot version so the rating can be updated with evidence.

---

## Feedback Loop

The PLATFORM_SPEC ratings are deliberately conservative. To promote a `❓`/`⚠️` to `✅`, record dated
evidence (a doc citation or an install test result) in PLATFORM_SPEC § Verification Evidence and
re-run `@g-platform-check`. A fresh `@g-platform-scan-docs copilot` crawl clears the
`last_doc_scan: never` caveat.
