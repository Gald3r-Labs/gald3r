---
subsystem_memberships: [AGENT_ORCHESTRATION]
---
# @g-marketing-hn

Write a proper Hacker News Show HN post — title, framing, story, technical depth.

## Usage
```
@g-marketing-hn              # Generate Show HN post (full)
@g-marketing-hn --title      # Generate 5 title options (most important element)
@g-marketing-hn --tellhn     # Write a "Tell HN" insight post instead
@g-marketing-hn --timing     # Get optimal posting time advice
```

## What it does
1. Reads PROJECT.md for product context and technical details
2. Generates 3-5 title options (title is the make-or-break element)
3. Writes the post body: problem → existing failures → your solution → technical decisions
4. Includes advice on comment engagement strategy for launch day
5. Writes to `.gald3r/reports/marketing/YYYY-MM-DD_hn_draft.md`

## Show HN Formula
```
Title: "Show HN: [What it does] ([key differentiator])"
Body:
  - The problem (1-2 sentences, relatable)
  - Why existing solutions failed you
  - What you built (clear, specific)
  - Interesting technical decisions (HN loves this)
  - Current stage
  - Specific ask for feedback
```

## Best Practices
- Post 7-9 AM US East Coast time
- Respond to every comment in first 2 hours
- Never ask for upvotes (instant credibility damage)
- Answer technical questions with depth — show you know your stuff

## Invoke
Activate `g-agnt-marketing` and run `g-skl-marketing` in HN mode.
