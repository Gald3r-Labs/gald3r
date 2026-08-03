---
subsystem_memberships: [PLATFORM_INTEGRATION]
platform: zed
authoring_path: new
docs_url: https://zed.dev/docs/ai/external-agents
docs_url_secondary:
  - https://zed.dev/docs/ai/agent-settings
  - https://zed.dev/docs/ai/instructions
  - https://zed.dev/docs/ai/skills
  - https://zed.dev/docs/ai/mcp
  - https://zed.dev/docs/ai/agent-panel
  - https://agents.md/
crawl_max_age_days: 14
vault_doc_path: research/platforms/zed/
last_doc_scan: 2026-07-03
reference: g-skl-platform-cursor
status: ⚠️
task: platform-Zed (agent panel + ACP host)
---

# PLATFORM_SPEC.md — Zed (agent panel + ACP host)

**Zed** (`zed.dev`) is a Rust-native, GPU-accelerated code editor. Its **Agent Panel** hosts Zed's
own built-in agent AND **External Agents** — third-party coding agents (Claude Code, Kimi Code,
Codex, Copilot, Cursor, OpenCode, Pi Coding Agent, and others) — through the open **Agent Client
Protocol (ACP)**, making Zed both an editor and a distribution/hosting surface for other vendors'
coding agents. It is also a native adopter of the open `AGENTS.md` instructions standard
(https://agents.md/).

**Authoring path**: NEW. **Verified 2026-07-03** against https://zed.dev/docs/ai/external-agents,
https://zed.dev/docs/ai/agent-settings, https://zed.dev/docs/ai/instructions,
https://zed.dev/docs/ai/skills, https://zed.dev/docs/ai/mcp, https://zed.dev/docs/ai/agent-panel,
and https://agents.md/ (see Verification Evidence). No prior gald3r spec existed for this platform.

> **Instruction-file truth (read carefully):** Zed reads a project-level instructions file chosen
> from a **fixed fallback list** — `.rules` first, then `.cursorrules`, `.windsurfrules`,
> `.clinerules`, `.github/copilot-instructions.md`, `AGENT.md`, `AGENTS.md`, `CLAUDE.md`, `GEMINI.md`
> — **only the first match in that list is read**. This is layered on top of an always-on
> **personal, machine-global** `AGENTS.md` at `~/.config/zed/AGENTS.md` (macOS/Linux) or
> `%APPDATA%\Zed\AGENTS.md` (Windows), which applies to every workspace on that machine. Project
> instructions win over the personal file on conflict. **`.rules` is a legacy filename kept for
> cross-tool back-compat** with pre-AGENTS.md-era Cursor/Windsurf/Cline projects — new projects are
> steered toward `AGENTS.md`, which Zed natively supports per the open agents.md standard.

---

## 1. Folder Hierarchy

```
<project-root>/
├── .rules OR AGENTS.md              ← project instructions (.rules wins if BOTH exist — precedence list)
└── .agents/
    └── skills/   <name>/SKILL.md    ← Agent Skills (YAML frontmatter: name, description + body)

~/.config/zed/ (macOS/Linux) or %APPDATA%\Zed\ (Windows)
└── AGENTS.md                        ← personal/global instructions — always-on, every workspace

~/.agents/skills/  <name>/SKILL.md   ← user-global Agent Skills (shared cross-client convention)

(.zed/settings.json)                 ← Zed-owned workspace settings; houses "agent_servers"
                                        (External ACP agents) and "context_servers" (MCP)
```

**gald3r writes**: project-root `AGENTS.md` and `.agents/skills/<name>/SKILL.md`. **Zed owns**: the
personal `~/.config/zed/AGENTS.md` (machine-global, not per-project), the `.zed/settings.json`
schema (`agent_servers`, `context_servers`, and all other editor settings), and the ACP registry
UI (`zed: acp registry`).

---

## 2. AI Instruction File

Zed selects **one** project-level instructions file via a fixed precedence list — first match wins,
no merging of multiple project files:

1. `.rules`
2. `.cursorrules`
3. `.windsurfrules`
4. `.clinerules`
5. `.github/copilot-instructions.md`
6. `AGENT.md`
7. `AGENTS.md`
8. `CLAUDE.md`
9. `GEMINI.md`

This selected project file is layered **on top of** the always-on personal
`~/.config/zed/AGENTS.md` (`%APPDATA%\Zed\AGENTS.md` on Windows); project instructions take priority
over personal instructions on conflict. Zed natively supports the open `AGENTS.md` standard
(https://agents.md/) as its primary/recommended project instructions format — `.rules` is
maintained purely for backward compatibility with projects that pre-date the `AGENTS.md`
convention. **gald3r ships `AGENTS.md`**, not `.rules` — if a target project already has a `.rules`
file (inherited from an older Cursor/Windsurf/Cline setup), that file wins over gald3r's
`AGENTS.md` in Zed until removed or renamed; document this as a manual step rather than having
gald3r silently delete/rename a pre-existing `.rules` file it does not own.
- Source: https://zed.dev/docs/ai/instructions

---

## 3. Agents Support — ❌ NO PROJECT-SCOPED ROSTER (native agent is UI/profile-based; third parties attach via ACP)

- Zed's own built-in agent is configured through **Agent Profiles** (Settings UI /
  `agent-settings.html`), not a committed per-project agent-definition file gald3r could populate.
- **External Agents** — Claude Code, Kimi Code, Codex, Copilot, Cursor, OpenCode, Pi Coding Agent,
  and others — attach to the Agent Panel and Threads Sidebar as independent processes speaking the
  **Agent Client Protocol (ACP)**. Zed hosts the thread UI; "the External Agent usually owns its own
  runtime, auth, model selection, tools, and native configuration" (docs, verbatim). Users install
  ACP agents from the **ACP Registry** (`zed: acp registry` command) or add a custom one via
  `agent: open settings` → Add Agent → Add Custom Agent, which writes an `agent_servers.<name>`
  entry to `.zed/settings.json`:
  ```json
  {
    "agent_servers": {
      "my-agent": {
        "type": "custom",
        "command": "node",
        "args": ["~/projects/agent/index.js", "--acp"],
        "env": {}
      }
    }
  }
  ```
- **gald3r gap**: there is no project-scoped `agents/<name>.md` roster file gald3r can drop into a
  Zed workspace — the closest equivalent is an ACP registry entry (Zed-managed) or a manually added
  `agent_servers` block in the user's own `.zed/settings.json`. Do not fabricate an `agents/` folder
  Zed does not read.
- Source: https://zed.dev/docs/ai/external-agents, https://zed.dev/docs/ai/agent-panel

## 4. Skills Support — ✅ NATIVE

- **Agent Skills**: a folder containing `SKILL.md` with required YAML frontmatter `name` (lowercase
  letters/numbers/hyphens only, max 64 chars, must match the folder name) and `description` (what it
  does + when to use it, under 1024 bytes), plus Markdown instructions body. Optional
  `disable-model-invocation: true` prevents autonomous discovery while keeping the skill available
  via slash command / `@`-mention.
- **Locations**: `~/.agents/skills/<name>/SKILL.md` (global scope, every project) and
  `<worktree>/.agents/skills/<name>/SKILL.md` (project-local scope). **Skills must be direct
  children of the skills root** — nested group folders (`.agents/skills/group/my-skill/`) are NOT
  discovered.
- **Discovery/invocation**: the agent autonomously discovers every installed skill (name +
  description surfaced in its system prompt) and calls the `skill` tool when a task matches. Manual
  invocation via `/` slash command or `@skill` mention-completion. Project-local skills load only
  from **trusted worktrees**; when a global and a project-local skill share a name, the
  project-local one wins.
- This is the **same `.agents/skills/` convention** gald3r already targets for Codex, Amp, and Deep
  Code — gald3r's `g-skl-*/SKILL.md` files are drop-in native, no adaptation needed.
- Source: https://zed.dev/docs/ai/skills

## 5. Commands / Workflows — ❌ NOT A SEPARATE SURFACE (Skills fill this role)

- Zed's Agent Panel documentation surfaces exactly one built-in slash command, `/compact` (manual
  context compaction of a long thread) — there is **no** documented dedicated file format, directory
  convention, or settings key for user-authored custom slash commands / prompt libraries distinct
  from Skills.
