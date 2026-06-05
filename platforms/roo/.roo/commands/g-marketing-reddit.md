---
subsystem_memberships: [AGENT_ORCHESTRATION]
---
# @g-marketing-reddit

Find authentic Reddit conversations to participate in + draft genuine replies.

## Usage
```
@g-marketing-reddit                          # Find subreddits + keywords to monitor
@g-marketing-reddit --keywords               # Generate keyword monitoring list
@g-marketing-reddit --post                   # Write a r/SideProject or r/IndieHackers launch post
@g-marketing-reddit --reply "<thread text>"  # Draft an authentic reply to a specific thread
```

## What it does
1. Reads PROJECT.md to understand product and target audience
2. Identifies top subreddits where target users gather
3. Generates keyword monitoring list for ongoing tracking
4. Writes launch posts in "builder story" format (not sales copy)
5. Drafts authentic replies that help first, mention product only if directly relevant
6. Writes to `.gald3r/reports/marketing/YYYY-MM-DD_reddit.md`

## Critical Rule
Reddit detects fake marketing. ALWAYS:
- Lead with genuine help
- Only mention your product when DIRECTLY relevant
- Review every AI-generated reply before posting
- Use "I built X because Y" not "Check out my product"

## Invoke
Activate `g-agnt-marketing` and run `g-skl-marketing` in REDDIT mode.
