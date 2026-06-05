---
schema: product-systems-v1
gald3r_version: 1.10.0
defined_groups:
  - TASK_MANAGEMENT
  - BUG_AND_QUALITY
  - MEMORY_AND_KNOWLEDGE
  - VAULT_AND_RESEARCH
  - WORKSPACE_COORDINATION
  - PROJECT_IDENTITY_SETUP
  - PLATFORM_INTEGRATION
  - AGENT_ORCHESTRATION
  - RELEASE_AND_VERSIONING
  - UI_AND_OUTPUT
  - SECURITY_AND_COMPLIANCE
  - LOGGING_SYSTEM
  - MARKETING_GROWTH
---

# Product Systems — Canonical Subsystem Group Registry

> **Purpose.** This file is the single source of truth for the valid values of the
> `subsystem_memberships:` front-matter field (`.md` components) and the
> `# @subsystems:` comment (`.ps1` components). It is read by `g-rl-38`
> (component-creation tagging), `g-rl-25` (session-start "Systems: N defined" line),
> `g-skl-subsystems`, `g-skl-medic`, `@g-subsystem-audit`, and `@g-system-rebuild`.
>
> Every gald3r framework component MUST tag itself with one or more of the groups
> listed in `defined_groups:` above. Tagging a component with a group **not** in this
> list is a validation failure (see the Layer-0 test `T0.2`).
>
> **History.** Restored 2026-06-03 during the salvage audit — this file was referenced
> framework-wide but had been lost. `MARKETING_GROWTH` was added at the same time to
> stop the 9 marketing components from polluting `AGENT_ORCHESTRATION`.

## Defined Groups

| Group | Function | Representative components |
|---|---|---|
| `TASK_MANAGEMENT` | Task lifecycle and the autonomous `@g-go*` pipeline. | `g-skl-tasks`, `g-agnt-task-manager`, `g-go*`, `g-dependency-graph`, `g-grooming`, `g-report`, `g-mission` |
| `BUG_AND_QUALITY` | Bug intake/lifecycle, QA, code review, verification, test plans, SWOT. | `g-skl-bugs`, `g-skl-qa`, `g-skl-code-review`, `g-skl-test`, `g-skl-verify-ladder`, agents `qa-engineer`/`code-reviewer`/`verifier`/`test` |
| `MEMORY_AND_KNOWLEDGE` | Session memory, learned facts, compression, code-graph (Muninn), context building. | `g-skl-memory`, `g-skl-learn`, `g-skl-compress-memory`, `g-skl-muninn`, `g-skl-graphify`, `g-skl-context-builder`, `g-skl-knowledge-refresh` |
| `VAULT_AND_RESEARCH` | File-first vault + recon ingestion (repos/URLs/docs/YouTube/files) and research→artifact conversion. | `g-skl-vault`, `g-skl-recon-*`, `g-skl-res-*`, `g-skl-crawl`, `g-skl-crr`, `g-skl-yt-video-analysis` |
| `WORKSPACE_COORDINATION` | Cross-project messaging (WPAC/WPAC) and manifest-backed Workspace-Control. | `g-skl-workspace`, `g-skl-wpac-*`, agents `wpac-coordinator`/`workspace-manager` |
| `PROJECT_IDENTITY_SETUP` | Bootstrap, identity, constraints, plan, features, PRDs, subsystem registry, ideas/goals, health/repair. | `g-skl-setup`, `g-skl-project`, `g-skl-plan`, `g-skl-features`, `g-skl-prds`, `g-skl-constraints`, `g-skl-subsystems`, `g-skl-ideas`, `g-skl-medic`, `g-skl-medkit` |
| `PLATFORM_INTEGRATION` | Per-IDE parity packs and CLI references for 34 tools; IDE-specific hooks/rules. | `g-skl-platform-*`, `g-skl-cli-*`, `g-platform-*`, `g-create-hook`, `g-mcp-new` |
| `AGENT_ORCHESTRATION` | The `@g-go` pipeline discipline, delegation, swarm coordination, the Python SDK, curation. | `g-skl-delegate`, `g-skl-curator`, `g-skl-oracle`, `agents/sdk/`, rules `g-rl-00`/`g-rl-33`/`g-rl-37` |
| `RELEASE_AND_VERSIONING` | Semver, CHANGELOG promotion, release lifecycle, git commit/push gates, PRs. | `g-skl-ship`, `g-skl-release`, `g-skl-git-commit`, `g-skl-github-pr`, `g-ship`, `g-release-*`, `g-feat-*`, rule `g-rl-02` |
| `UI_AND_OUTPUT` | Report rendering (HTML/JSON/TOON), themes, design, API docs, terse/persona presentation. | `g-skl-html-output`, `g-skl-json-output`, `g-skl-toon-output`, `g-skl-theme-editor`, `g-skl-design`, `g-skl-api-doc-gen`, `g-skl-keep-it-simple`, `g-pers-*` |
| `SECURITY_AND_COMPLIANCE` | SCA/license scanning, dependency audit, security scan, git sanity, compliance gates, CODEOWNERS. | `g-skl-compliance`, `g-skl-security-scan`, `g-skl-dependency-audit`, `g-compliance-*`, `g-git-sanity`, `g-codeowners-gen` |
| `LOGGING_SYSTEM` | Logging, session tracing, monitoring, diagnostics, output compression. | `g-skl-monitor`, hooks `g-hk-claude-chat-logger`, `g-hk-pre/post-session-trace`, `g-hk-pre-tool-call`, `g-hk-nightly-learn` |
| `MARKETING_GROWTH` | Growth across SEO/GEO, content, social, community, launch channels. | `g-skl-marketing`, `g-agnt-marketing`, `g-marketing-*` |

## Tagging Rules

- Components may belong to more than one group (e.g. `g-skl-crr: [VAULT_AND_RESEARCH, AGENT_ORCHESTRATION]`).
- A command and the skill it delegates to should normally share at least one group.
- `UNGROUPED`/`UNCATEGORIZED` is a temporary value only — it must be resolved to a real group within the same session.
- PowerShell components tag via `# @subsystems: GROUP` in the first 15 lines.

## Recommended future groups (not yet active)

These are noted by the salvage audit as candidates but are **not** in `defined_groups:` yet
(adding a group means retagging its members and updating `T0.2`):

- `MEDIA_GENERATION` — for `g-skl-comfyui` and any future image/video generation skills
  (currently filed under `UI_AND_OUTPUT` as the least-bad fit).
- `GIT_WORKFLOW` — would split git-specific concerns out of `RELEASE_AND_VERSIONING`.
