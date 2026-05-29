---
subsystem_memberships: [PLATFORM_INTEGRATION]
platform: kiro
authoring_path: update
docs_url: https://kiro.dev/docs
docs_url_secondary:
  - https://kiro.dev/docs/steering/
  - https://kiro.dev/docs/mcp/servers/
  - https://kiro.dev/docs/getting-started/first-project/
crawl_max_age_days: 7
vault_doc_path: research/platforms/kiro/
last_doc_scan: never
reference: g-skl-platform-cursor
status: ⚠️
---

# PLATFORM_SPEC.md — Kiro IDE (Amazon)

Kiro is Amazon's AI IDE (built on VS Code, launched 2025). Its defining model is **spec-driven
development**: structured specs (`requirements.md` / `design.md` / `tasks.md`) are the unit of
work, persistent context is supplied by **steering files**, and automation runs through a **native
agent-hook system**. This spec documents Kiro's actual primitives against the Cursor reference and
records, honestly, where gald3r's Cursor-origin concepts (agents, skills, slash commands) do NOT
have a 1:1 native equivalent on Kiro.

> **Authoring path: UPDATE** — `g-skl-platform-kiro/SKILL.md` already ships. This spec records the
> verified-from-docs findings (web doc citations, May 2026); install/runtime claims that were not
> exercised on a live Kiro install remain `❓`.

> **Doc-verified (May 2026), not install-tested.** Folder/format facts below are sourced from the
> official Kiro docs (see Verification Evidence). They have NOT been confirmed by a gald3r install
> on a live Kiro IDE; `last_doc_scan: never` for the formal SCAN_DOCS crawl.

---

## 1. Folder Hierarchy

Kiro reads everything under a repo-root `.kiro/` folder, with a parallel **global** tree under
`~/.kiro/` for user-wide context. Doc-verified layout:

```
<project-root>/
└── .kiro/
    ├── steering/                  ← always-injected context (project scope)
    │   ├── product.md             ← product context (maps to .gald3r/PROJECT.md)
    │   ├── structure.md           ← codebase structure
    │   ├── tech.md                ← tech-stack guidance
    │   └── gald3r.md              ← gald3r-authored steering (task-management context)
    ├── specs/                     ← spec-driven dev unit of work
    │   └── {feature}/
    │       ├── requirements.md
    │       ├── design.md
    │       └── tasks.md           ← Kiro's own task breakdown (distinct from .gald3r/tasks/)
    ├── hooks/                     ← NATIVE agent hooks — JSON files (NOT .md)
    │   └── {hook-name}.json
    └── settings/
        └── mcp.json               ← workspace-scope MCP config

~/.kiro/                           ← GLOBAL (user-wide) tree
├── steering/                      ← global steering, applies to all workspaces
└── settings/
    └── mcp.json                   ← global MCP config
```

**gald3r writes**: `.kiro/steering/gald3r.md` (context injection), optionally `.kiro/hooks/*.json`
(gald3r lifecycle automation), optionally `.kiro/settings/mcp.json` (MCP servers).
**Kiro owns**: the `.kiro/` namespace, the steering auto-injection mechanism, the spec workflow,
the hook trigger engine, and the MCP connection lifecycle.

**Correction vs. prior SKILL.md text**: hooks are **JSON** (`.kiro/hooks/*.json` with a
`when`/`then` schema), not markdown; specs include a `tasks.md`; MCP lives at
`.kiro/settings/mcp.json`, not the repo root.

---

## 2. AI Instruction File

Kiro has **no single top-level instruction file** like `AGENTS.md`/`CLAUDE.md`. Persistent
instruction is delivered through **steering files** in `.kiro/steering/*.md` (§7), which are
auto-injected into every Kiro session. gald3r therefore does not generate a `KIRO.md` root file;
it writes `.kiro/steering/gald3r.md` instead. (A root `AGENTS.md` may still exist for other tools,
but Kiro does not specifically read it as its primary instruction source. ❓ not install-verified.)

---

## 3. Agents Support

- **Native concept (IDE)**: ❌ Kiro IDE has no user-authored "agent file" mechanism equivalent to
  Cursor's `.cursor/agents/g-agnt-*.md`. Kiro's IDE agent is the built-in spec-driven assistant;
  there is no folder where gald3r drops `g-agnt-*.md` definitions that Kiro auto-discovers in the
  IDE. (Kiro **CLI** does support custom agents via a configuration reference — out of scope for
  the IDE skill; see `g-skl-platform-kiro-cli`.)
- **gald3r mapping**: agent behavior must be expressed as **steering content** (describe the agent
  role/responsibilities inside a steering file) rather than as a discoverable agent file.
- **Status**: ❌ no native IDE agent-file discovery.

---

## 4. Skills Support

- **Native concept**: ❌ Kiro IDE has no `g-skl-*/SKILL.md` discovery mechanism. There is no
  folder-per-skill auto-load equivalent to Cursor's `.cursor/skills/`.
