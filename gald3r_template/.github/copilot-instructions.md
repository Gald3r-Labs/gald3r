<!--
  .github/copilot-instructions.md — AUTO-GENERATED, DO NOT EDIT MANUALLY
  
  Generated from: .gald3r_sys always-apply rules
  Generator:      scripts/generate_copilot_instructions.ps1
  Generated at:   {run generate_copilot_instructions.ps1 to update}

  This file carries gald3r always-apply rules into GitHub Copilot sessions.
  Regenerate after modifying rules: .\scripts\generate_copilot_instructions.ps1

  gald3r — AI Development System for Cursor, Claude Code, Gemini, Codex, OpenCode, and GitHub Copilot
  Supported IDEs: Cursor (.cursor/), Claude Code (.claude/), Gemini (.agent/),
                  Codex (.codex/), OpenCode (.opencode/), GitHub Copilot (.copilot/)
-->

# gald3r System Instructions for GitHub Copilot

The following rules apply to every Copilot session in this repository.
They are automatically concatenated from gald3r's always-apply rule files.

---
<!-- Rule: g-rl-00-always.mdc -->
1. Include in the final line(s) on every response to the user:
   * Current timestamp with date, hour, and minutes (e.g., "2026-02-01 09:45 UTC")
   * List of tools used during the call
   * Context usage percentage (ALWAYS show, even if low)
   * Context breakdown showing:
     - Rules context: estimated % of context from .cursor/rules/
     - MCP context: estimated % from MCP tool descriptors/schemas
     - Conversation: % from actual conversation history
     - Skills/Other: % from skills, agents, and other sources

   Example format:
   ```
   ---
   2026-02-01 09:45 UTC
   Model: Claude Opus 4, Tokens: ~12,500 input / ~800 output, Est. Cost: ~$0.16
   Context: 45% used (Rules: ~15%, MCP: ~8%, Conversation: ~18%, Skills/Other: ~4%)
   Tools: Shell, Read, StrReplace
   ---
   ```

2. if any particular file in the code base exceeds 1500 lines of code...
 * begin asking the user if they would like to refactor the code to keep the file sizes smaller
 * become more insistant with every 100 lines added thereafter
 * become very insistant on refactoring once a file has hit 1700 lines

3. check your MCP tool lists, you seem to forget you have a lot of tools


4. When working with Python Project, please use the UV for virtual environment management

5. Your training data is 1-3 years old. For time-sensitive queries (versions, pricing, APIs, best practices), **research before answering** using WebSearch or WebFetch. Use today's date from system context, NOT training cutoff.

