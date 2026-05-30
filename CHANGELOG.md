# Changelog

All notable changes to gald3r are documented here.
Format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).
gald3r uses [Semantic Versioning](https://semver.org/).

---

## [Unreleased]

### Fixed
- **BUG-099 safety fix**: All platform scaffold `gald3r_worktree.ps1` scripts and `development.yaml` files defaulted `TargetBranch`/`default_branch` to `dev` instead of `main`. This caused new projects created from any platform template to target a long-lived `dev` branch for worktree merges — a data-loss trap. Flipped 78 files (44 worktree scripts + 34 development.yaml) to `main`. Affects all 34+ platform scaffolds.

---

## [1.7.0] - 2026-05-28 (Workspace Distribution + Swarm Fix + 34-Platform Sweep)

### Changed

- **Public-face restructure (T1522)**: The 23 ready-to-deploy platform templates moved from `platforms/<name>/` to `<name>/` directly at repo root. The standalone `platforms/README.md` matrix was removed (the platform comparison matrix lives in the main `README.md` per T1515). Removed internal/build artifacts that polluted the public view: `.cursor/`, `.claude/`, `.agent/`, `.codex/`, `.opencode/`, `.copilot/`, `.gald3r/`, `gald3r_template/`, `docs/`, `scripts/`, `AGENTS.md`, `CLAUDE.md`, `GEMINI.md`, `GUARDRAILS.md`, `.claudeignore`, `.cursorignore`, `opencode.json`. Added `instructions_new_project.md` + `instructions_existing_project.md` covering the two audiences. The hero `README.md` was rewritten as a discovery-first document (no internal-tool references).
- **Per-platform README templates fixed (T1522 iter 2)**: Original 23 platform READMEs (`cursor/`, `claude/`, etc.) updated for the new flat layout -- install instruction says `Copy the contents of <name>/` (not `platforms/<name>/`); cross-links use `../README.md` and `../CHANGELOG.md` (not `../../`); removed the stale `Platform comparison matrix` link (matrix now lives in main `README.md`). The 11 newer platform READMEs (T1523/T1524/T1525 -- `amp/`, `astrbot/`, `codebuddy/`, `continue/`, `deepcode/`, `hermes/`, `kilo-code/`, `kimi/`, `qoder/`, `trae/`, `void/`) were authored with the correct flat-layout patterns from the start and were not touched in this commit.

### Added

- **Platform Support section in README with tier matrix (T1515).** New top-level `## Platform Support (23 AI Coding Tools)` section listing all 23 platforms with shields.io tier badges (Tier 1 = green, Tier 2 = yellow, Tier 3 = orange), tier definitions, install steps, and per-platform folder links. Tier distribution: 8 Tier 1 (Claude Code, Cline, OpenAI Codex, GitHub Copilot, Cursor, opencode.ai, Roo Code, Windsurf), 10 Tier 2 (Aider, Augment, Gemini, Goose, Junie, Kiro, Kiro CLI, OpenHands, Replit AI, Warp), 5 Tier 3 (Antigravity, Mistral, OpenClaw, Qwen, SubQ). (T1521-era `platforms/<name>/` paths superseded by T1522 root-level layout; the `## Platform Support` section's table links are accurate for the flat layout.)
- "6-IDE parity" feature bullet updated to "23-platform parity" with full list.
- `What's Included` table updated: `IDE Platforms | 6 | ...` row replaced with `Platforms | 23 | See Platform Support` cross-link.
- `docs/PLUGINS.md`: plugin author guide covering skill pack structure, distribution, naming guidelines, and licensing options for third-party extensions.
- README "Plugins & Skill Packs" section with naming guideline and licensing clarification (plugins are separate works, any license allowed).
- NOTICE clarified with plain-language license summary and plugin naming guideline.

---

## [1.6.0] - 2026-05-25 (WPAC v1.6, Schema System, Ship Skill)

### Added

- **Schema enforcement system**: every `.gald3r/` file now carries version provenance, validated against 15 versioned schema definitions. A read-only session-start probe flags drift in under a second, and a data-preserving migration engine (`migrate_schemas.ps1`) upgrades older files in place. `g-medic` gained an L1 validation layer that auto-fixes common schema gaps.
- **Semantic versioning and release management** (`g-skl-ship`, `@g-ship`): promotes the CHANGELOG `[Unreleased]` section to a versioned release -- bumps `VERSION`, tags the release, and can publish. Task and bug completion feed CHANGELOG entries automatically.
- **Dedicated bug-fix pipeline** (`@g-go-bugs`, `@g-go-bugs-swarm`): an autopilot built only for bugs -- reproduce, fix, regression test, adversarial review -- working through the backlog in severity order (critical first).
- **Encoding normalization** (`g-hk-encoding-normalize`): pre-commit and stop-event hook that normalizes line endings and BOM policy, with a content-aware guard that leaves real binary files untouched. Ships with a `.gitattributes` scaffold and a one-command git-hooks installer so fresh installs are protected by default.
- **Cross-project promotion lifecycle** (`@g-wpac-promote`): workspace members can graduate from a lightweight controlled member to a fully independent autonomous child via a formal, dry-run-first lifecycle instead of hand-editing files.
- **Swarm file-lock manifests**: parallel `g-go --swarm` runs declare file locks so agents never edit the same files; overlapping buckets raise a lock conflict.
- **Profile-aware core skills**: `g-go`, `g-go-code`, `g-go-review`, and `@g-status` read a configurable `workflow_profile` instead of hardcoded status strings.
- **Context-aware autopilot**: `g-go-go` shrinks its parallel batch size under context pressure instead of stopping mid-run, with a stop-detection guard that resumes a stalled loop.

### Changed

- `@g-update` reconciles the gald3r version stamp in every consumer install on sync.
- PCAC terminology renamed to WPAC (Workspace Project-Aware Coordination) across the command suite.

### Fixed

- Cross-platform file corruption from an early coordination transition cleaned up across all framework trees; a reusable cleanup script was added.
- Several PowerShell hook parse and compatibility issues resolved.
- Root `VERSION` file and `.gald3r/releases/` history now created and backfilled by both setup and `@g-update`.
- Context Budget and Conflict Pattern hard rules restored to the core enforcement ruleset.

---

## [1.5.2] - 2026-05-21 (HTML/JSON/TOON Output, Memory Compression, Vocab)

### Added

- **HTML output + theme system** (`g-skl-html-output`, `--html` flag): human-facing reports (`@g-status`, `@g-review`, QA reports) render as self-contained themed HTML. Three built-in themes: `gald3r-dark` (default), `gald3r-light`, `gald3r-mocha`. Coordination files stay markdown.
- **JSON output mode** (`g-skl-json-output`, `--json` flag): a structured `{gald3r_version, generated_at, command, schema, data}` envelope for scripting, CI gates, and dashboards.
- **TOON output mode** (`g-skl-toon-output`, `--toon` flag): Token-Oriented Object Notation -- a compact, lossless, LLM-friendly tabular format (about 40% smaller than JSON).
- **Theme editor** (`g-skl-theme-editor`, `@g-theme-edit`): file-first editor for creating and editing gald3r HTML themes, with import/export of `:root` token blocks.
- **Memory compression** (`g-skl-compress-memory`, `@g-compress-memory`): compact session memory and learned-facts entries to reduce context bloat while preserving key insights.
- **Vocabulary management** (`@g-vocab-add`, `@g-vocab-list`, `@g-vocab-search`): define project-specific abbreviations that agents read at session start.
- **Skill review** (`@g-skill-review`): list, review, and selectively promote auto-proposed skill drafts; human approval required before promotion.
- **Auto-skill generation** (`--propose-skill` on `@g-go-review`): optionally drafts a `SKILL.md` after a PASS verdict when a novel, generalizable pattern is found. Off by default.
- **`@g-mission` improvements**: `resume --budget N`, drain-queue scan order, a 75% context checkpoint threshold, mandatory split for oversized tasks, cross-repo task fix in `--until-empty`, and an autonomous push gate.

---

## [1.5.1] - 2026-05-18

### Added

- `docs/PLUGINS.md`: plugin author guide covering skill pack structure, distribution, and naming guidelines for third-party extensions.
- README "Plugins & Skill Packs" section with a naming guideline (plugins are separate works).
- NOTICE clarified with the plugin naming guideline.

---

## [1.5.0] - 2026-05-10 (Maestro Harvest)

### Added

- **Security scanning** (`g-skl-security-scan`): a two-phase SAST scanner. A fast, free regex pass surfaces candidates across 12 vulnerability categories (hardcoded credentials, SQL injection, eval/exec, weak crypto, path traversal, CORS wildcards, and more), then a focused LLM pass analyzes only the flagged batches. Complements `g-skl-code-review`.
- **Dynamic context assembly** (`g-skl-context-builder`): builds a token-budgeted context block on the fly from live `.gald3r/` state -- active tasks, constraints, relevant subsystems, and recent memory.
- **Engineering-team delegation** (`g-skl-delegate`): task-brief templates, code-review request templates, quality-gate checklists, and clean handoff protocols.
- **More coding-agent runtimes**: `g-skl-cli-jcode` (jcode Rust agent -- millisecond startup, local embeddings via Ollama) and `g-skl-comfyui` (local GPU image/video generation via ComfyUI, zero cloud cost).
- **Code-graph context prep**: `g-go-code` can query a code graph (`g-skl-graphify`) for cheaper architecture lookups, with graceful fallback to grep-based prep.
- **External backlog intake** (`@g-triage`): turns unstructured input (emails, Slack, meeting notes) into routed gald3r items behind a hard human-approval gate.
- **Mid-flight control** (`@g-steer`, `@g-queue`): course-correct or queue work onto an in-progress worktree session; `@g-go-code --resume` adds crash recovery via checkpoint artifacts.
- **Harness tuning guide** (`AGENT_CONFIG.md`): documents context budgets, temperature presets, and retry configuration.
- **Recon provenance**: harvested patterns carry a similarity-risk field from capture through apply.

### Changed

- README component counts and platform parity updated for the 1.5 line.

### Fixed

- Session-start and lint hook compatibility issues on PowerShell resolved.

---

## [1.4.0] - 2026-04-14

### Added

- **GitHub Copilot support** (`.copilot/`): 6th IDE added to the parity set. Full command surface (89 commands) deployed to `.copilot/commands/`. gald3r now supports Cursor, Claude Code, Gemini, Codex, OpenCode, and GitHub Copilot.
- **Recon suite** (`g-skl-recon-repo`, `g-skl-recon-url`, `g-skl-recon-docs`, `g-skl-recon-yt`, `g-skl-recon-file`): unified research/reconnaissance skill family. Replaces the separate `g-skl-reverse-spec`, `g-skl-ingest-docs`, `g-skl-ingest-url`, `g-skl-ingest-youtube`, and `g-skl-harvest` skills with a consistent `recon-*` namespace. Each produces a structured recon report for human review before any writes occur.
- **Research review/apply suite** (`g-skl-res-review`, `g-skl-res-deep`, `g-skl-res-apply`): three-step workflow -- review a recon report, deep-dive on specific findings, then apply approved findings into `.gald3r/features/` staging. Replaces `g-skl-harvest-intake`.
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

- **PCAC Spawn skill** (`g-skl-pcac-spawn`, `@g-pcac-spawn`): spawn a new gald3r project from the current one -- creates the project folder in the ecosystem root, installs gald3r (matching current project's install style), seeds it with an optional description/features/code, runs subsystem discovery, and registers bidirectional PCAC topology links in both projects. Supports `--sibling`, `--child`, `--parent`, and `--dry-run`.
- **PCAC Send-To skill** (`g-skl-pcac-send-to`, `@g-pcac-send-to`): transfer files, features, specs, ideas, bugs, or code from the current project to any related project in the topology. Lighter-weight than `g-skl-pcac-move` -- works with freshly spawned projects, writes an INBOX notification in the destination, and logs provenance in the source vault. Supports `--type features|code|ideas|bugs|docs|spec`, `--delete-source`, and `--dry-run`.
- Both skills deployed across all 5 IDE trees (`.cursor`, `.claude`, `.agent`, `.codex`, `.opencode`) with full parity.

---

## [1.2.0] - 2026-04-14

### Added

- **Feature pipeline** (`g-skl-features`, `FEATURES.md`, `.gald3r/features/`): structured staging layer between idea capture and task creation. Features move through `staging → specced → committed → shipped`. Only reach the TASKS.md backlog when explicitly promoted via `@g-feat-promote`. Prevents backlog pollution and keeps implementation intent explicit.
- **Reverse-spec skill** (`g-skl-reverse-spec`, `@g-reverse-spec`): deep 5-pass analysis of any external repository. Produces a structured harvest report in `research/harvests/{slug}/` with skeleton, module map, feature scan, deep dives, and synthesis passes. Human reviews and marks features `[✅] approved` before APPLY writes to `.gald3r/features/`.
- **Harvest intake skill** (`g-skl-harvest-intake`, `@g-harvest-intake`): processes approved harvest output into `.gald3r/features/` staging entries. Deduplicates against existing staging features -- appends a Collected Approach rather than creating a duplicate.
- **Subsystem graph skill** (`g-skl-subsystem-graph`, `@g-subsystem-graph`): generates a visual Mermaid dependency graph of all registered subsystems with dependency annotations.
- **IDE CLI skills** (`g-skl-cli-cursor`, `g-skl-cli-claude`, `g-skl-cli-gemini`, `g-skl-cli-opencode`): dedicated reference skills for headless and terminal-first operation of each supported IDE. Cover agent mode, Cloud Agent handoff, API mode, session continuation, MCP config, checkpointing, and multi-agent patterns.
- **Granular task commands** (`@g-task-add`, `@g-task-upd`, `@g-task-del`): fine-grained task operations to supplement the existing `@g-task-new` and `@g-task-update` commands.
- **Granular bug commands** (`@g-bug-add`, `@g-bug-upd`, `@g-bug-del`): fine-grained bug management to complement `@g-bug-report` and `@g-bug-fix`.
- **Granular constraint commands** (`@g-constraint-upd`, `@g-constraint-del`): update and delete constraints in `CONSTRAINTS.md`.
- **Granular subsystem commands** (`@g-subsystem-add`, `@g-subsystem-upd`, `@g-subsystem-del`, `@g-subsystem-graph`): full CRUD surface for the subsystem registry.
- **Feature commands** (`@g-feat-new`, `@g-feat-add`, `@g-feat-upd`, `@g-feat-promote`, `@g-feat-rename`, `@g-feat-del`): full feature lifecycle management from the command surface.
- **IDE CLI commands** (`@g-cli-cursor`, `@g-cli-claude`, `@g-cli-gemini`): quick reference commands for each IDE's CLI usage patterns.

### Changed

- `g-go-verify` renamed to `@g-go-review` -- clearer intent (this is the review/verification phase, not a QA pass). Old command name removed from all IDE directories.
- `g-skl-cursor-cli`, `g-skl-claude-cli`, `g-skl-gemini-cli`, `g-skl-opencode-cli` renamed to `g-skl-cli-cursor`, `g-skl-cli-claude`, `g-skl-cli-gemini`, `g-skl-cli-opencode` -- consistent `g-skl-cli-*` namespace pattern. Old skill directories removed.
- `g-skl-plan` updated: `features/` replaces `prds/` as the primary deliverable directory. PRD concepts live inside feature spec files.
- `g-skl-harvest` updated: `APPLY` operation now calls `g-skl-features COLLECT` to dedup against existing staging features instead of creating tasks directly.
- `g-skl-medkit` updated: detects projects with `prds/` folder and no `features/` folder -- offers migration path to 1.2.0 feature pipeline.
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
- **Continual learning skill** (`g-skl-learn`): agents self-report insights to vault memory files after each session. No external services required -- file-only persistence.
- **Health and repair skill** (`g-skl-medkit`): single skill that detects what a `.gald3r/` directory needs (version migration, structural repair, or routine maintenance) and performs it. Replaces the separate g-cleanup, g-grooming, and g-upgrade skills.
- **Platform crawl skill** (`g-platform-crawl`): dedicated skill for crawling Cursor, Claude Code, Gemini, and other platform documentation with configurable targets.
- **Dependency graph** (`g-skl-dependency-graph`): auto-generates `.gald3r/DEPENDENCY_GRAPH.md` from task file dependencies. Shows blocked and blocking relationships.
- **SWOT review skill** (`g-skl-swot-review`): automated SWOT analysis for the current project phase. Reviewsprogress, architectural compliance, code quality, and technical debt.
- **Verify ladder skill** (`g-skl-verify-ladder`): configurable multi-level verification gates from minimal (lint only) to thorough (tests + acceptance + hallucination guard).
- **Knowledge refresh skill** (`g-skl-knowledge-refresh`): audit vault freshness, rebuild compiled pages, detect broken links and stale notes.

### Changed

- `g-go-code` now requires a Status History entry before marking any item `[🔍]`. The b3 step is mandatory.
- `g-go-review` FAIL path now counts FAIL rows in Status History to determine whether to reset to `[📋]` or escalate to `[🚨]`.
- `g-go-code` skips `[🚨]` items entirely -- logs them in the Skipped section as Requires-User-Attention.
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
