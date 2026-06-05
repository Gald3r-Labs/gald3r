---
name: g-skl-theme-editor
description: Create and edit gald3r HTML themes against docs/themes/theme-schema.json. Visual editor (live preview, per-token color pickers, import/export :root blocks) ships in example_desktop; this skill is the spec + a file-first fallback that works without the app. Invoked by g-theme-edit.
token_budget: low
subsystem_memberships: [UI_AND_OUTPUT]
---
# g-skl-theme-editor

Author and edit gald3r HTML themes. A theme is a `:root` token override on top of
`docs/themes/gald3r-dark.css` (the canonical structure). The editable surface is
defined by `docs/themes/theme-schema.json` (groups → variables → type/default).

## When to Use
- `g-theme-edit` was invoked.
- The user wants a new theme, to tweak an existing one, or to import/export tokens.

## Two paths

### A. Visual editor — `docs/theme-editor.html` (T1323–T1327, T1331)
A self-contained, build-free visual editor lives at **`docs/theme-editor.html`**.
Open it in any browser (or a Tauri/Electron webview). It:
- reads `docs/themes/theme-schema.json` (with an embedded offline fallback),
- renders grouped color/string/number inputs (T1324),
- live-previews a sample report with the in-progress tokens (T1325),
- imports/exports a `:root` block and downloads a `gald3r-<name>.css` (T1326),
- autosaves edits to `localStorage` (T1327),
- offers a base-theme selector (dark/light/mocha), reset, and rename (T1331).

**example_desktop integration:** throne ships the editor by serving this file as a
static asset (copy `docs/theme-editor.html` + `docs/themes/` into throne's
`public/theme-editor/`, or load it in a webview). No React/router surgery needed —
the editor is framework-free. Saving a downloaded `.css` into `docs/themes/` plus
`@g-theme-edit activate <name>` makes it the active theme.

### B. File-first fallback (no app required)
All theme features have a file-first path (per gald3r C-0xx file-first policy):

**CREATE `<name>`**
1. Read `docs/themes/theme-schema.json` for the token list + defaults.
2. Write `docs/themes/<name>.css`:
   ```css
   /*! gald3r-<name> theme */
   @import url('gald3r-dark.css');
   :root { /* override only the tokens you want to change */ }
   ```
3. Only include tokens that differ from dark; everything else inherits structure
   and values from `gald3r-dark.css`.

**EDIT `<name>` `<--token>` `<value>`** — update one variable in the theme's `:root`.

**IMPORT `<path>`** — read a `:root { … }` block (or full theme file) and write it
to `docs/themes/<name>.css` with the `@import` header prepended if absent.

**EXPORT `<name>`** — print the theme's `:root` block (the editable delta) so it
can be shared or pasted into the visual editor.

**PREVIEW `<name>`** — render the reference report through `g-skl-html-output`
RENDER with `html_theme` temporarily set to `<name>`, so the user can eyeball it.

**ACTIVATE `<name>`** — set `html_theme: <name>` in `.gald3r/config/AGENT_CONFIG.md`
and have `g-skl-html-output` CHOOSE_THEME rewrite `docs/themes/_active.css`.

## Validation
- Every overridden token name must exist in `theme-schema.json`.
- `color` values must be valid CSS colors; `number` values within `min`/`max`.
- The file must `@import url('gald3r-dark.css')` first (so structure is inherited).

## Notes
- Built-in themes (`gald3r-dark`, `gald3r-light`, `gald3r-mocha`) are reference
  examples; user themes follow the same shape.
- Never edit `gald3r-dark.css` structural rules to restyle — change tokens only.
