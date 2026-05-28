Register a parent project for this project: $ARGUMENTS

## What This Command Does

Establishes a **child → parent** relationship between this project and the target project.
Updates `link_topology.md` on **both sides** when the parent is locally accessible.

Delegates to `g-skl-pcac-claim`.

## Usage

```
@g-pcac-claim <parent_project_path>
@g-pcac-claim <parent_project_path> --one-way
```

**Arguments:**
- `parent_project_path` — absolute path to the project you want to claim as your parent
- `--one-way` — only update this project's topology (skip writing to the parent)

## Examples

```
# Claim gald3r_master_control as this project's parent
@g-pcac-claim G:\gald3r_ecosystem\gald3r_master_control

# Claim without touching the parent project (remote/read-only)
@g-pcac-claim G:\gald3r_ecosystem\gald3r_master_control --one-way
```

## What Happens

1. Reads `.gald3r/.identity` from both this project and the target parent
2. Creates `.gald3r/linking/` in this project if missing
3. Sets the parent in this project's `link_topology.md`
4. Adds this project to `children[]` in the parent's `link_topology.md` (unless `--one-way`)
5. Writes `peers/` snapshots in both projects
6. Prints confirmation with paths updated

> **Tip**: You only need to run one side. `@g-pcac-claim` from the child and
> `@g-pcac-adopt` from the parent both perform the same bidirectional update.
> Pick whichever project you have open.

## Companion Commands

| Command | Direction | When to Use |
|---------|-----------|-------------|
| `@g-pcac-claim <path>` | This → becomes child | Run from the **child** project |
| `@g-pcac-adopt <path>` | This → becomes parent | Run from the **parent** project |
| `@g-pcac-status` | — | Verify topology after setup |
| `@g-pcac-sync` | — | Sync shared contracts with siblings |
