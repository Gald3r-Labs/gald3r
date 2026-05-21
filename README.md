<p align="center">
  <img src="logo/Gald3r_Logo_Big.jpg" alt="gald3r banner" width="800">
</p>

<p align="center">
  <strong>Song magic for your codebase.</strong><br>
  Persistent memory, multi-repo orchestration, and adversarial quality gates for AI coding agents across every major IDE.
</p>

<p align="center">
  <a href="LICENSE"><img src="https://img.shields.io/badge/License-FSL--1.1--Apache-purple.svg" alt="License: FSL-1.1-Apache"></a>
  <a href="CHANGELOG.md"><img src="https://img.shields.io/badge/version-1.5.2-green.svg" alt="Version"></a>
  <a href="https://www.python.org"><img src="https://img.shields.io/badge/python-3.10+-blue.svg" alt="Python 3.10+"></a>
  <a href="https://github.com/wrm3/gald3r"><img src="https://img.shields.io/github/stars/wrm3/gald3r?style=social" alt="GitHub stars"></a>
</p>

---

## [Gald3r](https://gald3r.ai) Line Up

| Repo | Description |
|-----------|-----------------------|
| [Gald3r](https://github.com/wrm3/gald3r) | Original Clonable Template — Now mirror of Gald3r Slim |
| [Gald3r_Template_Slim](https://github.com/wrm3/gald3r_template_slim) |Gald3r Clonable Template — Just the Gald3r System |
| [Gald3r_Template_Full](https://github.com/wrm3/gald3r_template_full) | Gald3r Clonable Template — Installable Skill & Personality Packs |
| [Gald3r_Template_Adv](https://github.com/wrm3/gald3r_template_adv) | Gald3r Clonable Template — Advanced |
| [Gald3r_Throne](https://github.com/wrm3/gald3r_throne) | Gald3r Tauri Webapp Interface |
| [Gald3r_Agent](https://github.com/wrm3/gald3r_agent) | Gald3r Agent Harness & Model |
| [Gald3r_Valhalla](https://github.com/wrm3/gald3r_valhalla) | Gald3r Backend |

## The Problem

You have great AI coding agents. And they forget everything the moment you close the chat.

Session 1: You explain your architecture, your constraints, why you chose Postgres over Mongo.  
Session 12: The agent uses SQLite. Because it doesn't remember session 1.

You're running 4 repos — `api`, `web`, `mobile`, `shared-lib`. When something changes in `shared-lib`, every downstream repo needs to know. There's no mechanism for that. You copy-paste tasks manually. Half the time you forget.

You finish a feature and ask the same agent to verify it. It passes everything — of course it does, it wrote the code and knows what it *meant* to write. The bugs it introduced are invisible to it.

**gald3r is the infrastructure layer that fixes all three of these.** It wraps around your AI IDEs and gives agents durable memory, cross-repo coordination, and adversarial quality enforcement — without changing how you code.

---

## What gald3r gives your agents

**Persistent memory** — Architectural decisions, learned project conventions, session summaries, and research notes that survive across conversations, machines, and IDE restarts.

**Multi-repo orchestration** — Declare parent/child/sibling relationships between repos. Broadcast tasks that cascade down a project hierarchy. Let child projects request upstream action. Sync shared contracts between siblings. One unified INBOX for cross-project coordination.

**Adversarial quality gates** — The agent that implements code is *structurally prevented* from marking it done. A separate agent session runs verification. Stuck tasks (3+ failed reviews) auto-escalate to human attention with a full audit trail.

**An Obsidian-compatible knowledge vault** — Every research session, architectural decision, platform doc crawl, and YouTube transcript is stored as a properly-tagged Obsidian note. Open the vault folder in Obsidian and get graph view, search, and backlinks over everything your agents have ever learned.

**Architectural constraints** — Rules agents must follow, loaded at every session start. Not suggestions. If an agent's action would violate a constraint, it must flag the conflict before proceeding.

**6-IDE parity** — Cursor, Claude Code, Gemini, Codex, OpenCode, and GitHub Copilot. Same agents, same skills, same memory, same task state. Switch IDEs mid-task and pick up exactly where you left off.

---

## What's Included

> **How activation works:** All agents, skills, commands, hooks, and rules in this repo are inert markdown/script files until you copy the relevant platform folder into your project. Dropping `.cursor/` into a project activates the full gald3r surface for Cursor. Same for `.claude/`, `.agent/`, `.codex/`, `.opencode/`, and `.copilot/`. You pick which platforms you use — nothing runs without you copying the files first.

| Component | Count | What it covers |
|-----------|-------|----------------|
| **Agents** | 22 | Task manager, code reviewer, QA engineer, project planner, infrastructure, ideas, verifier, project initializer, PCAC coordinator, and more |
| **Core Skills** | 100 | Recon suite (docs/file/repo/url/yt), research suite (deep/review/apply), release management, platform skills (21 platforms), medic, tier-setup, PCAC (10 skills), tasks, bugs, plan, project, features, subsystems, vault, constraints, code review, git, crawl, learn, subsystem-graph, swot, verify-ladder, and more |
| **Addon: Skill Packs** | 142 skills / 20 packs | Vercel, HuggingFace, Cursor Team Kit, Superpowers, AI Media, AI Video Tools, Cloud Providers, Blockchain, 3D Graphics, Community, Content Creation, Startup Tools, Phantom Connect, Context7, Continual Learning, Create Plugin, Firecrawl, Infrastructure, User Skills, and more |
| **Addon: Personality Packs** | 8 themes | Silicon Valley, Star Wars, Star Trek, BSG, Firefly, Hackers, Shoresy, gald3r |
| **Commands** | 149 | Full `@g-*` command surface — task management, bug management, feature pipeline, release management, recon, research, code quality, vault, multi-repo, ideas, constraints, subsystems, swarm, and maintenance |
| **Hooks** | 17 | Session start, agent complete, pre-commit, pre-push, PCAC inbox check, vault operations |
| **Rules** | 15 | Always-apply: documentation, git workflow, error reporting, task completion gates, TODO/stub lifecycle, bug discovery |
| **IDE Platforms** | 21 | 16 installer-managed + 5 reference-skill platforms (see Quick Start for full list) |

### Agents

gald3r ships 22 specialized agents — each is a focused persona with a defined scope, tool set, and activation criteria. Agents are plain markdown files living in `.cursor/agents/`, `.claude/agents/`, etc. They are **inert until you copy the platform folder into your project.**

| Agent | File | What it does |
|-------|------|-------------|
| `g-agnt-task-manager` | `g-agnt-task-manager.md` | Owns `.gald3r/` state — creates, updates, and syncs tasks, bugs, and the TASKS.md index. The source of truth for all backlog operations. |
| `g-agnt-qa-engineer` | `g-agnt-qa-engineer.md` | QA specialist. Logs bugs, writes BUG entries with severity and code annotations, runs quality metrics, and tracks resolution. Enforces the bug discovery gate before any task reaches `[🔍]`. |
| `g-agnt-code-reviewer` | `g-agnt-code-reviewer.md` | Adversarial reviewer. Runs in a **separate session** from the implementer. Reads only what exists on disk, confirms every acceptance criterion, and decides `[✅]` or `[📋]` (fail with documented reasons). Cannot implement — only review. |
| `g-agnt-project` | `g-agnt-project.md` | Project strategist. Maintains `PROJECT.md`, `PLAN.md`, milestones, goal alignment, and the feature pipeline. Translates high-level intent into structured deliverables. |
| `g-agnt-infrastructure` | `g-agnt-infrastructure.md` | Architectural guardian. Manages `SUBSYSTEMS.md`, subsystem specs, `CONSTRAINTS.md`, and subsystem Activity Logs. Flags constraint violations and keeps the registry in sync with the actual codebase. |
| `g-agnt-ideas-goals` | `g-agnt-ideas-goals.md` | Idea and goal steward. Captures ideas to `IDEA_BOARD.md`, evaluates them against project goals, promotes promising ideas to the feature pipeline, and runs proactive codebase scans for improvement opportunities. |
| `g-agnt-verifier` | `g-agnt-verifier.md` | Standalone verification specialist. Operates identically to the code-reviewer but can be invoked explicitly on a single task or file set. Used when a dedicated reviewer session is warranted outside the normal `@g-go-review` flow. |
| `g-agnt-project-initializer` | `g-agnt-project-initializer.md` | Bootstrap agent. Runs `@g-setup` end-to-end for a brand-new project: creates `.gald3r/.identity`, seeds all structural files, registers the project, and produces a starter `PROJECT.md` and `PLAN.md`. |
| `g-agnt-pcac-coordinator` | `g-agnt-pcac-coordinator.md` | Cross-project coordinator. Manages the full PCAC topology — reads the INBOX, routes broadcasts from parent projects, handles requests from children, syncs contracts with siblings, and resolves conflicts before session work begins. |
| `g-agnt-workspace-manager` | `g-agnt-workspace-manager.md` | Workspace-Control specialist. Manages the workspace manifest, member repo boundaries, marker bootstrap/remediation, and cross-repo clean gates for multi-repository orchestration. |
| `g-agnt-marketing` | `g-agnt-marketing.md` | Growth and distribution agent. Orchestrates SEO, GEO (AI search visibility), content, community, and launch channel strategies for indie founders and small teams. |
| `g-agnt-test` | `g-agnt-test.md` | Test plan manager. Creates and maintains fast (L1), comprehensive (L2), and regression (L3) test plans. Enforces C-013 (test plan maintenance), C-014 (fast gate), and C-015 (pre-release comprehensive gate). |

### Skill Packs

Skills are detailed instruction documents that tell agents not just *what* to do but exactly *how* to do it — including operations, file formats, edge cases, and cross-references to sibling skills. Each skill owns a named slice of the system.

**Skills are plain markdown files living in `.cursor/skills/`, `.claude/skills/`, etc. They are inert until you copy a platform folder into your project.** Once active, your IDE's agent can read and follow them on demand or when triggered by a matching context.

**📋 Core Task Management Pack**

The foundation. Owns every file in `.gald3r/` and manages the full lifecycle of tasks, bugs, plans, goals, constraints, and subsystems.

| Skill | What it owns |
|-------|-------------|
| `g-skl-tasks` | `TASKS.md` + `tasks/` — full task lifecycle: create, update, sync, sprint plan, complexity score |
| `g-skl-bugs` | `BUGS.md` + `bugs/` — bug tracking, severity classification, quality metrics, resolution workflow |
| `g-skl-plan` | `PLAN.md` + `features/` — strategic milestones, deliverable index, phase management |
| `g-skl-features` | `FEATURES.md` + `features/` — feature staging pipeline: STAGE, COLLECT, SPEC, PROMOTE, RENAME, STATUS |
| `g-skl-project` | `PROJECT.md` — mission, vision, goals, project linking |
| `g-skl-constraints` | `CONSTRAINTS.md` — ADD, UPDATE, CHECK, DELETE, LIST operations for architectural rules |
| `g-skl-subsystems` | `SUBSYSTEMS.md` + `subsystems/` — component registry with Activity Logs and dependency tracking |
| `g-skl-ideas` | `IDEA_BOARD.md` — capture, review, farm, and promote ideas to the feature pipeline |
| `g-skl-status` | Read-only session context: active tasks, phase progress, open bugs, pending ideas |
| `g-skl-medkit` | `.gald3r/` health check, structural repair, and version migration (1.0 → 1.1 → 1.2) |
| `g-skl-setup` | Initialize gald3r in a brand-new project — creates all structural files from templates |

**🌐 Feature Pipeline Pack**

The staging layer between idea capture and the task backlog. Features are research artifacts before they become implementation work.

| Skill | What it owns |
|-------|-------------|
| `g-skl-features` | *(listed above — FEATURES.md and the full staging lifecycle)* |
| `g-skl-recon-repo` | Deep repo analysis (replaces reverse-spec) — 5-pass: skeleton → module map → feature scan → deep dives → synthesis |
| `g-skl-res-review` | Review a recon report and mark features approved/rejected before apply |
| `g-skl-res-apply` | Apply approved recon findings into `.gald3r/features/` staging |
| `g-skl-res-deep` | Follow-up deep dive on a specific approved feature from a recon report |

**🔗 Multi-Project Coordination Pack (PCAC)**

The full parent/child/sibling coordination system. Ten skills covering every direction of cross-project communication.

| Skill | What it does |
|-------|-------------|
| `g-skl-pcac-adopt` | Register a child project — writes `link_topology.md` on both sides |
| `g-skl-pcac-claim` | Register a parent project — bidirectional topology link |
| `g-skl-pcac-order` | Broadcast a task to child projects with configurable cascade depth (1–3) |
| `g-skl-pcac-ask` | Write a request to the parent project's `INBOX.md` |
| `g-skl-pcac-sync` | Initiate or respond to sibling contract sync — advisory, non-blocking |
| `g-skl-pcac-read` | Review and action all incoming INBOX items: conflicts, requests, broadcasts, notifications |
| `g-skl-pcac-notify` | Send a lightweight `[INFO]` FYI to one or more project INBOXes — no task created |
| `g-skl-pcac-move` | Transfer files/folders between topology projects with provenance tracking |
| `g-skl-pcac-spawn` | Spawn a new gald3r project from this one — creates folder, installs gald3r, seeds with features/code, links PCAC topology |
| `g-skl-pcac-send-to` | Send files, features, specs, ideas, or code to any related project with INBOX notification and vault provenance log |

**🧠 Knowledge Vault Pack**

Everything knowledge. Crawl, recon, learn, audit, and rebuild. All output is Obsidian-compatible YAML frontmatter.

| Skill | What it does |
|-------|-------------|
| `g-skl-vault` | Vault CRUD, Obsidian frontmatter compliance, `_INDEX.md` MOC hub rebuild, GitHub repo summaries |
| `g-skl-learn` | Continual learning — agents self-report insights to vault memory files after each session |
| `g-skl-crawl` | Native crawl4ai web crawler — clean LLM-optimized markdown from any URL, no Docker required |
| `g-skl-recon-docs` | Platform doc recon with per-platform freshness tracking and stale-doc surfacing at session start |
| `g-skl-recon-url` | One-time URL capture into `research/articles/` with deduplication by source URL |
| `g-skl-recon-yt` | YouTube transcript extraction via yt-dlp — offline, no API key, stored in `research/videos/` |
| `g-skl-recon-file` | Analyze local files/folders for insights — outputs structured recon report |
| `g-skl-knowledge-refresh` | Audit vault freshness, detect stale notes and broken links, rebuild MOC hub files |
| `g-platform-crawl` | Dedicated crawl targets for Cursor, Claude Code, Gemini, and other platform docs |

**🔍 Code Quality Pack**

Structured review, configurable verification gates, SWOT analysis, automated dependency visualization, and subsystem graph generation.

| Skill | What it does |
|-------|-------------|
| `g-skl-code-review` | Full structured review: security, performance, maintainability, architectural alignment — severity-classified with file/line references |
| `g-skl-review` | Quick-scan review — concise severity ratings and action items |
| `g-skl-verify-ladder` | Configurable verification gates from minimal (lint only) to thorough (tests + acceptance criteria + hallucination guard) |
| `g-skl-swot-review` | Automated SWOT analysis for the current project phase: progress, code quality, technical debt |
| `g-skl-dependency-graph` | Auto-generate `.gald3r/DEPENDENCY_GRAPH.md` from task `blocked_by` fields — shows blocked/blocking chains |
| `g-skl-subsystem-graph` | Generate a Mermaid visual of all registered subsystems and their dependency relationships |
| `g-skl-qa` | QA activation mode — bug discovery workflow, quality metrics reports, retroactive documentation |

**🛠️ Git & Workflow Pack**

Commit discipline, pre-commit gates, and conventional commit format with task references.

| Skill | What it does |
|-------|-------------|
| `g-skl-git-commit` | Conventional commit format (`feat/fix/chore`) with task ID reference and optional agent footer for autonomous commits |

**💻 IDE CLI Pack**

Headless, multi-agent, and terminal-first usage of each supported IDE from the command line. Covers session continuation, MCP config, Cloud Agent handoff, and overnight/CI patterns.

| Skill | What it does |
|-------|-------------|
| `g-skl-cli-cursor` | Cursor CLI: `agent` command, API mode, Cloud Agent handoff, session management |
| `g-skl-cli-claude` | Claude Code CLI: headless flags, `--continue`, MCP config, multi-agent via Agent SDK |
| `g-skl-cli-gemini` | Gemini CLI: authentication, checkpointing, `--checkpoint` flag, extensions/tools, memory patterns |
| `g-skl-cli-opencode` | OpenCode CLI: stub — full docs pending first stable release |

---

## How It Works

```
your-project/
├── .gald3r/                    # Everything gald3r manages
│   ├── TASKS.md               # Master task checklist (YAML + markdown specs)
│   ├── BUGS.md                # Bug index with severity and status
│   ├── PLAN.md                # Strategic milestones and PRD index
│   ├── PROJECT.md             # Mission, vision, goals (plain language)
│   ├── CONSTRAINTS.md         # Architectural rules agents must obey
│   ├── SUBSYSTEMS.md          # Component registry + dependency graph
│   ├── FEATURES.md            # Feature registry — staging pipeline (staging→specced→committed→shipped)
│   ├── .vault_location        # Path to your knowledge vault (default: local)
│   ├── tasks/                 # Individual task specs (YAML + acceptance criteria)
│   ├── bugs/                  # Individual bug spec files
│   ├── features/              # Feature staging files (feat-NNN_slug.md)
│   ├── prds/                  # Legacy PRD files (migrated to features/ in 1.2.0)
│   ├── subsystems/            # Per-subsystem spec files with Activity Logs
│   ├── linking/               # Cross-project topology + INBOX
│   └── vault/                 # Local vault (if .vault_location = {LOCAL})
│
├── .cursor/                   # Cursor IDE
│   ├── agents/                # 22 gald3r agents
│   ├── skills/                # 100 core skills (g-skl-*)
│   ├── commands/              # 149 @g-* commands
│   ├── hooks/                 # 17 PowerShell automation hooks
│   └── rules/                 # 15 always-apply rules
│
├── .claude/                   # Claude Code  (identical to .cursor/)
├── .agent/                    # Gemini        (identical, adapted format)
├── .codex/                    # Codex         (skills subset)
├── .opencode/                 # OpenCode      (agents + commands)
│
├── AGENTS.md                  # Project context (read at session start by all IDEs)
├── CLAUDE.md                  # Claude Code project instructions
└── GEMINI.md                  # Gemini project instructions
```

---

## Quick Start

### New Installation

**Step 1 — Clone the template for your tier:**

```powershell
# Advanced (full framework + skill & personality packs, always up-to-date)
git clone https://github.com/wrm3/gald3r_template_adv.git

# Full (core framework + installable skill & personality packs)
git clone https://github.com/wrm3/gald3r_template_full.git

# Slim (just the core gald3r system — no optional packs)
git clone https://github.com/wrm3/gald3r_template_slim.git
```

**Step 2 — Run the installer:**

> **Windows users:** Do not double-click the `.ps1` file — Windows will ask "Open with what?". Instead, open PowerShell and run:

```powershell
# Interactive — prompts for project path and platform selection
powershell -ExecutionPolicy Bypass -File setup_gald3r_project.ps1

# Or if you are already in the cloned template folder in PowerShell:
Set-ExecutionPolicy -Scope Process Bypass
.\setup_gald3r_project.ps1
```

The interactive installer will:
- Ask for your target project path
- Detect if this is a new project or an existing gald3r install (v1 / v2 / v3 — auto-migrates)
- Let you pick which AI platforms to enable (see the full platform list below)
- Deploy `.gald3r_sys/` — the canonical read-only framework payload
- Initialize `.gald3r/` project state (`TASKS.md`, `PROJECT.md`, `PLAN.md`, etc.)
- Merge `CLAUDE.md`, `AGENTS.md`, `.gitignore` using section markers (never overwrites your content)
- Deploy platform dirs (`.cursor/`, `.claude/`, `.agent/`, etc.) with skills, agents, commands, and rules
- Copy `setup_gald3r_project.ps1` into your project for future updates and session-start hooks

**Non-interactive install:**

```powershell
# Install specific platforms into a target project
powershell -ExecutionPolicy Bypass -File setup_gald3r_project.ps1 -TargetPath "C:\MyProject" -Platforms cursor,claude

# Preview without writing anything
powershell -ExecutionPolicy Bypass -File setup_gald3r_project.ps1 -TargetPath "C:\MyProject" -Platforms all -DryRun
```

**Step 3 — Initialize your project:**

Open your project in your preferred IDE, start a new session, and run:

```
@g-setup     # Cursor
/g-setup     # Claude Code
```

This creates your `.gald3r/.identity`, seeds structural files, and registers the project. You are ready.

---

### Updating an Existing Install

If you already have gald3r installed (any version), the installer handles migration automatically:

```powershell
# From the template folder — run against your existing project
powershell -ExecutionPolicy Bypass -File setup_gald3r_project.ps1 -TargetPath "C:\YourExistingProject" -Platforms cursor,claude

# Or from inside your already-installed project (regenerate platform dirs only):
powershell -ExecutionPolicy Bypass -File setup_gald3r_project.ps1 -Platform auto    # auto-detect running IDE
powershell -ExecutionPolicy Bypass -File setup_gald3r_project.ps1 -Platform all     # regenerate all installed platforms
powershell -ExecutionPolicy Bypass -File setup_gald3r_project.ps1 -Platform all -Clean  # wipe and regenerate
```

The update mode **never touches** your `README.md`, `LICENSE`, or `CHANGELOG.md`, **never overwrites** your non-gald3r skills and agents, and **safely updates** all `g-` prefixed framework files.

---

### Supported AI Platforms (21)

Platforms marked **[installer]** are fully automated by `setup_gald3r_project.ps1`.
Platforms marked **[skill]** have a `g-skl-platform-*` reference skill for manual setup guidance.

| Platform | Prefix | Capabilities | Notes |
|---|---|---|---|
| Cursor IDE | `.cursor/` | Rules (`.mdc`), skills, agents, commands | [installer] |
| Claude Code | `.claude/` | Rules (`.md`), skills, agents, commands, hooks | [installer] |
| Gemini / Antigravity | `.agent/` | Skills, agents, commands | [installer] |
| OpenAI Codex CLI | `.codex/` | Skills, agents, commands | [installer] |
| OpenCode (sst.dev) | `.opencode/` | Skills, agents, commands | [installer] |
| GitHub Copilot | `.copilot/` | Commands (Phase 1) | [installer] |
| Windsurf | `.windsurf/` | Skills, agents, commands | [installer] |
| Cline | `.cline/` | Skills, agents, commands | [installer] |
| Roo Code | `.roo-code/` | Skills, agents, commands | [installer] |
| Kiro (Amazon) | `.kiro/` | Skills, agents, commands | [installer] |
| Augment Code | `.augment/` | Skills, agents, commands | [installer] |
| Aider | `.aider/` | Skills, agents, commands | [installer] |
| Goose (Block) | `.goose/` | Skills, agents, commands | [installer] |
| Warp Terminal | `.warp/` | Skills, agents, commands | [installer] |
| OpenHands | `.openhands/` | Skills, agents, commands | [installer] |
| Replit Agent | `.replit/` | Skills, agents, commands | [installer] |
| Mistral Vibe | `.mistral/` | Skills, agents, commands | [skill] |
| Qwen Code (Alibaba) | `.qwen/` | Skills, agents, commands | [skill] |
| JetBrains Junie | `.junie/` | Skills, agents, commands | [skill] |
| Kiro CLI (Amazon) | `.kiro/` | CLI variant of Kiro IDE | [skill] |
| OpenClaw | — | SOUL.md pattern, workspace skills | [skill] |

---
## Key Features

### Multi-Project Orchestration (PCAC)

gald3r can model your entire software ecosystem as a graph of related projects — parent services, child microservices, sibling repos sharing contracts. Agents in each project can coordinate across the graph without manual copy-paste.

```
@g-pcac-adopt api-service        # Register api-service as a child of this project
@g-pcac-claim platform-core      # Register platform-core as parent of this project
@g-pcac-status                   # View your position in the topology + open INBOX items
```

**Broadcasting tasks downstream:**
```
@g-pcac-order "Upgrade auth library to v3"
# Creates the task in every child project's .gald3r/
# Cascades to grandchildren if cascade_depth > 1
# Child agents pick it up at their next session start
```

**Requesting upstream action:**
```
@g-pcac-ask "Need rate-limiting in the API gateway"
# Writes to parent project's INBOX.md
# Parent agent sees it at session start and can accept, reject, or defer
```

**Sibling contract sync:**
```
@g-pcac-sync shared-auth-schema   # Sync a shared contract spec with all siblings
@g-pcac-notify web-frontend "Deployed new endpoint: /api/v3/users"
```

Every project has an INBOX (`linking/INBOX.md`) that the session-start hook reads. Broadcasts, requests, and sync notifications land there and are surfaced before any other work begins. Conflicts (when two projects disagree on a shared contract) block all session work until resolved.

---

### Adversarial Code Review — Two-Phase Quality Gate

```
# Phase 1 — implement (your current session):
@g-go-code

# Every completed item is marked [🔍] (Awaiting Verification)
# The implementing agent NEVER marks [✅]
```

```
# Phase 2 — verify (a SEPARATE agent session, new window):
@g-go-review

# Reads only what exists on disk
# Confirms every acceptance criterion independently
# [✅] = all criteria confirmed | [📋] = fail, specific reasons documented
```

An agent that implements and verifies its own work has a systematic blind spot — it knows what it *intended* to write. A separate session reads only what actually exists. This is not optional ceremony; it is the only path to `[✅]`.

**Circuit breaker:** If a task fails verification 3 or more times, it is automatically escalated to `[🚨]` Requires-User-Attention. Automated agents skip it permanently. A Status History table records every state transition with timestamp and reason — complete audit trail.

| Status | Meaning |
|--------|---------|
| `[ ]` | Pending |
| `[📋]` | Ready — task spec created |
| `[🔄]` | Active — being implemented |
| `[🔍]` | Awaiting Verification — implementation complete |
| `[✅]` | Complete — verified by a separate session |
| `[🚨]` | Requires Human — circuit breaker engaged after 3+ failures |

---

### Feature Pipeline (Staging → Shipped)

Ideas don't go straight to tasks. gald3r now provides a structured feature pipeline — a staging layer between idea capture and task creation. Features move through four phases with checkpoints at each transition.

```
@g-feat-new "Webhook retry with exponential backoff"
# Creates .gald3r/features/feat-036_webhook_retry.md
# Status: staging — collecting approaches before committing

@g-feat-add feat-036 --source "github.com/user/repo" --approach "Redis-backed retry queue"
# Appends approach to the feature's Collected Approaches table

@g-recon-repo https://github.com/some/project
# 5-pass deep analysis: skeleton → module map → feature scan → deep dives → synthesis
# Output: research/recon/some__project/ for human review

@g-res-review some__project
# Review findings — mark individual items approved/rejected

@g-res-apply some__project
# Apply approved findings into .gald3r/features/ staging
```

**Feature lifecycle:**

| Phase | Description |
|-------|-------------|
| `staging` | Research phase — collecting approaches from external analysis, discussions, external repos |
| `specced` | Formal requirements written — acceptance criteria defined |
| `committed` | Active tasks created in TASKS.md — being coded |
| `shipped` | Fully implemented and verified |

Features only become tasks (and enter the TASKS.md backlog) when promoted via `@g-feat-promote`. This keeps the task backlog clean and intention-driven.

---

### Knowledge Vault (Obsidian-Compatible)

Every project gets a file-based knowledge store. All notes use a standardized YAML frontmatter schema compatible with Obsidian's native indexing — so the same vault that stores your AI's memory is also a proper personal knowledge base.

```
@g-recon-docs https://docs.cursor.com    # Crawl platform docs (schedule-aware, freshness tracked)
@g-recon-url  https://example.com/post   # One-time article capture
@g-recon-yt   https://youtu.be/...       # Extract YouTube transcript (yt-dlp, offline)
@g-learn                                  # Agents self-report insights to vault memory files
```

Open the vault folder directly in **Obsidian** for graph view, tag search, and backlinks over everything your agents have ever learned. The `_INDEX.md` MOC hub files (auto-generated for directories with 10+ notes) create the graph connections.

**Vault configuration** — set `vault_location` in `.gald3r/.identity`:

```
vault_location={LOCAL}                # Default: .gald3r/vault/ inside this project
vault_location=/path/to/shared        # Shared vault: multiple projects contribute to one knowledge base
```

**What the vault stores:**
- Session summaries captured after each conversation
- Architectural decisions extracted from discussions via `@g-learn`
- Platform documentation crawled for offline reference (Cursor, Claude, Gemini APIs, etc.)
- YouTube transcripts and video research notes
- Recon reports from external repo analysis

---

### Task Management

Tasks are YAML-frontmatter markdown files with structured specs and acceptance criteria. The master `TASKS.md` checklist syncs with individual files in `tasks/`. Every status change appends to the Status History table.

```
@g-task-new "Implement WebSocket reconnection with exponential backoff"
# Creates tasks/task051_websocket_reconnection.md with:
# - YAML frontmatter (id, priority, subsystems, dependencies)
# - Objective and acceptance criteria
# - Status History table
```

Tasks support dependencies (`blocked_by: [49, 50]`), subsystem tagging, sprint planning, and complexity scoring. The session-start protocol reads all `[📋]` tasks and surfaces any that have a recent FAIL in their history.

---

### Architectural Constraints

```
@g-constraint-add "Never use synchronous HTTP calls in async route handlers"
@g-constraint-check                   # Verify current implementation against all constraints
```

Constraints live in `CONSTRAINTS.md` with enforcement definitions. They load at every session start (Step 0 of the session protocol) and are checked before any task is marked `[🔍]`. An agent that would violate a constraint must flag it and get explicit approval — it cannot silently work around it.

---

### Skill Packs

Skills are detailed instruction documents that tell agents not just *what* to do but exactly *how* — covering operations, file formats, edge cases, and cross-references to sibling skills. Each skill owns a named slice of the system and is activated by copying the platform folder (`.cursor/`, `.claude/`, `.agent/`, `.codex/`, or `.opencode/`) into your project.

---

**📋 Core Task Management Pack**

The foundation. Owns every file in `.gald3r/` and manages the full lifecycle of tasks, bugs, plans, goals, constraints, and subsystems.

| Skill | Owned files | What it does |
|-------|-------------|-------------|
| `g-skl-tasks` | `TASKS.md`, `tasks/` | Full task lifecycle: create, update, sync, sprint plan, complexity score, dependency tracking |
| `g-skl-bugs` | `BUGS.md`, `bugs/` | Bug tracking, severity classification (Critical/High/Medium/Low), quality metrics, resolution workflow |
| `g-skl-plan` | `PLAN.md`, `features/` | Strategic milestones, deliverable index, phase management, PRD cross-references |
| `g-skl-features` | `FEATURES.md`, `features/` | Feature staging pipeline: STAGE, COLLECT, SPEC, PROMOTE, RENAME, STATUS operations |
| `g-skl-project` | `PROJECT.md` | Mission, vision, goals (G-NN format), project linking to topology |
| `g-skl-constraints` | `CONSTRAINTS.md` | ADD, UPDATE, CHECK, DELETE, LIST operations for architectural rules |
| `g-skl-subsystems` | `SUBSYSTEMS.md`, `subsystems/` | Component registry with Activity Logs, dependency and dependent tracking |
| `g-skl-ideas` | `IDEA_BOARD.md` | Capture, review, farm, and promote ideas to the feature pipeline |
| `g-skl-status` | read-only | Session context summary: active tasks, phase progress, open bugs, pending ideas |
| `g-skl-medkit` | `.gald3r/` | Health check, structural repair, and version migration (1.0 → 1.1 → 1.2) |
| `g-skl-setup` | `.gald3r/` | Initialize gald3r in a brand-new project — creates all structural files from templates |

---

**🌐 Feature Pipeline Pack**

The staging layer between idea capture and the task backlog. Features collect approaches and get formally specced before any task is created — keeps the backlog clean and intention-driven.

| Skill | What it does |
|-------|-------------|
| `g-skl-features` | STAGE a new feature, COLLECT approaches, SPEC requirements, PROMOTE to tasks, RENAME slugs |
| `g-skl-recon-repo` | Deep repo analysis — 5-pass: skeleton → module map → feature scan → deep dives → synthesis. Output in `research/recon/{slug}/` — no `.gald3r/` writes until human approves |
| `g-skl-recon-url` | One-time URL capture and analysis into `research/articles/` with deduplication |
| `g-skl-recon-docs` | Platform doc recon with freshness tracking; stale docs surfaced at session start |
| `g-skl-recon-yt` | YouTube transcript extraction via yt-dlp — offline, no API key, stored in `research/videos/` |
| `g-skl-recon-file` | Analyze local files/folders for patterns and insights — structured recon report output |
| `g-skl-res-review` | Review recon report output — mark findings approved/rejected before apply |
| `g-skl-res-deep` | Follow-up deep dive on a specific approved finding from a recon report |
| `g-skl-res-apply` | Apply approved recon findings into `.gald3r/features/` staging entries with dedup |

---

**🔗 Multi-Project Coordination Pack (PCAC)**

The full parent/child/sibling coordination system. Ten skills covering every direction of cross-project communication.

| Skill | What it does |
|-------|-------------|
| `g-skl-pcac-adopt` | Register a child project — writes `link_topology.md` bidirectionally on both sides |
| `g-skl-pcac-claim` | Register a parent project — bidirectional topology link with parent confirmation |
| `g-skl-pcac-order` | Broadcast a task to child projects with configurable cascade depth (1–3 hops) |
| `g-skl-pcac-ask` | Write a request to the parent project's `INBOX.md`; marks local task as blocked with cross-project metadata |
| `g-skl-pcac-sync` | Initiate or respond to sibling contract sync — advisory only, non-blocking |
| `g-skl-pcac-read` | Review and action all INBOX items: conflicts (block planning), requests from children, broadcasts from parents |
| `g-skl-pcac-notify` | Send a lightweight `[INFO]` FYI to one or more INBOXes — no task created, no approval required |
| `g-skl-pcac-move` | Transfer files/folders between topology projects with provenance tracking and vault log entries on both sides |
| `g-skl-pcac-spawn` | Spawn a new gald3r project from this one — creates folder, installs gald3r, seeds with features/code, runs setup, links PCAC topology bidirectionally |
| `g-skl-pcac-send-to` | Send files, features, specs, ideas, or code to any related project — writes destination INBOX notification and source vault provenance log |

---

**🧠 Knowledge Vault Pack**

Everything knowledge. Crawl, recon, learn, audit, and rebuild. All vault output uses a standardized Obsidian-compatible YAML frontmatter schema.

| Skill | What it does |
|-------|-------------|
| `g-skl-vault` | Vault CRUD, Obsidian frontmatter compliance, `_INDEX.md` MOC hub rebuild, GitHub repo summaries |
| `g-skl-learn` | Agents self-report insights to vault memory files after each session — file-only, no external services |
| `g-skl-crawl` | Native crawl4ai web crawler — LLM-optimized markdown from any URL, no Docker required. Shared primitive for recon skills |
| `g-skl-knowledge-refresh` | Audit vault freshness, detect stale notes and broken links, rebuild `_INDEX.md` MOC hub files |
| `g-platform-crawl` | Dedicated crawl targets for Cursor, Claude Code, Gemini, and other platform documentation |

---

**🔍 Code Quality Pack**

Structured review, configurable verification gates, SWOT analysis, automated dependency visualization, and subsystem graph generation.

| Skill | What it does |
|-------|-------------|
| `g-skl-code-review` | Full structured review: security, performance, maintainability, architectural alignment — severity-classified output with file/line references |
| `g-skl-review` | Quick-scan review — concise severity ratings and action items for smaller diffs |
| `g-skl-verify-ladder` | Configurable verification gates from minimal (lint only) to thorough (tests + every acceptance criterion + hallucination guard) |
| `g-skl-swot-review` | Automated SWOT analysis for the current project phase: progress, architectural compliance, code quality, technical debt |
| `g-skl-dependency-graph` | Auto-generate `.gald3r/DEPENDENCY_GRAPH.md` from task `blocked_by` fields — shows full blocked/blocking chains |
| `g-skl-subsystem-graph` | Generate a Mermaid visual of all registered subsystems and their declared dependency relationships |
| `g-skl-qa` | QA activation mode — bug discovery workflow, quality metrics reports, retroactive documentation |

---

**🛠️ Git & Workflow Pack**

Commit discipline, pre-commit gates, and conventional commit format with task references.

| Skill | What it does |
|-------|-------------|
| `g-skl-git-commit` | Conventional commit format (`feat/fix/chore/docs`) with task ID reference and optional agent footer for autonomous commits |

---

**💻 IDE CLI Pack**

Headless, multi-agent, and terminal-first usage of each supported IDE. Covers session continuation, MCP config, Cloud Agent handoff, and overnight/CI patterns. One skill per IDE.

| Skill | What it does |
|-------|-------------|
| `g-skl-cli-cursor` | Cursor CLI: `agent` command, API mode, Cloud Agent handoff, session management, approval modes |
| `g-skl-cli-claude` | Claude Code CLI: headless flags, `--continue`, MCP config, permissions, multi-agent via Agent SDK |
| `g-skl-cli-gemini` | Gemini CLI: authentication, `--checkpoint` flag, config file, extensions/tools, memory patterns |
| `g-skl-cli-opencode` | OpenCode CLI: stub — full documentation pending first stable release |

---

### Command Reference

**Task & Bug Management**

| Command | What it does |
|---------|-------------|
| `@g-task-new` | Create a task with full spec and acceptance criteria |
| `@g-task-add` | Add a task quickly with minimal spec |
| `@g-task-update` | Update task status, priority, or metadata |
| `@g-task-upd` | Update specific task fields |
| `@g-task-del` | Delete a task and remove from TASKS.md |
| `@g-task-sync-check` | Validate TASKS.md ↔ tasks/ file sync |
| `@g-bug-report` | Log a bug with severity, file, and description |
| `@g-bug-fix` | Fix a reported bug and update BUGS.md |
| `@g-bug-add` | Add a bug entry to BUGS.md |
| `@g-bug-upd` | Update an existing bug entry |
| `@g-bug-del` | Delete a bug entry |
| `@g-go` | Full autonomous cycle (implement + verify in sequence) |
| `@g-go-code` | Implement-only: marks completed items `[🔍]`, never `[✅]` |
| `@g-go-review` | Verify-only: run in a new agent session to confirm `[🔍]` items |
| `@g-status` | Project status: active tasks, goals, open bugs, ideas |
| `@g-workflow` | Task expansion and sprint planning |

**Planning & Goals**

| Command | What it does |
|---------|-------------|
| `@g-plan` | Create or update PLAN.md and milestone docs |
| `@g-setup` | Initialize gald3r in a new project |
| `@g-goal-update` | Update PROJECT_GOALS.md |
| `@g-phase-add` | Add a new project phase |
| `@g-phase-pivot` | Pivot project direction |
| `@g-subsystems` | Sync check, add, update subsystem Activity Logs |
| `@g-subsystem-add` | Add a new subsystem to the registry |
| `@g-subsystem-upd` | Update subsystem spec or Activity Log |
| `@g-subsystem-del` | Delete a subsystem from the registry |
| `@g-subsystem-graph` | Generate visual subsystem dependency graph |
| `@g-prd-add` | Create a new Product Requirements Document (governance/audit artifact) |
| `@g-prd-upd` | Update a PRD (blocked on released/superseded status) |
| `@g-prd-del` | Archive a PRD (soft-delete; audit trail preserved) |
| `@g-prd-revise` | Create v2 of a released PRD; atomically supersedes the original |

**Feature Pipeline**

| Command | What it does |
|---------|-------------|
| `@g-feat-new` | Stage a new feature and create the feature spec file |
| `@g-feat-add` | Add to an existing feature (collect approach, deliverable) |
| `@g-feat-upd` | Update feature status, metadata, or notes |
| `@g-feat-promote` | Promote a specced feature to committed — creates tasks |
| `@g-feat-rename` | Rename a feature slug and update all references |
| `@g-feat-del` | Delete a feature and remove from FEATURES.md |
| `@g-recon-repo` | 5-pass deep analysis of an external repo → recon report |
| `@g-recon-url` | One-time URL capture into vault |
| `@g-recon-docs` | Crawl platform docs with freshness tracking |
| `@g-recon-yt` | Extract and save YouTube transcript |
| `@g-recon-file` | Analyze local files/folders for patterns |
| `@g-res-review` | Review recon report — approve/reject findings |
| `@g-res-deep` | Deep dive on a specific approved finding |
| `@g-res-apply` | Apply approved findings into feature staging |

**Knowledge & Vault**

| Command | What it does |
|---------|-------------|
| `@g-vault-ingest` | Manual vault file ingest with frontmatter |
| `@g-vault-search` | Search the vault |
| `@g-vault-status` | Vault health and freshness report |
| `@g-vault-lint` | Audit vault frontmatter compliance |
| `@g-vault-process-inbox` | Process pending vault inbox items |
| `@g-learn` | Capture insights to vault memory files |

**Multi-Project (PCAC)**

| Command | What it does |
|---------|-------------|
| `@g-pcac-adopt` | Register a child project (bidirectional link) |
| `@g-pcac-claim` | Register a parent project (bidirectional link) |
| `@g-pcac-status` | View topology position and open INBOX items |
| `@g-pcac-order` | Broadcast a task to child projects with cascade depth |
| `@g-pcac-ask` | Send a request to the parent project |
| `@g-pcac-sync` | Initiate contract sync with a sibling project |
| `@g-pcac-read` | Review and action all INBOX items |
| `@g-pcac-notify` | Send a lightweight FYI notification across topology |
| `@g-pcac-move` | Transfer files/folders to another project in topology |
| `@g-pcac-spawn` | Spawn a new gald3r project — creates, installs gald3r, seeds with features/code, links topology |
| `@g-pcac-send-to` | Send files, features, ideas, or code to any related project with INBOX notification |

**Code Quality & Git**

| Command | What it does |
|---------|-------------|
| `@g-code-review` | Structured review: security, performance, quality, architecture |
| `@g-test` | Create or run test plans (L1 fast, L2 comprehensive, L3 regression) |
| `@g-crr` | Clean-room rewrite pipeline: analyze external patterns then produce original implementation |
| `@g-git-commit` | Conventional commit with task reference and agent footer |
| `@g-git-sanity` | Pre-commit check: staged secrets, large files, sync drift |
| `@g-git-push` | Pre-push gate: regular vs release validation |

**Constraints & Compliance**

| Command | What it does |
|---------|-------------|
| `@g-constraint-add` | Add a new architectural constraint |
| `@g-constraint-check` | Run compliance check against all active constraints |
| `@g-constraint-upd` | Update an existing constraint |
| `@g-constraint-del` | Delete a constraint |

**Ideas & Discovery**

| Command | What it does |
|---------|-------------|
| `@g-idea-capture` | Capture an idea to IDEA_BOARD.md |
| `@g-idea-review` | Review and evaluate IDEA_BOARD entries |
| `@g-idea-farm` | Proactive codebase scan for improvement opportunities |

**Autonomous Execution**

| Command | What it does |
|---------|-------------|
| `@g-go` | Run autonomously through the backlog (self-review mode — both phases) |
| `@g-go-code` | Implementation-only run — marks tasks `[🔍]`, never `[✅]` |
| `@g-go-review` | Verification-only run — run in a **new agent session** from the coder |
| `@g-go-swarm` | Coordinate multi-agent swarm execution across the backlog |
| `@g-go-code-swarm` | Multi-agent implementation swarm |
| `@g-go-review-swarm` | Multi-agent review swarm |
| `@g-go-go` | Autopilot loop - repeatedly calls `@g-go` until the backlog is clear or all remaining tasks are blocked |
| `@g-mission` | Autonomous completion loop - runs `@g-go` iterations until your stated verifiable condition is met; evaluator self-checks each iteration; turn-budgeted |
| `@g-juggernaut` | Alias for `@g-mission` — unstoppable forward momentum flavor |
| `@g-kamikaze` | Alias for `@g-mission` — all-in commitment flavor |

**Release Management**

| Command | What it does |
|---------|-------------|
| `@g-release-new` | Create a new release entry in `.gald3r/releases/` |
| `@g-release-assign` | Assign tasks/features to a release |
| `@g-release-status` | Show current release status and progress |
| `@g-release-accelerate` | Identify what can be fast-tracked to hit a release target |
| `@g-release-publish` | Finalize and publish a release (CHANGELOG, VERSION, tag) |
| `@g-ship` | Ship a versioned release from `[Unreleased]` CHANGELOG entries - bumps VERSION, tags, optionally publishes GitHub release |

**Personality & Skill Pack Management**

| Command | What it does |
|---------|-------------|
| `@g-pers-list` | List all available personality packs and show which is currently active |
| `@g-pers-pick` | Swap the active personality pack - removes old rules/skills from all platform dirs, installs new ones |
| `@g-skill-pack-list` | List available skill packs and per-skill install status across active platform dirs |
| `@g-skill-pack-add` | Install a skill pack or individual skill to all active platform dirs |
| `@g-skill-pack-del` | Remove a skill pack or individual skill from all active platform dirs |
| `@g-skill-pack-save` | Save a user-evolved skill back into the pack with `_evolved` suffix to survive updates |

**Maintenance**

| Command | What it does |
|---------|-------------|
| `@g-medkit` | `.gald3r/` health check, repair, and version migration |
| `@g-medic` | Targeted repair for a specific `.gald3r/` file or subsystem |
| `@g-tier-setup` | Set up or upgrade gald3r tier in a project (slim → full → adv) |
| `@g-swot-review` | SWOT analysis for the current project phase |
| `@g-dependency-graph` | Generate DEPENDENCY_GRAPH.md from task dependencies |
| `@g-cli-cursor` | Cursor CLI reference and usage patterns |
| `@g-cli-claude` | Claude Code CLI reference and usage patterns |
| `@g-cli-gemini` | Gemini CLI reference and usage patterns |
| `@g-cli-codex` | Codex CLI reference and usage patterns |
| `@g-cli-copilot` | GitHub Copilot CLI reference and usage patterns |

---

### Git Quality Gates

```
@g-git-sanity     # Before committing: detects staged secrets, files over size limits,
                  # and .gald3r/ sync drift between TASKS.md and tasks/ files

@g-git-commit     # Conventional commit format (feat/fix/chore) with task reference
                  # and optional agent footer for autonomous commits

@g-git-push       # Pre-push gate: validates task states, CHANGELOG updated,
                  # release-mode checks README version badge
```

---

## Optional: Docker MCP Server

gald3r is fully functional without any server infrastructure — the file-first architecture means every feature works with plain files. For teams that want semantic search, session memory across machines, Oracle database access, or server-side crawling, the gald3r Docker MCP server adds 42 server-backed tools.

The Docker server is a separate companion component (not included in this template). See the [gald3r Docker server repository](https://github.com/wrm3/gald3r_full) for setup instructions.

| Category | Tools |
|----------|-------|
| **Memory** | `memory_search`, `memory_capture_session`, `memory_context`, `memory_ingest_session`, `memory_sessions`, `memory_capture_insight`, `memory_search_combined`, `memory_setup_user` |
| **Vault** | `vault_search`, `vault_search_all`, `vault_sync`, `vault_read`, `vault_list`, `vault_export_sessions` |
| **Install** | `gald3r_install`, `gald3r_plan_reset`, `gald3r_health_report`, `gald3r_validate_task`, `gald3r_server_status` |
| **Crawling** | `platform_docs_search`, `platform_crawl_trigger`, `platform_crawl_status`, `crawl_add_target`, `crawl_list_targets`, `check_crawl_freshness` |
| **Oracle** | `oracle_query`, `oracle_execute` |
| **MediaWiki** | `mediawiki_page`, `mediawiki_search` |
| **Video** | `video_analyze`, `video_batch_process`, `video_extract_frames`, `video_extract_transcript`, `video_extract_metadata`, `video_get_playlist` |
| **Utility** | `md_to_html`, `config_reload`, `get_service_url` |

---

## Configuration

### Identity

`@g-setup` creates `.gald3r/.identity` with your project details:

```
project_id=<generated-uuid>
project_name=my-project
user_id=<your-user-id>
user_name=YourName
gald3r_version=1.5.1
```

### Vault Location

`vault_location` in `.gald3r/.identity` controls where knowledge is stored:

```
vault_location={LOCAL}                  # Default: .gald3r/vault/ inside this project
vault_location=/path/to/shared/vault    # Shared vault: multiple projects write here
```

A shared vault is opt-in. One-off or client projects should use `{LOCAL}` to keep knowledge isolated.

### Environment Variables (Docker only)

Only needed if you run the optional Docker MCP server. Copy `.env.example` to `.env`:

```bash
POSTGRES_DB=rag_knowledge
POSTGRES_USER=gald3r
POSTGRES_PASSWORD=your_password_here
OPENAI_API_KEY=your-key-here
```

---


---

## Personality Packs

gald3r ships a swappable personality system. Each personality pack is a set of always-apply rules that give agents a consistent character voice across every response. Use `@g-pers-pick` to swap personalities at any time.

**personality-rules** — Always-apply character voice packs (install one at a time)

| Personality | What it adds |
|------------|-------------|
| `silicon_valley_personality` | HBO Silicon Valley cast — Richard, Gilfoyle, Dinesh, Erlich, Jared, and supporting characters across every response |
| `norse_personality` | Norse pantheon startup team — Odin, Thor, Loki, Sindri, Freyja, Tyr, the Norns, and the Nine Realms framing |
| `star_wars_personality` | Star Wars characters — Luke, Vader, Yoda, droids, Mandalore, Andor-era, sequels cast |
| `star_trek_personality` | Star Trek characters — Kirk, Spock, Picard, Janeway, Sisko, Burnham, Pike, Mariner |
| `firefly_personality` | Firefly / Serenity crew — Mal, Zoe, Wash, Kaylee, Inara, Jayne, River, Simon, Book (Mandarin curses included) |
| `bsg_personality` | Battlestar Galactica reimagined — Adama, Roslin, Starbuck, Tigh, Six, Cavil, the Hybrid ("so say we all") |

**fandom-skills** — Encyclopedic mega-fan reference (pairs with personality-rules for deep canon depth)

| Skill | What it covers |
|-------|---------------|
| `silicon-valley-superfan` | Complete HBO Silicon Valley episode guide, character arcs, and technical references |
| `star-trek-megafan` | All Trek series and films: TOS / TNG / DS9 / VOY / ENT / DIS / PIC / SNW / LDS / PRO |
| `star-wars-megafan` | Star Wars canon — films, Mandalorian, Andor, Clone Wars, comics, expanded universe |
| `firefly-serenity-megafan` | Complete Firefly + Serenity 'verse (14 episodes + film + comics) |
| `bsg-megafan` | BSG reimagined — miniseries + 4 seasons + Razor + The Plan + Caprica + Blood & Chrome |
## Optional Skill Packs

Beyond the 195 built-in gald3r system skills, `skill_packs/` contains **142 optional, domain-specific packs across 20 categories** you install on demand. These are not loaded by default — nothing installs until you run the pack's `install.ps1`. Each pack deploys to all IDE targets (`.cursor/`, `.claude/`, `.agent/`, `.codex/`, `.opencode/`).

| Category | Packs | Description |
|----------|-------|-------------|
| `vercel` | 25 | AI SDK, AI Gateway, Next.js, Next Cache, Turbopack, Routing Middleware, Runtime Cache, Vercel Functions, Blob/Storage, Deployments/CI-CD, Chat SDK, Sandbox, Marketplace, Auth, next-forge, next-upgrade, shadcn, Vercel CLI, Vercel Agent, Vercel Workflow, env-vars, knowledge-update, react-best-practices, bootstrap, verification |
| `cursor-team-kit` | 19 | compiler-errors-check, cli-control, ui-control, deslop, ci-fix, merge-conflicts-fix, pr-comments-get, ci-loop, pr-easy-review, branch-pr-new, pr-review-canvas, review-ship, smoke-tests-run, verify-this, review-weekly, work-summary, workflow-from-chats, receiving-code-review, requesting-code-review |
| `superpowers` | 13 | brainstorming, agents-parallel-dispatch, plans-execute, branch-finish, code-review-receive, code-review-request, subagent-development, debug-systematic, tdd, git-worktrees, superpowers-guide, verify-completion, writing-plans, writing-skills |
| `huggingface` | 10 | hf-cli, hf-dataset-viewer, hf-datasets, hf-evaluation, hf-jobs, hf-model-trainer, hf-paper-publisher, hf-tool-builder, hf-trackio, huggingface-gradio |
| `user-skills` | 12 | babysit, canvas, hook-create, rule-create, skill-create, subagent-create, cursor-sdk, skills-migrate, shell, prs-split, statusline, cursor-settings-update |
| `ai-video-tools` | 8 | (AI video generation and editing tools) |
| `cloud-providers` | 16 | Cloudflare DNS, AWS, GCP, Azure, Hetzner, Oracle Cloud, and more |
| `phantom-connect` | 7 | social-login-add, phantom-wallet-mcp, sol-transaction-send, browser-app-setup, react-app-setup, react-native-app-setup, message-sign |
| `startup-tools` | 4 | (Startup toolchain and growth skills) |
| `ai-ml-dev` | 3 | (AI/ML development and training skills) |
| `ai-media` | 2 | Seedance 2.0, Higgsfield cinematic video generation |
| `3d-graphics` | 5 | (3D modeling and rendering skills) |
| `community` | 4 | (Community building and management skills) |
| `content-creation` | 4 | (Content writing and marketing skills) |
| `infrastructure` | 4 | MCP builder, project scaffolding, GitHub integration |
| `blockchain` | 1 | (Blockchain/Web3 development) |
| `create-plugin` | 2 | plugin-scaffold-create, review-plugin-submission |
| `context7` | 1 | context7-mcp — live library docs via Context7 MCP |
| `firecrawl` | 1 | Full web crawling and scraping with LLM-optimized output |
| `continual-learning` | 1 | Continual learning patterns for agent sessions |

```powershell
# Install a pack into the current project
.\skill_packs\infrastructure\install.ps1

# Install into a specific project directory
.\skill_packs\infrastructure\install.ps1 -ProjectRoot "C:\my-other-project"
```

To uninstall: delete the skill directories listed in the pack's `PACK.md`.

---


---

**🤖 ai-media** - AI video generation via Seedance 2.0 and Higgsfield cinematic models

| Skill | What it does |
|-------|-------------|
| `skl-seedance` | Seedance 2.0 text-to-video and image-to-video via fal.ai, VolcEngine, or Replicate |
| `skl-higgsfield` | Higgsfield DoP cinematic image-to-video with NSFW handling and async status polling |

---

**☁️ cloud-providers** - Cloud infrastructure management across 8 major providers

| Skill | What it does |
|-------|-------------|
| `skl-cloudflare-dns` | DNS zones, records, SSL/TLS, wrangler CLI, bulk operations |
| `skl-cloudflare-workers` | Workers, Pages, KV/D1/R2/Durable Objects, Cron triggers |
| `skl-cloudflare-tunnels` | Tunnels, Zero Trust access policies, WARP, Docker integration |
| `skl-aws-iam` | IAM users/roles/policies, STS, Secrets Manager, 5 policy templates |
| `skl-aws-compute` | EC2, Lambda, ECS, App Runner, CDK patterns |
| `skl-aws-storage` | S3, RDS, DynamoDB, EFS, Backup with bucket policy templates |
| `skl-aws-networking` | VPC (3-tier template), Route 53, CloudFront, ALB, VPN, peering |
| `skl-hetzner` | VPS, dedicated, Object Storage, hcloud CLI, Docker cloud-init |
| `skl-digitalocean` | Droplets, App Platform, managed DBs, DOKS, Spaces |

---

**💬 community** - Community management across Discord, Telegram, and Slack

| Skill | What it does |
|-------|-------------|
| `skl-discord` | Discord server setup, bots, moderation, growth playbook, analytics, GitHub/CI webhooks |
| `skl-telegram` | Telegram bots, channels, groups, moderation, notifications, growth, Mini Apps |
| `skl-slack` | Slack workspace management, app/bot dev (Bolt SDK), Block Kit UI, Workflow Builder, webhooks |
**🎬 ai-video-tools** — AI video generation, avatar creation, animated GIFs, explainer production, and multi-platform ad specs

| Skill | What it does |
|-------|-------------|
| `ai-video-generation` | 40+ models via inference.sh CLI: text-to-video, image-to-video, Veo, Wan, Seedance |
| `ai-avatar-lipsync` | OmniHuman/Fabric/PixVerse models; audio-driven lipsync and dubbing workflows |
| `remotion-video` | React-based video: compositions, audio, captions, 3D, transitions, cloud render |
| `animated-gif-creator` | Composable animation primitives, Slack constraints (2MB/64KB), easing and optimization |
| `explainer-video` | Script formulas (AIDA), pacing rules, scene planning, voiceover and music integration |
| `storyboard-creation` | Shot composition, camera angles, movement, continuity; pre-production workflow |
| `video-ad-specs` | TikTok/Instagram/YouTube/Facebook/LinkedIn dimensions, timing requirements, AIDA framework |
| `pipeline-validation` | Multi-agent QA gates: specs, narrative, render readiness, asset handoff checks |

---

**🧊 3d-graphics** — 3D performance optimization, asset pipelines, animation principles, and generative art

| Skill | What it does |
|-------|-------------|
| `3d-performance` | LOD strategies, frustum/occlusion culling, draw call reduction, R3F-specific optimizations |
| `asset-optimization` | gltf-transform pipeline: Draco mesh compression, WebP/KTX2 textures, LOD generation |
| `animation-principles` | Disney's 12 animation principles applied to 3D/game contexts, timing and frame count guidelines |
| `algorithmic-art` | p5.js generative art: seeded randomness, flow fields, particle systems, interactive parameters |

---

**📱 content-creation** — Social strategy, video scripting, storyboarding, and platform ad specs

| Skill | What it does |
|-------|-------------|
| `social-media-marketing` | YouTube/TikTok/Instagram/LinkedIn growth strategy, thumbnails, influencer workflows |
| `storyboard-creation` | Shot composition, angles, movement, continuity for film and animation pre-production |
| `explainer-video` | AIDA script formulas, pacing rules, scene planning, voiceover and music guidance |
| `video-ad-specs` | Platform-specific dimensions, timing, and AIDA framework for paid social |

---

**🤖 ai-ml-dev** — AI/ML development, cloud GPU training, and mathematical animation

| Skill | What it does |
|-------|-------------|
| `ai-ml-development` | Model selection, training loops, evaluation, fine-tuning, RLHF, RAG, MLOps patterns |
| `cloud-gpu-training` | RunPod/Lambda/Vast.ai: SCP workflow, batch sizing, cost estimates, checkpointing |
| `manim-animation` | 3Blue1Brown-style math animations: scenes, LaTeX, graphs, algorithm demos in Python |

---

**🚀 startup-tools** — VC fundraising, business formation, product development, and resource access

| Skill | What it does |
|-------|-------------|
| `startup-vc-fundraising` | Pre-seed through Series C+: pitch decks, investor targeting, term sheets, due diligence |
| `startup-business-formation` | Delaware C-Corp, cap table, 83(b) election, founder vesting, foreign qualification |
| `startup-product-development` | Discovery, MVP scoping, RICE prioritization, stack choice, QA, build vs buy decisions |
| `startup-resource-access` | Cloud credits, AI credits, grants, accelerators, banking tools, community resources |

---

**⛓️ blockchain** — Web3 and blockchain development

| Skill | What it does |
|-------|-------------|
| `web3-blockchain` | EVM/Solana/Cosmos/Bitcoin; Solidity smart contracts; DeFi, NFTs, token design; cross-chain bridging |

---

**☁️ infrastructure** — Cloud engineering, Kubernetes, CI/CD, and MCP server development

| Skill | What it does |
|-------|-------------|
| `cloud-engineering` | AWS/GCP/Azure IaC patterns, Terraform, cost optimization, security best practices |
| `kubernetes-operations` | Workloads, networking, Helm, RBAC, cloud-native ops, troubleshooting runbooks |
| `cicd-pipelines` | GitHub Actions, GitLab CI, Jenkins, Azure DevOps; deployment strategies, quality gates |
| `mcp-builder` | Build MCP servers with FastMCP or Node/TypeScript SDK for AI agent tool integration |

---

## Design Principles

1. **File-first** — Every feature works without Docker or any external service. MCP tools enhance, never gate.
2. **Platform parity** — 12 IDE targets stay synchronized (6 root + 6 template). Cursor, Claude Code, Gemini, Codex, OpenCode, and GitHub Copilot get identical skills, agents, and commands.
3. **Adversarial quality** — Implementation and verification are structurally separated. The same agent cannot do both.
4. **Memory is durable** — Session history, decisions, and research survive across conversations, machines, and IDE switches.
5. **Single source of truth** — Task state lives in files, not in agent memory. Any agent opening the project sees the same state.
6. **Constraints over conventions** — Rules are enforced at session start and at every task completion gate, not suggested once and forgotten.
7. **Topology-aware** — Projects are not islands. The PCAC system treats a multi-repo codebase as a first-class entity with discoverable structure.

---

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines on reporting bugs, requesting features, and contributing to the framework.

gald3r is built with gald3r. The framework develops itself — task specs, acceptance criteria, two-phase review, and all.

## Built With AI

gald3r is an AI development framework, and it is openly built with AI development tools. The same agents the framework provides are the agents that build the framework. Transparency about this is a feature, not a footnote.

Development tools and platforms used to build gald3r:

- **[Cursor](https://cursor.com)** — primary development IDE
- **[Claude Code](https://claude.ai/code)** — architectural reasoning, cross-file refactoring, review
- **[GitHub Copilot](https://github.com/features/copilot)** — inline completions
- **[Gemini CLI](https://github.com/google-gemini/gemini-cli)** — multi-modal and long-context support
- **[OpenAI Codex CLI](https://github.com/openai/codex)** — terminal-first iteration
- **[OpenCode](https://opencode.ai)** — open-source baseline and parity target

Primary human developer: **Warren R. Martel III** ([@wrm3](https://github.com/wrm3)).

If you see AI agent accounts (e.g., `cursoragent`) in the Contributors list, that is intentional — those agents genuinely co-authored commits. Commit messages include `Co-authored-by:` trailers to credit specific AI tools when they materially contributed to a change.

## Plugins & Skill Packs

gald3r is designed to be extended. Third-party skill packs, agents, commands, and hooks are welcome and supported.

**What you can build and distribute:**

- New skill packs that extend the `@g-` command surface
- Domain-specific agents (e.g., security reviewer, data pipeline planner)
- Additional IDE platform support (beyond the 6 built-in)
- Hooks that integrate gald3r with external services
- Skill packs that partially or fully replace built-in functionality (e.g., a different task manager)

**Licensing for plugin authors:**

Plugins and skill packs are treated as **separate works** under the gald3r license. You retain full ownership of your plugin code and may license it however you choose — MIT, Apache, proprietary, paid commercial, subscription, closed-source. gald3r's license does not extend to your work.

**Naming guideline:**

Plugins may identify themselves as **"for gald3r"** or **"gald3r-compatible"** in their description, documentation, and metadata. Plugins must **not** use "gald3r" as the primary name of the product in a way that implies the plugin is, or is an official product of, gald3r itself.

Examples:

- ✅ `video-tools-for-gald3r`
- ✅ `gald3r-compatible task manager`
- ✅ `ACME Skill Pack — works with gald3r`
- ❌ `gald3r-pro`
- ❌ `gald3r-enterprise`
- ❌ `official gald3r extension` (unless authorized)

See [docs/PLUGINS.md](docs/PLUGINS.md) for the full plugin author guide — structure, distribution, publishing, and examples.

---

## License

gald3r is licensed under the **[Fair Source License, version 1.1](LICENSE)**, with the **Apache License 2.0** as the Future License (FSL-1.1-Apache).

**In plain English:**

- You can use gald3r in any project, including commercial products, and sell what you build with it.
- You can modify gald3r for your own use.
- You can write and sell plugins and extensions under any license you choose.
- You **cannot** take gald3r, modify it, and offer the result as a competing product or service.
- Each released version of gald3r automatically becomes available under **Apache 2.0** on its **second anniversary** — so older versions graduate to full open source on a rolling basis.

Commercial license, enterprise terms, or OEM embedding? Contact the author.

---

**gald3r** — *Norse for "song magic." Because the best code is indistinguishable from incantation.*
