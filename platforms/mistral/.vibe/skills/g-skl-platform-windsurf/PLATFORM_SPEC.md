---
subsystem_memberships: [PLATFORM_INTEGRATION]
platform: windsurf
authoring_path: update
docs_url: https://docs.windsurf.com
docs_url_secondary:
  - https://docs.windsurf.com/windsurf/cascade/skills
  - https://docs.windsurf.com/windsurf/cascade/hooks
  - https://docs.windsurf.com/windsurf/cascade/workflows
  - https://docs.windsurf.com/windsurf/cascade/memories
  - https://docs.windsurf.com/windsurf/cascade/mcp
  - https://docs.windsurf.com/windsurf/cascade/cascade
crawl_max_age_days: 14
vault_doc_path: research/platforms/windsurf/
last_doc_scan: 2026-06-02
reference: g-skl-platform-cursor
status: ✅
task: T1466
---

# PLATFORM_SPEC.md — Windsurf (Cascade, by Cognition / Windsurf)

Windsurf is a VS Code-based AI-first IDE built around the **Cascade** agentic assistant. As of
mid-2026 Cascade natively supports **five** of the six gald3r-relevant extension primitives —
**Workflows (slash commands), Rules + Memories, Agent Skills (`SKILL.md`), Cascade Hooks, and
MCP** — with only **named user-defined sub-agents** absent (Cascade provides modes, Plan Mode, a
background planning agent, and Wave 13 parallel agents instead). Critically for gald3r, Cascade
discovers `SKILL.md` skills from **`.claude/skills/` and `.agents/skills/`** in addition to
`.windsurf/skills/`, and reads **`AGENTS.md`** as location-scoped rules, so gald3r's Claude-Code /
agents skill artifacts are **largely drop-in reusable** on Windsurf.

**Authoring path**: UPDATE. **Verified 2026-06-02** against https://docs.windsurf.com (see
Verification Evidence). This **supersedes** the prior spec (`last_doc_scan: never`) which
incorrectly marked hooks/skills/commands as unsupported — Skills, Hooks, and Workflows are now all
NATIVE in Cascade. The only honest gap vs. a Claude-Code-style platform is the **named sub-agent
primitive** (AGENTS = ⚠️).

> **Instruction-file convention:** Windsurf reads **`AGENTS.md`** (and legacy `.windsurfrules`) as
> Rules-engine input — it does **NOT** read `CLAUDE.md` as a primary instruction file the way the
> Claude-convention platforms do. Root-level `AGENTS.md` = always-on; subdirectory `AGENTS.md` =
> auto-glob. Durable shareable context belongs in `AGENTS.md` / `.windsurf/rules/`, NOT in the
> auto-generated, machine-local Memories store.

---

## 1. Folder Hierarchy

```
<project-root>/
├── AGENTS.md                       ← instruction file Cascade reads as Rules (root = always-on)
├── .windsurfrules                  ← legacy single-file project rules (still honored)
└── .windsurf/
    ├── rules/      *.md             ← per-rule files; activation: always_on / model_decision / glob / manual
    ├── workflows/  *.md             ← Workflows = /slash commands (manual-invoke, 12,000-char/file)
    ├── skills/     <name>/SKILL.md  ← Agent Skills (auto-invokable, progressive disclosure)
    └── hooks.json                   ← Cascade lifecycle hooks (12 events, bash + powershell keys)

~/.codeium/windsurf/                 ← user/global home (outside repo)
    ├── global_workflows/  *.md      ← global workflows
    ├── memories/global_rules.md     ← global rules (6,000-char) + Cascade auto-memories
    ├── skills/  <name>/SKILL.md      ← global skills
    ├── hooks.json                    ← user-level hooks
    └── mcp_config.json               ← Cascade MCP config (see §8)
```

