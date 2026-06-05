---
name: g-skl-design
description: >
  UI/UX design engineering skill — transforms functional AI output into stunning, production-grade
  interfaces. Merges Claude Design, Open Design, and web-design-skill methodologies. Covers oklch
  color systems, typography, layout composition, design tokens, component hierarchy, dark themes,
  motion, anti-AI-slop rules, 5-dimensional self-critique, and a six-step design workflow.
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

<!-- gald3r-thinned-shim -->
# g-skl-design — thinned shim (prompt-layer)

> **Judgment served by the bundled prompt layer** (one canonical copy in `.gald3r_sys/engine`). Full
> original text retained in **`SKILL.full.md`** for installs without the engine.

**What it does:** design engineering — stunning-not-functional, anti-slop.

## Preferred — fetch the centralized judgment
`uv run --project .gald3r_sys/engine gald3r prompt get playbook.design`   ·   MCP `gald3r_prompt_get id=playbook.design`

## Manual fallback (engine not provisioned)
Follow **`SKILL.full.md`** in this directory, plus any `rules.md` / `reference/` / `examples/`.
