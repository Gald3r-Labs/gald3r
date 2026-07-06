---
subsystem_memberships: [PLATFORM_INTEGRATION]
platform: claude
authoring_path: update            # existing g-skl-platform-claude/SKILL.md updated in place (T1462)
docs_url: https://docs.anthropic.com/en/docs/claude-code
docs_url_secondary:
  - https://docs.anthropic.com/en/docs/claude-code/hooks
  - https://docs.anthropic.com/en/docs/claude-code/mcp
  - https://docs.anthropic.com/en/docs/claude-code/settings
  - https://docs.anthropic.com/en/docs/claude-code/sub-agents
  - https://docs.anthropic.com/en/docs/claude-code/slash-commands
  - https://docs.anthropic.com/en/docs/claude-code/memory
crawl_max_age_days: 7
vault_doc_path: research/platforms/claude-code/
last_doc_scan: never              # @g-platform-scan-docs claude not run by this implementer subagent
reference: g-skl-platform-cursor
status: ⚠️                        # partial — functional Tier-1, but hook-config-shape inconsistency (see §6, §9)
---

# PLATFORM_SPEC.md — Claude Code

Per-T1462 platform spec for **Claude Code** (Anthropic's agentic coding CLI). Authored against the
T1460 template (9 sections). Grounded in this repository's actual `.claude/` install plus Claude Code
documentation. Unverified claims are marked `❓`.

> **Spec location note**: T1462's deliverable text names `.gald3r_sys/platforms/claude/PLATFORM_SPEC.md`,
> while the T1460 template says "inside the platform's skill folder (or a per-platform docs location)".
> This file lives in the skill folder (`g-skl-platform-claude/PLATFORM_SPEC.md`) so it ships and syncs
> with the skill it documents. If the canonical location is later standardized under
> `.gald3r_sys/platforms/claude/`, parity sync (T1484) can relocate/symlink it.

---

## 1. Folder Hierarchy

Claude Code reads project customization from a `.claude/` directory at the project root (and a
user-level `~/.claude/`). gald3r writes the project-level tree:

```
.claude/
├── CLAUDE.md                ← gald3r-managed project instruction file (loaded every session); imports @AGENTS.md
├── settings.json            ← gald3r/user — permissions, env, mcpServers, hooks (official schema)
├── settings.local.json      ← user-local overrides (gitignored)
├── local.settings.json      ← legacy/local overrides (gitignored)  ❓ non-standard name — see §9
├── hooks.json               ← gald3r-managed hook wiring (NON-standard top-level file — see §6/§9)
├── rules/                   ← gald3r — always-apply modular rules (g-rl-*.md, plain .md)
│   └── g-rl-*.md
├── skills/                  ← gald3r — folder-per-skill (g-skl-*/SKILL.md); native Claude Code Agent Skills
│   └── g-skl-*/SKILL.md
├── agents/                  ← gald3r — subagent definitions (g-agnt-*.md); native Claude Code subagents
│   └── g-agnt-*.md
├── commands/                ← gald3r — slash commands (g-*.md → /g-*)
│   └── g-*.md
└── hooks/                   ← gald3r — hook scripts (g-hk-*.ps1) + companion g-hk-*.md (T1171)
    └── g-hk-*.ps1 / g-hk-*.md
```

| Path | Owner | Notes |
|---|---|---|
| `CLAUDE.md`, `rules/`, `skills/`, `agents/`, `commands/`, `hooks/`, `hooks.json` | gald3r writes | parity-synced from canonical `.gald3r_sys/` |
| `settings.json`, `settings.local.json` | Claude Code owns the schema; gald3r seeds it | official config surface |
| `~/.claude/` (user global) | Claude Code / user | gald3r does NOT write the user-global tree |

Verified against the live install in this repo (`<ECOSYSTEM_ROOT>/<gald3r_source>/.claude/`).

---

## 2. AI Instruction File

Claude Code's project instruction file is **`CLAUDE.md`**. gald3r generates `.claude/CLAUDE.md`, which
`@AGENTS.md`-imports the shared `AGENTS.md` and appends Claude-Code-specific command/agent tables.

- **Location**: project root `CLAUDE.md` AND/OR `.claude/CLAUDE.md` are both read; gald3r ships `.claude/CLAUDE.md`.
- **Memory/import syntax**: Claude Code supports `@path` imports inside `CLAUDE.md` (the live file uses `@AGENTS.md`). ✅ verified in repo.
- **Load behavior**: loaded at every session start as always-apply context (the "memory" system).
- **gald3r generation**: gald3r generates `.claude/CLAUDE.md` and treats root `AGENTS.md` as the shared cross-platform source of truth.

---

## 3. Agents Support

Claude Code has a **native subagent** concept (`.claude/agents/*.md`), so gald3r `g-agnt-*.md` files map directly.

- **Discovery**: `.claude/agents/g-agnt-*.md` are auto-discovered as subagents. ✅
- **Format**: Markdown with YAML frontmatter (`name`, `description`, optional `tools`/`model`). gald3r agents follow this.
- **Invocation**: explicit `@g-agnt-<name>` mention, OR Claude auto-delegates to a subagent when its `description` matches the task (auto-dispatch). ✅
- **vs. Cursor**: Cursor has no first-class subagent dispatch in the same way; Claude Code's native subagents are a strength over the Cursor reference here.

---

## 4. Skills Support

Claude Code has **native Agent Skills** (`.claude/skills/<name>/SKILL.md`), folder-per-skill.

- **Discovery**: `.claude/skills/g-skl-*/SKILL.md` — folder-per-skill (NOT flat). ✅
- **Loading**: progressive disclosure — the `name`+`description` frontmatter is always available; the SKILL.md body loads when Claude determines the skill is relevant or the user invokes it. ✅
- **Invocation**: model-driven (auto when relevant) or via the Skill tool / a command that targets it.
- **Naming constraints**: skill directory name == frontmatter `name`; the entry file MUST be `SKILL.md`. gald3r uses `g-skl-<name>`.
- **Shared location**: `.claude/skills/` is also consumed by OpenCode and GitHub Copilot installs — the broadest skill location in the ecosystem. Keep content platform-neutral.

---

## 5. Commands / Workflows

Native **slash commands** via `.claude/commands/*.md`.

- **Location/format**: `.claude/commands/g-*.md` → invoked as `/g-*`. Markdown body is the prompt; optional frontmatter (`description`, `argument-hint`, `allowed-tools`). ✅
- **Arguments**: `$ARGUMENTS` / `$1`,`$2` placeholders are substituted at invocation. ❓ (documented Claude Code feature; not separately re-tested here)
- **Namespacing**: subdirectories namespace commands (`commands/foo/bar.md` → `/foo:bar`). gald3r keeps commands flat under `commands/`.
- **vs. Cursor**: parity — both expose `/g-*` style commands; Claude Code's are first-class slash commands.

---

## 6. Hooks System

Claude Code DOES have a native hooks system, but the **config surface and shape are the weakest-verified
area** for gald3r parity (this is the known ~80% gap). Two facts matter:

**(a) The official, supported location is `settings.json` (key `"hooks"`).** Official lifecycle events
(per Claude Code docs): `SessionStart`, `SessionEnd`, `UserPromptSubmit`, `PreToolUse`, `PostToolUse`,
`Notification`, `Stop`, `SubagentStop`, `PreCompact`. Official shape is matcher-grouped:

```jsonc
// settings.json (OFFICIAL shape)
"hooks": {
  "PreToolUse": [
    { "matcher": "Edit|Write|MultiEdit",
      "hooks": [ { "type": "command", "command": "powershell.exe -File .claude/hooks/g-hk-...ps1" } ] }
  ],
  "Stop": [ { "hooks": [ { "type": "command", "command": "..." } ] } ]
}
```

**(b) gald3r ALSO ships a top-level `.claude/hooks.json` with a DIFFERENT, partly-legacy shape.** In the
live install, `hooks.json` mixes two shapes:

- `sessionStart` / `stop` / `beforeShellExecution` → flat `{ "command": "...", "_hook_md": "..." }` (NO `matcher`, NO `hooks[]` wrapper, NO `"type"`)
- `PreToolUse` → the correct nested `{ "matcher", "hooks":[{ "type":"command", "command" }] }` shape

This is the **hook-firing-context inconsistency** the task flags. Concretely:

| Issue | Detail | Severity |
|---|---|---|
| Two config files compete | `hooks.json` (gald3r) AND `settings.json` `"hooks"` both define hooks; the live `settings.json` defines a `Stop` chat-logger while `hooks.json` defines a different `stop` chain | ⚠️ duplicate/ambiguous |
| Event-name casing mismatch | `hooks.json` uses lowercase `sessionStart`/`stop`/`beforeShellExecution`; official events are `SessionStart`/`Stop` (and there is no official `beforeShellExecution` — that is a Cursor-era name) | ⚠️ likely-non-firing ❓ |
| Mixed entry shapes in one file | flat vs. nested-with-matcher within the same `hooks.json` | ⚠️ |
| `_hook_md` injection contract | T1171 says the harness SHOULD inject the matching `hook.md` as `additional_context` when a hook fires; whether Claude Code actually does this is unconfirmed | ❓ unverified |

**Whether the lowercase `hooks.json` entries fire at all in current Claude Code is the open question.**
The `PreToolUse` block (correct shape, in `settings.json`-compatible form) is the most likely to fire;
`sessionStart`/`stop`/`beforeShellExecution` in `hooks.json` are the suspect ones. The `BUG-100` fix
(g-hk-session-start.py PS7 unicode escape) confirms the session-start hook IS exercised on at least some
Claude Code versions, but does not confirm the lowercase `hooks.json` wiring is the firing path.

**T1171 hook.md companion pattern** (verified present): every `g-hk-*.ps1` has a sibling `g-hk-*.md`
(5-section: Fires On / What It Does / Side Effects / Related Tasks), referenced via `_hook_md` in `hooks.json`.

**gald3r-internal lifecycle events** (`pre_skill`/`post_skill`, T1055) are NOT native Claude Code events —
they are dispatched by the gald3r skill/command runner and are intentionally not wired into the harness hook
config. The former `pre_session`/`post_session` internal events were retired by T1624 (WS-A-1, decision D-8):
the session-trace hooks now fire on the canonical SessionStart/Stop wiring in `settings.json` +
`g_hk_core.py` CONCERN_CHAIN.

---

## 7. Rules / Memory

- **Modular rules**: `.claude/rules/g-rl-*.md` — plain `.md` (NOT Cursor's `.mdc`). ✅ verified.
- **Always-apply**: rules + `CLAUDE.md` load at every session as the memory/context layer.
- **Frontmatter**: gald3r rules carry `description`/`globs`/`alwaysApply`/`subsystem_memberships`. Claude Code's
  own native rule-frontmatter contract (beyond `CLAUDE.md` imports) is `❓` — gald3r relies on `CLAUDE.md`
  always-apply + the rules being readable context rather than a documented per-rule activation engine like Cursor's `alwaysApply`.
- **Memory hierarchy**: user (`~/.claude/CLAUDE.md`) → project (`./CLAUDE.md` / `.claude/CLAUDE.md`) → imports. Precedence and `@`-imports are documented Claude Code behavior. ✅ (import use verified in repo).
- **Size/token limits**: no hard documented limit; large `CLAUDE.md` consumes session context budget. `❓` exact ceiling.

---

## 8. MCP Support

**Yes — native MCP support.** ✅

- **Config locations** (multiple, in precedence/scope order):
  - `.mcp.json` at project root — project-scoped servers (committed, shared). ❓ not present in this repo's root at scan time.
  - `.claude/settings.json` → `"mcpServers"` — verified present (defines `gald3r_docker` streamable-http + `chrome-devtools` stdio). ✅
  - `enableAllProjectMcpServers` / `enabledMcpjsonServers` toggles in `settings.json`. ✅ verified present.
  - `claude mcp add ...` CLI for user/local scope.
- **Transports**: `stdio` (command+args), `streamable-http` (url), and SSE. The live config uses both `streamable-http` (`http://localhost:8092/mcp`) and `stdio` (`npx chrome-devtools-mcp@latest`). ✅
- **Discovery/connect**: servers auto-connect at session start when enabled. ✅
- **Timeout behavior**: `MCP_TIMEOUT` / per-server settings. `❓` not separately tested.

---

## 9. Known Gaps vs. Cursor Reference

Using the decision tree in `g-skl-platform-cursor/SKILL.md` §4a (capability is (a) common `.gald3r_sys/`,
(b) platform-specific `.gald3r_sys/platforms/.claude/`, or (c) a documented gap):

| # | Gap / Risk | Classification | Status |
|---|---|---|---|
| 1 | **Lowercase `hooks.json` event names** (`sessionStart`/`stop`/`beforeShellExecution`) may not match Claude Code's official `SessionStart`/`Stop` events — and `beforeShellExecution` has no official Claude Code equivalent (Cursor-era name). Those hooks may silently not fire. | (b) platform-specific config — needs migration to official `settings.json` shape | ⚠️/❓ |
| 2 | **Two competing hook config surfaces** — `.claude/hooks.json` (gald3r) and `.claude/settings.json` `"hooks"` (live `Stop` chat-logger). Ambiguous which wins; possible double-fire or no-fire. | (b) — consolidate onto `settings.json` | ⚠️ |
| 3 | **Mixed entry shapes inside `hooks.json`** (flat vs. nested-matcher). | (b) — normalize all entries to `{matcher, hooks:[{type:"command",command}]}` | ⚠️ |
| 4 | **`_hook_md` → `additional_context` injection** (T1171) — unconfirmed that Claude Code injects the companion `hook.md` when a hook fires. | (c) documented gap (harness-dependent) | ❓ |
| 5 | **`local.settings.json`** non-standard filename alongside official `settings.local.json` — likely dead/legacy. | (c) cleanup item | ❓ |
| 6 | **Native per-rule activation engine** — Claude Code lacks Cursor's `.mdc` `alwaysApply`/`globs` rule engine; gald3r leans on `CLAUDE.md` always-apply + readable `rules/` instead. | (c) documented gap | ⚠️ |
| 7 | **`.mcp.json` (project-scoped, committed)** not present at repo root; MCP is configured via `settings.json` only. Cursor-parity-wise functional, but the shareable project-MCP file convention is unused. | (c) optional | ⚠️ |
| 8 | **Slash-command `$ARGUMENTS` substitution** documented but not re-verified in this pass. | (c) untested | ❓ |

**Strengths over Cursor reference**: native subagents (§3) and native Agent Skills (§4) are first-class in
Claude Code and require no shimming.

---

## Capability Summary (copy into PLATFORM_STATUS.md row)

| Hooks | Rules | Skills | Commands | MCP | Docs Fresh |
|---|---|---|---|---|---|
| ⚠️ | ✅ | ✅ | ✅ | ✅ | ❌ |

Legend: ✅ verified working · ⚠️ partial / Cursor-generic · ❌ not supported/not-run · ❓ untested.

(`Docs Fresh` = ❌ because `@g-platform-scan-docs claude` was not run in this implementer pass; `last_doc_scan: never`.)

---

## Verification Evidence

| Capability | Verdict | How verified |
|---|---|---|
| Folder hierarchy | ✅ | Listed live `<ECOSYSTEM_ROOT>/<gald3r_source>/.claude/` (Bash `ls`). |
| `CLAUDE.md` + `@AGENTS.md` import | ✅ | Read live `.claude/CLAUDE.md` (uses `@AGENTS.md`). |
| Rules `.md` (not `.mdc`) | ✅ | `.claude/rules/` contains `g-rl-*.md`; no `.mdc`. |
| Skills folder-per-skill | ✅ | `.claude/skills/g-skl-*/SKILL.md` present; this repo's `g-skl-platform-claude/SKILL.md` is one. |
| Agents (subagents) | ✅ | `.claude/agents/` populated; Claude Code subagent docs. |
| Commands `/g-*` | ✅ | `.claude/commands/g-*.md` present; live `CLAUDE.md` command table. |
| Hooks config inconsistency | ⚠️/❓ | Read live `hooks.json` (lowercase events + mixed shapes) AND `settings.json` (`Stop` chat-logger). Cross-checked vs. official Claude Code hook event names. |
| Hook actually fires | partial | BUG-100 (resolved) shows `g-hk-session-start.py` was exercised — but does not confirm the lowercase `hooks.json` wiring is the firing path. |
| MCP | ✅ | Read live `settings.json` `mcpServers` (streamable-http + stdio) + `enableAllProjectMcpServers`. |
| Docs freshness | ❌ | `@g-platform-scan-docs claude` not run (implementer subagent scope). |

Re-run `@g-platform-scan-docs claude` and a hook-firing smoke test to upgrade the `❓` rows (esp. §6).
