---
subsystem_memberships: [PLATFORM_INTEGRATION]
platform: continue
authoring_path: refresh
docs_url: https://docs.continue.dev
docs_url_secondary:
  - https://docs.continue.dev/customize/overview
  - https://docs.continue.dev/customize/deep-dives/prompts
  - https://docs.continue.dev/customize/deep-dives/rules
  - https://docs.continue.dev/customize/deep-dives/mcp
  - https://docs.continue.dev/customize/deep-dives/agents
  - https://docs.continue.dev/customize/deep-dives/slash-commands
crawl_max_age_days: 14
vault_doc_path: research/platforms/continue/
last_doc_scan: 2026-07-18
reference: g-skl-platform-cursor
status: ⚠️
gald3r_support_tier: T2
task: T386
---

# PLATFORM_SPEC.md — Continue.dev

> **Authoring status**: `refresh` (T386) — re-verified 2026-07-18 against the live
> docs.continue.dev deep-dive pages listed above, replacing the 2026-06-13 `create`
> scaffold. **Root cause of the T386 "23 vs 38/39 platform-roster disconnect"**:
> Continue's commands were being written to `.continue/commands/`, a directory
> Continue's Prompt-file engine never reads — so every gald3r command silently failed
> to load while every other roster bookkeeping surface reported Continue as
> "installed". See section 5 and 10 below for the corrected path.

Open-source AI coding extension for VS Code and JetBrains. Context providers, slash
commands via `.prompt`-style Markdown files ("Prompts"), MCP integration, custom
models, and native custom sub-agents.

**Relationship**: Open-source VS Code / JetBrains extension.

> Highly configurable. MCP + context providers. Good match for gald3r CRASH
> primitives, with two real gaps: no native hooks, and no confirmed native Agent
> Skills support (see sections 4 and 6).

---

## 1. Folder Hierarchy

```
<project-root>/
└── .continue/
    ├── config.yaml                ← primary config (models, context, MCP, etc.)
    ├── rules/
    │   └── <name>.md               ← persistent instructions (rules equivalent)
    ├── prompts/
    │   └── <name>.md               ← Prompt files = custom slash commands (/name)
    ├── agents/
    │   └── <name>.md               ← custom sub-agent definitions
    ├── skills/
    │   └── <name>/SKILL.md         ← third-party-convention Agent Skills location
    │                                  (NOT confirmed as a Continue-core feature —
    │                                  see section 4)
    └── mcpServers/
        └── <name>-mcp.yaml         ← one MCP server per file (native format)
        └── mcp.json                ← Continue also auto-recognizes Claude
                                        Desktop/Cursor-style JSON MCP config files
                                        dropped directly into this folder
```

**Config file**: `.continue/config.yaml` (project-scope). No documented global
`~/.continue/config.yaml` auto-discovery was re-confirmed this scan — do not assume
one without a fresh crawl if that distinction becomes load-bearing.

---

## 2. CRASH Primitive Support

| Primitive | Support | Notes |
|---|---|---|
| **Hooks** | ❌ | No lifecycle-hook/event-bus documentation found in this scan. |
| **Rules** | ✅ | `.continue/rules/*.md`, loaded automatically, lexicographic order. NOT `AGENTS.md` — see section 3. |
| **Skills** | ⚠️ | Third-party marketplaces (LobeHub, mdskills.ai) document a `.continue/skills/` / `~/.continue/skills/` convention, but Continue's own tracker has an OPEN "Are there any plans to support skills in Continue?" issue (#9216) as of this scan — native first-party support is unconfirmed. |
| **Commands** | ✅ | Prompt files (`.continue/prompts/*.md`, `invokable: true` frontmatter) — invoked `/name`. |
| **MCP** | ✅ | `.continue/mcpServers/<name>-mcp.yaml`, OR a plain JSON file (e.g. `mcp.json`) dropped in the same folder, OR inline `mcpServers:` in `config.yaml`. |
| **Agents** | ✅ | `.continue/agents/*.md` — Markdown + YAML frontmatter, one file per custom agent. |

