---
name: g-skl-prds
description: Own and manage all PRD data — PRDS.md index, prds/ individual files, governance lifecycle (draft→review→approved→in-implementation→released→archived), revision chain, and freeze enforcement. Parallel artifact to Features for compliance, audit, and external sign-off.
---
# g-skl-prds

**Files Owned**: `.gald3r/PRDS.md`, `.gald3r/prds/prdNNN_*.md`

**Activate for**: "create a PRD", "new PRD", "revise PRD", "approve PRD", "release PRD", "PRD status", "what PRDs do we have", "freeze PRD", "supersede PRD".

> ## Distinction from g-skl-features (single-sentence test)
>
> **A Feature is something we're building. A PRD is something we are accountable for.**
>
> - `g-skl-features` = engineering execution (staging → specced → committed → shipped)
> - `g-skl-prds` = governance, audit, sign-off (draft → review → approved → in-implementation → released → archived)
>
> Features and PRDs are **fully parallel** — neither requires the other. A Feature can ship without a PRD. A PRD can exist without any Features. The optional `related_features:` PRD field is informational only.
>
> Use a PRD when compliance, audit, executive sign-off, or external-stakeholder accountability is required (SOC2, HIPAA, PCI, SOX, regulatory). Use Features for everyday engineering work.

**Hierarchy**: `PRDS.md` is the index. Each `prds/prdNNN_*.md` moves through: `draft → review → approved → in-implementation → released → archived`. Terminal alt-state `superseded` marks the prior version of a revised PRD.

---

## PRD YAML Schema

```yaml
---
id: prd-NNN
title: 'PRD Title'
status: draft              # draft | review | approved | in-implementation | released | archived | superseded
min_tier: slim             # slim | full | adv
subsystems: []             # subsystems this PRD covers
related_features: []       # OPTIONAL list of feat-NNN ids; loose reference only, never enforced
compliance_frameworks: []  # OPTIONAL free-text: ["SOC2-CC6.1", "HIPAA-164.312(a)", "PCI-DSS-3.4"]
data_classification: ''    # OPTIONAL: public | internal | confidential | restricted | regulated
risk_level: ''             # OPTIONAL: low | medium | high | critical
authorizer_name: ''        # OPTIONAL free text — records the human who approved in the user's actual ticketing system
authorizer_date: ''        # OPTIONAL YYYY-MM-DD
authorizer_ticket: ''      # OPTIONAL free text (Jira/ServiceNow/etc.)
supersedes: null           # null OR prd-NNN this revision replaces
superseded_by: null        # null OR prd-NNN that replaced this
created_date: 'YYYY-MM-DD'
released_date: ''          # date moved to released (frozen marker)
archived_date: ''
---
```

**`authorizer_*` semantics** — pure free-text recording fields. gald3r does not enforce, validate, or block on them. The actual approval lives in the user's external ticketing system; gald3r only records the reference.

**`related_features:` semantics** — informational backlink only. Features are not aware of PRDs and never require one. PRD edits do not propagate to Features.

---

## PRD Body Sections (template)

```markdown
# PRD: {title}

## Problem Statement
What problem this solves and why now.

## Scope
What is in scope.

## Non-Scope
What is explicitly out of scope (audit-critical — reviewers and auditors read this section closely).

## Success Metrics
Measurable outcomes with acceptance thresholds.

| Metric | Target | Acceptance |
|--------|--------|------------|

## Risk Assessment
Risks, mitigations, residual risk.

| Risk | Likelihood | Impact | Mitigation | Residual |
|------|------------|--------|------------|----------|

## Compliance & Regulatory Mapping
Framework mappings, control references.

| Framework | Control | Notes |
|-----------|---------|-------|

## Data Handling
Classification, storage, retention, access controls.

## Rollback / Incident Plan
How to revert, who to notify.

## Sign-Off
*Optional free-text block — fills in `authorizer_*` YAML fields above.*

- Authorizer:
- Date:
- Ticket reference:

## Change Log
*Append-only after `released`. Each entry timestamped + reason. Pre-`released` edits use git history.*

| Date | Reason | Authorizer |
|------|--------|------------|

## Related Features
*Optional — backlinks to feat-NNN files for execution traceability.*

- (none)

## Status History
| Timestamp | From | To | Agent | Message |
|-----------|------|-----|-------|---------|
```

---

## Operation: CREATE (new draft PRD)

**Usage**: `CREATE "PRD Title" [--tier slim|full|adv] [--frameworks "SOC2-CC6.1,HIPAA-164.312(a)"] [--classification confidential] [--risk medium]`

