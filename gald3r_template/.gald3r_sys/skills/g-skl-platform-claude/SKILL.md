---
name: g-skl-platform-claude
description: Authoritative reference for Claude Code customization in gald3r projects. Covers .claude/ folder layout, CLAUDE.md, agents, skills, commands, hooks (hooks.json format), MCP, and install verification.
crawl_max_age_days: 7
vault_doc_path: research/platforms/claude-code/
vault_docs_url: https://docs.anthropic.com/en/docs/claude-code/overview
token_budget: low
---

# g-skl-platform-claude

Activate for: setting up Claude Code in a gald3r project, authoring `.claude/` configs, understanding hooks.json format, verifying Claude parity, or answering questions about Claude Code's capabilities.

---

## Crawl Freshness Gate

```
1. Read {vault_location}/.crawl_schedule.json
2. Find entry for: https://docs.anthropic.com/en/docs/claude-code
3. If entry missing OR (today - last_crawl) > 7 days:
   → TRIGGER g-skl-recon-docs with URL https://docs.anthropic.com/en/docs/claude-code/overview
   → READ new vault notes at research/platforms/claude-code/
   → UPDATE sections: "Platform Overview", "Supported Primitives", "Common Pitfalls"
4. Else: proceed with current content
```

---

## 1. Platform Overview

**Claude Code** is Anthropic's agentic coding tool — a CLI (`claude`) with a rich interactive terminal UI plus headless/CI modes.

- **Interactive mode**: Terminal UI with file editing, bash execution, MCP tools
- **Headless mode**: `claude -p "prompt"` for scripted/CI use
- **Session continuation**: `claude --continue` / `--resume`
- **Agent SDK**: Multi-agent workflows via the Claude Agent SDK (`.claude/agents/sdk/`)
- **Hooks**: `.claude/hooks.json` — lifecycle event hooks with PowerShell/bash scripts
- **MCP**: Configured via `.mcp.json` at project root or Claude Code settings

**gald3r target**: Full parity with Cursor. Uses `.md` extension for rules (not `.mdc`).

---

## 2. Folder Layout

```
.claude/
├── CLAUDE.md                 ← Project-level always-apply instructions (loaded every session)
├── rules/                    ← Always-apply rules (.md format)
│   └── g-rl-*.md
├── skills/                   ← Agent skills (auto-discovered by Claude Code AND OpenCode AND Copilot)
│   └── g-skl-*/SKILL.md
├── agents/                   ← Agent definitions
│   ├── g-agnt-*.md
│   └── sdk/                  ← Claude Agent SDK files
├── commands/                 ← /g-* slash commands
│   └── g-*.md
├── hooks/                    ← PowerShell automation scripts
│   └── g-hk-*.ps1
├── hooks.json                ← Hook event → script mapping (Claude-specific format)
├── settings.json             ← MCP server config, permissions
└── local.settings.json       ← Local overrides (gitignored)
```

**Key**: `.claude/skills/` is auto-discovered by Claude Code, OpenCode, AND GitHub Copilot — making it the most broadly supported skill location in the gald3r ecosystem.

---

## 3. Supported Primitives

| Primitive | Location | Format | Auto-loaded? |
|---|---|---|---|
| Always-apply rules | `.claude/rules/g-rl-*.md` + `CLAUDE.md` | Markdown | ✅ Every session |
| Skills | `.claude/skills/<name>/SKILL.md` | Markdown | ✅ When relevant |
| Agents | `.claude/agents/g-agnt-*.md` | Markdown | Manual select |
| Commands | `.claude/commands/g-*.md` | Markdown | Via `/command-name` |
| Hooks | `.claude/hooks.json` + `.claude/hooks/*.ps1` | JSON config + PS1 | ✅ At lifecycle events |
| MCP servers | `.mcp.json` or `settings.json` | JSON | ✅ Auto-connect |

### hooks.json Format (Claude Code)

```json
{
  "version": 1,
  "hooks": {
    "sessionStart": [{ "command": "powershell.exe -File .claude/hooks/g-hk-session-start.ps1" }],
    "stop": [
      { "command": "powershell.exe -File .claude/hooks/g-hk-agent-complete.ps1" },
      { "command": "powershell.exe -File .claude/hooks/g-hk-nightly-learn.ps1" },
      { "command": "powershell.exe -File .claude/hooks/g-hk-session-end.ps1" }
    ],
    "beforeShellExecution": [{ "command": "powershell.exe -File .claude/hooks/g-hk-validate-shell.ps1" }]
  }
}
```

