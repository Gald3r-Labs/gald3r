---
description: 'Run a marketing audit (positioning, GEO, SEO, channels) via g-agnt-marketing / g-skl-marketing.'
subsystem_memberships: [AGENT_ORCHESTRATION]
execution_tier: guarded_prompt
---
# @g-marketing-audit

Run a full marketing audit of the current project.

## Usage
```
@g-marketing-audit
@g-marketing-audit --quick    # 5-minute quick scan (positioning + top 3 actions)
@g-marketing-audit --deep     # Full audit including GEO, SEO, messaging, channels
```

## What it does
1. Reads PROJECT.md and PLAN.md for product context
2. Evaluates: positioning clarity, channel fit, GEO readiness, content gaps
3. Produces a prioritized audit report in `.gald3r/reports/marketing/`
4. Offers to create tasks for top action items

## Invoke
Activate `g-agnt-marketing` and run `g-skl-marketing` in AUDIT mode.
