# g-recon-repo

Capture a GitHub repository into the vault as a structured summary note.

Activates **g-skl-recon-repo** → CAPTURE operation.

## Usage

```
@g-recon-repo https://github.com/owner/repo
@g-recon-repo https://github.com/owner/repo --deep   # capture + deep feature analysis
```

## What it does

1. Reads key repo files (README, package.json/pyproject.toml/Cargo.toml, key source files)
2. Extracts: purpose, tech stack, architecture, notable patterns, license
3. Writes vault note to `research/repos/{owner}__{repo}.md`
4. Updates `vault/research/repos/_index.yaml`
5. Updates `vault/log.md`

## --deep flag

After capturing, runs a deep analysis pass (5-pass strategy from `g-res-deep`) and writes a
full recon report to `vault/research/recon/{slug}/04_FEATURES.md` and supporting docs.
Equivalent to running `@g-res-deep` after capture.

## Notes

- Uses existing `repos_location` mirrors when available; falls back to GitHub web scraping
- Produces a lightweight summary note — for full feature harvesting, use `@g-recon-repo --deep`
- Output in `research/repos/` follows Obsidian vault standard (frontmatter, tags, wikilinks)

## See Also

- `@g-res-deep` — Full deep analysis of a captured repo (5-pass strategy)
- `@g-res-review` — Review existing recon reports for adoption decisions
- `@g-res-apply` — Apply approved features from a recon report to .gald3r/
