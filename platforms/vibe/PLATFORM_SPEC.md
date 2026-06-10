---
subsystem_memberships: [PLATFORM_INTEGRATION]
platform: vibe
authoring_path: stub
docs_url: https://docs.mistral.ai/mistral-vibe/terminal
crawl_max_age_days: 14
vault_doc_path: research/platforms/mistral/
last_doc_scan: never
reference: g-skl-platform-mistral
status: stub
cross_link: .mistral
---

# PLATFORM_SPEC.md -- Mistral Vibe CLI (.vibe surface)

> **Stub spec.** The .vibe/ directory is the **config surface of Mistral Vibe CLI**,
> the open-source terminal coding agent powered by Devstral 2 / Codestral. The full,
> verified platform record lives in the **.mistral** spec
> (.gald3r_sys/platforms/.mistral/PLATFORM_SPEC.md); this file exists only so that
> the platforms/.vibe/ config directory (config.toml) appears in uniform platform
> discovery scans (scan_platform_docs.ps1, PLATFORM_CAPABILITY_MATRIX.md,
> HTML guide generation).

## Relationship to .mistral

| | |
|---|---|
| **Product** | Mistral Vibe CLI (the vibe-coding terminal surface of Mistral) |
| **Config dir** | .vibe/ (config.toml, AGENTS.md) |
| **Canonical spec** | See .mistral/PLATFORM_SPEC.md (Mistral Vibe CLI / Mistral Code / Le Chat) |
| **gald3r skill** | g-skl-platform-mistral |

The .mistral spec documents three Mistral surfaces (Vibe CLI, Mistral Code IDE
plugin, Le Chat). gald3r targets the **Vibe CLI** surface specifically because it is
the only one that reads project-level config files (.vibe/ + AGENTS.md). All
capability claims, install verification, and SCAN_DOCS checklist items for the
vibe-coding surface are maintained in .mistral/PLATFORM_SPEC.md -- do not duplicate
them here.

## Hook System

- **Type**: [STUB] — see `.mistral/PLATFORM_SPEC.md` for authoritative hook details
- **Config file**: `.vibe/config.toml` (experimental hook support)
- **Events available**: [STUB] — unverified; consult `.mistral` spec
- **Payload format**: [STUB] — unverified
- **Limitations**: This is the `.vibe/` config surface stub; all verified hook wiring details live in the `.mistral` canonical spec
- **gald3r hook files**: [STUB] — consult `g-skl-platform-mistral` SKILL.md for current hook wiring

## Atypical Handling

- This is a **stub spec** that exists only for platform discovery tooling (scan, matrix, HTML guide generation)
- All capability claims, install ACs, and hook wiring are in `.mistral/PLATFORM_SPEC.md`
- Do not populate this file with capability claims — cross-link to `.mistral` only
- The `.vibe/` config dir is the file-system surface; `.mistral` is the knowledge surface

## gald3r Integration Notes

- Do not ship `.vibe/`-specific gald3r files independently — use `g-skl-platform-mistral` (covers all three Mistral surfaces including Vibe CLI)
- `AGENTS.md` is the primary instruction file for Vibe CLI
- If the Vibe CLI surface diverges significantly from the Mistral CLI/Code surfaces, promote this stub to a full spec (backfill all sections from `.mistral` and remove the cross_link)
- Re-verify on next `@g-platform-scan-docs mistral` (crawl_max_age_days: 14) — hook support is listed as experimental