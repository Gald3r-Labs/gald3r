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
token_budget: medium
subsystem_memberships: [UI_AND_OUTPUT]
---

# g-skl-design — Design Engineering Skill

## When to Use This Skill

Activate whenever the request involves a **visual, interactive, or presentational deliverable**:

| ✅ In scope | ❌ Out of scope |
|---|---|
| Web pages, landing pages, marketing sites | Pure back-end APIs, CLI tools |
| Interactive prototypes with device frames | Data-processing scripts |
| HTML slide decks / presentations (1920×1080) | Non-visual code refactoring |
| CSS/JS animations and timeline demos | Performance tuning only |
| Dashboards and data visualizations | Debugging without UI output |
| Design system / token exploration | — |
| UI mockups turned into code | — |

---

## Core Design Philosophy

**The bar is "stunning," not "functional."** Every pixel is intentional. Every interaction is deliberate.

- Respect design systems and brand consistency while daring to innovate
- Aim for Dribbble / Behance showcase level on every output
- Whitespace is design — "1,000 no's for every yes"
- CSS, HTML, JS, and SVG are far more capable than most people realize — use them to astonish
- **Code ≫ Screenshots**: when both are provided, extract tokens from source code, not pixels

---

## Anti-AI-Slop Rules (MANDATORY — Check Before Emitting)

These patterns **instantly signal "assembled by AI"**. Ban them unconditionally:

### Forbidden Visual Patterns
- ❌ Purple-pink-blue gradient backgrounds
- ❌ Rounded card with a colored left-border accent
- ❌ Cookie-cutter gradient button + large-radius card combo
- ❌ Heavy glow effects or neon gradients for serious/business contexts
- ❌ Generic hero with centered text + stock-photo background
- ❌ Sections stuffed with emoji as "icons" (`🚀 ⚡ ✨` as fillers)
- ❌ Hand-drawn SVG humans (stick figures or blob people)
- ❌ Fabricated customer logo walls or made-up testimonial counts
- ❌ Meaningless stats / numbers / icon spam ("data slop")
- ❌ More than three font families in one design

### Forbidden Font Choices (Overused by AI)
- ❌ **Inter** as a display / hero face (fine for body in tech contexts, not as the statement face)
- ❌ Roboto, Arial, system-ui as primary brand fonts
- ❌ Fraunces + purple-pink gradients (peak 2024 AI aesthetic)

### Emoji Rules
**No emoji by default.** Only use emoji when the brand itself uses them (Notion, early Linear, consumer apps) and match their density precisely.
- ❌ Emoji as icon substitutes
- ❌ Emoji before headings for decoration
- ✅ Brand uses emoji → follow the brand
- ✅ No icon → use a placeholder (see Placeholder Philosophy)

---

## 5-Dimensional Self-Critique (Pre-Emit Gate)

Before emitting any artifact, **silently score your output 1–5 across five dimensions**. Anything below 3/5 on any axis is a regression — fix it and rescore. Two passes is normal.

| Dimension | What to evaluate |
|---|---|
| **Philosophy** | Does it embody a clear visual school? Is there a "why" behind the choices, or did I freestyle? |
| **Hierarchy** | Is visual weight used intentionally? Can the eye find the most important element in <1s? |
| **Execution** | Are spacing, alignment, and color consistent? Is the detail level appropriate for the fidelity? |
| **Specificity** | Is this design *specific to this context*, or could it belong to any product? |
| **Restraint** | Have I removed everything non-essential? Is whitespace working for me? |

Only emit when all five dimensions score ≥ 3/5.

---

## 6-Step Design Workflow

```
1. Understand requirements  →  Ask only when information is genuinely insufficient
2. Gather design context    →  Code > screenshots; never start from nothing
3. Declare design system    →  Colors, fonts, spacing, motion — in Markdown, before code
4. Show v0 draft early      →  Placeholders + layout + tokens; let the user course-correct
5. Full build               →  Components, states, motion; pause at key decision points
6. Verify                   →  Pre-delivery checklist; run 5-dim critique; no console errors
```

### Step 1: Understand Requirements

**Do not mechanically fire off a long question list every time:**

| Scenario | Ask? |
|---|---|
| "Make a deck" (no PRD, no audience) | ✅ Extensively: audience, duration, tone |
| "Use this PRD to make a 10-min deck for Eng All Hands" | ❌ Enough info — start building |
| "Turn this screenshot into an interactive prototype" | ⚠️ Only if interactions are unclear |
| "Design onboarding for my food-delivery app" | ✅ Heavily: users, flows, brand, variants |
| "Recreate the composer UI from this codebase" | ❌ Read the code directly |

### Step 2: Gather Design Context (Priority Order)

1. **Resources the user provides** (screenshots / Figma / codebase / design system) → extract tokens
2. **Existing pages of the product** → ask whether you can review them
3. **Industry best practices** → ask which brands to reference
4. **Starting from scratch** → tell the user explicitly, then pick from the Direction Picker below

