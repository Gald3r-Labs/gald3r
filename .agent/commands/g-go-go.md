Maximal workspace swarm autopilot — rolling implement/review until a hard stop: $ARGUMENTS

## Mode: AUTOPILOT (rolling implement → review → next batch)

`g-go-go` is the **explicit** "full throttle" command. It composes existing safe primitives (`g-go --swarm --workspace`, T531 housekeeping gate, T532 workspace mode, T212 rolling swarm pipeline, T206/207/208 swarm reconciliation policies, T170-172 worktree isolation, T495/496 per-root clean gates, marker-only `.gald3r/` invariant, PCAC conflict gates) into one continuous loop. It is **not** an alias for bare `/g-go`. Bare `/g-go` remains controller-only and unchanged.

> **Independence guarantee**: Each implementation/review cycle uses fresh reviewer subagents with no Phase 1 context. The autopilot loop never lets implementer agents self-verify their own work.

> **Bounded by design**: Autopilot is powerful but bounded. It cannot bypass PCAC conflict gates, clean gates, marker-only member `.gald3r/` protection, task workspace permissions, verification independence, secrets checks, explicit path staging, or non-destructive member rules. Every documented hard stop in the table below cleanly halts the run with an actionable summary.

---

### ⛔ NO-PROMPT RULE — READ AND ENFORCE BEFORE DOING ANYTHING ELSE

**The autopilot coordinator MUST NEVER ask the user to confirm a plan, select a scope, choose between options, or approve a proposal mid-run.** This command is fire-and-forget by design — the user typed it expecting unattended progress. The only valid reasons to halt are the documented **hard stops** below; everything else is resolved silently by the auto-plan rules and the loop continues.

Asking "Continue?" "Which next?" "Looks like X — proceed?" mid-run is a **violation of this rule**. Apply the auto-plan, run the next iteration, and if the run cannot continue safely, emit the final summary and exit.

---

## Default Configuration

| Knob | Default | Override |
|------|---------|----------|
| Mode | `--swarm --workspace` (T532 expands to manifest-declared repos) | `g-go-go --controller-only` to skip workspace expansion |
| Heartbeat interval | 30 minutes wall-clock | `g-go-go --heartbeat 15m` |
| Run budget (max iterations) | 12 implementation/review cycles | `g-go-go --budget 5` or `--budget 25` |
| Max parallel implementers | 5 (per swarm hard cap) | inherited from `g-go --swarm` |
| Review independence | one fresh reviewer agent per implementation checkpoint | non-overrideable |
| Backend dependency | file-first; `gald3r_valhalla` optional | tasks declaring backend dependency in their YAML are deferred when backend down |
| Verification retry ceiling | 3 FAIL cycles → `[🚨]` (T047) | non-overrideable |

`g-go-go` accepts the same `$ARGUMENTS` filters as `g-go` (`tasks N,M`, `bugs BUG-NNN`, `subsystem ...`, `bugs-only`, `tasks-only`) plus the autopilot knobs above.

---

## PCAC Inbox Gate (Before Claiming Work)

Before each loop iteration claims work, run the re-callable PCAC inbox check:

```powershell
$hook = @( ".cursor\hooks\g-hk-pcac-inbox-check.ps1", ".claude\hooks\g-hk-pcac-inbox-check.ps1", ".agent\hooks\g-hk-pcac-inbox-check.ps1", ".codex\hooks\g-hk-pcac-inbox-check.ps1", ".opencode\hooks\g-hk-pcac-inbox-check.ps1" ) | Where-Object { Test-Path $_ } | Select-Object -First 1
if ($hook) { powershell -NoProfile -ExecutionPolicy Bypass -File $hook -ProjectRoot . -BlockOnConflict }
```

