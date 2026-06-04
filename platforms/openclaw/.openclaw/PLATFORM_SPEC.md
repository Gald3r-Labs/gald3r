---
subsystem_memberships: [PLATFORM_INTEGRATION]
platform: openclaw
authoring_path: update
docs_url: https://docs.openclaw.ai
docs_url_secondary:
  - https://github.com/openclaw/openclaw
  - https://docs.openclaw.ai/cli/skills
  - https://docs.openclaw.ai/cli/hooks
  - https://docs.openclaw.ai/cli/mcp
  - https://docs.openclaw.ai/reference/AGENTS.default
crawl_max_age_days: 14
vault_doc_path: research/platforms/openclaw/
last_doc_scan: never
reference: g-skl-platform-cursor
status: ⚠️
---

# PLATFORM_SPEC.md — OpenClaw

OpenClaw is a real, MIT-licensed, **local-first autonomous AI agent** (formerly *clawdbot* /
*moltbot*). It runs on your own machine, connects through messaging apps (WhatsApp, Telegram,
Slack, Signal, etc.), stores memory as plain Markdown on disk, and runs a "heartbeat" daemon that
can act without prompting. It is **config-first**: you write a `SOUL.md`, run a command, and your
agent is live — "no Python, no chains, no graphs."

This makes OpenClaw materially **different** from the IDE-embedded coding agents that most other
gald3r platforms target. It is closer to a personal-assistant gateway than an in-editor coding
copilot, but it shares two gald3r-relevant primitives: a **portable `SKILL.md` skill format** and a
**workspace `skills/` directory** it reads natively.

> **Authoring path: UPDATE** — `g-skl-platform-openclaw/SKILL.md` already ships. **This spec
> CORRECTS the prior skill text**, which described OpenClaw as a minimal "SOUL.md + root skills/"
> reader with *no* hooks, *no* commands, and *no* MCP. The 2026 public docs at
> https://docs.openclaw.ai show OpenClaw **does** have a hooks system, slash commands, and MCP
> support. The corrected findings are recorded here; the SKILL.md Known Gaps section points back to
> this spec.

> **HONESTY NOTE**: All findings below are from the **public docs** (docs.openclaw.ai) and the
> existing gald3r override scaffold, NOT from a live install verified in this repo. `@g-platform-scan-docs
> openclaw` has **never** been run (`last_doc_scan: never`). Items marked ❓ are doc-derived-but-untested;
> gald3r has authored NO live OpenClaw deploy in this repo. Treat the ⚠️ status as "doc-supported,
> install-unverified."

---

## 1. Folder Hierarchy

OpenClaw is **not** repo-scoped the way an IDE agent is. It operates out of a per-user **workspace**,
not a project `.openclaw/` folder inside the codebase:

```
~/.openclaw/                          ← per-user OpenClaw home (default; not the project repo)
├── openclaw.json                     ← main config (hooks, mcp.servers, agent defaults)
└── workspace/                        ← default agent workspace (configurable via agents.defaults.workspace)
    ├── SOUL.md                       ← identity / tone / boundaries (primary persona file)
    ├── AGENTS.md                     ← agent configuration / instructions
    ├── TOOLS.md                      ← notes for Skills + environment-specific settings
    ├── IDENTITY.md                   ← identity template (per the awesome-openclaw-agents convention)
    ├── MEMORY.md                     ← durable facts / preferences / decisions (long-term memory)
    ├── memory/
    │   └── YYYY-MM-DD.md             ← daily memory logs
    └── skills/                       ← workspace skills dir (default install target; SKILL.md per skill)
        └── {skill-name}/
            └── SKILL.md
```

**gald3r deploy scaffold** lives at `.gald3r_sys/platforms/.openclaw/` and currently ships
`SOUL.md`, `openclaw_instructions.md`, and `README.md` only.

**Verified correction vs. prior SKILL.md text:** OpenClaw's canonical surface is the per-user
`~/.openclaw/workspace/`, **not** the project repo root. The prior skill's "`<project-root>/SOUL.md`
+ `<project-root>/skills/`" model only holds if a user points `agents.defaults.workspace` at the
repo, OR installs gald3r skills into the workspace `skills/` dir. The native default is `~/.openclaw/workspace/skills/`.

**gald3r writes (per scaffold)**: `SOUL.md`.
**OpenClaw owns**: `~/.openclaw/openclaw.json`, the workspace location, the skill/hook registries.

