# Changelog
<!-- APPEND ONLY: This file must only grow. Never use Write/overwrite on this file. Use StrReplace for targeted edits or PowerShell for structured operations. Reading with a line limit then writing back = silent truncation. -->

All notable changes to gald3r are documented here.
Format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).
gald3r uses [Semantic Versioning](https://semver.org/).

---

## [Unreleased]

### Added
- **`@g-mission resume --budget N`**: override the turn budget on resume without re-setting the mission — enables overnight budget expansion. `ACTIVE_MISSION.md` persists across terminal kills and context fills; paste `@g-mission resume` into any fresh session to continue from the last checkpoint.
- **`@g-mission` drain queue scan order**: `open/` → `in-progress/` → `paused/`, priority `critical → high → medium → low`, lowest task ID first within same priority.

### Changed
- **`@g-mission` context checkpoint threshold raised to 75%**: previous behaviour could fire session checkpoints at ~33% context, leaving almost no usable capacity after startup overhead. Checkpoint now fires at 75% — finishes in-flight task, writes checkpoint cleanly, maximises work per session.

### Fixed
- **`@g-mission` scope-too-large is now a mandatory split, never a defer**: tasks the agent considers too big for one session are immediately decomposed into subtasks (`T{id}a/b/c`); the first slice is claimed and implemented in the same loop iteration. Writing a "deferred" summary and stopping is explicitly forbidden.
- **`@g-mission --until-empty` — cross-repo tasks no longer blanket-skipped**: tasks with `workspace_repos:` are now run after passing the Clean Controller Gate; they are only skipped if a required repo is inaccessible or has unrelated dirty paths. Previously all cross-repo tasks were skipped in `--until-empty` mode.
- **`@g-mission --until-empty` — queue-level assessment forbidden**: the agent must individually read every task in `open/`, `in-progress/`, and `paused/` before writing a session checkpoint. A global "the queue looks hard" assessment no longer qualifies as a completed scan.
- **Autonomous push gate (all `g-go` family workflows)**: no `g-go`, `g-go-code`, `g-go-review`, `g-go-go`, or `g-mission` run may silently push to remote. Push is offered once in the final summary; the agent pushes only after the user confirms.
- **Push offer now appears once, in the final summary only**: `g-mission`, `g-go`, `g-go-go`, `g-go-code`, and `g-go-review` no longer offer a push at every checkpoint, between tasks, or between swarm waves — only in the final completed/achieved summary.
- **`.gald3r/` gitignore gate for controller and PCAC-linked repos**: if an agent detects the repo is a Workspace-Control controller, a PCAC-linked project, or an active coordination repo and would write a broad `.gald3r/` gitignore entry, it now surfaces a plan-loss warning and asks YES/NO before proceeding. Gitignoring `.gald3r/` in a coordination repo means all tasks, bugs, plans, and PCAC topology become unrecoverable on a fresh clone.
- **`@g-mission --until-empty` soft-pauses now convert to skips**: `blast_radius:high`, cross-repo touches, design-judgment-required, and oversized scope all become logged skips in `--until-empty` mode instead of pausing the loop. Only `ai_safe:false` and PCAC `[ORDER]`/`[CONFLICT]` remain as true hard stops.
- **`@g-mission` session-end framing corrected**: session boundaries now produce a brief checkpoint row (`status: active`) with "Run `@g-mission resume` to continue" — not a "paused-partial Mission Report".

### Removed

---

## [1.5.1] - 2026-05-18 (README sync, personality packs, new commands)

### Added

- **Clean-room rewrite pipeline** (`g-skl-crr`, `@g-crr`): when external analysis output needs to be adapted to your codebase without importing external code directly, the clean-room pipeline guides the agent through a structured ideation-and-rewrite process. Output is original work derived from concepts, not copied code.

- **Semantic versioning and release management** (`g-skl-ship`, `@g-ship`): ship a versioned release from your `[Unreleased]` CHANGELOG entries. `@g-ship patch`, `@g-ship minor`, and `@g-ship major` promote entries, bump `VERSION`, update the README badge, create a git tag, and optionally publish a GitHub release. CHANGELOG entries are now written automatically at task completion and bug closure.

- **Incremental CHANGELOG maintenance**: task completion (`g-skl-tasks`) and bug closure (`g-skl-bugs`) now prompt for or automatically write `[Unreleased]` CHANGELOG entries at the point of completion. Release notes build continuously during development, not in a rush at release time.

- **Agent test skill** (`g-skl-test`, `@g-test`): create and maintain multi-level test plans (fast L1, comprehensive L2, regression L3). Enforces test plan discipline at code review and release gates.

- **Dependency graph skill** (`g-skl-dependency-graph`, `@g-dependency-graph`): generate and maintain `.gald3r/DEPENDENCY_GRAPH.md` from task dependency chains. Auto-updates when tasks are created or dependency fields change.

- **Subsystem graph skill** (`g-skl-subsystem-graph`, `@g-subsystem-graph`): generate `.gald3r/SUBSYSTEM_GRAPH.md` from subsystem spec dependency declarations.

- **PRD management** (`g-skl-prds`, `@g-prd-add`, `@g-prd-upd`, `@g-prd-del`, `@g-prd-revise`): formal product requirement document lifecycle alongside features. PRDs are governance/audit artifacts — `released` and `superseded` PRDs are frozen; only `@g-prd-revise` can change them.

- **PCAC send-to skill** (`g-skl-pcac-send-to`, `@g-pcac-send-to`): send files, features, specs, or code from the current project to any related project in the topology with INBOX notification and vault provenance logging.

- **PCAC notify skill** (`g-skl-pcac-notify`, `@g-pcac-notify`): send lightweight `[INFO]` notifications to one or more project inboxes — no task created, no approval needed.

- **PCAC order and cascade** (`g-skl-pcac-order`, `@g-pcac-order`): push tasks to child projects with configurable cascade depth (1–3). Creates tasks in child `.gald3r/` folders with INBOX notification.

- **SWOT review skill** (`g-skl-swot-review`, `@g-swot-review`): automated project-phase SWOT analysis covering goal alignment, architectural compliance, code quality, and technical debt. Run weekly via heartbeat or on-demand.

- **Medkit skill** (`g-skl-medkit`, `@g-medkit`): surgical repair for a specific `.gald3r/` file without running a full medic pass.

- **Constraint management** (`g-skl-constraints`, `@g-constraint-add`, `@g-constraint-del`, `@g-constraint-upd`, `@g-constraint-check`): formal architectural constraint lifecycle with expiry evaluation and enforcement definitions.

- **OpenClaw platform support** (`g-skl-platform-opencode`): extended platform skill coverage.

- **Skill execution capture hook** (`g-hk-session-start`): opt-in hook that captures which skills were invoked during a session and stages brief summaries for continual learning. Zero-touch when not opted in.

- **Git push [Unreleased] gate**: `@g-git-push` now shows an advisory prompt when `CHANGELOG.md` has non-empty `[Unreleased]` content, letting you ship a versioned release or continue pushing as-is.

### Changed

- **`g-skl-tasks` COMPLETE gate strengthened**: the docs check (step 2b) now explicitly walks you through writing a CHANGELOG entry in the correct format with the correct subsection (`### Added`, `### Changed`, `### Fixed`, `### Removed`). No more vague "append entry" instruction.

- **`g-skl-bugs` FIX gate strengthened**: bug closure now always writes a `### Fixed` entry to `CHANGELOG.md [Unreleased]`, with clean user-facing language and no internal BUG-NNN IDs in the entry.

- **`@g-git-push` pre-push gate**: now checks for non-empty `[Unreleased]` CHANGELOG content and offers an advisory versioning prompt. Non-blocking — continue or ship.

- **Workspace-Control command aliases**: `g-wrkspc-*` is the short primary family. `g-workspace-*` remains supported as a compatibility alias. Lifecycle commands are dry-run by default.

- **Archive commands** (`@g-task-archive`, `@g-bug-archive`): terminal task and bug history moves to `.gald3r/archive/` in count-bucket format. `TASKS.md` and `BUGS.md` stay as active indexes.

### Fixed

- Session-start hook path resolution corrected for all 5+ platform hooks.
- `@g-go-go` autopilot no longer stops early on complex tasks; all technically runnable tasks are attempted before giving up.

---

## [1.5.0] - 2026-05-16 (Platform Framework Architecture)

### Added

- **`.gald3r_sys/` Platform Framework Directory**: gald3r now owns its own platform namespace alongside `.claude/` (Anthropic), `.cursor/` (Cursor), `.codex/` (OpenAI), and `.copilot/` (GitHub). The `.gald3r_sys/` directory is the committed, release-versioned source of truth for all framework files — `skills/`, `agents/`, `commands/`, `rules/`, `hooks/`, `plugins/`, `workflows/`, and `VERSION`. Platform-specific IDE directories (`.cursor/`, `.claude/`, etc.) are **generated outputs**, never committed to your project's git. This cleanly separates your project state (`.gald3r/`) from the gald3r framework (`.gald3r_sys/`).

- **Smart installer** (`setup_gald3r_project.ps1`): new interactive installer for initial project setup and a non-interactive session-mode for ongoing platform directory regeneration. The installer detects whether the target is a new project, an existing project, or a previous version of gald3r and handles each case appropriately. Supports intelligent merging — `g-` prefixed framework files are always updated; your files are preserved unless you opt in.

- **21-platform coverage** (`setup_gald3r_project.ps1`): platform dirs can be generated for all 21 platforms: Cursor, Claude Code, Gemini/Antigravity, Codex, OpenCode, GitHub Copilot, Junie, Kiro, Roo, Windsurf, Cline, Augment, Aider, Goose, Warp, OpenHands, Replit, Qwen, OpenClaw, Mistral, and Agents (cross-client). Platform dirs are **never committed** — run the installer to regenerate them or let session-start hooks do it automatically.

- **Two-phase platform deploy**: platform directory population now runs in two phases: (1) copy the platform scaffold from `.gald3r_sys/platforms/{prefix}/` (hooks.json, settings.json, instruction files specific to each IDE), then (2) sync universal content from `.gald3r_sys/` central dirs (skills, agents, commands, rules with correct extension translation, hook scripts). You only get the platform dirs you explicitly activate.

- **New template layout** (`gald3r_template/` subfolder): all deployable content lives in `gald3r_template/` inside each template repo. The template repo root holds GitHub-level files (README, CHANGELOG, LICENSE) that describe the template itself. This separation makes it clear what is deployed to your project vs what is template repository metadata.

- **`docs/PLUGINS.md`**: plugin author guide covering skill pack structure, distribution, naming guidelines, and licensing options for third-party extensions.

- **External analysis safety gate** (`@g-res-apply`): before creating implementation tasks from any externally analyzed codebase, gald3r now compares the proposed approach against your existing implementation and your pending work queue. Features that would replace something you already have are classified as `replacement`-type and require explicit confirmation before any tasks are created.

- **Pre-implementation verification for analyzed features** (`@g-go`, `@g-go-code`): when the AI agent picks up a task sourced from external analysis, it pauses before coding to review relevant subsystem specs and scan the pending task queue for overlap. Replacement-class features block until you confirm the approach is genuinely superior (`recon_approved: true` in task frontmatter, or `--override` for automated pipelines).

### Fixed

- **AI agent autopilot reliability** (`@g-go-go`): the autopilot no longer stops early when it encounters tasks that appear complex or large. The fixed behavior requires the agent to attempt every technically-runnable task individually, fall back to controller-only mode before giving up on multi-repo tasks, and only stop when every task in the queue has a concrete, objectively-verifiable reason it cannot proceed.

### Changed

- **Installer renamed**: `setup_dev_env.ps1` is superseded by `setup_gald3r_project.ps1`. The new script supports new project init, existing project updates, and session-mode platform regeneration in one unified entry point.

### Removed

- Root-level platform directories (`.cursor/`, `.claude/`, `.agent/`, `.codex/`, `.opencode/`, `.copilot/`) are no longer committed inside the template repo. They are generated outputs produced by `setup_gald3r_project.ps1`. Run the installer or session-start hook to populate them in your project.

---

## [1.4.0] - 2026-04-14

### Added

- **GitHub Copilot support** (`.copilot/`): 6th IDE added to the parity set. Full command surface (89 commands) deployed to `.copilot/commands/`. gald3r now supports Cursor, Claude Code, Gemini, Codex, OpenCode, and GitHub Copilot.
- **Recon suite** (`g-skl-recon-repo`, `g-skl-recon-url`, `g-skl-recon-docs`, `g-skl-recon-yt`, `g-skl-recon-file`): unified research/reconnaissance skill family. Consolidates the prior external analysis and per-platform ingestion skills into a consistent `recon-*` namespace. Each skill produces a structured recon report for human review before any writes occur.
- **Research review/apply suite** (`g-skl-res-review`, `g-skl-res-deep`, `g-skl-res-apply`): three-step workflow — review a recon report, deep-dive on specific findings, then apply approved findings into `.gald3r/features/` staging. Supersedes the prior single-step external analysis apply workflow.
- **Release management skill** (`g-skl-release`, `@g-release-new`, `@g-release-assign`, `@g-release-status`, `@g-release-accelerate`, `@g-release-publish`): full release lifecycle from planning to publishing. Manages `.gald3r/releases/` and `.gald3r/RELEASES.md`.
- **Platform skills** (`g-skl-platform-cursor`, `g-skl-platform-claude`, `g-skl-platform-gemini`, `g-skl-platform-codex`, `g-skl-platform-opencode`, `g-skl-platform-copilot`): per-IDE platform reference skills.
- **Medic skill** (`g-skl-medic`, `@g-medic`): targeted surgical repair for a specific `.gald3r/` file or subsystem.
- **Tier setup skill** (`g-skl-tier-setup`, `@g-tier-setup`): upgrade a project's gald3r installation tier (slim → full → adv) without losing existing state.
- **Codex CLI skill** (`g-skl-cli-codex`): dedicated reference skill for Codex terminal-first operation.
- **Copilot CLI skill** (`g-skl-cli-copilot`): dedicated reference skill for GitHub Copilot terminal-first operation.
- **Swarm commands** (`@g-go-swarm`, `@g-go-code-swarm`, `@g-go-review-swarm`): multi-agent coordinated execution across the backlog.
- **Vault process-inbox command** (`@g-vault-process-inbox`): process pending vault inbox items.
- **`.gald3r/releases/`** directory, **`.gald3r/release_profiles/`** directory, and **`.gald3r/RELEASES.md`** index: new release tracking structure.
- **`.gald3r/logs/`** directory: session log storage.
- **`ROADMAP.md`**: project roadmap file at repo root.
- **`raw-inbox-watcher.ps1`** hook: real-time PCAC inbox watcher.

### Changed

- External analysis and ingestion skills migrated to `recon-*` namespace (`g-skl-recon-repo`, `g-skl-recon-docs`, `g-skl-recon-url`, `g-skl-recon-yt`, `g-skl-recon-file`). Prior per-platform ingestion skills unified under consistent naming.
- External analysis apply skill migrated to `res-*` workflow (`g-skl-res-review` → `g-skl-res-deep` → `g-skl-res-apply`). Three discrete stages replace the former single-step apply.
- `g-skl-ingest-docs` → `g-skl-recon-docs`: unified into recon namespace.
- `g-skl-ingest-url` → `g-skl-recon-url`: unified into recon namespace.
- `g-skl-ingest-youtube` → `g-skl-recon-yt`: unified into recon namespace.
- README: IDE parity updated from 5 → 6 IDEs (12 parity targets). Skills 49 → 58, Commands 78 → 89.
- `g-skl-medkit` version migration updated to include 1.2 → 1.4 path.

### Removed

- Prior external analysis skill directories (superseded by `g-skl-recon-repo` + `g-skl-res-review` / `g-skl-res-deep` / `g-skl-res-apply`)
- `g-skl-ingest-docs`, `g-skl-ingest-url`, `g-skl-ingest-youtube` skill directories (superseded by `recon-*` family)
- Corresponding legacy ingestion and analysis commands (superseded by `@g-recon-*` and `@g-res-*` families)

---

## [1.3.0] - *not released*

*Version 1.3.0 was not shipped as a standalone release. Content that would have been 1.3.0 was folded into the 1.4.0 release.*

---

## [1.2.1] - 2026-04-14

### Added

- **PCAC Spawn skill** (`g-skl-pcac-spawn`, `@g-pcac-spawn`): spawn a new gald3r project from the current one — creates the project folder in the ecosystem root, installs gald3r (matching current project's install style), seeds it with an optional description/features/code, runs subsystem discovery, and registers bidirectional PCAC topology links in both projects. Supports `--sibling`, `--child`, `--parent`, and `--dry-run`.
- **PCAC Send-To skill** (`g-skl-pcac-send-to`, `@g-pcac-send-to`): transfer files, features, specs, ideas, bugs, or code from the current project to any related project in the topology. Lighter-weight than `g-skl-pcac-move`. Supports `--type features|code|ideas|bugs|docs|spec`, `--delete-source`, and `--dry-run`.
- Both skills deployed across all 5 IDE trees (`.cursor`, `.claude`, `.agent`, `.codex`, `.opencode`) with full parity.

---

## [1.2.0] - 2026-04-11

### Added

- **Feature pipeline** (`g-skl-features`, `FEATURES.md`, `.gald3r/features/`): structured staging layer between idea capture and task creation. Features move through `staging → specced → committed → shipped`. Only reach the TASKS.md backlog when explicitly promoted via `@g-feat-promote`. Prevents backlog pollution and keeps implementation intent explicit.
- **Deep recon skill** (`g-skl-recon-repo`, `@g-recon-repo`): deep 5-pass analysis of any external repository. Produces a structured recon report in `research/recon/{slug}/` with skeleton, module map, feature scan, deep dives, and synthesis passes. Human reviews and marks features `[✓] approved` before APPLY writes to `.gald3r/features/`.
- **Analysis apply skill** (`g-skl-res-apply`, `@g-res-apply`): processes approved recon output into `.gald3r/features/` staging entries. Deduplicates against existing staging features.
- **Subsystem graph skill** (`g-skl-subsystem-graph`, `@g-subsystem-graph`): generates a visual Mermaid dependency graph of all registered subsystems with dependency annotations.
- **IDE CLI skills** (`g-skl-cli-cursor`, `g-skl-cli-claude`, `g-skl-cli-gemini`, `g-skl-cli-opencode`): dedicated reference skills for headless and terminal-first operation of each supported IDE.
- **Granular task commands** (`@g-task-add`, `@g-task-upd`, `@g-task-del`): fine-grained task operations to supplement the existing `@g-task-new` and `@g-task-update` commands.
- **Granular bug commands** (`@g-bug-add`, `@g-bug-upd`, `@g-bug-del`): fine-grained bug management.
- **Granular constraint commands** (`@g-constraint-upd`, `@g-constraint-del`): update and delete constraints in `CONSTRAINTS.md`.
- **Granular subsystem commands** (`@g-subsystem-add`, `@g-subsystem-upd`, `@g-subsystem-del`, `@g-subsystem-graph`): full CRUD surface for the subsystem registry.
- **Feature commands** (`@g-feat-new`, `@g-feat-add`, `@g-feat-upd`, `@g-feat-promote`, `@g-feat-rename`, `@g-feat-del`): full feature lifecycle management from the command surface.
- **IDE CLI commands** (`@g-cli-cursor`, `@g-cli-claude`, `@g-cli-gemini`): quick reference commands for each IDE's CLI usage patterns.

### Changed

- `g-go-verify` renamed to `@g-go-review` — clearer intent (this is the review/verification phase, not a QA pass). Old command name removed from all IDE directories.
- `g-skl-cursor-cli`, `g-skl-claude-cli`, `g-skl-gemini-cli`, `g-skl-opencode-cli` renamed to `g-skl-cli-cursor`, `g-skl-cli-claude`, `g-skl-cli-gemini`, `g-skl-cli-opencode` — consistent `g-skl-cli-*` namespace pattern.
- `g-skl-plan` updated: `features/` replaces `prds/` as the primary deliverable directory.
- External analysis apply skill updated: `APPLY` operation now calls `g-skl-features COLLECT` to dedup against existing staging features instead of creating tasks directly.
- `g-skl-medkit` updated: detects projects with `prds/` folder and no `features/` folder — offers migration path to 1.2.0 feature pipeline.
- README: updated component counts (Skills: 39 → 47, Commands: 52 → 76, Skill Packs: 6 → 7), added Feature Pipeline section.

### Removed

- `g-claude-cli.md`, `g-cursor-cli.md`, `g-gemini-cli.md` commands (superseded by `g-cli-*.md` namespace)
- `g-go-verify.md` command (superseded by `g-go-review.md`)
- `g-skl-claude-cli`, `g-skl-cursor-cli`, `g-skl-gemini-cli`, `g-skl-opencode-cli` skill directories

---

## [1.1.0] - 2026-04-08

### Added

- **Task circuit breaker** (`[⚠️]` Requires-User-Attention): tasks that fail verification 3 or more times are automatically escalated for human review. Automated agents skip them and they remain visible in the backlog until a human resets or cancels.
- **Status History table** on all task and bug files: every state transition records a timestamp, from-state, to-state, and reason. Creates a full audit trail for every item in the backlog.
- **Re-work surface at session start**: if a task's last Status History entry is a FAIL, it is flagged at session start so the implementing agent knows what to watch for before starting.
- **Pre-push gate** (`@g-git-push`, `scripts/gald3r_push_gate.ps1`): validates that tasks are in the correct state, CHANGELOG is updated, and no staged secrets are present before allowing a push to reach the remote.
- **Pre-commit sanity check** (`@g-git-sanity`): detects staged secrets, files over size limits, and `.gald3r/` sync drift before a commit is created.
- **Architectural constraints skill** (`g-skl-constraints`): dedicated ADD, UPDATE, CHECK, and LIST operations for `CONSTRAINTS.md`. Constraints are validated at session start and before marking any task complete.
- **Knowledge vault Obsidian compliance**: standardized frontmatter schema (type, topics, date, source), type registry, tag taxonomy, and encoding rules.
- **MOC hub generation** (`gen_vault_moc.py`): automatically generates `_INDEX.md` navigation files for vault directories with 10 or more notes.
- **Platform documentation crawling** (`g-skl-ingest-docs`): schedule-aware ingestion with per-platform freshness tracking.
- **Native web crawler** (`g-skl-crawl`): crawl4ai integration for clean LLM-optimized markdown extraction without Docker.
- **URL ingestion** (`g-skl-ingest-url`): one-time article and page capture into the vault.
- **YouTube transcript ingestion** (`g-skl-ingest-youtube`): offline transcript extraction via yt-dlp. Stores in `research/videos/`.
- **Vault management skill** (`g-skl-vault`): unified vault operations including Obsidian compatibility tools, MOC rebuild, frontmatter linting, and GitHub repo summaries.
- **Continual learning skill** (`g-skl-learn`): agents self-report insights to vault memory files after each session.
- **Health and repair skill** (`g-skl-medkit`): single skill that detects what a `.gald3r/` directory needs (version migration, structural repair, or routine maintenance) and performs it.
- **Platform crawl skill** (`g-platform-crawl`): dedicated skill for crawling Cursor, Claude Code, Gemini, and other platform documentation with configurable targets.
- **Dependency graph** (`g-skl-dependency-graph`): auto-generates `.gald3r/DEPENDENCY_GRAPH.md` from task file dependencies.
- **SWOT review skill** (`g-skl-swot-review`): automated SWOT analysis for the current project phase.
- **Verify ladder skill** (`g-skl-verify-ladder`): configurable multi-level verification gates from minimal (lint only) to thorough (tests + acceptance + hallucination guard).
- **Knowledge refresh skill** (`g-skl-knowledge-refresh`): audit vault freshness, rebuild compiled pages, detect broken links and stale notes.

### Changed

- `g-go-code` now requires a Status History entry before marking any item `[🔍]`. The b3 step is mandatory.
- `g-go-review` FAIL path now counts FAIL rows in Status History to determine whether to reset to `[📋]` or escalate to `[⚠️]`.
- Session start protocol (step 2) now surfaces re-work tasks when the last Status History entry is a FAIL.
- `g-skl-tasks` and `g-skl-bugs` templates include Status History section.

### Fixed

- Session hook (`g-hk-agent-complete.ps1`): `$input` pipeline variable does not capture external-process stdin in PowerShell. Fixed to use `[Console]::In.ReadToEnd()`. Status mapping corrected from `"success"` to `"completed"` per Cursor hook schema.
- `pending_reflection.json` was never written when the session hook ran in a non-interactive terminal. Fixed `[Console]::IsInputRedirected` guard.

---

## [1.0.0] - 2026-04-04

### Added

- **Task management system**: YAML frontmatter task specs with sequential IDs, priority, dependencies, and subsystem tracking. Master `TASKS.md` checklist with per-file status sync.
- **Two-phase adversarial code review** (`@g-go-code` / `@g-go-review`): implementation and verification are separated into distinct agent sessions. The implementing agent marks `[🔍]`; a separate agent marks `[✅]`. Neither can do both.
- **Five-IDE parity**: identical agents, skills, commands, and rules across Cursor (`.cursor/`), Claude Code (`.claude/`), Gemini (`.agent/`), Codex (`.codex/`), and OpenCode (`.opencode/`).
- **PCAC cross-project topology**: projects declare parent, child, and sibling relationships. Parents broadcast tasks (`@g-pcac-order`). Children request actions (`@g-pcac-ask`). Siblings sync shared contracts (`@g-pcac-sync`). Cross-project INBOX tracks all coordination items.
- **Knowledge vault**: file-based knowledge store for session summaries, research notes, architectural decisions, and platform documentation. Vault notes use standardized YAML frontmatter.
- **Session start protocol**: reads `.gald3r/` state at session start, validates task sync, surfaces open bugs, checks for specification files, and displays project context in a structured summary.
- **Bug tracking**: sequential BUG-NNN IDs, severity classification (Critical/High/Medium/Low), `BUGS.md` index, individual bug spec files, and code annotation format (`BUG[BUG-NNN]: description`).
- **Architectural constraints** (`CONSTRAINTS.md`): non-negotiable project rules loaded at every session start. Agents flag violations before proceeding.
- **Subsystem registry** (`SUBSYSTEMS.md`, `subsystems/`): each subsystem has a spec file with locations, dependencies, dependents, and an Activity Log. Agents update the Activity Log on task completion.
- **9 gald3r system agents**: task-manager, qa-engineer, code-reviewer, project, infrastructure, ideas-goals, verifier, project-initializer, pcac-coordinator.
- **Docker MCP server** (42 tools): RAG search, Oracle SQL, MediaWiki, vault indexing, session memory capture and retrieval, video analysis, platform crawling, and project health reports.
- **Continual learning**: agents extract durable facts from conversation transcripts and persist them in `AGENTS.md`.
- **TODO lifecycle enforcement**: stubs and TODOs must be annotated with `TODO[TASK-X→TASK-Y]` format and a follow-up task created before the implementing task can be marked complete.
- **Bug discovery gate**: pre-existing bugs encountered during implementation must have a BUG entry and code annotation before the task is marked `[🔍]`.
- **Git commit skill** (`g-skl-git-commit`): conventional commit format with task references.
- **Project planning** (`g-skl-plan`, `g-skl-project`): PLAN.md (milestones and deliverables), PROJECT.md (mission, vision, goals), PRD files, and CONSTRAINTS.md.
- **Code review** (`g-skl-code-review`): structured review covering security, performance, maintainability, and architectural alignment.
- **External analysis skill** (`g-skl-res-review`): analyze external repositories for adoptable patterns and improvements.

---

*gald3r is built with gald3r. The development history of this framework lives in the gald3r_dev source repository.*