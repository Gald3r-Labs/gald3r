---
name: g-skl-ideas
description: Own and manage IDEA_BOARD.md — capture ideas instantly, review the board, promote to tasks, and run proactive codebase scans for improvement opportunities.
---
# g-ideas

**Files Owned**: `.gald3r/IDEA_BOARD.md`

**Activate for**: "make a note", "idea:", "remember this", "what if we", "someday", "for later", "eventually", review ideas, idea farm scan.

**Rule**: NEVER auto-promote to task. Capture now, user decides later.

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

**Description**:
[The idea in 1-3 sentences. Specific enough to reconstruct intent later.]

**Potential Value**:
[Why worth keeping — problem solved, opportunity, etc.]

**When Ready**:
[Prerequisites or triggers that would make this worth building]

---
```

4. **Confirm and continue**: `💡 Captured as IDEA-NNN: {title}` — then resume current work immediately

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

**Output format** for each idea found:
```markdown
### IDEA-NNN: {Title}
**Status**: raw
**Category**: refactor | simplify | performance | security | feature | test
**Source**: idea-farm (YYYY-MM-DD)
**Effort**: low | medium | high
**Impact**: low | medium | high
**Files**: `{path}` (lines N-M)

**Rationale**: {Why this improvement matters}
```

**Deduplication**: before adding, check if same file + same category already exists in IDEA_BOARD.md.

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
