---
name: g-skl-ideas
description: Own and manage IDEA_BOARD.md — capture ideas instantly, review the board, promote to tasks, and run proactive codebase scans for improvement opportunities.
token_budget: low
subsystem_memberships: [PROJECT_IDENTITY_SETUP, VAULT_AND_RESEARCH]
---
# g-ideas

**Files Owned**: `.gald3r/IDEA_BOARD.md`

**Activate for**: "make a note", "idea:", "remember this", "what if we", "someday", "for later", "eventually", review ideas, idea farm scan.

**Rule**: NEVER auto-promote to task. Capture now, user decides later.

**MCP acceleration (optional — guarded until T493 passes):** When a gald3r MCP server is configured, `capture_idea` can be routed through the MCP adapter (`adapter.capture_idea(content=..., category=..., source=...)`) instead of writing to `IDEA_BOARD.md` directly. File-first fallback is always required.

---

## Operation: CAPTURE (immediate — do not derail session)

**Trigger phrases**: "make a note", "idea:", "remember this", "what if we", "someday", "for later", "eventually"

1. **Get next ID**: read `IDEA_BOARD.md`, find highest IDEA-NNN → increment
2. **Classify**:
   - `feature` — new capability
   - `monetization` — revenue/pricing
   - `ux` — user experience improvement
   - `technical` — architecture, performance, tooling
   - `architecture` — structural change
   - `business` — strategy, positioning

3. **Add entry** under `## Active Ideas` in `IDEA_BOARD.md`:
```markdown
### IDEA-NNN: [Title — concise but specific]
**Status**: raw
**Category**: [category]
**Captured**: YYYY-MM-DD
**Source**: user | AI | session
**Target Repo**: local

**Description**:
[The idea in 1-3 sentences. Specific enough to reconstruct intent later.]

**Potential Value**:
[Why worth keeping — problem solved, opportunity, etc.]

**When Ready**:
[Prerequisites or triggers that would make this worth building]

---
```

#### `target_repo:` — WPAC-aware routing annotation (T1430)

The optional **Target Repo** field controls where the idea's downstream artifacts
(tasks/specs) land when promoted. It is set at capture time and may be changed during
`g-skl-res-review` triage. Supported values:

| Value | Meaning |
|-------|---------|
| `local` (default) | Promote into the current repo's `.gald3r/` |
| `<repo_id>` | A single `repository.id` from `workspace_manifest.yaml` / topology |
| `[repo_id, repo_id]` | Multi-repo list → controller decomposes + dispatches |
| `workspace` | Controller-managed: one undispatched task with `requires_decomposition: true` |

- **`--target-repo <value>` flag** sets it non-interactively: `@g-idea-capture "..." --target-repo example_desktop`.
- When **WPAC is active** (`.gald3r/workspace/topology.md` present) and no flag is given, prompt once: *"Route this idea to a specific repo? (default: local)"*.
- **`--local` flag** (mirrors the `g-vocab-add` convention) forces `local` even inside a workspace — skips the prompt.
- **Unlinked project (no `topology.md`)** → silently store `local`; never prompt, ignore any supplied `--target-repo` value (routing collapses to local downstream — see `g-skl-res-apply`).

4. **Confirm and continue**: `💡 Captured as IDEA-NNN: {title}` (append `→ {target_repo}` when not `local`) — then resume current work immediately

---

## Operation: REVIEW

1. **Read IDEA_BOARD.md** — list all ideas with status `raw` or `evaluating`
2. **Display**:
   ```
   💡 IDEA BOARD REVIEW
   IDEA-001: [Title] (raw) — feature
   IDEA-002: [Title] (evaluating) — monetization
   Total: N active ideas
   ```
3. **For each, show options**:
   - **Promote**: user says "promote IDEA-NNN" → activate g-tasks CREATE, update entry to `accepted`, move to `## Promoted Ideas` with task reference
   - **Evaluate**: needs discussion → set status to `evaluating`
   - **Shelve**: not pursuing → move to `## Shelved Ideas`, add reason + shelved date
   - **Keep raw**: no change
