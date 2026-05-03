# CONSTRAINTS.md — {PROJECT_NAME}

## Governance

This file is loaded at every session start. Constraints listed here are **non-negotiable** — they govern every decision made in this project.

No AI agent may override, work around, or silently ignore a constraint. Constraints may only be changed or removed with **explicit user approval** as described below.

### Who Can Change Constraints

The user has ultimate authority over all constraints. AI agents may:
- Flag when a requested action conflicts with an active constraint
- Suggest adding, modifying, or removing a constraint
- Explain the tradeoffs of a proposed change

AI agents may **NOT**:
- Assume silence or inferred agreement is approval
- Modify a constraint based on conversational context alone
- Bypass a constraint temporarily without explicit approval
- Override any constraint unilaterally

### What Counts as Approval

Approval requires an explicit, unambiguous statement from the user in the current session.

**Accepted approval phrases**: "yes", "approved", "accept", "go ahead", "confirmed", "do it"

**What does NOT count as approval**: user not objecting, user asking a question, prior-session approval, silence.

### Logging Requirement

Every change to this file must be recorded in the **Change Log** at the bottom of this document. The log is append-only.

---

## Constraint Index

| ID | Status | Name | Scope | One-line summary |
|----|--------|------|-------|-----------------|

*(No constraints yet — use `@g-constraint-add` to define the first constraint)*

---

## Constraint Definitions

*(Constraint definitions will appear here as constraints are added)*

---

## Archived Constraints

*Constraints that have expired or been deprecated. Retained for audit history.*

| ID | Title | Type | Archived Date | Reason |
|----|-------|------|---------------|--------|

---

## Change Log

| Date | ID | Change | Approved By |
|------|----|--------|-------------|
| {YYYY-MM-DD} | — | CONSTRAINTS.md initialized | project setup |
