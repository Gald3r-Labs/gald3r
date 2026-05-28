Create a new PRD. Activates **g-skl-prds** → CREATE operation.

```
@g-prd-add "PRD Title"
@g-prd-add "PRD Title" --tier full
@g-prd-add "PRD Title" --frameworks "SOC2-CC6.1,HIPAA-164.312(a)"
@g-prd-add "PRD Title" --classification confidential --risk medium
```

Creates `prds/prdNNN_slug.md` with `status: draft` and the full PRD body template. Adds an entry to `PRDS.md` under `### Draft`.

PRDs are governance artifacts (compliance, audit, sign-off). Use `@g-feat-add` for engineering execution work — Features and PRDs are fully parallel and neither requires the other.

After creation, fill in Problem Statement, Scope, Non-Scope, Success Metrics, Risk Assessment, Compliance & Regulatory Mapping, Data Handling, and Rollback / Incident Plan. Use `@g-prd-upd prd-NNN status review` when ready for review.