1. **Determine next prd ID**: read `PRDS.md` — find highest `prd-NNN` across ALL sections → next = highest + 1
2. **Scope check** (interactive prompt):
   - What problem does this solve?
   - What is in scope / out of scope?
   - Compliance frameworks (optional)?
   - Data classification (optional)?
   - Risk level (optional)?
3. **Create PRD file** at `.gald3r/prds/prdNNN_descriptive_slug.md` with the full body template above and YAML populated from prompts (`status: draft`, `created_date: YYYY-MM-DD`)
4. **Add to PRDS.md** under `### Draft` section:
   ```
   | [prd-NNN](prds/prdNNN_slug.md) | Title | draft | (frameworks) | — | — |
   ```
5. **Append Status History** row: `| YYYY-MM-DD HH:MM | — | draft | g-skl-prds | Created |`
6. Output: confirm `prd-NNN created: .gald3r/prds/prdNNN_slug.md`

---

## Operation: UPDATE (edit non-frozen PRD fields)

**Usage**: `UPDATE prd-NNN <field> <value>`

**Freeze gate**: if PRD `status` is `released` or `superseded`, REJECT with:

```
ERROR: prd-NNN is in status '{status}' and is FROZEN.
Use `@g-prd-revise prd-NNN` to create a v2 revision (recommended for compliance audit trail).
```

For all other statuses:

1. Read PRD file
2. Update YAML field in place
3. If `status` field changes → append Status History row, update PRDS.md section grouping, set status-specific date fields:
   - `status: approved` → no special date
   - `status: in-implementation` → no special date
   - `status: released` → set `released_date: YYYY-MM-DD` (this is the freeze marker)
   - `status: archived` → set `archived_date: YYYY-MM-DD`
4. Write file
5. Update PRDS.md row to match new field values
6. Output: `prd-NNN updated: {field} = {value}`

---

## Operation: REVISE (create v2 from a released PRD)

**Usage**: `REVISE prd-NNN [--reason "rationale"]`

This is the ONLY way to materially change a `released` PRD. Maintains audit trail via the `supersedes:` / `superseded_by:` chain.

1. Read source PRD — must be `status: released` (refuse for any other status; revisions of `superseded` PRDs require revising the latest in the chain instead)
2. **Determine next prd ID**: read `PRDS.md` — next = highest + 1
3. **Copy the file** to `.gald3r/prds/prdMMM_<slug>_v2.md` (or `_v3` etc. based on chain depth)
4. **Update new file YAML**:
   - `id: prd-MMM`
   - `status: draft` (revisions start in draft for re-review)
   - `supersedes: prd-NNN`
   - `superseded_by: null`
   - `created_date: YYYY-MM-DD` (today)
   - `released_date: ''` (clear)
5. **Update old file YAML** atomically:
   - `status: superseded`
   - `superseded_by: prd-MMM`
   - Append `## Change Log` row: `| YYYY-MM-DD | Superseded by prd-MMM: {reason} | (authorizer if known) |`
   - Append Status History row: `| YYYY-MM-DD HH:MM | released | superseded | g-skl-prds | Superseded by prd-MMM |`
6. **Update new file**: append Status History row: `| YYYY-MM-DD HH:MM | — | draft | g-skl-prds | Revision of prd-NNN: {reason} |`
7. **Update PRDS.md** index:
   - Move old row from `### Released` → `### Superseded` section
   - Add new row to `### Draft` section
8. Output: `prd-MMM created from prd-NNN. Old PRD marked superseded.`

---

## Operation: ARCHIVE (soft-delete)

**Usage**: `ARCHIVE prd-NNN [--reason "rationale"]`

Never hard-deletes a PRD — preserves audit trail.

1. Read PRD file
2. Update YAML: `status: archived`, `archived_date: YYYY-MM-DD`
3. Append Status History row
4. Move file to `.gald3r/prds/archive/` (create folder if missing)
5. Update PRDS.md: move row from current section → `### Archived`
6. Output: `prd-NNN archived.`

---

## Operation: STATUS (list PRDs)

**Usage**: `STATUS [--status <s>] [--frameworks <fw>] [--tier slim|full|adv]`

Reads `PRDS.md` and outputs a summary.

