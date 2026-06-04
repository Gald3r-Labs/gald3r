# GitHub Summary Templates

Use these templates when tracked repos or gists are mirrored into `repos_location` and summarized into the vault.

## Storage Split

- Raw downloads live in `repos_location`
- Curated notes live in `research/github/`
- Never ingest raw upstream markdown from the mirrored repo into the vault

## Repo Profile Note

Use for first-time ingest or a major re-baseline.

```markdown
---
date: YYYY-MM-DD
type: github_repo
ingestion_type: github_sync
source: https://github.com/owner/repo
title: "owner/repo"
topics: [tag1, tag2]
refresh_policy: weekly
source_volatility: high
last_version: vX.Y.Z
last_synced: YYYY-MM-DDTHH:MM:SSZ
project_id: null
---
# owner/repo

## Overview
One-paragraph summary of what the repo is and why it matters.

## Key Details
- Language:
- Category:
- Stars:
- Forks:
- Open issues:

## What This Repo Does
Short operational description.

## Why We Track It
Specific reason this repo belongs in gald3r knowledge.

## Related
- [[knowledge/entities/owner__repo]]
- [[knowledge/concepts/repo-tracking]]
```

## Repo Update Note Block

Append into the existing repo note when the tracked version changes.

```markdown
## Update History

### vX.Y.Z (YYYY-MM-DD)
- Previous: vA.B.C
- Impact: 1-3 bullets describing meaningful change
- Follow-up: whether gald3r docs, skills, or tooling should change
```

## Ingestion Workflow

1. Read `.gald3r/repos.txt`
2. Mirror the raw repo or gist into `repos_location`
3. Update `.gald3r/repo_tracker.json`
4. Run AI or heuristic classification
5. Create or refresh the curated note in `research/github/`
6. Append a `repo-sync` entry to `log.md`
7. Rebuild `_index.yaml` and `index.md`