> **Tool routing (BUG-031)**: invoke this snippet through the **PowerShell tool**, not Bash. PowerShell-only syntax (`@(...)` array, `Where-Object`, `Test-Path`) routed to Bash produces a parse error such as ``syntax error near unexpected token `('``  — that failure is a tool-selection error, **NOT** a real PCAC conflict gate.

If the check reports `INBOX CONFLICT GATE` or exits with code `2`, **HARD STOP**: emit the final summary and exit. Do not claim more work, spawn more agents, or commit.

The autopilot also re-runs the PCAC inbox check at every heartbeat interval and once before each rolling-wave bucket spawn.

---

## Gald3r Housekeeping Commit Gate (T531)

Before each iteration claims/spawns/commits, run the safety classifier helper at the orchestration root:

```powershell
.\scripts\gald3r_housekeeping_commit.ps1 -Mode preflight -Apply -Json
```

Behavior matches `g-go`:

- **`clean`** — continue.
- **`safe-gald3r-housekeeping`** — helper auto-commits classified-safe `.gald3r/` paths into a focused `chore(gald3r): preflight gald3r housekeeping` commit; loop continues.
- **`unsafe-gald3r` / `mixed-dirty` / `conflict` / `drift-detected` / unknown / member `config-fault`** — **HARD STOP** with the exact unsafe paths listed.

After every coordinator-owned shared write, re-run with `-Mode post-write -Apply` to land safe coordination state in a `chore(gald3r): commit g-go coordination state` commit before the next phase.

---

## Clean Controller Gate + Touch-Set v1/v2

Same per-root contract as `g-go --workspace`:

- Orchestration root is **always** in the touch set.
- v1 — every manifest member listed in any selected task's `workspace_repos:` joins the touch set.
- v2 — optional `extended_touch_repos:`, swarm `touch_repos:` handoffs, and absolute paths from subsystem `locations:` may union additional roots.
- Each root gets its own `git status --short`. Unrelated dirty paths in any per-repo touch set block coordinator-owned writes to that repo only — they do **not** block unrelated clean repos.
- The marker-only `.gald3r/` invariant for `controlled_member` and `migration_source` repositories remains absolute. `g-go-go` does NOT relax it.

If a per-root gate fails, the autopilot defers ALL work routed to that repo and **continues** with work routed to clean repos only — until no runnable work remains, at which point it stops with a final summary.

### Member-scoped task authorization

A selected task may run against a member repository only when ALL of the following are true (same six-condition contract as `g-go --workspace`):

1. The member's manifest `repository.id` appears in the task's `workspace_repos:` list.
2. The task's `workspace_touch_policy` is in the manifest entry's `allowed_write_policy.allowed_touch_policies`.
3. The manifest entry's `allowed_write_policy.write_allowed` is `true`.
4. Every dependency, blocker, PCAC inbox, and `[🚨]` check passes for that member root.
5. Per-repo clean check passes (or `-AllowDirty` is documented per-root in the task's `## Status History`).
6. No member `.gald3r/` control-plane path is targeted (marker-only invariant).

If any check fails for a member, the autopilot defers that task with a per-repo reason and continues. Autopilot **never** silently degrades authorization to keep the loop running.

---

## The Autopilot Loop

