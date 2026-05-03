---
name: g-skl-res-review
description: Analyze external sources (GitHub repos, URLs) for adoptable patterns and improvements. Vault-aware — reads from {vault}/research/recon/ when a shared vault is configured, else falls back to local research/harvests/. Uses _recon_index.yaml for cross-project dedup. Produces structured harvest reports and optional IDEA_BOARD suggestions. Zero-change-without-approval.
---
# g-skl-res-review

**Vault output** (vault-aware, T081): `{vault}/research/recon/` when `vault_location` ≠ `{LOCAL}`, else `research/harvests/`.

**Activate for**: "harvest ideas from", "analyze this repo for patterns", "what can we learn from", "review past harvests", any request to borrow ideas from external sources.

---

## Principle

> Analyze external sources. Present selective improvement suggestions.
> **User approves what to adopt — nothing changes without approval.**

Review is NOT vault ingestion (that stores knowledge for RAG). It is specifically about looking *outward* at other codebases and articles to find patterns worth borrowing. It writes vault notes and suggests IDEA_BOARD entries. It never modifies project code, configs, or skills.

---

## Clean Room Review Gate

Before marking a recon feature `[✅]`, reviewers must confirm the feature is expressed as behavior/specification, not copied implementation. Check that source references are provenance only, license is recorded or marked unknown, and no source code, docs prose, prompts, tests, or unique strings are being approved for direct reuse. If the suggestion depends on implementation details that cannot be cleanly rephrased, mark it `[🔍] needs-review` or `[⏸] defer` instead of approving it.

---

## Vault-Aware Output Path (T081)

Every operation resolves the output base path before doing anything else.

### Path resolution (per C-003)

```
1. Read .gald3r/.identity (key=value, no quotes)
2. Extract vault_location=
3. If vault_location is {LOCAL} or missing:
     recon_base  = "research/harvests/"
     index_path  = "research/harvests/_recon_index.yaml"
     vault_mode  = "local"
4. Else:
     recon_base  = f"{vault_location}/research/recon/"
     index_path  = f"{vault_location}/research/recon/_recon_index.yaml"
     vault_mode  = "shared"
```

### Dedup pre-flight

Before running any HARVEST_REPO or HARVEST_URL pass, consult `_recon_index.yaml`:

```
1. Resolve index_path
2. If file does not exist → continue (will be created by g-skl-res-deep or this skill on first write)
3. If exists: parse YAML, match by slug OR source_url
4. If match found and (today - last_run) <= max_age_days (default 30):
     print "[CACHED: {slug}] — report at {output_path}, last run {last_run}"
     surface existing suggestions for adoption; skip re-harvest
5. Else: proceed with harvest; write/update entry on completion
```

`--max-age-days N` overrides the staleness threshold (default 30). `--force` skips dedup entirely.

See `g-skl-res-deep` for the full `_recon_index.yaml` schema.

---

## Operation: HARVEST_REPO

Analyze a GitHub repository for adoptable patterns.

**Step 1 — Resolve repo**:
- Check `.gald3r/.identity` for `repos_location`
- If `repos_location` is set, look for the repo under that path
- If not mirrored: inform the user and offer to add to `repos.txt` via `g-skl-vault` GitHub Repo flow, then re-run after sync

**Step 2 — Resolve vault-aware output path + dedup check** (see Vault-Aware Output Path). If cached, surface and stop.

**Step 3 — Read key files** (no binary files, no node_modules, no .git):
- `README.md` and top-level docs
- Skill/command/rule/hook files (`.cursor/`, `.claude/`, etc.)
- Config files (`pyproject.toml`, `package.json`, `CONSTRAINTS.md`, etc.)

**Step 4 — Generate structured harvest report**:
For each notable pattern found, produce:
- What the pattern is
- Where it appears in the source (file reference)
- Why it's worth considering
- Complexity estimate: `low` (add a file/field) | `medium` (new subsystem) | `high` (multi-task refactor)
- A draft IDEA_BOARD entry

**Step 5 — Write harvest note** to `{recon_base}{YYYY-MM-DD}_{slug}.md` (flat file for review-style harvests) or `{recon_base}{slug}/REVIEW.md` (structured folder when promoting to deep recon). Include Obsidian-standard frontmatter (T044, T081 AC-8):

