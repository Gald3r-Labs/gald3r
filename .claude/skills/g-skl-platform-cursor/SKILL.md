---
name: g-skl-platform-cursor
description: Authoritative reference for Cursor IDE customization in gald3r projects. Covers .cursor/ folder layout, all supported primitives (rules/skills/agents/commands/hooks/MCP), parity tiers, vault doc location, crawl freshness gate, and install verification.
crawl_max_age_days: 7
vault_doc_path: research/platforms/cursor/
vault_docs_url: https://docs.cursor.com
---

# g-skl-platform-cursor

Activate for: setting up Cursor in a gald3r project, authoring rules/skills/agents/commands/hooks, understanding .cursor/ structure, verifying Cursor parity, or answering questions about Cursor's capabilities.

---

## Crawl Freshness Gate

```
1. Read {vault_location}/.crawl_schedule.json
2. Find entry for: https://docs.cursor.com
3. If entry missing OR (today - last_crawl) > 7 days:
   → TRIGGER g-skl-recon-docs with URL https://docs.cursor.com
   → READ new vault notes at research/platforms/cursor/
   → UPDATE sections: "Platform Overview", "Supported Primitives", "Common Pitfalls"
4. Else: proceed with current content
```

**Self-Update Procedure**: After a fresh crawl, update sections 1, 3, and 9 of this SKILL.md using StrReplace on the changed content.

---

## 1. Platform Overview

**Cursor** is an AI-first IDE built on VS Code, with deep agent mode integration. It runs locally as a desktop application.

- **Agent mode**: Background agents that autonomously complete multi-step tasks
- **Inline completions**: Tab-to-accept AI suggestions
- **Chat**: Sidebar chat with @ references to files, symbols, docs, and skills
- **Rules**: Auto-applied context injected into every session
- **Skills**: On-demand specialist procedures (`.cursor/rules/` or SKILL.md files)
- **MCP**: MCP servers accessible via Cursor's settings or `.cursor/mcp.json`

**gald3r target tier**: Canonical source. All gald3r features originate in `.cursor/` and propagate to other platforms.

---

## 2. Folder Layout

```
.cursor/
├── rules/                    ← Always-apply rules (.mdc format, loaded every session)
│   └── g-rl-*.mdc            ← Numbered rules (00-always, 01-docs, 25-session-start, etc.)
├── skills/                   ← Agent skills (auto-discovered by Cursor)
│   └── g-skl-*/SKILL.md      ← Each skill in its own folder
├── agents/                   ← Specialist agent definitions (markdown)
│   └── g-agnt-*.md
├── commands/                 ← @g-* slash commands (referenced via @ in chat)
│   └── g-*.md
├── hooks/                    ← PowerShell automation hooks
│   ├── hooks.json            ← (NOTE: Cursor uses hooks.json in .cursor/hooks/ — NOT used; hooks run via rules or manual)
│   └── g-hk-*.ps1
└── mcp.json                  ← MCP server configuration (or in Cursor settings)
```

**Key**: `.mdc` extension is Cursor-specific for rules. Other platforms use `.md`.

---

## 3. Supported Primitives

| Primitive | Location | Format | Auto-loaded? |
|---|---|---|---|
| Always-apply rules | `.cursor/rules/g-rl-*.mdc` | Markdown + frontmatter | ✅ Every session |
| Skills | `.cursor/skills/<name>/SKILL.md` | Markdown + frontmatter | ✅ When relevant |
| Agents | `.cursor/agents/g-agnt-*.md` | Markdown | Manual select |
| Commands | `.cursor/commands/g-*.md` | Markdown | Via `@command-name` |
| MCP servers | `.cursor/mcp.json` or Cursor settings | JSON | ✅ Auto-connect |
| Hooks | No native hooks.json — PowerShell scripts run manually or via rules | PS1 | Manual |

---

## 4. gald3r Parity Tier

Cursor is the **canonical source** for gald3r. All content originates here.

| Content | Slim | Full | Adv |
|---|---|---|---|
| rules/ (8 always-apply) | ✅ | ✅ | ✅ |
| skills/ (core gald3r) | ✅ | ✅ | ✅ |
| agents/ | ✅ | ✅ | ✅ |
| commands/ | ✅ | ✅ | ✅ |
| hooks/ | ✅ | ✅ | ✅ |

Run `.\scripts\platform_parity_sync.ps1` to propagate changes to all 11 other targets.

---

## 5. Vault Doc Location

```
{vault_location}/research/platforms/cursor/
```

Crawl entry point: `https://docs.cursor.com`

---

## 6. Crawl Freshness Gate (Detail)

`.crawl_schedule.json` entry:
```json
{
  "https://docs.cursor.com": {
    "last_crawl": "YYYY-MM-DD",
    "vault_path": "research/platforms/cursor/",
    "max_age_days": 7
  }
}
```

---

## 7. Self-Update Procedure

After each fresh crawl: read `research/platforms/cursor/*.md`, update sections 1, 3, and 9 with any changed capabilities or file paths.

---

## 8. Key URLs

| Purpose | URL |
|---|---|
| Cursor docs (primary) | https://docs.cursor.com |
| Rules documentation | https://docs.cursor.com/context/rules |
| MCP documentation | https://docs.cursor.com/context/model-context-protocol |
| Agent mode | https://docs.cursor.com/agent |

---

## 9. Common Pitfalls

1. **Rules must use `.mdc` extension** — Cursor only auto-loads rules with `.mdc`. Other platforms use `.md`. The parity sync handles extension mapping automatically.
2. **Skills folder structure** — Each skill must be in its own subfolder: `.cursor/skills/my-skill/SKILL.md`. A loose `.md` file in `skills/` root is NOT picked up.
3. **`.cursor/` is the canonical source** — When editing gald3r framework files, always edit `.cursor/` first, then run `platform_parity_sync.ps1 -Sync` to propagate. Never edit gald3r_template_full files directly.
4. **MCP timeout** — Default Cursor MCP timeout is 60s. For long-running tools, set `mcp.server.timeout: 600000` in Cursor settings.json.
5. **Proprietary skills stay in `.cursor/` only** — Never propagate business-specific or proprietary skills to `gald3r_template_full/`. C-009 exemption applies.

---

## 10. Install Verification Checklist

```
✅ .cursor/rules/ has 8+ g-rl-*.mdc always-apply files
✅ .cursor/skills/ has gald3r core skills (g-skl-tasks, g-skl-bugs, g-skl-plan, etc.)
✅ .cursor/agents/ has gald3r agent files
✅ .cursor/commands/ has g-* command files
✅ .cursor/hooks/ has session-start and other PS1 hooks
✅ platform_parity_sync.ps1 reports 0 gaps
✅ Cursor > Settings > MCP shows configured servers (if using MCP)
```