6. **Shell Context (Session Start) — OS + Shell Probe**. Before issuing ANY shell command, determine the host OS and target shell. This is a **session-start, one-shot probe** (a single env-var read or one `uname` call — not a multi-step diagnostic) intended to eliminate the bash-vs-PowerShell token-waste loop documented in BUG-031 / T1144.

   **Probe (pick the cheapest signal already available):**
   * `$env:OS` contains `"Windows"` **or** `$IsWindows -eq $true` (PowerShell 7+) → **PowerShell route**
   * `uname -s` returns `Linux` / `Darwin` **or** `$BASH_VERSION` is set → **bash/zsh route**
   * If the harness already tells you (e.g. system context says `Shell: PowerShell` or `Shell: Bash`), trust that — do not re-probe.

   **Never mix syntax inside a single tool call.** The interpreter is selected by the tool, not the snippet — `Bash(...)` will parse PowerShell syntax as bash and error. Concrete differences:

   | Concept | PowerShell | Bash / zsh |
   |---|---|---|
   | Array literal | `@("a","b","c")` | `("a" "b" "c")` or `arr=(a b c)` |
   | Statement separator | `;` (sequential); `&&` requires PS 7+ | `&&` (short-circuit), `;` (sequential) |
   | Env var read | `$env:VAR` | `$VAR` / `${VAR}` |
   | Path separator | `\` (forward `/` also accepted on Windows) | `/` |
   | File-exists test | `Test-Path $p` | `[ -f "$p" ]` / `[ -e "$p" ]` |
   | Pipeline filter | `Where-Object { ... }` | `grep` / `awk` / `xargs` |
   | Subshell / cmd substitution | `$(...)` (expression eval) | `$(...)` (command output) |

   **Default routing on Cursor/Claude Code on Windows**: assume PowerShell unless the terminal explicitly shows a bash/zsh prompt. When the harness exposes both a `Bash` and a `PowerShell` tool, route by **host OS**, not by tool-name preference.

   **Regression canonical example** — this is the exact construct that triggered T1144 (a PowerShell `@(...)` array piped through `Where-Object` to find a hook file, executed inside a `Bash` tool call):
   ```powershell
   $hook = @( ".cursor\hooks\g-hk-pcac-inbox-check.ps1", ".claude\hooks\g-hk-pcac-inbox-check.ps1" ) | Where-Object { Test-Path $_ } | Select-Object -First 1
   ```
   Bash rejects `@(` with `syntax error near unexpected token '('`. That error is a **tool-routing failure**, not a real PCAC conflict or hook-missing condition — re-route the same snippet through PowerShell and it succeeds. Do not enter an error-driven retry loop; switch tools.

---

<!-- Rule: g-rl-01-documentation.mdc -->
# Documentation Standards

## CRITICAL: No .md Files in Project Root

**All documentation files MUST go in `docs/` folder, NOT in project root.**

### Naming Convention

**Format:** `YYYYMMDD_HHMMSS_IDE_TOPIC_NAME.md`

**Example for Cursor:**
```
✅ docs/20251019_173407_Cursor_CODE_REVIEW_ANALYSIS.md
✅ docs/20251019_143022_Cursor_FEATURE_PLANNING.md
✅ docs/20251020_094523_Cursor_DATABASE_DESIGN.md

❌ CODE_REVIEW_ANALYSIS.md  (wrong location)
❌ docs/code-review.md  (missing timestamp and IDE)
```

### Components

- `YYYYMMDD` - Date
- `HHMMSS` - Time (24-hour)
- `IDE` - **Cursor** (for files you create)
- `TOPIC_NAME` - UPPERCASE_WITH_UNDERSCORES

### Get Timestamp (PowerShell)

```powershell
$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
# Creates: 20251019_173407
```

## Allowed Root Files (Exceptions)

**ONLY these files can be in root:**
- `AGENTS.md`
- `README.md`
- `LICENSE`
- `CLAUDE.md`
- `CHANGELOG.md`
- `ROADMAP.md` ← machine-generated by `@g-release-publish`; standard OSS convention

**Everything else → `docs/` folder**

## Benefits

1. ✅ Automatic chronological sorting
2. ✅ Cursor IDE
3. ✅ Clean root directory
4. ✅ Easy to find latest docs

## Before Creating .md File

1. Is it AGENTS.md, README.md, LICENSE, CLAUDE.md, CHANGELOG.md, or ROADMAP.md? → Root is OK
2. Anything else? → **MUST** go in `docs/`
3. Use format: `docs/YYYYMMDD_HHMMSS_Cursor_TOPIC.md`

---

**Always follow this convention!**

---

<!-- Rule: g-rl-02-git_workflow.mdc -->
# Git Workflow

## Commit Message Format
```
{type}({scope}): {brief description}

{optional body}

Task: #{id}
Phase: {N}
```

## Commit Types
| Type | Use For |
|---|---|
| `feat` | New feature or task |
| `fix` | Bug fix |
| `refactor` | Code refactor, no behavior change |
| `docs` | Documentation only |
| `test` | Tests only |
| `chore` | Config, build, maintenance |
| `phase` | Phase completion commit |

## Rules
- Subject line ≤ 72 characters
- Use imperative mood: "add" not "added" or "adds"
- Reference task ID in every task-related commit
- Never commit secrets, API keys, or passwords
- Run `git status` before committing to verify staged files

## Protected Files (NEVER commit these)

Before every `git add` or `git commit`, verify NONE of these are staged:

| Pattern | Why |
|---|---|
| `/.agent/` | Personal IDE config (gitignored) |
| `/.claude/` | Personal IDE config (gitignored) |
| `/.codex/` | Personal IDE config (gitignored) |
| `/.cursor/` | Personal IDE config (gitignored) |
| `/.opencode/` | Personal IDE config (gitignored) |
| `/.gald3r/` | Live project state (gitignored) |
| `/.gald3r_template/` | Root-level template copy (gitignored) |
| `/temp_docs/` | Scratch files (gitignored) |
| `/temp_scripts/` | Scratch files (gitignored) |
| `/AGENTS.md` | Personalized per-user (gitignored) |
| `/CLAUDE.md` | Personalized per-user (gitignored) |
| `/GEMINI.md` | Personalized per-user (gitignored) |
| `/GUARDRAILS.md` | Personalized per-user (gitignored) |
| `/.env` | Secrets (gitignored) |
| `/.mcp.json` | Machine-specific MCP config (gitignored) |

If `git status` shows ANY of these as staged or untracked-to-be-added:
1. **STOP** — do not commit
2. Remove from staging: `git reset HEAD <file>`
3. Verify `.gitignore` still contains the entry
4. Warn the user that a protected file was almost committed

## Branch Naming
- Feature: `feature/{task-id}-brief-description`
- Bug fix: `fix/{bug-id}-brief-description`
- Release: `release/v{major}.{minor}.{patch}`
- Gald3r agent worktree: `gald3r/{task_id}/{role}/{repo_slug}/{owner}-{suffix}`

## Worktree Isolation

Use `scripts/gald3r_worktree.ps1` as the shared primitive for agent-owned worktrees in the gald3r source repo. Installed templates also include the same helper in the `g-skl-git-commit/scripts/` skill directory for each IDE target.

- Default root: `$env:GALD3R_WORKTREE_ROOT`, or `<repo-parent>/.gald3r-worktrees/<repo-name>` when unset.
- Never create worktrees inside the active repository checkout.
- `Create` blocks on a dirty active checkout unless an explicit `-AllowDirty` override is used after recording ownership.
- For `g-go*`, `g-go-code*`, `g-go-review*`, and `--swarm` flows, follow `g-rl-33` **Clean Controller Gate** and **Pre-Reconciliation Clean Gate** on the **computed touch set** of git roots (orchestration + manifest members from `workspace_repos:` and v2 expansions per `g-rl-33`) before claims, worktrees, and coordinator shared writes; do not use `-AllowDirty` there except with documented task/bug ownership in `## Status History` **per root** that policy allows.
- Task claims created from worktrees should record `worktree_path`, `worktree_branch`, `worktree_created_at`, and `worktree_owner`.
- Cleanup is report-only unless `-Apply` is provided and may remove only directories with `.gald3r-worktree.json` ownership metadata.

## Windows (PowerShell)
```powershell
$msg = "feat(api): implement auth`n`nTask: #103`nPhase: 1"
git commit -m $msg
```

## Pre-Commit Sanity Check

Before every commit, run or rely on the **pre-commit sanity check** defined in `g-skl-git-commit` (PRE-COMMIT CHECKLIST section) and `@g-git-sanity` command:

| Severity | Check | Action |
|----------|-------|--------|
| BLOCK | Secrets / API keys in staged diff | Fix before committing |
| BLOCK | `.env` file staged with values | Fix before committing |
| WARN | Staged files > 5 MB | Use Git LFS or .gitignore |
| WARN | `.gald3r/TASKS.md` / `tasks/` sync drift | Run `@g-task-sync-check` |

### Optional Automation (opt-in hook)

```powershell
# Enable hook-based pre-commit checks
git config core.hooksPath .cursor/hooks

# Disable
git config --unset core.hooksPath
```

Hook file: `.cursor/hooks/g-hk-pre-commit.ps1`

## Pre-Push Gate (regular vs release)

Before `git push`, run **`.gald3r_sys/skills/g-skl-git-commit/scripts/gald3r_push_gate.ps1`** or `@g-git-push`:

| Mode | Trigger | CHANGELOG / docs |
|------|---------|------------------|
| **regular** | Default; interactive **N**; hook without `GALD3R_RELEASE_PUSH` | No changelog requirement — status and unpushed summary only (**never blocks**) |
| **release** | `-Release`; or `GALD3R_RELEASE_PUSH=1`; interactive **Y** | **Versioned** `## [x.y.z]` heading must exist in `CHANGELOG.md` (Keep a Changelog — not only `## [Unreleased]`). Override: `GALD3R_PUSH_GATE_OVERRIDE=1` |

Release mode also reminds you to re-read **README.md** and prints **version** lines from `pyproject.toml` / `package.json` if present (`g-rl-26`).

Shared scripts: `.gald3r_sys/skills/g-skl-git-commit/scripts/gald3r_push_gate.ps1`; `.gald3r_sys/skills/g-skl-git-commit/scripts/gald3r_git_sanity_common.ps1` (secret patterns for `g-hk-pre-commit.ps1`).

### Optional pre-push hook

Same opt-in `core.hooksPath` as pre-commit. Hook: `.cursor/hooks/g-hk-pre-push.ps1` — in hook mode, **release** checks run only when `GALD3R_RELEASE_PUSH=1`.

---

<!-- Rule: g-rl-04-code_reusability.mdc -->
# Code Reusability (DRY Enforcement)

## 3-Strike Rule
If logic appears **3+ times**, it MUST be extracted to a shared module. No exceptions.

## Before Writing New Code
1. Does a shared module already exist for this? → Use it
2. Can this be generalized for reuse? → Put it in `lib/` or `shared/`
3. Am I duplicating logic from another file? → Extract first

## Folder Conventions
| Category | Location |
|---|---|
| Utilities | `lib/utils/` or `src/lib/utils/` |
| Services | `lib/services/` or `src/lib/services/` |
| Types/DTOs | `lib/types/` or `src/lib/types/` |
| Config/Constants | `lib/config/` or `src/lib/config/` |
| Shared UI | `components/shared/` or `lib/components/` |
| Hooks | `lib/hooks/` or `src/lib/hooks/` |

Use barrel exports (`index.ts` / `__init__.py`) for clean imports.

## Anti-Patterns to Flag
- Copy-pasted logic across files → extract immediately
- Inline utility functions → move to `lib/utils/`
- Hardcoded values repeated → extract to `lib/config/constants`
- Fat classes/components mixing concerns → decompose
- Re-implementing stdlib functionality → use the standard library

## Self-Check (Every Response That Writes Code)
> Did I introduce duplicated code that should be a shared module?
> → If yes: extract to `lib/` or `shared/` before completing.

---

<!-- Rule: g-rl-08-powershell.mdc -->
# PowerShell on Windows 10/11

## Critical Rules
- Use `;` as command separator (NOT `&&`)
- `curl` is aliased to `Invoke-WebRequest` — use `curl.exe` or `Invoke-WebRequest -Uri "URL" -UseBasicParsing`
- NEVER use multi-line `python -c` commands — they cause parsing errors
- Set UTF-8 before Python: `$OutputEncoding = [Console]::OutputEncoding = [Text.Encoding]::UTF8`
- Run Flask/web servers as background tasks to avoid hanging
- Get UTC time: `powershell -Command "(Get-Date).ToUniversalTime().ToString('yyyy-MM-ddTHH:mm:ssZ')"`

## HTTP Requests
```powershell
# Use these (NOT bare curl):
curl.exe -s http://localhost:5000/api/status
Invoke-WebRequest -Uri "http://localhost:5000/api/status" -UseBasicParsing
```

## curl Flag → PowerShell Mapping
| curl | PowerShell |
|------|-----------|
| `-s` | `-UseBasicParsing` |
| `-o file` | `-OutFile "file"` |
| `-X POST` | `-Method POST` |
| `-H "K: V"` | `-Headers @{"K"="V"}` |
| `-d "data"` | `-Body "data"` |

## Python Execution
```powershell
# Single-line only:
python -c "import sys; print(sys.version)"

# For multi-line, use a script file or pipe:
$pythonCode = @"
from some_module import something
print(something())
"@
$pythonCode | python
```

## If Commands Hang or Parse Errors Occur
1. Stop — don't retry the same command
2. Reset encoding (UTF-8 commands above)
3. Use `cmd /c "python script.py"` as fallback
4. Redirect output to file: `python script.py > output.log 2>&1; Get-Content output.log`

---

<!-- Rule: g-rl-09-python_venv.mdc -->
# Python Virtual Environment (UV)

**CRITICAL**: Use UV, never `pip install` or `python -m venv` directly.

## Core Commands
```bash
uv venv                           # Create .venv/
uv pip install <package>          # Install
uv pip install -r requirements.txt
uv run python script.py           # Run in UV env
uv pip freeze > requirements.txt  # Save packages

# Activate (Windows)
.venv\Scripts\activate
# Activate (Unix/Mac)
source .venv/bin/activate
```

## Dependency Sync (MANDATORY)
`requirements.txt` AND `pyproject.toml` must ALWAYS match.
When adding a package: install → freeze → update pyproject.toml → commit both.

```toml
[project]
dependencies = ["package==version"]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"
```

## Code Standards
- Line length: 88-100 chars (black)
- Type hints on all new public functions
- Docstrings: Google style
- No bare `except:` — always catch specific exceptions

---

<!-- Rule: g-rl-25-gald3r_session_start.mdc -->
# Session Start Protocol

## .gald3r/ Folder Layout (v3)

**SLIM layout** (gald3r base — what g-skl-setup creates):
```
.gald3r/
├── .identity             # project_id, project_name, user_id, user_name, gald3r_version, vault_location
├── .gitignore
├── TASKS.md, PLAN.md, PROJECT.md, CONSTRAINTS.md, BUGS.md, SUBSYSTEMS.md, IDEA_BOARD.md, FEATURES.md
├── features/       # Individual PRD files
├── bugs/       # Individual bug detail files (optional; index in BUGS.md)
├── reports/
├── logs/
├── subsystems/ # Per-subsystem spec files (subsystem_name.md)
├── specifications_collection/  # Incoming specs, PRDs, wireframes from stakeholders (README.md index)
└── tasks/      # Individual task files (sequential task IDs)
```

**FULL layout additions** (gald3r_dev only — do NOT create in slim projects):
```
├── config/      # HEARTBEAT.md, SPRINT.md, AGENT_CONFIG.md
├── experiments/ # EXPERIMENTS.md, SELF_EVOLUTION.md, HYPOTHESIS.md, EXP-NNN.md
├── linking/     # README.md, INBOX.md — cross-project coordination
│   ├── sent_orders/    # Outbound order ledger (order_*.md per dispatched task — see g-skl-pcac-order)
│   ├── pending_orders/ # Staged orders not yet delivered (target inaccessible)
│   └── peers/          # Peer capability snapshots
├── vault/       # encrypted/sensitive context
└── phases/      # Legacy v2 only — phase defs / archives
```

## Display at Session Start (when .gald3r/ exists)
```
📌 SESSION CONTEXT
Mission: [from PROJECT.md, 1 line]
Goals: G-01: [name] | G-02: [name] (from PROJECT.md)
Plan focus: [current milestone or theme from PLAN.md]
Ideas: [N] active (from IDEA_BOARD.md)
Subsystems: [N] registered (from SUBSYSTEMS.md + subsystems/)
Specs: [N] in specifications_collection/ (newest: YYYY-MM-DD) [or "none"]
⚠️ Unreviewed: {spec_filename}  ← only if spec mtime > date of last [✅] task
🧠 Learned Facts: [N] project facts | [M] global facts  (run /g-learn review to see them)
Experiments: [summary from experiments/EXPERIMENTS.md if it has active entries]
🛡️ Constraints: [N] active — run @g-constraint-check before completing any task
⚠️ Release sync: N CHANGELOG version(s) missing release file — run @g-release-sync  ← only show when gap count > 0
```

Learned fact counts: count `-` bullet points in `.gald3r/learned-facts.md` (skip headers and empties).
Global fact count: count bullets in `{vault_location}/projects/{project_name}/memory.md` if it exists.

## Subsystem Awareness (MANDATORY)
At session start, read `.gald3r/SUBSYSTEMS.md` for the registry and interconnection graph.
For any subsystem you're about to modify, read its spec file at `.gald3r/subsystems/{name}.md`.
This prevents architectural drift and ensures changes respect subsystem boundaries.

## Sync Validation (Run When User Mentions Tasks/Phases/Status)

**Step 0: Constraints Load**
- Read `.gald3r/CONSTRAINTS.md`
- Count active constraints from the `## Constraint Index` table (Status = active)
- **Expiry check**: for each active constraint with expiry fields (`**Expires at**:`, `**Resolved when task**:`, `**Resolved when feature**:`), evaluate conditions. If any constraints expired since last session: `⏰ N constraint(s) auto-expired: C-{ids}`. Run the CHECK expiry evaluation from `g-skl-constraints` to auto-archive expired constraints.
- Display the LIST output from `g-skl-constraints` (compact one-liner per constraint)
- If any constraint definition block is missing the `**Enforcement**:` field → flag: `⚠️ C-{ID} has no enforcement definition`

**Step 1: Goals Check**
- PROJECT.md missing goals content or has `{Goal name}` placeholders → auto-generate from PROJECT.md mission / PLAN.md

**Step 1.5: Version Check** (optional, non-blocking)
- Skip if `disable_version_check: true` in `.gald3r/config/AGENT_CONFIG.md`
- Read `gald3r_version` from `.gald3r/.identity`; attempt a 3-second fetch of the version feed (configured `version_feed_url` or `https://api.github.com/repos/gald3r/gald3r/releases/latest`)
- If fetch succeeds and installed version < latest: `💡 gald3r update available (v{current} → v{latest}) — run @g-update`
- If fetch fails or times out: skip silently (no error, no delay)

**Step 2: Task Sync**
- Compare TASKS.md entries to `.gald3r/tasks/**` (T1025 status subfolders: `open/`, `in-progress/`, `awaiting/`, `completed/YYYY/MM/`, `closed/`; v3 source of truth; sequential task IDs)
- Legacy v2: completed tasks may still be under `.gald3r/phases/phase*/` until migrated
- Phantom = in TASKS.md but no matching `tasks/task{id}_*.md` (and not found in legacy archive if applicable)
- **Re-work Surface**: for each `[📋]`/pending task, check if its `## Status History` table has a FAIL row as the last entry (a row where the `To` column is `pending` and `Message` starts with `FAIL:`). If so, surface:
  ```
  ⚠️ Re-work: Task {id} previously failed verification on {Timestamp}: {Message}
  ```
  This alerts the implementing agent that prior attempts failed and what to watch for.

**Step 2b: Release Sync Check** (C-023)
- Read `CHANGELOG.md`, count all `## [x.x.x]` version headers (skip `## [Unreleased]`)
- For each, check if `.gald3r/releases/` has a file whose name contains the version (e.g., `v1-5-0` for `[1.5.0]`)
- Gap count > 0 → surface: `⚠️ N CHANGELOG version(s) missing release file — run @g-release-sync`
- Gap count == 0 → display: `✅ CHANGELOG/releases in sync`

**Step 3: Plan / PRD / Legacy Phase Sync**
- Verify `.gald3r/PLAN.md` and `.gald3r/features/` exist for delivery projects
- Legacy v2: if TASKS.md still has phase headers → check `phases/phaseN_*.md` exists until migrated off phases

**Step 4: SUBSYSTEMS.md Staleness**
- Collect `subsystems:` values from task files → compare to SUBSYSTEMS.md
- Missing entries → flag and offer to add stubs in `subsystems/`
- For each subsystem in SUBSYSTEMS.md, verify a spec file exists in `subsystems/`
- Spec files missing `locations:` in frontmatter → flag as incomplete

**Step 5: ACTIVE_BACKLOG.md**
- Older than 26 hours → flag as stale, offer regeneration

**Step 6: Cross-Project INBOX Check** (only when PCAC is configured)

Run this check only when the current project is a PCAC participant. PCAC is active only when `.gald3r/linking/link_topology.md` exists and declares at least one non-empty parent, child, or sibling relationship, or when `.gald3r/PROJECT.md` explicitly declares PCAC project linking relationships. A Workspace-Control manifest and a local `.gald3r/linking/INBOX.md` alone do **not** make a project part of a PCAC group.

When PCAC is active, `g-hk-pcac-inbox-check.ps1` runs this check automatically at session start. Behavior (T168):

- **Per-item display, not just counts** — the hook surfaces each open INBOX item with a one-line summary (type, source project, subject, age in hours/days). Items are grouped by type with subheadings, sorted within each group oldest-first, and truncated at 10 per group with a "+N more" note.

- **Auto-action policy** (T168):
  - `[INFO]` notifications → auto-mark-read (rewritten to `[DONE]` with an `**Auto-actioned:**` stamp). Low risk, no action required.
  - `[SYNC]` items from siblings → auto-mark-read after surfacing. Updating the local peer snapshot is left to `@g-pcac-read` (the hook does not write `linking/peers/`).
  - `[BROADCAST]` from a parent → surface only; user must `@g-pcac-read --ack <id>` to acknowledge.
  - `[REQUEST]` from a child → surface only; user must `@g-pcac-read --accept|--decline <id>` to action.
  - `[ORDER]` from a parent → surface only; user must `@g-pcac-read --accept <id>`. Treated as blocking until accepted.
  - `[CONFLICT]` → preserve existing gate behavior — surface immediately as `⚠️ WARNING` before any other work; agents MUST resolve/defer via `@g-pcac-read` before proceeding. Conflicts gate ALL session work.

- **Audit log** — every auto-action writes a row to `.gald3r/logs/pcac_auto_actions.log`: `{timestamp ISO-8601} | {item_id} | {action}`.

- **Idempotency** — re-running the hook on an already-actioned inbox is a no-op (auto-actioned items already have `[DONE]` status; only `[OPEN]` rows are processed).

- **Auto-mark-read mechanics** — the `[OPEN]` heading is rewritten to `[DONE]` and a `**Auto-actioned:** YYYY-MM-DD by g-hk-pcac-inbox-check` line is appended directly under the heading. Items are NEVER deleted (audit trail). On first run that produces auto-actions, a `## Recently Actioned` section is appended to the bottom of INBOX.md.

- **Skip auto-actions** — pass `-NoAutoAction` to the hook to surface items only without any rewrite.

**Step 6b: Cross-Project Dependency Surface** (if `.gald3r/linking/sent_orders/` exists)

**The sent_orders ledger is the ONLY tracking surface for outbound PCAC (T167)** — no local task should mirror it. Parents/siblings waiting on a child response track the wait via this ledger, never via a "[Waiting]" or "[Broadcast tracker]" task.

- List `.gald3r/linking/sent_orders/order_*.md`
- For each: read frontmatter `status:` field
  - **Awaiting** = count of records where `status` ∈ {`sent`, `acknowledged`, `in-progress`, `blocked`}
  - **Resolved-since-last-session** = count of records where `status: completed` AND the record's most-recent Sync History row timestamp is newer than the previous session boundary (use last `[✅]` task completion date in TASKS.md as a cheap proxy when no explicit session-boundary file is available)
  - **Stale (T167)** = records where `status` ∈ {`sent`, `acknowledged`} AND no Sync History row in the last 30 days. Surface so the user can `@g-pcac-status --close <ord-id>` to formally abandon (writes `status: abandoned` + a final Sync History row). This replaces the "task that never completes" problem.
- Display: `🔗 Cross-project: {N_awaiting} awaiting, {M_resolved} resolved, {S_stale} stale`
  - If `N_awaiting > 0`: also list the awaiting orders compactly:
    ```
       ⏳ ord-{shortid} → {sent_to}: {remote_task_title} ({status}, {days_out}d)
    ```
  - If `M_resolved > 0`: also list:
    ```
       ✅ ord-{shortid} → {sent_to}: {remote_task_title} (resolved {date})
    ```
  - If `S_stale > 0`: also list:
    ```
       ⚠️ ord-{shortid} → {sent_to}: {remote_task_title} (stale {N}d, {status}) — consider @g-pcac-status --close
    ```
- Skip silently when `sent_orders/` is empty or absent.

**Step 7: Cascade Forward Check** (if `.gald3r/PROJECT.md` **Project Linking** section lists children with cascade)
- Scan `.gald3r/tasks/**` (all status subfolders) for any task with `cascade_depth_remaining > 0` AND `cascade_forwarded: false`
- If found: forward cascades to children listed in topology (follow `g-broadcast` skill pattern but using the cascade chain metadata from the task)
- Mark forwarded tasks as `cascade_forwarded: true`
- Report: `Forwarded N cascade task(s) to: [child names]`
- If no children have `cascade_forward: true` or depth is 0: skip silently

**Step 8: Experiment Staleness Check** (if `.gald3r/experiments/EXPERIMENTS.md` exists)
- Read EXPERIMENTS.md for active experiments
- For each active experiment: read EXP file, check if any stage is `[🔄]` for >48h without update
- Stale experiments → flag: `⚠️ EXP-NNN has a running stage with no update for >48h`
- Display active experiment summary: `EXP-NNN (Stage M/N — status)`

**Step 9: Documentation Staleness Check** (if vault is configured and `research/platforms/_index.yaml` exists)
- Read `.gald3r/.identity` → get `vault_location`
- Read `{vault_location}/research/platforms/_index.yaml`
- Count entries where `next_refresh` field is earlier than today's date
- If any stale entries found → display: `📚 N documentation note(s) overdue for refresh — run @g-ingest-docs REFRESH_STALE`
- Skip silently if `_index.yaml` does not exist or vault is not configured

**Step 10: Version Check** (only when MCP backend is reachable)
- Call `gald3r_check_update(project_path=<cwd>, force=false)`
- If result is cached, unreachable, or fails for any reason: skip silently (do not slow down session start)
- If `update_available: true` AND `latestVersion` is NOT in `.gald3r/.update_skips`:
  Display: `🔔 gald3r {latestVersion} available — run @g-upgrade to update`
  (single line only — do not block the session or show full release notes)
- If `update_available: false`: skip silently

**Fix issues BEFORE proceeding with user request.**

## Idea Capture Triggers (IMMEDIATE, any time)
Capture to `IDEA_BOARD.md` when user says:
`"make a note"` | `"remember this"` | `"idea:"` | `"what if we"` | `"someday"` | `"for later"` | `"eventually"`

---

<!-- Rule: g-rl-26-readme-changelog.mdc -->
# Rule: Update Documentation at Feature Boundary

When completing any task that **adds, removes, or changes user-facing behavior** — skills, commands,
hooks, agents, rules, conventions, or any element visible to end-users — the completing agent MUST:

## 1. Append to CHANGELOG.md

Add an entry under the `[Unreleased]` section using Keep a Changelog format:

```markdown
### Added
- Feature description with relevant command/file names

### Changed
- What changed and what it replaces

### Removed
- What was deprecated or removed
```

- Place the entry in the appropriate subsection (`Added`, `Changed`, `Removed`)
- Be specific: include command names, file paths, or skill names
- One entry per logical change (not one per file)

## 2. Update README.md (If Relevant Section Exists)

If the completed task changes something that has a section in `README.md`:
- Update the relevant section to reflect the new state
- Update counts in the "What's Included" table if agents/skills/commands count changed
- Update command names if they were renamed

## What Qualifies as "User-Facing"

**YES — must update docs:**
- New command, skill, agent, hook, or rule
- Renamed/deprecated command, skill, agent
- Changed behavior of an existing command
- New convention that agents must follow
- New configuration option

**NO — can skip:**
- Internal refactor with no behavior change
- Task file updates (TASKS.md, individual task specs)
- Bug fix with no interface change
- Code comments or inline documentation

## Where to Update

| Project type | CHANGELOG.md | README.md |
|-------------|--------------|-----------|
| gald3r_dev (this repo) | `CHANGELOG.md` at root | `README.md` at root (contributor view) |
| G:/gald3r_ecosystem/gald3r_template_full | `G:/gald3r_ecosystem/gald3r_template_full/CHANGELOG.md` | `G:/gald3r_ecosystem/gald3r_template_full/README.md` (end-user view) |
| Installed gald3r project | `CHANGELOG.md` at project root | `README.md` at project root |

## Timing

- Update docs **before** marking the task `[🔍]` (awaiting verification)
- Docs check is part of the `g-go` and `g-go-code` post-task checklist

---

<!-- Rule: g-rl-33-enforcement_catchall.mdc -->
# Enforcement Catchall

These rules fire on EVERY response, even when no gald3r agent is explicitly active.

## Error Reporting (Zero Tolerance)

If your response mentions ANY of the following — create a `.gald3r/BUGS.md` entry and bug file in `.gald3r/bugs/` immediately:
- "error", "warning", "pre-existing", "was already there", "unrelated error"
- "lint error", "TypeScript error", "compile error", "exception"

"Pre-existing" and "unrelated" are NOT exemptions. If it's worth mentioning, it's worth logging.

**Fast-path entry** (takes 30 seconds):
```markdown
### BUG-NNN
- **Title**: [brief]
- **Severity**: Low/Medium/High/Critical
- **Status**: Open
- **File**: path/to/file (line N)
- **Note**: Pre-existing. Not blocking current task.
- **Created**: YYYY-MM-DD
```

| Rationalization | Reality |
|---|---|
| "It's pre-existing, not related to my changes" | Pre-existing = undocumented. Log it anyway. |
| "It's just a warning, not a real error" | Warnings become errors. Log it now. |
| "I'll log it after I finish this task" | You won't. Log it before moving on. |
| "It's in someone else's code" | Still in this codebase. Still needs a record. |
| "The user probably already knows" | Then the log takes 30 seconds and confirms it. |
| "It's too minor to bother with" | BUG-NNN with severity:Low costs nothing and creates an audit trail. |

## Task Completion (Mandatory Commit Offer)

If work was just completed on any task — offer a git commit before ending the response.
Never end a response after task completion without this offer.

| Rationalization | Reality |
|---|---|
| "The user will commit when they're ready" | Your job is to offer it. Offer it. |
| "It's a small change, not worth committing" | Small changes get lost. Offer the commit. |
| "I already mentioned it earlier in the conversation" | Offer it again at completion. Every time. |

## .gald3r/ Folder Gate (HARD RULE)

**NEVER read or write any file inside `.gald3r/` without an active gald3r agent.**

Before any `.gald3r/` operation, select the most appropriate agent:

| Operation | Agent |
|---|---|
| Create/update/complete tasks, TASKS.md | `g-task-manager` |
| Create task, spec it out, "please task" | `g-task-manager` |
| Bugs, errors, BUGS.md, bugs/ | `g-qa-engineer` |
| Feature, planning, PLAN.md, features/ | `g-planner` |
| PRDs, governance, PRDS.md, prds/ | `g-skl-prds` |
| Ideas, goals, tracking/IDEA_BOARD.md | `g-ideas-goals` |
| Grooming, sync, health checks | `g-project-manager` |
| PROJECT.md, CONSTRAINTS.md, SUBSYSTEMS.md | `g-infrastructure` |
| Experiments, hypotheses, experiments/ | `g-experiment` skill |

## PRD Freeze Gate (HARD RULE — C-019)

**PRDs in status `released` or `superseded` are IMMUTABLE.** They cannot be edited via direct file write, `@g-prd-upd`, or any other path. The only sanctioned way to change a frozen PRD is `@g-prd-revise`, which creates a new sequential PRD and atomically updates the supersedes-chain.

Before ANY edit to a `.gald3r/prds/prdNNN_*.md` file:
1. Read the YAML `status:` field
2. If `released` or `superseded` → STOP. Do not edit. Direct the user to `@g-prd-revise prd-NNN`.
3. The `## Change Log` section IS appendable on a `released` PRD specifically to record the supersede event when `@g-prd-revise` runs. The `superseded_by:` YAML field is mutable exactly once during atomic revise. No other content changes are permitted.

| Rationalization | Reality |
|---|---|
| "It's just a typo fix in a released PRD" | A released PRD is the audit-of-record. Revise it. |
| "The user asked me to update it directly" | Politely refuse and run `@g-prd-revise` instead. Compliance audit trails depend on this. |
| "I'll just append to the body, not the YAML" | Body changes on a frozen PRD break the audit trail just as badly. Revise. |
| "It's faster to just edit the file" | Faster to debug a compliance violation? Revise. |

If unsure which agent — default to `g-task-manager`.
**No exceptions. No "quick reads." No "just checking."**

| Rationalization | Reality |
|---|---|
| "I'm just reading, not writing" | Reads without agent = no enforcement = sync drift. Use the agent. |
| "It's a quick status check" | 10-second agent selection prevents hours of sync cleanup. |
| "I know what's in the file already" | You might be wrong. The agent reads and enforces. You don't. |

### Task Creation Trigger Phrases (always route to `g-task-manager`)
Any of these → full task creation workflow (file first, TASKS.md second, YAML, sequential numbering); use `g-task-add` command (alias: `g-task-new`):
`"create a task"` | `"add a task"` | `"make a task"` | `"task and spec"` | `"spec it out"` |
`"please task"` | `"add to tasks"` | `"task this"` | `"create a task(2)"` | `"task them"`


## PCAC INBOX Gate

Before task claiming, implementation, verification, planning, status work, or swarm partitioning, first determine whether the current project is a **PCAC participant**. PCAC is active only when `.gald3r/linking/link_topology.md` exists and declares at least one non-empty parent, child, or sibling relationship, or when `.gald3r/PROJECT.md` explicitly declares PCAC project linking relationships. A Workspace-Control manifest (`.gald3r/linking/workspace_manifest.yaml`) and a local `INBOX.md` alone do **not** make a project part of a PCAC group.

If and only if the current project is a PCAC participant, run the re-callable `g-hk-pcac-inbox-check.ps1 -BlockOnConflict` hook when present. If it reports `INBOX CONFLICT GATE` or exits with code `2`, stop and run `@g-pcac-read` before continuing. Exception: `g-medic` L1 triage runs the hook without `-BlockOnConflict`, completes health scoring, records the PCAC conflict severity, then blocks L2-L4 planning/apply work and all claim/implementation/review/planning work until `@g-pcac-read` resolves the conflict. Swarm coordinators rerun the check every 30 minutes and before final summaries only while PCAC is active.

If the project is not a PCAC participant, skip the PCAC hook and report `PCAC: not configured / skipped` when status or medic output includes gate state.

## Gald3r Housekeeping Commit Gate (T531 — `g-go*` only, controller-only)

Sits between the **PCAC INBOX Gate** and the **Clean Controller Gate** on the `g-go`, `g-go-code`, `g-go-review`, `g-go-swarm`, `g-go-code-swarm`, and `g-go-review-swarm` paths. It runs at two points: (a) **preflight** — before claims, worktrees, coding, review, or swarm partitioning; and (b) **post-coordinator-write** — immediately after `g-go*` coordinator-owned shared `.gald3r` writes (task/bug status updates, review-result writes, sent_orders ledger updates, safe report/log outputs) and before the next major phase.

Behavior at each invocation:

1. Run `.gald3r_sys/skills/g-skl-git-commit/scripts/gald3r_housekeeping_commit.ps1` against the orchestration git root. The helper reads `git status --porcelain=v1 -uall`, classifies every dirty path against an explicit allowlist of safe controller `.gald3r/` coordination paths and a deny list of sensitive/identity/config paths, and returns one of: `clean`, `safe-gald3r-housekeeping`, `safe-gald3r-coordination`, `unsafe-gald3r`, `mixed-dirty`, `conflict`, `drift-detected`, or `committed-*` (when `-Apply`).
2. If `clean` → continue without writing.
3. If `safe-gald3r-housekeeping` (preflight) or `safe-gald3r-coordination` (post-write) → invoke the helper with `-Apply`. The helper stages **only** the classified-safe paths via explicit `git add -- <paths>`, re-checks for drift, then commits with one of:
   - `chore(gald3r): preflight gald3r housekeeping`
   - `chore(gald3r): commit g-go coordination state`
   Include `Task: #<id>` / `Bug: BUG-<id>` in the body when ownership is clear (the helper accepts `-TaskId` / `-BugId`). `git add .` is **never** used.
4. If `unsafe-gald3r`, `mixed-dirty`, `conflict`, or `drift-detected` → preserve the existing **Clean Controller Gate** hard-block. Do not auto-commit. Report the exact unsafe paths and reasons; user action required.
5. Member-repo targets (marker-only `.gald3r/` with `.identity` but no manifest and no `TASKS.md`) are refused with `config-fault`. The helper never writes member repository `.gald3r/` content.

Concurrency / drift protection: in `--swarm` flows only the coordinator runs this gate, and the helper re-checks `git status` immediately before staging and again immediately after committing; if another writer altered the tree between classify and stage, the helper aborts the staging and exits non-zero with `drift-detected` so the coordinator falls back to the hard-gate path.

This gate is **controller-only `g-go*` behavior**. It is not a global rule for every gald3r command. Member repositories' marker-only `.gald3r/` policy is unchanged.

## Clean Controller Gate (orchestration repo)

After the PCAC gate passes and **before** task or bug claims, T170 worktree allocation (`gald3r_worktree.ps1 -Action Create`), swarm partitioning, or any coordinator-owned write to shared `.gald3r` ledgers (for example `.gald3r/TASKS.md`, `.gald3r/BUGS.md`, task/bug files when acting as coordination surfaces), `CHANGELOG.md`, generated Copilot instructions, or parity output, agents MUST verify the **orchestration git root** is clean enough to land the required checkpoint or review-result commit.

- The **Gald3r Housekeeping Commit Gate** runs first (see the section directly above). It may auto-commit dirty paths that are exclusively safe controller `.gald3r/` housekeeping; only paths it classifies as unsafe / mixed / unknown reach this gate as blockers.
- Run `git status --short` at the repository root from which `g-go*`, `g-go-code*`, or `g-go-review*` is executed (Workspace-Control owner when a manifest is active).
- Any path **outside** this run's explicit coordinator staging allowlist for the active task and bug IDs is a **blocker**: stop before those mutations; commit, stash, or split unrelated work first. Preserve any bucket handoff artifacts already produced and list the paths that blocked progress.
- Do **not** pass `gald3r_worktree.ps1 -AllowDirty` for `g-go*`, `g-go-code*`, `g-go-review*`, or `--swarm` flows unless every dirty path is owned exclusively by the active task/bug scope and a `## Status History` row documents that override.

## Member touch-set clean gate (v1 — `workspace_repos`)

The orchestration git root is **always** in the clean gate's touch set. When the active task or bug declares **`workspace_repos:`** naming one or more manifest `repository.id` values, extend the **Clean Controller Gate** and **Pre-Reconciliation Clean Gate** to each **additional** repository root resolved from those IDs (blast radius follows declared cross-repo scope).

- If `.gald3r/linking/workspace_manifest.yaml` exists, map each listed ID (deduplicated) to `repositories[?].local_path`. For each path that exists on disk, resolve the git root with `git -C "<path>" rev-parse --show-toplevel` (PowerShell quoting as needed). Run `git status --short` at that root. Apply the same **explicit coordinator staging allowlist** rule per root: unrelated dirty paths are **blockers** for claims, worktrees, coordinator shared writes, and checkpoint/review-result commits until committed, stashed, split, or documented per-root in the owning task or bug `## Status History` when policy permits the same `-AllowDirty` discipline as the orchestration root.
- Skip member IDs whose `local_path` is missing while `lifecycle_status` is a planned/bootstrap gap (report per `g-skl-workspace`); those do **not** expand the touch set until paths exist.
- If the manifest is missing while `workspace_repos` is non-empty, or a listed ID is unknown under `repositories:`, treat that as a **blocker** for coordinator writes that depend on workspace routing until the manifest or frontmatter is repaired (single-repo-only work queued to the orchestration root alone may still run if `workspace_repos` lists only the owner id and resolves).

## Touch-set expansion (v2 — optional blast-radius signals)

Union the following extra repository roots into the touch set (same `git status --short` + allowlist rules as v1), **in addition to** the orchestration root and any `workspace_repos` members:

1. **`extended_touch_repos:`** — optional task/bug YAML list of additional `repository.id` values present in the workspace manifest (identical resolution rules as v1). Use when planners know the operation spans repos beyond `workspace_repos`.
2. **`touch_repos:` (swarm handoff)** — In `--swarm` runs, when bucket work edits roots not already covered by `workspace_repos` + `extended_touch_repos:`, bucket summaries and the coordinator reconciliation block MUST list those ids under `touch_repos:` so the union is gated before shared writes.
3. **Subsystem `locations:` absolute paths** — When the active item declares **`subsystems:`**, read each `.gald3r/subsystems/{name}.md` frontmatter **`locations:`** (all nested list items and string values). For every value that matches a host **absolute** path (`^[A-Za-z]:[/\\]` on Windows, or POSIX `/` rooted at `/` for non-Windows), if that path exists, resolve `git -C <dir> rev-parse --show-toplevel` using the path's directory when the path is a file. Each distinct git root **other than** the orchestration root joins the touch set. Pure relative entries (`.gald3r/...`, `skills/...`) do not expand the set. **Non-goal:** never require every manifest member to be clean for every `g-go` run.

## Pre-Reconciliation Clean Gate (`--swarm`)

Immediately **before** the coordinator applies bucket handoffs to the primary checkout, updates shared `.gald3r` indexes, touches `CHANGELOG.md`, or creates checkpoint / review-result commits, **re-run** `git status --short` on the **orchestration root and every other repository root in the computed touch set** (orchestration + v1 `workspace_repos` members + v2 expansions). If unrelated dirty paths appeared during parallel bucket work in **any** of those roots, **fail closed**: do not write shared ledgers or docs; keep patches, artifacts, and evidence; report **per-root** blockers using the same narrow non-commit reasons as the Review Result Commit gate.

The orchestration root may also be passed through the **Gald3r Housekeeping Commit Gate (post-write mode)** between major phases (after task/bug status writes, after review-result writes, after sent_orders ledger updates, after safe report/log outputs). In post-write mode, when the dirty set is exclusively safe controller `.gald3r/` coordination, the coordinator creates a focused `chore(gald3r): commit g-go coordination state` commit and continues; otherwise the standard fail-closed behavior above applies.

## Swarm Reconciliation Gate

In `g-go --swarm`, `g-go-code --swarm`, and `g-go-review --swarm`, bucket agents are handoff producers. They return patch bundles, generated artifacts, evidence, changed-file inventories, and proposed Status History rows. When v2 applies, handoffs and coordinator summaries MUST include `touch_repos:` listing any additional manifest `repository.id` values whose git roots were edited whenever that set is not already covered by the claimed task's `workspace_repos` + `extended_touch_repos:`. Bucket agents MUST NOT directly write shared `.gald3r` status/index files, `CHANGELOG.md`, generated Copilot prompts, parity output, final staging, or commits. The coordinator performs all shared writes in one final pass after deterministic reconciliation **only after** the Pre-Reconciliation Clean Gate passes.

Swarm worktrees MUST stage by explicit path allowlist only. `git add .` is forbidden in bucket worktrees because it can leak transient ownership files such as `.gald3r-worktree.json`, terminal transcripts, local logs, or other non-deliverable artifacts. If a bucket patch touches shared coordination files, the coordinator must either reject that portion or convert it into a coordinator-owned final write.

## Review Checkpoint Gate

Default implementation-to-review handoff is a code-complete checkpoint commit. After implementation reconciliation and coordinator-owned shared writes, `g-go-code` / `g-go --swarm` creates a checkpoint commit and passes its branch/SHA to `g-go-review` / `g-go-review --swarm`. Reviewers create `review` / `review-swarm` worktrees from that checkpoint by default. Dirty snapshot mode is fallback-only for explicitly uncommitted, dirty, or non-branch-addressable sources, and the handoff must name the source checkout path.

## Review Result Commit Gate

After `g-go-review`, `g-go-review --swarm`, or `g-go` Phase 2 writes PASS or FAIL review statuses, the reviewer/coordinator MUST create a review-result commit by default. This applies to PASS (`[✅]`), FAIL back to pending/open (`[📋]`), requires-user-attention (`[🚨]`), and mixed verdicts. Do not stop at a mandatory commit offer when a safe commit is possible; the review result itself is the audit artifact.

The review-result commit must stage only review-owned paths by explicit allowlist. Never use `git add .`; exclude `.gald3r-worktree.json`, terminal transcripts, local logs, unrelated files, and other non-deliverable artifacts. Allowed reasons not to create the commit are limited to unresolved conflicts, failed commit hooks, staged or untracked unrelated changes, detected secrets, dirty generated outputs not owned by review, missing user permission for destructive or out-of-scope changes, or repository state that prevents a safe commit. If blocked, state the exact blocker in the final summary.


## Workspace-Control Command Gate

Use `g-wrkspc-*` as the short primary command family for Workspace-Control. Existing `g-workspace-*` commands remain backwards-compatible aliases. Lifecycle commands (`g-wrkspc-init`, `g-wrkspc-member-add`, `g-wrkspc-member-remove`) are dry-run by default; apply mode may update only `.gald3r/linking/workspace_manifest.yaml` unless the active task explicitly authorizes member repository writes. Member removal is registry-only and must never delete member folders, `.git/`, branches, remotes, commits, or worktrees.

## Active Index Archive Gate

`TASKS.md` and `BUGS.md` are active indexes, not unlimited historical ledgers. Terminal task and bug history must be moved through `g-task-archive` / `g-bug-archive`, using dry-run first. Archive index files live directly under `.gald3r/archive/` as count buckets (`archive_tasks_0000_0999.md`, `archive_bugs_0000_0999.md`, then `1000_1999`, etc.). Archived task and bug files live under `.gald3r/archive/tasks/tasks_0000_0999/` and `.gald3r/archive/bugs/bugs_0000_0999/` style buckets with at most 1000 files per bucket. Never delete historical records during archival; preserve provenance and leave active-index archive pointers.

## PCAC-Derived Task Priority Floor (T166)

When a task is created as the direct result of an inbound PCAC item (request from child, broadcast/order from parent, sync from sibling, or conflict resolution), the agent MUST:

1. Pass a `pcac_source: { type, source_project, inbox_ref }` block to `g-skl-tasks` CREATE TASK
2. Default priority to `high` (or `critical` when `type: conflict` or the source carries an explicit urgency flag)
3. When `priority: critical`, force `requires_verification: true` — cross-project critical work cannot skip verification
4. Render the TASKS.md row with a `[PCAC]` prefix (regenerated from frontmatter; never hand-edited)

Humans MAY manually downgrade priority after creation; agents MUST NOT auto-downgrade. PCAC-derived tasks must never sit at default medium priority — another project is, by definition, waiting on us.

## PCAC Outbound Tracking Surface (T167)

PCAC sends are **immediate operations**, never queued, never task-creating. The `.gald3r/linking/sent_orders/order_*.md` ledger is the **only** tracking surface for outbound PCAC state (status: `sent` → `acknowledged` → `in-progress` → `completed` | `blocked` | `abandoned`). Parents/siblings waiting on a child response track that wait via the ledger, NEVER via a local "await response" task. Creating tasks like "Send PCAC to X" or "Await response from children" is forbidden — `g-skl-tasks` CREATE TASK rejects them with the message: "Use sent_orders ledger, not a task."

## Code Change Enforcement (BLOCKED without Task/Bug)

If code files were modified in this response and no active task or bug is referenced, the agent MUST either:
1. Create a retroactive task via g-task-new before proceeding, OR
2. Create a bug via g-bug-report if the change was a fix

**Exceptions** (no task/bug required):
- `.gald3r/` file edits (task management housekeeping)
- Documentation-only changes (docs/, README.md, AGENTS.md, CLAUDE.md)
- Git operations (commits, branch management)

| Rationalization | Reality |
|---|---|
| "It's a quick fix, not worth a task" | Quick fixes become mystery changes. Log it. |
| "I'll create the task after I'm done" | You won't. Create it before or during. |
| "The user didn't ask for a task" | The system requires it. Create it retroactively. |
| "It's just a config change" | Config changes break things. Track them. |

## Follow-Up Task Filing Gate (Pipeline Runs — HARD RULE)

When a `g-go`, `g-go-code`, or `g-go-review` session produces a summary that includes ANY follow-up items, those items MUST be created as real task files via `g-skl-tasks CREATE TASK` **before** the summary is written. This rule fires even when no gald3r task manager is explicitly active.

**Violation indicators** — if you see any of these in a pipeline session summary, the gate was missed:
- Bullet points with slug-style names like `T1043-followup-*` or `T{id}-followup-{slug}`
- A section titled "Follow-ups created (named, not blocking)" or similar
- Any follow-up item without a real task ID (e.g. `T1110`)

**Required response**: Do NOT silently accept the incomplete state. Report the naming violation and create the missing task files via `g-skl-tasks CREATE TASK` immediately.

| Rationalization | Reality |
|---|---|
| "It's named for tracking" | Named-only = permanently lost. No file = no task. |
| "It's non-blocking" | Non-blocking items still need task files. Priority: low is fine. |
| "The user can file it later" | The user has moved on. The pipeline IS the filing point. |
| "It was just a slug, not a real task" | Exactly the violation. Create the real task now. |

## Delegation Hint

If the user mentions a task ID (e.g., "task 42", "#103") without explicitly invoking a gald3r agent:
→ Activate `g-task-manager` behavior for that operation.

If the user reports a bug or describes unexpected behavior without invoking `g-qa-engineer`:
→ Apply bug logging rules from `g-qa-engineer` immediately.

### Experiment Trigger Phrases (route to `g-experiment` skill)
Any of these → experiment workflow:
`"run experiment"` | `"check gate"` | `"experiment status"` | `"failure autopsy"` |
`"new experiment"` | `"experiment chain"` | `"run stage"` | `"next experiment"`

---

<!-- Rule: g-rl-34-todo_completion_gate.mdc -->
# TODO/Stub Lifecycle Enforcement

Stubs and TODOs are tracked from the **moment they are written** — not just at completion. This rule has two phases:

## Phase 1: Creation-Time (fires when writing any stub or TODO)

When writing code that includes a stub, placeholder, or TODO — **before moving to the next line** — immediately:

1. **Format the comment**: `TODO[TASK-{current_task_id}→TASK-{new_id}]: {description} — fix in follow-up task`
2. **Create the follow-up task** via `g-task-new` (type: `bug_fix` or `feature`)
3. **Insert the annotated comment** at the stub location (on the line directly above or same line)

**Do NOT write a bare `# TODO` and continue.** The follow-up task must exist before the stub is committed.

---

## Phase 2: Completion Gate

Fires whenever a task is marked `[🔍]` or `[✅]`. If the implementation contains **any** incomplete element, the agent MUST annotate it AND spawn a follow-up task before the status change is considered valid.

## What Triggers This Rule

Mark the task as incomplete (or add mandatory annotation) when ANY of the following exist in code written for this task:

| Pattern | Examples |
|---|---|
| TODO / FIXME comments | `# TODO`, `// TODO`, `/* FIXME */`, `-- TODO` |
| Stub function bodies | `pass`, `...`, `return None  # stub`, `throw new Error("not implemented")` |
| NotImplementedError | `raise NotImplementedError`, `todo!()` (Rust), `unimplemented!()` |
| Hardcoded / mock data | `FAKE_`, `MOCK_`, `TEST_`, `PLACEHOLDER_`, `"dummy"`, `"example.com"`, `12345` as real IDs |
| Hardcoded credentials or keys | Any literal string that looks like a key, token, password, or secret |
| Commented-out real logic | Sections replaced with `# real logic goes here` or similar |
| Empty except/catch blocks | `except: pass`, `catch (e) {}` with no handling |

## Mandatory Actions (BOTH required — not optional)

### 1. Annotate the code with a TODO comment

**Format** (use the comment syntax of the file's language):

```
TODO[TASK-{original_id}→TASK-{follow_up_id}]: {what is stubbed} — fix in follow-up task
```

**Examples by language:**

```python
# TODO[TASK-42→TASK-67]: Stub — replace with real Stripe payment processor call
def charge_card(amount):
    return {"status": "ok"}  # stub
```

```javascript
// TODO[TASK-15→TASK-23]: Hardcoded user ID — replace with auth context lookup
const userId = "abc-123-fake";
```

```sql
-- TODO[TASK-8→TASK-31]: Stub procedure — implement real balance recalculation logic
```

```typescript
// TODO[TASK-101→TASK-112]: NotImplemented — wire up real notification service
throw new Error("not implemented");
```

The comment MUST appear **on the line directly above or on the same line as** the stub/hardcoded value.

### 2. Spawn a follow-up task via gald3r-task-manager

Activate `g-task-manager` and create a new task that:
- Has a title clearly describing what the stub replaces
- References the original task ID in `dependencies:` field
- Has `type: bug_fix` or `type: feature` as appropriate
- Captures the file path and line number where the stub lives

The new task ID becomes `{follow_up_id}` in the comment above.

## Sequence (Do Not Reorder)

1. Identify all stubs/TODOs in code written for the task
2. Create follow-up task(s) → get new task ID(s)
3. Add `TODO[TASK-X→TASK-Y]` comments to each stub location
4. THEN mark the original task `[✅]` in TASKS.md

**Marking complete BEFORE annotating = violation.**

## Multi-Stub Tasks

If a single completed task has multiple stubs, each stub gets:
- Its own `TODO[TASK-{original}→TASK-{new}]` comment
- Its own follow-up task (or a single consolidated follow-up task if they are closely related, with the same `{new_id}` in multiple comments)

## Rationalization Table

| Rationalization | Reality |
|---|---|
| "It's just a temporary stub, everyone knows" | In 3 weeks nobody knows. The comment costs 5 seconds. |
| "The task is done, the stub is a separate concern" | If you shipped a stub, the task is not done. Annotate it. |
| "I'll remember to fix it later" | You won't. The follow-up task ensures it lives in the backlog. |
| "The TODO is obvious from context" | Context rots. The task ID is permanent. |
| "It's a test/dev stub, not production" | Dev stubs reach production. Every. Single. Time. |
| "Creating a task takes too long" | Fast-path task creation takes 60 seconds. Debugging a mystery stub takes hours. |

## Exemptions (Narrow)

The following do NOT require follow-up tasks or annotation:
- `pass` as the **entire body** of an abstract base class method explicitly declared abstract
- `...` in a `.pyi` stub file (type stubs only)
- Test fixtures with clearly named fake data (e.g., `fake_user = {"name": "Test User"}` inside a test file)

When in doubt — annotate it.

---

<!-- Rule: g-rl-35-bug-discovery-gate.mdc -->
# Bug-Discovery Gate (Zero-Ignore Policy)

When you encounter a bug during any coding or review session, the correct response depends on when the bug was introduced:

| Scenario | Correct Response |
|----------|-----------------|
| Bug introduced by **current task's code changes** | Fix it immediately (same task, same commit, no new ticket) |
| Bug is **pre-existing** (existed before this task started) | Create BUG entry + add `BUG[BUG-{id}]` comment; do NOT fix inline unless trivial |

**Silently ignoring a bug is never acceptable.**

---

## Step 1 — Determine Bug Origin

> Was the bug introduced by code changes in the *current task*?
> - Check: does the file modification list (or `git diff`) include the lines containing the bug?
> - **YES** → current-task bug
> - **NO** (or unsure) → treat as pre-existing (safer to over-log than under-log)

---

## Step 2A — Current-Task Bug

Fix it in place before marking `[🔍]`.

```
- No new BUG entry needed (it's part of this task's implementation)
- No BUG comment needed (it will be fixed before [🔍])
- If too complex to fix safely this session → treat as pre-existing (log it, move on)
```

---

## Step 2B — Pre-Existing Bug (Mandatory Steps)

1. **Create BUG entry** via `g-skl-bugs` REPORT operation → get `BUG-{id}`
2. **Add annotation** at the bug site (on the line directly above or same line):
   ```
   BUG[BUG-{id}]: {description} — see .gald3r/bugs/bug{id}_{slug}.md
   ```
3. **Do NOT fix inline** unless the fix is:
   - 1–3 lines
   - Zero risk of expanding scope
   - Confirmed by code inspection (not guessed)
   If it doesn't meet all three → log and move on
4. **Notify in session summary**: "Found pre-existing bug BUG-{id}: {title}"

---

## BUG Comment Format (by language)

```python
# BUG[BUG-03]: Off-by-one in page count — see .gald3r/bugs/bug003_page_count.md
total_pages = len(items) / page_size  # should use ceil division
```

```javascript
// BUG[BUG-07]: Race condition on concurrent writes — see .gald3r/bugs/bug007_write_race.md
await saveRecord(data);
```

```typescript
// BUG[BUG-09]: Missing null guard on user.profile — see .gald3r/bugs/bug009_null_profile.md
return user.profile.name;
```

```sql
-- BUG[BUG-12]: NULL guard missing — divide-by-zero possible — see .gald3r/bugs/bug012_null_divide.md
```

```powershell
# BUG[BUG-14]: Path assumes Windows drive letter — see .gald3r/bugs/bug014_path_assumption.md
```

The `BUG[BUG-{id}]` format intentionally mirrors `TODO[TASK-X→TASK-Y]` from `g-rl-34` for a uniform annotation system.

---

## Exemptions

Do NOT report as pre-existing bugs:
- Intentional placeholder values (test fixtures, examples with clearly fake data)
- Linter warnings already tracked as tech debt in BUGS.md
- Cosmetic issues (formatting, whitespace, naming) **unless** they cause incorrect behavior

---

## Integration with g-go-code / g-go-review

**During implementation (g-go-code b2 AC gate)**:
- Any pre-existing bug encountered must have a BUG entry + comment before `[🔍]`
- Bugs introduced by this task must be fixed inline before `[🔍]`

**During verification (g-go-review review step)**:
- Bug introduced by this task → flag as unmet criterion → task FAIL (back to `[📋]`)
- Pre-existing bug discovered → log BUG entry + comment; note in summary; does NOT fail this task

---

<!-- Rule: g-rl-36-workspace-member-gald3r-guard.mdc -->
# Workspace-Control Member `.gald3r/` Marker-Only Guard (HARD RULE)

**Workspace-Control controlled_member and migration_source repositories may keep ONLY a slim `.gald3r/` marker:**

- `.gald3r/.identity` — identifies the member and ties it back to the workspace controller
- `.gald3r/PROJECT.md` — copied / parity-maintained from the controller; describes the member's mission

**Live gald3r control-plane state is forbidden in member repositories.** Any of the following inside a member's `.gald3r/` is a hard violation: `TASKS.md`, `tasks/`, `BUGS.md`, `bugs/`, `PLAN.md`, `FEATURES.md`, `SUBSYSTEMS.md`, `RELEASES.md`, `CONSTRAINTS.md`, `IDEA_BOARD.md`, `PRDS.md`, `prds/`, `features/`, `releases/`, `subsystems/`, `config/`, `linking/`, `experiments/`, `logs/`, `reports/`, `archive/`, `specifications_collection/`, `learned-facts.md`, or any equivalent orchestration state.

The workspace controller (e.g. `gald3r_dev`) is the source of truth for live tasks, bugs, plans, features, releases, subsystems, constraints, ideas, PRDs, and cross-project orchestration. Members are independent git roots that hold source code, packaging, and history — but never live project task state.

External workspace member template repos (`G:/gald3r_ecosystem/gald3r_template_slim`, `G:/gald3r_ecosystem/gald3r_template_full`, `G:/gald3r_ecosystem/gald3r_template_adv`) are the **only** legitimate exception: their `.gald3r/` content is intentional install template content.

This invariant fires for every workflow that may write `.gald3r/` to an arbitrary destination: `g-skl-setup`, `g-skl-pcac-spawn`, `g-skl-pcac-adopt`, `g-skl-workspace` SPAWN_APPLY / ADOPT_APPLY, `gald3r_install`, and any future scaffold/repair flow.

## Source of truth

- **Bug**: `BUG-021` (Critical) — Workspace-Control scaffold/setup can create live `.gald3r/` control planes inside member repositories.
- **Task**: `Task 213` (spec v1.1) — defines the marker-only policy and its enforcement layers.
- **Manifest**: `.gald3r/linking/workspace_manifest.yaml` → `routing_policy.member_gald3r_invariant`.
- **Helper scripts** (gald3r_dev root + `G:/gald3r_ecosystem/gald3r_template_full/scripts/` for installed projects):
  - `.gald3r_sys/skills/g-skl-workspace/scripts/check_member_repo_gald3r_guard.ps1` — marker-aware preflight
  - `.gald3r_sys/skills/g-skl-workspace/scripts/bootstrap_member_gald3r_marker.ps1` — only sanctioned writer of member `.gald3r/`
  - `.gald3r_sys/skills/g-skl-workspace/scripts/remediate_member_gald3r_marker.ps1` — non-destructive cleanup of forbidden member content
  - `.gald3r_sys/skills/g-skl-workspace/scripts/validate_workspace_members_gald3r.ps1` — workspace-wide marker compliance audit

## Guard call contract

Before any code path writes a `.gald3r/` file inside a member repository, call the guard:

```powershell
# Per-path check (preferred — most precise)
powershell -NoProfile -ExecutionPolicy Bypass -File .gald3r_sys/skills/g-skl-workspace/scripts/check_member_repo_gald3r_guard.ps1 `
    -TargetPath "<absolute_member_repo_path>" `
    -DotGald3rPath "<relative_path_inside_dot_gald3r>"
$exit = $LASTEXITCODE
```

| Mode | What it answers |
|------|-----------------|
| `-DotGald3rPath ".identity"` or `-DotGald3rPath "PROJECT.md"` | ALLOW (marker-safe) |
| `-DotGald3rPath "TASKS.md"` (or any control-plane path) | BLOCK |
| `-AllowMarkerInit` (no path) | ALLOW (caller asserts marker bootstrap intent; bootstrap helper enforces actual filesystem allowlist) |
| Default (no path, no flags) | BLOCK on member targets — caller must specify intent |

Exit codes: `0` ALLOW, `1` BLOCK, `2` ERROR. Optional flags: `-WarnOnly`, `-Json`, `-ManifestPath`.

## Bootstrap call contract (the only legal `.gald3r/` writer for members)

When a member is added, adopted, or spawned, create the marker via:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .gald3r_sys/skills/g-skl-workspace/scripts/bootstrap_member_gald3r_marker.ps1 `
    -MemberPath "<absolute_member_repo_path>" `
    -MemberId "<manifest_repo_id>" `
    -ControllerPath "<absolute_controller_path>" `   # optional: defaults to upward manifest discovery
    -Apply                                            # omit for dry-run
```

The bootstrap helper:

1. Confirms membership via the guard (`-AllowMarkerInit` mode).
2. Refuses to proceed if existing `.gald3r/` already contains forbidden content — directs the user to remediate first.
3. Creates `.gald3r/.identity` (if absent) tying the member back to the controller (member project_id, member project_name, controller project_id, controller path, `member_gald3r_marker_only=true`).
4. Creates `.gald3r/PROJECT.md` (if absent) as a member-stub identifying the member + cross-linking to the controller.
5. Preserves any pre-existing `.identity` or `PROJECT.md`.
6. Refuses to write any other path.

## Remediation call contract (existing violation cleanup)

When a member already contains live control-plane content, remediate it:

```powershell
# Dry-run first
powershell -NoProfile -ExecutionPolicy Bypass -File .gald3r_sys/skills/g-skl-workspace/scripts/remediate_member_gald3r_marker.ps1 `
    -MemberPath "<absolute_member_repo_path>"

# Apply (quarantines forbidden entries to `.gald3r-quarantine/<timestamp>/`)
powershell -NoProfile -ExecutionPolicy Bypass -File .gald3r_sys/skills/g-skl-workspace/scripts/remediate_member_gald3r_marker.ps1 `
    -MemberPath "<absolute_member_repo_path>" `
    -Apply
```

Remediation **never deletes**; it quarantines forbidden entries to `<member>/.gald3r-quarantine/<timestamp>/` (or to an explicit `-BackupTo` path). The marker pair (`.identity` + `PROJECT.md`) is preserved in place. The user controls final disposition of the quarantine folder.

## Validation call contract

Audit all manifest members at any time:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .gald3r_sys/skills/g-skl-workspace/scripts/validate_workspace_members_gald3r.ps1
```

Reports per-member compliance: `clean` / `marker_missing` / `has_violations` / `not_yet_created`. Exit `0` if all clean, `1` if any have violations (use `-WarnOnly` for advisory mode). Required as part of pre-adoption preflight before any new member (e.g. `gald3r_valhalla`) is added.

## Skill / command preflight requirements

The following surfaces MUST call the guard before writing live `.gald3r/` content, and MUST call the bootstrap helper as the sanctioned writer:

- **`g-skl-workspace`**:
  - `SPAWN_APPLY` — after creating directory + git init + minimal `.gitignore`/`README.md`, call bootstrap with `-Apply` to create the marker pair.
  - `ADOPT_APPLY` — refuse if target's `.gald3r/` already contains live control plane (require remediation first); then call bootstrap to ensure marker is present.
  - `MEMBER_ADD_APPLY` — when path exists, call bootstrap; when path is planned, defer to first SPAWN/ADOPT.
  - New ops: `MEMBER_MARKER_BOOTSTRAP`, `MEMBER_MARKER_REMEDIATE`, `MEMBER_MARKER_VALIDATE`.
- **`g-skl-setup`** — Step 0 calls the guard. If target is a controlled_member, BLOCK setup (members get marker-only via `g-wrkspc-spawn` / `g-wrkspc-adopt`, not full setup).
- **`g-skl-pcac-spawn`** — Pre-Flight Checks call the guard. PCAC-spawning a project INTO a controlled member path is forbidden (PCAC spawn = new standalone project, not a workspace member; use `g-wrkspc-spawn` for workspace members).
- **`g-skl-pcac-adopt`** — Step 2.5 calls the guard for `.gald3r/linking/` writes against the target. If target is a workspace member, switch to `--one-way` automatically (skip the target write) and direct user to `@g-wrkspc-adopt` for full Workspace-Control adoption.
- **`gald3r_install` MCP tool** — before writing `.gald3r/.project_id`, `.gald3r/.vault_location`, `.gald3r/.user_id`, call the guard. If member match, refuse and direct to bootstrap helper instead.
- **Future workflows** (`@g-wrkspc-init`, scaffold/repair tools) that materialize `.gald3r/` files at an arbitrary path.

## Pre-adoption preflight (gald3r_valhalla and any future populated member)

Before adopting an existing populated gald3r project (e.g. `gald3r_valhalla`) as a Workspace-Control member, the operator MUST:

1. Run `.gald3r_sys/skills/g-skl-workspace/scripts/validate_workspace_members_gald3r.ps1` to baseline current workspace marker compliance.
2. Run `.gald3r_sys/skills/g-skl-workspace/scripts/check_member_repo_gald3r_guard.ps1 -TargetPath <candidate>` to confirm the candidate would be classified as a member after adoption.
3. Inspect the candidate's existing `.gald3r/` for live control plane.
4. If live control plane is present, do NOT silently overwrite. Either:
   - **Adopt the project's history** via the upcoming Workspace-Control populated-gald3r adoption flow (Tasks 214–217). The flow imports active items into the controller with provenance, archives terminal items, and reduces the candidate's `.gald3r/` to the marker pair via remediation.
   - **Defer adoption** until cleanup/migration is complete.
5. Pass marker bootstrap only after preflight + remediation + history import are all complete.

The adoption preflight refuses to overwrite an existing real `.gald3r/` control plane. It reports the required migration or cleanup steps instead of mutating it.

## Existing-violation handling (e.g. gald3r_throne)

If a member repository already contains a live control plane (the historical `gald3r_throne` case), the agent MUST:

1. Surface the violation explicitly in the session summary.
2. Refuse any new write that would touch the existing live state without explicit remediation.
3. Recommend the user run `remediate_member_gald3r_marker.ps1` (dry-run, then `-Apply`) followed by `bootstrap_member_gald3r_marker.ps1 -Apply` to land on the marker-only shape. Both helpers are non-destructive (the remediator quarantines, never deletes).
4. Cleanup is never bundled with prevention work — it gets its own task with explicit user authorization.

## Rationalization table

| Rationalization | Reality |
|---|---|
| "It's just a small TASKS.md stub" | A stub is still live control plane. Member `.gald3r/` is marker-only. |
| "The member needs its own task tracker" | The controller IS the task tracker. Members don't have parallel state. |
| "I'll mark it gitignored" | Gitignored is not the boundary. The bug is the existence of live state. |
| "But T197 created `.gald3r/TASKS.md` and it shipped" | That violated the policy. T213 v1.1 + remediate fix it; bootstrap creates the correct marker. |
| "The manifest has `write_allowed: true` for gald3r_throne" | `write_allowed: true` does not extend to `.gald3r/` control plane. See `member_gald3r_invariant.marker_allowlist` and `disallowed_paths` in the manifest. |
| "I just need a quick `.gald3r/PLAN.md` for this member" | No. PLAN.md is controller-only. The member's mission goes in `PROJECT.md`. |

## Template directory exception (mandatory honor)

Paths matching `**/template_(slim|full|adv)/**` carry deliberate `.gald3r/` template content. The guard helper recognizes these paths and returns ALLOW with reason `template_directory_exception`. Do **not** add additional carve-outs — the only legitimate `.gald3r/` writes outside the control project are template content under those three directories.

---

<!-- Rule: g-rl-37-think-in-code.mdc -->
# Think in Code — Context Reduction Pattern (g-rl-37)

**Source**: OpenAI context-mode MCP "Think in Code" pattern. Validated on gald3r g-go workflows.

## Rule

When a task requires **3 or more sequential reads, greps, or status checks** on the same or related files, **write a single script** instead of making multiple tool calls.

## Threshold

| Number of planned tool calls | Action |
|------------------------------|--------|
| 1–2 | Normal tool calls are fine |
| 3–9 | Prefer a single script |
| 10+ | **MUST** use a script |

## Why

- 1 script = up to 10 tool calls collapsed to 1 context round-trip
- 65–75% output token reduction for file-read-heavy tasks
- Reduces context window pressure, enabling more tasks per session

## Examples

### ❌ Multiple tool calls (wasteful)
```
read_file("config.py")
grep("OPENAI_KEY", "config.py")
read_file("config.py")  # again, looking for something else
```

### ✅ Single script (preferred)
```python
# Run with shell or Python tool in one call
import re, pathlib
src = pathlib.Path("config.py").read_text()
keys = {m.group(1) for m in re.finditer(r"(\w+_KEY)\s*=", src)}
print("keys:", sorted(keys))
print("lines:", src.count("\n"))
```

## Exemptions

Do NOT collapse to a script when:
- The second tool call depends on runtime output of the first (dynamic path resolution)
- You need an IDE diff/edit tool (not a script)
- The task is a single-file edit (script overhead not worth it)

## Integration with g-go-code

`g-go-code` Step b0 (Impact Scan) and Step c1 (context assembly) check `AGENT_CONFIG.md context_reduction_mode`. When `think_in_code: true`, agents are reminded of this rule before tool planning.