---

## 2. AI Instruction File

OpenClaw injects **multiple** prompt files on agent startup (not a single one):

| File | Role |
|---|---|
| `SOUL.md` | Identity, tone, boundaries — the persona document (gald3r ships this) |
| `AGENTS.md` | Agent configuration / behavioral instructions |
| `TOOLS.md` | Notes for Skills + environment-specific settings |
| `IDENTITY.md` | Identity template (community convention) |
| `MEMORY.md` | Long-term durable memory (read at startup) |

In the gald3r ecosystem, `AGENTS.md` is already the canonical cross-platform instruction file, so it
maps cleanly. `SOUL.md` is the OpenClaw-specific persona overlay — gald3r ships a templated
`SOUL.md` that points at `.gald3r/` (TASKS.md, CONSTRAINTS.md, PROJECT.md, BUGS.md). **Do not
confuse `SOUL.md` with `AGENTS.md`** — OpenClaw reads both, for different purposes.

**Status**: ⚠️ — SOUL.md mapping is verified by docs + scaffold; AGENTS.md/TOOLS.md/MEMORY.md
ingestion is doc-confirmed but the gald3r scaffold only ships `SOUL.md` today.

---

## 3. Agents Support

- **Native concept**: ✅ OpenClaw is an *agent runtime* — it has agents (`agents.defaults.*` in
  config; `check --agent <id>` inspects per-agent skill visibility). Agent personality is defined by
  the `SOUL.md` / `AGENTS.md` / `IDENTITY.md` workspace files, not by a directory of `g-agnt-*.md`
  files the way Cursor discovers them.
- **gald3r agent files (`g-agnt-*.md`)**: ❌ no native discovery path. OpenClaw does not scan an
  `agents/` folder of markdown agent definitions; its "agents" are workspace personas. gald3r's
  per-role agent files would have to be referenced manually from `SOUL.md`/`AGENTS.md`.
- **Status**: ⚠️ — OpenClaw HAS agents, but **not** the gald3r `g-agnt-*.md` discovery model.

---

## 4. Skills Support

- **Discovery**: ✅ workspace `skills/<name>/SKILL.md` — **folder-per-skill**, exactly matching
  gald3r's layout. Default install target is the workspace `skills/` dir; a `--global` flag targets a
  shared managed skills dir.
- **SKILL.md format**: ✅ install slug derives from `SKILL.md` frontmatter `name` (or dir/repo name;
  override with `--as <slug>`). This aligns with gald3r `g-skl-*` SKILL.md frontmatter.
- **Install sources**: ClawHub registry (`openclaw skills install <slug>`), `git:owner/repo[@ref]`,
  or local directory path containing a `SKILL.md`.
- **Enable/inspect**: `openclaw skills list|info|check`; `check --agent <id>` shows which ready
  skills are visible to a given agent's prompt/command surface. Skills are enabled via Settings → Skills.
- **gald3r mapping**: gald3r's root `skills/` (T1042 canonical source) maps to OpenClaw's workspace
  `skills/` dir — but only if the OpenClaw workspace is pointed at the repo OR the gald3r skills are
  installed into `~/.openclaw/workspace/skills/`. It is **not** automatic the way the prior SKILL.md
  implied.
- **Status**: ✅ format & discovery verified by docs; ⚠️ the "zero wiring, reads repo root natively"
  claim is install-dependent (workspace location must be configured).

---

## 5. Commands / Workflows

- **Native commands**: ✅ OpenClaw has slash commands — documented examples include `/new` and
  `/reset` (session lifecycle), plus a CLI surface (`openclaw skills ...`, `openclaw mcp ...`,
  `openclaw hooks ...`).
- **gald3r `g-*` commands**: ❌ no native `commands/` discovery directory analogous to
  `.cursor/commands/`. gald3r's `@g-*` / `/g-*` command markdown files are not auto-registered as
  OpenClaw slash commands. They would be invoked indirectly via skills or referenced in SOUL.md.
- **Status**: ⚠️ — OpenClaw HAS a slash-command/CLI surface, but does **not** ingest gald3r's
  `g-*.md` command files as executable commands.

---

## 6. Hooks System

OpenClaw has a **real, event-driven hooks system** (this directly contradicts the prior SKILL.md /
override README which said "No `hooks/` folder — minimal config by design").

