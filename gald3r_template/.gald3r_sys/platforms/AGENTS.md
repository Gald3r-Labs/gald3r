# agents.md - {project_name}

> This file follows the agents.md format for AI agent instructions.
> Compatible with Cursor (`.cursor/`), Claude Code (`.claude/`), Gemini (`.agent/`), Codex (`.codex/`), and OpenCode (`.opencode/`).
> Run `@g-setup` to initialize gald3r and auto-fill the placeholders below.

---

## Project Overview

**{project_name}** — {one sentence description of what this project does and who it's for}

**Tech Stack**: {e.g. Python / FastAPI / PostgreSQL}

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
├── linking/             # Cross-project coordination
│   ├── INBOX.md         # Incoming requests/broadcasts/syncs
│   ├── sent_orders/     # Outbound order ledger (order_*.md per dispatched task)
│   ├── pending_orders/  # Staged orders not yet delivered
│   └── peers/           # Peer capability snapshots
└── specifications_collection/  # Incoming specs, PRDs, wireframes from stakeholders

.cursor/                 # Cursor IDE configuration
├── agents/              # gald3r system agents (g-agnt-*)
├── skills/              # Skills (g-skl-*)
├── commands/            # @g-* commands
├── hooks/               # PowerShell automation hooks
└── rules/               # Always-apply rules (g-rl-*)

.claude/                 # Claude Code (same content as .cursor/)
.agent/                  # Gemini / Antigravity
.codex/                  # Codex
.opencode/               # OpenCode
```

---

## gald3r System Agents

| Agent | Description |
|-------|-------------|
| `g-agnt-task-manager` | Task lifecycle — create, update, track |
| `g-agnt-project` | Project init, grooming, planning, PRDs |
| `g-agnt-qa-engineer` | Bug tracking and quality assurance |
| `g-agnt-code-reviewer` | Code quality and security review |
| `g-agnt-infrastructure` | File organization, scope boundaries |
| `g-agnt-ideas-goals` | Idea capture and goal management |
| `g-agnt-verifier` | Verify completed task work |
| `g-agnt-project-initializer` | First-time project scaffolding |
| `g-agnt-pcac-coordinator` | Cross-project coordination — topology, inbox, broadcast, sync |

---

## Available Commands

Commands use `@g-` in Cursor, `/g-` in Claude Code.

### Core gald3r Commands

| Command | Description |
|---------|-------------|
| `g-setup` | Initialize gald3r in a project |
| `g-status` | Project status overview |
| `g-subsystems` | Subsystem registry sync check, add, update Activity Log |
| `g-task-new` | Create a new task |
| `g-task-update` | Update task status |
| `g-task-sync-check` | Validate task synchronization |
| `g-bug-report` | Report a bug |
| `g-bug-fix` | Document a bug fix |
| `g-code-review` | Code review (security, quality, performance) |
| `g-plan` | Create or update the project plan |
| `g-idea-capture` | Capture an idea to IDEA_BOARD.md |
| `g-idea-review` | Review and promote ideas |
| `g-medic` | Health check, repair, or upgrade `.gald3r/` |
| `g-dependency-graph` | Generate task and/or subsystem dependency graphs (`--tasks`, `--subsystems`, `--all`) |
| `g-subsystem-graph` | Generate subsystem dependency graph (alias: `@g-dependency-graph --subsystems`) |
| `g-git-commit` | Create structured commit messages |
| `g-go` | Run autonomously through the backlog (self-review mode — both phases) |
| `g-go-code` | Implementation-only run — marks tasks `[🔍]`, never `[✅]` |
| `g-go-review` | Verification-only run — run in a **new agent session** from the coder |
| `g-harvest` | Harvest improvements from external sources |
| `g-vault-ingest` | Ingest or refresh vault knowledge |
| `g-vault-search` | Search the file-first vault |
| `g-vault-lint` | Lint vault structure and freshness |
| `g-vault-status` | Show vault status and recent activity |

### Cross-project coordination

| Command | Description |
|---------|-------------|
| `g-pcac-adopt` | Register a project as a **child** of this project (bidirectional topology update) |
| `g-pcac-ask` | Send a request to the parent project |
| `g-pcac-claim` | Register a project as the **parent** of this project (bidirectional topology update) |
| `g-pcac-move` | Transfer files/folders to another project in the topology |
| `g-pcac-order` | Push a task to child projects (with configurable cascade depth) |
| `g-pcac-read` | Review and action the cross-project INBOX (CONFLICTs first) |
| `g-pcac-status` | Show topology role, open INBOX items, linked project health |
| `g-pcac-sync` | Initiate or respond to sibling contract sync (advisory) |
| `g-workspace-status` | Show Workspace-Control manifest status, including per-repo git/worktree boundaries |
| `g-workspace-validate` | Validate Workspace-Control manifest, routing metadata, and independent git-root boundaries |
| `g-workspace-export` | Show Workspace-Control export dry-run plan with per-member git/worktree preflight |
| `g-workspace-sync` | Show Workspace-Control sync dry-run plan with per-member git/worktree context |

See `docs/COMMANDS.md` for the full list.

---

## Task Management

PCAC inbox conflicts gate task claiming, implementation, verification, planning, status work, and swarm partitioning; commands rerun `g-hk-pcac-inbox-check.ps1 -BlockOnConflict` before work and swarm coordinators rerun it every 30 minutes plus before final summaries. `g-medic` L1 is the exception: it runs a non-blocking inbox check, records conflict severity in health scoring, then stops before L2-L4 or any claim/implementation/review/planning work.


### Task Status Indicators

Speccing claims use `spec_owner`, `spec_claimed_at`, and `spec_claim_expires_at`; finished specs promote `[📝] -> [📋]`, failed spec attempts move `[📝] -> [❌]`, and stale takeovers require Status History logging.


| TASKS.md | YAML status | Meaning |
|---------|-------------|---------|
| `[ ]` | (no file yet) | Pending — not started |
| `[📝]` | `speccing` | Spec claim active; skip non-expired claims (TTL: 1 hour) |
| `[📋]` | `pending` | Spec written, ready to start |
| `[🔄]` | `in-progress` | Being worked on (TTL: 2 hours) |
| `[🔍]` | `awaiting-verification` | Done, needs review |
| `[🕵️]` | `verification-in-progress` | Review claim active; skip non-expired claims |
| `[✅]` | `completed` | Done |
| `[❌]` | `failed` | Failed or cancelled |

### Direct Edit Policy

Edit these files directly without asking for permission:

- `.gald3r/TASKS.md` — task checklist
- `.gald3r/BUGS.md` — bug index
- `.gald3r/PLAN.md` — project plan
- `.gald3r/PROJECT.md` — project identity
- All files in `.gald3r/tasks/`, `.gald3r/bugs/`, `.gald3r/features/`

---

## Vault Knowledge System

This template includes a file-first vault designed for Obsidian compatibility.

- Primary path: `.gald3r/vault/`
- Optional shared override: `vault_location` in `.gald3r/.identity`
- Optional raw repo mirror override: `repos_location` in `.gald3r/.identity`
- Fallback behavior: if shared vault writes fail, write locally and log the event
- Raw GitHub repo mirrors belong in `repos_location`, not inside the Obsidian-indexed vault

Vault operations should use `g-skl-vault` and `g-skl-knowledge-refresh`.

- Read `VAULT_SCHEMA.md` before making structural vault changes
- Use `[[wikilinks]]` for durable internal references
- Keep curated repo notes in `research/github/`
- Rebuild `index.md` and `_index.yaml` after major vault updates

---

## Parity Model

This project is both a live gald3r workspace and a source of installable framework files.

- Reusable framework content must preserve self-hosting parity between the live project and the shipped templates
- The parity target set is 10 IDE trees: `.cursor/`, `.claude/`, `.agent/`, `.codex/`, `.opencode/`, `templates/.cursor/`, `templates/.claude/`, `templates/.agent/`, `templates/.codex/`, `templates/.opencode/`
- Template install files also belong to the parity surface: `templates/.gald3r/`, `templates/.gald3r_template/`, `templates/AGENTS.md`, `templates/CLAUDE.md`, `templates/GEMINI.md`, `templates/.gitignore`
- Reusable changes flow both directions between root and `templates/`; local or proprietary workspace content stays out of `templates/`
- Root and template IDE trees must remain independent real copies, never symlinks or junctions
- Automated parity propagation is deferred until the canonical tree stabilizes; during the rebuild, parity is enforced manually

---

## Security

- Never commit API keys, tokens, or passwords
- Use environment variables for secrets (`.env`, never committed)
- Always use parameterized queries for database access
- Validate all user input

---

## gald3r Version

**gald3r version**: 1.2.0
**Supported IDEs**: Cursor, Claude Code, Gemini, Codex, OpenCode

---

## Enforcement Rules (All IDEs — including Codex)

These rules apply in every session, on every response. Codex enforces these via this AGENTS.md since it has no native rules folder.

### Error Reporting (Zero Tolerance)
If any response mentions "error", "warning", "lint error", "exception", or "pre-existing" — create a `.gald3r/BUGS.md` entry immediately. There are no exemptions. Pre-existing errors must still be logged.

### Task Completion Gate
When marking a task `[✅]` completed: if the implementation contains any TODO, stub, `pass`, `NotImplementedError`, hardcoded mock data, or empty catch block — you MUST:
1. Annotate with `TODO[TASK-{original}→TASK-{followup}]: {what is stubbed}`
2. Create a follow-up task before marking complete

### Stub/TODO Lifecycle (Zero Tolerance)
When writing any stub, placeholder, or TODO comment — **immediately**:
1. Format as `TODO[TASK-{original_id}→TASK-{follow_up_id}]: {description} — fix in follow-up task`
2. Create the follow-up task via `g-task-new` before moving to the next line
Bare `# TODO` or `pass` stubs that ship without a linked task are violations of `g-rl-34`.

### Bug Discovery (Zero-Ignore Policy)
When you encounter a bug during any coding or review session:
- Bug was introduced by **your current task's changes** → fix it inline before marking `[🔍]`
- Bug is **pre-existing** → create a BUG entry via `g-skl-bugs` REPORT, add `BUG[BUG-{id}]: {desc}` comment at the bug site, note it in the session summary. Never silently ignore a bug.
See `g-rl-35-bug-discovery-gate.mdc` for full decision tree and format examples.

### Code Change Gate
If code files were modified and no task or bug is referenced — create a retroactive task via `g-task-new` before ending the response. Exceptions: `.gald3r/` housekeeping, docs-only changes, git operations.

### Session Start Sync (v3)
At session start, display:
```
📌 SESSION CONTEXT
Mission: [from PROJECT.md]
Plan focus: [current milestone from PLAN.md]
Active tasks: [in-progress count from TASKS.md]
```

Read `.gald3r/CONSTRAINTS.md` — load all constraints into active context. Constraints cannot be silently overridden.

### Commit Offer
After completing any task, always offer a git commit before ending the response.

### .gald3r/ Folder Gate
Never read or write `.gald3r/` files without following the appropriate skill workflow. Use `g-skl-tasks` for task operations, `g-skl-qa` for bugs, `g-skl-plan` for planning files.

### Documentation Placement
All `.md` documentation files go in `docs/` — never in the project root. Exceptions: `AGENTS.md`, `README.md`, `LICENSE`, `CLAUDE.md`, `CHANGELOG.md`, `GEMINI.md`, `GUARDRAILS.md`.

### PowerShell (Windows)
- Use `;` as command separator (NOT `&&`)
- Use `curl.exe` or `Invoke-WebRequest`, never bare `curl`
- Use `uv` for Python virtual environments, never bare `pip` or `python -m venv`

