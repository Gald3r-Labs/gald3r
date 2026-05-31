---
gald3r_rel_version: "1.6.0"
schema_version: "BUGS-md-v1"
---
<!--
  EXAMPLE ONLY — illustrative BUGS.md in current schema format.

  This is NOT a reset/restore source. To reset or restore a real BUGS.md:
    - run  pwsh -File .gald3r_sys/scripts/migrate_schemas.ps1 -ProjectPath <proj> -RestoreMissing -Apply
    - or copy  .gald3r_sys/template_verification/.gald3r/BUGS.md
  Never reconstruct BUGS.md from memory or from this example. See g-skl-bugs
  "Operation: RESET / RESTORE BUGS.md".
-->
# BUGS.md — Example Project Bug Tracker

## Status Indicators
<!-- DO NOT REMOVE THIS SECTION — agents depend on it for status parsing -->
- `[ ]` = Open (no bug file yet)
- `[📋]` = Documented (bug file created)
- `[🔄]` = Fix in progress
- `[🔍]` = Awaiting Verification
- `[🕵️]` = Verification In Progress
- `[✅]` = Resolved
- `[❌]` = Won't fix

## Bug Summary

| Status | ID | Bug | Severity | Subsystems |
|--------|----|-----|----------|------------|
| [✅] | BUG-001 | Login button not responding to clicks | Critical | AUTH |
| [🔄] | BUG-002 | Shopping cart total miscalculates discount | High | CART, CHECKOUT |
| [📋] | BUG-003 | Product images fail to load on mobile | Medium | CATALOG |

## Next Bug ID: BUG-004
