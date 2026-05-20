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
   - **missing frontmatter (T1334)** — run `frontmatter_fix.ps1` (dry-run) and flag any
     long-lived note lacking a `---` block: `⚠️ missing frontmatter: <relpath> — run @g-vault-frontmatter-fix`
4. Write a concise report
5. Append a `lint` entry to `log.md`

**Flag**: `--auto-fix <file>` → invoke `frontmatter_fix.ps1 -File <file> -Apply` (backup-first)
to retrofit one file's frontmatter, then re-lint.
