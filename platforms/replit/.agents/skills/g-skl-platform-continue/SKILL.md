---
name: g-skl-platform-continue
description: Authoritative reference for Continue.dev (open-source VS Code / JetBrains extension) customization in gald3r projects. Covers .continue/ rules/prompts/agents/skills/mcpServers, the corrected commands path (.continue/prompts, NOT .continue/commands), the absence of a native AGENTS.md read, the absent hook surface, and gald3r install verification.
crawl_max_age_days: 14
vault_doc_path: research/platforms/continue/
vault_docs_url: https://docs.continue.dev
docs_url: https://docs.continue.dev
docs_url_secondary:
  - https://docs.continue.dev/customize/overview
  - https://docs.continue.dev/customize/deep-dives/prompts
  - https://docs.continue.dev/customize/deep-dives/rules
  - https://docs.continue.dev/customize/deep-dives/mcp
  - https://docs.continue.dev/customize/deep-dives/agents
last_doc_scan: 2026-07-18
capability_status:
  hooks: "❌ no lifecycle-hook/event-bus documentation found; do not fabricate a hook config surface"
  rules: "✅ native — .continue/rules/*.md, loaded automatically, lexicographic order; NOT AGENTS.md"
  skills: "⚠️ third-party marketplaces document .continue/skills/ / ~/.continue/skills/; Continue's own tracker has an OPEN 'plans to support skills?' issue (#9216) — native first-party support unconfirmed"
  commands: "✅ native — Prompt files .continue/prompts/*.md (invokable: true), invoked /<name>; CORRECTED from .continue/commands/ (T386)"
  agents: "✅ native — .continue/agents/*.md, Markdown + YAML frontmatter, one file per custom sub-agent"
  mcp: "✅ native — .continue/mcpServers/<name>-mcp.yaml, or a plain JSON file auto-recognized in the same folder, or inline mcpServers: in config.yaml"
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

# g-skl-platform-continue

Activate for: setting up gald3r with Continue.dev (VS Code / JetBrains), authoring
rules/prompts/agents/MCP, understanding why Continue does NOT read a root `AGENTS.md`, or
verifying the Continue gald3r install.

---

> Full 11-section breakdown + evidence URLs in `PLATFORM_SPEC.md` (this folder). **Status: ⚠️
> partial parity** — Continue natively supports **rules, commands (Prompt files), agents, and
> MCP**; **Skills are unconfirmed as first-party** (third-party-documented convention only); and
> there are **no lifecycle hooks**. Two platform truths (re-verified 2026-07-18, T386): commands
> live at **`.continue/prompts/`**, NOT `.continue/commands/` (the prior path Continue never
> reads), and Continue does **NOT** natively read a root **`AGENTS.md`** — `.continue/rules/*.md`
> is the real rules surface.

## 1. Platform Overview

**Continue.dev** — an open-source AI coding extension for VS Code and JetBrains. Context
providers, slash commands via Markdown "Prompt files," MCP integration, custom models, and
native custom sub-agents. Highly configurable and a good match for gald3r's CRASH primitives,
with two real gaps: no native hooks, and Skills support that is documented only by third-party
marketplaces (not first-party-confirmed).

## 2. Config Layout

```
<project-root>/
└── .continue/
    ├── config.yaml                ← primary config (models, context, MCP, prompts:, etc.)
    ├── rules/    <name>.md        ← persistent instructions (rules equivalent; lexicographic order)
    ├── prompts/  <name>.md        ← Prompt files = custom slash commands (/name) — CORRECTED path
    ├── agents/   <name>.md        ← custom sub-agent definitions (Markdown + YAML frontmatter)
    ├── skills/   <name>/SKILL.md  ← third-party-convention Agent Skills location (unconfirmed native)
    └── mcpServers/
        ├── <name>-mcp.yaml        ← one MCP server per file (native format)
        └── mcp.json               ← Continue also auto-recognizes Claude-Desktop/Cursor-style JSON
```

No root `AGENTS.md` is read or written for Continue — see Common Pitfalls.

## 3. gald3r Integration

**Ship gald3r's `.continue/rules/*.md`** (rule content) + **`.continue/prompts/*.md`** (commands,
`invokable: true` frontmatter) + **`.continue/agents/*.md`** + an MCP registration at
**`.continue/mcpServers/mcp.json`**. Surface `g-skl-*/SKILL.md` at `.continue/skills/<name>/` —
cheap to ship, but the matrix cell stays `⚠️` until a live install test proves discovery.

```bash
gald3r platform install continue --into <target-dir>
```

### Verify
```powershell
Test-Path .continue/rules ; Test-Path .continue/prompts ; Test-Path .continue/agents
Test-Path .continue/mcpServers/mcp.json
```

## 4. Common Pitfalls

- **Commands live at `.continue/prompts/`, NOT `.continue/commands/`** — the T386 root cause of
  the "23 vs 38/39 platform-roster disconnect": gald3r commands were silently unreachable at the
  old path because Continue's Prompt-file engine never reads `.continue/commands/`.
- **No root `AGENTS.md`** — this is the single most consequential correction in the platform's
  history. Continue's own tracker has an **open, unimplemented** feature request
  ([continuedev/continue#6716](https://github.com/continuedev/continue/issues/6716)). Do not
  project a root instructions file for Continue.
- **No lifecycle hooks** — no session-start/pre-tool/pre-commit hook framework is documented.
- **Skills are unconfirmed as first-party** — an open tracker issue
  ([#9216](https://github.com/continuedev/continue/issues/9216)) suggests native discovery may
  not yet ship; treat `.continue/skills/` as a marketplace convention, not a confirmed native one.
- MCP is usable only in Agent mode.

## 5. Capability Summary

| Feature | Status | Notes |
|---|---|---|
| Hooks (`g-hk-*.py`) | ❌ | No lifecycle-hook/event-bus documentation found |
| Skills (`g-skl-*/SKILL.md`) | ⚠️ | Third-party-documented `.continue/skills/`; native support unconfirmed (open issue #9216) |
| Agents (`g-agnt-*.md`) | ✅ | `.continue/agents/*.md`; Markdown + YAML frontmatter |
| Commands (`@g-*`) | ✅ | `.continue/prompts/*.md` (`invokable: true`), `/<name>` — corrected from `.continue/commands/` (T386) |
| Rules (`g-rl-*`) | ✅ | `.continue/rules/*.md`; NOT `AGENTS.md` (open, unimplemented request #6716) |
| MCP | ✅ | `.continue/mcpServers/<name>-mcp.yaml` or auto-recognized JSON; also inline in `config.yaml` |

Full assessment + evidence in `PLATFORM_SPEC.md`. Re-verify on the next
`@g-platform-scan-docs continue` (crawl_max_age_days: 14).