```
INIT
  ├─ PCAC inbox gate (HARD STOP on conflict)
  ├─ Housekeeping preflight at orchestration root
  ├─ Clean Controller Gate per-root
  ├─ Initialize: iter=0, budget_remaining=12 (or user override)
  └─ Snapshot: tasks, bugs, manifest at start

LOOP (iter < budget_remaining)
  ├─ Re-evaluate runnable queue (T532 workspace selection unless --controller-only)
  ├─ If queue is empty → STOP (all-clear)
  ├─ Phase 1 (g-go-code --swarm --workspace protocol):
  │   ├─ Skip non-expired [📝] / [🔄] / [🕵️] claims
  │   ├─ Partition into N buckets (N = smart agent count from g-go)
  │   ├─ Pre-create one coding worktree per bucket
  │   ├─ Spawn N implementer subagents (handoff mode — return patches/artifacts/evidence/proposed-status only)
  │   ├─ Wait for all bucket handoffs
  │   ├─ Pre-Reconciliation Clean Gate per-root (HARD STOP on dirty drift)
  │   ├─ Coordinator reconciles bucket patches into primary checkout one at a time
  │   ├─ Coordinator owns shared writes: TASKS.md, BUGS.md, task/bug status files,
  │   │   CHANGELOG.md, generated Copilot prompts, parity output, per-repo final staging
  │   ├─ Coordinator creates per-repo code-complete checkpoint commits
  │   └─ phase1_results = list of [🔍] items per bucket
  ├─ Phase 2 (g-go-review --swarm protocol):
  │   ├─ Spawn M fresh reviewer subagents (no Phase 1 context)
  │   ├─ Each reviewer runs from a review-swarm worktree based on the Phase 1 checkpoint
  │   ├─ Reviewers return PASS/FAIL payloads + Status History rows + evidence (no writes)
  │   ├─ Coordinator batch-writes TASKS.md/BUGS.md verdicts (PASS → [✅], FAIL → [📋])
  │   ├─ Coordinator creates per-repo review-result commits (PASS, FAIL, mixed)
  │   └─ Detect ≥3 FAIL cycles per item → [🚨] Requires-User-Attention (T047)
  ├─ Heartbeat check: if elapsed >= heartbeat_interval, emit heartbeat summary
  ├─ Increment iter; recompute budget_remaining
  └─ Loop again

EXIT
  └─ Emit final summary
```

The loop never blocks on `[🔍]` dependencies of newly runnable downstream work unless the dependent task declares `requires_verified_dependencies: true`. Review failures that invalidate downstream checkpoints requeue the affected items.

---

## Hard Stops (autopilot HALTS, emits final summary, exits)

| Stop reason | Trigger | Action |
|-------------|---------|--------|
| **PCAC conflict** | inbox check exit code `2` | halt before next claim |
| **Unsafe dirty orchestration root** | housekeeping gate returns `unsafe-gald3r` / `mixed-dirty` / `conflict` / `drift-detected` | halt; do not stage |
| **Unsafe dirty member root** for ALL routed work | every selected member root has unrelated dirty paths | halt with per-root listing |
| **Marker-only violation** | guard helper rejects member `.gald3r/` write | halt; log file + reason |
| **Secret detection** | secret-pattern scanner fires on staged content | halt; do not commit |
| **Missing required dependency** | task has `requires_verified_dependencies: true` and any dep is non-`[✅]` | skip task; if all queue is so blocked → halt |
| **`[🚨]` user-attention item** | task or bug has user-attention status | skip item; never auto-retry |
| **Verification retry ceiling** | task has ≥3 FAIL cycles in Status History | mark `[🚨]`; halt if all queue is `[🚨]` |
| **Run budget exhausted** | `iter >= budget_remaining` | clean halt |
| **No runnable work** | recomputed queue is empty after a successful iteration | clean halt |
| **Manifest unparseable** | `workspace_manifest.yaml` missing/broken on a multi-repo run | halt; report manifest error |
| **Workspace-Control preflight denial** | unknown manifest repo IDs / not a git root / unauthorized routing | halt with the specific blocker |

Hard stops are not failures — they are the **purpose** of the safety contract. The final summary documents the stop reason and the next safe command.

---

## Heartbeat Summary (every `heartbeat_interval`)

```
[AUTOPILOT] Heartbeat — iter {N} / budget {B} — elapsed {HH:MM}
[AUTOPILOT] Mode: {workspace|controller-only}, swarm: {N implementers / M reviewers}
[AUTOPILOT] Active repos: {ids touched this run}
[AUTOPILOT] Completed → [✅]: {count}    Awaiting review → [🔍]: {count}    Failed → [📋]: {count}    [🚨]: {count}
[AUTOPILOT] Currently implementing: {task IDs in flight}
[AUTOPILOT] Currently reviewing:    {task IDs in review}
[AUTOPILOT] Per-repo blockers: {repo_id → reason, ...}
[AUTOPILOT] Next iteration starts in: {seconds}
```

