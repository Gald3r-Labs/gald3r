# Claude Code — gald3r System Instructions

@AGENTS.md

---

## Claude Code-Specific gald3r Guidance

### Command Prefix
Use `/g-` for all gald3r commands. See `docs/COMMANDS.md` for the full reference.

| Command | Description |
|---------|-------------|
| `/g-setup` | Initialize gald3r in this project |
| `/g-status` | Project status overview |
| `/g-task-new` | Create a new task |
| `/g-task-update` | Update task status |
| `/g-task-sync-check` | Validate task sync |
| `/g-workflow` | Task expansion and sprint planning |
| `/g-bug-report` | Report a bug |
| `/g-bug-fix` | Document a bug fix |
| `/g-qa` | Quality assurance activation |
| `/g-code-review` | Comprehensive code review |
| `/g-plan` | Create or update project plan |
| `/g-go` | Work through the task backlog autonomously |
| `/g-git-commit` | Structured git commit |
| `/g-idea-capture` | Capture an idea |
| `/g-idea-review` | Review and promote ideas |
| `/g-medic` | Health check and repair `.gald3r/` |
| `/g-swot-review` | SWOT analysis |
| `/g-dependency-graph` | Generate task dependency graph |
| `/g-report` | Project report |
| `/g-goal-update` | Update project goals |
| `/g-release-new` | Create a new release (CREATE) |
| `/g-release-assign` | Assign tasks to a release (ASSIGN) |
| `/g-release-status` | Show release status (STATUS) |
| `/g-release-publish` | Publish ROADMAP.md (PUBLISH) |
| `/g-release-accelerate` | Accelerate a release with cascade shift (ACCELERATE) |
| `/g-vault-ingest` | Ingest or refresh vault knowledge |
| `/g-vault-search` | Search the file-first vault |
| `/g-vault-lint` | Lint vault structure and freshness |
| `/g-vault-status` | Show vault status and recent activity |

### Agents
Invoke specialized agents with `@agent-name` syntax:

| Agent | Purpose |
|-------|---------|
| `@g-agnt-task-manager` | Task lifecycle — create, update, complete |
| `@g-agnt-project` | PRD writing, planning, PROJECT.md, CONSTRAINTS.md |
| `@g-agnt-qa-engineer` | Bug tracking and quality assurance |
| `@g-agnt-code-reviewer` | Code quality and security review |
| `@g-agnt-infrastructure` | File organization, scope boundaries, SUBSYSTEMS.md |
| `@g-agnt-ideas-goals` | Idea capture, IDEA_BOARD.md, goal management |
| `@g-agnt-verifier` | Verify completed task work |
| `@g-agnt-project-initializer` | First-time gald3r project setup |

### Rules
Rules live in `.claude/rules/g-rl-*.md` and load at every session. Do not edit them unless updating the gald3r system itself.

### Skills
Skills are in `.claude/skills/g-skl-*/SKILL.md`. They load when you invoke a command or when Claude determines they're relevant. All core gald3r skills are present, including `g-skl-workspace` for manifest-backed Workspace-Control status, validation, and per-repo git/worktree boundary reporting.

### Vault
The gald3r vault is file-first and Obsidian-compatible.

- Default vault path: `.gald3r/vault/`
- Shared override: `vault_location` in `.gald3r/.identity`
- Raw repo mirror override: `repos_location` in `.gald3r/.identity`
- Raw mirrored repos stay outside the indexed vault
- Curated repo notes belong in `research/github/`

Use `g-skl-vault` for ingest/search and `g-skl-knowledge-refresh` for lint/freshness. Read `VAULT_SCHEMA.md` before structural vault edits.

### Hooks
Claude Code hooks live in `.claude/hooks/`. They fire on session start, agent complete, and before shell execution. Session start injects `.gald3r/` context and `GUARDRAILS.md`.

### Multi-Agent Sessions
When multiple agents are working simultaneously:
- Skip tasks marked `[🔄]` (in-progress) — they are claimed
- `[🔄]` older than **2 hours** without a `status_changed` update is stale and available for pickup
- Always write `status_changed` timestamp to the task file when claiming a task

### Rate Limit Graceful Shutdown
At ~85% daily rate limit, stop accepting new tasks and produce a handoff report:
```
## Shutdown — Rate Limit Approaching
### Completed This Session: [tasks]
### Left In-Progress: [task ID, what was done, what remains]
### Files Modified: [list]
### Git Status: [committed/uncommitted]
```
