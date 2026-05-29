---
subsystem_memberships: [AGENT_ORCHESTRATION]
---
# @g-marketing-social

Generate X/Twitter (and LinkedIn) content in your brand voice.

## Usage
```
@g-marketing-social                          # Generate a week of content
@g-marketing-social --platform x             # X/Twitter only
@g-marketing-social --platform linkedin      # LinkedIn only
@g-marketing-social --thread                 # Write a full thread
@g-marketing-social --batch 10               # Generate 10 standalone posts
@g-marketing-social --repurpose <blog-url>   # Turn a blog post into 10 social posts
@g-marketing-social --milestone "<text>"     # Celebrate a milestone in your voice
```

## Content Pillars (generated in rotation)
1. Building in public — progress, mistakes, decisions
2. Hot takes — controversial but defensible opinions
3. Tutorials — short, specific how-to tips
4. Social proof — user wins, milestones, testimonials
5. Behind the scenes — technical choices, architecture

## What it does
1. Reads PROJECT.md to establish brand voice and product context
2. Generates content in a consistent, authentic-sounding voice (not generic AI)
3. Includes hashtag recommendations
4. Writes to `.gald3r/reports/marketing/YYYY-MM-DD_social.md`

## Invoke
Activate `g-agnt-marketing` and run `g-skl-marketing` in SOCIAL mode.
