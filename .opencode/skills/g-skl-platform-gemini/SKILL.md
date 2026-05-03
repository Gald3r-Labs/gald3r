---
name: g-skl-platform-gemini
description: Authoritative reference for Gemini CLI (Google DeepMind) customization in gald3r projects. Covers .agent/ folder layout, GEMINI.md, rules, skills, commands, and install verification.
crawl_max_age_days: 7
vault_doc_path: research/platforms/gemini/
vault_docs_url: https://github.com/google-gemini/gemini-cli
---

# g-skl-platform-gemini

Activate for: setting up Gemini CLI in a gald3r project, authoring `.agent/` configs, verifying Gemini parity, or answering questions about Gemini CLI's capabilities.

---

## Crawl Freshness Gate

```
1. Read {vault_location}/.crawl_schedule.json
2. Find entry for: https://github.com/google-gemini/gemini-cli
3. If entry missing OR (today - last_crawl) > 7 days:
   → TRIGGER g-skl-recon-docs with URL https://github.com/google-gemini/gemini-cli
   → READ new vault notes at research/platforms/gemini/
   → UPDATE sections: "Platform Overview", "Supported Primitives", "Common Pitfalls"
4. Else: proceed with current content
```

---

## 1. Platform Overview

**Gemini CLI** (`gemini` command) is Google DeepMind's open-source AI coding agent. It runs in the terminal with deep codebase awareness.

- **Gemini 2.5 Pro/Flash** models (model-swappable via config)
- **Free tier** available for personal use (Gemini API key)
- **Checkpointing**: `--checkpoint` flag for resumable sessions
- **Extensions**: Tool bundles extending Gemini's capabilities
- **Memory**: Project and global memory via GEMINI.md + memory files
- **MCP**: via `settings.json` `mcpServers` block

**gald3r target**: Full parity with Cursor. Uses `.agent/` folder (also called `.agents/` in some docs). gald3r uses `.agent/` as the canonical name.

---

## 2. Folder Layout

```
.agent/                       ← Gemini CLI config (gald3r canonical name)
├── GEMINI.md                 ← Project-level always-apply instructions
├── rules/                    ← Always-apply rules (.md format)
│   └── g-rl-*.md
├── skills/                   ← Agent skills (auto-discovered)
│   └── g-skl-*/SKILL.md
├── agents/                   ← Agent definitions
│   └── g-agnt-*.md
└── commands/                 ← /g-* commands
    └── g-*.md
```

**Note**: Gemini reads both `.agent/` and `.agents/` — gald3r uses `.agent/` for consistency.

---

## 3. Supported Primitives

| Primitive | Location | Format | Auto-loaded? |
|---|---|---|---|
| Always-apply rules | `.agent/rules/g-rl-*.md` + `GEMINI.md` | Markdown | ✅ Every session |
| Skills | `.agent/skills/<name>/SKILL.md` | Markdown | ✅ When relevant |
| Agents | `.agent/agents/g-agnt-*.md` | Markdown | Manual select |
| Commands | `.agent/commands/g-*.md` | Markdown | Via `/command-name` |
| MCP servers | `settings.json` → `mcpServers` | JSON | ✅ Auto-connect |
| Hooks | Not natively supported — use rules + scripts | n/a | Manual |

---

## 4. gald3r Parity Tier

| Content | Slim | Full | Adv |
|---|---|---|---|
| rules/ (8 always-apply) | ✅ | ✅ | ✅ |
| skills/ | ✅ | ✅ | ✅ |
| agents/ | ✅ | ✅ | ✅ |
| commands/ | ✅ | ✅ | ✅ |
| GEMINI.md | ✅ | ✅ | ✅ |

---

## 5. Vault Doc Location

```
{vault_location}/research/platforms/gemini/
```

---

## 6–7. Crawl Freshness Gate & Self-Update

See gate template in header. Update sections 1, 3, 9 after fresh crawl.

---

## 8. Key URLs

| Purpose | URL |
|---|---|
| Gemini CLI repo | https://github.com/google-gemini/gemini-cli |
| Gemini CLI docs | https://gemini.google.com/cli |
| Extensions guide | https://github.com/google-gemini/gemini-cli/blob/main/docs/extensions.md |

---

## 9. Common Pitfalls

1. **`.agent/` vs `.agents/`** — gald3r uses `.agent/` but Gemini reads both. Do not create both; `.agent/` is canonical.
2. **No native hooks** — Gemini has no hooks.json equivalent. Session automation must be done via rules/memory or external scripts.
3. **API key required** — `GEMINI_API_KEY` environment variable. Free tier has rate limits. Set in `.env` or system environment.
4. **Memory via GEMINI.md** — Gemini's "memory" feature appends to `GEMINI.md`. Be careful not to let gald3r rules be overwritten by Gemini's memory injections.
5. **Checkpointing** — `gemini --checkpoint` saves session state. Useful for long tasks; restart from checkpoint with `--resume`.

---

## 10. Install Verification Checklist

```
✅ .agent/rules/ has g-rl-*.md files
✅ .agent/skills/ has gald3r core skills  
✅ .agent/agents/ has g-agnt-*.md files
✅ .agent/commands/ has g-*.md files
✅ GEMINI.md exists at project root
✅ gemini --version runs without error
✅ GEMINI_API_KEY is set in environment
```
