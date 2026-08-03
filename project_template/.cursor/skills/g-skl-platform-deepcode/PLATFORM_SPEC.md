---
subsystem_memberships: [PLATFORM_INTEGRATION]
platform: deepcode
authoring_path: update
docs_url: https://github.com/lessweb/deepcode-cli
docs_url_secondary:
  - https://raw.githubusercontent.com/lessweb/deepcode-cli/main/docs/mcp.md
  - https://raw.githubusercontent.com/lessweb/deepcode-cli/main/docs/configuration.md
  - https://api-docs.deepseek.com/quick_start/agent_integrations/deepcode
crawl_max_age_days: 14
vault_doc_path: research/platforms/deepcode/
last_doc_scan: 2026-07-18
reference: g-skl-platform-cursor
status: ⚠️
task: T387
---

# PLATFORM_SPEC.md — Deep Code CLI (lessweb/deepcode-cli)

> **Authoring status**: `update` (T387, closes the T516 all-`❓` stub — the owner directive was
> *"DeepCode - if it can be made to work, keep otherwise I am ok removing"*; this spec is the
> **verdict: keep, fixed**). Verified live on 2026-07-18 directly against the project's GitHub
> README, `docs/mcp.md`, and `docs/configuration.md` (raw fetch, not cached), cross-checked
> against DeepSeek's own `api-docs.deepseek.com` integration page. This independently re-confirms
> (and refreshes) an earlier 2026-06-02 verification found in the retired `gald3r_templates_dev`
> donor tree (task T1474) — the two scans agree on every capability cell.

**Deep Code** (`@vegamo/deepcode-cli` on npm, `lessweb/deepcode-cli` on GitHub) is a real,
actively-maintained, **third-party community** terminal AI coding assistant optimized for the
`deepseek-v4` model family. DeepSeek's own docs site lists it under "Agent Integrations" with an
explicit disclaimer: *"This agent is provided entirely by a third party ... we assume no
responsibility for it."* This matches the 2026-07-16 PLATFORM_TEMPLATE_REVIEW's framing — an
obscure community CLI, not a major platform — but it is a **real, installable, documented tool**
with a genuine gald3r-relevant config surface, not a doc-only or nonexistent project.

Deep Code natively supports **three** of the six gald3r-relevant extension primitives — **rules**
(via an `AGENTS.md` instruction file), **Agent Skills**, and **MCP** — while **custom commands**
are limited to a fixed built-in slash set (partial), and **subagents** and a **lifecycle hook
system** are **absent**.

---

## 1. Folder Hierarchy

```
<project-root>/
├── AGENTS.md                        ← instruction file Deep Code reads (scaffolded via /init)
└── .agents/
    └── skills/  <name>/SKILL.md     ← Agent Skills (project scope, cross-client interop path)

<project-root>/.deepcode/            ← Deep Code project-scope config
├── settings.json                    ← model/env + mcpServers + notify + thinking/reasoning
└── skills/      <name>/SKILL.md     ← Deep Code's own native project skills path

~/                                    (user/home scope)
├── .deepcode/settings.json          ← global config — SHARED with the Deep Code VSCode extension
└── .agents/skills/ <name>/SKILL.md  ← user-global Agent Skills (interop path)
```

Per the live README's own documented scan priority (project native `.deepcode/skills/` first,
project interop `.agents/skills/` second, then the user-scope equivalents), **both** the native
and interop project skill paths are read — gald3r targets **`./.agents/skills/<name>/SKILL.md`**
(the cross-client Agent-Skills convention shared with every other gald3r-supported Agent-Skills
tool), which Deep Code resolves natively as its documented second-priority project skills path.

**Settings-file scope layering** (per `docs/configuration.md`): `<project_root>/.deepcode/
settings.json` **overrides** `~/.deepcode/settings.json` **field-by-field** (not a whole-file
replace) — confirmed by the doc's own per-field priority tables (e.g. `MODEL`: hardcoded default →
user settings.json → project settings.json → env var). A project-level `settings.json` containing
only `mcpServers` is therefore a valid, additive file that does not clobber the user's own
model/API-key configuration.

