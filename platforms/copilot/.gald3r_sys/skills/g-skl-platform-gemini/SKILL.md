---
name: g-skl-platform-gemini
description: Authoritative reference for Gemini CLI (Google) customization in gald3r projects. Covers .gemini/ native config, GEMINI.md memory, the gald3r .agent/ install tree, custom TOML commands, MCP, and install verification.
docs_url: https://github.com/google-gemini/gemini-cli
crawl_max_age_days: 7
vault_doc_path: research/platforms/gemini/
vault_docs_url: https://github.com/google-gemini/gemini-cli
token_budget: low
capability_status:
  hooks: ❌      # no native hook/event system
  rules: ⚠️     # only via GEMINI.md memory; no folder-based always-apply
  skills: ❌     # no native skills discovery (instruction-file reference only)
  commands: ⚠️  # native TOML slash commands exist, but gald3r g-* are .md, not executable
  mcp: ✅        # first-class mcpServers in .gemini/settings.json (mechanism doc-verified)
subsystem_memberships: [PLATFORM_INTEGRATION]
---

# g-skl-platform-gemini

Activate for: setting up Gemini CLI in a gald3r project, authoring `.agent/` configs, verifying Gemini parity, or answering questions about Gemini CLI's capabilities.

> **⚠️ EOL / migration notice (T1512, 2026-05-27):** Google is **replacing Gemini CLI with the
> Antigravity CLI (`agy`)**. The `gemini` binary **stops serving** Google AI Pro/Ultra/free-tier
> requests on **2026-06-18** (paid Code Assist Standard/Enterprise + API keys keep working); the
> `google-gemini/gemini-cli` repo is **not archived** (still Apache-2.0). This skill remains correct
> for the **legacy** Gemini CLI. For the successor — which **adds** Agent Skills, JSON lifecycle
> hooks, and dynamic subagents (closing Gemini's old ❌ gaps) — see **`g-skl-platform-antigravity`**
> and the migration note in `platforms/.gemini/PLATFORM_SPEC.md`. **Decision (T1512): keep the
> `gemini` platform key as legacy; new Antigravity work lives under the `antigravity` key.**

---

## Crawl Freshness Gate

```
1. Read {vault_location}/.crawl_schedule.json
2. Find entry for: https://github.com/google-gemini/gemini-cli
3. If entry missing OR (today - last_crawl) > 7 days:
   → TRIGGER g-skl-recon-docs with URL https://github.com/google-gemini/gemini-cli
   → READ new vault notes at research/platforms/gemini/
   → UPDATE sections: "Platform Overview", "Supported Primitives", "Common Pitfalls"
4. Else: proceed with current content
```

---

## 1. Platform Overview

**Gemini CLI** (`gemini` command, `google-gemini/gemini-cli`, Apache-2.0) is Google's open-source
terminal coding agent. It is an **instruction-file (`GEMINI.md`) + JSON-settings (`.gemini/
settings.json`)** platform — NOT a rules/skills/hooks platform like Cursor.

- **Model-swappable** via config (Gemini family); **free tier** available with a Gemini API key
- **Memory**: hierarchical **`GEMINI.md`** context files (`/memory show` / `/memory refresh`)
- **Custom commands**: native **TOML** files in `.gemini/commands/*.toml` (`/name` or `/dir:name`)
- **Extensions**: `gemini extensions` — tool bundles (the nearest native analogue to skills)
- **MCP**: first-class, via an **`mcpServers`** block in `.gemini/settings.json` (built-in `/mcp`)
- **No native rules folder, no skills system, no agent files, no hook/event system**

**gald3r target**: *portable* parity with Cursor, NOT native parity. gald3r installs its tree into
the `.agent/` folder, but Gemini CLI only natively reads **`GEMINI.md`** and **`.gemini/`**. The
`.agent/` content (rules/skills/agents/commands as `.md`) is surfaced to Gemini only by being
**referenced from `GEMINI.md`** — Gemini does not auto-discover `.agent/`. See **Known Gaps** below
and `PLATFORM_SPEC.md` for the full honest assessment. (gald3r uses `.agent/` as canonical; Gemini
also reads `.agents/` in some docs — do not create both.)

---

## 2. Folder Layout

```
.agent/                       ← Gemini CLI config (gald3r canonical name)
├── GEMINI.md                 ← Project-level always-apply instructions
├── rules/                    ← Always-apply rules (.md format)
│   └── g-rl-*.md
├── skills/                   ← Agent skills (auto-discovered)
│   └── g-skl-*/SKILL.md
├── agents/                   ← Agent definitions
│   └── g-agnt-*.md
└── commands/                 ← /g-* commands
    └── g-*.md
```

**Note**: Gemini reads both `.agent/` and `.agents/` — gald3r uses `.agent/` for consistency.

---

## 3. Supported Primitives

| Primitive | Location | Format | Native? |
|---|---|---|---|
| Memory / context | `GEMINI.md` (root + `.gemini/` + nested) | Markdown | ✅ Native, hierarchical |
| Custom commands | `.gemini/commands/<name>.toml` | **TOML** | ✅ Native (`/name`, `/dir:name`) |
| MCP servers | `.gemini/settings.json` → `mcpServers` | JSON | ✅ Native auto-connect (`/mcp`) |
| Extensions | `gemini extensions` | bundle | ✅ Native (nearest analogue to skills) |
| gald3r rules | `.agent/rules/g-rl-*.md` | Markdown | ⚠️ NOT auto-loaded — only via `GEMINI.md` reference |
| gald3r skills | `.agent/skills/<name>/SKILL.md` | Markdown | ❌ No native skills discovery — instruction reference only |
| gald3r agents | `.agent/agents/g-agnt-*.md` | Markdown | ❌ No native agent system — conversational reference only |
| gald3r commands | `.agent/commands/g-*.md` | Markdown | ⚠️ NOT `.toml` → not executable as Gemini slash commands |
| Hooks | (none) | n/a | ❌ No hook/event system — automation is manual |

---

## 4. gald3r Parity Tier

| Content | Slim | Full | Adv |
|---|---|---|---|
| rules/ (8 always-apply) | ✅ | ✅ | ✅ |
| skills/ | ✅ | ✅ | ✅ |
| agents/ | ✅ | ✅ | ✅ |
| commands/ | ✅ | ✅ | ✅ |
| GEMINI.md | ✅ | ✅ | ✅ |

---

## 5. Vault Doc Location

```
{vault_location}/research/platforms/gemini/
```

---

## 6–7. Crawl Freshness Gate & Self-Update

See gate template in header. Update sections 1, 3, 9 after fresh crawl.

---

## 8. Key URLs

| Purpose | URL |
|---|---|
| Gemini CLI repo | https://github.com/google-gemini/gemini-cli |
| Configuration (settings.json, GEMINI.md) | https://github.com/google-gemini/gemini-cli/blob/main/docs/cli/configuration.md |
| Custom commands (TOML) | https://github.com/google-gemini/gemini-cli/blob/main/docs/cli/commands.md |
| MCP server config | https://github.com/google-gemini/gemini-cli/blob/main/docs/tools/mcp-server.md |
| Extensions guide | https://github.com/google-gemini/gemini-cli/blob/main/docs/extensions.md |

---

## 8a. Known Gaps (vs. Cursor reference)

Gemini CLI provides **portable**, not **native**, gald3r parity. See `PLATFORM_SPEC.md` §9 for the
full assessment. The features below do **not** work the way they do on Cursor:

1. **Hooks ❌** — no native hook/event system (no `sessionStart`/`stop`/`preToolUse`/
   `beforeShellExecution`). PCAC inbox check, session-start context injection, and
   pre-commit/pre-push gates have **no automatic firing surface**; run scripts manually.
2. **Rules ⚠️** — `.agent/rules/g-rl-*.md` is **not auto-loaded**. Always-apply behavior must be
   inlined or linked from `GEMINI.md`. No `alwaysApply:` / `globs:` semantics.
3. **Skills ❌** — no native skills discovery. `SKILL.md` folders are reachable only via
   `GEMINI.md` references. Gemini's native analogues are **extensions** and **custom commands**.
4. **Agents ❌** — no native agent-file system. `g-agnt-*.md` works only as conversational
   instruction references ("act as @g-agnt-…").
5. **Commands ⚠️** — Gemini's native custom commands are **TOML** in `.gemini/commands/`
   (`/name`, `/dir:name`). gald3r ships `.md` under `.agent/commands/g-*.md`, which are **not
   executable** as slash commands; no TOML emitter exists yet.
6. **`.gemini/` vs `.agent/` split** — the only files Gemini reads natively are `GEMINI.md` and
   `.gemini/`. The whole `.agent/` tree is portability scaffolding.
7. **SCAN_DOCS not yet run ❓** — `last_doc_scan: never`. Confirm exact `settings.json` keys,
   built-in slash-command list, and extension API via `@g-platform-scan-docs gemini`.

---

## 9. Common Pitfalls

1. **`.agent/` vs `.agents/`** — gald3r uses `.agent/` but Gemini reads both. Do not create both; `.agent/` is canonical.
2. **No native hooks** — Gemini has no hooks.json equivalent. Session automation must be done via rules/memory or external scripts.
3. **API key required** — `GEMINI_API_KEY` environment variable. Free tier has rate limits. Set in `.env` or system environment.
4. **Memory via GEMINI.md** — Gemini's "memory" feature appends to `GEMINI.md`. Be careful not to let gald3r rules be overwritten by Gemini's memory injections.
5. **Checkpointing** — `gemini --checkpoint` saves session state. Useful for long tasks; restart from checkpoint with `--resume`.

---

## 10. Install Verification Checklist

```
✅ GEMINI.md exists at project root (the ONLY file Gemini reads natively)
✅ GEMINI.md references the .agent/ rules/skills/agents so they reach context
✅ .agent/rules/ has g-rl-*.md files        (present; NOT auto-loaded — see Known Gaps)
✅ .agent/skills/ has gald3r core skills    (present; NOT auto-loaded)
✅ .agent/agents/ has g-agnt-*.md files     (present; NOT auto-loaded)
✅ .agent/commands/ has g-*.md files        (present; NOT executable slash commands)
✅ .gemini/settings.json has mcpServers (if MCP used) — verify with /mcp
✅ gemini --version runs without error
✅ GEMINI_API_KEY is set in environment (free tier has rate limits)
```

> Honesty: the `.agent/` checks confirm files were **installed**, not that Gemini **loads** them.
> Native loading is `GEMINI.md` + `.gemini/` only — see **Known Gaps** and `PLATFORM_SPEC.md`.
