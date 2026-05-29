---
subsystem_memberships: [PLATFORM_INTEGRATION]
spec_for: antigravity
---

# PLATFORM_SPEC.md — antigravity (Google Antigravity)

> **Authoring path: CREATE** (T1465). There was NO pre-existing `g-skl-platform-antigravity/`.
> This spec accompanies a newly scaffolded `g-skl-platform-antigravity/SKILL.md`.
>
> **⚠️ VOLATILE / LARGELY UNVERIFIED.** Google Antigravity 2.0 relaunched ~**2026-05-19** with
> breaking config changes. This spec was authored conservatively from public guides + docs, NOT a
> live install. **Most capabilities are `❓` and require `@g-platform-scan-docs antigravity` plus an
> install test before promotion.** Do NOT fabricate specifics. Do NOT copy from Cursor.

---

## Header / Metadata

```yaml
platform: antigravity
authoring_path: create               # antigravity (T1465) — no existing skill
docs_url: https://antigravity.google/docs/home
docs_url_secondary: https://codelabs.developers.google.com/getting-started-google-antigravity
crawl_max_age_days: 7
vault_doc_path: research/platforms/antigravity/
last_doc_scan: never                 # SCAN_DOCS not yet run — see Implementation Approach in task T1465
reference: g-skl-platform-cursor
status: ⚠️                           # partial — AGENTS.md + MCP verified; rules/skills/agents/hooks unverified
```

> `docs_url:` is co-located in `g-skl-platform-antigravity/SKILL.md` frontmatter so
> `g-skl-platform-monitor SCAN_DOCS` knows what to crawl.

---

## 1. Folder Hierarchy

