---
name: g-skl-platform-opencode
description: Authoritative reference for OpenCode (sst.dev) customization in gald3r projects. Covers .opencode/ folder layout, opencode.json config, skills auto-discovery from .claude/skills/, commands, and install verification.
crawl_max_age_days: 7
vault_doc_path: research/platforms/opencode/
vault_docs_url: https://opencode.ai/docs
---

# g-skl-platform-opencode

Activate for: setting up OpenCode in a gald3r project, authoring `.opencode/` configs, understanding opencode.json, verifying OpenCode parity, or answering questions about OpenCode's capabilities.

---

## Crawl Freshness Gate

```
1. Read {vault_location}/.crawl_schedule.json
2. Find entry for: https://opencode.ai/docs
3. If entry missing OR (today - last_crawl) > 7 days:
   → TRIGGER g-skl-recon-docs with URL https://opencode.ai/docs
   → READ new vault notes at research/platforms/opencode/
   → UPDATE sections: "Platform Overview", "Supported Primitives", "Common Pitfalls"
4. Else: proceed with current content
```

---

## 1. Platform Overview

**OpenCode** (`opencode` command) is an open-source AI coding agent from [sst.dev](https://sst.dev). It runs as a TUI (terminal UI) with multi-provider support.

- **Multi-provider**: Claude, GPT-4o, Gemini, DeepSeek, local Ollama (configurable in `opencode.json`)
- **TUI interface**: Rich terminal UI with file tree, diff views, conversation history
- **Config file**: `opencode.json` at project root — controls model, provider, instructions
- **Skills auto-discovery**: Reads `.claude/skills/` and `.agents/skills/` natively
- **Rules via glob**: `opencode.json` `instructions` field accepts glob patterns pointing to `.cursor/rules/*.mdc`
- **No native hooks** — Phase 1 limitation; hooks via external scripts

**gald3r target**: Full primitive support via `.opencode/` + `opencode.json` conventions. Skills come from `.claude/skills/` automatically.

---

## 2. Folder Layout

```
.opencode/                    ← OpenCode config
├── agents/                   ← Agent definitions
│   └── g-agnt-*.md
└── commands/                 ← /g-* command reference
    └── g-*.md

opencode.json                 ← Root config (NOT in .opencode/)
```

**Skills**: OpenCode reads `.claude/skills/` natively. No `.opencode/skills/` needed.

**Rules**: Set via `opencode.json` `instructions` glob:
```json
{
  "instructions": [".cursor/rules/*.mdc"]
}
```

This means `.cursor/rules/` serves OpenCode directly — no rules copy to `.opencode/`.

---

## 3. Supported Primitives

| Primitive | Location | Format | Auto-loaded? |
|---|---|---|---|
| Always-apply rules | `.cursor/rules/*.mdc` (via opencode.json glob) | Markdown | ✅ Via opencode.json |
| Skills | `.claude/skills/<name>/SKILL.md` | Markdown | ✅ Auto-discovered |
| Agents | `.opencode/agents/g-agnt-*.md` | Markdown | Manual select |
| Commands | `.opencode/commands/g-*.md` | Markdown | Manual reference |
| MCP servers | `opencode.json` → `mcp` block | JSON | ✅ Auto-connect |
| Hooks | Not natively supported | n/a | n/a |

### opencode.json Structure

```json
{
  "model": "claude-sonnet-4-5",
  "provider": "anthropic",
  "instructions": [".cursor/rules/*.mdc"],
  "mcp": {
    "gald3r": {
      "type": "sse",
      "url": "http://localhost:8092/mcp"
    }
  }
}
```

---

## 4. gald3r Parity Tier

| Content | Slim | Full | Adv |
|---|---|---|---|
| agents/ | ✅ | ✅ | ✅ |
| commands/ | ✅ | ✅ | ✅ |
| opencode.json | ✅ | ✅ | ✅ |
| Skills (via .claude/skills/) | ✅ | ✅ | ✅ |
| Rules (via opencode.json glob) | ✅ | ✅ | ✅ |

---

## 5. Vault Doc Location

```
{vault_location}/research/platforms/opencode/
```

---

## 6–7. Crawl Freshness Gate & Self-Update

See gate template in header. Update sections 1, 3, 9 after fresh crawl.

---

## 8. Key URLs

| Purpose | URL |
|---|---|
| OpenCode website | https://opencode.ai |
| OpenCode docs | https://opencode.ai/docs |
| OpenCode GitHub | https://github.com/sst/opencode |
| Configuration reference | https://opencode.ai/docs/config |

---

## 9. Common Pitfalls

1. **`opencode.json` is at project root** — Not inside `.opencode/`. A common mistake is placing it in `.opencode/opencode.json` — it won't be found there.
2. **Rules via glob, not copy** — OpenCode reads `.cursor/rules/*.mdc` directly via the `instructions` glob. Do NOT copy rules into `.opencode/rules/` — there is no such directory in the gald3r convention.
3. **Skills from `.claude/skills/`** — OpenCode auto-discovers `.claude/skills/`. The `.opencode/skills/` folder does not exist in gald3r; skills propagate through `.claude/`.
4. **`.cursor/skills/` is NOT auto-discovered** — OpenCode does NOT read `.cursor/skills/`. Always ensure skills are in `.claude/skills/`.
5. **No hooks** — OpenCode has no hooks.json equivalent in Phase 1. Session automation must be handled via rules or external tooling.
6. **Model selection**: `opencode.json` `model` field accepts provider-specific model IDs. Use `claude-sonnet-4-5` not `claude` (ambiguous).

---

## 10. Install Verification Checklist

```
✅ opencode.json exists at project root
✅ opencode.json has "instructions": [".cursor/rules/*.mdc"]
✅ .opencode/agents/ has g-agnt-*.md files
✅ .opencode/commands/ has g-*.md command files
✅ .claude/skills/ has gald3r core skills (OpenCode reads from here)
✅ opencode --version runs without error
✅ Provider API key set in environment (ANTHROPIC_API_KEY, OPENAI_API_KEY, etc.)
```
