Assign tasks to a release. Activates **g-skl-release** → ASSIGN operation.

```
@g-release-assign 002 42
@g-release-assign 002 42,55,61
@g-release-assign "Spring Drop" 42,55
```

Merges the provided task IDs into the release's `tasks:` frontmatter list (de-duplicated, sorted), refreshes the `## Included Tasks` body bullets, and updates the `Tasks` column in `RELEASES.md`.

When Task 052-4 ships, also writes `release_id: {NNN}` back into each task file's frontmatter.
