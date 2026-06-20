---
name: g-skl-platform-subq
description: Authoritative reference for SubQ (Subquadratic Inc.) and "SubQ Code" in gald3r projects. SubQ is a long-context LLM (OpenAI-compatible Chat Completions API); SubQ Code is a PLUGIN / long-context layer that plugs into Claude Code, Codex, and Cursor — it exposes NO native commands/rules/agents/skills/hooks/MCP of its own. gald3r installs target the HOST tool, not SubQ.
crawl_max_age_days: 30
vault_doc_path: research/platforms/subq/
vault_docs_url: https://subq.ai
docs_url: https://subq.ai
docs_url_secondary:
  - https://subq.ai/code
  - https://docs.subq.ai/overview/
  - https://subq.ai/introducing-subq
  - https://console.subq.ai/
  - https://playground.subq.ai/
last_doc_scan: 2026-06-02
capability_status:
  hooks: "❌ none — SubQ Code is a plugin; no lifecycle hooks. Wire g-hk-*.ps1 on the HOST (Claude Code/Codex/Cursor) or via git core.hooksPath"
  rules: "❌ none — no .mdc/rules/memory mechanism; persistent instructions live in the host's AGENTS.md/CLAUDE.md"
  skills: "❌ none — no SKILL.md / Agent-Skills discovery; gald3r skills load via the host, not SubQ"
  commands: "❌ none — no slash/custom-command system; commands come from the host tool"
  agents: "❌ none — SubQ Code is a layer invoked by an existing agent; not a multi-agent framework"
  mcp: "❌ none — developer surface is an OpenAI-compatible Chat Completions API (HTTP), NOT MCP"
token_budget: low
subsystem_memberships: [PLATFORM_INTEGRATION]
---

# g-skl-platform-subq — SubQ (Subquadratic) / "SubQ Code"

Activate for: questions about installing gald3r alongside SubQ / SubQ Code, or about which extension
mechanisms SubQ exposes (answer: **none of its own** — SubQ Code is a plugin; the **host** owns them).

---

> Full per-mechanism breakdown + evidence URLs in `PLATFORM_SPEC.md` (this folder). **Status: ❌
> instruction-only.** SubQ Code is a **plugin / long-context layer** that "Plug[s] into Claude Code,
> Codex, and Cursor" — it exposes **no** native commands, rules, agents, skills, hooks, or MCP. A
> gald3r install therefore targets the **HOST** platform, not SubQ. (Verified 2026-06-02 against
> https://subq.ai + https://docs.subq.ai.)

## 1. Platform Overview

**SubQ** (Subquadratic Inc.) is a **long-context LLM** — SubQ 1M-Preview, Subquadratic Sparse
Attention (SSA, ~O(n)), 1M tokens production / up to ~12M research. Its developer-facing surface is an
**OpenAI-compatible Chat Completions API** (docs.subq.ai; console.subq.ai for keys;
playground.subq.ai to try).

**"SubQ Code" is NOT a standalone CLI/agent.** Per subq.ai/code it is a **plugin** — "the long-context
layer for coding agents" — installed via a "one-line install" that "auto-redirects expensive model
turns" for cheaper/faster whole-repo exploration (~25% lower bill, 10x faster). Because it runs
**inside** Claude Code / Codex / Cursor, every gald3r-relevant extension mechanism is a property of the
**host**, not of SubQ.

| Attribute | Value |
|---|---|
| Architecture | Subquadratic Sparse Attention (SSA), ~O(n) |
| Context window | 1,000,000 tokens production; up to ~12M research |
| Developer surface | OpenAI-compatible Chat Completions API (`/v1/chat/completions`) — HTTP, not MCP |
| SubQ Code | **Plugin** for Claude Code / Codex / Cursor (one-line install; auto-redirects turns) |
| Access (June 2026) | API/console/playground/docs publicly reachable; coding offering still a plugin |

## 2. Config Layout

```
<project-root>/
└── (no SubQ-native config tree)
    # SubQ Code is a plugin inside the host agent.
    # gald3r targets the HOST config tree: .claude/ | .codex/ | .cursor/ (+ AGENTS.md/CLAUDE.md).
```

SubQ publishes **no `.subq/` schema and no `SUBQ.md`**. It **inherits the host's instruction file**
(`AGENTS.md`, or `CLAUDE.md` under Claude Code).

## 3. gald3r Integration

**There is no SubQ-native install.** To bring gald3r to a SubQ-accelerated session, **install gald3r
into the host** the SubQ Code plugin runs inside, then let SubQ Code accelerate it underneath:

- Host = Claude Code → use `g-skl-platform-claude` (`.claude/` tree + `CLAUDE.md`/`AGENTS.md`)
- Host = Codex → use `g-skl-platform-codex` (`.codex/` config)
- Host = Cursor → use `g-skl-platform-cursor` (`.cursor/` tree)

### Verify
```powershell
# There is no .subq/ config to check. Verify the HOST install instead, e.g. Claude Code:
Test-Path .claude/commands ; Test-Path .claude/skills ; Test-Path .claude/agents
Test-Path .claude/settings.json   # host hooks + MCP (SubQ Code contributes neither)
```

## 4. Common Pitfalls

- **Do not treat SubQ Code as an agent with a config folder.** It is a **plugin** — no `.subq/`, no
  `SUBQ.md`, no native commands/rules/agents/skills/hooks/MCP.
- **Do not wire `g-hk-*.ps1` to SubQ.** It has no hook system; wire hooks on the **host** (e.g.
  `.claude/settings.json`) or via git `core.hooksPath`.
- **The SubQ API is OpenAI-compatible HTTP, NOT MCP.** Do not record MCP support for SubQ.
- **Persistent instructions live in the host's `AGENTS.md`/`CLAUDE.md`**, not in a SubQ file.

## 5. Capability Summary

| Feature | Status | Notes |
|---|---|---|
| Hooks (`g-hk-*.ps1`) | ❌ | No lifecycle hooks; wire on the host (Claude Code `.claude/settings.json`) or git `core.hooksPath` |
| Skills (`g-skl-*/SKILL.md`) | ❌ | No SKILL.md / Agent-Skills discovery; skills load via the host |
| Agents (`g-agnt-*.md`) | ❌ | SubQ Code is a layer invoked by an existing agent; not a multi-agent framework |
| Commands (`@g-*`) | ❌ | No slash/custom-command system; commands come from the host |
| Rules (`g-rl-*`) | ❌ | No `.mdc`/rules/memory; rules live in the host's `AGENTS.md`/`CLAUDE.md` |
| MCP | ❌ | Developer surface is an OpenAI-compatible Chat Completions API (HTTP), not MCP |

`status: ❌` overall = **instruction-only**. SubQ Code is a **plugin / long-context layer**, so the six
mechanisms are `none` because the **host** owns them — install gald3r into the host. This is the
**honest** mapping; do **not** upgrade any cell off `❌` unless a future standalone SubQ CLI ships and
`@g-platform-scan-docs subq` confirms a real SubQ-native convention. No fabrication.

Full assessment + evidence in `PLATFORM_SPEC.md`. Re-verify on the next `@g-platform-scan-docs subq`
(crawl_max_age_days: 30).

---
*Updated: 2026-06-02 | Task: T868 | SubQ Code = plugin for Claude Code/Codex/Cursor (no native extension surface) | Spec: PLATFORM_SPEC.md*
