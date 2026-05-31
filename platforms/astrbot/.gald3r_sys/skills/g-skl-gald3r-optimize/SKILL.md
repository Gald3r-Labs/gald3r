---
name: g-skl-gald3r-optimize
description: ROOT-ONLY gald3r_dev maintainer tooling. Audits gald3r system files (skills, rules, agents, commands) for bloat — oversized SKILL.md files, overgrown rationalization tables, near-identical enforcement messages, redundant agent Background/Context sections, back-reference filler, and duplicate acceptance criteria — and produces a ranked pruning report with specific suggested edits. AUDIT/PREVIEW are read-only; APPLY prunes only after explicit per-file confirmation. Sibling of g-skl-compress-memory (T1053). Not shipped to external templates.
token_budget: low
skill_trust_level: core
allowed-tools: [Read, Edit, Bash]
subsystem_memberships: [PROJECT_IDENTITY_SETUP, AGENT_ORCHESTRATION]
---
# g-skl-gald3r-optimize

gald3r system files (`.gald3r_sys/skills/*/SKILL.md`, `.gald3r_sys/rules/g-rl-*.md`,
`.gald3r_sys/agents/*.md`, `.gald3r_sys/commands/*.md`) accumulate bloat over time: rationalization
tables grow to a dozen rows, the same enforcement message is restated three different ways, agents
sprout multiple `## Background` sections, and SKILL.md files blow past their line budget. Every extra
line burns context tokens on every session. This skill **audits** that corpus, scores each file for
bloat, and proposes specific removals — then prunes only files you explicitly confirm.

It is the framework-corpus counterpart to **g-skl-compress-memory** (T1053): same
"preserve-always, dry-run-first" philosophy, but it targets the gald3r system/config files instead
of memory files (`AGENTS.md`/`CLAUDE.md`).

## ROOT-ONLY maintainer tooling
This skill and its `g-gald3r-optimize` command are **gald3r_dev controller-only**. They live under
`.gald3r_sys/` but are registered in `custom_scripts/root_only_manifest.yaml` with
`gald3r_sys_root_only: true`, so the parity sync **never** propagates them to the external
`gald3r_template_{slim,full,adv}` repos. Installed projects do not get this skill. Do not run it
against an installed project's `.gald3r_sys/` expecting deployment.

## Hard constraint — PRESERVE-ALWAYS
The audit and APPLY paths **never** flag or remove any of the following. These are the spine of the
framework and must survive compression untouched:

| Always preserved |
|---|
| Fenced code blocks (verbatim) |
| Command syntax lines (`@g-*`, `/g-*`) |
| Acceptance-criteria bodies |
| Hard rules / `HARD RULE` / `MANDATORY` / `MUST NOT` / `NEVER` blocks (enforcement logic) |
| YAML frontmatter |
| URLs (verbatim) |

A suggested removal is only ever a redundant *prose* line — never logic, never syntax.

## Bloat-signal heuristics and weights
The bloat score per file is a weighted sum of detected signals. Weights are documented here and in
the script header (`$Weights`):

| Signal | Trigger | Weight | Auto-removable? |
|---|---|--:|---|
| `rationalization_table_overflow` | a `\| Rationalization \| Reality \|` table with **>5 rows** | 3 | yes — suggests dropping rows past the first 3 |
| `skill_over_400_lines` | a `SKILL.md` longer than **400 lines** | 4 | no — flag for manual review (move reference content to `reference/`) |
| `near_identical_enforcement` | a rule file with **>3 near-identical** enforcement lines (normalized signature match) | 3 | yes — suggests dropping the duplicates |
| `multiple_background_sections` | an agent file with **>2** `## Background` / `## Context` headings | 2 | yes — suggests consolidating to one |
| `backref_filler` | a line starting "As mentioned above…" / "As noted in…" | 1 each | yes |
| `duplicate_acceptance_criteria` | the same acceptance criterion appears across two files in one subsystem | 2 | no — reported only (criteria are PRESERVE-always) |

**Why these weights:** SKILL.md overflow (4) is the single biggest context-tax and weighed highest;
table overflow and enforcement duplication (3) are the most common high-volume noise; agent section
duplication (2) is structural; back-reference filler (1) is cheap noise. Higher score ⇒ higher
priority for review.

## Operations

### AUDIT (default, read-only — never writes)
```
pwsh -File .gald3r_sys/skills/g-skl-gald3r-optimize/scripts/gald3r_optimize.ps1 -Mode AUDIT -Path <file-or-dir>
# default -Path (omitted) = .gald3r_sys/{skills,rules,agents,commands}
# -Json for machine-readable output; -Top N to size the suggested-removals list (default 10)
```
Scans the targets, computes a bloat score per file, and prints:
- **Files ranked by bloat score** (highest first) with the detected signals per file.
- **Top N suggested removals** across all files (weight-sorted), each with file, line, reason, and
  the literal text to be removed.

No writes. This is the safe default when `-Mode` is omitted.

### PREVIEW (read-only — shows per-file diffs)
```
pwsh -File .../gald3r_optimize.ps1 -Mode PREVIEW -Path <file-or-dir>
```
Shows, per file, every line the tool would remove (the proposed diff). No writes. Use this to review
a single file's full removal set before applying.

### APPLY (writes — per-file confirmation only, NEVER bulk)
```
pwsh -File .../gald3r_optimize.ps1 -Mode APPLY -Path <single-file> -Confirm
```
- Operates on **exactly one file** at a time. A directory `-Path` is refused.
- **Requires `-Confirm`.** Without it, no write happens.
- Prints the exact removals first, then prunes only the auto-removable suggestions (preserving all
  PRESERVE-always content), and writes the file.
- Flag-only signals (e.g. `skill_over_400_lines`) are never auto-applied — they need a human's
  editorial judgement to move content into `reference/`.

## Workflow (safe sequence)
1. **AUDIT** the corpus (or a subdir) → get the ranked bloat list and top removals.
2. Pick the worst-offending file; **PREVIEW** it to see the full proposed diff.
3. For files whose removals are purely redundant prose → **APPLY** that single file with `-Confirm`.
4. For `skill_over_400_lines` flags → manually relocate encyclopedic content to a `reference/`
   subdirectory (per the SKILL.md line-budget guidance) rather than auto-pruning.
5. Re-AUDIT to confirm the score dropped.

## Boundaries
- Dry-run (AUDIT) by default; only `-Mode APPLY -Path <single file> -Confirm` writes.
- Never removes code blocks, command syntax, acceptance criteria, hard rules, frontmatter, or URLs.
- Per-file only — there is no bulk-apply path by design.
- Advisory tool: it proposes; the maintainer decides. `duplicate_acceptance_criteria` is reported,
  never auto-cut.
- gald3r_dev controller-only; not propagated to installable templates.

Command: `@g-gald3r-optimize`. Helper:
`.gald3r_sys/skills/g-skl-gald3r-optimize/scripts/gald3r_optimize.ps1`. Source task: T1054.
Sibling: g-skl-compress-memory (T1053).
