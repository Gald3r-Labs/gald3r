# g-tier-setup

Configure product tiers for this project — interactive wizard to define tier names, operational requirements, version prefixes, and remote repos. Activates **g-skl-tier-setup**.

## When to use

Run this command when you want to adopt the product tier system for your project. This is a one-time setup for most projects, though you can re-run ENABLE any time the subsystem list changes.

Two operations:

- **SETUP** — first-time wizard. Creates `.gald3r/release_profiles/{tier}.yaml` files, scaffolds `template_{tier}/` directories, writes tier metadata into `.gald3r/.identity`.
- **ENABLE** — annotates existing subsystem specs with `min_tier:` (using inference heuristics), then runs `scripts/platform_parity_sync.ps1 -TierSync` to populate template directories.

## Usage

```
@g-tier-setup                   # If unconfigured, defaults to SETUP; if configured, defaults to ENABLE
@g-tier-setup SETUP             # Explicit first-time setup
@g-tier-setup ENABLE            # Annotate subsystems and run tier sync
@g-tier-setup SETUP --force     # Overwrite existing release_profiles/ (destructive; warns first)
```

## SETUP flow (5 questions)

1. How many product tiers? (default 3)
2. Name for each tier (lowercase, hyphens allowed; 2–20 chars)
3. Operational requirement per tier (`none` / `api-keys` / `docker` / `custom`)
4. Version prefix per tier (default = first letter uppercased)
5. Remote repo URL per tier (optional; enter to skip)

## ENABLE flow

1. Reads `.gald3r/release_profiles/*.yaml` to learn the tier list
2. Scans each `.gald3r/subsystems/*.md` spec
3. Applies inference heuristics (Docker references → highest-tier, API-key references → mid-tier, otherwise → lowest-tier)
4. Prompts once to accept all, abort, or edit line-by-line
5. Writes `min_tier:` into each subsystem's frontmatter
6. Appends Activity Log entry to `tier-management` subsystem
7. Calls `scripts/platform_parity_sync.ps1 -TierSync`

## Availability

Ships in `gald3r_template_full/` and `gald3r_template_adv/` only — NOT in `gald3r_template_slim/`. Slim projects are pre-configured by gald3r itself; they do not manage their own tier definitions.

## Related

- `g-skl-tier-setup` — the skill that this command delegates to
- `g-skl-subsystems` — writes `min_tier:` on new subsystem creation
- `g-skl-release` — reads `release_profiles/` for CREATE / ASSIGN / PUBLISH
- `scripts/platform_parity_sync.ps1 -TierSync` — the actual template-directory populator