- **Nearest analog**: Kiro's **"Powers"** (`kiro.dev/docs/powers/`) are a packaged-capability
  concept, but they are not the same as gald3r skills and gald3r does not currently emit Powers.
  ❓ untested whether gald3r skill content could be repackaged as a Power.
- **gald3r mapping**: skill knowledge that must be active is folded into steering files; skill
  *procedures* are invoked by referencing the spec/task workflow, not by Kiro auto-loading a SKILL.md.
- **Status**: ❌ no native SKILL.md discovery.

---

## 5. Commands / Workflows

- **Native concept**: ⚠️ Kiro has no `@g-*` / `/g-*` slash-command file mechanism like
  `.cursor/commands/g-*.md`. The Kiro-native "command" surface is the **spec workflow**
  (create spec → requirements → design → tasks → execute) plus hook-triggered `runCommand` actions.
- **gald3r mapping**: gald3r commands do not propagate as invokable Kiro commands. They are
  documented in steering for the human to drive, or wired as hook `then.runCommand` shell actions
  where a deterministic command exists.
- **Status**: ⚠️ no native command files; partial coverage via hooks + steering.

---

## 6. Hooks System

Kiro has a **native agent-hook system** — a genuine strength and the closest parity to Cursor's
`hooks.json`. Hooks are individual JSON files under `.kiro/hooks/`:

```json
{
  "name": "Lint on Save",
  "version": "1.0.0",
  "when": { "type": "fileEdited", "patterns": ["*.py"] },
  "then": { "type": "runCommand", "command": "python3 -m pylint ${file}" }
}
```

- **Format**: one JSON file per hook in `.kiro/hooks/`. Schema is `name` / `version` / `when` /
  `then`. (Hooks can also be created via the IDE's hook UI.)
- **Trigger model**: **event + file-pattern driven** (`when.type` e.g. `fileEdited`, with
  `patterns` globs). This differs fundamentally from Cursor's **lifecycle-event** model
  (`sessionStart`, `stop`, `preToolUse`, `beforeShellExecution`). Kiro's events are
  file/save-centric, not session/tool-call-centric.
- **Action model**: `then` specifies the action — `runCommand` (shell), or an agent action.
  Supports template variables like `${file}`.
- **Wiring mechanism**: Kiro's hook engine discovers files in `.kiro/hooks/` automatically; no
  central `hooks.json` index (contrast Cursor's single `.cursor/hooks.json`).
- **gald3r gap**: gald3r's PowerShell lifecycle hooks (`g-hk-session-start`, `g-hk-agent-complete`,
  `g-hk-validate-shell`, `preToolUse` guards) have **no direct Kiro event equivalent** — Kiro does
  not expose `sessionStart`/`stop`/`preToolUse`. gald3r hooks that map to a `fileEdited` trigger
  CAN be expressed as Kiro hooks; session/tool-lifecycle hooks cannot and must run manually. ❓ the
  exact set of Kiro `when.type` values beyond `fileEdited` was not exhaustively verified.
- **Status**: ⚠️ native hook system present and strong, but **event taxonomy differs** — partial
  parity, not drop-in.

---

## 7. Rules / Memory

- **Mechanism**: **steering files** are Kiro's persistent rules/memory. Markdown files in
  `.kiro/steering/` (project) and `~/.kiro/steering/` (global) are auto-injected into every session.
- **Extension**: plain **`.md`** (no `.mdc`).
- **Always-apply vs. on-demand**: docs describe steering as always-injected project context; there
  is no per-rule `alwaysApply`/`globs` frontmatter system like Cursor's `.mdc`. (❓ whether Kiro
  supports conditional/scoped steering inclusion was not verified.)
- **Default steering**: `product.md`, `structure.md`, `tech.md` are the conventional trio. Custom
  steering files are added via the IDE `+` button or by dropping `.md` files in `.kiro/steering/`.
- **gald3r mapping**: gald3r rules (`g-rl-*.mdc`) do not propagate as individual scoped rules. Their
  enforcement content must be consolidated into one or more steering `.md` files. This is a lossy
  mapping (no per-rule glob scoping).
- **Context budget**: steering is injected in full — keep each file lean (the prior SKILL.md
  guidance of ~2K tokens/file is a sensible cap; ❓ no documented hard limit found).
- **Status**: ✅ native persistent-context mechanism (steering) exists; ⚠️ no per-rule scoping.

---

## 8. MCP Support

- **Supported**: ✅ Yes (doc-verified).
- **Config format/location**: JSON at `.kiro/settings/mcp.json` (workspace) and
  `~/.kiro/settings/mcp.json` (global). Standard `mcpServers` object with `command`, `args`,
  `env`, `disabled`, and `autoApprove` fields. Example:
  ```json
  {
    "mcpServers": {
      "web-search": {
        "command": "uvx",
        "args": ["mcp-server-brave-search"],
        "env": { "BRAVE_API_KEY": "..." },
        "disabled": false,
        "autoApprove": ["search"]
      }
    }
  }
  ```
