---
subsystem_memberships: [WORKSPACE_COORDINATION]
---
Register a child project under this project: $ARGUMENTS

## What This Command Does

Establishes a **parent → child** relationship between this project and the target project.
Updates `link_topology.md` on **both sides** when the target is locally accessible.

Delegates to `g-skl-wpac-adopt`.

## Usage

```
@g-wpac-adopt <target_project_path>
@g-wpac-adopt <target_project_path> --one-way
```

**Arguments:**
- `target_project_path` — absolute path to the project you want to adopt as a child
- `--one-way` — only update this project's topology (skip writing to the target)

## Examples

```
# Adopt a child project
@g-wpac-adopt <workspace>\child_project

# Adopt without touching the other project (remote/read-only)
@g-wpac-adopt <workspace>\example_mcp --one-way
```

## What Happens

1. Reads `.gald3r/.identity` from both this project and the target
2. Creates `.gald3r/workspace/` in this project if missing
3. Adds the target to `children[]` in this project's `link_topology.md`
4. Sets this project as `parent` in the target's `link_topology.md` (unless `--one-way`)
5. Writes `peers/` snapshots in both projects
6. Prints confirmation with paths updated

## Companion Commands

| Command | Direction | When to Use |
|---------|-----------|-------------|
| `@g-wpac-adopt <path>` | This → becomes parent | Run from the **parent** project |
| `@g-wpac-claim <path>` | This → becomes child | Run from the **child** project |
| `@g-wpac-status` | — | Verify topology after setup |
| `@g-wpac-sync` | — | Sync shared contracts with siblings |
