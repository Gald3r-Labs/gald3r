---
name: g-skl-design
description: 'UI/UX design engineering — turns functional AI output into production-grade interfaces: oklch color, typography, tokens, dark themes, motion, anti-AI-slop rules, six-step workflow.'
triggers:
  - web page, landing page, dashboard, prototype, mockup
  - slide deck, presentation, animation, data visualization
  - HTML/CSS/JS design, UI component, design system
  - "make it look good", "improve the design", "visual", "stunning"
  - navigation, nav bar, top nav, sidebar, shell, layout, CSS, component styling
  - port component, refactor UI, navigation refactor, visual polish, design pass
  - tsx, React component, App.css, styles.css, any .tsx or .css file being created or modified
  - button, card, modal, dialog, panel, form, input, table, badge, tooltip, dropdown, menu
  - color, typography, spacing, font, theme, token, dark mode, light mode
  - animation, transition, motion, hover, focus, active state, interaction
  - figma, wireframe, mockup, prototype, pixel, responsive, mobile, breakpoint
  - looks bad, looks ugly, looks broken, too much whitespace, too cramped, hard to read
  - any time a .tsx or .css file is being written from scratch or substantially rewritten
sources:
  - https://github.com/abin-2008/web-design-skill (MIT)
  - https://github.com/nexu-io/open-design (Apache-2.0)
  - https://github.com/alchaincyf/huashu-design (via open-design attribution)
token_budget: low
subsystem_memberships: [UI_AND_OUTPUT]
---

## HELP CONTRACT (T442 — cross-platform, non-substitutable)

If the invoking command's arguments are EXACTLY `-h`, `--help`, or `help` (one
token, nothing else): do NOT run any operation of this skill. Respond ONLY with a
compact usage card — the command's name, its one-line purpose, each documented
argument/option on its own line (or "none"), and the path to its command file —
then STOP. Read-only: no `.gald3r/` writes, no state changes, no task/bug
creation. This block lives in the SKILL (not a rule) because skills are the
execution layer on every supported platform; rules are optional context on most.

Run: `gald3r prompt get playbook.design`
Documentation: https://docs.gald3r.ai
