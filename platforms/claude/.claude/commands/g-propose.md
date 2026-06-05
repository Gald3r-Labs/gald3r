---
subsystem_memberships: [TASK_MANAGEMENT]
---
One-shot proposal generation: produces a complete proposal package from a short description.

```
@g-propose "Add dark mode toggle to settings panel"
@g-propose "Replace synchronous file writes with async queue" --scope backend
@g-propose "Integrate Stripe payments" --scope payments,auth --constraints "no new deps"
```

## What This Command Does

Accepts a feature description and generates a self-contained **proposal document** at
`docs/proposals/YYYYMMDD_HHMMSS_Cursor_PROPOSAL_<slug>.md` covering everything needed
for human approval before any `.gald3r/` writes occur.

One command, one file, full context.

---

## Workflow

### Step 1 — Parse Input

Extract from `$ARGUMENTS`:
- **description** — required; the feature or change to propose
- `--scope <areas>` — optional; comma-separated subsystems or areas in scope
- `--constraints <text>` — optional; non-negotiable limits (budget, deps, API compat)

If description is missing or too vague (< 5 words), ask one clarifying question before continuing.

### Step 2 — Generate Proposal Document

**Filename**: `docs/proposals/YYYYMMDD_HHMMSS_Cursor_PROPOSAL_<slug>.md`
- Slug: lowercase description, spaces→underscores, max 40 chars, strip special chars
- Timestamp: use current UTC time (YYYYMMDD_HHMMSS format per g-rl-01 naming convention)

**Document structure** (fill all sections, do not leave placeholders):

```markdown
# Proposal: <Title>

> **Status**: draft | **Created**: YYYY-MM-DD | **Author**: g-propose

## Executive Summary
<!-- 3–5 sentences. What is being built, why now, and what success looks like. -->

## Problem Statement
<!-- Current pain point or gap. Why the status quo is insufficient. -->

## Proposed Solution
<!-- High-level solution description. What changes, at what layer. -->

## Technical Design

### Architecture
<!-- Key components, interaction diagram (ASCII or description), data flow. -->

### Data Model
<!-- New tables / fields / schema changes. "None" if not applicable. -->

### API Surface
<!-- New endpoints, commands, events, or public interfaces. -->

### Dependencies
<!-- New packages or services required. "None" if not applicable. -->

## Acceptance Criteria
<!-- Ready to paste into a task spec. Phrase as "Given / When / Then" or checkbox list. -->
- [ ] ...
- [ ] ...
- [ ] ...

## PRD Draft
<!-- Pre-filled content for @g-prd-add. Agent will paste this when user approves. -->

**Title**: <same as proposal title>
**Problem Statement**: <1 paragraph>
**Scope**: <what is in>
**Non-Scope**: <what is explicitly out>
**Success Metrics**: <measurable outcomes>
**Risk Assessment**: low | medium | high — <brief rationale>
**Data Handling**: <PII / sensitive data implications, or "None">
**Rollback Plan**: <how to revert if needed>

## Task Breakdown
<!-- 3–7 tasks, each ready for @g-task-add. Use dependency arrows where needed. -->

| # | Title | Type | Deps | Notes |
|---|-------|------|------|-------|
| 1 | ... | feature | — | ... |
| 2 | ... | feature | T1 | ... |

## Risks & Alternatives

### Risks
| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| ... | low/med/high | low/med/high | ... |

### Alternatives Considered
- **Alt A**: <name> — <why rejected>
- **Alt B**: <name> — <why rejected>

## Open Questions
<!-- List any unresolved decisions the human must answer before approval. -->
- [ ] ...
```

### Step 3 — Write the File

- Create `docs/proposals/` directory if it does not exist.
- Write the completed proposal file.
- Do **NOT** write to `.gald3r/` yet — all gald3r artifacts are created only after human approval.

### Step 4 — Show Summary and Next-Step Menu

After writing the file, output:

```
✅ Proposal generated: docs/proposals/<filename>.md

📋 Summary
  Feature : <title>
  Scope   : <scope or "not specified">
  Tasks   : <N> tasks in breakdown
  Risks   : <N> identified

📌 Next steps — choose one:
  A) Approve  → run @g-prd-add "<title>" then @g-task-add for each task
  B) Refine   → edit docs/proposals/<filename>.md then re-run @g-propose --from-file
  C) Discard  → delete docs/proposals/<filename>.md
```

Wait for the user to choose. Do not auto-create PRD or tasks.

---

## Optional: `--from-file`

```
@g-propose --from-file docs/proposals/20260509_120000_Cursor_PROPOSAL_dark_mode.md
```

Re-reads an existing proposal file and outputs the **Approve** next steps (PRD + task
creation commands) without regenerating. Use after refinement.

---

## Constraints

- Proposal file lives in `docs/` per g-rl-01 (not project root).
- No `.gald3r/` writes until user explicitly approves.
- Proposal is a **draft artifact** — it has no TASKS.md entry until approved.
- Keep the generated document under 400 lines.
- If `--scope` references subsystem names, cross-check against `.gald3r/SUBSYSTEMS.md`
  and note any mismatches in the Open Questions section.
