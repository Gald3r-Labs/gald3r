---
subsystem_memberships: [PROJECT_IDENTITY_SETUP]
---
# Hook: g-hk-component-tag-check

## Fires On
Git `pre-commit` event. Inspects every staged file under `.gald3r_sys/` at commit time.
Not auto-wired to `hooks.json` — activated via `git config core.hooksPath`.
See setup instructions below.

## What It Does
Scans staged `.md` files in `skills/`, `commands/`, `agents/`, `rules/` for a
`subsystem_memberships:` YAML frontmatter field, and staged `.ps1` files in
`hooks/`, `scripts/` for a `# @subsystems:` comment in the first 15 lines.
Blocks the commit (exit 1) if any staged file is missing its tag. Prints the
violation list and the valid group names.

## Side Effects
- No files written, no state changed — read-only scan
- Exits 0 (allow) on clean or non-.gald3r_sys files
- Exits 1 (block) on any untagged `.gald3r_sys` component file

## Setup (one-time per repo clone)

```powershell
# Create a git-hooks wrapper directory and link the hook
$gitHooksDir = ".gald3r_sys\git-hooks"
New-Item -ItemType Directory -Path $gitHooksDir -Force | Out-Null

# Write a thin pre-commit caller (no .ps1 extension — git expects bare filename)
Set-Content "$gitHooksDir\pre-commit" @'
#!/bin/sh
python ".cursor/hooks/g-hk-component-tag-check.py"
'@

# Register with git
git config core.hooksPath .gald3r_sys/git-hooks
```

Run setup once; it persists in `.git/config`. After that every `git commit` runs the tag check.

## Related Tasks
- T1458 — subsystem sprawl prevention enforcement
- T1459 — aggregate_subsystems.ps1 aggregation script
- Rule: `g-rl-38` — component creation standards (always-applied)
- Commands: `@g-skill-new` / `@g-command-new` / `@g-rule-new` / `@g-create-hook` / `@g-agent-hire` — scaffold correctly-tagged components