When analyzing references, extract: color system, typography, spacing, border-radius strategy, shadow hierarchy, motion style, component density, copywriting tone.

**Brand-spec extraction protocol** (when screenshots/URLs are provided):
1. Locate brand colors in the asset
2. `grep` or inspect for hex/oklch values
3. Codify into `brand-spec.md` with primary, secondary, neutral, accent
4. Vocalize your reading to the user before writing CSS

### Step 3: Declare the Design System

**Before writing the first line of code**, articulate the system in Markdown and let the user confirm:

```markdown
Design Decisions:
- Color palette:       [primary oklch value] / [neutral scale] / [accent]
- Typography:          [display font] / [body font] / [mono font]
- Spacing system:      base 4px or 8px; multiples: 4, 8, 12, 16, 24, 32, 48, 64
- Border-radius:       [tight: 4px | rounded: 8-12px | pill: 9999px]
- Shadow hierarchy:    elevation 1 (subtle) → 5 (modal)
- Motion style:        [duration range] / [easing preference] / [trigger type]
```

### Step 4: Show v0 Draft Early

Before writing full components, produce a "viewable v0":
- Core structure + color/typography tokens
- Key module placeholders with explicit markers (`[image]`, `[icon]`, `[chart]`)
- Your list of design assumptions

A v0 with placeholders is more valuable than a perfect v1 with the wrong direction.

### Step 5: Full Build

After v0 approval, write all components, add all states, implement motion. At key decision points (e.g., interaction approach), pause and confirm — don't silently push through.

### Step 6: Verify

Walk through the Pre-delivery Checklist. Run the 5-Dimensional Self-Critique. Only then emit.

---

## Design Direction Picker (No Brand = Pick One)

When the user has no brand spec, present five deterministic visual directions. Each direction includes a palette and font stack — **no freestyle improvisation**:

| Direction | Mood | Primary Palette | Font Stack | References |
|---|---|---|---|---|
| **Editorial — Monocle / FT** | Print magazine, ink + cream | `oklch(0.25 0.04 30)` ink-dark + `oklch(0.95 0.02 80)` cream | Newsreader (display) + Outfit (body) | Monocle, FT Weekend, NYT Magazine |
| **Modern Minimal — Linear / Vercel** | Cool, structured, sparse accent | `oklch(0.15 0.01 250)` off-black + `oklch(0.55 0.22 250)` electric blue | Space Grotesk (display) + Inter (body) | Linear, Vercel, Stripe |
| **Tech Utility** | Information density, monospace, terminal | `oklch(0.10 0.01 200)` terminal-dark + `oklch(0.65 0.18 160)` terminal-green | JetBrains Mono (display) + Space Grotesk (UI) | Bloomberg, Bauhaus tools |
| **Brutalist Experimental** | Raw, oversized type, harsh accents | `oklch(0.98 0.00 0)` white + `oklch(0.25 0.00 0)` black + `oklch(0.65 0.25 30)` raw orange | Any compressed / condensed sans (Barlow Condensed) | Bloomberg Businessweek, Achtung |
| **Soft Warm** | Generous, low-contrast, peachy neutrals | `oklch(0.96 0.015 80)` warm cream + `oklch(0.55 0.08 40)` terracotta | Plus Jakarta Sans (display) + Outfit (body) | Notion marketing, Apple Health |

---

## Color System — oklch

**Always use `oklch()` for color derivation.** It is perceptually uniform — same lightness values *look* the same brightness to the human eye, unlike HSL where yellow at 50% looks much brighter than blue at 50%.

```css
:root {
  /* oklch(lightness chroma hue) */
  /* lightness: 0 = black, 1 = white */
  /* chroma: 0 = gray, 0.4 = max vivid */
  /* hue: 0-360 degrees */

  --hue: 250; /* single source of truth for brand hue */

  /* Primary scale */
  --color-primary-900: oklch(0.20 0.22 var(--hue));
  --color-primary-700: oklch(0.35 0.24 var(--hue));
  --color-primary-500: oklch(0.55 0.25 var(--hue));  /* main CTA */
  --color-primary-300: oklch(0.75 0.15 var(--hue));
  --color-primary-100: oklch(0.93 0.06 var(--hue));

  /* Neutral scale (slightly chromatic — never pure gray) */
  --color-gray-950: oklch(0.12 0.012 var(--hue));
  --color-gray-900: oklch(0.21 0.014 var(--hue));
  --color-gray-800: oklch(0.27 0.014 var(--hue));
  --color-gray-700: oklch(0.37 0.014 var(--hue));
  --color-gray-600: oklch(0.45 0.014 var(--hue));
  --color-gray-500: oklch(0.55 0.014 var(--hue));
  --color-gray-400: oklch(0.71 0.010 var(--hue));
  --color-gray-300: oklch(0.87 0.008 var(--hue));
  --color-gray-200: oklch(0.92 0.006 var(--hue));
  --color-gray-100: oklch(0.96 0.004 var(--hue));
  --color-gray-50:  oklch(0.98 0.002 var(--hue));

  /* Semantic */
  --color-success: oklch(0.62 0.20 145);
  --color-warning: oklch(0.72 0.18 75);
  --color-danger:  oklch(0.58 0.22 25);
}
```

