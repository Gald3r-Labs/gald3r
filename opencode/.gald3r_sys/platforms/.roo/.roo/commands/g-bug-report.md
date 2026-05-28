---
description: Report a gald3r bug (BUGS.md entry + bug detail file)
argument-hint: <bug title / observed behavior>
---

# gald3r Bug Report

Log a bug into the gald3r bug tracker:

1. Determine the next sequential bug ID from `.gald3r/BUGS.md` and `.gald3r/bugs/`.
2. Add a `### BUG-{id}` entry to `.gald3r/BUGS.md` with Title, Severity, Status (Open),
   File (path + line if known), Note, and Created date.
3. Optionally create a detail file at `.gald3r/bugs/bug{id}_{slug}.md` with a `kind:`
   classification (`code` | `spec_defect` | `policy_incongruity` | `design_gap`).
4. Never silently ignore a discovered defect.

Bug: $ARGUMENTS
