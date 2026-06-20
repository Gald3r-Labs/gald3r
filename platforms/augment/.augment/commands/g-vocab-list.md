---
subsystem_memberships: [MEMORY_AND_KNOWLEDGE]
---
# g-vocab-list

Display all active abbreviations from `.gald3r/vocab.md`.

## Usage

```
@g-vocab-list
@g-vocab-list "CRASH"    # show definition for a specific abbreviation
```

## Output Format

Renders the full `## Active Vocabulary` table from `vocab.md`, plus the command group
convention table. If a term is provided, shows only matching rows (see `@g-vocab-search`).
