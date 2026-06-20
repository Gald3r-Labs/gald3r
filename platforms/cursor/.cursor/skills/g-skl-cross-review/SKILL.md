---
subsystem_memberships: [AGENT_ORCHESTRATION]
skill_trust_level: core
---
# g-skl-cross-review — Cross-vendor review enforcement (A7 / T495)

Runs code review with a reviewer on a **different LLM vendor** than the implementer (different
blind spots), given **only the diff + the acceptance contract as text** (no worktree, no
implementer transcript), **after deterministic gates** pass; blocking findings re-dispatch the
**same implementer**; the orchestrator **never merges**.

This skill is a **front door over existing machinery — NOT a parallel review system.** It layers
the cross-vendor + diff-only + gates-first constraints on top of the existing `@g-go-review` /
`@g-go-review-swarm` "fresh session, never self-review" discipline, and delegates the actual
gates-first / cross-vendor / re-dispatch / never-merge loop to the already-built
`src/review/` orchestrator (`CrossVendorReview` in `gald3r_agent/src/review/`). It reuses the A6
dispatcher and the swarm engine; it reimplements none of them.

## Trigger Phrases
- `@g-go-xreview` / `@g-go-xreview tasks 14 15`
- "cross-vendor review", "review with a different vendor", "independent vendor review"
- "diff-only review", "gates-first cross-vendor review"

## What it delegates to (do NOT reimplement)

| Concern | Owned by | Surface |
|---|---|---|
| Review queue build, verifier claims, isolation, PASS/FAIL writes, swarm partition | `@g-go-review` / `@g-go-review-swarm` | command machinery (unchanged) |
| Vendor mapping + roster preflight + different-vendor reviewer selection | `src/review/vendor.py` | `probe_roster`, `select_reviewer_harness`, `vendor_of`, `NoCrossVendorReviewer` |
| Diff + acceptance-contract text-only reviewer context | `src/review/bundle.py` | `build_review_bundle`, `ReviewBundle.to_prompt`, `ReviewFinding` |
| Gates-first → cross-vendor → re-dispatch loop → never-merge | `src/review/orchestrator.py` | `CrossVendorReview(...).run(...)` → `ReviewOutcome` |
| Implementer/reviewer `(agent, title)` threads + re-dispatch via title reuse | A6 dispatch | `src.dispatch.Dispatcher` / `DispatchRequest` |
| Parallel multi-task runs | Swarm engine | `src/swarm/` (via `@g-go-review-swarm`) |

The orchestrator's public entry point is `src.review.CrossVendorReview` (an async `.run(...)` plus
`.preflight(...)`). This skill assembles its inputs and invokes it; it does not duplicate its logic.

## Workflow

### Step 0 — Inherit g-go-review preflight (unchanged)
Run the `@g-go-review` preflight stack as-is: Workspace Member Clean-Status preflight, WPAC inbox
gate, Housekeeping Commit Gate, Clean Controller Gate, Branch Pre-Flight, and review-queue build.
A7 adds steps **on top of** this — it never replaces them. The fresh-session / never-self-review
guarantee is preserved.

### Step 1 — Roster preflight (≥2 vendors or escalate)
Probe the available harness roster and require **≥2 distinct available vendors**.

- Delegate to `select_reviewer_harness(implementer_harness, probe_roster())` (`src/review/vendor.py`).
- If it raises `NoCrossVendorReviewer` (fewer than 2 distinct available vendors), **escalate**:
  do **not** silently fall back to same-vendor review. Report
  `Cross-vendor review unavailable — only {vendors} available; need ≥2 distinct vendors`,
  and offer the explicit degrade to fresh-context single-vendor `@g-go-review` **only with a
  visible warning** (SPEC-A7 §5). Never pretend a same-vendor pass is a cross-vendor pass.
- On success, the selected reviewer is a harness of a **different vendor family** than the
  implementer (e.g. Claude implements → Codex/Pi reviews).