Note: Claude's `hooks.json` uses `"command"` (a full shell string), NOT Copilot's `"type"/"bash"/"powershell"` object format.

**Session lifecycle hooks (gald3r ships three on `stop`)**:
- `g-hk-agent-complete.ps1` — persists chat log, writes next-session reflection hint
- `g-hk-nightly-learn.ps1` — every N sessions, spawns LLM extraction into `.gald3r/learned-facts.md` (configurable in `AGENT_CONFIG.md`)
- `g-hk-session-end.ps1` (T1057) — appends a structured record to `.gald3r/logs/session_end.log` and overwrites `.gald3r/logs/session_end_pending.json` for a future `memory_capture_session` MCP consumer (T1263 wires that consumer)

All three are non-blocking. PS hooks cannot call MCP tools directly, so the actual session-summary capture is staged by `g-hk-session-end` and actioned later — either by the next session-start hook, the `g-learn` skill, or a scheduled drainer.

**gald3r-internal lifecycle events (T1055 — `pre_skill` / `post_skill` / `pre_session` / `post_session`)**:

Beyond the harness-native events (`sessionStart`, `stop`, `beforeShellExecution`, `PreToolUse`), gald3r defines four **gald3r-internal** lifecycle events. Claude Code does NOT expose a native skill-boundary event nor a gald3r-session-boundary event, so these are dispatched by the gald3r skill/command runner (or fired manually) and are **NOT auto-wired** into `hooks.json` — exactly like `manual` and `nightly` hooks. They enable per-skill tracing/timing and per-session observability without editing skill bodies.

| Event | Payload (stdin JSON) | Fires |
|-------|----------------------|-------|
| `pre_skill` | `skill_name`, `skill_path`, `timestamp` | Before a skill body executes |
| `post_skill` | `skill_name`, `skill_path`, `timestamp` | After a skill body finishes |
| `pre_session` | `session_id` (if available), `project_path` | Session start (gald3r-level, not harness `sessionStart`) |
| `post_session` | `session_id` (if available), `project_path` | Session end (gald3r-level, not harness `stop`) |

Reference example hooks (under `.claude/hooks/`, each with a companion `hook.md`): `g-hk-pre-skill-timing.ps1` + `g-hk-post-skill-timing.ps1` (per-skill elapsed timing via a `.gald3r/logs/skill_timing_*.json` start marker), and `g-hk-pre-session-trace.ps1` + `g-hk-post-session-trace.ps1` (per-session duration via `.gald3r/logs/session_trace_*.json`). All four are non-blocking, emit the standard `{ continue = true }` envelope, and never touch control-plane state. The `_doc.gald3r_lifecycle_events` key in `hooks.json` documents the same contract. Scaffold new ones with `/g-hook-create <hook-name> pre_skill|post_skill|pre_session|post_session`.

**Available `PreToolUse` hooks (gald3r ships four)**:
- `g-hk-pre-tool-call-gald3r-guard.ps1` (matcher `Edit|Write|MultiEdit|NotebookEdit`) — `.gald3r/` agent-required gate
- `g-hk-pre-tool-call-prd-freeze.ps1` — refuses Edit/Write to a released/superseded PRD (C-019)
- `g-hk-pre-tool-call-member-gald3r-guard.ps1` — `controlled_member` `.gald3r/` marker-only guard
- `g-hk-pre-tool-call.ps1` (matcher `Bash|Shell|Terminal|run_terminal_cmd`, T1106) — compresses large shell/terminal output to the last N lines + summary, preserving the full block to `.gald3r/logs/tool_output_<session_id>.log`. N = `pre_tool_call_compress_lines` in `AGENT_CONFIG.md` (default 50; 0 = disabled). Non-blocking; reports 60-90% token reduction in shell-heavy sessions.

### Hook Companion `hook.md` Pattern (T1171)

Every gald3r hook script (`.claude/hooks/g-hk-*.ps1`) has a companion `hook.md` self-description file at the same path. Pattern harvested from OpenClaw Hooks Crash Course (V18 — Bdr7afGhh4I, 2026-05-13).

**Why**: a `hook.md` is both human documentation AND a runtime context payload. When a hook fires under PreToolUse (or any other event), the harness SHOULD inject the matching `hook.md` content as `additional_context` so the agent knows what the hook just did and why a tool call was blocked / allowed / rewritten.

**5-section template** (use exactly):

