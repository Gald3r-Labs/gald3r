# Parity Exclusion List

Files and directories listed here are **intentionally local** to specific projects
and MUST be skipped during platform parity audits (Step 4 of g-cleanup).

These are NOT parity violations — they are opt-in, project-specific customizations.

## Excluded from Parity Audit

### Personality Rules (only one active per project)
- `rules/silicon_valley_personality.mdc` / `.md`
- `rules/norse_personality.mdc` / `.md`

### Fandom / Project-Specific Skills
- `skills/silicon-valley-superfan/`

## How It Works

- gald3r ships `norse_personality` as the default personality rule
- Projects may swap in `silicon_valley_personality` (or any other) instead
- The personality rule and its companion skill are gitignored in the gald3r source repo
- `gald3r_install` does NOT deploy personality rules — they are manually added per-project
- The parity audit in `g-cleanup` MUST check this file before flagging missing files
