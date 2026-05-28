---
subsystem_memberships: [PLATFORM_INTEGRATION]
platform: cursor
authoring_path: update
docs_url: https://docs.cursor.com
docs_url_secondary:
  - https://docs.cursor.com/context/rules
  - https://docs.cursor.com/context/model-context-protocol
  - https://docs.cursor.com/agent/hooks
crawl_max_age_days: 7
vault_doc_path: research/platforms/cursor/
last_doc_scan: never
reference: g-skl-platform-cursor
status: ✅
---

# PLATFORM_SPEC.md — Cursor (reference implementation)

Cursor is the **reference platform** for gald3r. All gald3r primitives originate in the Cursor
(`.cursor/`) tree and propagate to every other platform via
`custom_scripts/platform_parity_sync.ps1`. This document is therefore the **gold standard** that
T1462–T1483 compare their platforms against; its "Known Gaps" section (§9) is the baseline (the
reference cannot have gaps "vs. itself" — instead it records the small set of features that are
Cursor-native-but-not-yet-fully-wired, and the items still awaiting a SCAN_DOCS confirmation).

> **Authoring path: UPDATE** — `g-skl-platform-cursor/SKILL.md` already ships. This spec records
> the verified findings; the skill remains the living reference.

---

## 1. Folder Hierarchy

gald3r writes everything under the repo-root `.cursor/` folder. Verified layout in this repo:

```
.cursor/
├── cursor_instructions.md      ← gald3r-authored maintainer note (not a Cursor-native file)
├── rules/                      ← always-apply / on-demand rules (.mdc) — 17 files present
│   └── g-rl-*.mdc
├── skills/                     ← skills, folder-per-skill — 110 present
│   └── g-skl-*/SKILL.md
├── agents/                     ← agent definitions (.md) + sdk/ + README.md + JOURNAL_FORMAT.md
│   └── g-agnt-*.md
├── commands/                   ← @-invoked commands (.md) — 174 present
│   └── g-*.md
├── hooks/                      ← PowerShell hook scripts + companion hook.md files
│   ├── g-hk-*.ps1
│   └── g-hk-*.md               ← T1171 companion descriptions
├── hooks.json                  ← TOP-LEVEL hook wiring (NOT .cursor/hooks/hooks.json) — verified
├── hooks.json.example.disabled ← disabled reference variant
└── (no .cursor/mcp.json in this repo — MCP configured via Cursor settings / .mcp.json at root)
```

**gald3r writes**: `rules/`, `skills/`, `agents/`, `commands/`, `hooks/` (`.ps1` + `.md`),
`hooks.json`, `cursor_instructions.md`.
**Cursor owns**: the `.cursor/` namespace itself, the `hooks.json` schema, Cursor settings, and
the rule auto-load mechanism.

**Verified note (correction vs. prior SKILL.md text):** `hooks.json` lives at **`.cursor/hooks.json`**
(repo `.cursor/` root), not inside `.cursor/hooks/`. The `_hook_md` wiring fields point at the
companion `.md` files inside `.cursor/hooks/`.

---

## 2. AI Instruction File

Cursor reads top-level instruction files at session start. In the gald3r ecosystem the canonical
instruction file is **`AGENTS.md`** (root), with `CLAUDE.md`/`GEMINI.md` as platform-personalized
variants and `.cursor/cursor_instructions.md` as a Cursor-scoped maintainer note. Cursor also
honors `.cursorrules` historically, but gald3r uses the `.cursor/rules/*.mdc` mechanism (§7)
rather than the legacy single-file `.cursorrules`.

gald3r **generates/merges** these instruction files via the setup + parity pipeline; they are
personalized per user and are gitignored (see `g-rl-02` protected files).

---

## 3. Agents Support

- **Native concept**: Cursor supports background/agent-mode and reads agent definition markdown.
- **Discovery**: `.cursor/agents/g-agnt-*.md`. Each agent is a markdown file (some agents also
  have a same-named folder, e.g. `g-agnt-code-reviewer/` alongside `g-agnt-code-reviewer.md`, used
  for per-agent journals via `JOURNAL_FORMAT.md`).
