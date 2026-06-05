---
name: g-skl-platform-warp
description: Authoritative reference for Warp (AI terminal + Oz agent platform) customization in gald3r projects. Covers AGENTS.md/WARP.md project rules, Agent Skills (SKILL.md) cross-vendor discovery, Agent Profiles + Oz subagent orchestration, Warp Drive Workflows + MCP, the absent hook surface, and gald3r install verification.
crawl_max_age_days: 14
vault_doc_path: research/platforms/warp/
vault_docs_url: https://docs.warp.dev
docs_url: https://docs.warp.dev
docs_url_secondary:
  - https://docs.warp.dev/agent-platform/capabilities/rules/
  - https://docs.warp.dev/agent-platform/capabilities/skills/
  - https://docs.warp.dev/agent-platform/capabilities/agent-profiles-permissions/
  - https://docs.warp.dev/agent-platform/capabilities/slash-commands
  - https://docs.warp.dev/agent-platform/capabilities/mcp/
  - https://github.com/warpdotdev/warp/issues/7834
last_doc_scan: 2026-06-02
capability_status:
  hooks: "❌ no lifecycle-hook system; agent lifecycle hooks are open RFCs (warpdotdev/warp #7834, #6857). Oz Cloud Triggers fire agent runs, not local .ps1 hooks"
  rules: "✅ native Global + Project Rules (AGENTS.md/WARP.md, ALL-CAPS, WARP.md wins if both) + Agent Memory (cross-harness); single-file md, no .mdc/glob"
  skills: "✅ native Agent Skills (SKILL.md); discovers .agents/.warp/.claude/.cursor/… skills dirs (cross-vendor) — .claude/skills/ reusable"
  commands: "⚠️ built-in slash commands + cloud Warp Drive Workflows; NO user-defined custom slash commands (open RFC #6857); not installed from repo commands/"
  agents: "✅ Agent Profiles & permissions + Oz subagent orchestration (multi-harness: Warp Agent / Claude Code / Codex)"
  mcp: "✅ native — Settings > Agents > MCP servers (CLI + HTTP/SSE), per-profile access, shared local + Oz"
token_budget: low
subsystem_memberships: [PLATFORM_INTEGRATION]
---

# g-skl-platform-warp

Activate for: setting up gald3r with Warp (AI terminal + Oz agent platform), authoring rules/skills,
mapping agents to Agent Profiles + Oz orchestration, configuring MCP, or verifying the Warp gald3r
install.

---

