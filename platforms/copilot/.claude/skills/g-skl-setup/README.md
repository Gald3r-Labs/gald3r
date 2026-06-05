---
subsystem_memberships: [PROJECT_IDENTITY_SETUP]
---
# g-skl-setup

> Human-facing companion to `SKILL.md`. The LLM agent reads `SKILL.md`; this
> page is for developers browsing the skill library on GitHub.

## What it does

First-time gald3r installation in a project. Creates the `.gald3r/` folder structure, seeds the canonical template files (TASKS.md, BUGS.md, PROJECT.md, PLAN.md, CONSTRAINTS.md, SUBSYSTEMS.md, IDEA_BOARD.md, FEATURES.md, learned-facts.md), and runs subsystem discovery.

Two layouts:

- **Slim** — what `g-skl-setup` creates by default. Just the seven canonical files plus `tasks/`, `bugs/`, `features/`, `subsystems/`, `reports/`, `logs/`, `specifications_collection/`.
- **Full** — <gald3r_source> only. Adds `config/`, `experiments/`, `linking/`, `vault/`, `phases/`. Do not create these in slim installs.

## When to use

- First-time setup of gald3r in a project (`@g-setup`)
- Re-initialize a project after a `.gald3r/` wipe (`Reset` mode — DESTRUCTIVE)
- Add the lock file after a manual install (`@g-skl-setup` Step 8)

## Trigger phrases

```
@g-setup | install gald3r | initialize gald3r | set up gald3r in this project
```

## What happens, in order

1. **Workspace-Control member guard** (BUG-021 / `g-rl-36`). If the target is a controlled_member or migration_source, setup is refused — members get a marker-only `.gald3r/` shape via `@g-wrkspc-spawn` or `@g-wrkspc-adopt` instead.
2. **Existing-install detection.** If the target already has substantive content, asks: Merge / Skip / Reset.
3. **Call `gald3r_install` MCP** if available; otherwise create the folder tree manually.
4. **Generate `.identity`** with a UUID for stable project identification.
5. **Verify structure** against the canonical slim layout.
6. **Create PROJECT.md scaffolding** including the Project Linking section.
7. **Subsystem discovery** — scans the project for likely subsystems and creates one spec file per discovery.
8. **Write `gald3r-skills-lock.json`** (T1043) — SHA-256 hashes of every installed `SKILL.md`. Lets `gald3r_validate.ps1` detect tampering and `UPGRADE` flows classify which skills changed.
9. **Print next steps** for the user.

## Examples

### Fresh install

```
@g-setup
```

Walks through the slim layout creation, generates a project_id, and prints "what's next" guidance.

### Verify install integrity later

```powershell
.\scripts\gald3r_skills_lock.ps1 -Action VERIFY -ProjectPath .
```

Recomputes SKILL.md hashes against `gald3r-skills-lock.json`. Exits non-zero if any skill is tampered or missing.

### Detect available upgrades

```powershell
.\scripts\gald3r_skills_lock.ps1 -Action UPGRADE -ProjectPath . `
    -SourceRoot <workspace>\<gald3r_source>
```

Classifies each skill as `unchanged`, `local-modified`, `upstream-changed`, `both-changed`, `new`, or `removed`.

## Member-repo gotcha

Workspace-Control member repositories get a **marker-only** `.gald3r/` (only `.identity` + `PROJECT.md`). `g-skl-setup` deliberately refuses to install into members — use `g-skl-pcac-spawn` or `g-wrkspc-adopt` instead. See `g-rl-36`.

## See also

- `gald3r_install` (MCP tool) — the backend this skill prefers when available
- `g-rl-36` — member-repo marker-only invariant
- `g-skl-pcac-spawn`, `g-wrkspc-adopt` — the sanctioned install paths for member repos
- `docs/SKILLS_LOCK_FORMAT.md` — lock file format reference