- Skills are invoked the same way a "command" would be (`/` picker, `@`-mention), so gald3r's
  `@g-*` command surface maps onto the same `.agents/skills/<name>/SKILL.md` tree used for Skills —
  there is no separate `commands/` folder to populate.
- Source: https://zed.dev/docs/ai/agent-panel (only `/compact` documented); absence confirmed
  against the full AI docs nav (Skills vs. Agent Panel vs. Agent Settings pages).

## 6. Hooks System — ❌ NOT SUPPORTED (no published event taxonomy for hand-authored hooks)

- No dedicated hooks/lifecycle-events documentation page exists in Zed's AI docs nav (Agents, Agent
  Panel, Agent Settings, Agent Profiles, Tools [Tool Permissions, Agent Sandboxing, MCP], Skills,
  Instructions, Parallel Agents, Inline Assistant, LLM Providers, Edit Prediction, AI Privacy — no
  "Hooks" entry).
- **Tool Permissions** / **Agent Sandboxing** provide confirmation-gating around tool calls
  (allow/deny prompts, sandboxed execution), which is access-control, not an event-hook bus a
  project can extend with its own scripts.
- **gald3r gap**: there is no verified wiring target for `g-hk-*.py` files on Zed — do not fabricate
  a `hooks.json`/settings-driven hook file.