**Rules for derivation:**
- Keep chroma ≤ 0.12 for backgrounds; ≤ 0.25 for CTAs; ≤ 0.30 for accents
- Never invent new hues — derive harmonious variants from `--hue` ± 30°
- Prefer brand colors for palette; only oklch-derive when extending

---

## Color × Font Pairing Reference

Use when the user provides no design context. Drop this immediately once brand materials arrive.

| Style | Primary Color | Font Pairing | Best For |
|---|---|---|---|
| Modern tech | `oklch(0.55 0.25 250)` blue-violet | Space Grotesk + Inter | SaaS, dev tools, AI products |
| Elegant editorial | `oklch(0.35 0.10 30)` warm brown | Newsreader + Outfit | Content platforms, blogs |
| Premium brand | `oklch(0.20 0.02 250)` near-black | Sora + Plus Jakarta Sans | Luxury, consulting, finance |
| Lively consumer | `oklch(0.70 0.20 30)` coral | Plus Jakarta Sans + Outfit | E-commerce, lifestyle, social |
| Minimal professional | `oklch(0.50 0.15 200)` teal-blue | Outfit + Space Grotesk | Data products, dashboards, B2B |
| Artisan warmth | `oklch(0.55 0.15 80)` caramel | Caveat (decorative) + Newsreader | Food, education, creative |

**Avoid always:**
- ❌ Inter + Roboto + blue buttons (peak AI aesthetic)
- ❌ Fraunces + purple-pink gradients (overused)
- ❌ More than 3 font families

---

## Typography System

```css
/* Fluid typography with clamp() */
:root {
  --text-xs:   clamp(0.75rem, 0.7rem + 0.25vw,  0.875rem);
  --text-sm:   clamp(0.875rem, 0.8rem + 0.35vw, 1rem);
  --text-base: clamp(1rem,     0.9rem + 0.5vw,   1.125rem);
  --text-lg:   clamp(1.125rem, 1rem + 0.6vw,     1.25rem);
  --text-xl:   clamp(1.25rem,  1.1rem + 0.75vw,  1.5rem);
  --text-2xl:  clamp(1.5rem,   1.25rem + 1.25vw, 2rem);
  --text-3xl:  clamp(2rem,     1.5rem + 2.5vw,   3rem);
  --text-4xl:  clamp(2.5rem,   2rem + 2.5vw,     4rem);
  --text-hero: clamp(3rem,     2rem + 5vw,        7rem);
}
```

**Typography rules:**
- Bold type-size contrast: a 4–6× ratio between h1 and body text is normal (not excessive)
- `text-wrap: pretty` on all paragraphs and headings
- Use `font-feature-settings: "kern" 1, "liga" 1, "calt" 1` for professional typography
- Display fonts: use sparingly, only for hero text — body needs legibility
- Line height for body: 1.5–1.7; for headings: 1.0–1.2; for display: 0.9–1.0
- Letter spacing on ALL CAPS: `0.08–0.12em`

---

## Dark Theme Design

Dark themes are not "invert the colors" — they require distinct visual decisions:

```css
:root[data-theme="dark"] {
  /* Backgrounds use low-chroma, not pure black */
  --bg-base:    oklch(0.09 0.010 250);  /* near-black with slight hue */
  --bg-surface: oklch(0.14 0.012 250);  /* card / modal background */
  --bg-raised:  oklch(0.18 0.014 250);  /* elevated elements */
  --bg-overlay: oklch(0.22 0.016 250);  /* dropdowns, popovers */

  /* Text hierarchy — never pure white */
  --text-primary:   oklch(0.94 0.004 250);  /* primary text */
  --text-secondary: oklch(0.72 0.008 250);  /* secondary / muted */
  --text-tertiary:  oklch(0.52 0.008 250);  /* placeholders */

  /* Borders: very subtle */
  --border-default: oklch(0.27 0.014 250);
  --border-strong:  oklch(0.35 0.014 250);
}
```

**Dark theme rules:**
- Never use pure `#000000` or `#ffffff` — slightly chromatic values look more refined
- Shadows in dark UIs: use `box-shadow` with hue-tinted colors, not generic black shadows
- Reduce chroma on accent colors in dark mode (vivid colors look harsh on dark backgrounds)
- Ensure 4.5:1 contrast ratio for body text; 3:1 for large text (WCAG AA)
- Color-only information must have a secondary indicator (shape, pattern, label)

---

## Layout Composition Principles