> Full 9-section breakdown + evidence URLs in `PLATFORM_SPEC.md` (this folder). **Status: ⚠️ strong
> parity with honest gaps** — Warp's Agent Platform natively supports **rules, skills, agents, and
> MCP**, and its Skills system discovers `.claude/skills/` + `.agents/skills/` (cross-vendor), so
> gald3r's Claude-Code skill artifacts are largely reusable. **Commands are partial** (built-in slash
> commands + cloud Warp Drive Workflows; no custom slash commands — open RFC #6857) and **hooks are
> absent** (open RFCs #7834 / #6857). (Verified 2026-06-02 against https://docs.warp.dev.)

## 1. Platform Overview

**Warp** is an AI-native terminal (not an IDE) whose 2026 **Agent Platform** adds a real
extensibility surface. The AI surface splits into **Active AI** (always-on hints), **Agent Mode**
(interactive multi-step terminal tasks), and **Oz Cloud Agents** (autonomous, event-triggered, with
subagent orchestration). It has **no file tree / editor pane** — primitives are terminal sessions,
project **Rules** files, on-disk **Agent Skills**, app-managed **Agent Profiles + MCP**, and
**Warp Drive** (cloud store of Workflows, Notebooks, Prompts, Env Vars).

- **Rules**: `AGENTS.md` / `WARP.md` at the repo root **auto-apply** within the project (+ Global
  Rules + cross-harness Agent Memory)
- **Skills**: native `SKILL.md`; discovers `.agents/.warp/.claude/.cursor/…` skills dirs (cross-vendor)
- **Agents**: Agent Profiles & permissions + **Oz subagent orchestration** (Warp Agent / Claude Code / Codex)
- **MCP**: first-class; Settings > Agents > MCP servers (CLI + HTTP/SSE), shared across local + Oz
- **Commands**: built-in slash commands + cloud Warp Drive Workflows (no custom slash commands yet)
- **Hooks**: none (open RFCs #7834 / #6857)

**Instruction-file convention**: Warp reads **`AGENTS.md`** (default, vendor-neutral) or legacy
**`WARP.md`** — **not** `CLAUDE.md`. ALL-CAPS required; `WARP.md` wins if both exist.

> **Full capability assessment**: see `PLATFORM_SPEC.md` (9 sections) in this skill folder.

## 2. Config Layout

```
<project-root>/
├── AGENTS.md             ← default project rules (vendor-neutral) — gald3r writes
├── WARP.md               ← legacy native rules (ALL-CAPS); wins if both exist — gald3r writes
├── <subdir>/AGENTS.md    ← per-subdir rules (best-effort) — optional
├── .agents/skills/  <name>/SKILL.md  ← Agent Skills (SKILL.md) — gald3r writes
├── .warp/skills/    <name>/SKILL.md  ← Warp-native skill dir — optional
└── .claude/skills/  <name>/SKILL.md  ← also discovered (Claude-Code interop) — gald3r reuse

~/.warp/               ← Warp local app state (themes, launch configs) — platform-owned
(app/cloud) Agent Profiles · MCP servers · Warp Drive Workflows/Notebooks/Prompts/Env
```

Warp **also** discovers `.claude/skills/` (and `.agents/.cursor/.codex/.gemini/.copilot/…`) skill
trees → **gald3r's Claude-Code skill tree works as-is on Warp.** Rules are single-file markdown — no
`.mdc`/glob folder; flatten `g-rl-*` into the root `AGENTS.md`/`WARP.md`.

## 3. gald3r Integration

**Cheapest high-parity install: ship gald3r's `.claude/skills/` (or `.agents/skills/`) tree** — Warp's
Skills system discovers it natively. Flatten `g-rl-*` rules into the root `AGENTS.md`/`WARP.md` (Warp
auto-applies it every session). Configure MCP once in the Warp app. Map the agent roster to **Agent
Profiles** and g-go swarm orchestration to **Oz subagent orchestration**.

### Project Rules (primary text surface)

Fold gald3r enforcement into the root `AGENTS.md` (or `WARP.md`). Warp auto-applies it within the
project every session — no manual pin. Single-file markdown only, so consolidate the fine-grained
`g-rl-*` set into the root file.

### MCP (app-managed)

Add servers via **Settings > Agents > MCP servers** (CLI Server `npx`/Docker, or Streamable HTTP/SSE).
Per-profile access rules + env-var/OAuth auth; shared context across local and Oz agents.

### Warp Drive Workflows (manual / cloud-only)

Custom slash commands are **not** supported (open RFC #6857). Warp Drive Workflows (parameterized,
repo/user-scoped) are the closest user-authorable command primitive but are **cloud-backed**, not
installed from on-disk `commands/g-*.md`. Recreate gald3r operations manually if desired:
- `gald3r status` — show active tasks
- `gald3r commit T{id}` — commit with task reference
- `gald3r new-task` — launch task creation

### Verify
```powershell
warp --version 2>$null   # Warp app version (if CLI exposed)
Test-Path AGENTS.md ; Test-Path WARP.md          # project rules file
Test-Path .claude/skills ; Test-Path .agents/skills   # discoverable SKILL.md trees
```

## 4. Common Pitfalls

- Instruction file is **`AGENTS.md` / `WARP.md`** (ALL-CAPS), **not `CLAUDE.md`** — Warp does not read
  `CLAUDE.md` as a rules file. If both `AGENTS.md` and `WARP.md` exist, **`WARP.md` wins**.
- Warp rules are **single-file markdown** — no `.mdc`/glob-scoped rule folder; flatten `g-rl-*` into
  the root rules file.
- **Skills are real and cross-vendor** — ship `.claude/skills/` or `.agents/skills/`; do not assume
  skills are unsupported (the prior spec was wrong).
- Agents are **app-managed Agent Profiles** (+ Oz orchestration), not on-disk `g-agnt-*.md` files.
- **Custom slash commands are NOT supported** (open RFC #6857) — Warp Drive Workflows are cloud-only
  and not installed from the repo. Recreate them manually if you want gald3r ops as Workflows.
- **No lifecycle hooks fire on Warp** (session-start/inbox/pre-commit `.ps1` don't run); agent
  lifecycle hooks are open RFCs (#7834 / #6857). Run gald3r hook scripts manually, reference them
  from rules text, or wire pre-commit/pre-push via git `core.hooksPath`.

## 5. Capability Summary

| Feature | Status | Notes |
|---|---|---|
| Hooks (`g-hk-*.ps1`) | ❌ | No lifecycle-hook system; agent hooks open RFCs (#7834 / #6857). Oz Cloud Triggers fire agent runs, not local `.ps1`. Run manually or via git `core.hooksPath`. |
| Skills (`g-skl-*/SKILL.md`) | ✅ | Native Agent Skills (`SKILL.md`); discovers `.agents`/`.warp`/`.claude`/`.cursor`/… skills dirs (cross-vendor). `.claude/skills/` reusable. |
| Agents (`g-agnt-*.md`) | ✅ | Agent Profiles & permissions (base model, autonomy, tool/MCP allow-deny) + Oz subagent orchestration (Warp Agent / Claude Code / Codex). App-managed, not on-disk files. |
| Commands (`@g-*`) | ⚠️ | Built-in slash commands + cloud Warp Drive Workflows (parameterized, repo/user-scoped). NO custom slash commands (open RFC #6857); not installed from `commands/g-*.md`. |
| Rules (`g-rl-*`) | ✅ | Native Global + Project Rules (`AGENTS.md`/`WARP.md`, auto-applied) + Agent Memory (cross-harness). Single-file md — no `.mdc`/glob; flatten `g-rl-*`. |
| MCP | ✅ | Settings > Agents > MCP servers (CLI + HTTP/SSE); per-profile access; env-var/OAuth; shared local + Oz. |

> **Ground-truth hook events (T1538/T1554):** warp has **no native lifecycle hook system** for gald3r
> `g-hk-*.ps1` (Type: `none`). The authoritative, machine-readable statement of this — including the
> honest `none` event list (open RFCs #7834 / #6857) and how gald3r hook behaviors must instead run
> (manually, via rules text, or via git `core.hooksPath`) — lives in
> [`PLATFORM_SPEC.md` -> `## Hook System`](./PLATFORM_SPEC.md). Reference that block rather than
> re-listing hook details here.
> **Last verified against platform version:** warp (docs crawl `last_doc_scan: 2026-06-02`). Re-verify
> the event names in `PLATFORM_SPEC.md` `## Hook System` on the next `@g-platform-scan-docs warp`.

**Hard gap (not achievable from the repo today): lifecycle hooks. Partial: custom commands (cloud
Warp Drive Workflows only).** Clean native fits: **rules, skills, agents, MCP**. Full assessment +
evidence in `PLATFORM_SPEC.md`. Re-verify on the next `@g-platform-scan-docs warp`
(crawl_max_age_days: 14).
