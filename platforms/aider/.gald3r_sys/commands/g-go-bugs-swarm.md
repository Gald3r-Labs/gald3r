---
subsystem_memberships: [BUG_AND_QUALITY]
---
Parallel bug-fix swarm — coordinate multiple bug fixes simultaneously: $ARGUMENTS

## Mode: BUG-FIX SWARM (Parallel)

`g-go-bugs-swarm` is the parallel variant of `@g-go-bugs`. It follows the same
reproduce → fix → regression → review loop but runs multiple bugs concurrently using
the swarm bucket architecture from `@g-go --swarm`.

> **Independence guarantee**: Phase 2 reviewer agents have no Phase 1 context.
> Adversarial independence is preserved per bucket.

> **Coordinator-owned writes**: Bucket agents return patch bundles, evidence, and proposed
> status rows only. The coordinator performs all shared `.gald3r/` writes, CHANGELOG, and
> commits. Bucket agents MUST NOT write BUGS.md, bug files, or shared coordination surfaces.

---

### ⛔ NO-PROMPT RULE

**NEVER ask for confirmation, scope choices, or approval mid-run.** This is fire-and-forget.
Hard-gate failures are the only valid stop reasons (see hard stops below).

---

## Invocation

```
@g-go-bugs-swarm                    # all open bugs in parallel, critical→high→medium→low
@g-go-bugs-swarm severity:critical  # only critical bugs, max parallelism
@g-go-bugs-swarm severity:critical,high  # critical + high
@g-go-bugs-swarm bug:BUG-042,BUG-043    # specific bugs in parallel
@g-go-bugs-swarm --dry-run          # preview fix queue and bucket plan
```

---

## Phase 1: Parallel Bug-Fix (Swarm)

### Coordinator Preflight

Before spawning any bucket agents:

1. **PCAC inbox gate** — same as `@g-go-bugs` (only when PCAC is configured)
2. **Housekeeping commit gate** — `gald3r_housekeeping_commit.ps1 -Mode preflight -Apply -Json`
3. **Clean Controller Gate** — `git status --short`; stop if unrelated dirty paths
4. **Claim all target bugs at once** — mark every target bug `[🔄]` / `in-progress` in BUGS.md
   (prevents other agents from double-claiming during parallel work)

### Bug Partitioning

```
Smart Agent Count:
  1 bug     → 1 bucket (no swarm — fallback to sequential @g-go-bugs)
  2–4 bugs  → 2 buckets
  5–8 bugs  → 3 buckets
  9+ bugs   → 4 buckets (hard cap — bug-fix buckets are heavier than task buckets)

Batching for low-severity:
  medium/low bugs may be batched 2–3 per bucket
  critical/high bugs always get their own bucket
```

Each bucket is assigned bugs that:
- Do NOT share subsystems (conflict-safety)
- Are ordered by severity within the bucket (critical first)

### Worktree Creation (Per Bucket)

```powershell
.\scripts\gald3r_worktree.ps1 -Action Create -BugId {bug_ids_csv} -Role code-swarm -Owner {owner} -Json
```

Create one worktree per bucket before spawning agents. Pass `worktree_path` and
`worktree_branch` to each implementer.

### Bucket Agent Protocol

Each bucket agent receives:
- Assigned bug IDs and their `.gald3r/bugs/open/bugNNN_*.md` specs
- The worktree path to work in
- Coordinator-managed override: "Return patch bundle, regression test evidence, proposed
  BUGS.md rows, and Status History rows. Do NOT write BUGS.md, shared bug files, CHANGELOG.md,
  or commit. Use explicit path staging only — no `git add .`."

For each assigned bug, bucket agents:
1. Read bug spec (reproduction steps, expected/actual)
2. Reproduce — if cannot reproduce, record `cannot-reproduce` in handoff, skip fix
3. Fix — minimal fix in worktree
4. Add regression test
5. Run regression test (must pass)
6. Return handoff:
   ```
   bug_id: BUG-{id}
   verdict: fixed | cannot-reproduce | blocked
   patch: <git diff --binary --cached HEAD output>
   regression_test: {test file path and test name}
   test_evidence: {test output showing pass}
   proposed_bugs_md_row: "| [🔍] | BUG-{id} | ... |"
   proposed_status_history: "| YYYY-MM-DD | in-progress | awaiting-fix-review | Fixed + regression test |"
   changed_files: [list of modified paths]
   touch_repos: []  # additional repos edited, if any
   ```

Bucket agents MUST NOT use `git add .`. Use explicit `git add -- {paths}` only.

### Coordinator Reconciliation

After all bucket handoffs:

1. **Pre-Reconciliation Clean Gate** — re-run `git status --short` at orchestration root
2. For each bucket (in dependency order, lowest BUG-NNN first):
   - Stage only intended files: `git add -A -- {changed_files}`
   - Export patch: `git diff --binary --cached HEAD`
   - Apply to primary checkout: `git apply --3way --index`
   - If patch fails: preserve worktree, mark bug as skipped
3. **Coordinator-owned batch writes**:
   - Update BUGS.md (all fixed bugs → `[🔍]`)
   - Update individual bug files (status + Status History)
   - Update linked fix tasks (if `fix_task_id:` set via T1114)
