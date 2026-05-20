Lint the vault: $ARGUMENTS

## What This Command Does

Runs a structural and freshness audit of the vault.

## Workflow

1. Use `g-skl-knowledge-refresh`
2. Check freshness via `_index.yaml`
3. Check structure:
   - broken wikilinks
   - orphan pages
   - missing entities or concepts
   - duplicate or weak cards
   - contradictions needing review
4. Write a concise report
5. Append a `lint` entry to `log.md`
