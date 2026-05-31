---
description: Comprehensive gald3r code review of the current change
argument-hint: [file or directory]
---

# gald3r Code Review

Perform a comprehensive code review against gald3r standards:

1. Read the file(s) fully before reviewing — not just the changed lines.
2. Check: correctness, security (no secrets/injection), DRY (3-strike rule),
   convention conformance, and surgical scope (no unrelated refactors).
3. Flag any pre-existing bug found with a `BUG[BUG-{id}]` annotation and a `.gald3r/BUGS.md` entry.
4. Flag any stub/TODO without a `TODO[TASK-X->TASK-Y]` forward link.
5. Report findings by severity; do not auto-fix unless asked.

Target: $ARGUMENTS
