---
name: g-skl-platform-copilot
description: Authoritative reference for GitHub Copilot customization in gald3r projects. Covers the .github/ vs .copilot/ split, all supported primitives, Phase 1 capabilities, hooks JSON format, agent authoring, and install verification. Reference implementation for g-skl-platform-* family.
crawl_max_age_days: 7
vault_doc_path: research/platforms/github_copilot/
vault_docs_url: https://docs.github.com/en/copilot
---

# g-skl-platform-copilot

Activate for: setting up Copilot in a gald3r project, authoring `.github/agents/`, configuring hooks, understanding the `.github/` vs `.copilot/` split, verifying Copilot parity, or answering questions about what Copilot supports in gald3r Phase 1.

---

## Crawl Freshness Gate

Before using this skill's technical content, check vault doc freshness:

```
1. Read {vault_location}/.crawl_schedule.json
2. Find entry for: https://docs.github.com/en/copilot
3. If entry missing OR (today - last_crawl) > crawl_max_age_days (7):
   → TRIGGER: g-skl-recon-docs with URL https://docs.github.com/en/copilot/reference/customization-cheat-sheet
   → WAIT for crawl to complete
   → READ new vault notes at research/platforms/github_copilot/
   → UPDATE sections: "Platform Overview", "Supported Primitives", "Common Pitfalls" below
4. Else: proceed with current content (vault is fresh)
```

**Self-Update Procedure**: After a fresh crawl, update these three sections in this SKILL.md to reflect any changes discovered. Use `StrReplace` on the relevant section headers. Preserve the rest of the file.

---

## 1. Platform Overview

**GitHub Copilot** is GitHub's AI coding assistant, available in:
- **VS Code** — full feature support (chat, inline completions, agent mode)
- **Visual Studio** — partial (no agents, no prompt files)
- **JetBrains IDEs** — preview support
- **GitHub.com** — cloud agent (PR review, issue fixing, code search)
- **Copilot CLI** — terminal agent; `gh copilot` or standalone `copilot` binary

**Models**: Claude Sonnet/Opus (Anthropic), GPT-4o/o3 (OpenAI), Gemini 1.5 Pro (Google) — user-selectable per session.

**gald3r target tier**: Phase 1 compatible. Skills auto-discovered. Agents, hooks, prompts require `.github/` setup (Task 149). Full slash-command support is Phase 2.

---

## 2. Folder Layout

GitHub Copilot customization is split across **two directories**:

```
.github/                          ← Copilot's native customization home
├── copilot-instructions.md       ← Always-apply rules (repo-wide, auto-loaded)
├── instructions/                 ← Path-scoped rules (Copilot-only feature)
│   └── *.instructions.md         ← frontmatter: applyTo: "glob/pattern"
├── agents/                       ← Custom agent definitions
│   └── g-agnt-task-manager.md    ← Same format as .claude/agents/*.md
├── hooks/                        ← Lifecycle hooks (JSON format, NOT PS1 directly)
│   └── gald3r-hooks.json          ← version:1, hooks:{sessionStart:[...], ...}
├── prompts/                      ← Reusable prompt templates (VS Code only)
│   └── g-task-add.prompt.md      ← Same content as .cursor/commands/g-task-add.md
└── skills/                       ← (OPTIONAL — usually not needed, see Pitfall #2)
    └── my-skill/SKILL.md

.copilot/                         ← gald3r convention folder (NOT a Copilot native path)
├── README.md                     ← Platform orientation for gald3r users
└── commands/                     ← All g-* commands as reference markdown (CLI docs)
    └── g-*.md                    ← 93 command files (same as .cursor/commands/)
```

**Key insight**: `.copilot/` is a gald3r invention for documentation purposes. Copilot itself does not read it. Everything Copilot actually uses lives in `.github/`.

---

## 3. Supported Primitives

| Primitive | gald3r Name | Copilot Location | Format | Auto-loaded? | Support Surface |
|---|---|---|---|---|---|
| Always-apply rules | rules | `.github/copilot-instructions.md` | Markdown | ✅ Always | VS Code, CLI, GitHub.com |
| Path-scoped rules | (no gald3r equiv) | `.github/instructions/*.instructions.md` | MD + frontmatter `applyTo:` | ✅ When path matches | VS Code, GitHub.com |
| Agent definitions | agents | `.github/agents/*.md` | Markdown | Manual select | VS Code, CLI, GitHub.com |
| Skills | skills | `.claude/skills/<name>/SKILL.md` | MD + frontmatter | ✅ When relevant | VS Code, CLI, GitHub.com |
| Lifecycle hooks | hooks | `.github/hooks/*.json` | JSON (not PS1 directly) | ✅ At lifecycle events | CLI, GitHub.com (Preview in VS Code) |
| Prompt templates | commands | `.github/prompts/*.prompt.md` | Markdown | Manual (picker) | VS Code only |
| MCP servers | MCP | `mcp.json` or `/mcp add` | JSON | ✅ Auto-connect | VS Code, CLI, GitHub.com |
| gald3r commands (ref) | commands | `.copilot/commands/*.md` | Markdown | ❌ gald3r convention only | Not natively read |