```yaml
---
date: YYYY-MM-DD
type: recon
ingestion_type: review_harvest
source: https://github.com/owner/repo
title: "Review: owner/repo"
tags: [recon, review]
harvest_status: reviewed       # reviewed | partially_adopted | fully_adopted
suggestions_total: 5
suggestions_adopted: 0
---
```

**Step 6 — For each suggestion**, ask:
> "Add to feature staging or IDEA_BOARD? (feature/idea/skip)".

- `feature` → calls `g-skl-features COLLECT` on a matching staging feature (fuzzy match ≥70%) OR `g-skl-features STAGE` to create a new staging doc
- `idea` → posts to IDEA_BOARD via `g-skl-ideas CAPTURE`
- `skip` → log as skipped; available in HARVEST_REVIEW later

**Step 7 — Finalize dedup entry** in `_recon_index.yaml`:
```yaml
- slug: {slug}
  source_url: {url}
  title: "Review: {project name}"
  last_run: {YYYY-MM-DD}
  status: complete
  output_path: {relative_output_path}
```

**Step 8 — Log**: append to `{vault}/log.md` (or `research/log.md`):
```
| {YYYY-MM-DD} | review-harvest | {slug} | g-skl-res-review (suggestions={N}) |
```

---

## Operation: APPLY

```
APPLY {harvest_slug_or_path}
APPLY --dry-run {harvest_slug_or_path}
```

Converts approved harvest suggestions into feature staging documents.

For each approved suggestion:

1. **Fuzzy-match against existing staging features** in `.gald3r/features/` by title/description similarity ≥70%:
   - Match found → call `g-skl-features COLLECT`
   - No match → call `g-skl-features STAGE` then COLLECT
2. **Prompt on fuzzy matches**: `"This looks like feat-NNN '{{title}}' — add as approach? [y/n]"`
3. **harvest_sources dedup**: once a source path is in `harvest_sources:` of a feature YAML → skip re-harvesting same source for that feature
4. **--dry-run mode**: print planned COLLECT/STAGE operations without writing

**Hard rule**: APPLY NEVER creates TASKS.md entries. Feature → tasks is triggered only by `/g-feat-promote`.

---

## Operation: HARVEST_URL

Analyze a URL for architectural decisions, tooling choices, and workflow patterns.

**Step 1 — Crawl** the URL using `g-skl-crawl` FETCH.
**Step 2 — Extract** from the crawled Markdown.
**Step 3 — Same vault-aware path + dedup + report + APPLY/IDEA_BOARD flow as HARVEST_REPO.**

Note: URL harvest is about idea extraction, not content storage. If you also want to store the content, run `@g-ingest-url` separately.

---

## Operation: HARVEST_REVIEW

Review past harvest notes and surface unadopted suggestions.

1. Scan `{recon_base}` (vault-aware) for notes where `harvest_status: reviewed` (not `fully_adopted`)
2. For each unadopted suggestion, present:
   - Source: `{title}` from `{date}`
   - Suggestion text + complexity
   - Current IDEA_BOARD status
3. User can: promote to IDEA_BOARD, shelve, or dismiss each

---

## Harvest Note Schema (Obsidian-compliant, T081 AC-8)

```yaml
---
date: 2026-04-21
type: recon
ingestion_type: review_harvest
source: https://github.com/owner/repo
title: "Review: owner/repo"
tags: [recon, review]
harvest_status: reviewed       # reviewed | partially_adopted | fully_adopted
suggestions_total: 5
suggestions_adopted: 0
---

## Source Overview
{1-2 sentences: what was analyzed and why}

## Suggestions

### 1. {Suggestion Title} [complexity: low]
**Pattern found in**: `path/to/file.md`
**What it does**: ...
**Why adopt**: ...
**IDEA_BOARD status**: pending | posted as IDEA-042 | shelved
```

### Note on `tags:` vs `topics:`

