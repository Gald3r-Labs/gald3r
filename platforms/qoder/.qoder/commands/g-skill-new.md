---
description: 'Scaffold a new SKILL.md for your project in a chosen platform folder or custom repo path.'
subsystem_memberships: [PROJECT_IDENTITY_SETUP]
execution_tier: orchestration
---
# g-skill-new - Scaffold a new skill in YOUR project

Creates a new skill for your own project. You choose where it lives - your AI platform folder
(e.g. `.cursor/skills/`, `.claude/skills/`) or somewhere in your repo's own contents. This never
writes to `.gald3r_sys/` (the gald3r framework payload is read-only to your project).

## Usage

```
@g-skill-new <name>
@g-skill-new "my-feature"
```

- `<name>` - slug for the skill (e.g. `my-feature`).

## Steps

1. Ask **where** to create it:
   - **(a) Platform folder** - your chosen IDE: `.cursor/skills/<name>/SKILL.md`,
     `.claude/skills/<name>/SKILL.md`, etc. (pick one or more installed platforms).
   - **(b) Repo contents** - a path inside your own project source you specify.
2. Collect a one-line description and trigger phrases.
3. Write `SKILL.md` from the template at the chosen location. The preamble - immediately
   after the YAML frontmatter, before any other body content - MUST include the standard
   HELP CONTRACT block below, quoted verbatim (T442):

   ```
   ## HELP CONTRACT (T442 — cross-platform, non-substitutable)

   If the invoking command's arguments are EXACTLY `-h`, `--help`, or `help` (one
   token, nothing else): do NOT run any operation of this skill. Respond ONLY with a
   compact usage card — the command's name, its one-line purpose, each documented
   argument/option on its own line (or "none"), and the path to its command file —
   then STOP. Read-only: no `.gald3r/` writes, no state changes, no task/bug
   creation. This block lives in the SKILL (not a rule) because skills are the
   execution layer on every supported platform; rules are optional context on most.
   ```

   Every newly scaffolded `SKILL.md` inherits this block so `-h`/`--help`/`help` interception
   works cross-platform without depending on a rules surface (not every platform has one).
4. Offer a CHANGELOG entry if your project keeps one.
