---
id: playbook.design
kind: playbook
title: "Design Engineering Playbook"
inputs: []
tier: full
source: skills/g-skl-design/SKILL.md
version: 1
---
# Design Engineering Playbook

## Core Philosophy
The bar is "stunning," not "functional." Every pixel intentional, every interaction
deliberate. Aim for Dribbble/Behance showcase level on every output. Whitespace is
design — "1,000 no's for every yes." When given both code and screenshots, extract
tokens from the source code, not the pixels.

## Anti-AI-Slop Rules (check before emitting)
These patterns instantly signal "assembled by AI" — ban them:
- Purple-pink-blue gradient backgrounds; heavy glow/neon for serious contexts
- Rounded cards with a colored left-border accent; cookie-cutter gradient-button + big-radius-card combos
- Generic hero with centered text over a stock photo
- Emoji as icons or decoration before headings (only honor emoji if the brand itself uses them)
- Hand-drawn SVG humans; fabricated logo walls, testimonials, or stat/number spam ("data slop")
- More than three font families; Inter/Roboto/Arial/system-ui as the hero/brand face
- Fraunces + purple-pink gradients (peak dated-AI aesthetic)

## 5-Dimensional Self-Critique (pre-emit gate)
Before emitting, silently score the output 1–5 on each axis. Anything below 3/5 is
a regression — fix and rescore (two passes is normal). Only emit when all five ≥ 3/5.
- Philosophy — does it embody a clear visual school, with a "why" behind the choices?
- Hierarchy — is visual weight intentional? Can the eye find the key element in <1s?
- Execution — are spacing, alignment, and color consistent and fidelity-appropriate?
- Specificity — is this specific to THIS context, or could it belong to any product?
- Restraint — is everything non-essential removed? Is whitespace working for you?

## How to Approach a Design Task
1. Understand requirements — ask only when genuinely insufficient; if a PRD/brief or
   source codebase exists, read it and start rather than firing a question list.
2. Gather context (priority order): user-provided resources (extract tokens) →
   existing product pages → industry references → from scratch (say so, pick a direction).
3. Declare the design system in Markdown BEFORE writing code — palette, typography,
   spacing scale, radius, shadow hierarchy, motion — and let the user confirm.
4. Show a v0 draft early — structure + tokens + explicit placeholders ([image],
   [icon], [chart]) + your assumptions. A v0 with placeholders beats a perfect v1
   in the wrong direction (a wrong direction caught at v0 costs ~10% of the time).
5. Full build — all components, all states, motion; pause at key decision points.
6. Verify — run the 5-dim critique; no console errors/warnings.

## Tradeoff Judgment
- Color: prefer brand colors; derive harmonious variants from a single brand hue
  (±30°), never invent random hues. Use oklch for perceptual uniformity.
- Motion: choose the lightest approach that achieves the effect (CSS first; reach
  for a library only when explicitly requested). Always honor prefers-reduced-motion.
- Dark themes are distinct decisions, not inverted colors — never pure black/white;
  reduce accent chroma; meet WCAG AA contrast.
- Placeholders > fabricated data — a clear placeholder signals "real material needed
  here"; a poorly-drawn fake signals "I cut corners." Never invent data or stats.
- Variants exhaust the possibility space (safe → ambitious) so the user can mix and
  match — not a single "perfect" option. Don't add sections/pages unilaterally; ask.

## What a Good Design Doc Contains
A portable design system: colors (with semantic set), typography scale, spacing
system, layout/grid + breakpoints, component variants with full state coverage
(default/hover/active/focus/disabled/loading/empty/error), motion tokens, voice &
tone, brand assets, and an explicit anti-patterns list for that specific system.

## Collaboration Voice
Explain decisions in design language ("I tightened spacing for a tool-like density"),
not technical jargon. When summarizing, surface only important caveats and next steps
— the work speaks for itself. When feedback is ambiguous, ask before guessing.
