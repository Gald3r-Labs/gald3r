---
name: g-skl-cli-copilot
description: GitHub Copilot CLI (gh copilot command) — natural language to shell/git/gh commands, agent mode, chat sessions, workspace instructions, and multi-agent coordination via .github/copilot-instructions.md.
---

# g-skl-cli-copilot — GitHub Copilot CLI

> **Note**: This skill covers **GitHub Copilot CLI** (`gh copilot` subcommand from the `gh` CLI) and
> Copilot-in-IDE workspace instructions (`.github/copilot-instructions.md`).
> This is gald3r's **6th IDE platform** at the **Phase 1 "compatible"** level.
> Phase 2 (`.github/agents/*.agent.md` generation) is deferred — see notes below.

Reference docs at: `{vault_location}/research/platforms/copilot/` once populated via `@g-ingest-docs`.

## gald3r + Copilot: What Works Today

| Feature | Status | Notes |
|---------|--------|-------|
| Always-apply rules | ✅ | Via `.github/copilot-instructions.md` — run `generate_copilot_instructions.ps1` |
| Commands (`g-*`) | ✅ | `.copilot/commands/` mirrors other IDE targets |
| Skills | ❌ | Phase 2 — awaits gald3r_valhalla MCP URL |
| Agents | ❌ | Phase 2 — awaits public MCP endpoint |
| Hooks | ❌ | Not supported by Copilot CLI architecture |

## Installation

```bash
# GitHub CLI (required)
# Windows: winget install GitHub.cli  or  choco install gh
# macOS: brew install gh
# Linux: see https://cli.github.com/manual/installation

# Authenticate
gh auth login

# Install Copilot extension
gh extension install github/gh-copilot

# Verify
gh copilot --version
```

## Authentication

Copilot CLI authenticates via the GitHub CLI session (`gh auth login`).
Requires an active GitHub Copilot subscription (Individual, Business, or Enterprise).

```bash
gh auth login                         # interactive browser flow
gh auth login --with-token <<< $PAT  # headless with Personal Access Token
gh auth status                        # verify
```

## Natural Language to Shell / git / gh

```bash
# Explain what a command does
gh copilot explain "git rebase -i HEAD~5"
gh copilot explain "find . -name '*.ts' -mtime -1"

# Suggest a command from description
gh copilot suggest "undo the last commit but keep changes staged"
gh copilot suggest --target shell "find all files modified in the last 24h"
gh copilot suggest --target git "cherry pick commits from another branch"
gh copilot suggest --target gh "create a PR from this branch to main"
```

`--target` values: `shell` | `git` | `gh` (default: auto-detect)

## Agent Mode (Copilot in IDE)

In Cursor, VS Code, and JetBrains IDEs with Copilot enabled, Copilot reads:

1. `.github/copilot-instructions.md` — repository-wide instructions (gald3r always-apply rules live here)
2. Open file context in editor
3. Inline chat `#codebase` — semantic search across repo

```
# Invoke in VS Code Copilot Chat
@workspace What tasks are ready to work on?
@workspace Summarize the current sprint from PLAN.md
@workspace Apply the gald3r code review checklist to this file
```

## Workspace Instructions (copilot-instructions.md)

gald3r's always-apply rules are automatically compiled into `.github/copilot-instructions.md` by:

```powershell
.\scripts\generate_copilot_instructions.ps1
```

Regenerate after any change to `.cursor/rules/g-rl-*.mdc` files.

The generator:
- Reads all `g-rl-*.mdc` files in numeric order
- Strips Cursor-specific YAML frontmatter
- Wraps with a Copilot-friendly header banner
- Writes to `.github/copilot-instructions.md` and `gald3r_template_full/.github/copilot-instructions.md`
- Is idempotent (safe to rerun)

## Headless / CI Usage

```bash
# Suggest a command and execute it non-interactively (pipe 1 to confirm)
echo "1" | gh copilot suggest --target git "stage all tracked changes and commit"

# In CI — use for git/gh automation suggestions only
# Full-auto code generation requires IDE integration (no headless coding mode in Phase 1)
```

## Multi-Agent Coordination

Copilot Phase 1 does not have a headless coding agent like `cursor agent` or `codex`. For multi-agent workflows involving Copilot:
- Use `.github/copilot-instructions.md` to carry gald3r rules to Copilot IDE sessions
- Coordinate via `.gald3r/linking/INBOX.md` PCAC messages as usual
- Copilot users work in their IDE; task status is updated in `.gald3r/tasks/` files manually

Phase 2 will add `.github/agents/*.agent.md` to enable agent-mode invocation once gald3r_valhalla provides a public MCP server URL.

## Known Limitations (Phase 1)

- **No session continuation** — each `gh copilot suggest` is stateless
- **No MCP tool integration** — Phase 2 dependency
- **No hooks** — `g-hk-session-start.ps1` and inbox-check hooks are Cursor/Claude-only
- **No skill invocation** — skills require `@workspace` or explicit IDE paste; no `@g-*` command shorthand in Copilot Chat

## Dangerous Patterns to Avoid

| Pattern | Risk |
|---------|------|
| `echo "1" \| gh copilot suggest --target shell` piped to `bash` | Auto-executes shell commands without review |
| Copying copilot-instructions.md with secrets | GitHub commits instructions to the repo — never include credentials |
| Running `generate_copilot_instructions.ps1` on a stale rules directory | Output file will not reflect latest rules |

## Vault Reference

Once `@g-ingest-docs` is run for `copilot`, full docs will be at:
`{vault_location}/research/platforms/copilot/`