4. **Post-write housekeeping gate**: `gald3r_housekeeping_commit.ps1 -Mode post-write -Apply -Json`
5. **Checkpoint commit** (one commit for the whole swarm run):
   ```
   fix(bugs): swarm fix BUG-{id1}, BUG-{id2}, ... ({N} bugs)
   
   Bugs: BUG-{id1}, BUG-{id2}, ...
   Regression tests added for each fix.
   ```

---

## Phase 2: Swarm Review (Parallel)

Partition the `[🔍]` bugs round-robin across M reviewer agents (same count formula as Phase 1).

### Coordinator Claims Review Slots

Before spawning reviewers, atomically claim each `[🔍]` bug as `[🕵️]` / `verification-in-progress`
(skip non-expired claims; log stale takeovers).

Create one `review-swarm` worktree per reviewer from the Phase 1 checkpoint branch/SHA.

### Reviewer Agents

Each reviewer receives:
- Assigned bug IDs
- The `review-swarm` worktree path
- Coordinator override: "Return PASS/FAIL payloads and Status History rows only. No shared writes."

For each assigned bug:
1. Re-run reproduction steps → confirm fix resolves symptom
2. Run regression test → must pass
3. Run full test suite (if available) → no new failures
4. Return verdict: PASS or FAIL + evidence + proposed Status History row

### Coordinator Final Writes

After all review payloads:
1. Batch-update BUGS.md (PASS → `[✅]` Resolved; FAIL → back to `[🔴]`/`[🟠]`)
2. Batch-update bug files (PASS → `resolved`; FAIL → `open`)
3. Update linked fix tasks (PASS → `[✅]`; FAIL → `[📋]`)
4. Stuck-loop check: ≥3 FAILs → `[🚨]` (T047 circuit breaker)
5. Post-write housekeeping gate
6. Review-result commit (one per swarm run):
   ```
   fix(bugs): review result — {N} resolved, {M} failed
   
   Resolved: BUG-{ids}
   Failed: BUG-{ids}
   ```

---

## Follow-Up Task Filing Gate (MANDATORY — before Swarm Summary)

Same as `@g-go-bugs`: all follow-up items MUST be filed as real task files via
`g-skl-tasks CREATE TASK` before the summary is written. Named-only slugs are a policy
violation (T1113 enforcement).

---

## Swarm Pipeline Summary

```markdown
## g-go-bugs-swarm Session Summary

Run: g-go-bugs-swarm {args}
Bugs attempted: N
Buckets (Phase 1): {N implementers}
Reviewers (Phase 2): {M reviewers}

### Phase 1: Implementation
| Bucket | Bugs | Fixed → [🔍] | Skipped |
|--------|------|--------------|---------|
| 1 | BUG-042, BUG-043 | 2 | 0 |
| 2 | BUG-044 | 0 | 1 (cannot reproduce) |

Checkpoint: {branch}@{commit_sha}

### Phase 2: Review
| Reviewer | Bugs | PASS | FAIL |
|----------|------|------|------|
| R-1 | BUG-042, BUG-044 | 2 | 0 |
| R-2 | BUG-043 | 0 | 1 |

Review commit: {sha}

### Results
- ✅ BUG-{id}: {title} — fixed + verified
- ❌ BUG-{id}: {title} — fix failed: {reason}
- ⏸️ BUG-{id}: {title} — could not reproduce, skipped

### Follow-Up Tasks Filed
- T{id}: {title} — {reason surfaced}
(or: None)

### Final State
- ✅ Resolved: {N}
- 📋 Failed (back to open): {M}
- ⏸️ Skipped: {K}
- 🚨 Requires user attention: {U}
- Total commits this run: {C}
```

---

## Hard Stops

| Stop reason | Trigger |
|---|---|
| PCAC conflict | inbox check exit code `2` |
| Unsafe dirty root | housekeeping gate `unsafe-gald3r` / `mixed-dirty` |
| Pre-reconciliation dirty drift | coordinator detects unrelated changes after parallel work |
| `[🚨]` items only | all target bugs are requires-user-attention |
| Secret detection | secret-pattern scanner fires on staged content |
| No runnable bugs | after scope filter, zero eligible bugs |

---

## Behavioral Rules

| Rule | Why |
|------|-----|
| Coordinator claims ALL target bugs before spawning buckets | Prevents double-claiming during parallel work |
| Bucket agents return handoffs only — NO shared writes | Swarm reconciliation policy (T206) |
| `git add .` is forbidden in bucket worktrees | Prevents leaking transient files to commits |
| One checkpoint commit for whole swarm | Cleaner git history than per-bug commits |
| `[🚨]` bugs never retried | Human-only resolution (T047) |
| NEVER ask questions mid-run | Fire-and-forget design |

---

## Examples

```
@g-go-bugs-swarm                    # all open bugs in parallel
@g-go-bugs-swarm severity:critical  # only critical bugs
@g-go-bugs-swarm bug:BUG-042,BUG-043,BUG-044  # specific bug batch
```

See `@g-go-bugs` for sequential (single-agent-per-bug) variant.

Let's swarm those bugs.
