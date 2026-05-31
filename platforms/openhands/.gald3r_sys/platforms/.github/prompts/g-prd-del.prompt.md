Archive a PRD (soft-delete). Activates **g-skl-prds** → ARCHIVE operation.

```
@g-prd-del prd-NNN
@g-prd-del prd-NNN --reason "Replaced by alternative compliance approach"
```

Sets `status: archived`, populates `archived_date`, appends to `## Status History`, and moves the file to `prds/archive/`. Updates `PRDS.md` row to the `### Archived` section. PRD is preserved on disk — never hard-deletes.

If the PRD is in status `released`, prefer `@g-prd-revise` first to mark it superseded with a documented replacement, then archive.
