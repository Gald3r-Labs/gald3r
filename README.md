<p align="center">
  <img src="logo/gald3r-logo.png" alt="Gald3r" width="400" />
</p>

<h1 align="center">Gald3r -- AI Dev Framework for 34 AI Coding Tools</h1>

<p align="center">
  File-based memory, task management, and agent orchestration that works across
  Cursor, Claude Code, Copilot, Windsurf, Cline, Roo, Codex, Aider, Kilo Code, Deep Code,
  Hermes, CodeBuddy, AstrBot, OpenHands, Gemini, OpenCode, and 18 more.
</p>

<p align="center">
  <a href="https://www.gald3r.ai">www.gald3r.ai</a> |
  <a href="CHANGELOG.md">Changelog</a> |
  <a href="CONTRIBUTING.md">Contributing</a>
</p>

---

## What is Gald3r?

Gald3r is a framework that runs **inside your AI coding tool** -- not alongside it.
Drop the template for your tool into your project root, and your AI assistant gains:

- **Persistent memory** across sessions (tasks, bugs, plans, constraints)
- **22 specialized agents** (code reviewer, QA engineer, task manager, etc.)
- **100+ skills** for common dev workflows
- **149 commands** invoked directly in chat (`@g-status`, `@g-go`, `@g-medic`)
- **Hooks** that fire on IDE events (session start, file write, commit)
- **Cross-platform parity** -- the same framework, tuned per tool

Everything is plain markdown files in your repo. No server, no database, no Docker required.

---

## Platform Support (34 AI Coding Tools) {#platform-support}

Pick your tool and open its folder -- each contains a complete, ready-to-deploy gald3r setup.

### Tier 1 -- Fully Supported

*Tested by gald3r maintainers on every release. Bugs filed against this tier block release.*