- Source: absence confirmed against the full AI docs nav under https://zed.dev/docs/ai/overview.

## 7. Rules / Memory — ✅ NATIVE (`AGENTS.md`, project + personal scope, fixed fallback precedence)

- Persistent instructions are the project instructions file described in §2 (chosen via the fixed
  9-entry fallback list, `.rules` highest precedence) layered on top of the always-on personal
  `~/.config/zed/AGENTS.md` (`%APPDATA%\Zed\AGENTS.md` on Windows). There is **no** scoped/glob rule
  system (no `.mdc`-equivalent, no per-subdirectory `AGENTS.md` hierarchy scan documented) — Zed
  natively supports the open `AGENTS.md` standard (https://agents.md/) directly, unlike platforms
  that require an `@import` shim.
- gald3r ships **`AGENTS.md`** at the project root (not `.rules`) — this is Zed's recommended,
  natively-supported format and matches gald3r's existing `AGENTS.md`-native platforms. If a
  pre-existing `.rules` file is present from an older tool's setup, it silently outranks gald3r's
  `AGENTS.md` in Zed until removed; flag this to the user.
- Source: https://zed.dev/docs/ai/instructions

## 8. MCP Support — ✅ NATIVE

- MCP servers are configured via **`context_servers`** in `.zed/settings.json`:
  ```json
  {
    "context_servers": {
      "local-mcp-server": { "command": "some-command", "args": ["arg-1", "arg-2"], "env": {} },
      "remote-mcp-server": { "url": "https://example.com/mcp", "headers": { "Authorization": "Bearer <token>" } }
    }
  }
  ```
- **Local** servers use `command`/`args`/`env` (stdio); **remote** servers use `url`/optional
  `headers`. When a remote server has no configured `Authorization` header, Zed prompts for OAuth.
- **Distinct from `agent_servers`**: `context_servers` configures MCP tool/prompt servers for Zed's
  own agent; these same MCP servers are **also forwarded to External Agents via ACP**, so one
  `context_servers` entry serves both Zed's native agent and any ACP-hosted external agent.
- Source: https://zed.dev/docs/ai/mcp

## 9. Agent Client Protocol (ACP) — distribution/hosting channel (the defining Zed quirk)

- ACP is an **open standard for agent communication** that lets Zed host any compliant external
  coding agent as a first-class thread in the Agent Panel / Threads Sidebar, while the external
  agent retains its own runtime, auth, model selection, tools, and native configuration files (e.g.
  gald3r's own `CLAUDE.md`/`.claude/` tree for a Claude-Code-via-ACP session is untouched by Zed).
  Common ACP-hosted agents: Claude, Codex, Copilot, Cursor, OpenCode, Pi Coding Agent, Kimi Code.
- Registry-installed agents are added via `zed: acp registry`; custom agents are added via
  `agent: open settings` → Add Agent → Add Custom Agent, which writes an `agent_servers.<name>`
  block (`type: "custom"`, `command`, `args`, `env`) to `.zed/settings.json`.
- This makes Zed simultaneously an **editor platform** (its own Agent Panel + Skills + MCP + rules,
  covered in §§2-8) and a **distribution/hosting surface** for other vendors' agents — a gald3r
  install targeting "Zed" should be read as targeting Zed's own native surfaces; a Claude-Code- or
  Codex-via-ACP session inside Zed is separately covered by `g-skl-platform-claude` /
  `g-skl-platform-codex` and needs no additional Zed-specific files beyond what those specs already
  ship.
- Source: https://zed.dev/docs/ai/external-agents

---

## Known Gaps vs. Cursor Reference

| # | Gap | Severity |
|---|---|---|
| 1 | **No project-scoped agent roster** — Zed's own agent is Profile/UI-configured; third-party agents attach via ACP (`agent_servers` in `.zed/settings.json`, itself Zed-owned); gald3r's `g-agnt-*.md` set has no committed-file landing zone. (§3) | High |
| 2 | **No hand-authored hooks** — no published event taxonomy/schema; Tool Permissions/Sandboxing are access-control, not an extensible event bus. gald3r `g-hk-*.py` have no verified wiring target. (§6) | High |
| 3 | **No dedicated commands surface** — only one built-in slash command (`/compact`) is documented; gald3r's `@g-*` commands must ride on the Skills tree instead of a separate `commands/` folder. (§5) | Medium |
| 4 | **`.zed/settings.json` is a single Zed-owned file** covering `agent_servers` + `context_servers` + all other editor settings — gald3r cannot safely ship a full replacement file without risking clobbering unrelated user settings; a merge-snippet/documentation-only approach is required until a safe JSON-merge installer exists. (§8, §9) | Medium |
| 5 | **`.rules` outranks `AGENTS.md`** if both exist — a project migrating from Cursor/Windsurf/Cline may have a stale `.rules` file that silently wins over gald3r's `AGENTS.md` until removed. (§2, §7) | Low |

**Strongest parity points** (not gaps): Skills (§4) are a drop-in match for gald3r's `SKILL.md`
convention on the same `.agents/skills/` tree already used for Codex/Amp/Deep Code. Rules (§7) are
fully native `AGENTS.md` support per the open agents.md standard, with no import-shim needed. MCP
(§8) is fully native and dual-purposed (serves both Zed's own agent and every ACP-hosted external
agent from one config surface).

## Hook System

- **Type**: not supported for hand-authored hooks ❌
- **Config file**: none published for user-authored hooks
- **Events available**: none documented
- **Event payload format**: [STUB] — undocumented
- **gald3r hook files**: none verified — `g-hk-*.py` have no confirmed wiring target on Zed

## Atypical Handling

- **Zed is simultaneously an editor and an ACP host** — "platform support" here means Zed's own
  native surfaces (Skills, AGENTS.md, MCP); agents hosted *inside* Zed via ACP (Claude Code, Kimi
  Code, Codex, etc.) are separately covered by their own platform specs and need no Zed-specific
  duplication.
- **`.rules` precedence quirk** — do not assume `AGENTS.md` is always read; check for a pre-existing
  `.rules` (or `.cursorrules`/`.windsurfrules`/`.clinerules`/etc.) file first, since any of those
  silently outrank `AGENTS.md` per the fixed fallback list.
- **Personal AGENTS.md is machine-global, not project-scoped** — `~/.config/zed/AGENTS.md` applies
  to every workspace on that machine; gald3r does not write to it (out of scope for a per-project
  overlay), but should document it as the personal-scope equivalent.
- **No hooks surface, no dedicated commands file format** — do not fabricate either.

## gald3r Integration Notes

- Ship gald3r's rule content in the project-root **`AGENTS.md`** (not `.rules`) — Zed reads this
  natively provided no higher-precedence file (`.rules`, `.cursorrules`, etc.) already exists in the
  target project; flag a pre-existing `.rules` file to the user rather than silently overwriting or
  deleting it.
- gald3r skills (`g-skl-*/SKILL.md`) load natively under `.agents/skills/` — same tree already used
  for Codex/Amp/Deep Code, no adaptation needed.
- gald3r's `@g-*` "commands" have no dedicated file surface on Zed — they are satisfied entirely by
  the Skills tree (invoked via `/` or `@skill`).
- Do not ship a project-level `agents/` folder or a hooks config — neither has a project-scoped
  landing zone on Zed today per the docs.
- Do not ship a full `.zed/settings.json` replacement — document the `agent_servers`/
  `context_servers` merge snippets in `zed_instructions.md` instead, since that file is Zed-owned
  and typically carries unrelated user settings.
- Re-check on the next `@g-platform-scan-docs zed` (crawl_max_age_days: 14) — Zed's AI/ACP surface
  is actively expanding (ACP Registry contents, additional External Agents, possible future hooks).

---

## Capability Summary (copy into PLATFORM_STATUS.md row)

| Hooks | Rules | Skills | Commands | MCP | Docs Fresh |
|---|---|---|---|---|---|
| ❌ | ✅ | ✅ | ❌ | ✅ | ✅ |

Legend: ✅ verified working · ⚠️ partial / Cursor-generic · ❌ not supported · ❓ untested.

- **Hooks ❌** — no published event taxonomy/schema for hand-authored hooks; Tool Permissions/Agent
  Sandboxing are access-control, not an extensible hook bus.
- **Rules ✅** — native `AGENTS.md` (project + personal scope) per the open agents.md standard;
  `.rules` legacy filename outranks it if both exist.
- **Skills ✅** — native Agent Skills (`SKILL.md`, `name`/`description` frontmatter) in
  `.agents/skills/`, direct-children-only, same convention as Codex/Amp/Deep Code.
- **Commands ❌** — no dedicated user-authored slash-command file format; only one built-in
  (`/compact`) documented. Skills fill the invocation role instead.
- **MCP ✅** — native `context_servers` (local `command`/`args`/`env` or remote `url`/`headers`) in
  `.zed/settings.json`; same servers are forwarded to ACP-hosted External Agents.
- **Docs Fresh ✅** — `last_doc_scan: 2026-07-03`.

(Agents are ❌ for a project-scoped roster — Zed's own agent is Profile/UI-configured and
third-party agents attach via ACP `agent_servers`, neither of which is a gald3r-writable
per-project file — and are not one of the 5 summary columns tracked in `PLATFORM_STATUS.md`,
consistent with other specs.)

---

## Verification Evidence (docs crawl 2026-07-03, https://zed.dev/docs/ai/*)

| Capability | How verified |
|---|---|
| ACP hosting of External Agents (Claude, Codex, Copilot, Cursor, OpenCode, Pi Coding Agent, Kimi Code) | /docs/ai/external-agents — "Zed hosts the thread in the Agent Panel and Threads Sidebar, while the External Agent usually owns its own runtime, auth, model selection, tools, and native configuration"; install via `zed: acp registry`; custom agents via `agent: open settings` → Add Agent → Add Custom Agent |
| `agent_servers` custom-agent JSON shape (`type`, `command`, `args`, `env`) | /docs/ai/external-agents — example `agent_servers.my-agent` block with `"type": "custom"`, `"command": "node"`, `"args": [...]`, `"env": {}` |
| `.rules`-first, 9-entry project-instructions fallback list; personal `~/.config/zed/AGENTS.md` (`%APPDATA%\Zed\AGENTS.md` on Windows); project wins over personal on conflict | /docs/ai/instructions — precedence list `.rules > .cursorrules > .windsurfrules > .clinerules > .github/copilot-instructions.md > AGENT.md > AGENTS.md > CLAUDE.md > GEMINI.md`; personal file always-on across every workspace |
| Native `AGENTS.md` support as primary/recommended format; `.rules` kept for back-compat | /docs/ai/instructions — Zed natively supports the agents.md standard; `.rules` documented as legacy/back-compat filename |
| Skills: `SKILL.md` frontmatter (`name`, `description`, optional `disable-model-invocation`), `.agents/skills/` (project) + `~/.agents/skills/` (global), direct-children-only, project overrides global on name clash | /docs/ai/skills — frontmatter field table, "Skills must be direct children of the skills root", "the project-local skill takes precedence" |
| `context_servers` MCP shape — local (`command`/`args`/`env`) vs remote (`url`/`headers`), OAuth prompt on missing Authorization header, forwarded to External Agents via ACP | /docs/ai/mcp — example JSON for both local and remote server shapes; "forwarded to External Agents via the Agent Client Protocol" |
| Only `/compact` documented as a slash command; no dedicated custom-command file format | /docs/ai/agent-panel — "You can compact manually by typing /compact in the message editor"; no other slash-command mechanism documented |
| No dedicated hooks/lifecycle-events docs page | Full AI docs nav (Overview, AI Quick Start, AI by Company, Agents [Zed Agent, External Agents, Terminal Threads], Agent Panel, Agent Settings, Agent Profiles, Tools [Tool Permissions, Agent Sandboxing, MCP], Skills, Instructions, Parallel Agents, Inline Assistant, LLM Providers, Edit Prediction, AI Privacy) — no "Hooks" entry |
| AGENTS.md open standard — root-of-repo convention, nearest-file-wins for monorepos, no described merge beyond directory proximity, Zed listed as an adopter | https://agents.md/ — "created at the root of the repository"; "place another AGENTS.md inside each package... the closest one takes precedence"; Zed listed among 20+ supported agents |