### Phase 1 vs Phase 2 Capability Table

| Capability | Phase 1 (today) | Phase 2 (future — awaits gald3r_valhalla MCP URL) |
|---|---|---|
| Always-apply rules | ✅ | — |
| Skills (auto-discovered) | ✅ `.claude/skills/` | — |
| Agents | ✅ `.github/agents/` | — |
| Hooks (lifecycle) | ✅ `.github/hooks/*.json` | — |
| Prompt files (VS Code) | ✅ `.github/prompts/` | — |
| MCP tools | ✅ `mcp.json` | gald3r_valhalla URL needed for full set |
| Slash commands (CLI) | ⚠️ Reference docs only | Full `/g-*` command support |
| Path-scoped rules | ✅ `.github/instructions/` | — |

---

## 4. gald3r Parity Tier

| Content | Slim | Full | Adv |
|---|---|---|---|
| `.github/copilot-instructions.md` | ✅ | ✅ | ✅ |
| `.copilot/commands/` (93 files) | ✅ | ✅ | ✅ |
| `.copilot/README.md` | ✅ | ✅ | ✅ |
| `.github/agents/` | — | ✅ | ✅ |
| `.github/hooks/gald3r-hooks.json` | — | ✅ | ✅ |
| `.github/prompts/` | — | ✅ | ✅ |
| `.github/instructions/` | — | — | ✅ (optional) |

The `generate_copilot_instructions.ps1` script regenerates `copilot-instructions.md` from always-apply rules.

---

## 5. Vault Doc Location

Platform docs are stored in the vault at:
```
{vault_location}/research/platforms/github_copilot/
```

Key files to look for after a crawl:
- `github_copilot_customization_cheat_sheet.md` — full feature/surface matrix
- `github_copilot_custom_instructions.md` — instructions format details
- `github_copilot_agents.md` — agent authoring reference
- `github_copilot_hooks.md` — hooks configuration reference
- `github_copilot_skills.md` — skills specification

Crawl entry point: `https://docs.github.com/en/copilot/reference/customization-cheat-sheet`

---

## 6. Crawl Freshness Gate (Detail)

The `.crawl_schedule.json` entry for this platform follows this structure:
```json
{
  "https://docs.github.com/en/copilot": {
    "last_crawl": "2026-04-19",
    "vault_path": "research/platforms/github_copilot/",
    "max_age_days": 7,
    "status": "ok"
  }
}
```

If the entry is missing or stale:
1. Invoke `g-skl-recon-docs` with the URL above
2. After completion, read `research/platforms/github_copilot/*.md` for any changed primitives
3. Update sections 1, 3, and 9 of this SKILL.md with new information
4. Update `.crawl_schedule.json` `last_crawl` to today

---

## 7. Self-Update Procedure

After each fresh crawl of Copilot docs:

1. Read all `.md` files in `{vault_location}/research/platforms/github_copilot/`
2. Compare against current content in sections 1, 3, and 9 of this SKILL.md
3. For any changed capabilities, file locations, or new features:
   - Use `StrReplace` to update the relevant table rows or paragraphs
   - Do NOT rewrite unchanged sections
4. Add a comment at the top of the diff in the Status History of task 148 (if still open) or create a new task if a breaking change is found
5. If Copilot has added support for a new primitive (e.g. full slash commands in CLI), update Task 149 accordingly

---

## 8. Key URLs

| Purpose | URL |
|---|---|
| Customization cheat sheet (primary) | https://docs.github.com/copilot/reference/customization-cheat-sheet |
| Custom instructions | https://docs.github.com/copilot/customizing-copilot/adding-custom-instructions-for-github-copilot |
| Custom agents | https://docs.github.com/en/copilot/concepts/agents/cloud-agent/about-custom-agents |
| Agent skills spec | https://docs.github.com/en/copilot/concepts/agents/about-agent-skills |
| Hooks reference | https://docs.github.com/en/copilot/concepts/agents/cloud-agent/about-hooks |
| CLI agents | https://docs.github.com/copilot/how-tos/copilot-cli/use-copilot-cli-agents/invoke-custom-agents |
| Feature matrix | https://docs.github.com/en/copilot/reference/copilot-feature-matrix |

---

## 9. Common Pitfalls

1. **Hooks use JSON, not PS1 directly** — `.github/hooks/*.json` must wrap scripts via `"powershell": "./path/script.ps1"` or `"bash": "./path/script.sh"`. You cannot put a raw PS1 path. See Hook Format section below.

