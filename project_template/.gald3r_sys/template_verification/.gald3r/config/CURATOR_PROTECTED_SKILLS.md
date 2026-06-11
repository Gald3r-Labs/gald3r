---
gald3r_rel_version: "2.0.1"
schema_version: "generic-v1"
---
# Curator Protected Skills

Skills listed here are graded but the Curator MUST NOT propose them for archive, merge,
or prune.

These are framework-critical skills whose stability is more important than rubric
scores. They appear in the audit log's ranked skill list with the `[PROTECTED]` marker.

The Curator re-reads this file at the start of every run.

## Protected (do not modify or merge)

- g-skl-tasks
- g-skl-bugs
- g-skl-features
- g-skl-prds
- g-skl-plan
- g-skl-project
- g-skl-subsystems
- g-skl-constraints
- g-skl-medic
- g-skl-setup
- g-skl-curator
- g-skl-git-commit
- g-skl-workspace
- g-skl-test
- g-skl-verify-ladder
- g-skl-wpac-*
- g-skl-platform-*
- g-skl-cli-*
- g-skl-status
- g-skl-release
- g-skl-learn
- g-skl-memory

## Pattern matching

Entries ending in `*` are wildcard patterns. They match all skills whose name begins
with the prefix (e.g. `g-skl-wpac-*` matches `g-skl-wpac-adopt`, `g-skl-wpac-spawn`,
etc.). Wildcards are evaluated at the end of the name only — interior wildcards are
not supported.

## How to add a skill to this list

Append a new bullet under "Protected (do not modify or merge)". Optionally add a
trailing `# pinned because <reason>` comment so future maintainers understand the pin
rationale.

```markdown
- g-skl-foo  # pinned because used by every session-start hook
```

## How to remove a skill from this list

Delete the bullet. The Curator will resume normal grading on its next run; if the
skill scores low it may surface as `archive_candidate` or `merge_candidate`. Removal
should be a deliberate decision — the Curator never edits this file.

## Why pin a skill?

- The skill is referenced from always-apply rules (`g-rl-*-always*`) and any drift
  would destabilise session start.
- The skill owns a shared file (TASKS.md, BUGS.md, etc.) and merging it would create
  ownership ambiguity.
- The skill is new (less than 30 days old) and should not be archived for low
  invocation count alone.
- The skill ships in the gald3r install template and parity must be preserved.

## See Also

- `.claude/skills/g-skl-curator/SKILL.md` — Curator scope and operation
- `.claude/skills/g-skl-curator/reference/curator_rubric.md` — full scoring rubric
- `.claude/commands/g-curator.md` — manual trigger command