Cascade **also** discovers skills in `.claude/skills/`, `~/.claude/skills/`, `.agents/skills/`, and
`~/.agents/skills/` — the **same `SKILL.md` files that work in Claude Code and Cursor work
unmodified**. Enterprise/system-level config (hooks, rules, workflows, skills) is supported via OS
paths (e.g. `C:\ProgramData\Windsurf\`, `/etc/windsurf/`, `/Library/Application Support/Windsurf/`),
with system overriding workspace/global for governance.

**gald3r writes**: `AGENTS.md` / `.windsurfrules`, `.windsurf/rules/*.md`, `.windsurf/workflows/*.md`,
`.windsurf/skills/<name>/SKILL.md`, `.windsurf/hooks.json` — or simply reuse the gald3r `.claude/skills/`
tree, which Cascade loads as-is.
**Windsurf owns**: the `.windsurf/` namespace, the rule activation-mode schema, the Cascade-managed
**Memories** store under `~/.codeium/windsurf/memories/` (machine-local, workspace-specific, does
**not** sync — not a gald3r-writable surface), and the workflow `/`-invocation mechanism.

---

## 2. AI Instruction File

Cascade's persistent-instruction surface is the **Rules engine**, fed by (in increasing locality):

- **`~/.codeium/windsurf/memories/global_rules.md`** — global user rules (6,000-char limit).
- **`AGENTS.md`** (project root) — read as an **always-on** rule; subdirectory `AGENTS.md` files are
  applied with **auto-glob** scoping. This is the first-class gald3r instruction input.
- **`.windsurfrules`** (project root) — legacy single-file always-apply rules; still honored.
- **`.windsurf/rules/*.md`** — per-rule files with explicit activation modes (see §7).

No `CLAUDE.md` is consumed. Docs explicitly recommend writing durable knowledge to `AGENTS.md` or
`.windsurf/rules/` rather than relying on auto-generated Memories. gald3r generates/merges `AGENTS.md`
(or `.windsurfrules`) from its always-apply rule subset; keep it within the per-file context budget.

---

## 3. Agents Support — ⚠️ PARTIAL

- Cascade offers **Code and Chat modes**, a background **planning agent** that refines the long-term
  plan, **Plan Mode** for structured task decomposition, and (Wave 13, mid-March 2026) **parallel
  multi-agent sessions** spawning **up to 5** autonomous agents in isolated git worktrees.
- **No user-definable named sub-agent primitive**: the docs describe no per-agent config file with
  its own instructions/tool allowlist comparable to Claude Code subagents or Cursor's
  `.cursor/agents/g-agnt-*.md`. Agent behavior is shaped via **Skills, Rules, and Workflows**, not
  first-class custom agent definitions.
- gald3r `g-agnt-*` personas therefore collapse to **Skill / Rule content**, not a selectable agent.
  This is the one true gap vs. the Cursor reference → rated **⚠️ partial** (real multi-agent
  capability, no named-persona config surface).
- Source: https://docs.windsurf.com/windsurf/cascade/cascade

## 4. Skills Support — ✅ NATIVE

- **Cascade Skills** — each skill is a directory containing a `SKILL.md` with YAML frontmatter
  (required: `name`, `description`), bundling reference scripts, templates, and checklists Cascade can
  invoke. **Progressive disclosure**: only `name`+`description` are loaded until Cascade auto-invokes
  by task relevance or the user `@mentions` the skill.
- Discovered in `.windsurf/skills/<name>/`, `~/.codeium/windsurf/skills/<name>/`, enterprise system
  paths, **and** `.claude/skills/`, `~/.claude/skills/`, `.agents/skills/`, `~/.agents/skills/` — the
  **same `SKILL.md` packs that work in Claude Code and Cursor load unmodified**.
- gald3r `g-skl-*/SKILL.md` load natively — including straight from `.claude/skills/`.
- Source: https://docs.windsurf.com/windsurf/cascade/skills

## 5. Commands / Workflows — ✅ NATIVE

- **Workflows** = markdown files in `.windsurf/workflows/*.md` (global at
  `~/.codeium/windsurf/global_workflows/*.md`; system/enterprise paths also supported), invoked in
  Cascade via a slash command `/[name-of-workflow]`. Each workflow is a **series of steps** Cascade
  follows. **Manual-only** (Cascade never auto-invokes a workflow — that is Skills' job). **12,000-char**
  limit per file.
- gald3r's `@g-*` / `/g-*` command catalog maps to workflow files (`/<name>` slash-invoked). Note the
  Workflows-vs-Skills split: **Workflows = manual `/`-invoked scripts; Skills = auto-invokable
  multi-step capabilities** — pick the surface per command's intended trigger.
- Source: https://docs.windsurf.com/windsurf/cascade/workflows

## 6. Hooks System — ✅ NATIVE

- **Cascade Hooks** — shell commands that run automatically on Cascade lifecycle actions, defined in
  **`hooks.json`** at system / user (`~/.codeium/windsurf/hooks.json`) / workspace
  (`.windsurf/hooks.json`) levels (merged). **12 events**: `pre_read_code`, `post_read_code`,
  `pre_write_code`, `post_write_code`, `pre_run_command`, `post_run_command`, `pre_mcp_tool_use`,
  `post_mcp_tool_use`, `pre_user_prompt`, `post_cascade_response`,
  `post_cascade_response_with_transcript`, `post_setup_worktree`.
- Hooks receive **JSON context on stdin**; **pre-hooks can BLOCK** an action by exiting with **exit
  code 2**. Each hook supports a **`command`** (bash) key **and** a **`powershell`** key, plus
  `show_output` / `working_directory` — so gald3r `g-hk-*.ps1` PowerShell hooks wire **natively**
  (session/prompt context injection via `pre_user_prompt`, `.gald3r/` write guards via
  `pre_write_code`, command guards via `pre_run_command`, worktree setup via `post_setup_worktree`).
- Source: https://docs.windsurf.com/windsurf/cascade/hooks

## 7. Rules / Memory — ✅ NATIVE

- **Rules** are developer-authored instructions stored as **`.windsurf/rules/*.md`** (one file per
  rule, up to **12,000 chars** each, each with its own activation mode), plus legacy `.windsurfrules`
  (root) and global `~/.codeium/windsurf/memories/global_rules.md` (**6,000-char** limit). Cascade also
  reads `AGENTS.md` (§2) through the same Rules engine.
- **Four activation modes**: `always_on`, `model_decision`, `glob`, `manual` (`@rule-name`). The
  extension is **`.md`** (vs. Cursor's `.mdc`) — the parity sync maps the extension. These modes are the
  Windsurf analog of Cursor's `alwaysApply:` / `globs:` / `description:`.
- **Memories** are auto-generated, **machine-local, workspace-specific, and do NOT sync**; for durable
  shareable context the docs recommend Rules or `AGENTS.md` instead. Memories are Cascade-managed, not
  gald3r-authored.
- gald3r `g-rl-*` map to `always_on` (for `alwaysApply: true`), `glob` (for `globs:`-scoped), or
  `model_decision` (for `description:`-scoped) rule files.
- Source: https://docs.windsurf.com/windsurf/cascade/memories

## 8. MCP Support — ✅ NATIVE

- MCP servers extend Cascade's capabilities, configured via **`~/.codeium/windsurf/mcp_config.json`**
  (`mcpServers` object: `command`/`args`/`env`) or the one-click **MCP Marketplace** in the Cascade
  panel. Supports **stdio** and **Streamable HTTP** transports. Per-tool toggling enables specific
  tools; **hard limit of 100 active tools** in Cascade's MCP panel.
- Config file name/location (`mcp_config.json` under `~/.codeium/windsurf/`) **differs** from Cursor's
  `.cursor/mcp.json` — MCP is fully supported but **not single-path portable**; gald3r cannot ship one
  `mcp.json` that both Cursor and Windsurf read.
- Source: https://docs.windsurf.com/windsurf/cascade/mcp

## 9. Other Extensibility / Notable

- **VS Code / Cursor extension compatibility**: Windsurf imports VS Code / Cursor extensions (AI
  code-complete and certain proprietary extensions excluded).
- **Enterprise system-level governance**: hooks, rules, workflows, and skills can be set at OS
  system paths (`C:\ProgramData\Windsurf\`, `/etc/windsurf/`, `/Library/Application Support/Windsurf/`)
  with system overriding workspace/global.
- **Workflows vs. Skills**: Workflows are the manual `/`-invoked complement; Skills are the
  auto-trigger complement. Cross-tool skill discovery in `.claude/skills` / `.agents/skills` makes
  gald3r `SKILL.md` packs drop-in compatible.

---

## Parity vs. Cursor Reference

Windsurf now reaches **near-full parity** with the Cursor reference (`g-skl-platform-cursor`): native
**commands (Workflows), rules, skills, hooks, and MCP**. The single caveat is **agents** — Cascade
provides modes, Plan Mode, a planning agent, and Wave 13 parallel agents (up to 5) but **no
user-definable named sub-agent file**, so gald3r `g-agnt-*` personas surface as Skill/Rule content
(⚠️). The Cascade-managed **Memories** layer is a Windsurf-native bonus with no Cursor analog —
machine-local recall, not a gald3r-writable store.

**Reuse note (important):** because Cascade reads `AGENTS.md` and discovers `.claude/skills/` +
`.agents/skills/` trees, gald3r's **Skill artifacts are largely reusable on Windsurf without a
separate port** — the cheapest path to a high-parity Windsurf install is to ship the gald3r
`.claude/skills/` tree (+ `AGENTS.md`) and add `.windsurf/workflows/` + `.windsurf/hooks.json` for the
command and hook surfaces. Note Windsurf reads `AGENTS.md`, **not** `CLAUDE.md`.

## Hook System

- **Type**: native (`hooks.json`)
- **Config file**: `.windsurf/hooks.json` (workspace), `~/.codeium/windsurf/hooks.json` (user), system path (merged)
- **Events available**: pre_read_code, post_read_code, pre_write_code, post_write_code, pre_run_command, post_run_command, pre_mcp_tool_use, post_mcp_tool_use, pre_user_prompt, post_cascade_response, post_cascade_response_with_transcript, post_setup_worktree (12 total)
- **Event payload format**: JSON via stdin; pre-hooks BLOCK via exit code 2
- **Command extensions**: `command` (bash) key **and** `powershell` key per hook (+ `show_output`, `working_directory`) — PowerShell supported
- **gald3r hook files**: `g-hk-*.ps1` wire natively via the `powershell` key on the events above

## Atypical Handling

- Instruction file is **`AGENTS.md`** (and legacy `.windsurfrules`), **not** `CLAUDE.md` — Cascade
  reads it through the Rules engine (root = always-on, subdir = auto-glob).
- **Memories** (`~/.codeium/windsurf/memories/`) are auto-generated, machine-local, and do **not**
  sync — never treat them as a shippable gald3r surface; use `AGENTS.md` / `.windsurf/rules/` instead.
- **Workflows ≠ Skills**: Workflows are manual `/`-invoked; Skills auto-invoke. Map gald3r commands to
  Workflows and gald3r skills to Skills accordingly.
- Rule files use `.md` (not Cursor's `.mdc`); MCP config path (`mcp_config.json`) is Windsurf-specific.

## gald3r Integration Notes

- Ship gald3r's `.claude/skills/` tree (Cascade discovers it) + `.windsurf/workflows/` for commands +
  `.windsurf/hooks.json` (with `powershell` keys) for hooks; write instructions to `AGENTS.md`.
- Hooks fire natively (`powershell` key supported) — no need to degrade session/pre-commit hooks to
  manual or to git `core.hooksPath`.
- `g-agnt-*` personas have no native agent file — express them as Skills/Rules until Windsurf ships a
  named sub-agent primitive.
- Re-verify on the next `@g-platform-scan-docs windsurf` (crawl_max_age_days: 14).

---

## Capability Summary (copy into PLATFORM_STATUS.md row)

| Hooks | Rules | Skills | Commands | MCP | Docs Fresh |
|---|---|---|---|---|---|
| ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |

Legend: ✅ verified working · ⚠️ partial / Cursor-generic · ❌ not supported · ❓ untested.

Rationale (agents tracked separately from the 5-column summary):
- **Hooks ✅** — native `hooks.json`, 12 lifecycle events, `powershell` key fires gald3r `g-hk-*.ps1`; pre-hooks block via exit code 2.
- **Rules ✅** — `.windsurf/rules/*.md` (4 activation modes, 12,000-char) + `AGENTS.md` + legacy `.windsurfrules` + global_rules.md.
- **Skills ✅** — Cascade Skills `SKILL.md`; discovers `.claude/skills/` + `.agents/skills/` → gald3r packs install verbatim.
- **Commands ✅** — Workflows `.windsurf/workflows/*.md`, `/`-invoked (manual; 12,000-char); maps gald3r `g-*` commands.
- **MCP ✅** — `~/.codeium/windsurf/mcp_config.json` + Marketplace; stdio + Streamable HTTP; 100-tool cap (Windsurf-specific path).
- **Agents ⚠️** — modes/Plan Mode/planning agent/Wave 13 parallel agents (up to 5), but no named sub-agent config file.
- **Docs Fresh ✅** — re-crawled 2026-06-02 against https://docs.windsurf.com.

---

## Verification Evidence (docs crawl 2026-06-02, https://docs.windsurf.com)

| Capability | How verified |
|---|---|
| Instruction file | /windsurf/cascade/memories — Cascade reads `AGENTS.md` as Rules (root always-on, subdir auto-glob); legacy `.windsurfrules`; NOT `CLAUDE.md` |
| Commands | /windsurf/cascade/workflows — Workflows `.windsurf/workflows/*.md`, `/[name]` slash-invoked, manual-only, 12,000-char; global `~/.codeium/windsurf/global_workflows/` |
| Rules | /windsurf/cascade/memories — `.windsurf/rules/*.md` (always_on/model_decision/glob/manual, 12,000-char), `global_rules.md` (6,000-char); Memories are local-only |
| Agents | /windsurf/cascade/cascade — Code/Chat modes, planning agent, Plan Mode, Wave 13 parallel agents (≤5 in worktrees); NO named sub-agent config primitive → partial |
| Skills | /windsurf/cascade/skills — Cascade Skills `SKILL.md` (name+description); discovered in `.windsurf` / `.claude` / `.agents` skills dirs; progressive disclosure |
| Hooks | /windsurf/cascade/hooks — `hooks.json` (workspace/user/system); 12 events; stdin JSON; pre-hooks block on exit code 2; `command` (bash) + `powershell` keys |
| MCP | /windsurf/cascade/mcp — `~/.codeium/windsurf/mcp_config.json` + Marketplace; stdio + Streamable HTTP; 100-tool hard limit |
| Cross-compat | Cascade discovers `.claude/skills/` + `.agents/skills/` and reads `AGENTS.md` → gald3r Skill artifacts reusable (path differs from Cursor `.cursor/mcp.json`) |