- **Visual rhythm**: use consistent spacing multiples (4px base → 4, 8, 12, 16, 24, 32, 48, 64)
- **Whitespace as a design element**: generous negative space signals premium; crowded signals cheap
- **Asymmetric grids**: editorial designs use off-center layouts to create visual tension
- **Type-led layouts**: let typographic scale determine the grid, not the other way around
- **Z-axis depth**: use subtle layering (shadows, blur, overlap) to create dimensionality without heavy shadows
- **Focal hierarchy**: one clear primary focal point per screen section; not three competing for attention

```css
/* Modern layout primitives */
.layout-prose      { max-width: 65ch; }          /* Optimal reading width */
.layout-content    { max-width: 80rem; }          /* Standard content */
.layout-wide       { max-width: 96rem; }          /* Wide dashboards */
.layout-full       { width: 100%; }

/* Responsive grid */
.grid-auto-fill    { display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: var(--space-6); }
.grid-sidebar      { display: grid; grid-template-columns: 240px 1fr; gap: var(--space-8); }
```

### Appropriate Scale

| Context | Minimum Size |
|---|---|
| 1920×1080 presentations | Text ≥ 24px (ideally ≥ 32px for body) |
| Mobile mockups | Touch targets ≥ 44×44px |
| Web body text | Start at 16–18px |
| Data labels in charts | ≥ 12px |

---

## Design Token Declaration

Declare all tokens in CSS custom properties before writing any component styles:

```css
:root {
  /* === COLOR TOKENS === */
  --hue-brand: 250;
  /* (full scale declared per Color System section above) */

  /* === SPACING TOKENS === */
  --space-1: 4px;   --space-2: 8px;   --space-3: 12px;  --space-4: 16px;
  --space-5: 20px;  --space-6: 24px;  --space-8: 32px;  --space-10: 40px;
  --space-12: 48px; --space-16: 64px; --space-20: 80px; --space-24: 96px;

  /* === RADIUS TOKENS === */
  --radius-sm:  4px;
  --radius-md:  8px;
  --radius-lg:  12px;
  --radius-xl:  16px;
  --radius-2xl: 24px;
  --radius-pill: 9999px;

  /* === SHADOW TOKENS === */
  --shadow-1: 0 1px 2px oklch(0.0 0.0 0 / 0.08);
  --shadow-2: 0 2px 8px oklch(0.0 0.0 0 / 0.10);
  --shadow-3: 0 4px 16px oklch(0.0 0.0 0 / 0.12);
  --shadow-4: 0 8px 32px oklch(0.0 0.0 0 / 0.15);
  --shadow-5: 0 24px 64px oklch(0.0 0.0 0 / 0.20);

  /* === MOTION TOKENS === */
  --duration-fast:   100ms;
  --duration-normal: 200ms;
  --duration-slow:   350ms;
  --duration-enter:  500ms;
  --ease-out:     cubic-bezier(0.0, 0.0, 0.2, 1.0);
  --ease-in:      cubic-bezier(0.4, 0.0, 1.0, 1.0);
  --ease-in-out:  cubic-bezier(0.4, 0.0, 0.2, 1.0);
  --ease-spring:  cubic-bezier(0.34, 1.56, 0.64, 1.0);  /* overshoot */
}
```

---

## Component Hierarchy & Visual Weight

Map every element to a **visual weight tier** before building:

| Tier | Examples | Visual Treatment |
|---|---|---|
| **P0 — Hero** | Page title, CTA, hero stat | Largest type, highest contrast, most whitespace around |
| **P1 — Primary** | Section headings, primary actions | Prominent but subordinate to P0 |
| **P2 — Secondary** | Body text, secondary labels | Standard reading size, medium contrast |
| **P3 — Tertiary** | Captions, helper text, metadata | Small, low contrast, supporting role |
| **P4 — Structural** | Dividers, grid lines, backgrounds | Should disappear — presence is a sign of over-design |

**State coverage** — every interactive component must have these states declared:
- `default` → `hover` (color shift or shadow lift)
- `active` / `pressed` (scale-down or color darken)
- `focus` (visible outline for keyboard navigation)
- `disabled` (reduced opacity, cursor: not-allowed, no pointer events)
- `loading` (skeleton or spinner state)
- `empty` (zero-state with call-to-action)
- `error` (red/danger variant + error message)

---

## Motion & Animation Design

**Choose the lightest approach that achieves the effect:**

1. **CSS transitions/animations** — 80% of micro-interactions (hover, press, entry, toggle)
2. **React state + `setTimeout` / `requestAnimationFrame`** — simple frame-by-frame
3. **Custom `useTime` + `Easing` + `interpolate`** — timeline-driven video/demo scenes
4. **Third-party library** — only when user explicitly requests Framer Motion / GSAP / Lottie

