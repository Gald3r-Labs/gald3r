---
subsystem_memberships: [PLATFORM_INTEGRATION]
platform: codex
authoring_path: update
docs_url: https://developers.openai.com/codex
docs_url_secondary: https://developers.openai.com/codex/config-schema.json
crawl_max_age_days: 7
vault_doc_path: research/platforms/openai/
last_doc_scan: never
reference: g-skl-platform-cursor
status: ⚠️
task: T1464
---

# PLATFORM_SPEC — codex (OpenAI Codex CLI)

Authoring path: **UPDATE** existing `g-skl-platform-codex/SKILL.md`.

OpenAI Codex CLI (`codex` command) is OpenAI's open-source terminal-based coding agent.
It is a **config-file-centric** platform: a single `config.toml` (TOML, schema-validated)
drives the model, sandbox, approval policy, skills registration, and inline agent roles.
There is **no native rules folder, no commands folder, and no hook/lifecycle-event system**.
Behavioral enforcement is delivered entirely through the root `AGENTS.md` instruction file
plus `config.toml` agent-role descriptions.

This spec reflects the **modern Codex CLI config format** (`.codex/config.toml`,
`#:schema https://developers.openai.com/codex/config-schema.json`) as actually shipped in
this repo at `gald3r_template/.gald3r_sys/platforms/.codex/`. Earlier gald3r notes referenced
a legacy `codex.config.json` + `suggest`/`auto-edit`/`full-auto` mode naming; those are
superseded by `config.toml` + `approval_policy` / `sandbox_mode` keys documented below.

---

## 1. Folder Hierarchy

```
.codex/                       ← Codex CLI project config (gald3r writes this)
├── config.toml               ← master config: model, sandbox, approval, [features],
│                                [[skills.config]] registrations, [agents.*] roles
├── INSTALL.md                ← gald3r setup instructions (optional, gald3r-authored)
└── skills/                   ← skill folders, one dir per skill
    └── g-skl-*/SKILL.md      ← only paths explicitly registered in config.toml are active

AGENTS.md                     ← project ROOT (NOT inside .codex/) — primary instruction file
~/.codex/config.toml          ← optional user-level config (Codex merges user + project)
```

- **gald3r writes**: `.codex/config.toml`, `.codex/skills/g-skl-*/`, root `AGENTS.md`.
- **Platform owns**: the `config.toml` schema, the `~/.codex/` user-level config, sandbox
  internals, and auth/session state.
- **No `.codex/rules/`**, **no `.codex/commands/`**, **no `.codex/agents/`**, **no `.codex/hooks/`** —
  agents are inline in `config.toml`; rules/commands fold into `AGENTS.md`. ❓ A future Codex
  release could add `.codex/prompts/` (slash-prompt) support; not verified here.

## 2. AI Instruction File

- **File**: `AGENTS.md` at the **project root** (not inside `.codex/`).
- **Format**: Markdown. Read natively by Codex CLI at session start.
- **gald3r behavior**: gald3r generates/merges the root `AGENTS.md`, including a dedicated
  **Enforcement Rules** section (error reporting, task-completion gate, code-change gate,
  session-start sync, `.gald3r/` folder gate, doc placement, PowerShell conventions). Because
  Codex has no rules folder, `AGENTS.md` is the *only* always-apply enforcement surface.
