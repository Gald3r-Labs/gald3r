---
name: g-skl-status
description: Show project status — session context, active tasks, phase progress, goals, ideas.
---
# gald3r-status

## When to Use
Session start, checking project health, @g-status command.

## PCAC Inbox Gate

At the start of this skill, call `g-hk-pcac-inbox-check.ps1 -BlockOnConflict` when present. `INBOX CONFLICT GATE` blocks status work until `@g-pcac-read` resolves conflicts. `g-medic` L1 uses its own non-blocking health gate before blocking higher-risk work. Non-conflict requests, broadcasts, and syncs remain advisory and should be surfaced in output.

## Steps

1. **Load session context** (if files exist):
   ```
   📌 SESSION CONTEXT
   Mission: [1 line from PROJECT.md]
   Goals: G-01: [name] | G-02: [name]
   Phase: [current phase name and status]
   Ideas: [N] active on IDEA_BOARD
   ```

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
   Workspace-Control: gald3r_dev Workspace-Control Bootstrap (active_bootstrap)
   Manifest: .gald3r/linking/workspace_manifest.yaml
   Owner: gald3r_dev | Controlled members: 3
   Members: gald3r_template_slim (planned_clean_member, path missing, writes blocked), gald3r_template_full (...), gald3r_template_adv (...)
   Routing: valid policies docs_only, generated_output, source_only, multi_repo
   Current work scope: task/bug workspace_repos=<ids or current repo only>; workspace_touch_policy=<policy or default current-repo>
   Boundary: report-only; Task 177 defers backend, UI, Docker/Kubernetes/MCP, Valhalla, and Yggdrasil systems.
   ```

   When member paths exist, report git cleanliness per member repo, not from the control repo:

   ```text
   Git: gald3r_template_full clean | gald3r_template_adv dirty (2 files) | gald3r_template_slim missing
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
