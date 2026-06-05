---
subsystem_memberships: [PLATFORM_INTEGRATION]
platform: subq
authoring_path: update
docs_url: https://subq.ai
docs_url_secondary:
  - https://subq.ai/code
  - https://docs.subq.ai/overview/
  - https://subq.ai/introducing-subq
  - https://docs.subq.ai/
  - https://console.subq.ai/
  - https://playground.subq.ai/
crawl_max_age_days: 30
vault_doc_path: research/platforms/subq/
last_doc_scan: 2026-06-02
reference: g-skl-platform-cursor
status: ❌
task: T868
---

# PLATFORM_SPEC.md — SubQ (Subquadratic Inc.) / "SubQ Code"

**SubQ** is a subquadratic long-context **LLM** from Subquadratic Inc. (SubQ 1M-Preview; Subquadratic
Sparse Attention / SSA, ~O(n); 1M tokens production, up to ~12M research). Its developer-facing
surface is an **OpenAI-compatible Chat Completions API** (docs.subq.ai). **"SubQ Code" is NOT a
standalone CLI or coding agent** — the official product page (subq.ai/code) describes it as a
**plugin / "long-context layer for coding agents"** that you "Plug into **Claude Code, Codex, and
Cursor**" via a "one-line install", whose job is to "auto-redirect expensive model turns" for
cheaper/faster whole-repo exploration.

Because SubQ Code runs **inside a host agent**, it exposes **none of its own extension mechanisms**:
commands, rules, sub-agents, skills, hooks, and MCP are all properties of the **host tool**
(Claude Code / Codex / Cursor), not of SubQ. As of **June 2026** there is still **no public standalone
SubQ CLI, no published config-folder schema (`.subq/`), and no SubQ-native instruction-file
convention**. A gald3r install therefore targets the **host platform**, never SubQ itself.

> **Authoring path: UPDATE** — supersedes the prior heavy-❓ spec (`last_doc_scan: never`, status `❓`).
> That spec correctly refused to fabricate, but treated SubQ-native conventions as merely
> *undocumented*. The June-2026 official docs (subq.ai/code, docs.subq.ai) make clear they are
> **not-applicable**: SubQ Code is a plugin with **no own extension surface**, so the six gald3r
> mechanisms are downgraded from `❓` to `❌` (`none`). **Verified 2026-06-02** (see Verification
> Evidence). This is the **honest** state — `❌` here means "the host owns it", not "broken".

> **Access status change.** *May 2026*: API/SubQ Code/SubQ Search were waitlist / private-beta with no
> public config docs (prior spec). *June 2026*: the API, **console** (console.subq.ai, keys),
> **playground** (playground.subq.ai), and **docs** (docs.subq.ai) are publicly reachable — but the
> coding offering remains a **plugin**, not an agent with its own extensibility. So the six gald3r
> mechanisms are **not-applicable to SubQ as a host**.

---

## 1. Folder Hierarchy

**Status: ❌ no SubQ-native config folder.**

SubQ publishes **no `.subq/` config-folder schema** and ships no standalone CLI that would read one.
SubQ Code is a plugin loaded by a host agent, so the only config tree that matters is the **host's**
(`.claude/`, `.codex/`, `.cursor/`). gald3r writes **nothing** SubQ-native.

```
<project-root>/
└── (no SubQ-native config tree)
    # SubQ Code is a plugin inside the host agent (Claude Code / Codex / Cursor).
    # gald3r targets the HOST's config tree (.claude/ | .codex/ | .cursor/), not .subq/.
```

**gald3r writes**: nothing SubQ-native. Install gald3r into the **host** platform instead.
**SubQ owns**: the model API (docs.subq.ai), the console (keys), and the plugin's internal
turn-redirection — none of which is a gald3r-writable surface.
Source: https://subq.ai/code

---

## 2. AI Instruction File