- **Loading**: manual selection (agent invoked by name / `@agent-name`), not auto-loaded.
- **Extras present**: `sdk/` (platform SDK agent material), `README.md`, `JOURNAL_FORMAT.md`.
- **Reference status**: ✅ verified — this is the canonical agent layout other platforms mirror.

---

## 4. Skills Support

- **Discovery**: `.cursor/skills/<name>/SKILL.md` — **folder-per-skill**. A loose `.md` directly
  in `skills/` root is NOT picked up.
- **Loading**: auto-loaded when Cursor judges the skill relevant to the request (model-driven
  relevance), or invoked via a command that references the skill.
- **Naming**: gald3r skills are `g-skl-*`; the SKILL.md frontmatter carries `name`, `description`,
  and `subsystem_memberships`.
- **Count in this repo**: 110 skill folders.
- **Reference status**: ✅ verified.

---

## 5. Commands / Workflows

- **Format**: `.cursor/commands/g-*.md` — markdown command definitions.
- **Invocation**: referenced via `@command-name` (and surfaced in this project as `/g-*` per the
  project CLAUDE.md command table).
- **Count in this repo**: 174 command files.
- **Reference status**: ✅ verified.

---

## 6. Hooks System

Cursor exposes a **native hook system** via a JSON wiring file. Verified events wired in this
repo's `.cursor/hooks.json`:

| Event | Hooks wired | Matcher |
|---|---|---|
| `sessionStart` | `g-hk-session-start.ps1` | (none) |
| `stop` | `g-hk-agent-complete.ps1`, `g-hk-nightly-learn.ps1`, `g-hk-session-end.ps1` | (none) |
| `beforeShellExecution` | `g-hk-validate-shell.ps1` | (none) |
| `preToolUse` | `g-hk-pre-tool-call-gald3r-guard.ps1`, `g-hk-pre-tool-call-prd-freeze.ps1`, `g-hk-pre-tool-call-member-gald3r-guard.ps1` | `Edit\|Write\|MultiEdit\|NotebookEdit\|Patch\|ApplyPatch\|str_replace_editor` |

- **Format**: `hooks.json` at `.cursor/hooks.json` (version 1). Each entry: `command` (full
  PowerShell invocation), optional `matcher` (regex over tool names), optional `_hook_md`
  (companion doc path, T1171). Top-level `_doc` documents the hook.md contract.
- **Wiring mechanism**: Cursor invokes the `command` for each matching event; hooks return the
  standard `{ continue = true }` envelope (or block via exit code / verdict).
- **Companion docs (T1171)**: every `g-hk-*.ps1` has a sibling `g-hk-*.md` (5-section template).
- **Extended contract (T600)**: HTTP hook type, glob tool matcher, `block_on_failure`, shell-safe
  arg substitution, and the 6-event worktree lifecycle — see SKILL.md §3a. Some T600 features
  (HTTP hook caller) currently live in `.claude/hooks/` and are a parity follow-up to `.cursor/`.
- **gald3r-internal events (T1055)**: `pre_skill` / `post_skill` / `pre_session` / `post_session`
  are NOT auto-wired into `hooks.json` (Cursor has no native skill-boundary event) — dispatched by
  the gald3r runner. Reference hooks present: `g-hk-pre-skill-timing`, `g-hk-post-skill-timing`,
  `g-hk-pre-session-trace`, `g-hk-post-session-trace`.
- **Reference status**: ✅ verified working — this is the canonical hook layout.

---

## 7. Rules / Memory

- **Extension**: **`.mdc`** (Cursor-specific). All other platforms use plain `.md`; the parity
  sync maps the extension automatically.
- **Location**: `.cursor/rules/g-rl-*.mdc` (17 rule files present in this repo).
- **Loading**: frontmatter-driven. `alwaysApply: true` rules inject into every session;
  `globs:` scope a rule to matching files; `description:` + on-demand for the rest.
