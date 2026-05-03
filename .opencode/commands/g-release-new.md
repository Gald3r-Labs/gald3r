Create a new release. Activates **g-skl-release** → CREATE operation.

```
@g-release-new "Release Name"
@g-release-new "Release Name" --version 1.2.0
@g-release-new "Release Name" --target 2026-05-15
@g-release-new "Release Name" --cadence 21
```

Creates `.gald3r/releases/release{NNN}_{slug}.md` and appends a row to `RELEASES.md`.

- Next ID = highest in `RELEASES.md` + 1 (zero-padded to 3 digits)
- `target_date` defaults to (most-recent target_date + `cadence_days`); falls back to (today + cadence) for the first release
- `cadence_days` defaults to 14 (biweekly)
- Status starts at `planned`
