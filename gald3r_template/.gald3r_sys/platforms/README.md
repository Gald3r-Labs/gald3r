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

Deployable markdown (GUARDRAILS.md, WORKFLOW.md, GALD3R-MIGRATION.md, GALD3R-PROMPT.md) lives in
`.gald3r_sys/install/project_root/` and is merged into the target project root on install/update.

Payload scaffold at `gald3r_template/` root: `.gald3r/`, `.gitignore`, `scripts/`, `temp_docs/`,
`temp_scripts/`, `docs/`, and `setup_gald3r_project.ps1`.