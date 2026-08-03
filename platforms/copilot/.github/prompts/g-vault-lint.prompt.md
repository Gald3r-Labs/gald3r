---
description: 'Audit the vault for freshness, broken wikilinks, orphan pages, and OKF-conformance via gald3r vault lint'
argument-hint: '[--auto-fix <file>]'
subsystem_memberships: [VAULT_AND_RESEARCH]
execution_tier: orchestration
---
Lint the vault: $ARGUMENTS

## What This Command Does

Runs a structural and freshness audit of the vault.

## Workflow

1. Use `g-skl-knowledge-refresh`
2. Check freshness via `_index.yaml`
3. Check structure:
   - broken wikilinks (`gald3r vault lint` — slug-tolerant resolution, T185)
   - orphan pages
   - missing entities or concepts
   - duplicate or weak cards
   - contradictions needing review
   - OKF-conformance (T185): frontmatter parses, `type:` non-empty, UTF-8 no BOM
     (folded into `gald3r vault lint`; see `g-skl-vault/SKILL.full.md` §4 Lint)
4. Write a concise report
5. Append a `lint` entry to `log.md`