```markdown
# Hook: <hook-name>

## Fires On
<event, trigger, matcher, idempotency story>

## What It Does
<2-3 sentence description>

## Side Effects
<files written, processes run, state changed, allow / deny verdicts>

## Related Tasks
<T### IDs / rule IDs / constraint IDs>
```

Target length ~30-60 lines per `hook.md` — lean by design. Full design docs live in `docs/<timestamp>_*_HOOK_*.md`.

**Wiring** — reference the companion via `"_hook_md"` per entry in `hooks.json`:

```json
{
  "type": "command",
  "command": "...powershell.exe ... -File .claude/hooks/g-hk-pre-tool-call-gald3r-guard.ps1",
  "_hook_md": ".claude/hooks/g-hk-pre-tool-call-gald3r-guard.md"
}
```

Top-level `_doc` in `hooks.json` documents the contract for new contributors. Scaffold new hooks via `/g-hook-create <hook-name> <event>`. See `skills/g-skl-platform-cursor/SKILL.md` §11a for the cross-platform authoring contract.

---

## 4. gald3r Parity Tier

| Content | Slim | Full | Adv |
|---|---|---|---|
| rules/ (8 always-apply) | ✅ | ✅ | ✅ |
| skills/ | ✅ | ✅ | ✅ |
| agents/ | ✅ | ✅ | ✅ |
| commands/ | ✅ | ✅ | ✅ |
| hooks/ + hooks.json | ✅ | ✅ | ✅ |
| CLAUDE.md | ✅ | ✅ | ✅ |

---

## 5. Vault Doc Location

```
{vault_location}/research/platforms/claude-code/
```

Crawl entry: `https://docs.anthropic.com/en/docs/claude-code/overview`

---

## 6–7. Crawl Freshness Gate & Self-Update

See gate template in header. Update sections 1, 3, 9 after fresh crawl.

---

## 8. Key URLs

| Purpose | URL |
|---|---|
| Claude Code overview | https://docs.anthropic.com/en/docs/claude-code/overview |
| Hooks reference | https://docs.anthropic.com/en/docs/claude-code/hooks |
| MCP integration | https://docs.anthropic.com/en/docs/claude-code/mcp |
| Agent SDK | https://docs.anthropic.com/en/docs/claude-code/agent-sdk |

---

## 9. Common Pitfalls

