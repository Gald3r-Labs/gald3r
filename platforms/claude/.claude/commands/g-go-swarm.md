---
subsystem_memberships: [TASK_MANAGEMENT]
---
Alias for `@g-go --swarm`: $ARGUMENTS

> **Step 0 — Workspace Member Clean-Status Preflight (T1431):** inherited from `@g-go`. The
> read-only member clean-status preflight (manifest scan + `git status --short` per
> `autonomous_child` member, dirty-table prompt, `--skip-member-clean-check` bypass) runs before
> task selection. See `g-go.md` Step 0 for the authoritative algorithm.

### ⛔ NO-PROMPT RULE — READ AND ENFORCE BEFORE DOING ANYTHING ELSE

**The coordinator MUST NEVER ask the user to confirm a plan, select a scope, choose between options, or approve a proposal.** This command is designed for fire-and-forget operation across multi-window workflows and scheduled automation. The user typed this command and moved on — they are NOT watching this session.

The **only** valid reasons to stop are documented **hard-gate failures** (WPAC conflict exit-code `2`, dirty orchestration root outside the active task's staging allowlist, manifest / `workspace_repos` resolution error on multi-repo work). Everything else — including ambiguous queue composition, mixed <gald3r_source> vs member tasks, varying scope, and large `[🔍]` queues — is resolved by the **auto-plan algorithm** below without comment to the user.

**Asking "Go?" or "Conservative or expanded?" or "Which tasks?" is a violation of this rule.** Apply the auto-plan and start working.

#### Auto-Plan Algorithm (no explicit task IDs in `$ARGUMENTS`)

When `$ARGUMENTS` is empty or contains no task/bug IDs:

1. **Scope filter** — determined by flags AND `.gald3r/config/AGENT_CONFIG.md` `g_go_default_scope` (same logic as `g-go`):

   | Priority | Condition | Effective scope |
   |---|---|---|
   | 1 | `--local` flag | local-only (current repo tasks only) |
   | 2 | `--workspace <id>` or `--workspace <id1,id2>` | narrow to named member(s) |
   | 3 | `--workspace` (no value) | all manifest members |
   | 4 | *(no flag)* + `g_go_default_scope: workspace_all` | all members (controller default) |
   | 5 | *(no flag)* + `g_go_default_scope: local_only` or absent | local-only (member default) |

   - **local-only** — `workspace_repos` is absent, empty, or contains only the current repo's manifest ID. Items naming other member repos are **deferred** (logged; no prompt).
   - **workspace scope** — include items routed to manifest-declared repositories in the resolved member set whose `local_path` exists, `lifecycle_status` permits work, `write_allowed` is true, and `workspace_touch_policy` is compatible. Items routing to missing/unauthorized repos are deferred with explicit per-repo reasons. Per-repo clean checks, worktree contexts, and blocker reporting apply individually.
2. **Phase 1 queue** — all `[📋]` / `[ ]` / stale-`[📝]` items passing the scope filter, Critical → High → Medium → Low. Auto-downgrade to single-agent if exactly one item passes after preflight.
3. **Phase 2 queue** — all `[🔍]` items passing the scope filter, reachable from the Phase 1 checkpoint.
4. **Zero runnable items** — output `[PIPELINE] No runnable items after scope filter. Deferred: {list}. Nothing to commit.` and exit cleanly. **Do not ask.**

When `$ARGUMENTS` provides explicit IDs, use those exactly — skip scope filtering entirely. The `--workspace` flag still affects per-repo clean-check and authorization behavior even with explicit IDs.

---

Runs the full **pipeline orchestrator** in swarm mode:
- **Phase 1**: N parallel implementation agents via `g-go-code-swarm` (subsystem-boundary partition)
- **Phase 2**: M parallel reviewer agents via `g-go-review-swarm` (round-robin, fresh context each)
- **Rolling waves**: implementation continues on newly runnable downstream work while review catches up on committed checkpoints

This is exactly `@g-go --swarm`. Use this command for discoverability.
⚡ **Phase 1 invocation**: The coordinator MUST invoke `g-go-code-swarm` (or `g-go-code --swarm`) as the Phase 1 driver — N coders run in parallel, fan-in to a checkpoint, THEN Phase 2 begins. Invoking bare `g-go` per task is sequential coding and defeats the swarm architecture.
Phase 1 implementer agents use the `g-go-code --swarm` implementation-only boundary: they may run smoke/unit readiness checks, but must not launch full adversarial review. Phase 2 is the only review lane in this pipeline.
If Phase 1 has exactly one runnable item after workspace preflight, auto-downgrade Phase 1 to standard `@g-go` / `@g-go-code` single-agent implementation and continue the pipeline. Do not stop merely because swarm partitioning would produce one bucket. Workspace preflight blockers still stop the run.
Phase 1 must create or reuse one T170 coding worktree per implementation bucket before
spawning agents; Phase 2 remains governed by the review workflow.
All bucket agents run in handoff mode: they return patches/artifacts/evidence and proposed status rows. They must not write shared `.gald3r` status files, changelog/docs, generated prompts, parity output, final staging, or commits. The coordinator performs those shared writes once after deterministic reconciliation.
The coordinator then creates a code-complete checkpoint commit and passes its branch/SHA to review. Review swarms should create clean `review-swarm` worktrees from that checkpoint by default; snapshot mode is fallback-only for explicitly uncommitted or non-branch-addressable sources.
Do not stop the swarm pipeline just because an upstream item is `[🔍]`. A checkpointed `[🔍]` dependency is implementation-satisfied for downstream coding unless the downstream task declares `requires_verified_dependencies: true`. Review failures requeue the failed item and any downstream checkpoint consumers; unrelated waves keep moving.


### WPAC inbox Gate (Only When WPAC is configured)

Before task claiming, implementation, verification, planning, or swarm partitioning, first determine whether this project is a WPAC participant. WPAC is configured only when `.gald3r/workspace/topology.md` declares at least one parent/child/sibling relationship, or `.gald3r/PROJECT.md` explicitly declares WPAC project linking relationships. A Workspace-Control manifest and local `INBOX.md` alone do not make the project a WPAC group member.

If WPAC is configured, run the re-callable inbox check when the hook exists:

```powershell
$hook = @( ".cursor\hooks\g-hk-wpac-inbox-check.ps1", ".claude\hooks\g-hk-wpac-inbox-check.ps1", ".agent\hooks\g-hk-wpac-inbox-check.ps1", ".codex\hooks\g-hk-wpac-inbox-check.ps1", ".opencode\hooks\g-hk-wpac-inbox-check.ps1" ) | Where-Object { Test-Path $_ } | Select-Object -First 1
if ($hook) { powershell -NoProfile -ExecutionPolicy Bypass -File $hook -ProjectRoot . -BlockOnConflict }
```

Installed templates may call the equivalent hook from the active IDE folder. If the check reports `INBOX CONFLICT GATE` or exits with code `2`, stop immediately and run `@g-wpac-read`; do not claim tasks, create worktrees, spawn reviewers, or continue planning until conflicts are resolved. Non-conflict requests, broadcasts, and syncs are advisory and should be surfaced in the session summary. If WPAC is not configured, skip this gate and report `WPAC: not configured / skipped`.


### Gald3r Housekeeping Commit Gate (T531)

<!-- T531-HOUSEKEEPING-GATE -->
After the WPAC gate is skipped or passes and **before** the Clean Controller Gate hard-blocks the run, run the safety classifier helper at the orchestration root:

```powershell
.\scripts\gald3r_housekeeping_commit.ps1 -Mode preflight -Apply -TaskId <id-when-known> -Json
```

Behavior:

- **`clean`** -> continue.
- **`safe-gald3r-housekeeping`** -> the helper stages **only** allowlisted controller `.gald3r/` paths via explicit `git add -- <paths>` (never `git add .`), re-checks for drift, and creates a focused `chore(gald3r): preflight gald3r housekeeping` commit. The run continues automatically.
- **`unsafe-gald3r` / `mixed-dirty` / `conflict` / `drift-detected` / unknown `.gald3r` paths / member-repo `config-fault`** -> the helper exits non-zero, the existing Clean Controller Gate hard-block applies, and the run STOPs with the exact unsafe paths listed.

The helper allowlist covers the safe controller `.gald3r/` coordination surfaces (TASKS.md, BUGS.md, FEATURES.md, PRDS.md, SUBSYSTEMS.md, IDEA_BOARD.md, learned-facts.md, tasks/, bugs/, features/, prds/, subsystems/, reports/, logs/wpac_auto_actions.log, workspace/sent_orders/, workspace/inbox.md). The deny list covers `.identity`, `.user_id`, `.project_id`, `.vault_location`, `vault/`, `config/`, `.gald3r-worktree.json`, secret-named files, and unknown `.gald3r/` paths. Member-repo targets (marker-only `.gald3r/`) are refused -- this gate is **controller-only**.

Re-run the helper in `-Mode post-write -Apply` immediately after coordinator-owned shared `.gald3r` writes (task/bug status writes, review-result writes, sent_orders ledger updates, safe report/log outputs) and before the next major phase so the shared-state dirty window stays short. In `--swarm` flows only the coordinator runs the helper; bucket agents remain handoff producers.
### Clean Controller Gate (before claims, worktrees, reconciliation)

After the WPAC gate is skipped or passes:

1. At the **orchestration git root** (the repo from which you run this command — normally the Workspace-Control owner, e.g. `<gald3r_source>`): run `git status --short`. If anything is listed **outside** this run's explicit coordinator staging allowlist for the active task and bug IDs, **STOP** here. Do not claim tasks or bugs, create or reuse T170 worktrees, partition swarms, or write coordinator-owned updates to `.gald3r/TASKS.md`, `.gald3r/BUGS.md`, other shared `.gald3r` coordination files, `CHANGELOG.md`, generated Copilot prompts, or parity output until unrelated changes are committed, stashed, or moved to a prior focused commit. Preserve any bucket handoff artifacts already produced and list the paths that blocked progress.

2. **`gald3r_worktree.ps1 -AllowDirty`**: do not use this switch for `g-go`, `g-go-code`, `g-go-review`, or any `--swarm` variant **except** when every dirty path is owned exclusively by the active task/bug scope and a `## Status History` row documents that override. Otherwise clean the checkout first. The same **per-root** `-AllowDirty` discipline applies to every repository included in the touch set below when multi-repo work is in scope.

3. **Member touch-set (v1 — `workspace_repos`)** — The orchestration root is **always** gated. When the active task or bug declares **`workspace_repos:`** with manifest `repository.id` entries, extend the gate to each **other** resolved member root (blast radius follows declared cross-repo scope). Read `.gald3r/workspace/workspace_manifest.yaml` when present; map each listed ID (deduplicated) to `repositories[?].local_path`. For each existing path, run `git -C "<path>" rev-parse --show-toplevel` then `git status --short` at that root. Apply the same **explicit coordinator staging allowlist** per root. Skip IDs whose paths are missing while `lifecycle_status` is a planned/bootstrap gap (report only; do not expand the touch set). If the manifest is missing while `workspace_repos` is non-empty, or an ID is unknown under `repositories:`, **STOP** multi-repo coordinator work until manifest or frontmatter is repaired (controller-only queue items whose `workspace_repos` lists only the owner id may proceed once that id resolves).

4. **Touch-set expansion (v2 — optional signals)** — Union extra repository roots into the same per-root checks (still **not** a blanket scan of every manifest member):
   - **`extended_touch_repos:`** — optional task/bug YAML list of additional manifest `repository.id` values beyond `workspace_repos`.
   - **`touch_repos:` (swarm handoffs)** — In `--swarm` runs, when bucket work edits roots not already covered by `workspace_repos` + `extended_touch_repos:`, bucket summaries and the coordinator reconciliation block MUST list those ids under `touch_repos:` so the union is gated before shared writes.
   - **Subsystem `locations:` absolutes** — When the active item declares **`subsystems:`**, read each `.gald3r/subsystems/{name}.md` frontmatter **`locations:`** (all nested strings). For values matching a host **absolute** path (`^[A-Za-z]:[/\\]` on Windows, or POSIX `/` rooted at `/` elsewhere), if the path exists, resolve `git -C <dir> rev-parse --show-toplevel` (use the file's parent directory when the path is a file). Each distinct root **other than** the orchestration root joins the touch set. Relative paths do not expand the set.

### Pre-Reconciliation Clean Gate (before coordinator shared writes)

Also re-run the **Gald3r Housekeeping Commit Gate** with `-Mode post-write -Apply` against the orchestration root immediately after each coordinator-owned shared `.gald3r` write so safe controller coordination state lands in a focused `chore(gald3r): commit g-go coordination state` commit before the next major phase begins.


Immediately before the coordinator merges bucket results into the primary checkout, updates shared `.gald3r` indexes or task/bug files as coordinator-owned writes, touches `CHANGELOG.md`, or creates checkpoint / review-result commits: **re-run** `git status --short` on the **orchestration root and every other repository root in the computed touch set** (steps 1 + 3 + 4). For `--swarm` runs, if unrelated dirty paths appear in **any** of those roots during parallel bucket work, **fail closed** — do not apply those shared writes; keep patches, artifacts, and evidence; report **per-root** blockers using the same blocker family as checkpoint and review-result commits.

### WPAC inbox Heartbeats (Swarm / Long Runs)

For swarm mode or any run lasting more than 30 minutes, the coordinator reruns the WPAC inbox check every 30 minutes and once more before the final summary. If a conflict appears mid-run, pause new claims/spawns/reconciliation, preserve worktrees and partial outputs, and require `@g-wpac-read` before continuing.

## Usage

```
@g-go-swarm
@g-go-swarm tasks 7, 9, 10, 11, 12
@g-go-swarm bugs-only
@g-go-swarm --workspace
@g-go-swarm --workspace tasks 220, 221, 222
```

All filter arguments pass through to `@g-go --swarm`. The `--workspace` flag composes with task/bug filters and bugs-only.

## Spawned-agent task/bug creation (T585 AC3)

During this run, **any** task or bug a spawned agent needs to create (deferred sub-feature,
newly discovered bug, follow-up) goes into the **hot inbox**, never a direct `tasks/open/` /
`bugs/open/` write + index regeneration:

- **Preferred** — call the engine verb (`gald3r task create …` / `gald3r bug report …`, or the
  `gald3r_task_*` / `gald3r_bug_*` MCP tools). When the run marker
  (`.gald3r/logs/ggo_run_state.json` `active: true`, or `GALD3R_AGENT_RUN=1`) is set, the engine
  **auto-routes** the new item to `tasks/inbox/` / `bugs/inbox/` as an id-less, uuid-suffixed
  draft — no id is assigned at create time.
- **Manual fallback** (no engine) — hand-write the draft directly into `tasks/inbox/` /
  `bugs/inbox/` (id-less, uuid-suffixed filename). Do **not** write `tasks/open/` / `bugs/open/`
  or touch `TASKS.md` / `BUGS.md`.

The hot-inbox **intake** (run at each iteration boundary — see the inbox-intake step) is the
*single ID-assigning authority*: it assigns ids atomically, so N concurrent agents can never
collide on the next id. This is the spawn-side complement of that intake step.

## Multi-Agent Communication Frameworks (T1094)

gald3r implements all five frontier multi-agent communication frameworks (Factory's taxonomy)
across its primitives. Use this table to name what's happening and pick the right primitive.

| Framework | What it is | gald3r primitive(s) |
|-----------|-----------|---------------------|
| **Delegation** | Parent spawns child work, gets a result | `@g-go-code` spawning swarm buckets; `@g-WPAC-order` (parent→child task) |
| **Creator–verifier** | One agent builds, a **fresh** agent verifies (no implementation-cost bias) | `@g-go` Phase 1 (`g-go-code`) → Phase 2 (`g-go-review`); `g-agnt-verifier` may not verify its own work |
| **Direct communication** | Agents/projects message point-to-point | `@g-WPAC-ask` (child→parent), `@g-WPAC-send-to` / `@g-WPAC-move` |
| **Negotiation** | Agents coordinate over shared resources, net-positive | `@g-WPAC-sync` (sibling contract sync); the swarm coordinator's resource reconciliation over shared `.gald3r/` ledgers |
| **Broadcast** | One-to-many: status, new context, constraints | `@g-WPAC-order` (broadcast), `@g-WPAC-notify`, INBOX `[BROADCAST]`, session-start surfacing |

`g-go --swarm` itself combines **delegation** (buckets) + **creator–verifier** (Phase 2 review) +
**negotiation** (coordinator-owned reconciliation, T206). Each `@g-WPAC-*` SKILL.md carries a
one-line `Multi-agent framework (T1094):` tag identifying its type.

**Serial vs. parallel (important).** Like Factory's "Missions," gald3r runs *features* serially
within a mission/pipeline even though *buckets* within a phase run in parallel — long-running,
state-dependent work is sequenced (claims, gates, reconciliation), and only independent,
side-effect-isolated work fans out to parallel worktrees. Don't parallelize tasks that mutate the
same shared `.gald3r/` state or depend on each other's output; partition on independence.

See `@g-go` for full pipeline documentation, worktree isolation, and swarm agent count / partition rules.

---

## ADR-001 — Shared-context vs. independent-context bucket model (T976)

**Status:** Accepted (2026-05-21) · **Default:** independent-context (current behavior, unchanged)

### Context

`g-go-swarm` runs Phase 1 implementation buckets with **independent context** — each bucket
agent sees only its own slice spec, not the live output of sibling buckets. This maximizes
parallelism and isolation but can produce **incoherence** when bucket outputs must read as one
voice or share conventions (naming, prose tone, helper-extraction choices).

An alternative is the **shared-context** pattern: the orchestrator holds the full prompt, breaks
it into N subtasks, and each specialist agent sees the **full prompt + all prior specialist
outputs** before generating its own. Coherence rises; parallelism falls (buckets serialize on
each other's output) and token cost rises (every bucket re-reads the growing shared context).

### Decision

Keep **independent-context as the default**. Treat shared-context as an **opt-in mode** chosen by
the coordinator per run, not a global switch. The two models are selected by task *character*,
not preference.

### When to prefer SHARED context

- **Documentation generation** spanning multiple files/sections that must read as one voice
  (e.g. a multi-page guide, a README + reference set, llms.txt + llms-full.txt).
- **Consistency-critical refactors** where every bucket must apply the *same* naming, API shape,
  or helper-extraction decision (e.g. a cross-file rename, a shared-utility extraction pass).
- **Small bucket counts** (≈2–4) where the serialization cost is acceptable.
- Output where a human would notice "different hands wrote these" as a defect.

### When to prefer INDEPENDENT context (default)

- **Independent implementation buckets** partitioned on true subsystem boundaries with no shared
  surface (the normal `g-go-swarm` case).
- **Security-isolated work** where a bucket must NOT see another bucket's secrets, paths, or
  scratch reasoning (least-context is a safety property here).
- **Large bucket counts** where serialization would erase the parallelism that justifies a swarm.
- Latency- or token-budget-sensitive runs.

### Evaluation criteria for a future switch / per-run heuristic

The coordinator MAY auto-select shared-context for a Phase 1 wave when **all** hold:

1. **Coherence-sensitive type** — the wave is dominated by `type: documentation` or a refactor
   tagged consistency-critical (e.g. `tags: [cross-file-rename, shared-extraction]`).
2. **Small fan-out** — runnable bucket count ≤ 4 after partitioning.
3. **Shared surface present** — buckets touch overlapping files or a shared public API (high
   incoherence risk if isolated).
4. **No security-isolation requirement** — no bucket carries `context_isolation: required`.

A future coherence metric (e.g. reviewer-flagged style/naming inconsistencies per 1k LOC above a
threshold) can promote a task class from independent → shared. Until that metric exists, the mode
is a coordinator judgment call documented in the run summary. Independent-context remains the safe
default whenever the criteria are not unambiguously met.

> Compatibility: this ADR is descriptive — terminal-first, markdown-defined bucket instructions
> support both models, and no current `g-go-swarm` behavior changes by adopting this record.

Let's go.