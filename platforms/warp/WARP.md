# agents.md

> This file follows the agents.md format for AI agent instructions.
> Compatible with Cursor (`.cursor/`), Claude Code (`.claude/`), Gemini (`.agent/`),
> Codex (`.codex/`), and OpenCode (`.opencode/`).
>
> This block is framework-authored and refreshed by `gald3r platform install
> --generated` (T357) — content between the marker comments wrapping this block is
> regenerated on every install; anything added **outside** the block (above the
> START marker or below the END marker) is local customization and is preserved
> across re-runs.
>
> Run `gald3r setup` / `@g-setup` to fill in this project's mission, goals, and
> command catalog — this generated block intentionally carries no project-specific
> content. See the sibling `GALD3R.md` root file for how the gald3r framework
> itself works.

---

## Project Structure

```
.gald3r/                  # Task management data (shared across all IDEs)
├── TASKS.md             # Master task checklist
├── BUGS.md              # Bug index
├── PLAN.md              # Strategy and milestones
├── PROJECT.md           # Vision, mission, goals
├── CONSTRAINTS.md       # Architectural rules agents must follow
├── SUBSYSTEMS.md        # Component registry
├── tasks/               # Individual task spec files
├── bugs/                # Individual bug files
├── features/            # PRD files
└── linking/             # Cross-project coordination

.cursor/                 # Cursor IDE configuration
├── agents/              # gald3r system agents (g-agnt-*)
├── skills/               # Skills (g-skl-*)
├── commands/             # @g-* commands
├── hooks/                # Automation hooks
└── rules/                # Always-apply rules (g-rl-*)

.claude/                 # Claude Code (same content as .cursor/)
.agent/                  # Gemini / Antigravity
.codex/                  # Codex
.opencode/               # OpenCode
```

---

## Task Status Indicators

| TASKS.md | YAML status | Meaning |
|---------|-------------|---------|
| `[ ]` | (no file yet) | Pending — not started |
| `[📋]` | `pending` | Spec written, ready to start |
| `[🔄]` | `in-progress` | Being worked on |
| `[🔍]` | `awaiting-verification` | Done, needs review |
| `[✅]` | `completed` | Done |
| `[❌]` | `failed` | Failed or cancelled |

---

## Direct Edit Policy

Edit these files directly without asking for permission:

- `.gald3r/TASKS.md` — task checklist
- `.gald3r/BUGS.md` — bug index
- `.gald3r/PLAN.md` — project plan
- `.gald3r/PROJECT.md` — project identity
- All files in `.gald3r/tasks/`, `.gald3r/bugs/`, `.gald3r/features/`

---

## `.gald3r/` Folder Gate

Never read or write `.gald3r/` files without following the appropriate skill
workflow. Use `g-skl-tasks` for task operations, `g-skl-qa` for bugs, `g-skl-plan`
for planning files.

---

## Documentation Placement

All `.md` documentation files go in `docs/` — never in the project root.
Exceptions: `AGENTS.md`, `README.md`, `LICENSE`, `CLAUDE.md`, `CHANGELOG.md`,
`GALD3R.md`.

---

## PowerShell (Windows)
- Use `;` as command separator (NOT `&&`)
- Use `curl.exe` or `Invoke-WebRequest`, never bare `curl`
- Use `uv` for Python virtual environments, never bare `pip` or `python -m venv`
