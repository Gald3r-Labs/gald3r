<p align="center">
  <img src="logo/Gald3r_Logo_Big.jpg" alt="Gald3r" width="400" />
</p>

<h1 align="center">Gald3r -- AI Dev Framework for 34 AI Coding Tools</h1>

<p align="center">
  File-based memory, task management, and agent orchestration that works across
  Cursor, Claude Code, Copilot, Windsurf, Cline, Roo, Codex, Aider, Kilo Code, Deep Code,
  Hermes, CodeBuddy, AstrBot, OpenHands, Gemini, OpenCode, and 18 more.
</p>

<p align="center">
  <a href="https://www.gald3r.ai">www.gald3r.ai</a> |
  <a href="CHANGELOG.md">Changelog</a> |
  <a href="CONTRIBUTING.md">Contributing</a>
</p>

---

## What is Gald3r?

Gald3r is a framework that runs **inside your AI coding tool** -- not alongside it.
Drop the template for your tool into your project root, and your AI assistant gains:

- **Persistent memory** across sessions (tasks, bugs, plans, constraints)
- **13 specialized agents** (code reviewer, QA engineer, task manager, platformer, etc.)
- **110 skills** for common dev workflows
- **178 commands** invoked directly in chat (`@g-status`, `@g-go`, `@g-medic`)
- **27 hooks** that fire on IDE events (session start, file write, commit)
- **14 rules** that keep agents disciplined every session
- **Cross-platform parity** -- the same framework, tuned per tool

Everything is plain markdown files in your repo. No server, no database, no Docker required.

---

## Platform Support (34 AI Coding Tools) {#platform-support}

Pick your tool and open its folder -- each contains a complete, ready-to-deploy gald3r setup.

### Tier 1 -- Fully Supported

*Tested by gald3r maintainers on every release. Bugs filed against this tier block release.*

