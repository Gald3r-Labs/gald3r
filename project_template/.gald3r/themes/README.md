---
gald3r_rel_version: "2.1.1"
schema_version: "generic-v1"
---
# .gald3r/themes/ — Project-Local Theme Override Layer

**This folder is intentionally empty by default.**

Global user themes live in `{vault_location}/themes/` (see `.gald3r/.identity` for your vault path).

## Purpose

This folder is the **project-local override layer** in the two-tier theme resolution system:

```
Resolution order (first match wins):
1. .gald3r/themes/{active_slug}/     ← project-local override  ← YOU ARE HERE
2. {vault_location}/themes/{active_slug}/   ← global vault theme
3. ERROR: theme not found
```

## When to use this folder

- You want a **project-specific variant** of a global theme (e.g. different SOUL.md for a work project)
- You want a **completely project-local** theme not shared across other projects
- You need to **test theme changes** before promoting to the vault

## Active theme selection

The active theme slug is set per-project in `.gald3r/config/active_theme.json`:

```json
{
  "slug": "trentworks",
  "source": "vault",
  "overrides": {}
}
```

`source` is `"vault"` (default) or `"local"` (forces this override folder).

## Global themes

To install or browse global themes, look in:
```
{vault_location}/themes/
  trentworks/     ← primary user theme
  codeshop/       ← alternate workspace theme
```