Antigravity 2.0 splits config between a **project-local** `.antigravity/` dir and **user-global**
state under `~/.gemini/antigravity/` (Gemini-namespaced — the IDE shares Gemini's state tree).

```
<project_root>/
├── AGENTS.md                  ← ✅ project-root instruction file (read at session start)
└── .antigravity/
    └── mcp.json               ← ✅ project-local MCP config { "mcpServers": { ... } }

~/.gemini/antigravity/         ← ✅ user-global Antigravity state
├── global_workflows/          ← ✅ saved-prompt workflows (slash commands, invoked with /)
└── mcp_config.json            ← ✅ alternate/global MCP config (same mcpServers shape)
```

- **gald3r writes**: `AGENTS.md` (already generated), and (proposed) `.antigravity/mcp.json` for MCP servers.
- **Platform owns**: `~/.gemini/antigravity/` global state, IDE settings, subagent runtime.
- **❓ UNCONFIRMED**: dedicated always-apply rules dir, folder-per-skill dir, file-based agents dir,
  any hooks config. None of these were found in public docs/guides post-relaunch.

## 2. AI Instruction File

✅ **`AGENTS.md`** in the project root is the standard instruction file Antigravity reads.
This is the verified, primary gald3r integration point — gald3r already authors `AGENTS.md`, so
mission + rule-pointer + task-location-pointer wiring works without platform-specific changes.
Format: standard markdown. gald3r **generates** it (shared `AGENTS.md`, not Antigravity-bespoke).

## 3. Agents Support

❓ **Untested.** Antigravity is agent-first and runs native **dynamic subagents in parallel**, but
there is no documented mechanism for discovering/loading file-based `g-agnt-*.md` definitions (unlike
Cursor's `.cursor/agents/` manual-select model). The native subagent concept may not map onto
gald3r's markdown agent files at all. Verify whether `.antigravity/agents/` or any agent-file path
is honored during SCAN_DOCS + install test. Until then, treat gald3r agents as a documented gap and
fold critical agent guidance into `AGENTS.md`.

## 4. Skills Support

❓ **Untested — likely a gap.** No documented `SKILL.md` auto-discovery (folder-per-skill or flat)
was found for Antigravity post-relaunch. gald3r `g-skl-*` content cannot be assumed to auto-load.
Pragmatic v1: reference essential skill procedures from `AGENTS.md` or invoke them as workflows.
Confirm during install test whether any skill-discovery path exists.

## 5. Commands / Workflows

⚠️ **Partial.** Antigravity "**workflows**" are saved prompts triggered with `/` in agent chat,
stored at `~/.gemini/antigravity/global_workflows/`. This is the closest analogue to gald3r `@g-*`
commands. **Unverified**: the exact workflow file format, and whether gald3r `g-*` command files can
be dropped into `global_workflows/` to surface as `/g-*`. Verify file format + mapping during SCAN_DOCS.

## 6. Hooks System

❓ **No native hook/lifecycle system documented.** No `hooks.json` equivalent or
`sessionStart`/`stop`/`preToolUse`/`beforeShellExecution` event surface was found post-relaunch.
**Likely a GAP**: gald3r PowerShell hooks (`g-hk-*.ps1`) would run manually or be referenced from
`AGENTS.md` until a native hook mechanism is confirmed. (Note: Antigravity exposes security
**policies** — terminal auto-execution, terminal sandbox, artifact review, browser URL allow-list —
but these are settings, not programmable lifecycle hooks.)

## 7. Rules / Memory

⚠️ **Partial.** Confirmed persistent-context mechanism: **`AGENTS.md`** (project-root instructions).
NOT confirmed: a dedicated always-apply rules directory analogous to Cursor's `.cursor/rules/*.mdc`.
Antigravity also supports **"memories"** (durable agent state), surfaced via the memories.sh MCP
server rather than a gald3r-style rules file. gald3r `g-rl-*` always-apply guarantees therefore may
not hold beyond whatever `AGENTS.md` carries. No documented extension/token/size limit found.
Verify whether any always-apply rule file/dir exists during SCAN_DOCS.

## 8. MCP Support

✅ **Yes — verified.** Config shape `{ "mcpServers": { ... } }` at one of (install-dependent):
- `.antigravity/mcp.json` (project-local), or
- `~/.gemini/antigravity/mcp_config.json` (global; **Settings → Customizations → Open MCP Config**).

Server discovery is via that JSON. **Trusted Workspaces** security (v1.20.5+): only enable
write-capable MCP servers in repositories you own. Timeout behavior: **❓ not documented** — verify.

## 9. Known Gaps vs. Cursor Reference

Per `g-skl-platform-cursor/SKILL.md` §4a decision tree, each Cursor-reference feature is (a) common,
(b) a platform-specific override, or (c) a documented gap here:

| Cursor-reference feature | Antigravity status | Classification |
|---|---|---|
| Always-apply rules (`.mdc`) | ⚠️ only via `AGENTS.md`; no rules dir confirmed | (c) documented gap / partial |
| Skills (folder-per-skill `SKILL.md`) | ❓ no discovery mechanism found | (c) documented gap |
| Agents (`g-agnt-*.md` files) | ❓ native subagents only; file discovery unconfirmed | (c) documented gap |
| Commands (`@g-*`) | ⚠️ workflows `/` in `global_workflows/`; mapping untested | (b) platform-specific override (proposed) |
| Hooks (`hooks.json` + PS1) | ❓ no native lifecycle/hook surface found | (c) documented gap |
| MCP (`mcp.json`) | ✅ supported (`.antigravity/mcp.json`) | (b) platform-specific config |
| AI instruction file | ✅ `AGENTS.md` (project root) | (a) common (gald3r already generates) |

**Needs SCAN_DOCS**: every `❓`/`⚠️` cell above. The parity override dir
`.gald3r_sys/platforms/.antigravity/` did not exist before T1465 — create it for genuinely
platform-specific config and run `g-skl-platform-monitor VALIDATE antigravity` to catch
Cursor-generic copies.

---

## Capability Summary (copy into PLATFORM_STATUS.md row)

| Hooks | Rules | Skills | Commands | MCP | Docs Fresh |
|---|---|---|---|---|---|
| ❓ | ⚠️ | ❓ | ⚠️ | ✅ | ❓ |

Legend: ✅ verified working · ⚠️ partial / Cursor-generic · ❌ not supported · ❓ untested.

---

## Verification Evidence

| Capability | Status | How verified |
|---|---|---|
| AGENTS.md instruction file | ✅ | Public guides (community setup docs) state AGENTS.md is the Antigravity instruction-file standard, created in project root. Consistent across multiple sources (2026). Not yet confirmed by gald3r install test. |
| MCP support | ✅ | Multiple 2026 sources confirm `.antigravity/mcp.json` / `~/.gemini/antigravity/mcp_config.json` with `{ "mcpServers": {...} }`; UI path Settings → Customizations → Open MCP Config. |
| Workflows / slash commands | ⚠️ | Confirmed mechanism (saved prompts via `/`, stored in `~/.gemini/antigravity/global_workflows/`). gald3r `g-*` → `/g-*` mapping NOT tested. |
| Rules / memory | ⚠️ | AGENTS.md confirmed; native "memories" via memories.sh MCP confirmed. Always-apply `.mdc`-style rules dir NOT found in docs. |
| Hooks | ❓ | No native hook/lifecycle config documented in any source reviewed. |
| Skills (SKILL.md discovery) | ❓ | No documented auto-discovery mechanism found. |
| Agents (file-based) | ❓ | Native subagents confirmed; file-based `g-agnt-*.md` discovery NOT documented. |

**Authoring note**: No live install was performed. All ✅ cells rest on doc/guide citations, not
gald3r install tests. Promote `❓`/`⚠️` cells ONLY after `@g-platform-scan-docs antigravity` + an
install test records concrete evidence.
