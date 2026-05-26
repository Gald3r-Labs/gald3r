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

---

## Per-Platform Deploy Scaffolds (T1207 / T1277)

Each `*/` subdirectory here is a per-platform deploy scaffold: a
`<platform>_instructions.md` guide plus the config files that platform actually consumes
(e.g. Aider `.aider.conf.yml` + `CONVENTIONS.md`, Kiro `steering/`, Warp Drive workflow
stubs). The authoritative source for each guide is the matching `g-skl-platform-*` skill.

## gitignore Decision — root platform output dirs (T1277 AC6)

**Decision: in installed projects, the gald3r-authored platform config dirs are TRACKED
source — they are NOT gitignored.**

- Platform config files (`.windsurfrules`, `.clinerules`, `.roorules`, `.kiro/steering/*.md`,
  `.junie/guidelines.md`, `.augment/guidelines.md`, `.aider.conf.yml`, `CONVENTIONS.md`,
  `GOOSE.md`, `SOUL.md`, `.openhands/microagents/*.md`, `.mistral/*`, `.qwen/*`, `.replit`,
  `replit.nix`, `.warp/workflows/*.yaml`) are deliberate, version-controlled project context.
  Losing them would lose the project's AI behavior contract. They are committed, like the
  existing `.cursor`/`.claude`/`.codex` scaffolds.
- **No new ignore entries are added** for these platforms. The only platform-related ignores
  remain the *generated* skill/agent/command mirror subdirs that are regenerated from the
  canonical root `skills/`,`agents/`,`commands/` (already covered by the install `.gitignore`
  T1048 section and the Cursor continual-learning state files).
- Secrets are never gitignored at the dir level — API keys belong in environment variables,
  not in committed config (and `.env` is already ignored by the universal `.gitignore` section).
- `.gald3r-agent/` is a **parity platform**, not an install deploy target: it has no installed
  project output dir and therefore no install `.gitignore` entry (see its instructions guide).

`g-skl-setup` delegates platform deployment and `.gitignore` section-marker merge to
`setup_gald3r_project.ps1`; this decision requires no g-skl-setup behavior change because the
default (track platform config) needs no new ignore rule.