**gald3r writes**: `AGENTS.md` (once T385's central per-platform instruction-file emission lands —
see Rules/Memory below), `.agents/skills/<name>/SKILL.md`, and a minimal MCP registration inside
`.deepcode/settings.json` (`mcpServers.gald3r`, not a standalone `.mcp.json` — see MCP Support and
BUG note below).
**Deep Code owns**: the rest of the `settings.json` schema (model, env, thinking/reasoning,
notify, webSearchTool, telemetry, permissions), the built-in slash-command set, and the
fine-grained shell/file/network permission framework.

---

## 2. AI Instruction File

Deep Code reads **`AGENTS.md`** as its persistent, always-on instruction/context file —
**scaffolded by the `/init` command** (live README slash-command table: `/init` → *"初始化
AGENTS.md 文件"*, i.e. "initializes the AGENTS.md file"). There is **no `CLAUDE.md` read** and
**no separate `rules/`/`memory/` directory** — `AGENTS.md` is the single instruction surface.
gald3r's `AGENTS.md` is therefore a first-class input; `CLAUDE.md` is **not** consumed.

---

## 3. Agents Support — ❌ NONE

- Deep Code operates as a **single AI assistant**. No sub-agents, agent roles, or distinct agent
  modes are documented in the live README or DeepSeek's integration page.
- `thinkingEnabled` / `reasoningEffort` are **model settings**, not agent roles — no `g-agnt-*`
  parity target exists. Fold agent behavior into `AGENTS.md` instructions or per-skill `SKILL.md`
  context instead.
- Source: https://github.com/lessweb/deepcode-cli (live README, 2026-07-18 fetch)

## 4. Skills Support — ✅ NATIVE

- **Agent Skills** (open `SKILL.md` standard) discovered from, in scan-priority order: project
  `./.deepcode/skills/` (native) → project `./.agents/skills/` (cross-client interop) → user
  `~/.deepcode/skills/` (native) → user `~/.agents/skills/` (interop). Activate via the **`/`**
  skill/command picker or by typing the skill name.
- `settings.json`'s `enabledSkills` field can selectively hide a skill by resolved name across
  both project and user scope (project overrides user, per-skill).
- gald3r `g-skl-*/SKILL.md` loads natively at `.agents/skills/` — confirmed live, current.
- Source: live README (`docs/mcp.md`/`docs/configuration.md` corroborate `enabledSkills`),
  2026-07-18 fetch.

## 5. Commands / Workflows — ⚠️ PARTIAL

- **Built-in slash commands only**: `/new`, `/resume`, `/continue`, `/model`, `/raw`, `/init`,
  `/skills`, `/mcp`, `/undo`, `/exit`; the skill/command picker opens with **`/`**.
- **No mechanism for user-defined custom commands** is documented — there is **no**
  `.deepcode/commands/` (or equivalent) directory. gald3r `@g-*` / `/g-*` commands have **no**
  native slash-command target; surface them as **skills** instead (each skill is invocable via the
  `/` picker).
- Source: live README, 2026-07-18 fetch.

## 6. Hooks System — ❌ NONE

- **No lifecycle/event hook system** — no session-start, pre-tool, pre-commit, or file-watch hook
  framework.
- The only automation is the **`notify`** field in `settings.json`: *"a Shell script path executed
  automatically after each AI turn completes"* — a **post-turn-only** callback (receives
  `DURATION`/`STATUS`/`FAIL_REASON`/`BODY`/`TITLE` as env vars), it **cannot block** tool calls,
  inject session-start context, or gate commits.
- gald3r `g-hk-*.py` hooks have **no native wiring**; the `notify` script can at most fire a
  post-turn side-effect.
- Source: `docs/configuration.md` (`notify` field table), 2026-07-18 fetch.

## 7. Rules / Memory — ✅ NATIVE

- **`AGENTS.md`** is the persistent always-on instruction/context file, scaffolded via `/init`. It
  is the single rules surface — no `.deepcode/rules/`, no `.mdc` files, no separate memory store.
  `/resume`/`/continue` restore prior conversation state but are not a persistent rules file.
- gald3r `g-rl-*` rules map into the single `AGENTS.md` instruction file (concatenated always-apply
  content); there is no per-rule `always_apply`/`agent_requested` typing and no `globs:` scoping.