**Status: ❌ none-native (inherits the host's instruction file).**

SubQ publishes **no native instruction-file convention** — there is **no `SUBQ.md` and no `.subq/`
instruction schema**. Because SubQ Code plugs into Claude Code / Codex / Cursor, it **inherits
whatever instruction file the host uses** (e.g. **`AGENTS.md`**, or **`CLAUDE.md`** under Claude Code).
gald3r context reaches SubQ today **only indirectly**, via the host tool's `AGENTS.md` / `CLAUDE.md`.
There is no SubQ-specific instruction file to write.
Source: https://docs.subq.ai/overview/

---

## 3. Agents Support — ❌ none

- SubQ Code is itself a **layer/plugin** invoked by an existing coding agent; it is **not** a
  multi-agent framework and documents **no** sub-agent / agent-role / mode definitions. Any subagents
  are the host's (e.g. Claude Code `.claude/agents/`).
- Evidence: subq.ai/code — "The long-context layer for coding agents. Plug into Claude Code, Codex,
  and Cursor."
- Source: https://subq.ai/code

## 4. Skills Support — ❌ none

- **No `SKILL.md` / Agent-Skills / reusable-workflow-file mechanism** is documented on any official
  SubQ page. The whole-repo-context value proposition explicitly de-emphasizes chunking/skill
  machinery, but **no skills API exists**. gald3r `g-skl-*/SKILL.md` are not ingested by SubQ; they
  load only via the host (e.g. Claude Code skills discovery).
- Source: https://subq.ai/code

## 5. Commands / Workflows — ❌ none

- The official SubQ Code page describes only a plugin that "Auto-redirects expensive model turns" via
  "One-line install"; **no slash / custom-command system is documented**. docs.subq.ai covers only
  the Chat Completions API. Any slash commands a user sees come from the **host** tool
  (Claude Code / Codex / Cursor), not SubQ.
- Source: https://subq.ai/code

## 6. Hooks System — ❌ none

- **No lifecycle / event-hook system** (session-start, pre-tool, pre-commit, file-watch, or a
  `hooks.json` equivalent) is documented. The only "automatic" behavior is **internal turn-redirection
  inside the plugin**, which is **not** a user-configurable script hook. gald3r PowerShell
  `g-hk-*.ps1` hooks do **not** run on SubQ; they must run via the **host** (e.g. Claude Code
  `.claude/settings.json` hooks) or via git `core.hooksPath` / manual invocation.
- Source: https://subq.ai/code

## 7. Rules / Memory — ❌ none

- **No persistent-rules / memory / always-on-instructions mechanism** is documented anywhere on
  subq.ai or docs.subq.ai. SubQ's pitch is that a **1M–12M token window loads the whole repo
  directly**, so there is no rules/memory file convention; persistent instructions live in the
  **host** tool's own files (e.g. `AGENTS.md` / `CLAUDE.md`), not SubQ's. gald3r `g-rl-*` rules have
  **no SubQ-native injection point**.
- Source: https://docs.subq.ai/overview/

## 8. MCP Support — ❌ none

- docs.subq.ai documents an **OpenAI-compatible Chat Completions API** (Base URL, API key,
  `/v1/chat/completions`) with "Streaming + tool use" and "OpenAI-compatible endpoints" — an **HTTP
  contract, NOT Model Context Protocol**. **No MCP client/server support** is mentioned. MCP, if used,
  is provided by the **host** agent SubQ plugs into.
- Source: https://docs.subq.ai/overview/

---

## 9. Plugin Caveat vs. Cursor Reference

Compared to the Cursor reference (`g-skl-platform-cursor/PLATFORM_SPEC.md`), SubQ has **no native
gald3r-relevant extension surface at all** — not because it is undocumented, but because **SubQ Code
is a plugin**, not an agent. Every gald3r mechanism (commands / rules / agents / skills / hooks / MCP)
belongs to the **host** the plugin is installed into.

1. **What SubQ actually is** — a subquadratic long-context **LLM** (SubQ 1M-Preview; SSA ~O(n); 1M
   production / ~12M research), sold as **model API + a coding plugin**, not a coding agent.
2. **Developer surface** — OpenAI-compatible Chat Completions API only (docs.subq.ai; console.subq.ai
   for keys; playground.subq.ai to try). Marketed gains for the Code plugin: **"~25% lower bill, 10x
   faster exploration"**.
3. **Output formats / workflows** — streaming responses and OpenAI-style tool calling at the **API**
   level only; **no agent-level workflow / output-format extensibility** is exposed.
4. **Commands ❌ / Rules ❌ / Agents ❌ / Skills ❌ / Hooks ❌ / MCP ❌** — all `none` on SubQ itself;
   each is a **host** property (Claude Code / Codex / Cursor).
5. **Instruction file ❌ (none-native)** — no `SUBQ.md`; inherits the host's `AGENTS.md` / `CLAUDE.md`.
6. **Install targets the host, not SubQ** — to bring gald3r to a SubQ-accelerated workflow, install
   gald3r into the host (Claude Code / Codex / Cursor) and let SubQ Code accelerate it underneath.

## Hook System

- **Type**: none ❌
- **Config file**: none — SubQ documents no hook wiring file (no `hooks.json` equivalent); the plugin
  exposes no user-configurable script hooks
- **Events available**: none — no published lifecycle-event taxonomy; the only "automatic" behavior is
  internal turn-redirection, not a hook
- **Event payload format**: n/a
- **OS limits**: n/a (no hook runtime to constrain)
- **gald3r hook files**: `g-hk-*.ps1` do **not** run on SubQ — wire them on the **host** (e.g.
  Claude Code `.claude/settings.json`) or via git `core.hooksPath` / manual invocation instead

## Atypical Handling

- **SubQ Code is a plugin, not an agent.** It runs inside Claude Code / Codex / Cursor and contributes
  long-context turn-redirection only — it owns no commands/rules/agents/skills/hooks/MCP surface.
- **No `.subq/` config tree and no `SUBQ.md`.** gald3r targets the **host** platform's config tree.
- The public SubQ developer surface is the **model API** (OpenAI-compatible HTTP), not an agent SDK.

## gald3r Integration Notes

- To bring gald3r to a SubQ-accelerated session, **install gald3r into the host** (Claude Code /
  Codex / Cursor) — see `g-skl-platform-claude`, `g-skl-platform-codex`, `g-skl-platform-cursor`.
- Do **not** assume any `.ps1` hook, rule, skill, command, agent, or MCP wiring works on SubQ — all of
  it lives on the host.
- Re-verify on the next `@g-platform-scan-docs subq` (crawl_max_age_days: 30) **only** to catch a
  future standalone SubQ CLI; today there is no SubQ-native config surface to crawl.

---

## Capability Summary (copy into PLATFORM_STATUS.md row)

| Hooks | Rules | Skills | Commands | MCP | Docs Fresh |
|---|---|---|---|---|---|
| ❌ | ❌ | ❌ | ❌ | ❌ | ✅ |

Legend: ✅ verified working · ⚠️ partial / Cursor-generic · ❌ not supported (host owns it) · ❓ untested.

Overall platform `status: ❌` — **instruction-only**. SubQ Code is a confirmed *real product*
(Subquadratic Inc.), but it is a **plugin / long-context layer**, not a standalone agent, so it
exposes **no native gald3r-writable extension surface**. The six mechanisms are `none` because the
**host** (Claude Code / Codex / Cursor) owns them — install gald3r into the host. `❌` here is the
**honest** mapping of "not-applicable to SubQ as a host", not a fabricated negative.

---

## Verification Evidence (docs crawl 2026-06-02, https://subq.ai + https://docs.subq.ai)

| Capability | How verified |
|---|---|
| What SubQ is | subq.ai/introducing-subq + docs.subq.ai/overview — subquadratic long-context LLM (SSA ~O(n); 1M prod / ~12M research); developer surface is an OpenAI-compatible Chat Completions API |
| SubQ Code is a plugin | subq.ai/code — "The long-context layer for coding agents. Plug into Claude Code, Codex, and Cursor"; "one-line install"; "auto-redirects expensive model turns" (~25% lower bill, 10x faster exploration) |
| Commands ❌ | subq.ai/code — only a plugin + one-line install; no slash/custom-command system documented; commands come from the host |
| Rules ❌ | docs.subq.ai/overview — no persistent-rules/memory/always-on convention; whole-repo context replaces it; persistent instructions live in host AGENTS.md/CLAUDE.md |
| Agents ❌ | subq.ai/code — SubQ Code is a layer invoked by an existing agent; no sub-agent/role/mode definitions; not a multi-agent framework |
| Skills ❌ | subq.ai/code — no SKILL.md / Agent-Skills / reusable-workflow mechanism documented |
| Hooks ❌ | subq.ai/code — no lifecycle/event-hook system (no hooks.json equivalent); only internal turn-redirection, not a user hook |
| MCP ❌ | docs.subq.ai/overview — OpenAI-compatible Chat Completions API (Base URL, key, /v1/chat/completions, streaming + tool use); HTTP contract, NOT MCP; no MCP client/server |
| Instruction file ❌ | docs.subq.ai/overview + subq.ai/code — no native SUBQ.md / .subq/ schema; SubQ Code inherits the host's AGENTS.md/CLAUDE.md |
| Access status | June 2026: API/console (console.subq.ai)/playground (playground.subq.ai)/docs (docs.subq.ai) publicly reachable; coding offering still a plugin (was waitlist/private-beta in May 2026) |
| Docs freshness | `last_doc_scan: 2026-06-02` — crawl of subq.ai, subq.ai/code, docs.subq.ai/overview, console.subq.ai, playground.subq.ai |