```
PRDS STATUS
───────────────────────────────────────
Draft (N)
  prd-NNN  Title                 [slim] frameworks: SOC2-CC6.1
  ...
Review (N)
  prd-NNN  Title                 [full]
  ...
Approved (N)
  prd-NNN  Title                 [adv]
  ...
In-Implementation (N)
  prd-NNN  Title                 [full]  → released_date target: YYYY-MM-DD
  ...
Released (N) — FROZEN
  prd-NNN  Title                 [full]  released: YYYY-MM-DD  authorizer: Name (Ticket)
  ...
Superseded (N)
  prd-NNN  Title  → prd-MMM
  ...
Archived (N)
  prd-NNN  Title  archived: YYYY-MM-DD
  ...
───────────────────────────────────────
Total: N PRDs | Active: N (excluding archived/superseded)
Next prd ID: prd-NNN
```

---

## PRDS.md Index Structure

```markdown
# PRDS.md — {project_name} PRD Registry

## Overview
PRDs are governance artifacts: compliance, audit, executive sign-off, external accountability.
Each `prds/prdNNN_*.md` carries the full record. Released PRDs are frozen; revisions go through `@g-prd-revise`.

### PRD Lifecycle
draft → review → approved → in-implementation → released → archived
                                                  └─→ superseded (terminal alt-state for revised PRDs)

| Status              | Meaning |
|---------------------|---------|
| draft               | First-pass content; freely editable |
| review              | Out for review; freely editable but should be stable |
| approved            | Reviewer/authorizer approved; freely editable until release |
| in-implementation   | Engineering work underway; freely editable |
| released            | FROZEN — only `@g-prd-revise` can modify (creates v2) |
| archived            | Soft-deleted; preserved for audit |
| superseded          | Replaced by a newer prd-MMM; preserved for audit chain |

## PRDs Index

### Released
| ID | Title | Status | Frameworks | Authorizer | Released Date |

### In-Implementation
| ID | Title | Status | Frameworks | Authorizer | Released Date |

### Approved
| ID | Title | Status | Frameworks | Authorizer | Released Date |

### Review
| ID | Title | Status | Frameworks | Authorizer | Released Date |

### Draft
| ID | Title | Status | Frameworks | Authorizer | Released Date |

### Superseded
| ID | Title | Status | Frameworks | Authorizer | Released Date |

### Archived
| ID | Title | Status | Frameworks | Authorizer | Released Date |

---
**Last Updated**: YYYY-MM-DD
**Next prd ID**: prd-NNN
```

---

## ID Sequencing Rules

- PRD IDs are globally sequential: `prd-001`, `prd-002`, ... `prd-NNN`
- IDs are never reused — even after archive or supersede
- Revisions get a new sequential ID (NOT a v1/v2 suffix in the ID); the supersedes-chain is the audit trail
- Slug may include a version hint for human readability (e.g., `prd012_payment_processing_v2.md`)

---

## Freeze Enforcement (Critical)

`released` and `superseded` PRDs are **immutable**. The skill blocks edits. This is reinforced by:

- `g-skl-prds UPDATE` rejects with a clear error pointing to `g-prd-revise`
- `g-rl-33-enforcement_catchall.md` enforces parallel restraint at the agent level — no direct file writes to frozen PRDs
- Constraint `C-019` (PRDs in status `released` or `superseded` are immutable except via `g-prd-revise`)

The `## Change Log` section IS appendable on a `released` PRD specifically to record the supersede event when a revision is created. No other content changes are permitted on a frozen PRD.

---

## Integration Points

**With `g-skl-features`**: zero coupling. Features have no awareness of PRDs. PRDs may carry an optional `related_features:` list as a backlink only. A Feature shipping does not require a PRD; a PRD existing does not require Features.

**With `g-skl-tasks`**: tasks may reference a PRD via the existing `prd:` YAML field. This is informational only; tasks remain the engineering execution layer.

**With `g-skl-subsystems`**: PRDs may list subsystems in YAML — used for cross-reference and audit ("which subsystems does this control map to?").

**With `g-skl-constraints`**: C-019 (PRDs frozen on `released`) is the canonical enforcement constraint.

**With session start (`g-rl-25`)**: optional — surface count of `in-implementation` PRDs at session start. Not required.

---

## When to Use a PRD vs a Feature

Reach for a **PRD** when ANY of:
- Compliance / regulatory framework requires a documented, signed-off artifact
- External stakeholder (executive, customer, auditor) needs a single-source-of-truth document
- Sign-off and accountability are first-class concerns (the question "who approved this?" must be answerable)
- Rollback / incident plan must be pre-recorded for audit
- Risk assessment with mitigations must be on file

Reach for a **Feature** when:
- Engineering team needs to plan, stage, and execute capability work
- The artifact is for the team, not the auditor
- Approval is implicit (PR review, sprint planning) rather than formal sign-off

When in doubt: build a Feature. Add a PRD later if compliance asks for one. They are fully parallel; you can do both for the same capability if needed.