**Easing cheat sheet:**
```css
/* Entry animations */
.fade-in     { animation: fadeIn var(--duration-enter) var(--ease-out) forwards; }
.slide-up    { animation: slideUp var(--duration-enter) var(--ease-out) forwards; }
.scale-in    { animation: scaleIn var(--duration-normal) var(--ease-spring) forwards; }

@keyframes fadeIn   { from { opacity: 0; } to { opacity: 1; } }
@keyframes slideUp  { from { opacity: 0; transform: translateY(16px); } to { opacity: 1; transform: translateY(0); } }
@keyframes scaleIn  { from { opacity: 0; transform: scale(0.92); } to { opacity: 1; transform: scale(1); } }
```

**Motion rules:**
- Always provide `@media (prefers-reduced-motion)` fallback — disable or reduce animations
- Duration: micro-interactions 100–200ms; page transitions 300–500ms; elaborate entries 500–800ms
- Use a unified easing-function library — reuse the same set within a project for consistent feel
- Don't add a title screen to animation/video artifacts — go straight to the content

### Animation Timeline Engine (React)

```jsx
const useTime = (duration = 5000) => {
  const [time, setTime] = React.useState(0);
  const [playing, setPlaying] = React.useState(true);
  const frameRef = React.useRef();
  const startRef = React.useRef();
  React.useEffect(() => {
    if (!playing) return;
    const animate = (ts) => {
      if (!startRef.current) startRef.current = ts;
      setTime(((ts - startRef.current) % duration) / duration);
      frameRef.current = requestAnimationFrame(animate);
    };
    frameRef.current = requestAnimationFrame(animate);
    return () => cancelAnimationFrame(frameRef.current);
  }, [playing, duration]);
  return { time, playing, setPlaying };
};

const Easing = {
  linear:   t => t,
  easeOut:  t => 1 - Math.pow(1 - t, 3),
  easeIn:   t => t * t * t,
  easeInOut: t => t < 0.5 ? 2*t*t : -1+(4-2*t)*t,
  spring:   t => 1 - Math.pow(Math.E, -6*t) * Math.cos(8*t),
};

// interpolate(t, fromValue, toValue, easingFn) → number
const interpolate = (t, from, to, easing = Easing.easeInOut) =>
  from + (to - from) * easing(Math.max(0, Math.min(1, t)));
```

---

## Technical Specifications

### HTML File Structure

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Descriptive Title</title>
  <style>/* All design tokens first, then component styles */</style>
</head>
<body>
  <!-- Content -->
  <script>/* JS */</script>
</body>
</html>
```

### React + Babel (Inline CDN)

Pinned-version scripts — do not update versions:
```html
<script src="https://unpkg.com/react@18.3.1/umd/react.development.js" crossorigin></script>
<script src="https://unpkg.com/react-dom@18.3.1/umd/react-dom.development.js" crossorigin></script>
<script src="https://unpkg.com/@babel/standalone@7.29.0/babel.min.js" crossorigin></script>
```

**Three hard rules for inline React:**

1. **Never `const styles = {...}`** — multiple components sharing `styles` silently overwrite each other. Namespace: `const headerStyles = {...}` or use inline `style={{...}}`.

2. **Separate `<script type="text/babel">` blocks don't share scope** — export components via `window`:
   ```jsx
   function MyComponent() { /* ... */ }
   Object.assign(window, { MyComponent });
   ```

3. **No `scrollIntoView`** — breaks in iframe preview environments. Use `element.scrollTop = N` or `window.scrollTo({top: N, behavior: 'smooth'})` instead.

### CSS Best Practices

```css
/* Use CSS Grid + Flexbox for layout — never float */
/* Manage all values through CSS custom properties */
/* Responsive: clamp() for fluid type, @container for component-level */

p, h1, h2, h3, h4 { text-wrap: pretty; }

/* Prefer brand colors; derive scale with oklch, never invent random hues */
/* @media (prefers-color-scheme) for auto dark mode */
/* @media (prefers-reduced-motion) for safe animations */
```

### CDN Resources (Load Only When Needed)

```html
<!-- Data visualization -->
<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
<script src="https://d3js.org/d3.v7.min.js"></script>

<!-- Fonts (not Inter / Roboto / Arial / system-ui as primary) -->
<link href="https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600;700&family=Newsreader:ital,wght@0,400;0,600;1,400&family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap" rel="stylesheet">

<!-- Icons: only when user provides/specifies; otherwise use placeholders -->
<script src="https://unpkg.com/lucide@latest"></script>

