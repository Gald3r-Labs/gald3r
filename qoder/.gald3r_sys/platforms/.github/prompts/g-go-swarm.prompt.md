Alias for `@g-go --swarm`: $ARGUMENTS

### ⛔ NO-PROMPT RULE — READ AND ENFORCE BEFORE DOING ANYTHING ELSE

**The coordinator MUST NEVER ask the user to confirm a plan, select a scope, choose between options, or approve a proposal.** This command is designed for fire-and-forget operation across multi-window workflows and scheduled automation. The user typed this command and moved on — they are NOT watching this session.

The **only** valid reasons to stop are documented **hard-gate failures** (PCAC conflict exit-code `2`, dirty orchestration root outside the active task's staging allowlist, manifest / `workspace_repos` resolution error on multi-repo work). Everything else — including ambiguous queue composition, mixed gald3r_dev vs member tasks, varying scope, and large `[🔍]` queues — is resolved by the **auto-plan algorithm** below without comment to the user.

**Asking "Go?" or "Conservative or expanded?" or "Which tasks?" is a violation of this rule.** Apply the auto-plan and start working.

#### Auto-Plan Algorithm (no explicit task IDs in `$ARGUMENTS`)

When `$ARGUMENTS` is empty or contains no task/bug IDs:

1. **Scope filter** — branches on the `--workspace` flag (T532):
   - **Bare `@g-go-swarm` (default)** — include only items that are **gald3r_dev-scoped**: `workspace_repos` is absent, empty, or contains only the controller repo's own manifest ID. Items naming other member repos are **deferred** (logged in session summary; no user prompt). Bare swarm MUST NEVER scan member repos automatically.
   - **`@g-go-swarm --workspace`** (alias for `@g-go --swarm --workspace`) — include items routed to manifest-declared workspace repositories whose `local_path` exists, `lifecycle_status` permits work, `allowed_write_policy.write_allowed` is true, and `workspace_touch_policy` is compatible. Items routing to missing/planned/unauthorized repos are deferred with explicit per-repo reasons. Per-repo clean checks, worktree contexts, and blocker reporting apply individually to every selected member root.
2. **Phase 1 queue** — all `[📋]` / `[ ]` / stale-`[📝]` items passing the scope filter, Critical → High → Medium → Low. Auto-downgrade to single-agent if exactly one item passes after preflight.
3. **Phase 2 queue** — all `[🔍]` items passing the scope filter, reachable from the Phase 1 checkpoint.
4. **Zero runnable items** — output `[PIPELINE] No runnable items after scope filter. Deferred: {list}. Nothing to commit.` and exit cleanly. **Do not ask.**

When `$ARGUMENTS` provides explicit IDs, use those exactly — skip scope filtering entirely. The `--workspace` flag still affects per-repo clean-check and authorization behavior even with explicit IDs.

---

Runs the full **pipeline orchestrator** in swarm mode:
- **Phase 1**: N parallel implementation agents (subsystem-boundary partition)
- **Phase 2**: M parallel reviewer agents (round-robin, fresh context each)
- **Rolling waves**: implementation continues on newly runnable downstream work while review catches up on committed checkpoints

This is exactly `@g-go --swarm`. Use this command for discoverability.
Phase 1 implementer agents use the `g-go-code --swarm` implementation-only boundary: they may run smoke/unit readiness checks, but must not launch full adversarial review. Phase 2 is the only review lane in this pipeline.
If Phase 1 has exactly one runnable item after workspace preflight, auto-downgrade Phase 1 to standard `@g-go` / `@g-go-code` single-agent implementation and continue the pipeline. Do not stop merely because swarm partitioning would produce one bucket. Workspace preflight blockers still stop the run.
Phase 1 must create or reuse one T170 coding worktree per implementation bucket before
spawning agents; Phase 2 remains governed by the review workflow.
All bucket agents run in handoff mode: they return patches/artifacts/evidence and proposed status rows. They must not write shared `.gald3r` status files, changelog/docs, generated prompts, parity output, final staging, or commits. The coordinator performs those shared writes once after deterministic reconciliation.
The coordinator then creates a code-complete checkpoint commit and passes its branch/SHA to review. Review swarms should create clean `review-swarm` worktrees from that checkpoint by default; snapshot mode is fallback-only for explicitly uncommitted or non-branch-addressable sources.
Do not stop the swarm pipeline just because an upstream item is `[🔍]`. A checkpointed `[🔍]` dependency is implementation-satisfied for downstream coding unless the downstream task declares `requires_verified_dependencies: true`. Review failures requeue the failed item and any downstream checkpoint consumers; unrelated waves keep moving.


### PCAC Inbox Gate (Only When PCAC Is Configured)

Before task claiming, implementation, verification, planning, or swarm partitioning, first determine whether this project is a PCAC participant. PCAC is configured only when `.gald3r/linking/link_topology.md` declares at least one parent/child/sibling relationship, or `.gald3r/PROJECT.md` explicitly declares PCAC project linking relationships. A Workspace-Control manifest and local `INBOX.md` alone do not make the project a PCAC group member.

If PCAC is configured, run the re-callable inbox check when the hook exists:

```powershell
$hook = @( ".cursor\hooks\g-hk-pcac-inbox-check.ps1", ".claude\hooks\g-hk-pcac-inbox-check.ps1", ".agent\hooks\g-hk-pcac-inbox-check.ps1", ".codex\hooks\g-hk-pcac-inbox-check.ps1", ".opencode\hooks\g-hk-pcac-inbox-check.ps1" ) | Where-Object { Test-Path $_ } | Select-Object -First 1
if ($hook) { powershell -NoProfile -ExecutionPolicy Bypass -File $hook -ProjectRoot . -BlockOnConflict }
```

Installed templates may call the equivalent hook from the active IDE folder. If the check reports `INBOX CONFLICT GATE` or exits with code `2`, stop immediately and run `@g-pcac-read`; do not claim tasks, create worktrees, spawn reviewers, or continue planning until conflicts are resolved. Non-conflict requests, broadcasts, and syncs are advisory and should be surfaced in the session summary. If PCAC is not configured, skip this gate and report `PCAC: not configured / skipped`.


### Gald3r Housekeeping Commit Gate (T531)

<!-- T531-HOUSEKEEPING-GATE -->
After the PCAC gate is skipped or passes and **before** the Clean Controller Gate hard-blocks the run, run the safety classifier helper at the orchestration root:

```powershell
.\scripts\gald3r_housekeeping_commit.ps1 -Mode preflight -Apply -TaskId <id-when-known> -Json
```

Behavior:

- **`clean`** -> continue.
- **`safe-gald3r-housekeeping`** -> the helper stages **only** allowlisted controller `.gald3r/` paths via explicit `git add -- <paths>` (never `git add .`), re-checks for drift, and creates a focused `chore(gald3r): preflight gald3r housekeeping` commit. The run continues automatically.
- **`unsafe-gald3r` / `mixed-dirty` / `conflict` / `drift-detected` / unknown `.gald3r` paths / member-repo `config-fault`** -> the helper exits non-zero, the existing Clean Controller Gate hard-block applies, and the run STOPs with the exact unsafe paths listed.

The helper allowlist covers the safe controller `.gald3r/` coordination surfaces (TASKS.md, BUGS.md, FEATURES.md, PRDS.md, SUBSYSTEMS.md, IDEA_BOARD.md, learned-facts.md, tasks/, bugs/, features/, prds/, subsystems/, reports/, logs/pcac_auto_actions.log, linking/sent_orders/, linking/INBOX.md). The deny list covers `.identity`, `.user_id`, `.project_id`, `.vault_location`, `vault/`, `config/`, `.gald3r-worktree.json`, secret-named files, and unknown `.gald3r/` paths. Member-repo targets (marker-only `.gald3r/`) are refused -- this gate is **controller-only**.

Re-run the helper in `-Mode post-write -Apply` immediately after coordinator-owned shared `.gald3r` writes (task/bug status writes, review-result writes, sent_orders ledger updates, safe report/log outputs) and before the next major phase so the shared-state dirty window stays short. In `--swarm` flows only the coordinator runs the helper; bucket agents remain handoff producers.
### Clean Controller Gate (before claims, worktrees, reconciliation)

After the PCAC gate is skipped or passes:

1. At the **orchestration git root** (the repo from which you run this command — normally the Workspace-Control owner, e.g. `gald3r_dev`): run `git status --short`. If anything is listed **outside** this run's explicit coordinator staging allowlist for the active task and bug IDs, **STOP** here. Do not claim tasks or bugs, create or reuse T170 worktrees, partition swarms, or write coordinator-owned updates to `.gald3r/TASKS.md`, `.gald3r/BUGS.md`, other shared `.gald3r` coordination files, `CHANGELOG.md`, generated Copilot prompts, or parity output until unrelated changes are committed, stashed, or moved to a prior focused commit. Preserve any bucket handoff artifacts already produced and list the paths that blocked progress.

2. **`gald3r_worktree.ps1 -AllowDirty`**: do not use this switch for `g-go`, `g-go-code`, `g-go-review`, or any `--swarm` variant **except** when every dirty path is owned exclusively by the active task/bug scope and a `## Status History` row documents that override. Otherwise clean the checkout first. The same **per-root** `-AllowDirty` discipline applies to every repository included in the touch set below when multi-repo work is in scope.

3. **Member touch-set (v1 — `workspace_repos`)** — The orchestration root is **always** gated. When the active task or bug declares **`workspace_repos:`** with manifest `repository.id` entries, extend the gate to each **other** resolved member root (blast radius follows declared cross-repo scope). Read `.gald3r/linking/workspace_manifest.yaml` when present; map each listed ID (deduplicated) to `repositories[?].local_path`. For each existing path, run `git -C "<path>" rev-parse --show-toplevel` then `git status --short` at that root. Apply the same **explicit coordinator staging allowlist** per root. Skip IDs whose paths are missing while `lifecycle_status` is a planned/bootstrap gap (report only; do not expand the touch set). If the manifest is missing while `workspace_repos` is non-empty, or an ID is unknown under `repositories:`, **STOP** multi-repo coordinator work until manifest or frontmatter is repaired (controller-only queue items whose `workspace_repos` lists only the owner id may proceed once that id resolves).

4. **Touch-set expansion (v2 — optional signals)** — Union extra repository roots into the same per-root checks (still **not** a blanket scan of every manifest member):
   - **`extended_touch_repos:`** — optional task/bug YAML list of additional manifest `repository.id` values beyond `workspace_repos`.
   - **`touch_repos:` (swarm handoffs)** — In `--swarm` runs, when bucket work edits roots not already covered by `workspace_repos` + `extended_touch_repos:`, bucket summaries and the coordinator reconciliation block MUST list those ids under `touch_repos:` so the union is gated before shared writes.
   - **Subsystem `locations:` absolutes** — When the active item declares **`subsystems:`**, read each `.gald3r/subsystems/{name}.md` frontmatter **`locations:`** (all nested strings). For values matching a host **absolute** path (`^[A-Za-z]:[/\\]` on Windows, or POSIX `/` rooted at `/` elsewhere), if the path exists, resolve `git -C <dir> rev-parse --show-toplevel` (use the file's parent directory when the path is a file). Each distinct root **other than** the orchestration root joins the touch set. Relative paths do not expand the set.

### Pre-Reconciliation Clean Gate (before coordinator shared writes)

Also re-run the **Gald3r Housekeeping Commit Gate** with `-Mode post-write -Apply` against the orchestration root immediately after each coordinator-owned shared `.gald3r` write so safe controller coordination state lands in a focused `chore(gald3r): commit g-go coordination state` commit before the next major phase begins.


Immediately before the coordinator merges bucket results into the primary checkout, updates shared `.gald3r` indexes or task/bug files as coordinator-owned writes, touches `CHANGELOG.md`, or creates checkpoint / review-result commits: **re-run** `git status --short` on the **orchestration root and every other repository root in the computed touch set** (steps 1 + 3 + 4). For `--swarm` runs, if unrelated dirty paths appear in **any** of those roots during parallel bucket work, **fail closed** — do not apply those shared writes; keep patches, artifacts, and evidence; report **per-root** blockers using the same blocker family as checkpoint and review-result commits.

### PCAC Inbox Heartbeats (Swarm / Long Runs)

For swarm mode or any run lasting more than 30 minutes, the coordinator reruns the PCAC inbox check every 30 minutes and once more before the final summary. If a conflict appears mid-run, pause new claims/spawns/reconciliation, preserve worktrees and partial outputs, and require `@g-pcac-read` before continuing.

## Usage

```
@g-go-swarm
@g-go-swarm tasks 7, 9, 10, 11, 12
@g-go-swarm bugs-only
@g-go-swarm --workspace
@g-go-swarm --workspace tasks 220, 221, 222
```

All filter arguments pass through to `@g-go --swarm`. The `--workspace` flag composes with task/bug filters and bugs-only.

See `@g-go` for full pipeline documentation, worktree isolation, and swarm agent count / partition rules.

Let's go.