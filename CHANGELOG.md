# Changelog

All notable changes to gald3r are documented here.
Format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).
gald3r uses [Semantic Versioning](https://semver.org/).

---

## [Unreleased]

### Added

- `docs/PLUGINS.md`: plugin author guide covering skill pack structure, distribution, naming guidelines, and licensing options for third-party extensions.
- README "Plugins & Skill Packs" section with naming guideline and licensing clarification (plugins are separate works, any license allowed).
- NOTICE clarified with plain-language license summary and plugin naming guideline.

### Changed

- **License changed from MIT to Fair Source License 1.1 with Apache 2.0 future grant (FSL-1.1-Apache).**
  - gald3r remains source-available and free to use, modify, and redistribute for any purpose except a Competing Use (offering gald3r itself as a commercial product or service that substitutes for, or substantially duplicates, gald3r).
  - Individual, internal, and commercial downstream use (using gald3r to build your own products and services) is fully permitted.
  - Plugin and skill pack authors retain full rights to their own work under any license.
  - Each version automatically converts to Apache 2.0 on its second anniversary, providing a rolling transition to fully open source.
  - See LICENSE for the full license text and README.md for a plain-language summary.
- README: License badge updated from `License-MIT` to `License-FSL-1.1-Apache`.
- Repository history was reset as part of the license transition. Previous MIT-licensed history is available in the pre-reset backup branch on the maintainer's local clone.

### Removed

---

## [1.4.0] - 2026-04-14

### Added

- **GitHub Copilot support** (`.copilot/`): 6th IDE added to the parity set. Full command surface (89 commands) deployed to `.copilot/commands/`. gald3r now supports Cursor, Claude Code, Gemini, Codex, OpenCode, and GitHub Copilot.
- **Recon suite** (`g-skl-recon-repo`, `g-skl-recon-url`, `g-skl-recon-docs`, `g-skl-recon-yt`, `g-skl-recon-file`): unified research/reconnaissance skill family. Replaces the separate `g-skl-reverse-spec`, `g-skl-ingest-docs`, `g-skl-ingest-url`, `g-skl-ingest-youtube`, and `g-skl-harvest` skills with a consistent `recon-*` namespace. Each produces a structured recon report for human review before any writes occur.
- **Research review/apply suite** (`g-skl-res-review`, `g-skl-res-deep`, `g-skl-res-apply`): three-step workflow — review a recon report, deep-dive on specific findings, then apply approved findings into `.gald3r/features/` staging. Replaces `g-skl-harvest-intake`.
- **Release management skill** (`g-skl-release`, `@g-release-new`, `@g-release-assign`, `@g-release-status`, `@g-release-accelerate`, `@g-release-publish`): full release lifecycle from planning to publishing. Manages `.gald3r/releases/` and `.gald3r/RELEASES.md`.
- **Platform skills** (`g-skl-platform-cursor`, `g-skl-platform-claude`, `g-skl-platform-gemini`, `g-skl-platform-codex`, `g-skl-platform-opencode`, `g-skl-platform-copilot`): per-IDE platform reference skills for understanding each IDE's agent model, permission system, and tool surface.
- **Medic skill** (`g-skl-medic`, `@g-medic`): targeted surgical repair for a specific `.gald3r/` file or subsystem, complementing `g-skl-medkit` (which does full-project health checks).
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

- `g-skl-reverse-spec` → `g-skl-recon-repo`: renamed and expanded. The recon namespace (`recon-*`) supersedes the ad-hoc harvest/ingest/reverse-spec naming.
- `g-skl-harvest-intake` → `g-skl-res-apply`: part of the three-step res-* workflow (res-review → res-deep → res-apply).
- `g-skl-ingest-docs` → `g-skl-recon-docs`: unified into recon namespace.
- `g-skl-ingest-url` → `g-skl-recon-url`: unified into recon namespace.
- `g-skl-ingest-youtube` → `g-skl-recon-yt`: unified into recon namespace.
- `g-skl-harvest` → subsumed by `g-skl-recon-repo` + `g-skl-res-review`.
- README: IDE parity updated from 5 → 6 IDEs (12 parity targets). Skills 49 → 58, Commands 78 → 89.
- `g-skl-medkit` version migration updated to include 1.2 → 1.4 path.

### Removed

- `g-skl-harvest`, `g-skl-harvest-intake` skill directories (superseded by recon-* / res-* suites)
- `g-skl-ingest-docs`, `g-skl-ingest-url`, `g-skl-ingest-youtube` skill directories (superseded by recon-*)
- `g-skl-reverse-spec` skill directory (superseded by `g-skl-recon-repo`)
- Corresponding commands: `@g-harvest`, `@g-harvest-intake`, `@g-ingest-docs`, `@g-ingest-url`, `@g-ingest-youtube`, `@g-reverse-spec`

---

## [1.2.1] - 2026-04-14

### Added

- **PCAC Spawn skill** (`g-skl-pcac-spawn`, `@g-pcac-spawn`): spawn a new gald3r project from the current one — creates the project folder in the ecosystem root, installs gald3r (matching current project's install style), seeds it with an optional description/features/code, runs subsystem discovery, and registers bidirectional PCAC topology links in both projects. Supports `--sibling`, `--child`, `--parent`, and `--dry-run`.
- **PCAC Send-To skill** (`g-skl-pcac-send-to`, `@g-pcac-send-to`): transfer files, features, specs, ideas, bugs, or code from the current project to any related project in the topology. Lighter-weight than `g-skl-pcac-move` — works with freshly spawned projects, writes an INBOX notification in the destination, and logs provenance in the source vault. Supports `--type features|code|ideas|bugs|docs|spec`, `--delete-source`, and `--dry-run`.
- Both skills deployed across all 5 IDE trees (`.cursor`, `.claude`, `.agent`, `.codex`, `.opencode`) with full parity.

---

## [1.2.0] - 2026-04-14

### Added

- **Feature pipeline** (`g-skl-features`, `FEATURES.md`, `.gald3r/features/`): structured staging layer between idea capture and task creation. Features move through `staging → specced → committed → shipped`. Only reach the TASKS.md backlog when explicitly promoted via `@g-feat-promote`. Prevents backlog pollution and keeps implementation intent explicit.
- **Reverse-spec skill** (`g-skl-reverse-spec`, `@g-reverse-spec`): deep 5-pass analysis of any external repository. Produces a structured harvest report in `research/harvests/{slug}/` with skeleton, module map, feature scan, deep dives, and synthesis passes. Human reviews and marks features `[✅] approved` before APPLY writes to `.gald3r/features/`.
- **Harvest intake skill** (`g-skl-harvest-intake`, `@g-harvest-intake`): processes approved harvest output into `.gald3r/features/` staging entries. Deduplicates against existing staging features — appends a Collected Approach rather than creating a duplicate.
- **Subsystem graph skill** (`g-skl-subsystem-graph`, `@g-subsystem-graph`): generates a visual Mermaid dependency graph of all registered subsystems with dependency annotations.
- **IDE CLI skills** (`g-skl-cli-cursor`, `g-skl-cli-claude`, `g-skl-cli-gemini`, `g-skl-cli-opencode`): dedicated reference skills for headless and terminal-first operation of each supported IDE. Cover agent mode, Cloud Agent handoff, API mode, session continuation, MCP config, checkpointing, and multi-agent patterns.
- **Granular task commands** (`@g-task-add`, `@g-task-upd`, `@g-task-del`): fine-grained task operations to supplement the existing `@g-task-new` and `@g-task-update` commands.
- **Granular bug commands** (`@g-bug-add`, `@g-bug-upd`, `@g-bug-del`): fine-grained bug management to complement `@g-bug-report` and `@g-bug-fix`.
- **Granular constraint commands** (`@g-constraint-upd`, `@g-constraint-del`): update and delete constraints in `CONSTRAINTS.md`.
- **Granular subsystem commands** (`@g-subsystem-add`, `@g-subsystem-upd`, `@g-subsystem-del`, `@g-subsystem-graph`): full CRUD surface for the subsystem registry.
- **Feature commands** (`@g-feat-new`, `@g-feat-add`, `@g-feat-upd`, `@g-feat-promote`, `@g-feat-rename`, `@g-feat-del`): full feature lifecycle management from the command surface.
- **IDE CLI commands** (`@g-cli-cursor`, `@g-cli-claude`, `@g-cli-gemini`): quick reference commands for each IDE's CLI usage patterns.

### Changed

- `g-go-verify` renamed to `@g-go-review` — clearer intent (this is the review/verification phase, not a QA pass). Old command name removed from all IDE directories.
- `g-skl-cursor-cli`, `g-skl-claude-cli`, `g-skl-gemini-cli`, `g-skl-opencode-cli` renamed to `g-skl-cli-cursor`, `g-skl-cli-claude`, `g-skl-cli-gemini`, `g-skl-cli-opencode` — consistent `g-skl-cli-*` namespace pattern. Old skill directories removed.
- `g-skl-plan` updated: `features/` replaces `prds/` as the primary deliverable directory. PRD concepts live inside feature spec files.
- `g-skl-harvest` updated: `APPLY` operation now calls `g-skl-features COLLECT` to dedup against existing staging features instead of creating tasks directly.
- `g-skl-medkit` updated: detects projects with `prds/` folder and no `features/` folder — offers migration path to 1.2.0 feature pipeline.
- README: updated component counts (Skills: 39 → 47, Commands: 52 → 76, Skill Packs: 6 → 7), added Feature Pipeline section, updated directory tree to show `features/`, updated all skill and command references.

### Removed

- `g-claude-cli.md`, `g-cursor-cli.md`, `g-gemini-cli.md` commands (superseded by `g-cli-claude.md`, `g-cli-cursor.md`, `g-cli-gemini.md`)
- `g-go-verify.md` command (superseded by `g-go-review.md`)
- `g-skl-claude-cli`, `g-skl-cursor-cli`, `g-skl-gemini-cli`, `g-skl-opencode-cli` skill directories (superseded by `g-skl-cli-*` namespace)

---

## [1.1.0] - 2026-04-08

### Added

- **Task circuit breaker** (`[🚨]` Requires-User-Attention): tasks that fail verification 3 or more times are automatically escalated for human review. Automated agents skip them and they remain visible in the backlog until a human resets or cancels.
- **Status History table** on all task and bug files: every state transition records a timestamp, from-state, to-state, and reason. Creates a full audit trail for every item in the backlog.
- **Re-work surface at session start**: if a task's last Status History entry is a FAIL, it is flagged at session start so the implementing agent knows what to watch for before starting.
- **Pre-push gate** (`@g-git-push`, `scripts/gald3r_push_gate.ps1`): validates that tasks are in the correct state, CHANGELOG is updated, and no staged secrets are present before allowing a push to reach the remote.
- **Pre-commit sanity check** (`@g-git-sanity`): detects staged secrets, files over size limits, and `.gald3r/` sync drift before a commit is created.
- **Architectural constraints skill** (`g-skl-constraints`): dedicated ADD, UPDATE, CHECK, and LIST operations for `CONSTRAINTS.md`. Constraints are validated at session start and before marking any task complete.
- **Knowledge vault Obsidian compliance**: standardized frontmatter schema (type, topics, date, source), type registry, tag taxonomy, and encoding rules. All vault notes now comply with Obsidian's native indexing format.
- **MOC hub generation** (`gen_vault_moc.py`): automatically generates `_INDEX.md` navigation files for vault directories with 10 or more notes. Creates wikilinks that show connections in Obsidian graph view.
- **Platform documentation crawling** (`g-skl-ingest-docs`): schedule-aware ingestion with per-platform freshness tracking. Stale docs are flagged at session start.
- **Native web crawler** (`g-skl-crawl`): crawl4ai integration for clean LLM-optimized markdown extraction without Docker. Shared primitive used by ingest-docs, ingest-url, and harvest.
- **URL ingestion** (`g-skl-ingest-url`): one-time article and page capture into the vault with frontmatter and deduplication by source URL.
- **YouTube transcript ingestion** (`g-skl-ingest-youtube`): offline transcript extraction via yt-dlp. Stores in `research/videos/` with full frontmatter compliance.
- **Vault management skill** (`g-skl-vault`): unified vault operations including Obsidian compatibility tools, MOC rebuild, frontmatter linting, and GitHub repo summaries.
- **Continual learning skill** (`g-skl-learn`): agents self-report insights to vault memory files after each session. No external services required — file-only persistence.
- **Health and repair skill** (`g-skl-medkit`): single skill that detects what a `.gald3r/` directory needs (version migration, structural repair, or routine maintenance) and performs it. Replaces the separate g-cleanup, g-grooming, and g-upgrade skills.
- **Platform crawl skill** (`g-platform-crawl`): dedicated skill for crawling Cursor, Claude Code, Gemini, and other platform documentation with configurable targets.
- **Dependency graph** (`g-skl-dependency-graph`): auto-generates `.gald3r/DEPENDENCY_GRAPH.md` from task file dependencies. Shows blocked and blocking relationships.
- **SWOT review skill** (`g-skl-swot-review`): automated SWOT analysis for the current project phase. Reviewsprogress, architectural compliance, code quality, and technical debt.
- **Verify ladder skill** (`g-skl-verify-ladder`): configurable multi-level verification gates from minimal (lint only) to thorough (tests + acceptance + hallucination guard).
- **Knowledge refresh skill** (`g-skl-knowledge-refresh`): audit vault freshness, rebuild compiled pages, detect broken links and stale notes.

### Changed

- `g-go-code` now requires a Status History entry before marking any item `[🔍]`. The b3 step is mandatory.
- `g-go-review` FAIL path now counts FAIL rows in Status History to determine whether to reset to `[📋]` or escalate to `[🚨]`.
- `g-go-code` skips `[🚨]` items entirely — logs them in the Skipped section as Requires-User-Attention.
- Session start protocol (step 2) now surfaces re-work tasks when the last Status History entry is a FAIL.
- `g-skl-tasks` and `g-skl-bugs` templates include Status History section. Every status transition appends a row.

### Fixed

- Session hook (`g-hk-agent-complete.ps1`): `$input` pipeline variable does not capture external-process stdin in PowerShell. Fixed to use `[Console]::In.ReadToEnd()`. Status mapping corrected from `"success"` to `"completed"` per Cursor hook schema.
- `pending_reflection.json` was never written when the session hook ran in a non-interactive terminal. Fixed `[Console]::IsInputRedirected` guard to prevent blocking on `ReadToEnd()`.

---

## [1.0.0] - 2026-04-04

### Added

- **Task management system**: YAML frontmatter task specs with sequential IDs, priority, dependencies, and subsystem tracking. Master `TASKS.md` checklist with per-file status sync.
- **Two-phase adversarial code review** (`@g-go-code` / `@g-go-verify`): implementation and verification are separated into distinct agent sessions. The implementing agent marks `[🔍]`; a separate agent marks `[✅]`. Neither can do both.
- **Five-IDE parity**: identical agents, skills, commands, and rules across Cursor (`.cursor/`), Claude Code (`.claude/`), Gemini (`.agent/`), Codex (`.codex/`), and OpenCode (`.opencode/`).
- **PCAC cross-project topology**: projects declare parent, child, and sibling relationships. Parents broadcast tasks (`@g-pcac-order`). Children request actions (`@g-pcac-ask`). Siblings sync shared contracts (`@g-pcac-sync`). Cross-project INBOX tracks all coordination items.
- **Knowledge vault**: file-based knowledge store for session summaries, research notes, architectural decisions, and platform documentation. Vault notes use standardized YAML frontmatter.
- **Session start protocol**: reads `.gald3r/` state at session start, validates task sync, surfaces open bugs, checks for specification files, and displays project context in a structured summary.
- **Bug tracking**: sequential BUG-NNN IDs, severity classification (Critical/High/Medium/Low), `BUGS.md` index, individual bug spec files, and code annotation format (`BUG[BUG-NNN]: description`).
- **Architectural constraints** (`CONSTRAINTS.md`): non-negotiable project rules loaded at every session start. Agents flag violations before proceeding.
- **Subsystem registry** (`SUBSYSTEMS.md`, `subsystems/`): each subsystem has a spec file with locations, dependencies, dependents, and an Activity Log. Agents update the Activity Log on task completion.
- **9 gald3r system agents**: task-manager, qa-engineer, code-reviewer, project, infrastructure, ideas-goals, verifier, project-initializer, pcac-coordinator.
- **Docker MCP server** (42 tools): RAG search, Oracle SQL, MediaWiki, vault indexing, session memory capture and retrieval, video analysis, platform crawling, and project health reports.
- **Continual learning**: agents extract durable facts from conversation transcripts and persist them in `AGENTS.md`. Agents remember preferences, project conventions, and past decisions across sessions.
- **TODO lifecycle enforcement**: stubs and TODOs must be annotated with `TODO[TASK-X→TASK-Y]` format and a follow-up task created before the implementing task can be marked complete.
- **Bug discovery gate**: pre-existing bugs encountered during implementation must have a BUG entry and code annotation before the task is marked `[🔍]`.
- **Git commit skill** (`g-skl-git-commit`): conventional commit format with task references and agent footers.
- **Project planning** (`g-skl-plan`, `g-skl-project`): PLAN.md (milestones and deliverables), PROJECT.md (mission, vision, goals), PRD files, and CONSTRAINTS.md.
- **Code review** (`g-skl-code-review`): structured review covering security, performance, maintainability, and architectural alignment. Severity-classified output with file/line references.
- **Harvest skill** (`g-skl-harvest`): analyze external repositories for adoptable patterns and improvements. Zero-change-without-approval output.

---

*gald3r is built with gald3r. The development history of this framework lives in the gald3r_dev source repository.*
