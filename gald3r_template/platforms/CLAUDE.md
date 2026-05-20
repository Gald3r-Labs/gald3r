# CLAUDE.md - {project_name}

> Replace this file with your project's Claude Code instructions.
> Run `@g-setup` to initialize gald3r and auto-fill the placeholders below.

---

## Project Overview

**{project_name}** — {one sentence description of what this project does}

## Tech Stack

- **Language**: {e.g. Python 3.11, TypeScript, Go}
- **Framework**: {e.g. FastAPI, Next.js, Django}
- **Database**: {e.g. PostgreSQL, SQLite, MySQL}
- **Package Manager**: {e.g. uv, npm, pip}

## Key Directories

```
.gald3r/        # Task management — TASKS.md, tasks/, bugs/, features/, subsystems/,
               #   linking/ (INBOX.md, sent_orders/, pending_orders/, peers/),
               #   specifications_collection/ (incoming specs/PRDs from stakeholders)
.claude/       # Claude Code configuration (rules, skills, agents, commands)
src/           # {main source folder}
docs/          # Documentation
```

## Development Commands

```bash
# {Add your project's setup/run commands here}
# e.g.:
# uv sync          # Install dependencies
# uv run dev       # Start dev server
# uv run test      # Run tests
```

## MCP Tools Available

{List MCP tools configured in .mcp.json — or delete this section if not using MCP}

## Security

- Never commit API keys, tokens, or passwords
- Use environment variables for secrets (.env, never committed)
- Always use parameterized queries for database access

## gald3r Task Management

PCAC inbox conflicts gate task claiming, implementation, verification, planning, status work, and swarm partitioning; commands rerun `g-hk-pcac-inbox-check.ps1 -BlockOnConflict` before work and swarm coordinators rerun it every 30 minutes plus before final summaries. `g-medic` L1 is the exception: it runs a non-blocking inbox check, records conflict severity in health scoring, then stops before L2-L4 or any claim/implementation/review/planning work.


This project uses gald3r for AI-assisted task tracking.

- **Tasks**: `.gald3r/TASKS.md` (index) + `.gald3r/tasks/` (individual specs)
- **Bugs**: `.gald3r/BUGS.md` (index) + `.gald3r/bugs/` (individual specs)
- **Plan**: `.gald3r/PLAN.md`
- **Project context**: `.gald3r/PROJECT.md`
- **Constraints**: `.gald3r/CONSTRAINTS.md`
- **Cross-project linking**: `.gald3r/linking/INBOX.md` + `.gald3r/linking/sent_orders/` (outbound order ledger) + `.gald3r/linking/pending_orders/` (staged orders) + `.gald3r/linking/peers/`
- **Incoming specs**: `.gald3r/specifications_collection/` (PRDs, wireframes, contracts from stakeholders)

Task status claims: `[📝]` / `speccing` is an active spec-authoring claim with `spec_owner`, `spec_claimed_at`, and `spec_claim_expires_at`; skip non-expired claims, log stale takeovers, promote finished specs to `[📋]`, and cancel failed specs to `[❌]`. `[🕵️]` / `verification-in-progress` is the equivalent review claim for `[🔍]` work.

**Commands** (use `/g-` prefix in Claude Code):
- `/g-status` — project overview
- `/g-task-new` — create a task
- `/g-bug-report` — report a bug
- `/g-medic` — health check and repair
- `/g-code-review` — code review
- `/g-vault-ingest` — ingest or refresh vault knowledge
- `/g-vault-search` — search the file-first vault
- `/g-vault-lint` — lint vault structure and freshness
- `/g-vault-status` — show vault status and recent activity
- `/g-workspace-status` — show Workspace-Control manifest status
- `/g-workspace-validate` — validate Workspace-Control manifest and routing metadata
- `/g-workspace-export --dry-run` — show export plan only; no files are written
- `/g-workspace-sync --dry-run` — show sync plan only; no files are written

See `docs/COMMANDS.md` for the full command list.

## Vault Knowledge System

This template includes a file-first vault designed to work cleanly with Obsidian.

- Default vault path: `.gald3r/vault/`
- Shared override: `vault_location` in `.gald3r/.identity`
- Raw repo mirror override: `repos_location` in `.gald3r/.identity`
- Raw mirrored repos never belong inside the Obsidian-indexed vault
- Curated repo notes belong in `research/github/`

When working with the vault:

- use `g-skl-vault` for ingest and search workflows
- use `g-skl-knowledge-refresh` for lint and freshness workflows
- read `VAULT_SCHEMA.md` before changing vault structure
- rebuild `index.md` and `_index.yaml` after major vault updates

## Parity Model

This project doubles as a live gald3r workspace and a source of installable framework files.

- Preserve self-hosting parity between the live project and the shipped templates
- Treat these as the reusable IDE parity set: `.cursor/`, `.claude/`, `.agent/`, `.codex/`, `.opencode/`, `templates/.cursor/`, `templates/.claude/`, `templates/.agent/`, `templates/.codex/`, `templates/.opencode/`
- Include the install surface in parity reviews: `templates/.gald3r/`, `templates/.gald3r_template/`, `templates/AGENTS.md`, `templates/CLAUDE.md`, `templates/GEMINI.md`, `templates/.gitignore`
- Reusable framework changes must stay bidirectionally aligned between root and `templates/`
- Keep root and template trees as independent real copies, never junctions or symlinks
- Defer parity automation until the canonical tree is stable; enforce parity manually during the rebuild

---

## Enforcement Rules (All IDEs)

### Stub/TODO Lifecycle (Zero Tolerance)
When writing any stub, placeholder, or TODO comment — **immediately**:
1. Format as `TODO[TASK-{original_id}→TASK-{follow_up_id}]: {description} — fix in follow-up task`
2. Create the follow-up task via `/g-task-new` before moving to the next line
Bare `# TODO` or `pass` stubs that ship without a linked task are violations.

### Bug Discovery (Zero-Ignore Policy)
When you encounter a bug during any coding or review session:
- Bug introduced by **your current task's changes** → fix inline before marking `[🔍]`
- **Pre-existing bug** → create BUG entry via `/g-bug-report`, add `BUG[BUG-{id}]: {desc}` comment at the bug site, note in session summary. Never silently ignore a bug.

### Task Completion Gate
When marking a task `[✅]`: if implementation contains any TODO, stub, `pass`, `NotImplementedError`, or empty catch block — annotate with `TODO[TASK-{original}→TASK-{followup}]: {what is stubbed}` and create a follow-up task before marking complete.

### Code Change Gate
If code files were modified and no task or bug is referenced — create a retroactive task via `/g-task-new` before ending the response.

---

**gald3r version**: 1.2.0
**Supported IDEs**: Cursor, Claude Code, Gemini, Codex, OpenCode