---

## 3. Instruction Files (Rules Equivalent)

**Continue does NOT natively read a root `AGENTS.md`.** This was the single most
consequential correction of this refresh — the prior scaffold assumed AGENTS.md
parity with gald3r's other platforms; it does not exist.

- `.continue/rules/*.md` — the real, documented, native mechanism. "You can create
  project-specific rules by adding a `.continue/rules` folder to the root of your
  project and adding new rule files." Each rule file is Markdown with optional YAML
  frontmatter (`name`, `globs`, `alwaysApply`, `description`). Rules load
  automatically for every Agent/Chat/Edit request and are concatenated into the
  system message. Rule files load in lexicographic order (number-prefix to control
  ordering).
- `AGENTS.md` root-file support is a still-open, unimplemented feature request:
  [continuedev/continue#6716](https://github.com/continuedev/continue/issues/6716)
  ("Add Support for Agent Rules Standard via Root AGENTS.md File"), opened
  2025-07-19. As of this scan, docs.continue.dev/customize/deep-dives/rules makes
  zero mention of AGENTS.md.
- gald3r therefore ships its rule content as `.continue/rules/*.md` (see
  `layout_map.yaml`'s `continue.rules` entry) and does **not** attempt a root
  `AGENTS.md`/`root_instructions` projection for this platform (see
  `layout_map.yaml`'s `root_instructions` module comment — `continue` is now in the
  deliberately-excluded list, alongside claude/cursor/copilot/aider/etc.).

---

## 4. Skills

⚠️ Unconfirmed as a first-party Continue feature.

- Third-party skill marketplaces (LobeHub's `terminalskills-skills-continue-dev`,
  mdskills.ai) document skills living at `.continue/skills/` (project) or
  `~/.continue/skills/` (global), using the standard `SKILL.md` + YAML frontmatter
  (`name`/`description`) shape gald3r already ships for Claude/Cursor/ZCode/etc.
- Continue's own GitHub tracker has an open request,
  [continuedev/continue#9216](https://github.com/continuedev/continue/issues/9216)
  ("Are there any plans to support skills in Continue?"), suggesting native
  first-party Skills discovery may not yet be shipped as of this scan.
- gald3r keeps the `.continue/skills/` `dir-per-skill` layout mapping (matches the
  marketplace-documented convention and costs nothing if unused) but the matrix cell
  stays `⚠️` (partial/unconfirmed) rather than `✅` until a live install test proves
  discovery.

---

## 5. Commands (Slash Commands / Prompt Files)

✅ Native, via **Prompt files**.

- **Directory**: `.continue/prompts/*.md` (project scope). This is the corrected
  path — the prior scaffold (and gald3r's shipped `layout_map.yaml` entry, until
  T386) pointed at `.continue/commands/`, which Continue never reads.
- **Format**: Markdown with YAML frontmatter (`name`, `description`,
  `invokable: true`). Setting `invokable: true` makes the file available as a `/`
  slash command in Chat, Plan, and Agent mode. Files can also use full prompt
  templating (referencing files, URLs, highlighted code).
- **Invocation**: `/<name>` (the frontmatter `name`, not necessarily the filename).
- Prompts can also be declared inline in `config.yaml` via a `prompts:` block
  (e.g. `prompts: - uses: supabase/create-functions`) — a distribution/reuse
  mechanism, not the primary per-project authoring path gald3r targets.

---

## 6. Hooks

❌ Not supported.

No lifecycle-hook / event-bus documentation was found across
`customize/overview`, `customize/deep-dives/configuration`, or the other deep-dive
pages crawled this scan. Do not fabricate a hook config surface for Continue.

---

## 7. MCP

✅ Native, two supported shapes.

- **Per-server YAML files** (the documented native format): create
  `.continue/mcpServers/` at the workspace root, then one `<name>-mcp.yaml` file
  per server:
  ```yaml
  name: Playwright mcpServer
  version: 0.0.1
  schema: v1
  mcpServers:
    - name: Browser search
      command: npx
      args: ["@playwright/mcp@latest"]
  ```
- **Plain JSON config auto-recognition**: "You can also place JSON config files
  (from Claude Desktop, Cursor, etc.) directly in `.continue/mcpServers/` and
  Continue will automatically recognize them, such as `.continue/mcpServers/mcp.json`."
  This is the shape gald3r's generic minimal-JSON MCP registration
  (`generate.py`'s `_emit_mcp`) already produces — corrected `layout_map.yaml` target:
  `.continue/mcpServers/mcp.json` (was `.continue/.mcp.json`, a path Continue never
  reads).
- **Inline in `config.yaml`**: `mcpServers:` can also be declared directly inside
  the main `config.yaml` (a Block-composition alternative to the per-file form
  above) — not gald3r's install target, documented here for completeness.
- MCP is usable only in Agent mode.

---

## 8. Agents

✅ Native custom sub-agents.

- **Directory**: `.continue/agents/*.md` (project scope, version-controlled and
  shared with the team).
- **Format**: Markdown file with YAML frontmatter configuring the agent, plus a
  Markdown body that becomes the agent's system-prompt/instructions. The filename
  becomes the agent's name.

---

## 9. Instruction Files — see section 3 (folded in; Continue has no separate
"instruction file" concept distinct from Rules).

---

## 10. gald3r Installation

### Install Path (corrected, T386)

```
<project-root>/
└── .continue/
    ├── rules/<name>.md            ← g-rl-* rules
    ├── prompts/<name>.md          ← g-* commands (CORRECTED from commands/)
    ├── agents/<name>.md           ← g-agnt-* agents
    ├── skills/<name>/SKILL.md     ← g-skl-* skills (dir-per-skill, unconfirmed native discovery)
    └── mcpServers/mcp.json        ← gald3r MCP registration (CORRECTED from .continue/.mcp.json)
```

```bash
gald3r platform install continue --into <target-dir>
```

No root `AGENTS.md`/root-instructions file is written for Continue (see section 3).

### Verification Checklist

- [x] Rules file location confirmed: `.continue/rules/*.md` (2026-07-18 docs crawl)
- [x] Commands (Prompt files) location confirmed: `.continue/prompts/*.md` (2026-07-18 docs crawl)
- [x] Agents location confirmed: `.continue/agents/*.md` (2026-07-18 docs crawl)
- [x] MCP config syntax verified: `.continue/mcpServers/<name>-mcp.yaml` or auto-recognized JSON (2026-07-18 docs crawl)
- [x] Root AGENTS.md NOT natively read — confirmed absent, do not project one (2026-07-18)
- [ ] Skills discovery path — third-party-documented only, not first-party-confirmed; re-check on next scan
- [ ] Full live `gald3r platform install continue` + open-in-Continue smoke test

---

## 11. Official Docs

- Primary: <https://docs.continue.dev>
- Overview: <https://docs.continue.dev/customize/overview>
- Prompts (commands): <https://docs.continue.dev/customize/deep-dives/prompts>
- Rules: <https://docs.continue.dev/customize/deep-dives/rules>
- MCP: <https://docs.continue.dev/customize/deep-dives/mcp>
- Agents: <https://docs.continue.dev/customize/deep-dives/agents>
- AGENTS.md feature request (open, unimplemented): <https://github.com/continuedev/continue/issues/6716>
- Skills feature request (open, unimplemented): <https://github.com/continuedev/continue/issues/9216>

---

*Scaffold created 2026-06-13. Refreshed 2026-07-18 (T386) against the live docs
listed above — see section headers for per-capability citations. Re-run
`@g-platform-scan-docs continue` on the next `crawl_max_age_days` (14) cycle.*
