# g-res-review

Review existing recon reports in `vault/research/recon/` and triage features for adoption.

Activates **g-skl-res-review** → REVIEW operation.

> **Replaces**: `@g-harvest --review` (that mode is now `@g-res-review`)

## Usage

```
@g-res-review                          # list all available recon reports
@g-res-review {slug}                   # review a specific report
@g-res-review --all-unadopted          # surface all unadopted suggestions across reports
```

## What it does

1. Scans `vault/research/recon/` for `04_FEATURES.md` files
2. Presents unadopted features for user triage:
   - `[✅]` approve → mark for `@g-res-apply`
   - `[❌]` reject → flag as dismissed
   - `[⏸]` defer → skip in APPLY, surface again next review cycle
3. Shows feature counts, source repos, and time-since-last-review per report
4. If `--topology-aware` (requires T118): cross-references capabilities.md to suggest `--target` routing

## Zero-change-without-approval guarantee

`@g-res-review` **never modifies `.gald3r/`** — it only updates approval status markers in the
`vault/research/recon/{slug}/04_FEATURES.md` review columns.

## See Also

- `@g-res-deep` — Run the deep analysis pass to generate a recon report
- `@g-res-apply` — Apply approved features to `.gald3r/`
