<p align="center">
  <img src="logo/Gald3r_Logo_Big.jpg" alt="Gald3r" width="400" />
</p>

<h1 align="center">gald3r — give your AI coding tools one shared brain</h1>

<p align="center">
  Your AI assistants each start from zero, every session, in every tool.<br />
  gald3r drops a persistent, file-based brain into your repo — tasks, bugs, plans,
  and constraints that <strong>every</strong> AI tool reads and writes.<br />
  Plan in one tool. Code in another. Nothing is lost between them.
</p>

<p align="center">
  <a href="https://github.com/Gald3r-Labs/gald3r/releases"><img src="https://img.shields.io/badge/version-4.0.0-blue" alt="version 4.0.0" /></a>
  <a href="https://github.com/Gald3r-Labs/gald3r_core"><img src="https://img.shields.io/badge/engine-gald3r__core-6f42c1" alt="engine" /></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-FSL--1.1--Apache-green" alt="license" /></a>
  <a href="CHANGELOG.md">Changelog</a> ·
  <a href="ROADMAP.md">Roadmap</a> ·
  <a href="PLATFORM_SUPPORT.html">All 39 platforms</a>
</p>

---

## The problem

You use Cursor for one thing and Claude Code for another. Maybe Copilot at work, Codex
on a side project, a local model when you're offline. Each one opens with no idea what
you decided yesterday, what's already broken, or what you told the last one never to touch.

So you re-explain. Every time. In every tool.

## What gald3r does

gald3r installs a `.gald3r/` folder in your project — plain markdown, tracked in git, owned
by you. Your tasks, bugs, plans, constraints, and architecture decisions live there.

Every AI tool you use reads the same folder.

```
your-project/
├── .gald3r/          ← the shared brain: tasks, bugs, plans, constraints
├── .claude/          ← Claude Code reads these
├── .cursor/          ← Cursor reads these
└── AGENTS.md         ← every other platform reads this
```

Switch tools mid-task and the context follows you. Your teammate clones the repo and their
AI already knows the project. Nothing lives in a vendor's session history.

---

## Two pieces, one product

**gald3r 4.0** is a matched pair. This repo is half of it.

| | | |
|---|---|---|
| **gald3r** (this repo) | The framework | The `.gald3r/` brain, plus 116 skills, 182 commands, 13 rules, 38 hooks, and 15 agents — packaged for 39 AI coding platforms. This is what lands *in your project*. |
| **[gald3r_core](https://github.com/Gald3r-Labs/gald3r_core)** | The engine | One signed binary. Runs every deterministic operation — task and bug lifecycle, validation, the local database, multi-agent orchestration — with **zero LLM calls**. |

The framework is what your AI reads. The engine is what actually executes. You can run the
framework on its own; adding the engine makes it fast, deterministic, and enforceable.

> **Getting the engine:** download the signed binary or MSI installer from
> **[gald3r_core releases](https://github.com/Gald3r-Labs/gald3r_core/releases)**.
> The desktop app installs from **[gald3r_throne](https://github.com/Gald3r-Labs/gald3r_throne)**.
> Each product installs from its own repo — this one carries the framework.

---

## Quick start

### Copy the template

```bash
git clone https://github.com/Gald3r-Labs/gald3r.git
cp -r gald3r/project_template/. /path/to/your/project/
```

Open your project and run `/g-setup` (Claude Code) or `@g-setup` (Cursor). That's it —
the brain is live and your AI can see it.

### Or use the installer (any of 39 platforms)

```bash
# macOS / Linux
python setup_gald3r_project.py --target-path "/path/to/MyProject"

# one platform only
python setup_gald3r_project.py --target-path "/path/to/MyProject" --platform windsurf
```

```powershell
# Windows
.\setup_gald3r_project.bat -TargetPath "C:\MyProject"
.\setup_gald3r_project.bat -TargetPath "C:\MyProject" -Platform cursor
```

No accounts. No API keys beyond the ones your AI tool already has. No server, no database,
no Docker.

---

## What you get

- **A brain that survives restarts** — tasks, bugs, plans, and constraints in plain markdown,
  in your repo, in your git history
- **116 skills** covering the work you actually do: code review, QA, planning, task
  management, release, security scanning, research
- **182 commands** you invoke straight from chat — `/g-status`, `/g-go`, `/g-task-new`,
  `/g-bug-report`, `/g-plan`
- **38 hooks** that fire on real IDE events — session start, file save, pre-commit — so
  discipline is *enforced*, not merely suggested
- **13 rules** loaded every session to keep the agent honest
- **15 specialized agents** for review, verification, QA, and infrastructure work
- **39 platforms supported**, with Cursor and Claude Code at full parity

---

## Platform support

| Platform | Tier | What it gets |
|---|---|---|
| **Cursor**, **Claude Code** | Tier 1 | Everything — rules, skills, commands, hooks, agents |
| **Windsurf, Cline, Roo, Aider, Copilot, Codex, Gemini, Qwen, Continue** | Tier 2 | Rules + shared brain + `AGENTS.md` |
| **30 more** | Tier 3 | Shared brain + `AGENTS.md`, rules where the platform supports them |

Full matrix: [PLATFORM_SUPPORT.html](PLATFORM_SUPPORT.html) ·
[PLATFORM_CAPABILITY_MATRIX.md](PLATFORM_CAPABILITY_MATRIX.md)

Every tier reads the same `.gald3r/` folder. A Tier 3 tool and a Tier 1 tool working the
same repo stay in sync.

---

## Commands you'll use first

| Command | What it does |
|---|---|
| `/g-setup` | Initialize gald3r in a project |
| `/g-status` | Project health — tasks, bugs, blockers, what's next |
| `/g-task-new` | Create a task, fully specced |
| `/g-bug-report` | File and triage a bug |
| `/g-go` | Autonomous work session on the next task, with independent review |
| `/g-plan` | Update the project plan |
| `/g-medic` | Diagnose and repair the gald3r install |

Cursor uses `@g-` instead of `/g-`. Same commands, same brain.

Full catalog: [gald3r Wiki](https://github.com/Gald3r-Labs/gald3r/wiki)

---

## What's in this repo

```
project_template/    ← what gets copied into your project
platforms/           ← per-platform payloads (39 of them)
setup_gald3r_project.py / .bat / .sh   ← the installers
PLATFORM_SUPPORT.html                  ← the full support matrix
releases/            ← release notes archive
```

---

## Contributing

Issues and PRs welcome — see [CONTRIBUTING.md](CONTRIBUTING.md).

## License

[Fair Source License 1.1 (FSL-1.1-Apache)](LICENSE) — see [NOTICE](NOTICE) for third-party
attributions.

---

<p align="center">
  <em>gald3r 4.0 · framework + <a href="https://github.com/Gald3r-Labs/gald3r_core">engine</a></em><br />
  <a href="CHANGELOG.md">Changelog</a> · <a href="ROADMAP.md">Roadmap</a>
</p>
