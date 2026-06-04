<p align="center">
  <img src="logo/Gald3r_Logo_Big.jpg" alt="Gald3r" width="400" />
</p>

<h1 align="center">gald3r — AI Agent Framework for Your Project</h1>

<p align="center">
  File-based memory, task management, and agent orchestration that installs in minutes.
  Works in <strong>Cursor</strong> and <strong>Claude Code</strong> (Tier 1), plus
  <strong>34 AI coding platforms</strong> — no server, no database, no Docker.
</p>

<p align="center">
  <a href="https://github.com/wrm3/gald3r/releases/tag/v1.11.0"><img src="https://img.shields.io/badge/version-1.11.0-blue" alt="version 1.11.0" /></a>
  <a href="CHANGELOG.md">Changelog</a> |
  <a href="CONTRIBUTING.md">Contributing</a> |
  <a href="gald3r_supported_platforms.html">All 34 platforms</a>
</p>

---

## What is gald3r?

gald3r is a template you drop into any project to give your AI coding assistant a persistent brain.

Once installed, your AI gains:

- **Persistent memory** across sessions — tasks, bugs, plans, constraints survive every restart
- **110 skills** for common dev workflows (code review, QA, task management, planning, and more)
- **177 commands** invoked directly in chat (`@g-status`, `@g-go`, `@g-task-new`, `@g-bug-report`)
- **37 hooks** that fire on IDE events (session start, file save, commit)
- **12 rules** that keep the agent disciplined every session
- **Works in both Cursor and Claude Code** over one shared `.gald3r/` brain — plan in one, code in the other

Everything is plain markdown files in your repo. No accounts, no API keys beyond what you already have.

---

## Quick Install

### Option 1 — Copy the template (recommended)

```bash
git clone https://github.com/wrm3/gald3r.git

# Default: installs Cursor + Claude Code + shared brain
cp -r gald3r/project_template/. /path/to/your/project/
```

Then open your project in Cursor or Claude Code and run `@g-setup` / `/g-setup`.

### Option 2 — Installer script (supports all 34 platforms)

```powershell
# Default: Cursor + Claude Code (same as copying project_template/)
.\setup_gald3r_project.ps1 -TargetPath "C:\MyProject"

# Install for a specific platform only
.\setup_gald3r_project.ps1 -TargetPath "C:\MyProject" -Platform windsurf
.\setup_gald3r_project.ps1 -TargetPath "C:\MyProject" -Platform cline
.\setup_gald3r_project.ps1 -TargetPath "C:\MyProject" -Platform cursor    # Cursor only (no .claude/)
```

---

## What Gets Installed

**Default install** (Cursor + Claude Code):

```
your-project/
├── .cursor/          ← Cursor config (rules, skills, commands, hooks, agents)
├── .claude/          ← Claude Code config (same skill set, markdown format)
├── .gald3r/          ← Shared project memory (tasks, bugs, plans, constraints)
├── .gald3r_sys/      ← gald3r system files (skills engine, platform specs)
├── AGENTS.md         ← Universal agent instructions (read by both IDEs)
├── CLAUDE.md         ← Claude Code entry point
└── WORKFLOW.md       ← Project workflow definition
```

**Platform-specific install** (e.g. `-Platform windsurf`): same shared brain, plus the platform's config folder (`.windsurf/rules/` etc.). Cursor and Claude config are skipped.

---

## Platform Support

| Platform | Tier | Notes |
|---|---|---|
| **Cursor** | ✅ Tier 1 | Rules (`.mdc`), skills, commands, hooks, agents |
| **Claude Code** | ✅ Tier 1 | Rules (`.md`), skills, commands, hooks, agents |
| **Windsurf, Cline, Roo, Aider** | ⚠️ Tier 2 | Rules + brain + AGENTS.md |
| **Copilot, Codex, Augment, Gemini, Qwen, Continue** | ⚠️ Tier 2 | Rules + brain + AGENTS.md |
| **20+ more** | 🔜 Tier 3 | Brain + AGENTS.md (rules where supported) |

Use `-Platform <name>` with the installer, or copy `platforms/<name>/` manually.
See [gald3r_supported_platforms.html](gald3r_supported_platforms.html) for the full list.

> **Cursor + Claude Code users get the full experience.** Other platforms receive the shared
> `.gald3r/` brain and `AGENTS.md` instructions, with rules where the platform supports them.

---

## How It Works

```
Your project root
├── AGENTS.md  ─────────────────────────────────────────────────────────┐
├── .cursor/ (rules + skills + commands)   ← Cursor reads these         │
├── .claude/ (rules + skills + commands)   ← Claude Code reads these     │
│                                                                         │
└── .gald3r/ ────────────────────────────────────────────────────────────┘
    TASKS.md    ← shared task list, visible to both IDEs
    BUGS.md     ← shared bug tracker
    PLAN.md     ← shared strategy & milestones
    CONSTRAINTS.md  ← rules the agent must never break
```

Every command you run in Cursor or Claude Code reads and writes these same files. Switch between tools anytime — context is never lost.

---

## Key Commands

| Command | What it does |
|---|---|
| `@g-setup` / `/g-setup` | Initialize gald3r in a new project |
| `@g-status` / `/g-status` | Show project health: tasks, bugs, open items |
| `@g-go` / `/g-go` | Start an autonomous work session on the next task |
| `@g-task-new` | Create a new task with spec |
| `@g-bug-report` | File and triage a bug |
| `@g-medic` | Run self-diagnostics on the gald3r installation |
| `@g-plan` | Update and review the project plan |

Full command catalog: [gald3r Wiki — Commands](https://github.com/wrm3/gald3r/wiki/Commands)

---

## Project Structure After Install

```
.gald3r/
├── TASKS.md          ← master task index
├── BUGS.md           ← bug index
├── PLAN.md           ← milestones and strategy
├── PROJECT.md        ← vision, mission, goals
├── CONSTRAINTS.md    ← things the AI must never do
├── SUBSYSTEMS.md     ← component registry
├── tasks/            ← individual task files (one per task)
├── bugs/             ← individual bug files
└── features/         ← PRD files
```

---

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md). Issues and PRs welcome.

---

## License

[MIT](LICENSE) — see [NOTICE](NOTICE) for third-party attributions.

---

*Powered by gald3r v1.11.0 · [Changelog](CHANGELOG.md) · [Roadmap](ROADMAP.md)*
