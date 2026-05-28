# CLAUDE.md - {project_name}

> Claude Code identity overlay for this project.
> **Universal instructions live in [`AGENTS.md`](./AGENTS.md)** — read it first.
> This file holds ONLY Claude Code-specific notes; shared architecture,
> commands, task-management, vault, parity, and enforcement rules are in `AGENTS.md`.
> Run `@g-setup` to initialize gald3r and auto-fill `{project_name}`.

---

## What is gald3r?

gald3r is a file-first, AI-assisted task-tracking and coordination framework that
runs across every major AI IDE (Cursor, Claude Code, Gemini, Codex, OpenCode, and
more). All project state — tasks, bugs, plans, constraints, subsystems, and
cross-project coordination — lives under `.gald3r/` as plain markdown, so it is
portable, git-trackable, and editor-agnostic.

`AGENTS.md` is the single source of truth for how agents behave in this project.
Claude Code reads `AGENTS.md` plus the Claude-specific notes below.

---

## Claude Code-Specific Notes

### Command Prefix
Use the `/g-` prefix for gald3r commands in Claude Code (Cursor uses `@g-`).
The full command and agent catalog is in `AGENTS.md` and `docs/COMMANDS.md`.

### Rules
Always-apply rules live in `.claude/rules/g-rl-*.md` and load automatically at the
start of every session. They are **referenced, not inlined here** — trimming this
file does not disable them. Do not edit rule files unless updating gald3r itself.

### Skills
Skills live in `.claude/skills/g-skl-*/SKILL.md` and load when you invoke a command
or when Claude determines they are relevant.

### Agents
Invoke specialized gald3r agents with `@g-agnt-*` syntax (see the agent table in
`AGENTS.md`).

### Hooks
Claude Code hooks live in `.claude/hooks/` and fire on session start, agent
complete, and before shell execution. Session start injects `.gald3r/` context and
`GUARDRAILS.md`.

### Multi-Agent Sessions
- Skip tasks marked `[🔄]` (in-progress) — they are claimed.
- `[🔄]` older than **2 hours** without a `status_changed` update is stale and
  available for pickup.
- Always write a `status_changed` timestamp to the task file when claiming a task.

### Rate-Limit Graceful Shutdown
At ~85% daily rate limit, stop accepting new tasks and produce a handoff report
(completed this session, left in-progress, files modified, git status).

---

> All other guidance — project structure, command catalog, task status indicators,
> vault knowledge system, parity model, security, and enforcement rules —
> is in [`AGENTS.md`](./AGENTS.md). It is intentionally **not duplicated here**.
