---
description: 'List all active abbreviations from .gald3r/vocab.md, or show one term''s definition'
argument-hint: '[term]'
subsystem_memberships: [MEMORY_AND_KNOWLEDGE]
execution_tier: orchestration
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
