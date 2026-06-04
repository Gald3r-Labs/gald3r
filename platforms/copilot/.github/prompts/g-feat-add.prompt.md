Stage a new feature. Activates **g-skl-features** → STAGE operation.

```
@g-feat-add "Feature Name"
@g-feat-add "Feature Name" --goal G-01
@g-feat-add "Feature Name" --tier full
@g-feat-add "Feature Name" --from-harvest research/harvests/repo_slug/
@g-feat-add "Feature Name" --skip-match
```

**Before creating**, automatically runs `g-skl-features MATCH` to check for existing features that cover the same capability. If a match is found, prompts to collect into the existing feature instead of creating a duplicate.

- `exact match found` → offers to COLLECT into existing feat instead
- `fuzzy match found` → shows candidates, asks: separate / merge / show-me-both
- `no match` → proceeds directly to create

Use `--skip-match` to bypass the dedup check (e.g., if you already ran MATCH manually or know it's unique).

Creates `features/feat-NNN_slug.md` with `status: staging`. Does NOT create tasks.
Feature stays in staging until manually promoted with `/g-feat-spec` then `/g-feat-promote`.

> **Alias**: `@g-feat-new` also works (deprecated; use `@g-feat-add` for new work).