| Documented event | Meaning |
|---|---|
| `command:new` | fires on `/new` |
| `command:reset` | fires on `/reset` |
| `gateway:startup` | fires when the gateway starts |
| `agent:bootstrap` | fires during agent bootstrap |

- **Format**: each hook is a directory with a `HOOK.md` (documentation) + `handler.ts` (TypeScript
  implementation). **This is fundamentally incompatible with gald3r's PowerShell `g-hk-*.ps1` hooks**
  — OpenClaw hooks are TS handlers, not `.ps1`.
- **Wiring**: configured in `~/.openclaw/openclaw.json` under `hooks.internal.entries.<name>.enabled`,
  with `hooks.internal.load.extraDirs` for extra hook dirs and `hooks.internal.installs` for npm hook
  packs. Workspace hooks require `openclaw hooks enable <name>` before the gateway loads them.
- **gald3r mapping**: ❌ gald3r's `.ps1` hook bodies are **not portable** to OpenClaw's `handler.ts`
  model. The event names also differ (gald3r uses `sessionStart`/`stop`/`preToolUse`; OpenClaw uses
  `gateway:startup`/`agent:bootstrap`/`command:new`). A port would require rewriting hook logic in
  TypeScript and re-mapping events.
- **Status**: ⚠️ — OpenClaw HAS hooks, but the gald3r hook payload is non-portable (TS vs PS1,
  different event taxonomy). Marked ⚠️ rather than ❌ because the *capability* exists; the *gald3r
  integration* does not.

---

## 7. Rules / Memory

- **Native rules**: OpenClaw has **no dedicated `rules/` directory or `.mdc` rule mechanism**.
  Behavioral guidance lives in `SOUL.md` (identity/tone/boundaries) and `AGENTS.md`.
- **Memory**: ✅ first-class and Markdown-native — `MEMORY.md` for durable facts/preferences/decisions
  and `memory/YYYY-MM-DD.md` daily logs. This is a genuine differentiator (local-first persistent
  memory), and aligns conceptually with gald3r `.gald3r/learned-facts.md`.
- **gald3r mapping**: gald3r's `g-rl-*.md`/`.mdc` always-apply rules have **no native injection
  point**. They must be summarized into `SOUL.md`/`AGENTS.md` prose. gald3r learned-facts could be
  mirrored into `MEMORY.md`.
- **Status**: ⚠️ — no native rule format; rules collapse into the persona files. Memory is ✅ as a
  concept but no gald3r↔MEMORY.md sync is wired.

---

## 8. MCP Support

- **Supported**: ✅ Yes — first-class MCP, contradicting the prior "minimal config, no MCP" framing.
- **Config**: centralized registry in `~/.openclaw/openclaw.json` under `mcp.servers`. Managed via
  `openclaw mcp set|list|show|unset <name> <json>`.
- **Transports**: stdio (`command` + `args`), SSE/HTTP (`url` + optional `headers`), and
  streamable-http (`transport: "streamable-http"`).
- **Discovery**: servers are stored centrally; "runtime adapters" and downstream clients consume the
  saved registry — runtimes do not keep duplicate server lists.
- **gald3r mapping**: gald3r MCP config (root `.mcp.json` / Cursor settings) does **not**
  auto-translate; servers must be re-declared via `openclaw mcp set`. The *capability* is fully
  present.
- **Status**: ✅ mechanism verified by docs; ⚠️ gald3r-side server set untranslated/untested.

---

## 9. Known Gaps vs. Cursor Reference

Compared to the Cursor reference (§ Cursor PLATFORM_SPEC):

1. **Not an IDE / not repo-scoped** — OpenClaw runs out of `~/.openclaw/workspace/`, not a project
   `.openclaw/` checkout. gald3r's repo-root-everything model only partly applies; the workspace must
   be pointed at the repo or skills installed into the OpenClaw home.
2. **Rules ❌** — no `.mdc` / `rules/` mechanism. gald3r `g-rl-*` rules must be folded into
   `SOUL.md`/`AGENTS.md` prose. No always-apply injection.
3. **Hooks non-portable ⚠️** — OpenClaw HAS hooks, but they are `HOOK.md` + `handler.ts` (TypeScript)
   wired via `openclaw.json`, with a different event taxonomy (`gateway:startup`, `agent:bootstrap`,
   `command:new/reset`). gald3r `.ps1` hooks do not run; events do not map 1:1. Porting requires TS
   rewrites.
