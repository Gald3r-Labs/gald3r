Revise a released PRD. Activates **g-skl-prds** → REVISE operation.

```
@g-prd-revise prd-NNN
@g-prd-revise prd-NNN --reason "Updated risk assessment for new threat model"
```

The ONLY supported way to materially change a `released` PRD. Atomic operation:

1. Reads source PRD (must be `status: released`)
2. Creates a new file `prds/prdMMM_<slug>_v2.md` (or `_v3` etc.) with:
   - Fresh sequential `id: prd-MMM`
   - `status: draft` (revisions start in draft for re-review)
   - `supersedes: prd-NNN`
3. Updates the old PRD atomically:
   - `status: superseded`
   - `superseded_by: prd-MMM`
   - Appends `## Change Log` row recording the supersede event
4. Updates `PRDS.md`: old row → `### Superseded` section; new row → `### Draft`

This preserves the audit chain. Compliance reviewers can walk the `supersedes:` / `superseded_by:` linked list to see the full revision history.
