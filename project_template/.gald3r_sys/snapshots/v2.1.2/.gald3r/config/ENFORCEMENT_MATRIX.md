---
gald3r_rel_version: "2.2.0"
schema_version: "generic-v1"
title: gald3r Enforcement Matrix
purpose: Audit-and-design surface for migrating hard-constraint rules from context-injected always-apply text (~70% agent compliance) to hooks (~100% mechanical enforcement).
owner_task: T997
status: audit-complete; hook-implementation-shipped (claude+cursor); per-platform parity per coverage table
created: 2026-05-10
last_updated: 2026-05-10
---

# gald3r Enforcement Matrix

## Background

Research finding (<gald3r_source> empirical observation across 2026-04 / 2026-05 autopilot runs):

| Enforcement surface | Compliance |
|---|---|
| Context-injected text (CLAUDE.md, always-apply `.mdc`/`.md` rule files) | **~70%** — agents read but occasionally drift, especially under context pressure |
| Hooks (PowerShell scripts invoked by the IDE harness around tool calls) | **~100%** — mechanical execution; runs regardless of what the agent "decides" |

For constraints that **MUST NEVER be violated** (data-loss, marker-only invariant, PRD freeze, secret leak), context-injected enforcement is insufficient. These constraints belong at the hook layer.

## Classification scheme

Each always-apply rule is classified one of three ways:

| Class | Meaning | Enforcement target |
|---|---|---|
| `advisory` | Guidance/style/preference. Violation is suboptimal but not unsafe. | Rule file only. No hook. |
| `hard-constraint` | Must never be violated. Violations cause data loss, audit-trail damage, leaked secrets, or framework drift. | Rule file (human-readable) + hook (mechanical enforcement). |
| `mixed` | Contains both advisory and hard-constraint sections. Hard-constraint portion must be hook-backed. | Rule file + hook (for the hard-constraint portion). |

The rule text is **never deleted** when a constraint is migrated to a hook. Humans still read rules; hooks enforce them. The rule file documents the contract; the hook makes it true.

## Audit — always-apply rule files

Scanned: `.claude/rules/*.md` and `.cursor/rules/*.mdc` (15 files each; pairs are content-equivalent across IDE platforms; the catchall is the primary parity surface).