### Step 2 — Deterministic gates BEFORE review
Run the project's existing test/lint/typecheck gates (the same invocations `g-go-code` uses) on the
candidate. While any gate is red, **re-dispatch the SAME implementer** (reuse `agent` + `title` →
same worktree/PR via A6) to green it — **before any reviewer is involved**. This is the
`CrossVendorReview` "gates-to-green" loop; pass the gates as the `gates=[...]` argument rather than
hand-rolling the loop.

### Step 3 — Cross-vendor, diff-only review
Build the reviewer context with `build_review_bundle(diff, acceptance_criteria, task_id)` — **the
`git diff` + the task's Acceptance Criteria as text only.** Never hand the reviewer the worktree,
the filesystem, or the implementer's transcript. The reviewer:
- runs on the **different vendor** chosen in Step 1,
- has **read-only** tools (never edits code; it only reports `ReviewFinding`s),
- marks each finding **blocking** (a criterion unmet / correctness bug) or non-blocking (follow-up).

A weak/empty acceptance contract is flagged (review is only as good as the contract — SPEC-A7 §5).

### Step 4 — Blocking findings → re-dispatch the SAME implementer
Each **blocking** finding becomes a fix sent back to the **same implementer** (reuse `agent` +
`title` → same worktree/PR), then the loop returns to Step 2 (gates) before re-reviewing. This is
bounded by `max_fix_rounds`. **Non-blocking** findings become follow-up tasks (file them via
`g-skl-tasks CREATE TASK`; named-but-not-filed follow-ups are a policy violation, per
`@g-go-review`).

### Step 5 — Never merge
The orchestrator **never** runs `git merge` / `pr merge` — `ReviewOutcome.merged` is always
`False`. The PR / checkpoint is the deliverable; a **human merges**. PASS/FAIL status writes,
TASKS.md/BUGS.md updates, and the review-result commit follow the normal `@g-go-review`
coordinator-owned write rules (in `--swarm`, only the coordinator writes shared state).

## Invocation sketch (delegates to the orchestrator)

```python
from src.dispatch import Dispatcher
from src.review import CrossVendorReview  # the existing orchestrator — do NOT reimplement

review = CrossVendorReview(Dispatcher(...))           # roster probed by default
review.preflight(implementer_harness)                 # raises NoCrossVendorReviewer → escalate
outcome = await review.run(                            # gates → cross-vendor diff-only → loop → never-merge
    implementer_harness=implementer_harness,
    implementer_title=implementer_title,              # reuse → same worktree/PR on re-dispatch
    diff=git_diff_text,
    acceptance_criteria=task_acceptance_criteria,
    gates=[test_gate, lint_gate, typecheck_gate],     # reuse g-go-code's gate invocations
    parse_findings=parse_reviewer_output,
    task_id=task_id,
)
# outcome.approved → no blocking findings; outcome.merged is ALWAYS False (human merges)
# outcome.escalated → cross-vendor review was impossible; surface the reason
```

## Behavioral Rules

| Rule | Why |
|------|-----|
| Reviewer MUST be a different vendor than the implementer | Same family = shared blind spots; not independent |
| <2 distinct vendors → escalate, never silently single-vendor | A false "cross-vendor PASS" is worse than an honest gap |
| Reviewer sees ONLY diff + acceptance contract (text) | Independence of context; judge the change, not the reasoning |
| Gates pass BEFORE any reviewer is involved | Don't spend a reviewer on a red build; re-dispatch implementer first |
| Blocking findings re-dispatch the SAME implementer (title reuse) | Keeps the same worktree/PR; non-blocking → follow-up tasks |
| Orchestrator NEVER merges | The PR is the deliverable; a human merges |
| Delegate to `src/review/` + `g-go-review`/swarm — never fork them | A7 is a layer, not a parallel review system |

## Related
- Command: `@g-go-xreview` (the user-facing front door)
- Base review machinery: `@g-go-review`, `@g-go-review-swarm` (preflight, claims, isolation, writes)
- Orchestrator (delegated to): `gald3r_agent/src/review/` — `CrossVendorReview`, `build_review_bundle`, `select_reviewer_harness`
- Dispatch (A6): `src.dispatch.Dispatcher` / `DispatchRequest`
- Design spec: `.gald3r/specifications_collection/SPEC-A7-cross-vendor-review.md` (T495, EPIC T488)