- **Generator status**: `layout_map.yaml` currently declares no dedicated `rules:` entry for
  `deepcode` (T228's bootstrap-provenance convention: an entry is added only once a REAL donor
  placement is verified, never guessed). `AGENTS.md` emission is the **general per-platform fix
  covered by sibling task T385** ("Generator must always emit a root AGENTS.md per platform") —
  its per-platform instruction-filename mapping is the correct place to add `deepcode → AGENTS.md`,
  not a deepcode-specific branch here. Until T385 lands, this remains a `CAPABILITY_GAPS.md`
  entry for the `rules` component when a deepcode overlay is generated.
- Source: live README `/init` slash-command description, 2026-07-18 fetch.

## 8. MCP Support — ✅ NATIVE (config path corrected by T387)

- MCP is configured via the **`mcpServers`** object **inside `settings.json`** (user- or
  project-scope) — **there is no standalone `.mcp.json` file anywhere in Deep Code's documented
  config surface**. Inspect configured servers/tools with **`/mcp`**. Standard **stdio** transport
  (`command`/`args`/`env` per server); when `command` is `npx`, Deep Code auto-prepends `-y`.
- Because `~/.deepcode/settings.json` is shared with the VSCode extension, MCP servers configured
  once apply to both surfaces.
- **BUG FOUND AND FIXED (T387)**: `layout_map.yaml`'s `deepcode.mcp.file` previously pointed at
  `.deepcode/.mcp.json` — a path Deep Code **never reads**. gald3r's generated MCP registration
  therefore silently never reached the tool ("dead `.mcp.json`" finding from the 2026-07-16
  PLATFORM_TEMPLATE_REVIEW, confirmed correct by this live re-verification). Corrected to
  `.deepcode/settings.json`, which matches `generate_overlay`'s existing minimal-registration-JSON
  contract (`_emit_mcp`) verbatim — a project `settings.json` containing only `mcpServers` is valid
  per the documented field-layered config model (see Folder Hierarchy above).
- Source: `docs/mcp.md` + `docs/configuration.md` (`mcpServers` field table, full worked examples),
  2026-07-18 fetch.

---

## Parity vs. Cursor Reference

Deep Code reaches **partial parity** with the Cursor reference (`g-skl-platform-cursor`): native
**rules** (`AGENTS.md`, pending T385's central emission), **skills** (Agent Skills standard, native
today), and **MCP** (`mcpServers` in `settings.json`, path now corrected); **partial commands**
(fixed built-in slash set only); **no subagents** and **no lifecycle hooks**. The biggest gaps vs.
the reference are custom commands, subagents, and the hook system — these are real capability
absences in the tool itself, not gald3r integration gaps.

**Reuse note:** Deep Code reads **`AGENTS.md`** (not `CLAUDE.md`) and discovers
**`.agents/skills/`** (not `.claude/skills/`). gald3r's `AGENTS.md` + `.agents/skills/` artifacts
are directly reusable; the Claude-Code-specific `CLAUDE.md` / `.claude/` tree is not consumed.

## Hook System

- **Type**: none (no lifecycle-hook framework)
- **Config file**: `settings.json` (`notify` field only)
- **Events available**: none — a single post-turn `notify` callback, fired after each model turn
- **Event payload format**: env vars (`DURATION`, `STATUS`, `FAIL_REASON`, `BODY`, `TITLE`) passed
  to the notify script; fire-and-forget, no structured event stream
- **gald3r hook files**: `g-hk-*.py` do **not** wire natively — at most a post-turn side-effect

## Atypical Handling

- **Shared config surface**: `~/.deepcode/settings.json` is shared with the **Deep Code VSCode
  extension** — gald3r-managed settings (model, `mcpServers`, `notify`) apply to both surfaces.
- **Instruction-file convention**: Deep Code reads **`AGENTS.md`** (via `/init`), not `CLAUDE.md`.
- **Skills path duality**: project skills resolve from both `.deepcode/skills/` (native, higher
  scan priority) and `.agents/skills/` (interop, lower priority but still read) — gald3r targets
  the interop path since it is the one shared with every other Agent-Skills tool in the roster.
