---
subsystem_memberships: [AGENT_ORCHESTRATION]
---
# @g-marketing-content

Generate content that compounds over time — blog posts, tutorials, comparisons.

## Usage
```
@g-marketing-content                         # Generate content ideas based on product
@g-marketing-content --type tutorial         # Write a tutorial post
@g-marketing-content --type comparison       # Write a competitor comparison post
@g-marketing-content --type casestudy        # Write a case study format
@g-marketing-content --type faq              # Generate FAQ page (good for GEO)
@g-marketing-content --calendar              # Build a 30-day content calendar
@g-marketing-content --repurpose <url>       # Repurpose an existing post into social
```

## What it does
1. Reads PROJECT.md to understand product and target audience
2. Generates SEO-optimized content that targets search intent
3. All posts include: title, meta description, H2 structure, CTAs
4. Writes to `.gald3r/reports/marketing/YYYY-MM-DD_content.md`

## Invoke
Activate `g-agnt-marketing` and run `g-skl-marketing` in CONTENT mode.
