---
subsystem_memberships: [MEMORY_AND_KNOWLEDGE]
---
# g-vocab-search

Find matching abbreviations or conventions in `.gald3r/vocab.md`.

## Usage

```
@g-vocab-search "term"
@g-vocab-search "platform"   # matches CRASH (expansion mentions platform folders)
```

## What It Does

1. Reads `.gald3r/vocab.md`
2. Case-insensitive substring match of `term` against each row's Abbreviation, Expansion,
   and Context columns (both the `## Active Vocabulary` and the convention tables)
3. Prints matching rows; if none match, reports `No vocab entry matches "term"`

## Behavior Rules

- Read-only — never modifies `vocab.md` (use `@g-vocab-add` to add/update)
- Matching is case-insensitive
- The vocab file `.gald3r/vocab.md` is always the source of truth