- **Context injection**: always-apply rules are prepended to the session context; this is the
  primary persistent-memory mechanism (gald3r also uses `.gald3r/learned-facts.md` for durable
  project facts, surfaced at session start by `g-rl-25`).
- **Reference status**: ✅ verified.

---

## 8. MCP Support

- **Supported**: ✅ Yes.
- **Config format/location**: `.cursor/mcp.json` (JSON) OR Cursor Settings → MCP. In this repo
  there is **no** `.cursor/mcp.json`; MCP is configured via Cursor settings and/or a root
  `.mcp.json` (which is gitignored, machine-specific per `g-rl-02`).
- **Server discovery**: Cursor auto-connects to configured servers on startup.
- **Timeout behavior**: default MCP timeout is 60s; for long-running tools set
  `mcp.server.timeout: 600000` in Cursor settings.json.
- **Reference status**: ✅ verified (config mechanism); active server set is per-machine.

---

## 9. Known Gaps vs. Cursor Reference (baseline)

Cursor is the reference, so there are no "gaps vs. another platform." This section records the
small set of items that are **incomplete, deferred, or awaiting verification** within the Cursor
implementation itself — the honest baseline that feeds `PLATFORM_STATUS.md`:

1. **T600 HTTP hook parity** — the drop-in HTTP hook caller (`g-hk-http-event.ps1`) currently
   lives under `.claude/hooks/`; propagation to `.cursor/hooks/` is a documented follow-up.
2. **`block_on_failure` propagation** — `.cursor/hooks/g-hk-pre-commit.ps1` will honor
   `$env:GALD3R_HOOK_BYPASS=1` only once the T600 patch is propagated from `.claude/hooks/`.
3. **Per-machine MCP server set ❓** — the *mechanism* is verified ✅, but the concrete server
   list is machine-specific (no `.cursor/mcp.json` committed). Active servers untested in CI.
4. **SCAN_DOCS not yet run** — `last_doc_scan: never`. Doc-derived claims (exact rule frontmatter
   fields, any 2026 Cursor hook-event additions) should be confirmed by a future
   `@g-platform-scan-docs cursor` crawl of https://docs.cursor.com.
5. **Decision-tree placement** — per the Common vs. Platform-Specific decision tree (SKILL.md §4a),
   Cursor's `.mdc` rule format and `hooks.json` wiring are correctly classified as
   **platform-specific** (live in the Cursor tree, not common `.gald3r_sys/`).

---

## Capability Summary (copy into PLATFORM_STATUS.md row)

| Hooks | Rules | Skills | Commands | MCP | Docs Fresh |
|---|---|---|---|---|---|
| ✅ | ✅ | ✅ | ✅ | ✅ | ❓ |

Legend: ✅ verified working · ⚠️ partial / Cursor-generic · ❌ not supported · ❓ untested.

`Docs Fresh = ❓` because `last_doc_scan: never` — flip to ✅ after the first SCAN_DOCS crawl.

---

## Verification Evidence

| Capability | How verified |
|---|---|
| Folder hierarchy | Direct `ls` of `.cursor/` in this repo (rules/skills/agents/commands/hooks present) |
| Rules `.mdc` | 17 `g-rl-*.mdc` files confirmed in `.cursor/rules/` |
| Skills folder-per-skill | 110 `.cursor/skills/<name>/` folders confirmed |
| Commands | 174 `.cursor/commands/g-*.md` files confirmed |
| Agents | `.cursor/agents/g-agnt-*.md` + `sdk/`, `README.md`, `JOURNAL_FORMAT.md` confirmed |
| Hooks (native) | `.cursor/hooks.json` read directly — 4 events wired (sessionStart, stop, beforeShellExecution, preToolUse) with matchers and `_hook_md` |
| Hook companions (T1171) | `g-hk-*.md` files confirmed alongside `.ps1` in `.cursor/hooks/` |
| MCP | Mechanism documented (Cursor settings / `.cursor/mcp.json`); no committed `.cursor/mcp.json` — server set untested |
| Docs freshness | Not verified — `last_doc_scan: never`; pending `@g-platform-scan-docs cursor` |
