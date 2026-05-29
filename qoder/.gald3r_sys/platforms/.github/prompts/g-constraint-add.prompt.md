# g-constraint-add

Add a new architectural constraint to `.gald3r/CONSTRAINTS.md`.

## When to use

Run this command when you want to formalize a new non-negotiable architectural rule for the project. New constraints should be rare — they are permanent guardrails, not preferences.

## Steps

1. Read `g-skl-constraints` skill
2. Run the **ADD** operation

## Process

The skill will:
1. Assign the next sequential C-ID
2. Prompt for name, rationale, applies-to, in-practice rules, violation examples, enforcement, scope
3. *(Optional)* Offer expiry fields: `expires_at` (date), `resolved_when_task` (task ID), `resolved_when_feature` (feature slug), `resolved_when` (free-text condition), `auto_archive` (default: true)
4. Update `## Constraint Index` table
5. Add full `## Constraint Definitions` block (with optional expiry fields)
6. Append entry to `## Change Log`

**Note**: Expiry fields are for temporary constraints only (migration guards, sprint policies). Permanent architectural rules should never have expiry. The skill warns if `scope: ecosystem-wide` constraints have expiry set.

## Usage

```
@g-constraint-add
```

Or with context:
```
@g-constraint-add — All SQL queries must use parameterized statements, never string formatting
```
