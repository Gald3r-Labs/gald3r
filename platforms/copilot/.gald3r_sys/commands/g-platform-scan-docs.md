---
subsystem_memberships: [PLATFORM_INTEGRATION]
---
Scan a platform's official docs for breaking changes: $ARGUMENTS

## What This Command Does

Crawls the official documentation of the named platform and diffs against the last crawl,
surfacing sections that changed since the previous scan so they can be reviewed for gald3r
compatibility impact. Delegates to `g-skl-platform-monitor` operation `SCAN_DOCS`.

## Delegates To

- Skill: `g-skl-platform-monitor` → `SCAN_DOCS`
- Crawl: `g-skl-crawl` / `g-skl-recon-docs` on the platform's `docs_url:`
- Agent: `g-agnt-platformer`

## Workflow

1. Activate `g-agnt-platformer`.
2. Read `docs_url:` from `g-skl-platform-<platform>/SKILL.md` frontmatter.
3. Run `g-skl-platform-monitor SCAN_DOCS <platform>` — crawls the URL, stores results under
   `{vault_location}/research/platforms/<platform>/`, diffs against the prior snapshot.
4. Surface changed sections; update `last_doc_scan` in `.gald3r/PLATFORM_STATUS.md`.
5. If changes are material, follow with `g-skl-platform-monitor UPGRADE <platform>` to produce a
   human-review proposal (never auto-applied).

## Usage Examples

```
@g-platform-scan-docs antigravity     # high-priority: relaunched with breaking changes
@g-platform-scan-docs cursor
```

> **Status (T1460):** scaffolding. The crawl/diff wiring is defined; per-platform diff heuristics
> are completed by T1461–T1483.