Heartbeats are append-only to the session output; they do NOT trigger user prompts.

---

## File-First Fallback

`g-go-go` MUST work without `gald3r_valhalla` services. Optional backend failures are surfaced and degraded:

- Vault MCP unavailable → file-first vault reads only; tasks that explicitly declare `requires_backend: true` in their YAML are deferred with `Deferred — gald3r_valhalla unavailable` in the summary.
- Memory MCP unavailable → no memory capture/recall; loop continues using local task/bug specs only.
- Oracle MCP unavailable → tasks routed through Oracle subsystems are deferred.
- Platform-docs search unavailable → loop falls back to local docs reads.

Never crash on optional backend failure; deferring affected work and continuing is the safe default.

---

## Final Summary

```markdown
## g-go-go Autopilot Session Summary

### Run config
- Mode: {workspace|controller-only} {+swarm}
- Budget: {used}/{max} iterations
- Elapsed: {HH:MM}
- Stop reason: {hard stop name OR "no runnable work" OR "budget exhausted"}

### Per-iteration log
| Iter | Implementers | Reviewers | [✅] | [📋] | Checkpoint commit | Review commit |
|------|--------------|-----------|-----|-----|-------------------|---------------|
| 1    | 3            | 2         | 4   | 1   | abc123            | def456        |
| 2    | 2            | 1         | 2   | 0   | 789abc            | 012def        |

### Repos touched
- gald3r_dev: {commits} commits, last {sha}
- gald3r_template_full: SKIPPED (unrelated dirty: .github/...)
- gald3r_throne: {commits} commits, last {sha}

### Failed / blocked items
- Task {id}: FAIL — {reason}; ≥3 cycles → marked [🚨]
- Bug BUG-{id}: blocked — {reason}

### Final state
- ✅ Completed (verified): {N}
- 📋 Failed (back to pending): {M}
- 🚨 Requires user attention: {U}
- ⏸️  Skipped (blocked): {K}
- Total commits this run: {C}

### Next safe command
@g-go-go --budget 5    # if you want another short run
@g-go tasks {failed_ids}    # to retry specific failures
@g-pcac-read    # if a PCAC conflict halted the run
```

---

## Behavioral Rules

| Rule | Why |
|------|-----|
| Bare `/g-go` is unchanged — `/g-go-go` is a separate explicit command | Autopilot must be opt-in, never silent |
| Autopilot composes existing safe primitives — never bypasses any gate | One command, same safety contract |
| Implementation agents NEVER self-verify their own work | Adversarial independence preserved across all loop iterations |
| Hard stops emit final summaries and exit cleanly | Stops are not failures; they are the safety boundary |
| Run budget bounds the loop | Prevents runaway autonomous runs |
| Heartbeats are output-only — never prompt the user | Fire-and-forget design |
| File-first fallback when optional backends are down | `gald3r_valhalla` is optional, not required |
| Per-repo commits only — no cross-repo single commits | Each manifest member is an independent git root |
| Marker-only `.gald3r/` invariant is absolute | Member control-plane writes are forbidden, period |
| `[🚨]` items are NEVER auto-retried | Human-only resolution by policy (T047) |

---

## Usage Examples

```
@g-go-go
@g-go-go --budget 5
@g-go-go --heartbeat 15m
@g-go-go --controller-only
@g-go-go --controller-only --budget 3
@g-go-go tasks 220, 222, 223
@g-go-go bugs-only
@g-go-go subsystem multiple-ide-platform-parity
```

The defaults (workspace mode, 12-iteration budget, 30-minute heartbeat) are tuned for a multi-hour overnight or background run. Use `--budget 3` and `--heartbeat 5m` for quick autopilot bursts.

**For supervised pipeline runs (one batch only), use `@g-go --swarm --workspace` instead — that is one iteration of this loop.**

Let's go.