<!-- Tailwind: quick throwaway only — conflicts with design-token-first workflow -->
<script src="https://cdn.tailwindcss.com"></script>
```

---

## Output Type Guidelines

### Interactive Prototypes
- No title/cover screen — center in viewport, let the user see the product immediately
- Use device frames (iPhone/Android/browser window) to enhance realism
- Minimum 3 variants, toggled via the Tweaks panel
- Full state coverage: default / hover / active / focus / disabled / loading / empty / error

### HTML Slide Decks
- Fixed canvas at 1920×1080 (16:9), auto-fitted via JS `transform: scale()`
- Controls **outside** the scaled container (remain usable on small screens)
- Keyboard nav: ← → to change slides, Space for next
- Persist position in `localStorage`
- Slide numbering is 1-indexed (never confuse users with 0-indexed labels)
- `data-screen-label="01 Title"` on each `<section class="slide">`

**Responsive Slide Engine:**
```javascript
function scaleStage() {
  const stage = document.querySelector('.stage');
  const scale = Math.min(window.innerWidth / 1920, window.innerHeight / 1080);
  stage.style.transform = `scale(${scale})`;
}
window.addEventListener('resize', scaleStage);
scaleStage();
```

### Data Visualization Dashboards
- Chart.js (simple) or D3.js (complex custom) — loaded via CDN
- `ResizeObserver` on chart containers for responsiveness
- Provide dark/light toggle
- **Data-ink ratio**: remove unnecessary gridlines, 3D effects, decorative shadows
- Color encoding must carry semantic meaning; never decorative only

### Static Visual Comparisons
- Pure visual comparison (button colors, type, card styles) → use a Design Canvas layout
- Interactions / flows / multi-option → full clickable prototype + Tweaks panel

---

## Placeholder Philosophy

**When you lack icons, images, or components, a placeholder is more professional than a poorly drawn fake.**

| Missing asset | Replacement |
|---|---|
| Icon | Square + label: `[icon]`, `▢`, or a simple geometric shape |
| Avatar | Initial-letter circle with color fill |
| Image | Aspect-ratio card: `16:9 image`, `400×300` with light gray fill |
| Data | Ask the user; never fabricate |
| Logo | Brand name in text + simple geometric shape |
| Chart data | Clearly labeled sample: `[placeholder data — replace with real values]` |

A placeholder signals "real material needed here." A fake signals "I cut corners."

---

## Variant Exploration Philosophy

Providing variants is about **exhausting possibilities so the user can mix and match**, not delivering a single perfect option:

1. **Layout**: content organization (split pane / card grid / list / timeline / magazine)
2. **Visual**: color palette, typography, texture, layering, blend modes
3. **Interaction**: motion, feedback, navigation patterns
4. **Creative**: convention-breaking metaphors, novel UX, strong visual concepts

Start first variants safely within the design system; then progressively push boundaries. Show the full spectrum from "safe and functional" to "ambitious and daring."

---

## Tweaks Panel (Live Parameter Adjustment)

Add a floating parameter panel even when not requested — expose 1–2 creative parameters at minimum:

```jsx
// Minimal Tweaks panel — floating bottom-right, completely hidden when closed
const TweaksPanel = ({ open, params, onChange }) => {
  if (!open) return null;
  return (
    <div style={{
      position: 'fixed', bottom: 20, right: 20, width: 260,
      background: 'rgba(20,20,24,0.96)', backdropFilter: 'blur(12px)',
      borderRadius: 12, padding: 16, color: '#fff', fontSize: 13,
      zIndex: 9999, border: '1px solid rgba(255,255,255,0.10)'
    }}>
      <div style={{ fontWeight: 600, marginBottom: 12 }}>Tweaks</div>
      {Object.entries(params).map(([key, val]) => (
        <label key={key} style={{ display: 'flex', flexDirection: 'column', marginBottom: 10, gap: 4 }}>
          <span style={{ opacity: 0.6 }}>{key}</span>
          {typeof val === 'boolean'
            ? <input type="checkbox" checked={val} onChange={e => onChange({ ...params, [key]: e.target.checked })} />
            : typeof val === 'number'
            ? <input type="range" min={0} max={100} value={val} style={{ width: '100%' }}
                onChange={e => onChange({ ...params, [key]: +e.target.value })} />
            : <input type="text" value={val} style={{ background: 'rgba(255,255,255,0.1)', border: '1px solid rgba(255,255,255,0.2)', borderRadius: 4, padding: '4px 8px', color: '#fff' }}
                onChange={e => onChange({ ...params, [key]: e.target.value })} />
          }
        </label>
      ))}
    </div>
  );
};
```

---

## Device Frames

### iPhone Frame (React)

```jsx
const IPhoneFrame = ({ children }) => (
  <div style={{ width: 390, height: 844, borderRadius: 48, border: '12px solid #1a1a1a',
    overflow: 'hidden', position: 'relative', boxShadow: '0 25px 50px -12px rgba(0,0,0,0.25)' }}>
    <div style={{ height: 54, display: 'flex', alignItems: 'center', justifyContent: 'space-between',
      padding: '0 24px', fontSize: 14, fontWeight: 600, position: 'relative' }}>
      <span>9:41</span>
      <div style={{ width: 126, height: 34, background: '#1a1a1a', borderRadius: 20,
        position: 'absolute', left: '50%', transform: 'translateX(-50%)', top: 8 }} />
      <span style={{ fontSize: 12 }}>●●● 🔋</span>
    </div>
    <div style={{ height: 'calc(100% - 54px - 30px)', overflowY: 'auto' }}>{children}</div>
    <div style={{ position: 'absolute', bottom: 8, left: '50%', transform: 'translateX(-50%)',
      width: 134, height: 5, background: '#1a1a1a', borderRadius: 3 }} />
  </div>
);
```

### Browser Window Frame (React)

```jsx
const BrowserFrame = ({ children, url = "https://example.com" }) => (
  <div style={{ borderRadius: 12, overflow: 'hidden', boxShadow: '0 25px 50px -12px rgba(0,0,0,0.25)', border: '1px solid #e5e5e5' }}>
    <div style={{ background: '#f5f5f5', padding: '12px 16px', display: 'flex', alignItems: 'center', gap: 12, borderBottom: '1px solid #e5e5e5' }}>
      <div style={{ display: 'flex', gap: 8 }}>
        {['#ff5f57','#febc2e','#28c840'].map(c => <div key={c} style={{ width: 12, height: 12, borderRadius: '50%', background: c }} />)}
      </div>
      <div style={{ flex: 1, background: '#fff', borderRadius: 6, padding: '6px 12px', fontSize: 13, color: '#666', border: '1px solid #e0e0e0' }}>{url}</div>
    </div>
    <div>{children}</div>
  </div>
);
```

---

## Pre-delivery Checklist

All items must pass before the work is considered delivered:

- [ ] Browser console shows **no errors, no warnings**
- [ ] Renders correctly on **target devices/viewports**
- [ ] All interactive components have hover / focus / active / disabled states
- [ ] No text overflow or truncation; `text-wrap: pretty` applied
- [ ] All colors come from declared design system — **no rogue hues**
- [ ] No `scrollIntoView` (iframe-safe)
- [ ] No `const styles = {...}` in React; cross-file components exported via `window`
- [ ] No AI clichés (purple-pink gradients, emoji abuse, left-border accent cards, Inter/Roboto as hero font)
- [ ] No filler content, no fabricated data or stats
- [ ] Placeholder markers used for missing assets (`[icon]`, `[image]`)
- [ ] `@media (prefers-reduced-motion)` fallback for animations
- [ ] 5-Dimensional Self-Critique completed — all dimensions ≥ 3/5
- [ ] Visual quality at Dribbble / Behance showcase level

---

## Collaborating with the User

- **Show v0 with placeholders early** — a wrong direction caught at v0 costs 10% of the time vs at v1
- Explain decisions in **design language** ("I tightened the spacing to create a tool-like density") not technical language
- When summarizing, **only mention important caveats and next steps** — the code speaks for itself
- Offer variants and creative options so the user sees the full possibility space
- When feedback is ambiguous, **ask for clarification** before guessing

---

## Content Principles

- **No filler content** — every element must earn its place
- **Don't add sections/pages unilaterally** — if more content seems needed, ask
- **Placeholders > fabricated data** — fake data damages credibility more than admitting a gap
- **Less is more** — if the page looks empty, it's a layout problem, not a content problem
- Solve emptiness with composition, whitespace, and type-scale rhythm — not by stuffing sections

---

## DESIGN.md Schema (9 Sections)

When working within the Open Design / Claude Design ecosystem, a `DESIGN.md` file carries the portable design system. Structure it with these nine sections:

```markdown
# DESIGN.md — [Brand Name]