4. **Summary**:
   ```
   Promoted: N → N tasks created | Shelved: N | Evaluating: N | Kept raw: N
   ```

---

## Operation: FARM (proactive scan)

Scan the codebase for improvement opportunities. Limit 10 new ideas per run. Skip duplicates.

**Pass 1 — Simplification**: files >500 lines, functions >50 lines, nesting >4 levels, repeated patterns
**Pass 2 — Dead code**: unused imports, unreferenced functions, commented-out blocks >10 lines
**Pass 3 — Duplication**: similar signatures, copy-pasted blocks, overlapping skill content
**Pass 4 — Best practices**: bare except/catch, missing type hints, missing tests, N+1 patterns
**Pass 5 — Knowledge gaps**: vault research not applied, IDEA_BOARD ideas now unblocked
**Pass 6 — Skill candidates (T1174)**: scan `.gald3r/reports/skill_candidates/` for stubs staged by `g-hk-agent-complete` and promote filled ones to IDEA_BOARD entries with `Category: skill_candidate`

**Output format** for each idea found:
```markdown
### IDEA-NNN: {Title}
**Status**: raw
**Category**: refactor | simplify | performance | security | feature | test | skill_candidate
**Source**: idea-farm (YYYY-MM-DD)
**Effort**: low | medium | high
**Impact**: low | medium | high
**Files**: `{path}` (lines N-M)

**Rationale**: {Why this improvement matters}
```

**Deduplication**: before adding, check if same file + same category already exists in IDEA_BOARD.md.

### Pass 6 — Skill Candidate Sweep (T1174)

When `.gald3r/reports/skill_candidates/` exists, perform a dedicated sub-pass:

1. **List stubs**: enumerate `.gald3r/reports/skill_candidates/*.md`
2. **Read frontmatter** `status:` from each:
   - `pending` (default after hook stages it) → stub is unfilled; skip and report count as `awaiting_input`
   - `discarded` → agent reviewed and decided no reusable pattern; move file to `.gald3r/reports/skill_candidates/discarded/`
   - `filled` or `ready` → eligible for promotion to IDEA_BOARD
3. **Promote filled stubs** to `IDEA_BOARD.md` as a single entry per stub:
   ```markdown
   ### IDEA-NNN: Skill candidate — {name from stub}
   **Status**: raw
   **Category**: skill_candidate
   **Captured**: YYYY-MM-DD
   **Source**: skill_capture_hook ({stub filename})

   **Description**:
   {when_to_use} — {how_it_works} (3-5 lines from stub)

   **Potential Value**:
   Reusable pattern surfaced during task execution. Promote via `@g-skill-create` if validated.

   **When Ready**:
   Review the captured pattern; if it generalizes, scaffold via `@g-skill-create` and link the stub.

   **Stub reference**: `.gald3r/reports/skill_candidates/{filename}`
   ```
4. **Move promoted stub** to `.gald3r/reports/skill_candidates/promoted/{filename}` (preserve audit trail)
5. **Summary line**: `Skill candidates: N pending input, M promoted, K discarded`

**Stub format expected** (matches SKILL.md structure per AC5):
```yaml
---
status: pending | filled | ready | discarded
captured_at: YYYY-MM-DD HH:MM:SS
session_id: ...
task_id: ""
---

## name
<kebab-case skill name>

## when_to_use
<one sentence trigger>

## how_it_works
<3-5 lines of procedure>

## example
<minimal example>
```

**Dedup rule for skill candidates**: skip a stub whose `name:` already appears in any existing IDEA_BOARD entry of category `skill_candidate`. The stub still gets moved to `promoted/` to clear the queue.

---

## IDEA_BOARD.md Structure

```markdown
# IDEA_BOARD.md — {project_name}

## Active Ideas
[entries here]

## Promoted Ideas
[entries moved here when accepted, with task reference]

## Shelved Ideas
[entries moved here when not pursuing, with reason]
```

## Status Values
`raw` → `evaluating` → `accepted` (promoted) | `shelved`
