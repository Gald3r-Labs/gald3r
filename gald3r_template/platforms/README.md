# gald3r Platform-Conditional Files

This folder contains files that are only installed when specific platforms are selected
during setup_gald3r_project.ps1 installation.

| File / Folder     | Installed when platform selected |
|-------------------|----------------------------------|
| AGENTS.md       | Any (universal — read by Codex, Gemini, Claude, Cursor, Copilot, OpenCode, OpenHands) |
| CLAUDE.md       | claude, cursor, kiro, windsurf, roo, cline, augment |
| GEMINI.md       | agent (Gemini CLI)               |
| opencode.json   | opencode (OpenCode / sst.dev)    |
| .github/        | copilot (GitHub Copilot)         |

Files at the gald3r_template/ root (GUARDRAILS.md, WORKFLOW.md, .gitignore, scripts/, etc.)
are installed unconditionally for every project.