## 1. Colors
Primary: oklch(…) — #hex
Secondary: oklch(…) — #hex
Neutral scale: [full scale with lightness steps]
Semantic: success / warning / danger / info

## 2. Typography
Display: [font name] [weight range]
Body: [font name] [weight range]
Mono: [font name]
Scale: xs / sm / base / lg / xl / 2xl / 3xl / hero

## 3. Spacing
Base unit: 4px
Scale: 1=4px, 2=8px, 3=12px, 4=16px, 5=20px, 6=24px, 8=32px, 10=40px, 12=48px, 16=64px

## 4. Layout
Max-width content: 80rem
Max-width prose: 65ch
Grid: 12-column, 24px gutter
Breakpoints: sm=640px, md=768px, lg=1024px, xl=1280px, 2xl=1536px

## 5. Components
Button: primary / secondary / ghost / destructive + size variants
Card: default / raised / outlined
Input: default / focus / error / disabled
Badge / Tag: color variants

## 6. Motion
Default duration: 200ms
Slow duration: 350ms
Default easing: cubic-bezier(0.0, 0.0, 0.2, 1.0)
Spring: cubic-bezier(0.34, 1.56, 0.64, 1.0)
Reduced motion: disable or replace with instant transitions

## 7. Voice & Tone
Personality: [adjectives: e.g., "Confident, clear, human"]
Vocabulary: [preferred terms and terms to avoid]
Headline style: [Title Case | Sentence case]

## 8. Brand
Logo: [SVG reference or placeholder path]
Icon set: [Lucide / Heroicons / custom]
Illustration style: [geometric / isometric / line art / none]