1. **`hooks.json` format differs from Copilot** — Claude uses `"command"` (full shell string). Copilot uses `"type"/"powershell"/"bash"` keys. They are NOT interchangeable.
2. **`.claude/skills/` is shared with OpenCode and Copilot** — changes here affect all three platforms. Do not add Cursor-only or Claude-only content.
3. **Rules use `.md` not `.mdc`** — Unlike Cursor, Claude rules are plain `.md`. Parity sync handles the extension rename.
4. **CLAUDE.md vs rules/**: CLAUDE.md is a single always-apply file (project-level). `rules/` holds individual modular rules. Both are loaded; CLAUDE.md takes precedence for project identity.
5. **Headless mode flags**: `--dangerously-skip-permissions` should never be used in production; use `--allowedTools` to restrict scope instead.

---

## 10. Install Verification Checklist

```
✅ .claude/CLAUDE.md exists (project identity)
✅ .claude/rules/ has g-rl-*.md files (parity with .cursor/rules/)
✅ .claude/skills/ has gald3r core skills
✅ .claude/agents/ has g-agnt-*.md files
✅ .claude/commands/ has g-*.md files
✅ .claude/hooks.json is valid JSON with sessionStart hook
✅ .mcp.json exists (if using MCP tools)
```

---

## Portable Deployment (OpenClaude Portable)

[OpenClaude Portable](https://github.com/techjarves/OpenClaude-Portable) is an MIT-licensed bundle that packages an OpenClaw engine (a Claude-Code-compatible CLI wrapper) into a single folder runnable from a USB drive. It is the recommended pattern for using gald3r at university labs, client sites, locked-down corporate machines, demo laptops, and other environments where Claude Code itself cannot be installed.

Vault reference: `{vault_location}/research/repos/openclaude_portable.md` (full evaluation, license, and risk notes).

### When to use portable vs. full Claude Code install

| Situation | Recommended path |
|---|---|
| Personal dev machine with admin rights | Full Claude Code install (this skill's default) |
| Locked-down corporate / client / shared lab machine | OpenClaude Portable on a USB drive |
| Travel / demo with no install rights and no reliable network | OpenClaude Portable + bundled Ollama (offline mode) |
| Restricted region or no Anthropic subscription | OpenClaude Portable + Nvidia NIM / OpenRouter free tier |
| Hot-handing a gald3r project between machines without per-host setup | OpenClaude Portable (zero host traces after unplug) |

### Setup steps (portable mode)

1. Download the OpenClaude Portable release ZIP (~150 MB base) onto a USB drive (FAT32 / exFAT both work).
2. Extract in place. The bundle is self-contained: engine, providers, optional Ollama, optional model cache.
3. Inside the extracted folder, configure providers in `config/providers.yaml`. At minimum one provider is required; six are supported out of the box including free tiers (Nvidia NIM 1000 credits/month, OpenRouter, local Ollama).
4. Clone or mount the gald3r project under the bundle's project workspace.
5. Launch the portable engine from the bundle's launcher script (`run.bat` / `run.sh`). The engine reads gald3r primitives from the project's `.claude/` directory the same way Claude Code itself does.

### What gald3r primitives work in portable context

| Primitive | Works portable? | Notes |
|---|---|---|
| `.claude/CLAUDE.md` identity overlay | ✅ Full | Read identically to native Claude Code. |
| `.claude/rules/` always-apply rules | ✅ Full | Loaded at every conversation start. |
| `.claude/skills/` and `.claude/commands/` | ✅ Full | Skill discovery, command dispatch, and `/g-*` aliases all work. |
| `.claude/agents/` | ✅ Full | Subagent dispatch via `@g-agnt-*` is engine-level and unaffected. |
| `.claude/hooks.json` + `.ps1` hook scripts | ⚠️ Partial | Hooks fire when the portable engine supports the same lifecycle events. Confirm the running OpenClaw engine version's hook contract before relying on hook side effects (e.g. `g-hk-session-start.ps1` context injection). |
| MCP tools (gald3r_valhalla, gald3r_muninn) | ⚠️ Degraded | Local MCP requires Docker; on locked-down machines Docker is usually unavailable. Use a remote MCP URL in `.mcp.json` (point at a hosted gald3r_valhalla) or fall back to the file-first paths that every gald3r skill ships with. |
| File-first vault / `g-skl-memory` / `g-skl-vault` | ✅ Full | All vault features have explicit file-first fallbacks — semantic search degrades to local grep, vault writes go straight to disk. No Docker required. |
| `gald3r_install` (server-side install) | ⚠️ Degraded | Requires reaching the install MCP. Locally on the USB drive, prefer `node bin/install.js` (zero-deps) or the `.gald3r_sys/_install_helper.ps1` path. |

### Limitations vs. full Claude Code

- No native Anthropic billing — the user supplies API keys per provider, OR uses the bundled offline path (Ollama).
- Hook compatibility is OpenClaw-engine-version dependent. Always-apply rules and skills are the safe bet; bet less on hooks for critical safety gates.
- Performance depends on the chosen provider and the USB drive's read/write speed. SSD-class USB is strongly recommended for non-trivial sessions.
- Zero host traces after unplug is a feature, but it also means no per-host config or cached state — every machine starts cold from the bundle.

### Cross-references

- T1082 — Portable mode architecture spec / launcher (parallel native-gald3r portable initiative).
- T1083 — gald3r_agent portable executable (zero-install). The OpenClaude path-resolution lessons from this section feed into T1083's path-resolution work.
- T1085 — Portable path resolution audit (shares the same problem space).

---

## Zero-Cost Provider Options

### Nvidia NIM Free Tier

[Nvidia NIM](https://build.nvidia.com) offers a **1000 free API credits/month** with no credit card required — the best free option for gald3r users who want real cloud inference beyond Ollama.

| Detail | Value |
|--------|-------|
| Signup | https://build.nvidia.com |
| Free credits | 1000/month (no CC required) |
| Best for | reviewer, qa_engineer, task_manager roles |
| Not recommended for | primary orchestrator on heavy workloads |
| OpenRouter access | Use `provider: openrouter, model: nvidia/...` |

**Compatible models for gald3r roles**:
- `nimitron` — good for code review, structured output
- `glm4` — strong reasoning, suited for task management and QA

**Provider fallback config** (reference for AGENT_CONFIG.md `provider_fallback_chain`):
```yaml
reviewer:
  - provider: nvidia-nim
    model: nimitron
    tier: free
  - provider: ollama
    model: qwen2.5
    tier: offline
```

> Credit note: 1000 credits/month is sufficient for ~200-400 reviewer calls. Budget-conscious teams should reserve NIM for the reviewer/QA roles and use Ollama for task_manager.
