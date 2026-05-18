---
name: g-skl-platform-claude
description: Authoritative reference for Claude Code customization in gald3r projects. Covers .claude/ folder layout, CLAUDE.md, agents, skills, commands, hooks (hooks.json format), MCP, and install verification.
crawl_max_age_days: 7
vault_doc_path: research/platforms/claude-code/
vault_docs_url: https://docs.anthropic.com/en/docs/claude-code/overview
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
    "stop": [{ "command": "powershell.exe -File .claude/hooks/g-hk-agent-complete.ps1" }],
    "beforeShellExecution": [{ "command": "powershell.exe -File .claude/hooks/g-hk-validate-shell.ps1" }]
  }
}
```

Note: Claude's `hooks.json` uses `"command"` (a full shell string), NOT Copilot's `"type"/"bash"/"powershell"` object format.

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