2. **Skills are auto-discovered from `.claude/skills/`** — Copilot natively reads `.claude/skills/`, `.agents/skills/`, and `.github/skills/`. You do NOT need a `.github/skills/` copy. All gald3r skills already work for Copilot users with zero extra files.

3. **`.copilot/commands/` is NOT a Copilot-native path** — It's a gald3r convention for storing command reference docs. Copilot CLI does not auto-discover or execute files in `.copilot/`. These files are for human and agent reference only.

4. **`copilot-instructions.md` context budget** — The gald3r source repo has 877 lines in `.github/copilot-instructions.md`. In consumer projects installed via `gald3r_install`, this is auto-generated and will be shorter. Extremely large instruction files may be truncated by the model context window. Keep under 500 lines for consumer projects.

5. **Path-specific instructions are Copilot-only** — `.github/instructions/*.instructions.md` with `applyTo: "glob"` frontmatter is a unique Copilot feature. No equivalent exists in Cursor, Claude, or other platforms. Do not add this to the parity sync targets.

6. **Hooks only fire during agent sessions** — `.github/hooks/*.json` hooks are NOT CI scripts, git hooks, or GitHub Actions. They only execute when a Copilot agent session is actively running (CLI or GitHub.com cloud agent). Normal git operations, commits, and pushes are completely unaffected.

7. **Feature support varies by surface** — VS Code has the most features. Copilot CLI supports agents, skills, hooks, and MCP but NOT prompt files. GitHub.com supports cloud agent only. JetBrains/Xcode are in preview. Always check the feature matrix before documenting a capability as universally available.

8. **Agent file naming** — `.github/agents/` files use `.md` extension (not `.agent.md`). Some older docs reference `.agent.md` — use `.md`.

---

## Hook Format Reference

Copilot hooks use a specific JSON schema. Example `gald3r-hooks.json`:

```json
{
  "version": 1,
  "hooks": {
    "sessionStart": [
      {
        "type": "command",
        "bash": ".claude/hooks/g-hk-session-start.sh",
        "powershell": ".claude/hooks/g-hk-session-start.ps1",
        "cwd": ".",
        "timeoutSec": 30
      }
    ],
    "agentStop": [
      {
        "type": "command",
        "bash": ".claude/hooks/g-hk-agent-complete.sh",
        "powershell": ".claude/hooks/g-hk-agent-complete.ps1",
        "timeoutSec": 30
      }
    ],
    "preToolUse": [
      {
        "type": "command",
        "bash": ".claude/hooks/g-hk-validate-shell.sh",
        "powershell": ".claude/hooks/g-hk-validate-shell.ps1",
        "timeoutSec": 15
      }
    ]
  }
}
```

**Hook type mapping** (gald3r hooks.json → Copilot hooks JSON):

| gald3r hooks.json event | Copilot hook type | Notes |
|---|---|---|
| `sessionStart` | `sessionStart` | Direct mapping |
| `stop` | `agentStop` | Renamed in Copilot |
| `beforeShellExecution` | `preToolUse` | Broader in Copilot (all tools, not just shell) |
| n/a | `sessionEnd` | New in Copilot — cleanup/reporting |
| n/a | `postToolUse` | New in Copilot — audit logging |
| n/a | `userPromptSubmitted` | New in Copilot — prompt logging |
| n/a | `subagentStop` | New in Copilot — subagent lifecycle |
| n/a | `errorOccurred` | New in Copilot — error handling |

**Note**: Copilot hooks require `"type": "command"` in each hook object. The gald3r `hooks.json` (Claude Code format) does not require this field. They are NOT the same format.

---

## 10. Install Verification Checklist

After running `gald3r_install` or setting up Copilot support manually, verify:

```
✅ .github/copilot-instructions.md exists and is non-empty
✅ .github/copilot-instructions.md was generated from always-apply rules (run generate_copilot_instructions.ps1 if missing)
✅ .copilot/commands/ has 93+ command files (run platform_parity_sync.ps1 -Sync if below count)
✅ .copilot/README.md exists

For full tier (Task 149 completed):
✅ .github/agents/ exists and is populated
✅ .github/hooks/gald3r-hooks.json exists and is valid JSON (version: 1)
✅ .github/prompts/ exists with .prompt.md files
✅ Skills work: open VS Code → Copilot Chat → ask about a gald3r skill → Copilot should find it from .claude/skills/

MCP check (optional):
✅ mcp.json exists in project root (or ~/.copilot/mcp-config.json for CLI)
✅ Copilot CLI: run `copilot /mcp` to list configured servers
```

**Common install failures**:
- `copilot-instructions.md` missing → run `.\scripts\generate_copilot_instructions.ps1`
- Commands count low → run `.\scripts\platform_parity_sync.ps1 -Sync`
- Skills not loading in VS Code → ensure `.claude/skills/` exists (not just `.cursor/skills/`)
- Hooks not firing → verify `.github/hooks/*.json` is valid JSON and `version: 1` is set