| Rule | Title | Class | Why | Existing hook coverage | Gap |
|---|---|---|---|---|---|
| `g-rl-00-always.md` | Response footer + file-size nag + UV + freshness | `advisory` | Style + tool-choice nudges. No data risk. | none needed | none |
| `g-rl-01-documentation.md` | docs/ folder placement + timestamped filenames | `advisory` | Cosmetic organisation. Violation = misplaced file, not unsafe. | none needed | none |
| `g-rl-02-git_workflow.md` | Commit message format + **Protected Files** list + worktree rules + pre-commit/pre-push gates | `mixed` | Format is advisory; **Protected Files (no .env / no AGENTS.md / no .gald3r/ committed) is a hard-constraint** | `g-hk-pre-commit.ps1` (pattern scan); `g-hk-pre-push.ps1`; `gald3r_push_gate.ps1` | Pre-commit hook should explicitly reject every Protected Files entry by glob, not rely on agent diff inspection. Today the hook scans for secret patterns but not for the full Protected Files allowlist. |
| `g-rl-04-code_reusability.md` | DRY 3-strike rule + folder conventions | `advisory` | Code quality nudges. Reviewable post-hoc. | none needed | none |
| `g-rl-08-powershell.md` | PowerShell command-separator + curl alias notes | `advisory` | Tool-choice guidance. Wrong syntax fails immediately and is self-correcting. | none needed | none |
| `g-rl-09-python_venv.md` | UV venv + dependency sync | `advisory` | Code-style and dependency hygiene. Violations show up in next install. | none needed | none |
| `g-rl-25-gald3r_session_start.md` | Session start display + sync validation + WPAC inbox surface | `mixed` | Display is advisory; **WPAC INBOX conflict gate is a hard-constraint** (must block claims/coding when an open conflict exists) | `g-hk-wpac-inbox-check.ps1` (`-BlockOnConflict` exit code 2); wired into `g-go-go`, `g-go`, `g-go-code`, `g-go-review` commands; sessionStart hook can surface but does not currently block tool calls | Pre-tool-call hook (planned) should re-check WPAC INBOX conflict state and refuse `Edit`/`Write` on `.gald3r/` paths while an unresolved `[CONFLICT]` exists. Today this is command-internal only. |
| `g-rl-26-readme-changelog.md` | Update CHANGELOG/README at feature boundary | `advisory` | Doc hygiene. Missing CHANGELOG entry is a review-time fail, not a runtime hazard. | review-time only | none (review owns it) |
| `g-rl-33-enforcement_catchall.md` | The catchall: error reporting, mandatory commit offer, **`.gald3r/` folder gate**, **PRD freeze gate (C-019)**, WPAC INBOX gate, **Clean Controller Gate**, gald3r housekeeping commit gate, **WPAC priority floor**, WPAC outbound tracking, code-change-enforcement, delegation hints | `hard-constraint` (multiple) | This file is the central hard-constraint document. Multiple sub-rules are data-loss-risky if violated. | Partial: `g-hk-pre-commit.ps1` (secret scan); `gald3r_housekeeping_commit.ps1`; `gald3r_push_gate.ps1`; `g-hk-wpac-inbox-check.ps1` (WPAC). **No `.gald3r/` write guard hook.** **No PRD freeze hook.** **No code-change-vs-task-id check at pre-commit.** | **Major gap** — see next section. |
| `g-rl-34-todo_completion_gate.md` | Stub/TODO annotation + follow-up task creation | `mixed` | Stub annotation is hard-constraint at task completion (`[🔍]` gate); discovery is advisory at any other time. | task verifier runs at `g-go-review`; no hook | A pre-commit hook scanning for bare `# TODO` / `pass` / `raise NotImplementedError` without the `TODO[TASK-X→TASK-Y]` form would surface unannotated stubs deterministically. |
| `g-rl-35-bug-discovery-gate.md` | Pre-existing bug logging + `BUG[BUG-{id}]` annotation | `advisory` | Bug discovery is an agent-judgement step. Hook can't easily detect "what is a pre-existing bug". | none needed | none |
| `g-rl-36-workspace-member-gald3r-guard.md` | Workspace-Control member `.gald3r/` MUST be marker-only (`.identity` + `PROJECT.md` only) | `hard-constraint` | Violation = control-plane drift, framework integrity loss. BUG-021 was filed for exactly this case. | `.claude/skills/g-skl-workspace/scripts/check_member_repo_gald3r_guard.ps1` invoked from skills (`g-skl-workspace`, `g-skl-setup`, `g-skl-wpac-spawn`, `g-skl-wpac-adopt`); `.claude/skills/g-skl-workspace/scripts/validate_workspace_members_gald3r.ps1` for audit | **No pre-tool-call hook.** Today the guard is called from skill code paths only — direct `Write`/`Edit` to a member `.gald3r/` path bypasses it. A pre-tool-call hook that recognises `<member>/.gald3r/<not-marker>` paths and refuses the write closes this. |
| `g-rl-37-think-in-code.md` | Use a single script when 3+ tool calls would do the same work | `advisory` | Token-efficiency guidance. No safety risk. | none needed | none |
| `rally.md` | Rally HTTP API conventions | `advisory` | Operational guidance for an internal task tracker. | none needed | none |
| `silicon_valley_personality.md` | Persona rule | `advisory` | Cosmetic. | none needed | none |

## The hard-constraint shortlist

These five constraints need hook-backed enforcement. They are the explicit Phase-2 implementation work for this task (AC2-AC6):

| Constraint | Source | Current state | Proposed hook | Hook type |
|---|---|---|---|---|
| **`.gald3r/` write guard** (no agent writes to `.gald3r/` without an active gald3r agent/skill) | g-rl-33 § ".gald3r/ Folder Gate" | Context-only | `g-hk-pre-tool-call-gald3r-guard.ps1` — inspects tool name + target path + active agent/skill ID; refuses unsupervised `Edit`/`Write` to `.gald3r/` | pre-tool-call |
| **PRD freeze gate (C-019)** (released/superseded PRDs are immutable; only `@g-prd-revise` may touch them) | g-rl-33 § "PRD Freeze Gate" | Context-only | `g-hk-pre-tool-call-prd-freeze.ps1` — on any `Edit`/`Write` targeting `.gald3r/prds/prdNNN_*.md`, reads YAML `status:`; refuses if `released`/`superseded`; allows only via `@g-prd-revise` flow | pre-tool-call |
| **Member `.gald3r/` marker-only invariant** (workspace member repos may keep ONLY `.identity` + `PROJECT.md`) | g-rl-36 | Skill-code paths only; direct tool calls bypass | `g-hk-pre-tool-call-member-gald3r-guard.ps1` — recognises `<workspace_member>/.gald3r/<not-marker>` path patterns from the workspace manifest; refuses with the existing guard helper exit message | pre-tool-call |
| **Protected Files commit guard** (never commit `.env`, `AGENTS.md`, `CLAUDE.md`, `.cursor/`, `.gald3r/`, etc.) | g-rl-02 § "Protected Files" | Partial — secret-pattern scan only | `g-hk-pre-commit.ps1` extension — full Protected Files allowlist scan, not just secret regex | pre-commit (existing hook, extend) |
| **Stub/TODO commit guard** (no bare `# TODO`, `pass`, `raise NotImplementedError` in staged commits without `TODO[TASK-X→TASK-Y]` annotation) | g-rl-34 | Review-time only | `g-hk-pre-commit.ps1` extension — staged-diff scan for bare-stub patterns missing the annotation form | pre-commit (existing hook, extend) |