## 9. Anti-Patterns
[List of what NOT to do in this specific design system]
```

---

## Known Design System Reference (Brand × Direction)

When the user names a product, apply its established visual language rather than inventing a generic direction:

| Brand | Visual School | Key Signals |
|---|---|---|
| **Linear** | Modern Minimal | Off-black bg, electric violet accent, Space Grotesk, dense sidebar, 2px borders |
| **Vercel** | Modern Minimal | Pure black/white, geist font, sharp edges, generous whitespace |
| **Stripe** | Premium Utility | Deep ocean blue, Inter, structured tables, corporate-clean |
| **Notion** | Soft Warm | Cream bg, minimal borders, playful emoji use, humanist sans |
| **Apple** | Editorial Minimal | SF Pro, extreme whitespace, hero product photography, gradients only for system chrome |
| **Spotify** | Dark Energetic | Pure black, electric green `#1DB954`, circular album art, motion-led |
| **Figma** | Product Craft | Brand purple `oklch(0.55 0.28 290)`, component-first thinking |
| **GitHub** | Developer Utility | Monochrome + blue, code-first density, Mona sans |
| **Airbnb** | Warm Consumer | Rausch coral `#FF5A5F`, humanist sans, photography-first |
| **Tesla** | Premium Dark | Near-black with white text, no decorative elements, cinematic photography |

---

## Advanced CSS Patterns

### Grain Texture Overlay (Film / Analog Feel)

```css
.grain::after {
  content: '';
  position: fixed;
  inset: 0;
  background-image: url("data:image/svg+xml,%3Csvg viewBox='0 0 256 256' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noise'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23noise)' opacity='0.04'/%3E%3C/svg%3E");
  pointer-events: none;
  z-index: 9998;
  opacity: 0.35;
}
```

### Ken Burns (Slow Pan on Hero Image)

```css
.hero-img {
  animation: kenBurns 24s ease-in-out infinite alternate;
}
@keyframes kenBurns {
  from { transform: scale(1.00) translate(0%, 0%); }
  to   { transform: scale(1.08) translate(-2%, -1%); }
}
```

### Masthead with `mix-blend-mode: difference` (Seamless on Any BG)

```css
.nav {
  mix-blend-mode: difference;
  color: white;            /* renders as black over white sections, white over dark */
  position: fixed;
  top: 0; left: 0; right: 0;
  z-index: 100;
}
```

### Frosted Glass Panel

```css
.glass {
  background: oklch(0.95 0.005 250 / 0.75);
  backdrop-filter: blur(20px) saturate(1.8);
  -webkit-backdrop-filter: blur(20px) saturate(1.8);
  border: 1px solid oklch(0.90 0.005 250 / 0.60);
}

/* Dark variant */
.glass-dark {
  background: oklch(0.12 0.012 250 / 0.80);
  backdrop-filter: blur(20px) saturate(1.6);
  border: 1px solid oklch(0.30 0.012 250 / 0.40);
}
```

### Responsive Type Scale with `@container`

```css
@container (min-width: 600px) {
  .card-headline {
    font-size: var(--text-2xl);
  }
}
@container (min-width: 900px) {
  .card-headline {
    font-size: var(--text-3xl);
  }
}
```

### Staggered Entry Animation (CSS)

```css
.list-item {
  opacity: 0;
  transform: translateY(12px);
  animation: slideUp 400ms var(--ease-out) forwards;
}

/* Stagger via nth-child or JS-applied delay */
.list-item:nth-child(1) { animation-delay: 0ms; }
.list-item:nth-child(2) { animation-delay: 60ms; }
.list-item:nth-child(3) { animation-delay: 120ms; }
.list-item:nth-child(4) { animation-delay: 180ms; }
/* For long lists: set --delay CSS var via JS */
```

---

## Design Canvas (Multi-Option Side-by-Side)

Use when comparing pure visual options (not flows):

```jsx
const DesignCanvas = ({ options, columns = 3 }) => (
  <div style={{ display: 'grid', gridTemplateColumns: `repeat(${columns}, 1fr)`,
    gap: 24, padding: 40, background: '#f8f9fa', minHeight: '100vh' }}>
    {options.map((opt, i) => (
      <div key={i} style={{ background: '#fff', borderRadius: 12, overflow: 'hidden',
        boxShadow: '0 1px 3px rgba(0,0,0,0.10)' }}>
        <div style={{ padding: '12px 16px', borderBottom: '1px solid #eee',
          fontSize: 13, fontWeight: 600, color: '#666' }}>
          Option {String.fromCharCode(65 + i)}: {opt.label}
        </div>
        <div style={{ padding: 16 }}>{opt.content}</div>
      </div>
    ))}
  </div>
);
```

---

## File Management

- Descriptive filenames: `Landing Page.html`, `Dashboard Prototype.html`
- Split large files (> 1000 lines) into JSX files and compose via `<script>` tags
- For major revisions: `My Design.html` → `My Design v2.html` — preserve older versions
- Multiple variants: single file + Tweaks toggles rather than separate files
- Copy assets locally before referencing — don't hotlink user-provided assets
