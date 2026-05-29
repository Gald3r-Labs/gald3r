---
subsystem_memberships: [PLATFORM_INTEGRATION]
spec_for: antigravity
---

# PLATFORM_SPEC.md — antigravity (Google Antigravity)

> **Last doc scan**: 2026-05-28 — crawled live:
> [skills](https://antigravity.google/docs/skills) ✅ |
> [mcp](https://antigravity.google/docs/mcp) ✅ |
> [plugins](https://antigravity.google/docs/plugins) ✅ |
> [hooks](https://antigravity.google/docs/hooks) ✅ |
> [rules-workflows](https://antigravity.google/docs/rules-workflows) ⏱️ timed out |
> [sidecars](https://antigravity.google/docs/sidecars) ⏱️ timed out
>
> **Antigravity 2.0** — re-launched ~2026-05-19.

---

## Header / Metadata

```yaml
platform: antigravity
docs_url: https://antigravity.google/docs/home
docs_url_skills: https://antigravity.google/docs/skills
docs_url_mcp: https://antigravity.google/docs/mcp
docs_url_plugins: https://antigravity.google/docs/plugins
docs_url_hooks: https://antigravity.google/docs/hooks
docs_url_secondary: https://codelabs.developers.google.com/getting-started-google-antigravity
crawl_max_age_days: 7
vault_doc_path: research/platforms/antigravity/
last_doc_scan: 2026-05-28
reference: g-skl-platform-cursor
status: ✅                           # hooks/plugins/skills/MCP all verified from live docs
```

---

## 1. Folder Hierarchy

Antigravity 2.0 splits config between **project-local** dirs and **user-global** state under
`~/.gemini/` (shared with Gemini CLI's state tree).

```
<project_root>/
├── AGENTS.md                        ← ✅ project-root instruction file
├── .agents/                         ← ✅ primary workspace customization root (Antigravity 2.0)
│   ├── skills/                      ← ✅ workspace-scoped skills
│   │   └── <skill-name>/
│   │       ├── SKILL.md             ← required
│   │       ├── scripts/             ← optional
│   │       └── references/          ← optional
│   ├── plugins/                     ← ✅ workspace-scoped plugin bundles
│   │   └── <plugin-name>/
│   │       ├── plugin.json          ← required marker { "name": "..." }
│   │       ├── mcp_config.json      ← optional MCP servers
│   │       ├── hooks.json           ← optional hooks
│   │       ├── skills/              ← optional skills within plugin
│   │       └── rules/               ← optional rules/*.md within plugin
│   └── hooks.json                   ← ✅ workspace-level hooks (outside any plugin)
└── .antigravity/
    └── mcp.json                     ← ✅ project-local MCP config { "mcpServers": { ... } }

~/.gemini/config/                    ← ✅ user-global customizations
├── skills/                          ← global skills (all workspaces)
│   └── <skill-name>/
│       └── SKILL.md
├── plugins/                         ← global plugin bundles
│   └── <plugin-name>/
│       └── plugin.json
└── hooks.json                       ← global hooks

~/.gemini/antigravity/               ← ✅ user-global Antigravity state
├── mcp_config.json                  ← global MCP config (same mcpServers shape)
├── global_workflows/                ← saved-prompt workflows (slash commands, /)
└── mcp_oauth_tokens.json            ← OAuth tokens (auto-managed)
```

- **gald3r writes**: `AGENTS.md`, `.agents/skills/<name>/SKILL.md`, `.agents/hooks.json`, `.antigravity/mcp.json`
- **gald3r plugin bundle**: `.agents/plugins/gald3r/` with `plugin.json`, `skills/`, `rules/`, `hooks.json`
- **Platform owns**: `~/.gemini/` global state, IDE settings, subagent runtime

---

## 2. AI Instruction File

✅ **`AGENTS.md`** at project root — the verified primary gald3r integration point.
Standard markdown. gald3r generates it (shared file, not Antigravity-bespoke).

---

## 3. Skills Support

✅ **Fully verified (2026-05-28)** — [antigravity.google/docs/skills](https://antigravity.google/docs/skills)

### Skill file structure

```
<skill-name>/
├── SKILL.md          ← required; YAML frontmatter with description:
├── scripts/          ← optional scripts the agent can run
└── references/       ← optional reference documents
```

### SKILL.md frontmatter

```yaml
---
name: my-skill-name           # optional; defaults to folder name
description: >                # required — agent sees this when deciding to activate
  Generates unit tests for Python code using pytest conventions.
---
```

### Skill locations

| Path | Scope |
|---|---|
| `<workspace>/.agents/skills/<name>/` | Workspace (default, Antigravity 2.0) |
| `<workspace>/_agents/skills/<name>/` | Workspace (alternate root) |
| `~/.gemini/config/skills/<name>/` | Global (all workspaces) |
| Inside plugin: `.agents/plugins/<p>/skills/<name>/` | Plugin-bundled |

> **Note**: `.agent/skills/` (singular) still works for backward compatibility.

### Progressive disclosure

1. Discovery: agent sees all skill names + descriptions at conversation start
2. Activation: agent reads full `SKILL.md` when skill looks relevant
3. Execution: agent follows instructions. Mention skill by name to force activation.

### gald3r mapping

Deploy `g-skl-*` as `.agents/skills/<name>/` with `SKILL.md` + `scripts/`. This is the
**primary gald3r skills integration point**.

---

## 4. Plugins Support

✅ **Fully verified (2026-05-28)** — [antigravity.google/docs/plugins](https://antigravity.google/docs/plugins)

Plugins are **namespaced bundles** grouping skills, rules, MCP servers, and hooks into one package.

### Plugin structure

```
<plugin-name>/
├── plugin.json       ← required marker
├── mcp_config.json   ← optional: MCP server definitions (mcpServers shape)
├── hooks.json        ← optional: hooks definition
├── skills/           ← optional: skill subdirs, each with SKILL.md
│   └── <skill-name>/
│       └── SKILL.md
└── rules/            ← optional: always-apply rules as .md files
    └── <rule-name>.md
```

### plugin.json

```json
{
  "name": "my-custom-plugin"
}
```

`name` defaults to directory name if omitted.

### Plugin locations

| Path | Scope |
|---|---|
| `<workspace>/.agents/plugins/<name>/` | Workspace |
| `<workspace>/_agents/plugins/<name>/` | Workspace (alternate) |
| `~/.gemini/config/plugins/<name>/` | Global |

Google also provides **bundled plugins** (Build with Google) browseable from the Customizations UI.

### gald3r plugin bundle strategy

Create `.agents/plugins/gald3r/` with:
- `plugin.json` — `{ "name": "gald3r" }`
- `rules/g-rl-*.md` — always-apply gald3r rules
- `skills/` — gald3r skills
- `hooks.json` — gald3r lifecycle hooks

This is the cleanest single-bundle install for gald3r on Antigravity.

---

## 5. Hooks Support

✅ **Fully verified (2026-05-28)** — [antigravity.google/docs/hooks](https://antigravity.google/docs/hooks)

Hooks run custom scripts at specific points in Antigravity's execution loop.

### Config file

`hooks.json` — place in `.agents/` (workspace-level) or inside a plugin's root, or `~/.gemini/config/`.

### hooks.json format

```json
{
  "my-linter-hook": {
    "PostToolUse": [
      {
        "matcher": "run_command",
        "hooks": [
          {
            "type": "command",
            "command": "./scripts/lint.sh",
            "timeout": 10
          }
        ]
      }
    ]
  },
  "safety-gate": {
    "enabled": false,
    "PreToolUse": [
      {
        "matcher": "run_command",
        "hooks": [{ "command": "./scripts/safety-check.sh" }]
      }
    ]
  },
  "session-start": {
    "PreInvocation": [
      {
        "type": "command",
        "command": "./scripts/reminder.sh"
      }
    ]
  }
}
```

### Supported events

| Event | Fires | Matcher |
|---|---|---|
| `PreToolUse` | Before a tool executes | Tool name regex (e.g. `run_command`, `browser_.*`) |
| `PostToolUse` | After a tool completes | Tool name regex |
| `PreInvocation` | Before model is called | N/A (ignored) |
| `PostInvocation` | After tool calls finish | N/A (ignored) |
| `Stop` | When execution loop terminates | N/A (ignored) |

### PreToolUse / PostToolUse matchers

Regex matched against tool name. Examples:
- `""` or `"*"` — match all tools
- `"run_command"` — exact match
- `"run_command|view_file"` — either tool
- `"browser_.*"` — any browser tool

### Hook handler fields

| Field | Type | Description |
|---|---|---|
| `type` | string | Optional. Only `"command"` supported. Defaults to `"command"` |
| `command` | string | Required. Shell command to execute |
| `timeout` | integer | Optional. Seconds. Defaults to 30 |
| `enabled` | boolean | Optional (on hook group). `false` to disable without removing |

### Input/Output contract

Hooks receive JSON on stdin, return JSON on stdout.

**Common stdin fields** (all events):

| Field | Description |
|---|---|
| `conversationId` | UUID of active conversation |
| `workspacePaths` | Array of absolute workspace paths |
| `transcriptPath` | Path to `transcript.jsonl` |
| `artifactDirectoryPath` | Path to artifacts dir |

**PreToolUse stdin** also includes: `toolCall.name`, `toolCall.args`, `stepIdx`

**PreToolUse stdout** (decision gate):

| Field | Values |
|---|---|
| `decision` | `"allow"` / `"deny"` / `"ask"` / `"force_ask"` |
| `reason` | Optional explanation |
| `permissionOverrides` | Optional array of resource strings |

**PreInvocation stdout**: `{ "injectSteps": [...] }` — inject steps before model call

**PostInvocation stdout**: `{ "injectSteps": [...], "terminationBehavior": "force_continue"|"terminate"|"" }`

**Stop stdout**: `{ "decision": "continue"|"", "reason": "..." }`

### Supported tool names for matchers

File ops: `view_file`, `write_to_file`, `replace_file_content`, `multi_replace_file_content`, `list_dir`, `find_by_name`
Search: `grep_search`, `search_web`, `read_url_content`
System: `run_command`, `manage_task`, `schedule`, `list_permissions`, `ask_permission`
Agents: `invoke_subagent`, `define_subagent`, `send_message`, `manage_subagents`
Media: `ask_question`, `generate_image`

### gald3r hooks mapping

gald3r's PowerShell hooks (`g-hk-*.ps1`) map naturally:

| gald3r hook | Antigravity event | Matcher |
|---|---|---|
| session start | `PreInvocation` (invocationNum == 0) | N/A |
| pre-tool safety | `PreToolUse` | `"run_command"` |
| post-tool lint | `PostToolUse` | `"write_to_file\|replace_file_content"` |
| session end | `Stop` | N/A |

---

## 6. Rules / Always-Apply Instructions

✅ **Confirmed structure via Plugins doc (2026-05-28)**

Rules are markdown files in a `rules/` directory inside a plugin bundle. They define constraints
or guidelines the agent follows. Standalone rules path (outside a plugin) not yet confirmed.

### Rule file format

```
rules/
└── g-rl-00-always.md     ← plain markdown, no special frontmatter required
```

### Where rules live

| Path | Scope |
|---|---|
| `.agents/plugins/<name>/rules/<rule>.md` | Plugin-bundled (confirmed) |
| `.agents/rules/<rule>.md` | Workspace standalone (⚠️ unconfirmed — page timed out) |
| `~/.gemini/config/rules/<rule>.md` | Global standalone (⚠️ unconfirmed) |

### gald3r mapping

Bundle gald3r `g-rl-*` rules as markdown files inside `.agents/plugins/gald3r/rules/`.
This is confirmed to work via the plugins doc. Standalone rules/ path needs install test.

---

## 7. Commands / Workflows

⚠️ **Partial.** Slash commands confirmed; workflow file format TBD (rules-workflows page timed out).

### Built-in slash commands

| Command | Description |
|---|---|
| `/goal` | Run until task fully complete (no intermediate input) |
| `/grill-me` | Ask clarifying questions before implementing |
| `/schedule` | One-time timer or recurring cron (via Sidecars) |
| `/browser` | Enable browser primitives for session (requires Chrome) |

Saved workflows stored at `~/.gemini/antigravity/global_workflows/`. File format for custom
entries not yet confirmed — rules-workflows page timed out during crawl.

---

## 8. MCP Support

✅ **Fully verified (2026-05-28)** — [antigravity.google/docs/mcp](https://antigravity.google/docs/mcp)

### Config locations

| Path | Scope |
|---|---|
| `.antigravity/mcp.json` | Project-local |
| `~/.gemini/antigravity/mcp_config.json` | Global (via Settings → Customizations → View raw config) |
| Inside plugin: `.agents/plugins/<name>/mcp_config.json` | Plugin-bundled |

### Config shape

```json
{
  "mcpServers": {
    "serverName": {
      "command": "path/to/executable",
      "args": ["--arg1", "value1"],
      "env": { "API_KEY": "your-api-key" }
    }
  }
}
```

### Transport options

| Property | Type | Description |
|---|---|---|
| `command` | string | Executable path (stdio transport) |
| `serverUrl` | string | URL for remote servers (Streamable HTTP) |
| `args` | string[] | CLI arguments for stdio |
| `env` | object | Environment variables |
| `cwd` | string | Working directory for stdio |
| `headers` | object | Custom HTTP headers for remote |
| `authProviderType` | string | `"google_credentials"` for ADC |
| `oauth` | object | `{ clientId, clientSecret }` |
| `disabled` | boolean | Temporarily disable without removing |
| `disabledTools` | string[] | Tool names to exclude from model |

### OAuth

- Tokens stored at `~/.gemini/antigravity/mcp_oauth_tokens.json` (auto-refreshed)
- Redirect URI to register: `https://antigravity.google/oauth-callback`
- ADC: set `authProviderType: "google_credentials"`, then `gcloud auth application-default login`

### Built-in MCP Store

Browse 30+ pre-integrated servers via `"..." → MCP Store → Browse & Install`:
BigQuery, Chrome DevTools, Firebase, GitHub, Linear, MongoDB, Neon, Notion, Stripe, Supabase, and more.

---

## 9. Agents Support

❓ **Untested.** Antigravity runs native **dynamic subagents** (`invoke_subagent`, `define_subagent`
tools) but there is no documented mechanism for file-based `g-agnt-*.md` discovery.
Fold critical agent guidance into `AGENTS.md` until confirmed.

---

## 10. Sidecars

⚠️ **Confirmed to exist (via `/schedule` slash command and sidebar); full doc timed out.**

Sidecars appear to be persistent background processes enabling scheduled/cron tasks.
The `schedule` tool accepts `DurationSeconds`, `CronExpression`, `MaxIterations`, `Prompt`.

---

## 11. Known Gaps vs. Cursor Reference

| Cursor-reference feature | Antigravity status | Classification |
|---|---|---|
| Always-apply rules | ✅ via plugin `rules/*.md`; standalone path ⚠️ | (b) platform-specific path |
| Skills (folder-per-skill) | ✅ `.agents/skills/<name>/SKILL.md` | (b) platform-specific path |
| Agents (file-based) | ❓ native subagents only | (c) documented gap |
| Commands (`@g-*`) | ⚠️ slash commands `/` confirmed; gald3r mapping TBD | (b) platform override |
| Hooks (`hooks.json`) | ✅ fully verified format + all events | (b) platform-specific format |
| MCP (`mcp.json`) | ✅ `.antigravity/mcp.json` + plugin bundle | (b) platform-specific |
| AI instruction file | ✅ `AGENTS.md` project root | (a) common |
| Plugins (bundle) | ✅ `.agents/plugins/<name>/plugin.json` | Antigravity-native feature |
| Sidecars / cron | ⚠️ `/schedule` confirmed; config format TBD | Antigravity-native feature |

---

## Capability Summary (copy into PLATFORM_STATUS.md row)

| Hooks | Rules | Skills | Commands | MCP | Docs Fresh |
|---|---|---|---|---|---|
| ✅ | ✅ | ✅ | ⚠️ | ✅ | ✅ |

Legend: ✅ verified working · ⚠️ partial / format TBD · ❌ not supported · ❓ untested.

---

## Verification Evidence

| Capability | Status | How verified |
|---|---|---|
| AGENTS.md | ✅ | Multiple public guides + docs 2026 |
| Skills at `.agents/skills/` | ✅ | Live docs `/docs/skills` 2026-05-28 |
| Global skills at `~/.gemini/config/skills/` | ✅ | Live docs `/docs/skills` 2026-05-28 |
| Plugin structure (`plugin.json`, `skills/`, `rules/`, `hooks.json`, `mcp_config.json`) | ✅ | Live docs `/docs/plugins` 2026-05-28 |
| Plugin locations (`.agents/plugins/`, `~/.gemini/config/plugins/`) | ✅ | Live docs `/docs/plugins` 2026-05-28 |
| Rules inside plugin `rules/*.md` | ✅ | Live docs `/docs/plugins` 2026-05-28 |
| Hooks config format (all 5 events) | ✅ | Live docs `/docs/hooks` 2026-05-28 |
| Hooks input/output contract (stdin/stdout JSON) | ✅ | Live docs `/docs/hooks` 2026-05-28 |
| PreToolUse decision gate (`allow`/`deny`/`ask`/`force_ask`) | ✅ | Live docs `/docs/hooks` 2026-05-28 |
| All matchable tool names | ✅ | Live docs `/docs/hooks` 2026-05-28 |
| MCP config (project + global + plugin) | ✅ | Live docs `/docs/mcp` 2026-05-28 |
| Slash commands (`/goal`, `/grill-me`, `/schedule`, `/browser`) | ✅ | Live docs `/docs/home` 2026-05-28 |
| Sidecars / cron | ⚠️ | `/schedule` tool confirmed; `/docs/sidecars` timed out |
| Workflow file format | ⚠️ | `/docs/rules-workflows` timed out |
| Standalone rules path | ⚠️ | Confirmed inside plugin; standalone path TBD |
| File-based agents | ❓ | Native subagents confirmed; file discovery NOT documented |