## Implementation pathway — shipped 2026-05-11 (T997 AC2-AC6)

Live PowerShell implementation landed in this commit. The contract is identical across platforms; per-platform wiring varies (see coverage table below).

**Files shipped:**

| Hook | Path | Type | ACs |
|---|---|---|---|
| `.gald3r/` write guard | `.claude/hooks/g-hk-pre-tool-call-gald3r-guard.ps1` (+ .cursor / .agent / .codex parity) | pre-tool-call | AC5 |
| PRD freeze gate | `.claude/hooks/g-hk-pre-tool-call-prd-freeze.ps1` (+ parity) | pre-tool-call | AC6 |
| Member marker-only guard | `.claude/hooks/g-hk-pre-tool-call-member-gald3r-guard.ps1` (+ parity) | pre-tool-call | AC2 |
| Protected Files allowlist | `.claude/hooks/g-hk-pre-commit.ps1` § "PROTECTED FILES ALLOWLIST" (+ parity) | pre-commit (extended) | AC4 |
| Stub annotation guard | `.claude/hooks/g-hk-pre-commit.ps1` § "STUB / TODO ANNOTATION" (+ parity) | pre-commit (extended) | AC5 (g-rl-34) |

**Hook contract** (matches `g-hk-validate-shell.ps1` precedent):

- **stdin**  : JSON `{ tool_name, tool_input: { file_path | path | ... } }`
- **exit 0** : allow  (body: `{"permission":"allow"}`)
- **exit 2** : deny   (body: `{"permission":"deny", "user_message":"...", "agent_message":"..."}`)

Refusal messages reference the relevant rule path (`.claude/rules/g-rl-NN-...md`) so the human can read the contract being enforced.

**Bypass switches** (for emergency parity / bootstrap flows):

| Switch | Effect |
|---|---|
| `$env:GALD3R_HOOK_BYPASS = '1'` | All gald3r hooks treat BLOCK as WARN (T600 §3.3 user override). |
| `$env:GALD3R_ACTIVE_AGENT = '<agent_id>'` | `.gald3r/` write guard treats the call as an active agent invocation. |
| `$env:GALD3R_PRD_REVISE_ACTIVE = '1'` | PRD freeze gate allows the write (set only by `@g-prd-revise`). |
| `$env:GALD3R_MARKER_INIT_ACTIVE = '1'` | Member marker-only guard allows writing `.identity` / `PROJECT.md` during bootstrap. |

**Per-IDE wiring** (AC7):

