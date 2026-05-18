# Release Profiles

This directory contains per-tier release profile definitions for the gald3r product tier system.

## Purpose

Release profiles define the routing table for the tier release system (`g-skl-release`) and tier-aware parity sync (`platform_parity_sync.ps1 -TierSync`). Each profile describes one release tier: where it lives, what it includes, and what it requires to run.

## Schema

```yaml
name: string                    # Tier name (must match filename without .yaml)
tier_prefix: string             # Version prefix letter/string (e.g. "S" → "S1.2.0")
template_dir: string            # Relative path to the template directory for this tier
destination: string             # Absolute local path to the sibling release repo
remote: string                  # GitHub remote URL for this tier's public repo
included_tiers: [string]        # Tiers included in this release (adv includes slim+full+adv)
operational_requirement: string # "none" | "api-keys" | "docker"
description: string             # Human-readable description
```

## Files in This Project

| File | Tier | Requires |
|------|------|----------|
| `slim.yaml` | Baseline | Nothing — git clone only |
| `full.yaml` | Full | API keys + network |
| `adv.yaml` | Advanced | Docker + managed services |

## Usage

Read by:
- `g-skl-release` (CANDIDATE-CHECK, SHIP, ROADMAP-GENERATE)
- `platform_parity_sync.ps1 -TierSync`
- `g-skl-tasks` (for tier badge derivation fallback)
- `g-skl-tier-setup` (wizard reads profiles to enumerate available tiers)

## Extending (Consumer Projects)

Projects using gald3r can define **their own tier names** — they are not required to use `slim/full/adv`. Create a `release_profiles/` directory in your `.gald3r/` folder and add one YAML file per tier. The tier name is the `name:` field, not the filename (though they should match for clarity).

Example custom project with two tiers:
```yaml
# .gald3r/release_profiles/community.yaml
name: community
tier_prefix: C
template_dir: template_community/
destination: /path/to/community-repo
remote: https://github.com/org/project-community.git
included_tiers: [community]
operational_requirement: none
description: "Free community edition"
```