| Tool | Folder | Install |
|---|---|---|
| ![Cursor](https://img.shields.io/badge/Cursor-Tier_1-green) | [cursor/](./cursor/) | Copy `cursor/` contents to project root |
| ![Claude Code](https://img.shields.io/badge/Claude_Code-Tier_1-green) | [claude/](./claude/) | Copy `claude/` contents to project root |
| ![Copilot](https://img.shields.io/badge/GitHub_Copilot-Tier_1-green) | [copilot/](./copilot/) | Copy `copilot/` contents to project root |
| ![OpenCode](https://img.shields.io/badge/OpenCode-Tier_1-green) | [opencode/](./opencode/) | Copy `opencode/` contents to project root |
| ![Windsurf](https://img.shields.io/badge/Windsurf-Tier_1-green) | [windsurf/](./windsurf/) | Copy `windsurf/` contents to project root |
| ![Cline](https://img.shields.io/badge/Cline-Tier_1-green) | [cline/](./cline/) | Copy `cline/` contents to project root |
| ![Roo Code](https://img.shields.io/badge/Roo_Code-Tier_1-green) | [roo/](./roo/) | Copy `roo/` contents to project root |
| ![Codex CLI](https://img.shields.io/badge/Codex_CLI-Tier_1-green) | [codex/](./codex/) | Copy `codex/` contents to project root |
| ![CodeBuddy](https://img.shields.io/badge/CodeBuddy_(Tencent)-Tier_1-green) | [codebuddy/](./codebuddy/) | Copy `codebuddy/` contents to project root |

### Tier 2 -- Community Supported

*Tested by the community. Contributions and bug reports welcome.*

| Tool | Folder | Install |
|---|---|---|
| ![Aider](https://img.shields.io/badge/Aider-Tier_2-yellow) | [aider/](./aider/) | Copy `aider/` contents to project root |
| ![Augment](https://img.shields.io/badge/Augment-Tier_2-yellow) | [augment/](./augment/) | Copy `augment/` contents to project root |
| ![Goose](https://img.shields.io/badge/Goose-Tier_2-yellow) | [goose/](./goose/) | Copy `goose/` contents to project root |
| ![Warp](https://img.shields.io/badge/Warp-Tier_2-yellow) | [warp/](./warp/) | Copy `warp/` contents to project root |
| ![OpenHands](https://img.shields.io/badge/OpenHands-Tier_2-yellow) | [openhands/](./openhands/) | Copy `openhands/` contents to project root |
| ![Kiro](https://img.shields.io/badge/Kiro-Tier_2-yellow) | [kiro/](./kiro/) | Copy `kiro/` contents to project root |
| ![Kiro CLI](https://img.shields.io/badge/Kiro_CLI-Tier_2-yellow) | [kiro-cli/](./kiro-cli/) | Copy `kiro-cli/` contents to project root |
| ![Junie](https://img.shields.io/badge/Junie-Tier_2-yellow) | [junie/](./junie/) | Copy `junie/` contents to project root |
| ![Replit](https://img.shields.io/badge/Replit-Tier_2-yellow) | [replit/](./replit/) | Copy `replit/` contents to project root |
| ![Gemini CLI](https://img.shields.io/badge/Gemini_CLI-Tier_2-yellow) | [gemini/](./gemini/) | Copy `gemini/` contents to project root |
| ![Kilo Code](https://img.shields.io/badge/Kilo_Code-Tier_2-yellow) | [kilo-code/](./kilo-code/) | Copy `kilo-code/` contents to project root |

### Tier 3 -- Experimental

*Scaffold available. May have structural gaps. Contributions very welcome.*

| Tool | Folder | Install |
|---|---|---|
| ![Mistral](https://img.shields.io/badge/Mistral-Tier_3-orange) | [mistral/](./mistral/) | Copy `mistral/` contents to project root |
| ![Antigravity](https://img.shields.io/badge/Antigravity-Tier_3-orange) | [antigravity/](./antigravity/) | Copy `antigravity/` contents to project root |
| ![OpenClaw](https://img.shields.io/badge/OpenClaw-Tier_3-orange) | [openclaw/](./openclaw/) | Copy `openclaw/` contents to project root |
| ![Qwen](https://img.shields.io/badge/Qwen-Tier_3-orange) | [qwen/](./qwen/) | Copy `qwen/` contents to project root |
| ![SubQ](https://img.shields.io/badge/SubQ-Tier_3-orange) | [subq/](./subq/) | Copy `subq/` contents to project root |
| ![Deep Code](https://img.shields.io/badge/Deep_Code_(DeepSeek)-Tier_3-orange) | [deepcode/](./deepcode/) | Copy `deepcode/` contents to project root |
| ![Hermes](https://img.shields.io/badge/Hermes_(Nous_Research)-Tier_3-orange) | [hermes/](./hermes/) | Copy `hermes/` contents to project root |
| ![AstrBot](https://img.shields.io/badge/AstrBot-Tier_3-orange) | [astrbot/](./astrbot/) | Upload skills .zip via WebUI |
| ![Amp Code](https://img.shields.io/badge/Amp_Code_(Sourcegraph)-Tier_1-green) | [amp/](./amp/) | Copy `amp/` contents to project root |
| ![Continue](https://img.shields.io/badge/Continue-Tier_1-green) | [continue/](./continue/) | Copy `continue/` contents to project root |
| ![Void Editor](https://img.shields.io/badge/Void_Editor-Tier_3-orange) | [void/](./void/) | Copy `void/` contents to project root |
| ![Kimi Code](https://img.shields.io/badge/Kimi_Code_(Moonshot)-Tier_1-green) | [kimi/](./kimi/) | Copy `kimi/` contents to project root |
| ![TRAE](https://img.shields.io/badge/TRAE_(ByteDance)-Tier_1-green) | [trae/](./trae/) | Copy `trae/` contents to project root |
| ![Qoder](https://img.shields.io/badge/Qoder_(Alibaba)-Tier_2-yellow) | [qoder/](./qoder/) | Copy `qoder/` contents to project root |

---

## Quick Start

**New project?** -> [instructions_new_project.md](./instructions_new_project.md)

**Adding to an existing project?** -> [instructions_existing_project.md](./instructions_existing_project.md)

---

## What's Inside Each Template

Every platform folder contains the same gald3r core, tuned for that tool:

- **Agents** -- 22 specialized AI roles (code reviewer, QA, task manager, infrastructure, etc.)
- **Skills** -- 100+ reusable workflows invoked by agents and commands
- **Commands** -- 149 chat commands (`@g-go`, `@g-status`, `@g-medic`, `@g-task-new`, ...)
- **Rules** -- Persistent behavioral standards loaded every session
- **Hooks** -- Event-driven automation (pre-commit, session-start, file-write)
- **Task system** -- File-based `.gald3r/` folder tracks tasks, bugs, plans, constraints

---

## Releases

See [releases/](./releases/) for release notes and [CHANGELOG.md](./CHANGELOG.md) for full history.

Latest: **v1.6.0** -- WPAC Workspace-Control Architecture

---

## Contributing

See [CONTRIBUTING.md](./CONTRIBUTING.md). Platform contributions especially welcome for Tier 2 and Tier 3 tools.

---

*Built with gald3r. Runs on gald3r.*
