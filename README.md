<p align="center">
  <img src="logo/Gald3r_Logo_Big.jpg" alt="Gald3r" width="400" />
</p>

<h1 align="center">gald3r â€” AI Agent Framework for Your Project</h1>

<p align="center">
  File-based memory, task management, and agent orchestration that installs in minutes â€”
  now backed by a bundled <strong>file-first engine</strong> (a <code>gald3r</code> CLI + MCP server,
  zero LLM calls). Works in <strong>Cursor</strong> and <strong>Claude Code</strong> (Tier 1), plus
  <strong>34 AI coding platforms</strong> â€” no server, no database, no Docker.
</p>

<p align="center">
  <a href="https://github.com/wrm3/gald3r/releases/tag/v2.4.0"><img src="https://img.shields.io/badge/version-2.4.0-blue" alt="version 2.4.0" /></a>
  <a href="CHANGELOG.md">Changelog</a> |
  <a href="CONTRIBUTING.md">Contributing</a> |
  <a href="gald3r_supported_platforms.html">All 34 platforms</a>
</p>

---

## What is gald3r?

gald3r is a template you drop into any project to give your AI coding assistant a persistent brain.

Once installed, your AI gains:

- **Persistent memory** across sessions â€” tasks, bugs, plans, constraints survive every restart
- **110 skills** for common dev workflows (code review, QA, task management, planning, and more)
- **179 commands** invoked directly in chat (`@g-status`, `@g-go`, `@g-task-new`, `@g-bug-report`)
- **37 hooks** that fire on IDE events (session start, file save, commit)
- **12 rules** that keep the agent disciplined every session
- **Works in both Cursor and Claude Code** over one shared `.gald3r/` brain â€” plan in one, code in the other
- **A bundled file-first engine** (Mode-A, new in 2.0) â€” every system (tasks, bugs, vault, releases, â€¦) is driven by a deterministic Python core via the `gald3r` CLI or an MCP server, with zero LLM calls. `gald3r doctor` keeps the install healthy. One prerequisite: [`uv`](https://docs.astral.sh/uv/).

Everything is plain markdown files in your repo. No accounts, no API keys beyond what you already have.


## What is new in v2.1.0

<!-- Pending release highlights (user-facing). Filled as features ship; cleared at publish. -->
### Coming in the next release

**Safe self-update â€” CLI and in-app**

```bash
gald3r version-check        # see if a newer gald3r version is available (offline-safe)
gald3r upgrade              # safe update: auto-backup â†’ migrate â†’ rollback on failure
gald3r upgrade --apply      # confirm and apply (--dry-run is the default)
gald3r init --name "My App" # scaffold a fresh gald3r project in any folder
gald3r setup all            # initialize agent + throne against your shared install home
```

- **`gald3r version-check`** queries the gald3r server and reports your version vs. the latest â€” degrades gracefully offline.
- **`gald3r upgrade`** backs up your `.gald3r/` folder with a timestamp, migrates it to the latest format, and rolls back byte-for-byte if anything goes wrong. Your tasks, bugs, and plans are **never touched**.
- **Throne in-app update** â€” gald3r_throne shows an "update available" badge when a new version is detected and can apply the update entirely from within the app (no Python required, compiled Rust updater with full backup + rollback).
- **Centralized install home** + a global `gald3r` command, with a USB-portable mode (`--portable`).
- **`gald3r init` / `gald3r update`** scaffold and update projects in any folder, idempotently.

> **Install the apps:** `gald3r install agent` and `gald3r install throne` download the precompiled, signed apps from our public GitHub Releases (`Gald3r-Labs/gald3r_agent` and `Gald3r-Labs/gald3r_throne`) and verify them before installing -- the agent binary against a SHA-256 sidecar, the Throne installer against a minisign `.sig` (a missing/tampered signature fails loud, never a silent install). Use `--dry-run` to preview, `--release vX.Y.Z` to pin a version, or `--from-source` for a local developer build (see [RELEASE.md](RELEASE.md)). macOS is coming soon.
<!-- PENDING_RELEASE_START -->
<!-- Pending release highlights (user-facing). Filled as features ship; cleared at publish. -->
<!-- PENDING_RELEASE_END -->

---

## Quick Install

### Option 1 â€” Copy the template (recommended)

```bash
git clone https://github.com/wrm3/gald3r.git

# Default: installs Cursor + Claude Code + shared brain
cp -r gald3r/project_template/. /path/to/your/project/
```

Then open your project in Cursor or Claude Code and run `@g-setup` / `/g-setup`.

### Option 2 â€” Installer script (supports all 34 platforms)

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
â”œâ”€â”€ .cursor/          â† Cursor config (rules, skills, commands, hooks, agents)
â”œâ”€â”€ .claude/          â† Claude Code config (same skill set, markdown format)
â”œâ”€â”€ .gald3r/          â† Shared project memory (tasks, bugs, plans, constraints)
â”œâ”€â”€ .gald3r_sys/      â† gald3r system files (skills engine, platform specs)
â”œâ”€â”€ AGENTS.md         â† Universal agent instructions (read by both IDEs)
â”œâ”€â”€ CLAUDE.md         â† Claude Code entry point
â””â”€â”€ WORKFLOW.md       â† Project workflow definition
```

**Platform-specific install** (e.g. `-Platform windsurf`): same shared brain, plus the platform's config folder (`.windsurf/rules/` etc.). Cursor and Claude config are skipped.

---

## The engine (CLI + MCP)

New in 2.0: a bundled, file-first Python engine drives every system deterministically â€” **no LLM,
no network, no Docker**. It lives in `.gald3r_sys/engine/`. The only prerequisite is
[`uv`](https://docs.astral.sh/uv/); the first run provisions it automatically.

### Command line

```bash
# from your project root â€” the first run builds the engine (a few seconds), then it's instant
uv run --project .gald3r_sys/engine gald3r doctor          # health check  (add --fail-below 80 for CI)
```

For brevity, alias the prefix â€” `alias gald3r='uv run --project .gald3r_sys/engine gald3r'` â€” then:

```bash
gald3r task new   --title "Wire up auth" --priority high
gald3r bug new    --title "Login 500 on empty cart" --severity high
gald3r goal add   --text "Ship the MVP by Friday"
gald3r vault ingest --title "JWT notes" --type article --source https://example.com/jwt
gald3r inbox                                               # absorb staged task/bug drafts into live state
gald3r prompt get role.code_reviewer                       # load a reasoning brief
gald3r --json task list                                    # machine-readable output
```

(`python -m gald3r â€¦` works too, if you'd rather not alias.)

### As an MCP server

Expose the same operations as ~20 MCP tools to any MCP-capable agent. Add to your client's MCP config:

```json
{
  "mcpServers": {
    "gald3r": {
      "command": "uv",
      "args": ["run", "--project", ".gald3r_sys/engine", "gald3r", "mcp"]
    }
  }
}
```

Your agent then calls `gald3r_task_new`, `gald3r_bug_list`, `gald3r_prompt_get`, â€¦ directly.

### No engine? Still works.

The engine is **additive**. The `.gald3r/` state is plain markdown, and every slimmed skill keeps a
`SKILL.full.md` fallback â€” so a files-only install (no `uv` / Python) runs unchanged.

---

## Platform Support

| Platform | Tier | Notes |
|---|---|---|
| **Cursor** | âœ… Tier 1 | Rules (`.mdc`), skills, commands, hooks, agents |
| **Claude Code** | âœ… Tier 1 | Rules (`.md`), skills, commands, hooks, agents |
| **Windsurf, Cline, Roo, Aider** | âš ï¸ Tier 2 | Rules + brain + AGENTS.md |
| **Copilot, Codex, Augment, Gemini, Qwen, Continue** | âš ï¸ Tier 2 | Rules + brain + AGENTS.md |
| **20+ more** | ðŸ”œ Tier 3 | Brain + AGENTS.md (rules where supported) |

Use `-Platform <name>` with the installer, or copy `platforms/<name>/` manually.
See [gald3r_supported_platforms.html](gald3r_supported_platforms.html) for the full list.

> **Cursor + Claude Code users get the full experience.** Other platforms receive the shared
> `.gald3r/` brain and `AGENTS.md` instructions, with rules where the platform supports them.

---

## How It Works

```
Your project root
â”œâ”€â”€ AGENTS.md  â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
â”œâ”€â”€ .cursor/ (rules + skills + commands)   â† Cursor reads these         â”‚
â”œâ”€â”€ .claude/ (rules + skills + commands)   â† Claude Code reads these     â”‚
â”‚                                                                         â”‚
â””â”€â”€ .gald3r/ â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
    TASKS.md    â† shared task list, visible to both IDEs
    BUGS.md     â† shared bug tracker
    PLAN.md     â† shared strategy & milestones
    CONSTRAINTS.md  â† rules the agent must never break
```

Every command you run in Cursor or Claude Code reads and writes these same files. Switch between tools anytime â€” context is never lost.

---

## Key Commands

| Command | What it does |
|---|---|
| `@g-setup` / `/g-setup` | Initialize gald3r in a new project |
| `@g-install-agent` / `/g-install-agent` | Download + install the Gald3r Agent CLI from the public GitHub Release |
| `@g-install-throne` / `/g-install-throne` | Download + install the Gald3r Throne desktop app from the public GitHub Release |
| `@g-status` / `/g-status` | Show project health: tasks, bugs, open items |
| `@g-go` / `/g-go` | Start an autonomous work session on the next task |
| `@g-task-new` | Create a new task with spec |
| `@g-bug-report` | File and triage a bug |
| `@g-medic` | Run self-diagnostics on the gald3r installation |
| `@g-plan` | Update and review the project plan |

Full command catalog: [gald3r Wiki â€” Commands](https://github.com/wrm3/gald3r/wiki/Commands)

---

## Project Structure After Install

```
.gald3r/
â”œâ”€â”€ TASKS.md          â† master task index
â”œâ”€â”€ BUGS.md           â† bug index
â”œâ”€â”€ PLAN.md           â† milestones and strategy
â”œâ”€â”€ PROJECT.md        â† vision, mission, goals
â”œâ”€â”€ CONSTRAINTS.md    â† things the AI must never do
â”œâ”€â”€ SUBSYSTEMS.md     â† component registry
â”œâ”€â”€ tasks/            â† individual task files (one per task)
â”œâ”€â”€ bugs/             â† individual bug files
â””â”€â”€ features/         â† PRD files
```

---

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md). Issues and PRs welcome.

---

## License

[Fair Source License 1.1 (FSL-1.1-Apache)](LICENSE) â€” see [NOTICE](NOTICE) for third-party attributions.

---

*Powered by gald3r v2.4.0 Â· [Changelog](CHANGELOG.md) Â· [Roadmap](ROADMAP.md)*