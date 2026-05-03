---
name: g-skl-platform-codex
description: Authoritative reference for OpenAI Codex CLI customization in gald3r projects. Covers .codex/ folder layout, approval modes, commands, MCP, and install verification.
crawl_max_age_days: 7
vault_doc_path: research/platforms/openai/
vault_docs_url: https://github.com/openai/codex
---

# g-skl-platform-codex

Activate for: setting up Codex CLI in a gald3r project, authoring `.codex/` configs, understanding approval modes, verifying Codex parity, or answering questions about Codex CLI's capabilities.

---

## Crawl Freshness Gate

```
1. Read {vault_location}/.crawl_schedule.json
2. Find entry for: https://github.com/openai/codex
3. If entry missing OR (today - last_crawl) > 7 days:
   → TRIGGER g-skl-recon-docs with URL https://github.com/openai/codex
   → READ new vault notes at research/platforms/openai/
   → UPDATE sections: "Platform Overview", "Supported Primitives", "Common Pitfalls"
4. Else: proceed with current content
```

---

## 1. Platform Overview

**Codex CLI** (`codex` command) is OpenAI's open-source terminal-based coding agent.

- **GPT-4o / o3** models (configurable)
- **Approval modes**: `suggest` (read-only), `auto-edit` (file edits only), `full-auto` (full execution)
- **Sandbox**: Network/filesystem isolation in full-auto mode
- **Session continuation**: `codex --continue`
- **Provider support**: OpenAI, Azure OpenAI, Gemini, Anthropic, local Ollama
- **MCP**: via config file `mcpServers` block

**gald3r target**: Minimal primitive support — commands and skills only. No native rules directory. No hooks. Config-heavy platform.

---

## 2. Folder Layout

```
.codex/                       ← Codex CLI config
├── skills/                   ← Agent skills (discovered from .claude/skills/ primarily)
│   └── g-skl-*/SKILL.md      ← Codex reads .claude/skills/ natively too
└── commands/                 ← /g-* command reference
    └── g-*.md
```

**No rules directory** — Codex uses `AGENTS.md` at project root for always-apply instructions. It does not have a rules/ subfolder.

**Skills**: Codex reads `.claude/skills/` natively (same as OpenCode and Copilot). The `.codex/skills/` copy is kept for explicit awareness only.

---

## 3. Supported Primitives

| Primitive | Location | Format | Auto-loaded? |
|---|---|---|---|
| Always-apply rules | `AGENTS.md` at project root | Markdown | ✅ Every session |
| Skills | `.codex/skills/` OR `.claude/skills/` | Markdown | ✅ When relevant |
| Agents | Not natively supported in Phase 1 | n/a | n/a |
| Commands | `.codex/commands/g-*.md` | Markdown | Manual reference |
| MCP servers | `codex.config.json` → `mcpServers` | JSON | ✅ Auto-connect |
| Hooks | Not supported | n/a | n/a |

---

## 4. gald3r Parity Tier

| Content | Slim | Full | Adv |
|---|---|---|---|
| skills/ | ✅ | ✅ | ✅ |
| commands/ | ✅ | ✅ | ✅ |
| No rules dir | n/a | n/a | n/a |

---

## 5. Vault Doc Location

```
{vault_location}/research/platforms/openai/
```

---

## 6–7. Crawl Freshness Gate & Self-Update

See gate template in header. Update sections 1, 3, 9 after fresh crawl.

---

## 8. Key URLs

| Purpose | URL |
|---|---|
| Codex CLI repo | https://github.com/openai/codex |
| Codex CLI docs | https://platform.openai.com/docs/codex |
| Approval modes | https://github.com/openai/codex#approval-policy |

---

## 9. Common Pitfalls

1. **No rules directory** — Codex does not have a `.codex/rules/` folder. Always-apply rules go in `AGENTS.md` at project root. The parity sync skips rules for `.codex/` (RulesExt is null).
2. **Skills come from `.claude/skills/`** — Codex auto-discovers `.claude/skills/`. The `.codex/skills/` folder is kept for gald3r parity tracking but Codex reads `.claude/skills/` directly.
3. **Approval mode for gald3r hooks** — gald3r's PS1 hooks require shell execution. In `suggest` mode, Codex won't run them. Use `auto-edit` or `full-auto` for full gald3r integration.
4. **Multi-provider setup** — Codex can use Anthropic models. Set `ANTHROPIC_API_KEY` + `--provider anthropic` for Claude-based Codex sessions.
5. **`codex.config.json` location** — Config file is at `~/.codex/config.json` (user-level) or `.codex/codex.config.json` (project-level). MCP servers go in the `mcpServers` block.

---

## 10. Install Verification Checklist

```
✅ .codex/commands/ has g-*.md command files
✅ .codex/skills/ has gald3r core skills
✅ AGENTS.md exists at project root (always-apply rules)
✅ codex --version runs without error
✅ OPENAI_API_KEY is set (or other provider key)
✅ Approval mode: codex --approval-mode auto-edit (for gald3r file operations)
```
