---
subsystem_memberships: [PROJECT_IDENTITY_SETUP]
---
# g-skl-subsystems

> Human-facing companion to `SKILL.md`. The LLM agent reads `SKILL.md`; this
> page is for developers browsing the skill library on GitHub.

## What it does

Owns the subsystem registry and the per-subsystem spec files. A subsystem is a coherent unit of code + state + lifecycle (e.g. `vault`, `platform-parity`, `gald3r_install`).

- `.gald3r/SUBSYSTEMS.md` — registry table + mermaid interconnection graph.
- `.gald3r/subsystems/<name>.md` — one spec file per subsystem with frontmatter, dependencies, locations (`code:`, `skills:`, `agents:`, `commands:`, `config:`, `db_tables:`), responsibility, data flow, architecture rules, and an Activity Log.

## When to use

- "add subsystem", "deprecate subsystem", "what subsystems exist"
- Before modifying any subsystem's code (read the spec first — this is mandatory per `g-rl-33`)
- After completing a task that affects a subsystem (append to its Activity Log)
- During `@g-setup` for first-time subsystem discovery

## Trigger phrases

```
@g-subsystem-add | @g-subsystem-upd | @g-subsystem-del | @g-subsystems
@g-subsystem-graph
```

## Classification

Not everything is a subsystem. Use this triage:

| Kind              | Has its own code? | Has its own state? | Has its own lifecycle? | Entry in SUBSYSTEMS.md? |
|-------------------|-------------------|---------------------|-------------------------|--------------------------|
| **Subsystem**     | yes               | yes                 | yes                     | top-level entry + spec file |
| **Sub-feature**   | shares parent     | shares parent       | shares parent           | documented inside parent spec |
| **Integration**   | external adapter  | external service    | n/a                     | listed under host subsystem |

## Examples

### Add a new subsystem

```
@g-subsystem-add platform-parity
```

Creates `.gald3r/subsystems/platform-parity.md` with the standard template, prompts you to fill in dependencies and locations, and adds a row + node to the SUBSYSTEMS.md mermaid graph.

### Update Activity Log on task completion

This skill auto-fires when `@g-task-upd` marks a task `completed` — it walks the task's `subsystems:` frontmatter list and appends one row per subsystem to that subsystem's Activity Log table.

### Sync check

```
@g-subsystems --sync-check
```

Reports drift: spec files missing `locations:`, tasks referencing subsystems with no spec, subsystems listed but with no spec file.

## File ownership boundary

Only this skill writes to:

- `.gald3r/SUBSYSTEMS.md`
- `.gald3r/subsystems/**/*.md`

## See also

- `g-skl-tasks` — calls into this skill to update Activity Logs
- `g-skl-bugs` — also appends to Activity Log on bug resolution
- `g-skl-infrastructure` — owns the rules about file organization that subsystems must respect
- `g-rl-33` — gate that requires reading the relevant subsystem spec before code edits
