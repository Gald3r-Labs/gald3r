---
subsystem_memberships: [TASK_MANAGEMENT]
---
Manage workflow profiles (project types): $ARGUMENTS

`@g-pt` ("project type") lists, switches, copies, locates, and validates gald3r
**Workflow Profiles** — the per-domain task-lifecycle vocabularies under
`.gald3r/config/workflow_profiles/*.yaml` that `load_profile.py` (T1239/T1335)
resolves at runtime. It is the management front-end for those profiles, so you
never have to hand-edit the YAML to switch or fork one.

> Not to be confused with `@g-workflow` (task complexity-scoring / sprint
> planning) — that is a separate, unrelated command. `@g-pt` only touches
> workflow profiles.

## Behavior

Runs the helper `.claude/skills/g-skl-project-types/scripts/g_pt.py`:

```powershell
uv run python .claude/skills/g-skl-project-types/scripts/g_pt.py list
uv run python .claude/skills/g-skl-project-types/scripts/g_pt.py use content_creation
uv run python .claude/skills/g-skl-project-types/scripts/g_pt.py copy software_dev my_workflow
uv run python .claude/skills/g-skl-project-types/scripts/g_pt.py edit my_workflow
uv run python .claude/skills/g-skl-project-types/scripts/g_pt.py validate my_workflow
```

## Subcommands

| Subcommand | What it does |
|---|---|
| `list` | List every built-in + custom profile; marks the **active** one with `*` and `(active)`. |
| `use <profile>` | Set `workflow_profile: <profile>` in `.gald3r/PROJECT.md` (creates/updates the frontmatter field). Validates the profile exists first. |
| `copy <src> <new-name>` | Copy `<src>.yaml` to `<new-name>.yaml`, rewriting the `id:`/`name:` inside. Refuses if the target already exists or the source is missing. |
| `edit <profile>` | Print the resolved absolute path to `<profile>.yaml` so an editor/agent can open it (the no-GUI-safe form of "edit"). |
| `validate <profile>` | Structurally check a profile: parses as YAML, required fields present (`id`, `name`, `task_statuses`), no duplicate/unknown status ids, and `transitions` (if any) reference defined status ids. Exits non-zero on any problem. |

## How the active profile is resolved

`list` reuses `load_profile.py`'s hybrid activation chain (highest priority
first): task frontmatter `workflow_profile:` → `PROJECT.md` `workflow_profile:`
→ `.gald3r/.identity` `project_type=` → `.gald3r/.project_type` → `freeform`.
Legacy ids are alias-normalized (e.g. `software_development` → `software_dev`).

## Notes

- Profiles are **individual `<id>.yaml` files** read by name — there is no
  single `custom.yaml`. `copy` therefore creates `<new-name>.yaml` (a new
  custom profile), and `use <new-name>` activates it.
- `--project-root <path>` pins the `.gald3r/` root (defaults to walking up from
  the script). Useful for tests and out-of-tree invocation.
- Idempotent: re-running `use` updates the field in place (never duplicates it);
  `copy` never overwrites an existing profile.
- Built-in profiles ship under `.gald3r/config/workflow_profiles/`:
  `software_dev`, `content_creation`, `research`.