| IDE | hooks.json schema | preToolUse wired | PreToolUse wired | Pre-commit hook | Phase-1 status |
|---|---|---|---|---|---|
| Claude Code (`.claude/hooks.json`) | Cursor-style + Claude PascalCase | ✅ (camelCase) | ✅ (PascalCase) | ✅ extended | shipped |
| Cursor (`.cursor/hooks.json`) | Cursor-style camelCase | ✅ | n/a | ✅ extended | shipped (preToolUse depends on Cursor harness firing it; Cursor's documented hook events do not include a write-time pre-tool-call as of late 2025 — see "Cross-platform footnote") |
| Codex (`.codex/hooks/`) | scripts present; no hooks.json | scripts callable manually | scripts callable manually | ✅ extended (script copied) | scripts-ready; harness wiring TBD |
| Gemini / Antigravity (`.agent/hooks/`) | scripts present; no hooks.json | scripts callable manually | scripts callable manually | ✅ extended (script copied) | scripts-ready; harness wiring TBD |
| OpenCode (`.opencode/hooks/`) | no hooks.json (per learned fact #47 OpenCode has no native hooks) | n/a | n/a | ✅ extended (script copied for manual invocation) | scripts-only; documented gap |
| GitHub Copilot (`.copilot/`) | no hooks (per learned fact #49 Copilot Phase 1 has no hooks) | n/a | n/a | n/a | documented gap; Phase 2 awaits example_app public MCP URL |

Cursor's documented hook events as of late 2025 are `sessionStart`, `stop`, `beforeShellExecution`, `beforeReadFile`, `beforeSubmitPrompt`, `beforeMCPExecution`, `afterFileEdit`. There is no documented `beforeFileWrite` event in Cursor — meaning Cursor's harness cannot today auto-refuse an `Edit`/`Write` tool call via these hooks. The `preToolUse` key in `.cursor/hooks.json` is forward-looking: if Cursor adds tool-arg introspection, the wiring is already in place. Until then, the same Cursor-side enforcement falls back to context-injected rules + the pre-commit extensions. Claude Code's `PreToolUse` event is the only platform-supported tool-arg-introspecting hook surface today.

**Validated** via standalone invocation in T997 ITER 3 (2026-05-11):

- `g-hk-pre-tool-call-gald3r-guard.ps1` correctly denies `Write` to `.gald3r/test.md`, allows with `GALD3R_ACTIVE_AGENT` set, allows non-`.gald3r/` paths.
- `g-hk-pre-tool-call-prd-freeze.ps1` correctly denies `Edit` on a `released` PRD fixture, allows with `GALD3R_PRD_REVISE_ACTIVE`, allows draft PRDs, allows non-PRD paths.
- `g-hk-pre-tool-call-member-gald3r-guard.ps1` correctly denies `Write` to a member's `.gald3r/TASKS.md`, allows the member marker pair, allows controller `.gald3r/` writes, allows non-`.gald3r/` paths.

## Rule → hook coverage summary (post-T997 implementation 2026-05-11)

| Rule ID | Coverage | Notes |
|---|---|---|
| g-rl-00 | n/a (advisory) | — |
| g-rl-01 | n/a (advisory) | — |
| g-rl-02 | **shipped** — pre-commit hook now enforces full Protected Files allowlist (15+ patterns) + existing secret regex | `g-hk-pre-commit.ps1` § "PROTECTED FILES ALLOWLIST" (AC4) |
| g-rl-04 | n/a (advisory) | — |
| g-rl-08 | n/a (advisory) | — |
| g-rl-09 | n/a (advisory) | — |
| g-rl-25 | partial — WPAC INBOX hook surfaces conflicts; pre-tool-call extension not yet wired | Future: extend `g-hk-pre-tool-call-gald3r-guard.ps1` to re-check INBOX conflict state when an active CONFLICT exists |
| g-rl-26 | review-time | n/a |
| g-rl-33 (.gald3r/ guard) | **shipped** | `g-hk-pre-tool-call-gald3r-guard.ps1` (AC5) — refuses unsupervised Edit/Write to `.gald3r/`; bypassable via `GALD3R_ACTIVE_AGENT` env var |
| g-rl-33 (PRD freeze C-019) | **shipped** | `g-hk-pre-tool-call-prd-freeze.ps1` (AC6) — refuses Edit/Write to released/superseded PRDs; bypassable via `GALD3R_PRD_REVISE_ACTIVE` env var |
| g-rl-33 (Clean Controller Gate) | **partial** — `gald3r_housekeeping_commit.ps1` handles housekeeping classification; full clean check is command-internal | Acceptable: command-internal gate is sufficient for orchestration roots; agents that bypass commands are bypassing all gates anyway |
| g-rl-34 (stub annotation) | **shipped** | `g-hk-pre-commit.ps1` § "STUB / TODO ANNOTATION" — staged-diff scan rejects bare `# TODO`, `// TODO`, `raise NotImplementedError`, etc. without the `TODO[TASK-X→TASK-Y]` form |
| g-rl-35 | n/a (judgement) | — |
| g-rl-36 (member marker-only) | **shipped** | `g-hk-pre-tool-call-member-gald3r-guard.ps1` (AC2) — refuses Edit/Write to any member `.gald3r/` path that is not `.identity` or `PROJECT.md`; bypassable via `GALD3R_MARKER_INIT_ACTIVE` env var |
| g-rl-37 | n/a (advisory) | — |
| rally | n/a (operational) | — |
| silicon-valley | n/a (cosmetic) | — |

## Cross-platform footnote

This matrix is written from `<gald3r_source>` (Claude Code orientation). Hook parity across the other five IDE platforms is part of the Phase-2 implementation work, not this audit. The audit findings (which rules are hard vs advisory) are platform-neutral.

## Related

- Task: T997 (this audit)
- Follow-up implementation task: T1008 (to be filed when this audit is verified)
- Subsystems: `g-go-orchestration`, `hook-system`, `rule-system`, `gald3r-templates`
- Source rules: `.claude/rules/g-rl-*.md` (and `.cursor/rules/g-rl-*.mdc` parity copies)
- Existing hooks: `.claude/hooks/g-hk-*.ps1` (and `.cursor/hooks/g-hk-*.ps1` parity)
- Hook wiring: `.claude/hooks.json`, `.cursor/hooks.json`
- Guard helpers: `.claude/skills/g-skl-workspace/scripts/check_member_repo_gald3r_guard.ps1`, `.claude/skills/g-skl-git-commit/scripts/gald3r_push_gate.ps1`, `.claude/skills/g-skl-git-commit/scripts/gald3r_housekeeping_commit.ps1`
