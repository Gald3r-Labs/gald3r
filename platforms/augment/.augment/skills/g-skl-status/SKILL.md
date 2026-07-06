---
name: g-skl-status
description: Show project status — session context, active tasks, phase progress, goals, ideas.
token_budget: low
subsystem_memberships: [TASK_MANAGEMENT]
---
# gald3r-status

## When to Use
Session start, checking project health, @g-status command.

## PCAC Inbox Gate

At the start of this skill, determine whether the project is a PCAC participant. PCAC is active only when `.gald3r/linking/link_topology.md` declares at least one parent/child/sibling relationship, or `.gald3r/PROJECT.md` explicitly declares PCAC project linking relationships. A Workspace-Control manifest and local `INBOX.md` alone do not make a project part of a PCAC group.

Only when PCAC is active, call `g-hk-pcac-inbox-check.ps1 -BlockOnConflict` when present. `INBOX CONFLICT GATE` blocks status work until `@g-pcac-read` resolves conflicts. `g-medic` L1 uses its own non-blocking health gate before blocking higher-risk work. Non-conflict requests, broadcasts, and syncs remain advisory and should be surfaced in output. If PCAC is not active, skip the hook and report `PCAC: not configured / skipped`.

## Steps

1. **Load session context** (if files exist):
   ```
   📌 SESSION CONTEXT
   Mission: [1 line from PROJECT.md]
   Project type: [project_type from .identity] | github_integration: [enabled/disabled]
   Goals: G-01: [name] | G-02: [name]
   Phase: [current phase name and status]
   Ideas: [N] active on IDEA_BOARD
   ```

   **Project type line (T1283)**: read `project_type=` from `.gald3r/.identity` (default
   `software_development` if absent — log silently, never error). The active workflow profile is
   `<project_type>.yaml` under `.gald3r/config/workflow_profiles/`. `github_integration` is
   `enabled` only when `project_type=software_development` (the GitHub bundle is gated on that type
   per T1285+); otherwise `disabled`. No-op silently when invoked outside a gald3r project.

   **Workflow line (T1239)**: resolve the active profile via the loader
   (`gald3r project-type resolve` in the active skill folder — see g-skl-tasks "Reading the
   active profile") and surface it as a dedicated session-context line:
   ```
   Workflow: Content Creation (content_creation.yaml)
   ```
   Use the profile's `name` field and source filename. When the loader falls back
   to `freeform`/`software_dev`, show that resolved profile. Skip silently when no
   `.gald3r/config/workflow_profiles/` directory exists (pre-T1238 installs).

   **Status labels from the profile (T1239 — AC2)**: any phase/active/ready/done
   counts and badges in the output use the active profile's `task_statuses[]`
   `symbol` + human label, **not** hardcoded `[🔄]`/`In-Progress`. For a
   `content_creation` project this renders e.g. `🎬 In Production` instead of
   `🔄 In Progress`. The `software_dev` profile resolves to the legacy labels, so
   code repos are unchanged.

   **PR column (T1293)**: when any task has a `pr_url` frontmatter field, add a compact `PR`
   column to the task lines — `#1234 (ready)` / `#1234 (merged)` derived from `pr_url` + `pr_status`.
   Omit the column when no task has a PR (keeps non-software / integration-off projects clean).
   This is a **pure display read of task frontmatter — never a GitHub API call**. `--pr-detail`
   expands to full URLs and any cached check status.

2. **Run sync validation** (brief):
   - TASKS.md ↔ task files: X synced, Y issues
   -    - SUBSYSTEMS.md: fresh / stale
   - 
3. **Workspace-Control snapshot** (quiet by default):

   Check for the canonical registry:

   ```text
   .gald3r/linking/workspace_manifest.yaml
   ```

   - If absent: omit the Workspace-Control section unless the user explicitly asks for workspace status.
   - If present: reuse `g-skl-workspace STATUS` / `VALIDATE` behavior and include a compact section.
   - Do not infer workspace members from sibling folders, `template_*` folders, remotes, or PCAC topology.
   - Keep PCAC separate: PCAC reports topology, INBOX, orders, requests, and peer snapshots; Workspace-Control reports manifest-backed local member scope.

   Suggested compact output:

   ```text
   Workspace-Control: <gald3r_source> Workspace-Control Bootstrap (active_bootstrap)
   Manifest: .gald3r/linking/workspace_manifest.yaml
   Owner: <gald3r_source> | Controlled members: 3
   Members: <template_slim> (planned_clean_member, path missing, writes blocked), <template_full> (...), <template_adv> (...)
   Routing: valid policies docs_only, generated_output, source_only, multi_repo
   Current work scope: task/bug workspace_repos=<ids or current repo only>; workspace_touch_policy=<policy or default current-repo>
   Boundary: report-only; Task 177 defers backend, UI, Docker/Kubernetes/MCP, Valhalla, and Yggdrasil systems.
   ```

   When member paths exist, report git cleanliness per member repo, not from the control repo:

   ```text
   Git: <template_full> clean | <template_adv> dirty (2 files) | <template_slim> missing
   ```

   If the active task or bug has `workspace_repos` / `workspace_touch_policy`, show it in one line near active work. Omitted metadata means current repository only.

4. **Phase progress summary**:
   ```
   Phase 1: Foundation [🔄] — 3/8 tasks complete (37%)
     🔄 Active:  task102_auth_layer (claimed 2h ago)
     📋 Ready:   task103_api_endpoints, task104_db_migrate
     ❌ Blocked: task105_deploy (waiting on task103)
   ```

5. **Health indicators**:
   - Any tasks in `[🔄]` for > 8 hours → flag as stale
   - Any tasks in `[🔍]` for > 4 hours → flag for verification timeout
   - Phase completion: any phase where all tasks are `[✅]` but not archived
   - Active bugs: count from BUGS.md

6. **Experiment status** (if `.gald3r/experiments/EXPERIMENTS.md` exists):
   ```
   🧪 EXPERIMENTS
   Active: EXP-001 — {title} (Stage 3/6 ✅✅🔄[ ][ ][ ])
     Hypothesis: HYP-001 ({status})
     Next gate: Stage 3 — {name}
   Planned: EXP-002 — {title}
   ```
   - Flag stale experiments: any stage `[🔄]` for >48h

7. **Next recommended actions** (top 3):
   - Highest priority unblocked `[📋]` tasks
   - Any `[🔍]` tasks needing verification by different agent
   - Any overdue heartbeats

8. **Cross-project advisories** (if `.gald3r/PROJECT.md` has a **Project Linking** section):

   Read `.gald3r/linking/INBOX.md` and categorize:

   a. **CONFLICTS** → Surface as `⚠️ WARNING` before anything else (not advisory — these gate planning):
   ```
   ⚠️ CROSS-PROJECT CONFLICT — requires resolution before planning:
     CONF-001: [parent-A] says "[instruction A]" | [parent-B] says "[instruction B]"
     Subsystem: [name] — run @g-inbox to resolve
   ```

   b. **Requests, broadcasts, peer syncs** → Advisory section at the bottom:
   ```
   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
   Cross-Project Advisories (non-blocking):
   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
     📨 [parent] → broadcast: [subject] [task NNN created]
     🔄 [sibling] → peer sync: [contract] updated [task NNN created]
     💬 [sibling] → advisory: [note, no action yet]
     📤 [child] → request pending: [brief description]
   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
   ```

   If INBOX is empty or has no open items: omit this section entirely.

## Workspace Reporting Guardrails

- Use `.gald3r/linking/workspace_manifest.yaml` as the only canonical Workspace-Control registry.
- Keep non-workspace projects quiet: absent registry means no section by default.
- Include active manifest path, owner ID, controlled member count, member IDs, lifecycle status, path reachability, write policy summary, and per-member git cleanliness when paths are reachable.
- Include current task/bug `workspace_repos` and `workspace_touch_policy` only when metadata exists or the user asks for routing detail.
- Cite Task 177 boundaries when a user might expect backend/UI/control-plane status: those systems are deferred and must not appear as missing or broken bootstrap deliverables.
- For deeper detail, point to `@g-workspace-status` and `@g-workspace-validate` instead of expanding `@g-status` into a full manifest dump.


## HTML Output (`--html`) — T1318

When invoked with `--html` (or AGENT_CONFIG `output_format: html|both`), render this
report as themed HTML instead of / in addition to markdown:

1. Assemble the report body as an HTML fragment following the `docs/templates/report.html` structure.
2. Invoke **g-skl-html-output** `RENDER` with template `report`, the body fragment, and a topic slug.
3. g-skl-html-output links the active theme (`docs/themes/_active.css`, T1328) and writes a
   timestamped file to `html_output_dir` (default `docs/`) per the g-rl-01 naming convention.

Flags: `--html` forces HTML, `--md` forces markdown. With neither flag, AGENT_CONFIG
`output_format` decides (default `markdown` — current behavior, unchanged).
Example: `g-status --html`. Coordination files (TASKS.md, task specs) are never HTML.
