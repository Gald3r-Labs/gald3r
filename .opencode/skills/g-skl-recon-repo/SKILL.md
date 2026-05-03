---
name: g-skl-recon-repo
description: Capture a GitHub repository into the vault as a structured summary note. Produces research/repos/ notes and _index.yaml. Optional --deep flag triggers full g-skl-res-deep analysis pass.
---
# g-recon-repo

**Activate for**: "capture this repo", "save repo to vault", "summarize this GitHub project", "recon repo", "add repository to knowledge base", `@g-recon-repo`

---

## Purpose

Quickly capture a GitHub repository as an Obsidian-compatible vault note in `research/repos/`. Unlike `g-skl-res-deep` (which runs a full 5-pass analysis), this skill produces a lightweight summary note optimized for vault browsing and quick reference.

Optionally, pass `--deep` to run `g-skl-res-deep` after capture and produce a full recon report in `vault/research/recon/{slug}/`.

---

## Clean Room Boundary

This capture skill may store source material in the vault for research, provenance, and later review. When captured content is used for `--deep`, `g-skl-res-deep`, or any adoption workflow, downstream outputs must be clean-room reverse specs: behavior-level summaries, interfaces, workflows, data shapes, constraints, and architectural patterns only. Do not copy source code, comments, docs prose, prompts, tests, or unique strings into generated gald3r artifacts except tiny attributed excerpts that are license-compatible and necessary for review. Record source URL/path, license when discoverable, capture date, and extraction limits so reviewers can separate source evidence from original gald3r specifications.

---

## Operation: CAPTURE

```
@g-recon-repo https://github.com/owner/repo
@g-recon-repo https://github.com/owner/repo --deep
@g-recon-repo https://github.com/owner/repo --title "Custom Title" --topics "ai,agents"
```

### Steps

1. **Read key files**: README.md, package.json / pyproject.toml / Cargo.toml / go.mod, LICENSE, primary source files (max 20). Summarize behavior and structure; do not preserve source snippets beyond tiny attributed, license-compatible excerpts.
2. **Extract**: purpose, tech stack, architecture, notable patterns, license, activity level
3. **Write vault note** to `research/repos/{owner}__{repo}.md` with Obsidian frontmatter:
   ```yaml
   ---
   title: "{repo title}"
   date: YYYY-MM-DD
   type: repo_capture
   ingestion_type: manual
   source: https://github.com/owner/repo
   topics: [inferred]
   tags: [repo, {language}, {domain}]
   owner: owner
   repo: repo
   license: MIT / Apache-2.0 / etc
   stars: N (if available)
   ---
   ```
4. **Register** in `research/repos/_index.yaml`
5. **Append** to `vault/log.md` per C-006
6. **If --deep**: activate `g-skl-res-deep ANALYZE` on the captured repo

### Dedup check

- Check `research/repos/_index.yaml` for existing entry with same `source`
- If found and age < 30 days → skip unless `--force`
- If found and age ≥ 30 days → re-capture (update existing note in-place)

---

## Vault Note Format

```markdown
---
[frontmatter as above]
---

# {Repo Title}

> {one-line description from README or package.json description field}

## Tech Stack
- Language: Python 3.11 / TypeScript / Rust / etc.
- Framework: FastAPI / Next.js / etc.
- Key deps: {top 5-8 from package file}

## Architecture
{2-3 sentence summary of project structure}

## Notable Patterns
- {pattern 1}
- {pattern 2}

## License
{license name} — {permissive/copyleft/proprietary}

## Links
- Repo: https://github.com/owner/repo
- [[research/repos/_index]] — back to index
```

---

## Output Path

`{vault_location}/research/repos/{owner}__{repo}.md`
(vault_location from `.gald3r/.identity`)

---

## See Also

- `@g-res-deep` — Full 5-pass deep analysis (5-10x more thorough)
- `@g-res-review` — Review existing recon reports
- `@g-res-apply` — Apply approved features to `.gald3r/`