| Tool | Folder | Install |
|---|---|---|
| ![Cursor](https://img.shields.io/badge/Cursor-Tier_1-green) | [cursor/](./cursor/) | Copy `cursor/` contents to project root |
| ![Claude Code](https://img.shields.io/badge/Claude_Code-Tier_1-green) | [claude/](./claude/) | Copy `claude/` contents to project root |
| ![Copilot](https://img.shields.io/badge/GitHub_Copilot-Tier_1-green) | [copilot/](./copilot/) | Copy `copilot/` contents to project root |
| ![OpenCode](https://img.shields.io/badge/OpenCode-Tier_1-green) | [opencode/](./opencode/) | Copy `opencode/` contents to project root |
| ![Windsurf](https://img.shields.io/badge/Windsurf-Tier_1-green) | [windsurf/](./windsurf/) | Copy `windsurf/` contents to project root |
| ![Cline](https://img.shields.io/badge/Cline-Tier_1-green) | [cline/](./cline/) | Copy `cline/` contents to project root |
| ![Roo Code](https://img.shields.io/badge/Roo_Code-Tier_1-green) | [roo/](./roo/) | Copy `roo/` contents to project root |
| ![Codex CLI](https://img.shields.io/badge/Codex_CLI-Tier_1-green) | [codex/](./codex/) | Copy `codex/` contents to project root |
| ![CodeBuddy](https://img.shields.io/badge/CodeBuddy_(Tencent)-Tier_1-green) | [codebuddy/](./codebuddy/) | Copy `codebuddy/` contents to project root |
| ![Amp Code](https://img.shields.io/badge/Amp_Code_(Sourcegraph)-Tier_1-green) | [amp/](./amp/) | Copy `amp/` contents to project root |
| ![Continue](https://img.shields.io/badge/Continue-Tier_1-green) | [continue/](./continue/) | Copy `continue/` contents to project root |
| ![Kimi Code](https://img.shields.io/badge/Kimi_Code_(Moonshot)-Tier_1-green) | [kimi/](./kimi/) | Copy `kimi/` contents to project root |
| ![TRAE](https://img.shields.io/badge/TRAE_(ByteDance)-Tier_1-green) | [trae/](./trae/) | Copy `trae/` contents to project root |

### Tier 2 -- Community Supported

*Tested by the community. Contributions and bug reports welcome.*

| Tool | Folder | Install |
|---|---|---|
| ![Aider](https://img.shields.io/badge/Aider-Tier_2-yellow) | [aider/](./aider/) | Copy `aider/` contents to project root |
| ![Augment](https://img.shields.io/badge/Augment-Tier_2-yellow) | [augment/](./augment/) | Copy `augment/` contents to project root |
| ![Goose](https://img.shields.io/badge/Goose-Tier_2-yellow) | [goose/](./goose/) | Copy `goose/` contents to project root |
| ![Warp](https://img.shields.io/badge/Warp-Tier_2-yellow) | [warp/](./warp/) | Copy `warp/` contents to project root |
| ![OpenHands](https://img.shields.io/badge/OpenHands-Tier_2-yellow) | [openhands/](./openhands/) | Copy `openhands/` contents to project root |
| ![Kiro](https://img.shields.io/badge/Kiro-Tier_2-yellow) | [kiro/](./kiro/) | Copy `kiro/` contents to project root |
| ![Kiro CLI](https://img.shields.io/badge/Kiro_CLI-Tier_2-yellow) | [kiro-cli/](./kiro-cli/) | Copy `kiro-cli/` contents to project root |
| ![Junie](https://img.shields.io/badge/Junie-Tier_2-yellow) | [junie/](./junie/) | Copy `junie/` contents to project root |
| ![Replit](https://img.shields.io/badge/Replit-Tier_2-yellow) | [replit/](./replit/) | Copy `replit/` contents to project root |
| ![Gemini CLI](https://img.shields.io/badge/Gemini_CLI-Tier_2-yellow) | [gemini/](./gemini/) | Copy `gemini/` contents to project root |
| ![Kilo Code](https://img.shields.io/badge/Kilo_Code-Tier_2-yellow) | [kilo-code/](./kilo-code/) | Copy `kilo-code/` contents to project root |
| ![Qoder](https://img.shields.io/badge/Qoder_(Alibaba)-Tier_2-yellow) | [qoder/](./qoder/) | Copy `qoder/` contents to project root |

### Tier 3 -- Experimental

*Scaffold available. May have structural gaps. Contributions very welcome.*

| Tool | Folder | Install |
|---|---|---|
| ![Mistral](https://img.shields.io/badge/Mistral-Tier_3-orange) | [mistral/](./mistral/) | Copy `mistral/` contents to project root |
| ![Antigravity](https://img.shields.io/badge/Antigravity-Tier_3-orange) | [antigravity/](./antigravity/) | Copy `antigravity/` contents to project root |
| ![OpenClaw](https://img.shields.io/badge/OpenClaw-Tier_3-orange) | [openclaw/](./openclaw/) | Copy `openclaw/` contents to project root |
| ![Qwen](https://img.shields.io/badge/Qwen-Tier_3-orange) | [qwen/](./qwen/) | Copy `qwen/` contents to project root |
| ![SubQ](https://img.shields.io/badge/SubQ-Tier_3-orange) | [subq/](./subq/) | Copy `subq/` contents to project root |
| ![Deep Code](https://img.shields.io/badge/Deep_Code_(DeepSeek)-Tier_3-orange) | [deepcode/](./deepcode/) | Copy `deepcode/` contents to project root |
| ![Hermes](https://img.shields.io/badge/Hermes_(Nous_Research)-Tier_3-orange) | [hermes/](./hermes/) | Copy `hermes/` contents to project root |
| ![AstrBot](https://img.shields.io/badge/AstrBot-Tier_3-orange) | [astrbot/](./astrbot/) | Upload skills .zip via WebUI |
| ![Void Editor](https://img.shields.io/badge/Void_Editor-Tier_3-orange) | [void/](./void/) | Copy `void/` contents to project root |

---

## Quick Start

**New project?** -> [instructions_new_project.md](./instructions_new_project.md)

**Adding to an existing project?** -> [instructions_existing_project.md](./instructions_existing_project.md)

---

## What's Inside Each Template

Every platform folder contains the same gald3r core, tuned for that tool. The full
component reference below documents what ships in the box as of **v1.8.0**.

| Component | Count | What it is |
|---|---|---|
| Agents | 13 | Specialized AI roles with their own focus and trigger phrases |
| Skills | 110 | Reusable workflows invoked by agents and commands |
| Commands | 179 | Chat commands you type directly (`@g-go`, `@g-status`, ...) |
| Hooks | 27 | Event-driven automation (session start, pre-commit, file write) |
| Rules | 14 | Persistent behavioral standards loaded every session |
| Task system | -- | File-based `.gald3r/` folder for tasks, bugs, plans, constraints |

---

## Agents (13)

Agents are specialized roles your AI assistant adopts for specific work. Each has its
own focus, trigger phrases, and discipline. Invoke them implicitly (describe the work)
or explicitly via the matching command.

| Agent | Role |
|---|---|
| `g-agnt-task-manager` | Creates, updates, completes, and syncs tasks in `.gald3r/`. Owns TASKS.md and task files. |
| `g-agnt-qa-engineer` | Reports and tracks bugs, documents fixes, owns BUGS.md. Fires on any error or defect mentioned. |
| `g-agnt-code-reviewer` | Reviews code for security, quality, and performance. Runs after any significant implementation. |
| `g-agnt-verifier` | Independently verifies completed work against acceptance criteria. Never verifies its own code. |
| `g-agnt-test` | Builds and maintains fast (L1), comprehensive (L2), and regression (L3) test plans. |
| `g-agnt-project` | Project-level concerns: setup, grooming, PLAN.md, PRDs, subsystems, constraints, planning. |
| `g-agnt-project-initializer` | Bootstraps `.gald3r/` in a brand-new project from templates. |
| `g-agnt-infrastructure` | Organizes files, manages folder structure and scope boundaries, prevents over-engineering. |
| `g-agnt-ideas-goals` | Captures ideas to IDEA_BOARD.md and manages project goals in PROJECT.md. |
| `g-agnt-platformer` | Maintains cross-platform parity across all 34 supported AI tools; scans for breaking changes. |
| `g-agnt-workspace-manager` | Manages Workspace-Control: manifests, member repos, lifecycle operations (dry-run first). |
| `g-agnt-pcac-coordinator` | Coordinates cross-project messaging (WPAC): inbox, orders, broadcasts, sync between repos. |
| `g-agnt-marketing` | Deploys growth agents across SEO, GEO, content, community, and launch channels. |

---

## Commands (179)

Type these directly in your AI chat. Commands are grouped by purpose. Common aliases
are noted in parentheses.

### Autonomous execution

The headline feature: hand the agent your backlog and let it work.

| Command | What it does |
|---|---|
| `@g-go` | Run the full task pipeline: pick a task, implement, review, verify, commit. |
| `@g-go-code` | Implementation phase only (code + acceptance gate, no review handoff). |
| `@g-go-review` | Adversarial cold-review phase only (verify someone else's implementation). |
| `@g-go-bugs` | Dedicated bug-fix pipeline: reproduce -> fix -> regression test -> review. |
| `@g-go-go` | Autopilot: loop `@g-go` across the whole backlog with context-aware throttling. |
| `@g-go-swarm` / `@g-go-code-swarm` / `@g-go-review-swarm` / `@g-go-bugs-swarm` | Parallel multi-agent variants (N coders fan out, fan in to review). |
| `@g-mission` | Run until a stated mission condition is achieved. |
| `@g-juggernaut` | High-throughput continuous execution mode. |
| `@g-kamikaze` | Aggressive single-pass execution for low-risk batches. |
| `@g-steer` | Mid-flight course-correction for an in-progress worktree session. |
| `@g-queue` | Queue additional work onto a running pipeline. |

### Tasks

| Command | What it does |
|---|---|
| `@g-task-new` (`@g-task-add`) | Create a new task with full spec and sequential ID. |
| `@g-task-upd` (`@g-task-update`) | Update a task's status, fields, or status history. |
| `@g-task-del` | Delete a task (hard delete for routing errors). |
| `@g-task-archive` | Move terminal tasks from TASKS.md into archive buckets. |
| `@g-task-sync-check` | Validate TASKS.md against the `tasks/` folder for drift. |

### Bugs & quality

| Command | What it does |
|---|---|
| `@g-bug-report` (`@g-bug-add`) | Log a new bug with severity and detail file. |
| `@g-bug-fix` | Work a bug to resolution with regression coverage. |
| `@g-bug-upd` | Update a bug's status or fields. |
| `@g-bug-del` / `@g-bug-archive` | Delete or archive bug records. |
| `@g-qa` | QA workflow entry point. |
| `@g-code-review` (`@g-review`) | Run a structured code review with severity ratings. |
| `@g-test` | Create, maintain, and run multi-level test plans. |
| `@g-swot-review` | Automated SWOT analysis of the current phase. |
| `@g-doctor` | Diagnose project health. |
| `@g-skill-review` | Audit a skill file for quality. |
| `@g-dependency-graph` | Generate/update the task dependency graph. |
| `@g-hotfix-open` | Open a hotfix workstream. |
| `@g-triage` | Intake external backlog (emails, Slack, notes) with human approval gate. |

### Planning, projects & subsystems

| Command | What it does |
|---|---|
| `@g-setup` | Initialize gald3r in a project. |
| `@g-status` | Show session context, active tasks, goals, ideas. |
| `@g-plan` | Create or update PLAN.md (master strategy). |
| `@g-goal` / `@g-goal-update` | Manage project goals in PROJECT.md. |
| `@g-grooming` | Groom and sync `.gald3r/` files. |
| `@g-propose` | Propose new work for the backlog. |
| `@g-report` | Generate a project report. |
| `@g-subsystems` | View the subsystem registry and graph. |
| `@g-subsystem-add` / `-upd` / `-del` | Manage individual subsystem specs. |
| `@g-subsystem-audit` | Audit subsystem boundaries and drift. |
| `@g-subsystem-graph` | Regenerate the subsystem dependency graph. |
| `@g-idea-capture` | Capture an idea to IDEA_BOARD.md instantly. |
| `@g-idea-review` | Review the idea board and promote ideas to tasks. |
| `@g-idea-farm` | Proactive codebase scan for improvement opportunities. |

### Constraints

| Command | What it does |
|---|---|
| `@g-constraint-add` / `-upd` / `-del` | Manage project constraints in CONSTRAINTS.md. |
| `@g-constraint-check` | Verify active constraints before completing work. |

### Features & PRDs

| Command | What it does |
|---|---|
| `@g-feat-new` (`@g-feat-add`) | Stage a new feature. |
| `@g-feat-promote` | Advance a feature through its lifecycle (staging -> shipped). |
| `@g-feat-upd` / `-rename` / `-del` | Manage feature records. |
| `@g-prd-add` / `-upd` / `-del` | Manage PRDs (compliance/audit artifacts). |
| `@g-prd-revise` | Create a sequential revision of a frozen PRD (only sanctioned edit path). |

### Releases & versioning

| Command | What it does |
|---|---|
| `@g-ship` | Promote CHANGELOG [Unreleased] to a version, tag, and optionally publish. |
| `@g-release-propose` | Analyze completed tasks and propose the next semver bump + draft notes. |
| `@g-release-cut` | Accept a proposal, cut a local git tag, commit the release file (no push). |
| `@g-release-new` / `-assign` / `-accelerate` / `-status` / `-publish` | Full release lifecycle management. |
| `@g-pr-open` / `@g-pr-close` | Open and close pull requests. |
| `@g-tier-setup` | Configure product-tier (slim/full/adv) onboarding. |
| `@g-template-export` | Export the full template to a clonable slim repo. |
| `@g-gald3r-export` | Export gald3r framework artifacts. |

### Recon & research

| Command | What it does |
|---|---|
| `@g-recon-repo` | Capture a GitHub repo into the vault as a structured summary. |
| `@g-recon-url` | One-time URL ingestion into the vault. |
| `@g-recon-docs` | Documentation-site ingestion with staleness tracking. |
| `@g-recon-yt` | YouTube transcript ingestion (local, no Docker). |
| `@g-recon-file` | Capture a local file (PDF, DOCX, XLSX, ...) into the vault. |
| `@g-res-deep` | Deep analysis of a captured source -> structured recon report. |
| `@g-res-review` | Triage external sources for adoptable patterns. |
| `@g-res-apply` | Convert a recon report into gald3r artifacts (goals, PRDs, tasks). |
| `@g-crr` | Clean-room rewrite pipeline (harvest -> ideas -> tasks -> native spec). |

### Vault & knowledge

| Command | What it does |
|---|---|
| `@g-vault-search` | Search the file-first knowledge vault. |
| `@g-vault-ingest` | Ingest content into the vault. |
| `@g-vault-status` | Vault health and freshness. |
| `@g-vault-lint` / `-frontmatter-fix` | Lint and repair vault notes. |
| `@g-vault-process-inbox` | Process the vault raw inbox. |
| `@g-learn` | Capture session insights to learned-facts.md and global vault memory. |
| `@g-learn-wrap-up` | End-of-session learning summary. |
| `@g-vocab-add` / `-list` / `-search` | Manage project abbreviation vocabulary. |
| `@g-compress-memory` | Compress non-gald3r memory sections to cut token overhead. |
| `@g-keep-it-simple` | Toggle terse mode (suppress personality + scaffolding). |
| `@g-issue-sync` | Sync issues with the vault. |

### Cross-project coordination (WPAC)

| Command | What it does |
|---|---|
| `@g-wpac-spawn` | Spawn a new gald3r project with bidirectional topology links. |
| `@g-wpac-adopt` / `@g-wpac-claim` | Register a child or parent relationship. |
| `@g-wpac-order` | Push a task to child projects with cascade depth. |
| `@g-wpac-ask` | Child requests parent action (writes parent INBOX). |
| `@g-wpac-read` | Review and action all incoming coordination items. |
| `@g-wpac-notify` | Lightweight [INFO] notification to project INBOXes. |
| `@g-wpac-send-to` / `@g-wpac-move` | Send or migrate files/features between linked projects. |
| `@g-wpac-sync` / `@g-wpac-status` / `@g-wpac-promote` | Sibling sync, status, and member promotion. |

### Workspace-Control

| Command | What it does |
|---|---|
| `@g-wrkspc` | Workspace-Control entry point. |
| `@g-wrkspc-init` | Initialize the workspace manifest (dry-run first). |
| `@g-wrkspc-member-add` / `-remove` / `-list` | Manage workspace members (registry-only). |
| `@g-wrkspc-spawn` / `-adopt` | Spawn or adopt member repos. |
| `@g-wrkspc-status` / `-validate` / `-sync` / `-export` | Workspace lifecycle operations. |
| `@g-workspace-*` | Backwards-compatible aliases for the above. |

### Platform management

| Command | What it does |
|---|---|
| `@g-platform-status` | Show parity status across all 34 platforms. |
| `@g-platform-check` | Check a platform's capability gaps vs. the Cursor reference. |
| `@g-platform-scan` / `-scan-docs` | Scan platform docs for breaking changes. |
| `@g-pers-list` / `@g-pers-pick` | List and pick personality packs. |
| `@g-skill-pack-add` / `-del` / `-list` / `-save` | Manage optional skill packs. |
| `@g-codeowners-gen` | Generate a CODEOWNERS file. |

### CLI quick references

| Command | What it does |
|---|---|
| `@g-cli-claude` / `@g-cli-codex` / `@g-cli-cursor` / `@g-cli-gemini` / `@g-cli-copilot` | Per-tool CLI cheat sheets (headless flags, sessions, MCP, overnight use). |

### Marketing & growth

| Command | What it does |
|---|---|
| `@g-marketing-audit` / `-status` | Audit and report marketing posture. |
| `@g-marketing-content` / `-social` / `-geo` | Content, social, and AI-search-visibility (GEO) work. |
| `@g-marketing-hn` / `-reddit` / `-launch` | Channel-specific launch playbooks. |

### Compliance & security

| Command | What it does |
|---|---|
| `@g-compliance-scan` / `-report` / `-gate` | SCA/license compliance scanning with pass/warn/fail verdicts. |
| `@g-git-commit` | Create a well-structured gald3r-convention commit. |
| `@g-git-push` | Push with optional compliance gate. |
| `@g-git-sanity` | Pre-push sanity checks. |

### Component creation & maintenance

| Command | What it does |
|---|---|
| `@g-skill-new` | Scaffold a new skill (tagging pre-filled). |
| `@g-command-new` | Scaffold a new command. |
| `@g-rule-new` | Scaffold a new rule. |
| `@g-agent-hire` | Research-gated new-agent creation. |
| `@g-create-hook` | Scaffold a new multi-platform hook. |
| `@g-mcp-new` | Scaffold a new MCP integration. |
| `@g-system-rebuild` | Rebuild platform trees from canonical source. |
| `@g-gald3r-optimize` | (Maintainer-only) audit the gald3r corpus for bloat. |
| `@g-theme-edit` | Create and edit HTML report themes. |
| `@g-workflow` | Manage workflow profiles. |

### Updates & health

| Command | What it does |
|---|---|
| `@g-medic` | Tiered `.gald3r/` health and repair (L1 triage -> L4 ecosystem). |
| `@g-medkit` | Quick-fix health toolkit. |
| `@g-update` / `@g-upgrade` | Check for and apply gald3r framework updates. |
| `@g-migrate` | Migrate `.gald3r/` schema versions. |
| `@g-cleanup` | Clean stale artifacts. |
| `@g-curator` | Autonomous skill-library curation and grading. |

---

## Skills (110)

Skills are reusable workflows that agents and commands invoke. They are grouped into
packs below. The core packs ship in every template; platform and CLI packs scale with
the tier you install.

### Project & delivery

`g-skl-project`, `g-skl-plan`, `g-skl-tasks`, `g-skl-bugs`, `g-skl-qa`,
`g-skl-features`, `g-skl-prds`, `g-skl-subsystems`, `g-skl-subsystem-graph`,
`g-skl-dependency-graph`, `g-skl-constraints`, `g-skl-ideas`, `g-skl-status`,
`g-skl-context-builder`, `g-skl-delegate`, `g-skl-verify-ladder`, `g-skl-design`.

### Code review, testing & security

`g-skl-code-review`, `g-skl-review`, `g-skl-test`, `g-skl-security-scan`,
`g-skl-compliance`, `g-skl-dependency-audit`, `g-skl-swot-review`,
`g-skl-graphify`, `g-skl-muninn`.

### Autonomous execution support

`g-skl-git-commit`, `g-skl-github-pr`, `g-skl-verify-ladder`,
`g-skl-auto-triage`, `g-skl-medic`, `g-skl-medkit`.

### Recon & research

`g-skl-recon-repo`, `g-skl-recon-url`, `g-skl-recon-docs`, `g-skl-recon-yt`,
`g-skl-recon-file`, `g-skl-res-deep`, `g-skl-res-review`, `g-skl-res-apply`,
`g-skl-crr`, `g-skl-crawl`.

### Vault & knowledge

`g-skl-vault`, `g-skl-learn`, `g-skl-memory`, `g-skl-monitor`,
`g-skl-knowledge-refresh`, `g-skl-compress-memory`, `g-skl-keep-it-simple`,
`g-skl-yt-video-analysis`.

### Cross-project coordination (WPAC)

`g-skl-workspace`, `g-skl-wpac-spawn`, `g-skl-wpac-adopt`, `g-skl-wpac-claim`,
`g-skl-wpac-order`, `g-skl-wpac-ask`, `g-skl-wpac-read`, `g-skl-wpac-notify`,
`g-skl-wpac-send-to`, `g-skl-wpac-move`, `g-skl-wpac-sync`.

### Release & distribution

`g-skl-ship`, `g-skl-release`, `g-skl-setup`, `g-skl-tier-setup`,
`g-skl-template-export`, `g-skl-gald3r-component-new`, `g-skl-gald3r-optimize`,
`g-skl-curator`.

### Output formats

`g-skl-html-output`, `g-skl-json-output`, `g-skl-toon-output`,
`g-skl-theme-editor`, `g-skl-api-doc-gen`.

### Platform packs (one per supported tool)

`g-skl-platform-cursor`, `g-skl-platform-claude`, `g-skl-platform-copilot`,
`g-skl-platform-codex`, `g-skl-platform-opencode`, `g-skl-platform-gemini`,
`g-skl-platform-windsurf`, `g-skl-platform-cline`, `g-skl-platform-roo`,
`g-skl-platform-aider`, `g-skl-platform-augment`, `g-skl-platform-goose`,
`g-skl-platform-warp`, `g-skl-platform-openhands`, `g-skl-platform-kiro`,
`g-skl-platform-kiro-cli`, `g-skl-platform-junie`, `g-skl-platform-replit`,
`g-skl-platform-mistral`, `g-skl-platform-qwen`, `g-skl-platform-openclaw`,
`g-skl-platform-subq`, `g-skl-platform-opencode`, `g-skl-platform-crawl`.

### CLI packs

`g-skl-cli-claude`, `g-skl-cli-codex`, `g-skl-cli-copilot`, `g-skl-cli-cursor`,
`g-skl-cli-gemini`, `g-skl-cli-jcode`, `g-skl-cli-opencode`.

### Specialty & integrations

`g-skl-browser-use`, `g-skl-comfyui`, `g-skl-oracle`, `g-skl-marketing`.

*New in the 1.6 -> 1.7 line:* `g-skl-security-scan`, `g-skl-context-builder`,
`g-skl-delegate`, `g-skl-graphify`, `g-skl-auto-triage`, `g-skl-gald3r-optimize`,
`g-skl-comfyui`, `g-skl-cli-jcode`.

---

## Rules (14)

Rules are persistent behavioral standards your AI assistant loads every session. They
encode the discipline that keeps autonomous work safe and consistent.

| Rule | What it enforces |
|---|---|
| `g-rl-00-always` | Response footer (timestamp, tools, context budget), large-file refactor nudges, MCP/tool reminders, and OS/shell routing. |
| `g-rl-01-documentation` | Documentation file placement and naming standards (docs/ folder, timestamped names). |
| `g-rl-02-git_workflow` | Git workflow conventions: commit message format and branch standards. |
| `g-rl-04-code_reusability` | Code reusability and DRY enforcement. |
| `g-rl-08-powershell` | PowerShell standards for Windows 10/11. |
| `g-rl-09-python_venv` | UV package manager and virtual-environment standards for Python projects. |
| `g-rl-25-gald3r_session_start` | Session-start protocol: sync validation and context display. |
| `g-rl-26-readme-changelog` | Update CHANGELOG.md and README.md when completing user-facing feature work. |
| `g-rl-33-enforcement_catchall` | Ambient guardrails active regardless of which agent is loaded (error logging, commit offers, push gate). |
| `g-rl-34-todo_completion_gate` | Stub/TODO lifecycle: stubs require forward-linking comments and follow-up tasks. |
| `g-rl-35-bug-discovery-gate` | Bugs found during work are never silently ignored; pre-existing bugs are logged. |
| `g-rl-36-workspace-member-gald3r-guard` | Workspace member `.gald3r/` policy (autonomous vs. marker-only repos). |
| `g-rl-37-think-in-code` | Use code for deterministic decisions; reserve the model for judgment. Context-reduction pattern. |
| `g-rl-38-component-creation-standards` | Subsystem tagging required on all framework components; coding-agent discipline. |

A `rally` integration rule and a Silicon Valley personality pack also ship and activate
when configured.

---

## Hooks (27)

Hooks are scripts that fire automatically on IDE/agent lifecycle events. They are wired
per platform (Cursor `hooks.json`, Claude Code `settings.json`, etc.) and run silently.

### Session lifecycle

| Hook | Fires on |
|---|---|
| `g-hk-session-start` | Session init -- loads context, surfaces tasks/constraints/inbox. |
| `g-hk-session-end` | Session close. |
| `g-hk-agent-complete` | Agent/stop lifecycle. |
| `g-hk-pre-session-trace` / `g-hk-post-session-trace` | Session tracing. |

### Tool & command guards

| Hook | Fires on |
|---|---|
| `g-hk-pre-tool-call` | Before tool calls -- compresses noisy shell output, preserves full log. |
| `g-hk-pre-tool-call-gald3r-guard` | Guards `.gald3r/` access without an active agent. |
| `g-hk-pre-tool-call-member-gald3r-guard` | Enforces member-repo `.gald3r/` marker policy. |
| `g-hk-pre-tool-call-prd-freeze` | Blocks edits to frozen (released) PRDs. |
| `g-hk-validate-shell` | Validates shell commands before execution. |

### Git & quality

| Hook | Fires on |
|---|---|
| `g-hk-pre-commit` / `g-hk-pre-push` | Pre-commit and pre-push gates. |
| `g-hk-component-tag-check` | Pre-commit: enforce subsystem tagging on framework components. |
| `g-hk-encoding-normalize` | Normalize encoding (CRLF/LF, BOM policy); content-aware binary skip. |
| `g-hk-ggo-stop-detect` | Detect unauthorized autopilot halts and re-invoke (BUG-107 guard). |

### Skills, learning & timing

| Hook | Fires on |
|---|---|
| `g-hk-pre-skill-timing` / `g-hk-post-skill-timing` | Skill execution timing. |
| `g-hk-nightly-learn` | Nightly learning pass. |
| `g-hk-graph-update` | Update the code/dependency graph. |

### Vault & workspace

| Hook | Fires on |
|---|---|
| `g-hk-vault-resolve` / `g-hk-vault-verify` / `g-hk-vault-reindex` / `g-hk-vault-migrate` | Vault path resolution, verification, reindex, migration. |
| `g-hk-pcac-inbox-check` | Cross-project INBOX conflict gate. |
| `g-hk-wrkspc-manifest-check` | Validate the workspace manifest. |
| `g-hk-setup-user` | First-run user setup. |
| `raw-inbox-watcher` | Vault raw-inbox processor (manual trigger). |

---

## The .gald3r/ Folder

Everything gald3r remembers lives in a single `.gald3r/` folder in your repo -- plain
markdown and YAML, fully diffable, fully yours.

```
.gald3r/
  .identity          project id, type, version
  PROJECT.md         mission and goals
  PLAN.md            master strategy
  TASKS.md           task index
  tasks/             individual task files (open/in-progress/completed/...)
  BUGS.md            bug index
  bugs/              individual bug files
  CONSTRAINTS.md     project constraints
  SUBSYSTEMS.md      subsystem registry + graph
  subsystems/        per-subsystem specs
  FEATURES.md        feature pipeline
  IDEA_BOARD.md      captured ideas
  learned-facts.md   session learning
  releases/          release notes
  logs/              audit logs
```

---

## Key Capabilities

- **Autonomous pipeline** -- `@g-go-go` works your backlog end to end: implement, adversarial cold review, verify, commit. Swarm variants run multiple agents in parallel.
- **Adversarial review** -- the agent that verifies a task is never the one that wrote it. Implementation and review are separate phases with separate context.
- **Cross-project coordination (WPAC)** -- link projects into parent/child/sibling topologies and push tasks, requests, and broadcasts between them.
- **File-first vault** -- Obsidian-compatible knowledge store with recon ingestion from repos, URLs, docs sites, YouTube, and local files.
- **Constraints & PRDs** -- hard project constraints enforced at session start; frozen PRDs for compliance and audit trails.
- **Personality packs** -- optional character voices layered over technical output.

Optional Docker MCP backend (PostgreSQL/pgvector) adds semantic memory and monitoring
for the advanced tier; the core framework needs none of it.

---

## Releases

See [releases/](./releases/) for release notes and [CHANGELOG.md](./CHANGELOG.md) for full history.

Latest: **v1.8.0** -- Wiki Launch + GitHub Discussions + Test Harness + 35-Platform Sweep

---

## Contributing

See [CONTRIBUTING.md](./CONTRIBUTING.md). Platform contributions especially welcome for Tier 2 and Tier 3 tools.

---

*Built with gald3r. Runs on gald3r.*
