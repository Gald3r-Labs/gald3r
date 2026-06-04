Publish `ROADMAP.md`. Activates **g-skl-release** → PUBLISH operation.

```
@g-release-publish
```

Scans `.gald3r/releases/` for all `planned`, `in_progress`, and `released` files, sorts them by `target_date`, and writes `ROADMAP.md` at the project root as a two-section table (Upcoming + Released).

When Task 052-5 ships, this delegates to the full tier×window grid generator with `roadmap_visibility` filtering (public / teaser / secret). Until then, entries are included regardless of visibility.