- **MCP config is field-layered, not file-standalone**: unlike most gald3r platforms, MCP does not
  get its own dedicated file — it is one field inside a settings file Deep Code also uses for
  model/API-key/notify config. `layout_map.yaml`'s `mcp: {file: ".deepcode/settings.json"}` mapping
  reuses the SAME target path a user might already have populated with their own model settings;
  `generate_overlay`'s existing overwrite-not-merge `materialize_overlay` behavior (uniform across
  every platform, T234) means a fresh MCP overlay write will **replace** an existing project-level
  `.deepcode/settings.json` wholesale if one is already present — this is a pre-existing, generic
  generator characteristic (not unique to deepcode) and out of this task's scope to change; flagged
  here for visibility since deepcode is the platform most likely to have a pre-populated file at
  that exact path (its own model/API-key config commonly lives there too).
- **Source disambiguation**: web searches surface unrelated DeepSeek-adjacent tools (DeepSeek-
  Reasonix, DeepSeek-TUI, deepseek-as-subagent) that DO have hooks/subagents — these are
  **different projects** and are excluded from this assessment of `lessweb/deepcode-cli`.

## gald3r Integration Notes

- Ship gald3r's **`AGENTS.md`** (instruction/rules, pending T385) + **`.agents/skills/<name>/
  SKILL.md`** tree — Deep Code discovers both natively today.
- Surface gald3r commands **as skills** (invocable via the `/` picker); there is no custom-command
  directory to target.
- Do **not** rely on hooks — degrade SessionStart context injection, PreToolUse guards, and
  pre-commit gates to manual/skill-driven flows; `notify` is post-turn-only and cannot block.
- Configure MCP via `mcpServers` in `.deepcode/settings.json` (corrected path, T387) — remember it
  also applies to the shared VSCode surface.
- Re-verify on the next `@g-platform-scan-docs deepcode` (`crawl_max_age_days: 14`).

---

## Capability Summary (copy into PLATFORM_STATUS.md row)

| Hooks | Rules | Skills | Commands | MCP | Docs Fresh |
|---|---|---|---|---|---|
| ❌ | ✅ | ✅ | ⚠️ | ✅ | ✅ |

Legend: ✅ verified working · ⚠️ partial / Cursor-generic · ❌ not supported · ❓ untested.

Overall platform `status: ⚠️` — real, verified config surface (skills + MCP fully wired by this
task; rules/AGENTS.md pending sibling task T385's central emission); commands/agents/hooks are
genuine tool-side gaps, not integration gaps. This is a **stub-tier, non-roster platform** (not one
of the 23 fully-supported IDE targets) — kept per owner directive because it has a real, working
config surface, not merely because it exists.

---

## Verification Evidence (live re-scan 2026-07-18)

| Capability | How verified |
|---|---|
| Project existence/legitimacy | `curl` raw-fetch of `github.com/lessweb/deepcode-cli` README (npm badges, MIT license, real contributor/issue links) + DeepSeek's own `api-docs.deepseek.com/quick_start/agent_integrations/deepcode` page (title: "Integrate with Deep Code \| DeepSeek API Docs") |
| Commands | Live README — fixed built-in slash set; **no** user-defined custom-command directory → ⚠️ partial |
| Rules | Live README — `/init` scaffolds **`AGENTS.md`**; reads `AGENTS.md` **not** `CLAUDE.md`; no `rules/` dir → ✅ native (gald3r wiring pending T385) |
| Agents | Live README / DeepSeek docs — single assistant, no sub-agents/roles/modes → ❌ none |
| Skills | Live README's documented scan-priority table (4 paths, project + user, native + interop) → ✅ native |
| Hooks | `docs/configuration.md`'s `notify` field table — no lifecycle hooks, post-turn-only → ❌ none |
| MCP | `docs/mcp.md` + `docs/configuration.md` — `mcpServers` field **inside** `settings.json`; **no** standalone `.mcp.json` anywhere in the docs → ✅ native; **generator path bug found and fixed** (T387) |
| Instruction file | Live README slash-command table — `AGENTS.md` via `/init` |
| Shared config | Live README FAQ + `docs/configuration.md` — `~/.deepcode/settings.json` shared with the Deep Code VSCode extension |

**Cross-check**: this 2026-07-18 live scan independently reproduces every capability cell from an
earlier 2026-06-02 scan (T1474, recorded in the retired `gald3r_templates_dev` donor tree) —
agreement across two independent scans 46 days apart is strong evidence the capability profile is
stable, not a transient doc state.
