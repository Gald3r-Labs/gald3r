Ingest or update vault content: $ARGUMENTS

## What This Command Does

Routes new knowledge into the file-first gald3r vault with Obsidian-safe wikilinks.

## Workflow

1. Use `g-skl-vault`
2. Resolve vault and repos paths
3. Decide between:
   - quick ingest: source note only
   - full ingest: source note plus compiled wiki pages
4. Write or update the relevant note
5. Append a `log.md` entry
6. Run `g-hk-vault-reindex.ps1`

## Special Case: GitHub Repos

If the source is a tracked repo or gist:

- raw mirror goes to `repos_location`
- curated summary note goes to `research/github/`
- do not ingest raw upstream markdown into the vault
