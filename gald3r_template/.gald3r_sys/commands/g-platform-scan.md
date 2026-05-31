---
subsystem_memberships: [PLATFORM_INTEGRATION]
---
Scan platforms whose official docs are overdue for re-crawl, and refresh staleness state.

## What This Command Does

Runs `custom_scripts/scan_platform_docs.ps1 -StaleOnly` to identify which platforms
have a `last_doc_scan:` older than their per-platform `crawl_max_age_days` window,
crawl their official docs, store snapshots under
`{vault_location}/research/platforms/<platform>/`, diff against the prior snapshot,
and update `.gald3r/PLATFORM_STATUS.md`.

Intended for the routine "refresh anything stale" sweep. For a focused per-platform
scan use `@g-platform-scan-docs <name>` instead. For a forced refresh of every
platform (regardless of freshness window) use the `-SCAN_ALL` flag.

## Delegates To

- Script: `custom_scripts/scan_platform_docs.ps1`
- Skill: `g-skl-platform-monitor` → `SCAN_DOCS`
- Agent: `g-agnt-platformer`

## Workflow

1. Activate `g-agnt-platformer`.
2. Run `pwsh -NoProfile -File custom_scripts/scan_platform_docs.ps1 -StaleOnly`.
3. For each stale platform the script crawls its `docs_url:`, diffs against the
   previous snapshot in `{vault_location}/research/platforms/<platform>/`, surfaces
   changed sections, and writes the new `last_doc_scan:` date.
4. After the sweep, regenerate `.gald3r/PLATFORM_STATUS.md` so the
   `Last Doc Scan` column reflects the new state.
5. If any platform shows material changes, follow with
   `@g-platform-scan-docs <name>` for that platform, then
   `g-skl-platform-monitor UPGRADE <name>` to produce a human-review proposal
   (never auto-applied).

## Usage Examples

```
@g-platform-scan                        # routine: scan only platforms past their crawl window
@g-platform-scan -SCAN_ALL              # force refresh every platform
```

## Acceptance / Verification

- Running `@g-platform-scan` in a session surfaces stale platforms (`Stale: N` summary).
- `.gald3r/PLATFORM_STATUS.md` `Last Doc Scan` column is updated for scanned platforms.
- The session-start Platform Doc Staleness Check (g-rl-25 Step 9b) reports `0` overdue
  on the very next session.

## Related

- **g-rl-25 Step 9b** — session-start staleness alert that points here
- **g-skl-medic L1-J Platform Doc Freshness** — reports the same staleness signal as part of L1 triage
- `@g-platform-scan-docs <name>` — per-platform focused scan
- `@g-platform-status` — render the PLATFORM_STATUS.md table
- `@g-platform-check` — capability matrix sanity check

> **Origin**: created by T1520 (platform staleness gate).
