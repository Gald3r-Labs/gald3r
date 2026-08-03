---
name: g-skl-status
description: Show project status — session context, active tasks, phase progress, goals, ideas.
token_budget: low
subsystem_memberships: [TASK_MANAGEMENT]
---

## HELP CONTRACT (T442 — cross-platform, non-substitutable)

If the invoking command's arguments are EXACTLY `-h`, `--help`, or `help` (one
token, nothing else): do NOT run any operation of this skill. Respond ONLY with a
compact usage card — the command's name, its one-line purpose, each documented
argument/option on its own line (or "none"), and the path to its command file —
then STOP. Read-only: no `.gald3r/` writes, no state changes, no task/bug
creation. This block lives in the SKILL (not a rule) because skills are the
execution layer on every supported platform; rules are optional context on most.

# gald3r-status

## When to Use
Session start, checking project health, @g-status command.

## WPAC Inbox Gate

At the start of this skill, determine whether the project is a WPAC participant. WPAC is active only when `.gald3r/linking/link_topology.md` declares at least one parent/child/sibling relationship, or `.gald3r/PROJECT.md` explicitly declares WPAC project linking relationships. A Workspace-Control manifest and local `INBOX.md` alone do not make a project part of a WPAC group.

Only when WPAC is active, call `g-hk-wpac-inbox-check.py -BlockOnConflict` when present. `INBOX CONFLICT GATE` blocks status work until `@g-wpac-read` resolves conflicts. `g-medic` L1 uses its own non-blocking health gate before blocking higher-risk work. Non-conflict requests, broadcasts, and syncs remain advisory and should be surfaced in output. If WPAC is not active, skip the hook and report `WPAC: not configured / skipped`.

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
   - Do not infer workspace members from sibling folders, `template_*` folders, remotes, or WPAC topology.
   - Keep WPAC separate: WPAC reports topology, INBOX, orders, requests, and peer snapshots; Workspace-Control reports manifest-backed local member scope.
   - **Composed-capability preflight (BUG-515)**: `gald3r workspace status --json` / `gald3r workspace validate --json` are `server_bridge`-backed verbs that only work through the COMPOSED console entrypoint (`gald3r_core.entry:main`). A stale bare-PATH `gald3r` executable — one built before this capability existed, or one that resolves to the deliberate uncomposed `gald3r_core.cli.main:main` fallback — exits 2 with the opaque `no composed server_bridge capability for this verb in this process` message and gives the operator no reason why. Before running the probe, check whether cwd is at or inside a gald3r_core SOURCE checkout (a directory carrying its own `pyproject.toml` + `src/gald3r_core/platform/pipeline/neutral_source/` — the same checkout marker `cli/_build_fingerprint.py`'s `_find_checkout_root` uses for the `--version` build-drift warning):
     - **Inside a checkout**: run the probe as `uv run gald3r workspace status --json` (and `uv run gald3r workspace validate --json` when VALIDATE also runs) instead of a bare `gald3r` invocation — `uv run` always resolves the checkout's own current, composed build regardless of what stale executable shadows it on PATH.
     - **If `uv` is unavailable** and a bare `gald3r` call is unavoidable: run `gald3r --version` and `uv run gald3r --version` first and compare the trailing `(build <hash>)` fingerprints BEFORE calling the capability-dependent probe. A mismatch means the bare PATH binary is stale relative to this checkout — stop and report a direct diagnosis instead of invoking the probe:
       ```text
       ⚠️ Stale installed gald3r binary detected (build <bare_hash>) vs current source checkout (build <source_hash>).
       Workspace-Control status was not collected — rerun via `uv run gald3r workspace status --json`, or reinstall gald3r from this checkout.
       ```
     - **Outside a checkout** (the normal case for every installed/consumer project): invoke `gald3r workspace status --json` as before — there is no dual-build ambiguity to guard against there.

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

4a. **Release Pipeline block (T419)** — rendered **only when `tasks/awaiting-verification/` has content** (the awaiting state folder; the spec's `tasks/awaiting/` is the awaiting-verification status). Read each awaiting task's `release_hold` frontmatter field and group:

   ```
   🚀 Release Pipeline
      awaiting-verification/ (ready for staging):  2
         T1273 - copilot-instructions from template rules
         T1278 - gald3r_install graph init offer
      Held - manual:         1
         T1055 - plugin lifecycle hooks
      Held - sync_required:  1
         T0890 - API contract (sync: gald3r_agent/T890)
   ```

   - "ready for staging" = `release_hold: none` (or field omitted). "Held" = `manual` / `sync_required`.
   - **Nudge (required)**: whenever ≥1 awaiting task has `release_hold: none`, append:
     ```
     💡 {N} task(s) ready to ship (release_hold: none) — run @g-ship to stage them.
     ```
   - Omit the entire block when `tasks/awaiting-verification/` is empty (keeps the report clean).
   - Read-only — never mutates `release_hold`. Set/clear via `@g-task set-release-hold` / `clear-release-hold`.

4b. **Severity / Value Breakdown (ALWAYS INCLUDED — not optional)**: run `gald3r bug list`
   and `gald3r task list` and surface their subtotal histograms verbatim, **including the
   legend line each prints**. This makes the backlog legible at a glance ("a few real fires
   vs. a pile of nitpicks") and is high-value enough that it appears on EVERY status — never
   behind a flag.

   **NON-SUBSTITUTABLE (BUG-394).** These two commands MUST actually be EXECUTED and their
   band-chart header blocks (bars + counts + legend) pasted into the report **verbatim** —
   the charts are engine-drawn output, not derivable data. Hand-rebuilt tables, your own
   histogram math, or a summary sentence are NOT acceptable substitutes; a status report
   without BOTH charts is an incomplete report. g-rl-37 script-collapse does NOT exempt
   these calls — if you collapse the status sweep into one script, invoke both verbs from
   INSIDE it (`subprocess.run(["gald3r","task","list"], ...)` etc.) and capture their
   stdout. The charts cost zero agent tokens to draw (Python renders them at the user's
   terminal); the only way to lose them is to skip the calls:

   ```
   🎯 Severity / Value Breakdown
   Bugs by severity (damage):   9-10=0  7-8=10  5-6=25  1-4=60
      9-10 data loss/leak/destruction · 7-8 crash/security · 5-6 real bug/token-waste · 1-4 nitpick/cosmetic
   Tasks by value (if done):    9-10=12  7-8=127  5-6=148  1-4=150
      9-10 release/demo-critical (the moat) · 7-8 major feature · 5-6 useful/user-docs · 1-4 minor/busywork
   ```

   Numbers come from the numeric 1-10 triage scale (`severity_scale.py`: SEVERITY_RUBRIC for
   bugs, TASK_VALUE_RUBRIC for tasks). A record with no numeric score derives one from its
   `severity`/`priority` word, so legacy items still bucket correctly.

   **`gald3r status`'s own score-band charts (T508 — a single-call alternative for this
   breakdown alone).** `gald3r status --json` (T494) now ALSO returns two DB-backed 1-10
   histograms, computed at zero extra query cost inside that same command (no separate round
   trip beyond the `status` call itself):
   - `tasks.open_by_value` — open tasks (excludes completed/verified/closed/cancelled)
     bucketed 1-10 by their resolved value score.
   - `bugs.open_by_severity_score` — open bugs (respecting `--min-severity`, same set
     `bugs.open_by_severity` already reports) bucketed 1-10 by their resolved damage score.

   Each histogram carries `bins` (the raw 1-10 counts), `total`, and the **derived-vs-stored
   split**: `scored_directly` (rows whose DB `priority_score`/`severity_score` column was
   already populated) vs. `derived_from_enum` (rows that had to fall back to the
   `priority`/`severity` word via `resolve_score`) — surfacing when a backlog is
   score-flattening (e.g. every open task landing in one band purely because none carry a
   stored numeric score) instead of hiding it inside an aggregate count. `bugs.
   open_by_severity_score.min_severity_floor` records the active `--min-severity` floor
   (`null` when unset) — bands below an active floor legitimately read 0 because `open_bugs`
   was already floor-filtered before the histogram was built.

   `gald3r status` (non-JSON/text mode) renders BOTH histograms as the SAME 4-band ASCII
   chart shape shown above (`9-10 (crit)` / `7-8 (high)` / `5-6 (med)` / `1-4 (low|nit)`),
   reusing the identical `_task_bug_shared._render_band_chart` renderer `task list`/`bug
   list` use (g-rl-04 — one chart shape, not a second one) — automatically, whenever the
   corresponding open count is non-zero. An active `--min-severity` floor marks the band it
   falls in with a trailing `*` (a longer inline label would break the shared renderer's
   fixed-width column alignment) plus a legend line spelling the floor out.

   Prefer `gald3r status --json`/`gald3r status` for this breakdown specifically when the
   report ALSO needs `gald3r status`'s other single-call sections (task/bug counts,
   awaiting-verification groups, dependency-blocked list, active milestone, WPAC gate) — one
   command instead of several. The `gald3r bug list`/`gald3r task list` calls documented below
   remain the retrieval path when this skill needs their PER-ROW data too (step 5's active-bug
   rows reuse `gald3r bug list`'s captured rows, which `gald3r status` does not return) — both
   commands' band charts are equivalent in shape and score source, so either is safe to paste
   verbatim per the NON-SUBSTITUTABLE rule above.

   **Single-snapshot discipline (BUG-516).** The `gald3r bug list` invocation above is the
   ONE and ONLY bug-state read for this entire report. Capture its FULL stdout — both the
   band-chart block (headline `{N} bug(s) by severity...` line + bars + legend) AND the
   per-bug rows that follow it (`{bug_id}  {severity:<8} {status:<10} {title}`) — into a
   held variable/buffer, and reuse that single capture for every other bug-related number
   in the report: the headline total, the severity breakdown, and step 5's active-bug
   count/breakdown (tally the already-captured rows' `status` column; do not re-derive it
   from anywhere else). Do NOT invoke `gald3r bug list` a second time (with `--all`,
   `--json`, or any other flags) later in the same sweep, and do NOT independently re-count
   from BUGS.md for step 5 — a bug created, resolved, or reassigned between two separate
   reads produces a self-contradictory report where the headline total and an active-state
   breakdown disagree even though each read was individually correct at its own instant
   (BUG-516's exact reproduction: 95 vs. 96 from two time-separated calls in the same
   sweep). If this skill's steps are ever collapsed into one script per g-rl-37, the bug
   fetch still happens exactly once — store its parsed result and pass it to every section
   that needs a bug number, never re-invoke the CLI mid-script.

5. **Health indicators**:
   - Any tasks in `[🔄]` for > 8 hours → flag as stale
   - Any tasks in `[🔍]` for > 4 hours → flag for verification timeout
   - Phase completion: any phase where all tasks are `[✅]` but not archived
   - Active bugs: reuse the row count and per-row `status` values already captured from
     step 4b's single `gald3r bug list` snapshot (BUG-516) — do NOT re-read BUGS.md and do
     NOT re-invoke `gald3r bug list`/`gald3r bug list --all --json` here; a second,
     later-in-time read is exactly the non-atomic-snapshot defect BUG-516 fixed.

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