- **Server discovery**: Kiro reads `mcp.json` on startup; servers can also be added via the IDE
  ("ask Kiro to add a new server" or edit the JSON directly).
- **Timeout behavior**: ❓ not documented in the pages crawled.
- **Status**: ✅ verified (config format from docs); active server set / runtime untested on a live
  install.

---

## 9. Known Gaps vs. Cursor Reference

Honest list of Cursor-reference features that do NOT work, are partial, or are untested on Kiro IDE:

1. **No agent-file discovery (❌)** — Kiro IDE has no `.cursor/agents/`-style mechanism. gald3r
   `g-agnt-*.md` definitions are not auto-loaded; agent roles must be written into steering.
   (Custom agents exist only in Kiro **CLI**, not the IDE.)
2. **No SKILL.md discovery (❌)** — no `.cursor/skills/`-style folder-per-skill auto-load. Skill
   knowledge must be folded into steering. "Powers" are a different, unmapped concept.
3. **No command files (⚠️)** — no `@g-*`/`/g-*` invokable command surface. gald3r commands are
   documented in steering or wired as hook `runCommand` actions where deterministic.
4. **Hook event taxonomy differs (⚠️)** — Kiro hooks are **file/save-event** driven
   (`when.type: fileEdited` + patterns), NOT session/tool-lifecycle driven. gald3r's
   `sessionStart`/`stop`/`preToolUse`/`beforeShellExecution` PowerShell hooks have no native Kiro
   equivalent and must run manually. The hook *system itself* is strong (native JSON, file-pattern
   triggers, `runCommand`), so this is partial, not absent.
5. **No per-rule scoping (⚠️)** — steering has no `alwaysApply`/`globs` frontmatter; gald3r's `.mdc`
   per-rule glob scoping degrades to whole-file always-injected steering content.
6. **No top-level instruction file** — Kiro uses steering, not `AGENTS.md`/`CLAUDE.md`; gald3r
   writes `.kiro/steering/gald3r.md` instead.
7. **SCAN_DOCS not yet run (❓)** — `last_doc_scan: never`. Folder/format claims here are from a
   May-2026 manual doc read, not the formal `@g-platform-scan-docs kiro` crawl. Confirm the full
   hook `when.type` taxonomy, any steering size limits, and MCP timeout behavior on the next crawl.
8. **Decision-tree placement** — Kiro's JSON hook schema and steering format are correctly
   classified as **platform-specific** (live in the `.kiro/` tree / a `.gald3r_sys/platforms/kiro/`
   adapter), not common `.gald3r_sys/`. Spec/PRD mapping (Kiro specs ↔ gald3r PRDs) is the natural
   integration seam.

---

## Capability Summary (copy into PLATFORM_STATUS.md row)

| Hooks | Rules | Skills | Commands | MCP | Docs Fresh |
|---|---|---|---|---|---|
| ⚠️ | ⚠️ | ❌ | ⚠️ | ✅ | ❓ |

Legend: ✅ verified working · ⚠️ partial / Cursor-generic · ❌ not supported · ❓ untested.

- **Hooks ⚠️**: native JSON hook system exists (strength) but event taxonomy is file-event, not
  session/tool-lifecycle — gald3r lifecycle hooks do not map 1:1.
- **Rules ⚠️**: steering provides persistent context but no per-rule glob scoping.
- **Skills ❌**: no SKILL.md discovery mechanism.
- **Commands ⚠️**: no command-file surface; partial via hooks + steering.
- **MCP ✅**: `.kiro/settings/mcp.json` format doc-verified.
- **Docs Fresh ❓**: `last_doc_scan: never` — flip to ✅ after the first SCAN_DOCS crawl.

---

## Verification Evidence

| Capability | How verified |
|---|---|
| Folder hierarchy (`.kiro/steering`, `specs`, `hooks`, `settings`) | Kiro docs (kiro.dev/docs/steering, getting-started/first-project) — May 2026 manual read |
| Steering files (`product.md`/`structure.md`/`tech.md`, global `~/.kiro/steering/`) | kiro.dev/docs/steering — doc-verified |
| Hooks JSON schema (`when`/`then`, `fileEdited`, `runCommand`, `${file}`) | Kiro docs hook example — doc-verified; full `when.type` taxonomy ❓ |
| MCP config (`.kiro/settings/mcp.json`, `~/.kiro/settings/mcp.json`, `mcpServers` schema) | repost.aws Kiro+MCP article + kiro.dev/docs/mcp/servers — doc-verified |
| No agent-file / SKILL.md / command-file discovery (IDE) | Absence in Kiro IDE docs; CLI custom-agents documented separately (kiro.dev/docs/cli/custom-agents) |
| Install / runtime behavior | ❓ NOT exercised on a live Kiro install; `node bin/install.js --only kiro` path untested here |
| Docs freshness | Not formally crawled — `last_doc_scan: never`; pending `@g-platform-scan-docs kiro` |
