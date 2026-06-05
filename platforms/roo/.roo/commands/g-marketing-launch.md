---
subsystem_memberships: [AGENT_ORCHESTRATION]
---
# @g-marketing-launch

Orchestrate a full product launch across channels.

## Usage
```
@g-marketing-launch                          # Generate full launch plan
@g-marketing-launch --channel hn             # HN-specific launch post
@g-marketing-launch --channel reddit         # Reddit launch post
@g-marketing-launch --channel ph             # Product Hunt submission copy
@g-marketing-launch --channel social         # Social announcement thread
@g-marketing-launch --sequence               # Full 2-week launch sequence
```

## What it does
1. Reads PROJECT.md for product context
2. Generates launch artifacts for each requested channel
3. Creates a 2-week launch timeline with daily actions
4. Writes outputs to `.gald3r/reports/marketing/YYYY-MM-DD_launch.md`
5. Creates tasks for each launch day action item

## Invoke
Activate `g-agnt-marketing` and run `g-skl-marketing` in LAUNCH mode.
