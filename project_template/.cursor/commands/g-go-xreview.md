---
subsystem_memberships: [AGENT_ORCHESTRATION]
---
Cross-vendor verification review (A7 / T495): $ARGUMENTS

## Mode: CROSS-VENDOR REVIEW ONLY

> ⚠️  **Run this in a NEW agent session** — different window, different invocation.
> If you implemented any of these tasks in this session, **skip them** (leave `[🔍]`).
> Self-review defeats the purpose of this gate.

This command is the **user-facing front door for cross-vendor review.** It is **not a parallel
review system** — it runs `@g-go-review` (and `@g-go-review --swarm` for parallel runs) and adds
the A7 constraints on top via **`g-skl-cross-review`**, which delegates to the already-built
`gald3r_agent/src/review/` orchestrator (`CrossVendorReview`). Everything `@g-go-review` does —
preflight, verifier claims, review isolation, PASS/FAIL writes, swarm partitioning, review-result
commit — is **inherited unchanged**. A7 adds only: a different-vendor reviewer, diff-only reviewer
context, deterministic gates first, and a never-merge guarantee.

Activates **g-skl-cross-review**.

---

### Step 0 — Inherit the full g-go-review preflight (unchanged)

Run the `@g-go-review` preflight stack as-is — do not re-document or fork it here:
Workspace Member Clean-Status Preflight (T1431), WPAC inbox Gate, Gald3r Housekeeping Commit Gate
(T531), Clean Controller Gate + Pre-Reconciliation Clean Gate, Branch Pre-Flight (T1374), and the
review-queue build (`[🔍]` tasks **and** bugs; skip non-expired `[🕵️]` claims). The fresh-session /
never-self-review guarantee is preserved. **See `@g-go-review` for the authoritative algorithm.**

### Step 1 — Roster preflight (≥2 vendors or escalate)

Probe the available harness roster. Delegate to `g-skl-cross-review` Step 1
(`select_reviewer_harness(implementer_harness, probe_roster())` in `src/review/vendor.py`):

- **≥2 distinct available vendors** → pick a reviewer harness of a **different vendor** than the
  implementer (Claude → Codex/Pi, etc.). Continue.
- **<2 distinct vendors** (`NoCrossVendorReviewer`) → **STOP and escalate.** Do **not** silently
  single-vendor. Report `Cross-vendor review unavailable — only {vendors} available; need ≥2`.
  Offer the explicit, **warned** degrade to fresh-context single-vendor `@g-go-review`. Never
  report a same-vendor pass as a cross-vendor pass.

### Step 2 — Deterministic gates BEFORE review

Run the project's existing test/lint/typecheck gates (the same invocations `@g-go-code` uses) on
the candidate. Red → **re-dispatch the SAME implementer** (reuse `agent` + `title` → same
worktree/PR via A6) to green it **before any reviewer is involved**. This is the
`CrossVendorReview` gates-to-green loop — pass the gates to the orchestrator; do not hand-roll it.

### Step 3 — Cross-vendor, diff-only review

For each claimed `[🕵️]` item, hand the **different-vendor** reviewer a context bundle built by
`build_review_bundle(diff, acceptance_criteria, task_id)` — **the `git diff` + the task's
Acceptance Criteria as text ONLY** (no worktree, no implementer transcript). The reviewer has
**read-only** tools, **never edits**, and marks each finding **blocking** or non-blocking. A
weak/empty acceptance contract is flagged. Score PASS/FAIL per criterion exactly as `@g-go-review`
Step 3 does.

### Step 4 — Blocking findings → re-dispatch the SAME implementer

Each **blocking** finding re-dispatches a fix to the **same implementer** (reuse `agent` + `title`
→ same worktree/PR), then loop back to Step 2 (gates) before re-reviewing (bounded by
`max_fix_rounds`). **Non-blocking** findings become follow-up tasks — file them via
`g-skl-tasks CREATE TASK` (named-but-not-filed follow-ups are a policy violation).

### Step 5 — Never merge; write verdicts the g-go-review way

The orchestrator **never** runs `git merge` / `pr merge` (`ReviewOutcome.merged` is always
`False`) — the PR / checkpoint is the deliverable; a **human merges**. PASS → `[✅]`, FAIL → back
to `[📋]` (with the stuck-loop `[🚨]` rule), docs check, auto-learn, and the review-result commit
all follow the normal `@g-go-review` coordinator-owned write rules. In `--swarm`, only the
coordinator writes shared state.

---

## Swarm Mode (`--swarm`)

`@g-go-xreview --swarm` runs the cross-vendor review over `@g-go-review --swarm` — the swarm engine
(`src/swarm/`) partitions the `[🔍]` queue across parallel reviewers exactly as
`@g-go-review-swarm` does; each bucket applies the A7 cross-vendor + diff-only + gates-first +
never-merge constraints from `g-skl-cross-review`. Review bucket agents return PASS/FAIL payloads,
evidence, proposed Status History rows, and authorized fix-forward patches only; the coordinator
owns all shared `.gald3r` writes, TASKS.md/BUGS.md updates, changelog/docs, and the review-result
commit. **See `@g-go-review` Swarm Mode for the authoritative coordinator algorithm.**

## Usage

```
@g-go-xreview
@g-go-xreview tasks 14 15 16
@g-go-xreview tasks 14
@g-go-xreview --swarm
@g-go-xreview --swarm tasks 14 15 16 17 18
```

All filter arguments pass through to `@g-go-review`. Use this command when you specifically want a
**different-vendor** reviewer on the diff; use `@g-go-review` when same-vendor fresh-context review
is sufficient.

## Related

- Skill: `g-skl-cross-review` (implementation; delegates to `src/review/`)
- Base review machinery: `@g-go-review`, `@g-go-review-swarm`
- Orchestrator: `gald3r_agent/src/review/` — `CrossVendorReview`, `build_review_bundle`, `select_reviewer_harness`
- Design spec: `.gald3r/specifications_collection/SPEC-A7-cross-vendor-review.md` (T495, EPIC T488)

Ready to review.
