---
subsystem_memberships: [PLATFORM_INTEGRATION]
platform: augment
authoring_path: update
docs_url: https://docs.augmentcode.com
docs_url_secondary:
  - https://docs.augmentcode.com/cli/custom-commands
  - https://docs.augmentcode.com/cli/subagents
  - https://docs.augmentcode.com/cli/skills
  - https://docs.augmentcode.com/cli/hooks
  - https://docs.augmentcode.com/cli/rules
  - https://docs.augmentcode.com/cli/integrations
  - https://docs.augmentcode.com/cli/plugins
crawl_max_age_days: 14
vault_doc_path: research/platforms/augment/
last_doc_scan: 2026-06-02
reference: g-skl-platform-cursor
status: ✅
task: T1474
---

# PLATFORM_SPEC.md — Augment Code (Auggie CLI + VS Code / JetBrains)

Augment Code ships as a VS Code extension, a JetBrains plugin, and the **`auggie` CLI**. As of
early-2026 the Auggie CLI natively supports **all six** gald3r-relevant extension primitives —
custom slash commands, rules/memory, subagents, Agent Skills, lifecycle hooks, and MCP — bundled
through a **Claude-Code-compatible plugin/marketplace** system. Critically for gald3r, Auggie reads
**`CLAUDE.md` and `AGENTS.md`** and discovers commands/agents/skills from **`.claude/` and
`.agents/`** in addition to `.augment/`, so gald3r's Claude-Code artifacts are **largely drop-in
reusable** on Augment.

**Authoring path**: UPDATE. **Verified 2026-06-02** against https://docs.augmentcode.com (see
Verification Evidence). This **supersedes** the prior spec (`last_doc_scan: never`) which incorrectly
marked hooks/skills/agents/commands as unsupported — they are now all NATIVE in the Auggie CLI.

> **Surface split:** the full extensibility (commands/rules/agents/skills/hooks/MCP/plugins) lives in
> the **Auggie CLI**. The IDE extensions expose a narrower surface (rules/guidelines + MCP + the
> Context Engine). Where a feature is CLI-only or has an IDE caveat it is noted inline.

---

## 1. Folder Hierarchy

```
<project-root>/
├── CLAUDE.md / AGENTS.md          ← instruction files Auggie reads (Claude/agents compatible)
├── .augment-guidelines            ← legacy single-file workspace guidelines (root)
└── .augment/
    ├── rules/        *.md          ← always_apply / agent_requested / manual
    ├── commands/     *.md          ← custom slash commands
    ├── agents/       *.md          ← subagents (markdown + YAML frontmatter)
    ├── skills/       <name>/SKILL.md  ← Agent Skills (agentskills.io standard)
    └── settings.json              ← hooks + MCP configuration
```

Auggie **also** discovers `.claude/commands|skills|agents` and `.agents/commands|skills` (workspace
or `~/`). gald3r's `.claude/`-style trees therefore work on Augment with **no Augment-specific port**.

**gald3r writes**: any of the above; for maximum reuse, gald3r's Claude-Code tree (`.claude/…` +
`CLAUDE.md`/`AGENTS.md`) is loaded as-is.
**Augment owns**: the `.augment/` namespace, `settings.json` schema, and the **Context Engine** index
(semantic codebase retrieval — Augment-managed, not a gald3r-writable surface).

---

## 2. AI Instruction File

Auggie reads, in precedence order: `--rules` flag → **`CLAUDE.md`** → **`AGENTS.md`** →
`.augment-guidelines` → `.augment/rules/*.md` (walks up the directory tree). No dedicated `AUGMENT.md`
is required — gald3r's `AGENTS.md` / `CLAUDE.md` are first-class inputs.

---

## 3. Agents Support — ✅ NATIVE

- **Subagents**: markdown + YAML frontmatter (`name`, `description`, `color`, `model`, `tools`
  allowlist, `disabled_tools` denylist) in `./.augment/agents/` or `~/.augment/agents/`; invoked by
  name (e.g. "use the code-review agent"); multiple subagents run in parallel from the CLI.
  Announced **2026-01-09**.
- gald3r `g-agnt-*` definitions map directly to Auggie subagent files.
- Source: https://docs.augmentcode.com/cli/subagents

## 4. Skills Support — ✅ NATIVE

- **Agent Skills** (agentskills.io `SKILL.md` open standard) discovered in `.augment/skills/`,
  **`.claude/skills/`**, or **`.agents/skills/`** (workspace or home). Every discovered skill is
  registered as its own slash command (directory name). Frontmatter: `name` (lowercase+hyphens),
  `description`.
- gald3r `g-skl-*/SKILL.md` load natively — including straight from `.claude/skills/`.
- Source: https://docs.augmentcode.com/cli/skills

## 5. Commands / Workflows — ✅ NATIVE

- **Custom slash commands**: markdown in `.augment/commands/*.md` (also `.claude/commands/`,
  `.agents/commands/`); invoked `/<command-name>` with args; frontmatter `description`,
  `argument-hint`, `model`.
- gald3r `@g-*` / `/g-*` commands map directly.
- Source: https://docs.augmentcode.com/cli/custom-commands

## 6. Hooks System — ✅ NATIVE

