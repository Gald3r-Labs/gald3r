---
name: g-skl-platform-opencode
description: Authoritative reference for OpenCode (sst/opencode) customization in gald3r projects. Covers .opencode/ folder layout, opencode.json config, native skills discovery (.opencode/skills/ + .claude/skills/), AGENTS.md/CLAUDE.md instructions, JS/TS plugin hooks, MCP, and install verification.
crawl_max_age_days: 7
vault_doc_path: research/platforms/opencode/
docs_url: https://opencode.ai/docs
vault_docs_url: https://opencode.ai/docs
capability_status:
  hooks: ⚠️    # native plugin (JS/TS) hooks exist; gald3r .ps1 hooks not portable without a shim
  rules: ⚠️    # content via AGENTS.md/CLAUDE.md; no .mdc glob-scoped rule engine
  skills: ⚠️   # native skills + .claude/skills/ reuse (doc-verified, not install-tested)
  commands: ⚠️ # .opencode/commands/ exists; gald3r command execution parity untested
  mcp: ⚠️      # opencode.json mcp block (doc-verified, not install-tested)
last_doc_scan: 2026-05-26
token_budget: low
subsystem_memberships: [PLATFORM_INTEGRATION]
---

# g-skl-platform-opencode

Activate for: setting up OpenCode in a gald3r project, authoring `.opencode/` configs, understanding opencode.json, verifying OpenCode parity, or answering questions about OpenCode's capabilities.

---

## Crawl Freshness Gate

```
1. Read {vault_location}/.crawl_schedule.json
2. Find entry for: https://opencode.ai/docs
3. If entry missing OR (today - last_crawl) > 7 days:
   → TRIGGER g-skl-recon-docs with URL https://opencode.ai/docs
   → READ new vault notes at research/platforms/opencode/
   → UPDATE sections: "Platform Overview", "Supported Primitives", "Common Pitfalls"
4. Else: proceed with current content
```

---

## 1. Platform Overview