- Codex also honors user-level `~/.codex/AGENTS.md` and merges nested `AGENTS.md` files up the
  directory tree (per OpenAI's documented AGENTS.md convention). ❓ exact precedence/merge order
  not independently verified for this gald3r install.

## 3. Agents Support

- **Native concept: yes, but inline (not file-per-agent).** Codex defines agent roles in
  `config.toml` under `[agents]` (global tuning: `max_threads`, `max_depth`) and `[agents.<role>]`
  sections, each with a `description`.
- gald3r maps its agent roster to inline role descriptions (task-manager, planner, qa-engineer,
  code-reviewer, infrastructure, verifier — see repo `config.toml`).
- **Difference from Cursor reference**: Cursor/Claude discover `g-agnt-*.md` files in an `agents/`
  folder. Codex has **no** `g-agnt-*.md` file discovery — the `.md` agent files do not load. The
  role *descriptions* must be hand-maintained in `config.toml`, so the agent files and the TOML
  can drift. Multi-agent execution requires `[features] multi_agent = true`.

## 4. Skills Support

- **Folder-per-skill** under `.codex/skills/g-skl-<name>/SKILL.md`.
- **Explicit registration required** — unlike Cursor/Claude folder auto-discovery, every skill
  must be listed in `config.toml`:
  ```toml
  [[skills.config]]
  path = ".codex/skills/g-skl-tasks"
  enabled = true
  ```
- **Only register paths that exist** — a registered path that is missing on disk can cause a
  startup error. The repo currently registers the 17 gald3r core skills (bugs, code-review,
  dependency-graph, git-commit, ideas, medkit, plan, project, qa, review, setup, status,
  subsystems, swot-review, tasks, verify-ladder + medic/medkit). The full ~90-skill gald3r set
  is NOT registered for Codex.
- Once registered and `enabled = true`, Codex loads the skill when contextually relevant
  (model-judged), similar to other platforms. ❓ the precise auto-activation trigger
  (relevance vs. explicit invoke) is not independently verified.

## 5. Commands / Workflows

- **No native slash-command / workflow-file system.** Codex has no `commands/` discovery folder.
- gald3r `g-*` "commands" are surfaced two ways on Codex: (a) as **skills** in `.codex/skills/`
  that carry the workflow instructions, and (b) as behavioral guidance in root `AGENTS.md`.
- There is no `@g-*` or `/g-*` command palette equivalent. Users describe intent in natural
  language; Codex matches it to a registered skill. ❓ Codex may support custom prompts/profiles
  in newer builds; not verified for this install.

## 6. Hooks System

- **No hook system. ❌** Codex exposes **no** lifecycle events — there is no `sessionStart`,
  `stop`, `preToolUse`, `postToolUse`, or `beforeShellExecution` equivalent, and no `hooks.json`.
- Consequence for gald3r: the PowerShell session-start / inbox-check / pre-commit hooks that fire
  automatically on Cursor and Claude Code **do not auto-fire on Codex**. Their logic must be
  invoked manually or restated as `AGENTS.md` instructions.
- Shell execution itself is gated by `approval_policy` + `sandbox_mode` (below), not by a hook
  layer. `[features] shell_tool = true` enables shell calls.

## 7. Rules / Memory

- **No native rules directory. ❌** No `.codex/rules/`, no `.mdc`/`.md` rule-file discovery.
- Persistent always-apply "rules" live in the root `AGENTS.md` Enforcement Rules section.
  `config.toml` agent-role `description` strings carry secondary behavioral guardrails.
- No documented per-rule token/size limit; the practical limit is `AGENTS.md`'s contribution to
  the context window. `model_reasoning_effort = "high"` and `personality` are TOML-level
  behavior knobs, not rule files.

## 8. MCP Support

- **Yes. ✅** Codex CLI supports Model Context Protocol servers.
- **Config location/format**: MCP servers are declared in `config.toml` (modern format). Earlier
  gald3r notes referenced an `mcpServers` block in `codex.config.json`; the current
  schema-validated `config.toml` is the authoritative target. The exact TOML table name for MCP
  servers in this install is **❓ not verified by inspection** (the repo `config.toml` does not
  currently declare MCP servers) — confirm against
  `https://developers.openai.com/codex/config-schema.json` before asserting the table key.
- Server discovery is config-declared (not auto-scanned). Timeout/connect behavior: ❓ untested.

## 9. Known Gaps vs. Cursor Reference

Using the decision tree in `g-skl-platform-cursor/SKILL.md` — a capability either (a) lives in
common `.gald3r_sys/`, (b) needs platform-specific config in `.gald3r_sys/platforms/.codex/`, or
(c) is a documented gap:

| Cursor-reference capability | Codex status | Disposition |
|---|---|---|
| `.cursor/rules/*.mdc` always-apply rules | ❌ no rules dir | (c) gap → folded into root `AGENTS.md` |
| `agents/g-agnt-*.md` file discovery | ❌ inline only | (b) `config.toml [agents.*]` descriptions; `.md` files don't load |
| `commands/` slash-command palette (`@g-*`) | ❌ none | (c) gap → skills + `AGENTS.md` carry the workflow |
| Lifecycle hooks (`hooks.json`, sessionStart, etc.) | ❌ none | (c) hard gap → manual / `AGENTS.md` restatement |
| Skill folder auto-discovery | ⚠️ explicit registration | (b) every skill must be listed in `config.toml` |
| Full ~90-skill gald3r set | ⚠️ 17 core registered | (b) Codex install ships core subset only |
| MCP servers | ✅ supported | (a)/(b) declared in `config.toml`; exact table key ❓ |

**Hard gaps (not achievable on Codex today): hooks, rules folder, command palette, agent-file
auto-discovery.** Soft gaps (achievable with platform-specific config): skill registration,
agent-role descriptions, MCP wiring.

---

## Capability Summary (copy into PLATFORM_STATUS.md row)

| Hooks | Rules | Skills | Commands | MCP | Docs Fresh |
|---|---|---|---|---|---|
| ❌ | ⚠️ | ⚠️ | ❌ | ⚠️ | ❌ |

Legend: ✅ verified working · ⚠️ partial / Cursor-generic · ❌ not supported · ❓ untested.

- **Hooks ❌** — no native lifecycle-event system (verified: no hook key in schema/config; old SKILL.md and `codex_instructions.md` both state "no hooks").
- **Rules ⚠️** — no rules folder, but always-apply enforcement IS delivered via root `AGENTS.md` (partial parity, not a clean ✅, not a total ❌).
- **Skills ⚠️** — supported but require explicit `[[skills.config]]` registration; only 17 core skills shipped, not the full set.
- **Commands ❌** — no slash/workflow command system.
- **MCP ⚠️** — protocol supported, but the exact `config.toml` declaration is not verified by repo inspection and no servers are currently declared.
- **Docs Fresh ❌** — `last_doc_scan: never`; `@g-platform-scan-docs codex` not yet run.

---

## Verification Evidence

| Capability | How verified | Confidence |
|---|---|---|
| Folder layout / config.toml format | Read `gald3r_template/.gald3r_sys/platforms/.codex/config.toml` + `codex_instructions.md` in this repo | High (direct file inspection) |
| `AGENTS.md` is root instruction file | Repo root `AGENTS.md` present; `codex_instructions.md` documents it | High |
| Inline agents in `config.toml` | `[agents]`, `[agents.task-manager]` etc. present in repo `config.toml` | High |
| Explicit skill registration | 17 `[[skills.config]]` blocks present in repo `config.toml` | High |
| No hooks / no rules dir / no commands dir | `codex_instructions.md` "What Codex does NOT have" + existing SKILL.md §3 | Medium (gald3r docs, not OpenAI doc citation) |
| MCP support + exact config key | NOT verified — no MCP block in repo config; needs official doc/schema crawl | ❓ Low |
| approval_policy / sandbox_mode semantics | `config.toml` values (`on-request`, `workspace-write`); semantics from gald3r notes | Medium |

**Unverified items remain `❓` above.** A doc scan (`@g-platform-scan-docs codex` against
`https://developers.openai.com/codex` + the config-schema URL) is required to (1) confirm the MCP
TOML table key, (2) confirm AGENTS.md merge precedence, and (3) set `last_doc_scan`. Until then
`status: ⚠️` (partial / config-verified, docs-unscanned).
