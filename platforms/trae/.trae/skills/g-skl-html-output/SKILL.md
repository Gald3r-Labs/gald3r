---
name: g-skl-html-output
description: Render human-facing reports (status, review, backlog) as themed HTML using docs/templates/ + docs/themes/. Operations RENDER, CHOOSE_THEME, VALIDATE, EXPORT. Invoked by --html flag commands (T1318). Never used for coordination files (TASKS.md, BUGS.md, task specs) which are always markdown.
token_budget: low
subsystem_memberships: [UI_AND_OUTPUT]
---
# g-skl-html-output

Centralized HTML rendering for gald3r human-facing reports. All `--html`-flag
commands (`g-status`, `g-review`, `g-qa-report` — see T1318) route through this
skill. Visual styling lives entirely in `docs/themes/*.css`; templates carry no
inline CSS (T1314/T1315).

## When to Use
- A report command was invoked with `--html` (or AGENT_CONFIG `output_format: html|both`).
- You need to produce a styled, self-contained HTML doc for human consumption.

## Boundary (HARD)
HTML output is **only** for human-facing reports. Coordination/state files are
**always** markdown and must never be rendered to HTML:
`TASKS.md`, `BUGS.md`, `CONSTRAINTS.md`, `learned-facts.md`, task specs in
`.gald3r/tasks/`, and any `.gald3r/` control-plane file.

## Theme / template layout
```
docs/themes/
  gald3r-dark.css     # canonical default (Catppuccin Mocha) — structure + tokens
  gald3r-light.css    # @imports dark, overrides :root (Latte)
  gald3r-mocha.css    # @imports dark, overrides :root (warm sepia)
  gald3r-default.css  # backwards-compat alias -> gald3r-dark.css
  _active.css         # active-theme redirect (rewritten by CHOOSE_THEME)
  theme-schema.json   # editable token contract (drives the Theme Editor)
docs/templates/
  html-base.html      # shell: {{ title }} {{ generated_date }} {{ session_label }} {{ theme_href }} {{ mermaid_theme }} {{ body }}
  report.html         # body fragment for status/reports
  review.html         # body fragment for code reviews
  backlog.html        # body fragment for task backlogs
```

## Operations

### RENDER `<template> <data> <output_path>`
Compose `html-base.html` with a topic body fragment and write the result.
1. Resolve theme via CHOOSE_THEME → `theme_name`.
2. `theme_href = relpath(docs/themes/_active.css, dirname(output_path))`
   (for default `docs/` output this is `themes/_active.css`).
3. `mermaid_theme = 'default'` when `theme_name == gald3r-light`, else `'dark'`.
4. Substitute `{{ title }}`, `{{ generated_date }}` (ISO date), `{{ session_label }}`,
   `{{ theme_href }}`, `{{ mermaid_theme }}`; inject the rendered fragment into `{{ body }}`.
5. Fragment repeat-blocks `<!-- repeat:NAME --> … <!-- /repeat:NAME -->` are
   expanded once per data row, then the literal template block is removed.
6. Call VALIDATE; then EXPORT.

Helper: `.claude/skills/g-skl-html-output/scripts/render.ps1`
```powershell
pwsh -File .claude/skills/g-skl-html-output/scripts/render.ps1 `
  -Template report -Title "Project Status" -SessionLabel "g-status • <gald3r_source>" `
  -BodyHtml $bodyFragmentHtml -OutDir docs
```

### CHOOSE_THEME
1. Read `html_theme:` from `.gald3r/config/AGENT_CONFIG.md` (default `gald3r-dark`).
2. Confirm `docs/themes/<html_theme>.css` exists; else fall back to `gald3r-dark`.
3. Rewrite `docs/themes/_active.css` to `@import url('<html_theme>.css');`
   (portable redirect — no filesystem symlink; Windows-safe). This is the T1328
   active-theme resolution path: templates always link `_active.css`.

### VALIDATE
- The linked theme CSS resolves (target of `_active.css` exists on disk).
- No `<style>` block remains in the output (styling must be external).
- Each `<div class="mermaid">` body is non-empty and starts with a known
  diagram keyword (`graph|flowchart|sequenceDiagram|classDiagram|stateDiagram|erDiagram|gantt|pie|journey`).
- All `{{ … }}` placeholders were substituted (none remain).
Return a pass/fail list; RENDER aborts on fail.

### EXPORT `<html> <topic>`
Save under `html_output_dir:` (default `docs/`) using the g-rl-01 naming
convention: `YYYYMMDD_HHMMSS_<IDE>_<TOPIC>.html` (TOPIC UPPERCASE_WITH_UNDERSCORES).
Return the written path.

## Notes
- Output is self-contained except the single `<link>` to the theme and the
  Mermaid CDN `<script>` (matches the pre-extraction reference docs).
- Token cost: a standard report drops from ~2800 to ~900 output tokens because
  ~140 lines of CSS are no longer emitted inline (T1314/T1315).