**OpenCode** (`opencode` command) is an open-source AI coding agent from [sst.dev](https://sst.dev). It runs as a TUI (terminal UI) with multi-provider support.

- **Multi-provider**: Claude, GPT-4o, Gemini, DeepSeek, local Ollama (configurable in `opencode.json`)
- **TUI interface**: Rich terminal UI with file tree, diff views, conversation history
- **Config file**: `opencode.json` / `opencode.jsonc` at project root (global: `~/.config/opencode/opencode.json`)
- **Native skills**: discovered from `.opencode/skills/`, `.claude/skills/`, and `.agents/skills/` (verified via https://opencode.ai/docs/skills)
- **Instructions**: `AGENTS.md` (root + `~/.config/opencode/AGENTS.md`); falls back to `CLAUDE.md`/`~/.claude/CLAUDE.md`. The `opencode.json` `instructions` array references *additional* instruction files (NOT a glob into `.cursor/rules/*.mdc`)
- **Native hooks**: yes — via the **plugins** system (JS/TS in `.opencode/plugins/`). NOT a JSON `hooks.json`, and NOT PowerShell — so gald3r `.ps1` hooks are not portable without a shim

**gald3r target**: skills and rules content reach OpenCode via `.claude/skills/` and `CLAUDE.md`/`AGENTS.md`; agents/commands map to `.opencode/`. See `PLATFORM_SPEC.md` (this folder) for the full 9-section capability assessment.

> **Doc-scan basis (2026-05-26)**: capability claims below are verified against https://opencode.ai/docs
> but NOT install-tested in this repo (no `.opencode/` or `opencode.json` present). Status is ⚠️
> partial accordingly. See the Known Gaps section.

---

## 2. Folder Layout

```
opencode.json                 ← Root config (NOT in .opencode/); opencode.jsonc also accepted
.opencode/                    ← OpenCode config dir (plural subdir names; singular tolerated)
├── agents/                   ← Agent definitions (g-agnt-*.md)
├── commands/                 ← /g-* command reference (g-*.md)
├── skills/                   ← Native skills (folder-per-skill SKILL.md) — optional; .claude/skills/ also read
└── plugins/                  ← JS/TS plugins == OpenCode's hook system (gald3r does not emit these yet)
```

**Skills**: OpenCode discovers skills from `.opencode/skills/`, `.claude/skills/`, AND `.agents/skills/`
(verified). gald3r skills are reachable via the shared `.claude/skills/` path — no mandatory copy into
`.opencode/skills/`. Skill `name` must be 1–64 lowercase alphanumeric with single hyphens (`g-skl-*` is fine).

**Rules / instructions**: OpenCode reads `AGENTS.md` (root) and falls back to `CLAUDE.md`. The
`opencode.json` `instructions` array references *additional* plain instruction files — it is NOT a
glob into `.cursor/rules/*.mdc`:
```json
{
  "instructions": ["AGENTS.md", "docs/guidelines.md"]
}
```
There is no `.mdc` glob-scoped rule engine on OpenCode; gald3r `g-rl-*` content must consolidate into
`AGENTS.md`/`CLAUDE.md` (glob scoping is lost).

---

## 3. Supported Primitives

| Primitive | Location | Format | Status |
|---|---|---|---|
| Rules / instructions | `AGENTS.md` / `CLAUDE.md` (+ `instructions` array) | Markdown | ⚠️ Content carries; no glob scoping |
| Skills | `.opencode/skills/` or `.claude/skills/<name>/SKILL.md` | Markdown (`name`+`description` frontmatter) | ⚠️ Native + `.claude/` reuse (doc-verified) |
| Agents | `.opencode/agents/g-agnt-*.md` (or `agent` field) | Markdown | ⚠️ Native concept; frontmatter shim may be needed |
| Commands | `.opencode/commands/g-*.md` (or `command` field) | Markdown | ⚠️ Native; gald3r execution parity untested |
| MCP servers | `opencode.json` → `mcp` block | JSON | ⚠️ Doc-verified; live server untested |
| Hooks | `.opencode/plugins/*.{js,ts}` (plugin callbacks) | JS/TS | ⚠️ Native plugin hooks; gald3r `.ps1` not portable |

### opencode.json Structure

```json
{
  "model": "anthropic/claude-sonnet-4-5",
  "instructions": ["AGENTS.md", "docs/guidelines.md"],
  "mcp": {
    "gald3r": {
      "type": "remote",
      "url": "http://localhost:8092/mcp"
    }
  }
}
```

Config supports `{env:VAR}` and `{file:path}` substitution for secrets. `opencode.jsonc` (comments)
is also accepted; a global config lives at `~/.config/opencode/opencode.json`.

---

## 4. gald3r Parity Tier

| Content | Slim | Full | Adv |
|---|---|---|---|
| agents/ | ✅ | ✅ | ✅ |
| commands/ | ✅ | ✅ | ✅ |
| opencode.json | ✅ | ✅ | ✅ |
| Skills (via .claude/skills/) | ✅ | ✅ | ✅ |
| Rules (via AGENTS.md / CLAUDE.md instructions) | ⚠️ | ⚠️ | ⚠️ |

---

## 5. Vault Doc Location

```
{vault_location}/research/platforms/opencode/
```

---

## 6–7. Crawl Freshness Gate & Self-Update

See gate template in header. Update sections 1, 3, 9 after fresh crawl.

---

## 8. Key URLs

| Purpose | URL |
|---|---|
| OpenCode website | https://opencode.ai |
| OpenCode docs | https://opencode.ai/docs |
| OpenCode GitHub | https://github.com/sst/opencode |
| Configuration reference | https://opencode.ai/docs/config |

---

## 9. Common Pitfalls

1. **`opencode.json` is at project root** — Not inside `.opencode/`. Placing it in `.opencode/opencode.json` won't be found.
2. **`instructions` is NOT a `.mdc` glob** — A prior version of this skill claimed `instructions: [".cursor/rules/*.mdc"]`. That is **wrong**. OpenCode rules come from `AGENTS.md`/`CLAUDE.md`; `instructions` references additional plain instruction files (and remote URLs). gald3r `g-rl-*` content must be consolidated into `AGENTS.md`/`CLAUDE.md` — per-rule glob scoping does not exist on OpenCode.
3. **Skills are native AND read from `.claude/skills/`** — OpenCode discovers `.opencode/skills/`, `.claude/skills/`, and `.agents/skills/`. The shared `.claude/skills/` path is the zero-copy route for gald3r skills.
4. **`.cursor/skills/` is NOT discovered** — OpenCode does not read `.cursor/skills/`. Keep skills in `.claude/skills/` (or `.opencode/skills/`).
5. **Hooks exist but are JS/TS plugins** — OpenCode has a native hook system via `.opencode/plugins/` (JavaScript/TypeScript), with events like `tool.execute.before`, `session.created`, `file.edited`. It is NOT a `hooks.json` and NOT PowerShell — so gald3r's `g-hk-*.ps1` hooks do not run without a JS/TS plugin shim that shells out to them.
6. **Model selection**: `model` field uses `provider/model` IDs (e.g. `anthropic/claude-sonnet-4-5`), not a bare `claude`.

---

## 10. Install Verification Checklist

```
✅ opencode.json exists at project root
✅ AGENTS.md (or CLAUDE.md) at project root carries the gald3r instructions (NOT .cursor/rules/*.mdc glob — see Known Gaps #2)
✅ .opencode/agents/ has g-agnt-*.md files
✅ .opencode/commands/ has g-*.md command files
✅ .claude/skills/ has gald3r core skills (OpenCode reads from here)
✅ opencode --version runs without error
✅ Provider API key set in environment (ANTHROPIC_API_KEY, OPENAI_API_KEY, etc.)
```

---

## 11. Known Gaps (vs. Cursor reference)

Honest status — see `PLATFORM_SPEC.md` §9 (this folder) for the full assessment. Doc-verified
against https://opencode.ai/docs on 2026-05-26; NOT install-tested in this repo.

1. **Hooks (⚠️/❌)** — gald3r ships PowerShell `g-hk-*.ps1` hooks wired through Cursor's
   `hooks.json`. OpenCode's native hooks are JS/TS plugins (`.opencode/plugins/`). gald3r hooks do
   NOT run on OpenCode without a JS/TS shim invoking the `.ps1` scripts via the plugin Bun shell API.
2. **Rules glob scoping (⚠️)** — no `.mdc` rule engine; gald3r's per-rule `globs:`/`alwaysApply:`
   selectivity collapses into one always-on `AGENTS.md`/`CLAUDE.md` document.
3. **Command execution parity (⚠️)** — `.opencode/commands/` exists, but gald3r `@g-*` command
   execution semantics and slash invocation were not install-verified.
4. **Agent frontmatter shim (⚠️)** — OpenCode has its own agent/mode schema; `g-agnt-*.md`
   frontmatter compatibility is untested.
5. **No live install verification (❓)** — no `.opencode/` or `opencode.json` in this repo; all
   doc-derived ✅ claims await an `opencode --version` + load test. Flip ⚠️→✅ after that run.