- **Lifecycle hooks** configured in `.augment/settings.json`. Events: **PreToolUse** (blocking),
  **PostToolUse**, **Stop**, **SessionStart**, **SessionEnd**. Event data arrives via **stdin JSON**;
  results via exit codes / output streams. Commands may be `.sh` / **`.ps1`** / `.cmd` / `.bat` —
  **PowerShell is explicitly supported**, so gald3r `g-hk-*.ps1` hooks wire **natively**
  (SessionStart context injection, PreToolUse `.gald3r/` guards, pre-commit gates, etc.).
- Source: https://docs.augmentcode.com/cli/hooks

## 7. Rules / Memory — ✅ NATIVE

- `.augment/rules/*.md` (`always_apply` / `agent_requested` / `manual` types) + root
  `.augment-guidelines` + **reads `CLAUDE.md` & `AGENTS.md`**. `always_apply` injected into every
  prompt; user rules in `~/.augment/rules/` are always `always_apply`. Plain `.md` (not Cursor's
  `.mdc` — parity sync swaps the extension). `manual` rules are **IDE-only** (the `auggie` CLI skips
  them — use `always_apply`/`agent_requested` for CLI-relevant gald3r rules).
- gald3r `g-rl-*` map to `always_apply` (for `alwaysApply: true`) or `agent_requested` (for
  `description:`-scoped).
- Source: https://docs.augmentcode.com/cli/rules

## 8. MCP Support — ✅ NATIVE

- MCP servers persisted in `~/.augment/settings.json` (initialize on startup); managed via
  `auggie mcp add` / `list` / `remove`; IDE "Easy MCP" install in the extensions.
- Source: https://docs.augmentcode.com/cli/integrations

## 9. Plugins / Marketplace — distribution channel

- **Claude-Code-compatible** plugin + marketplace system (Git-repo marketplaces). A single plugin
  bundle can ship commands + subagents + rules + hooks + MCP servers + skills **together**
  (backwards-compatible with Claude Code's `.claude-plugin` format). Added via
  `auggie plugin marketplace add owner/repo`; browsed via `/plugins`. **This is the natural
  distribution channel for a gald3r Augment plugin.**
- Source: https://docs.augmentcode.com/cli/plugins

---

## Parity vs. Cursor Reference

Augment now reaches **near-full parity** with the Cursor reference (`g-skl-platform-cursor`): native
**commands, rules, agents, skills, hooks, and MCP**. Caveats: the full surface is CLI-only (IDE
extensions are narrower), and `manual`-type rules are IDE-only. The **Context Engine** (semantic
codebase index) is an Augment-native bonus with no Cursor analog — retrieval, not a writable store.

**Reuse note (important):** because Auggie reads `CLAUDE.md`/`AGENTS.md` and discovers `.claude/` +
`.agents/` trees, gald3r's **Claude-Code platform artifacts are largely reusable on Augment without a
separate port** — the cheapest path to a high-parity Augment install is to ship the gald3r `.claude/`
tree (or a Claude-Code-format plugin bundle).

## Hook System

- **Type**: native (settings.json hooks)
- **Config file**: `.augment/settings.json`
- **Events available**: PreToolUse, PostToolUse, Stop, SessionStart, SessionEnd
- **Event payload format**: JSON via stdin; result via exit codes / output streams
- **Command extensions**: `.sh`, `.ps1`, `.cmd`, `.bat` (PowerShell supported)
- **gald3r hook files**: `g-hk-*.ps1` wire natively via the events above

## Atypical Handling

- Two surfaces: the **Auggie CLI** (full extensibility) and the **IDE extensions** (rules + MCP +
  Context Engine). Target the CLI for full gald3r parity.
- Claude-Code interop: `.claude/` trees + `CLAUDE.md` are loaded directly — prefer reusing them.

## gald3r Integration Notes

- Ship gald3r's `.claude/`-format tree (commands/skills/agents/hooks/rules) — Auggie discovers it.
- Hooks fire natively (`.ps1` supported); no need to degrade session-start/pre-commit to manual.
- Re-verify on the next `@g-platform-scan-docs augment` (crawl_max_age_days: 14).

---

## Capability Summary (copy into PLATFORM_STATUS.md row)

| Hooks | Rules | Skills | Commands | MCP | Docs Fresh |
|---|---|---|---|---|---|
| ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |

Legend: ✅ verified working · ⚠️ partial / Cursor-generic · ❌ not supported · ❓ untested.

---

## Verification Evidence (docs crawl 2026-06-02, https://docs.augmentcode.com)

| Capability | How verified |
|---|---|
| Commands | /cli/custom-commands — `.augment/commands/*.md`; also reads `.claude/commands/`, `.agents/commands/` |
| Rules | /cli/rules — precedence reads `CLAUDE.md` + `AGENTS.md` above `.augment/rules` (always_apply/agent_requested/manual) |
| Agents | /cli/subagents — `.augment/agents/` md+YAML; parallel subagents; announced 2026-01-09 |
| Skills | /cli/skills — agentskills.io `SKILL.md` in `.augment/.claude/.agents` skills/; each registered as a slash command |
| Hooks | /cli/hooks — `.augment/settings.json`; PreToolUse/PostToolUse/Stop/SessionStart/SessionEnd; `.ps1` supported |
| MCP | /cli/integrations — `~/.augment/settings.json`, `auggie mcp add/list/remove` |
| Plugins | /cli/plugins — Claude-Code `.claude-plugin`-compatible bundles (commands+agents+rules+hooks+MCP+skills) |
| Cross-compat | Auggie discovers `.claude/` + `.agents/` and reads `CLAUDE.md`/`AGENTS.md` → gald3r Claude artifacts reusable |