Use **`tags:`** (Obsidian's native field, C-002). Historical notes may still carry `topics:` — the migration in T039 converted 510+ notes. New writes must use `tags:` only.

---

## GitHub Repo Coordination

When `@g-res-review {github_url}` targets an unmirrored repo:

1. Check `repos_location` from `.gald3r/.identity`
2. If `repos_location` is set but repo not found:
   - Suggest: "Add `{github_url}` to `{repos_location}/repos.txt` and run `@g-vault-ingest` to mirror it, then re-run review"
3. If `repos_location` is not set:
   - Suggest using HARVEST_URL instead

---

## Hard Constraints

- **Never modify project code, configs, or skills** — review only writes vault notes, IDEA_BOARD entries, and feature staging docs
- **Feature staging posting requires explicit user confirmation per suggestion** (or APPLY with a reviewed harvest) and clean-room approval
- **Review never creates tasks** — this skill only reviews and stages suggestions; task creation happens later via `g-res-apply APPLY` after clean-room approval or via `/g-feat-promote` for feature-staging flows
- **Zero scope creep** — if a suggestion would take >2 days to implement, mark complexity `high` and let the user decide whether to promote
- **Vault-first writes** (T081): when `vault_location` ≠ `{LOCAL}`, output goes to the shared vault to prevent duplicated work across projects
- **Dedup-first scans** (T081): always consult `_recon_index.yaml` before running a new review; respect `--max-age-days` (default 30)
- **No verbatim reuse** — review suggestions must not approve copied source code, docs prose, prompts, tests, or unique strings for direct reuse

---

## Topology-Aware Routing (T118)

When a PCAC topology is configured (`.gald3r/linking/link_topology.md` exists with `children:` entries), each suggestion in a harvest is assigned a **routing suggestion** before presenting to the user. This ensures findings reach the right project rather than all landing in the current project.

### Topology Load Sequence

```
1. Read .gald3r/linking/link_topology.md — get children[] list (name, path)
2. For each child, read .gald3r/linking/peers/{child_name}.md OR {child_path}/.gald3r/linking/capabilities.md
   - Fall back to peers/ snapshot if child is not locally accessible
3. Build peer_capabilities dict: { peer_name: [capability_name, ...] }
4. Also read current project's .gald3r/linking/capabilities.md
5. If no topology / no children: run in non-topology mode (routing column omitted)
```

### Routing Algorithm

For each finding `F` in the harvest report:

```
1. Extract domain tags from F.title + F.description
   Common domain tags: "frontend", "backend", "api", "auth", "ui", "database",
   "cli", "desktop", "mobile", "mcp", "vault", "agent", "llm", "comms", "ext"

2. Score each peer (including this project):
   - For each capability_name in peer_capabilities[peer]:
     score += count of domain_tags that appear in capability_name (case-insensitive)

3. Determine routing:
   - Score > 0 and single winner:   suggest "{peer_slug}"
   - Score > 0 and multiple tied:   suggest "multiple:{slug1},{slug2}"
   - Score == 0 for all peers:
     - If this-project owns a matching capability: suggest "this-project"
     - Otherwise: suggest "new-project" (explain what capability is missing)

4. "new-project" suggestion text: "⚡ No project owns [{domain}] — consider spawning a [{type}] project via @g-pcac-spawn"
```

### Display Format

Harvest report with topology routing adds a `Routing` column:

```
## Suggestions

| # | Finding | Complexity | Routing | Notes |
|---|---------|------------|---------|-------|
| 1 | Platform adapter pattern | Medium | → gald3r_valhalla | gald3r_valhalla owns communications subsystem |
| 2 | Fast Mode execution profile | Low | → this-project | gald3r_dev owns autonomous-coding capability |
| 3 | gRPC streaming transport | High | ⚡ new-project | No peer owns real-time-transport capability |
| 4 | iMessage gateway | Medium | → multiple:gald3r_valhalla,gald3r_agent | Both own relevant capabilities |
```

**User override**: user can manually change routing before APPLY by typing the target slug when prompted.

### Cross-Project APPLY

After reviewing routing suggestions, user confirms each routing. Then:

- `→ this-project`: standard APPLY (writes to current project)
- `→ {peer_slug}`: calls `g-skl-res-apply APPLY --target {peer_slug}`
- `⚡ new-project`: offers `@g-pcac-spawn {type}` with capability description
- `→ multiple:...`: prompts user to choose or split

### TOPOLOGY_STATUS Operation

```
@g-res-review TOPOLOGY_STATUS
```

Displays current topology awareness:
- Lists all known peers and their loaded capabilities
- Shows which capabilities are `ready` vs `planned`
- Shows `peers/` snapshot staleness (age in days; >7 days flagged)
- If no topology: prints `"No PCAC topology configured — run @g-pcac-adopt to link projects"`
