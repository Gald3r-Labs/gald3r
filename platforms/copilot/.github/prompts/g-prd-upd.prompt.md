Update a PRD field. Activates **g-skl-prds** → UPDATE operation.

```
@g-prd-upd prd-NNN status review
@g-prd-upd prd-NNN status approved
@g-prd-upd prd-NNN status in-implementation
@g-prd-upd prd-NNN status released
@g-prd-upd prd-NNN authorizer-name "Jane Doe"
@g-prd-upd prd-NNN authorizer-date 2026-04-25
@g-prd-upd prd-NNN authorizer-ticket "JIRA-1234"
@g-prd-upd prd-NNN add-framework "PCI-DSS-3.4"
@g-prd-upd prd-NNN risk-level high
```

**Freeze gate**: PRDs in status `released` or `superseded` are FROZEN. `@g-prd-upd` will reject with a clear error and direct you to `@g-prd-revise`. This protects the audit trail.

Status transitions append a row to the PRD's `## Status History` table. Moving to `released` sets `released_date` (the freeze marker). Moving to `archived` sets `archived_date` and moves the file to `prds/archive/`.