4. **Commands ⚠️** — OpenClaw has slash commands (`/new`, `/reset`) and a CLI, but does **not** ingest
   gald3r `g-*.md` command files as executable commands.
5. **Agents ⚠️** — OpenClaw is itself an agent runtime, but does not discover gald3r `g-agnt-*.md`
   agent-definition files; personas come from `SOUL.md`/`AGENTS.md`/`IDENTITY.md`.
6. **Skills ✅ (install-dependent)** — `skills/<name>/SKILL.md` folder-per-skill matches gald3r, but
   skills land in `~/.openclaw/workspace/skills/` (or `--global`), not "the repo root natively." Prior
   SKILL.md overstated the automatic-repo-read behavior.
7. **MCP ✅ (re-declaration needed)** — first-class, but gald3r MCP server definitions are not
   auto-imported; use `openclaw mcp set`.
8. **SCAN_DOCS not yet run** — `last_doc_scan: never`. **Needs `@g-platform-scan-docs openclaw`** to
   confirm exact `SKILL.md` frontmatter fields OpenClaw honors, the full hook event list, and whether a
   project-local `.openclaw/` config is supported in addition to `~/.openclaw/`. All findings here are
   public-doc-derived and **install-unverified**.
9. **No live gald3r deploy verified** — the override scaffold ships only `SOUL.md`; the
   `AGENTS.md`/`TOOLS.md`/`MEMORY.md`/skills-install path is documented but not exercised in this repo.

---

## Capability Summary (copy into PLATFORM_STATUS.md row)

| Hooks | Rules | Skills | Commands | MCP | Docs Fresh |
|---|---|---|---|---|---|
| ⚠️ | ❌ | ⚠️ | ⚠️ | ⚠️ | ❓ |

Legend: ✅ verified working · ⚠️ partial / capability-exists-but-gald3r-integration-unverified · ❌ not supported · ❓ untested.

- **Hooks ⚠️**: capability exists (TS handlers, openclaw.json), gald3r `.ps1` payload non-portable.
- **Rules ❌**: no native rule/`.mdc` mechanism; rules fold into SOUL.md/AGENTS.md.
- **Skills ⚠️**: SKILL.md format & discovery ✅ by docs, but install-path-dependent and unverified live.
- **Commands ⚠️**: native slash/CLI commands exist; gald3r `g-*.md` files not ingested.
- **MCP ⚠️**: first-class capability ✅, but gald3r server set not translated/tested.
- **Docs Fresh ❓**: `last_doc_scan: never`.

Overall platform `status: ⚠️` — doc-supported, install-unverified.

---

## Verification Evidence

| Capability | How verified |
|---|---|
| Platform is real | WebSearch: github.com/openclaw/openclaw ("personal AI assistant, any OS/platform, the lobster way"); Milvus guide (formerly clawdbot/moltbot, MIT, local-first, Markdown memory) |
| Config files (SOUL/AGENTS/TOOLS/MEMORY) | WebFetch docs.openclaw.ai/reference/AGENTS.default — SOUL.md (identity/tone/boundaries), AGENTS.md, TOOLS.md (notes for Skills), MEMORY.md + memory/YYYY-MM-DD.md |
| Workspace location | docs.openclaw.ai — default `~/.openclaw/workspace`, configurable via `agents.defaults.workspace` |
| Skills format/discovery | WebFetch docs.openclaw.ai/cli/skills — SKILL.md frontmatter `name`, workspace `skills/` + `--global`, ClawHub / git: / local install sources |
| Hooks | WebFetch docs.openclaw.ai/cli/hooks — HOOK.md + handler.ts; events command:new/reset, gateway:startup, agent:bootstrap; wired in openclaw.json `hooks.internal.*` |
| MCP | WebFetch docs.openclaw.ai/cli/mcp — `mcp.servers` registry, stdio/SSE/streamable-http transports, `openclaw mcp set` |
| gald3r scaffold | `.gald3r_sys/platforms/.openclaw/` ships SOUL.md, openclaw_instructions.md, README.md |
| Live install | NOT verified — no live OpenClaw install exercised in this repo; `last_doc_scan: never`; needs `@g-platform-scan-docs openclaw` |
