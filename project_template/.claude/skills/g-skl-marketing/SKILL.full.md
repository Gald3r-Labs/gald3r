---
name: g-skl-marketing
description: >
  AI-powered marketing system for gald3r projects. Deploys specialized
  growth agents across SEO, GEO (AI search visibility), content, community,
  and launch channels. Designed for indie founders, solopreneurs, and small
  teams where distribution is the bottleneck — not building.
triggers:
  - "@g-marketing"
  - "@g-marketing-audit"
  - "@g-marketing-launch"
  - "@g-marketing-content"
  - "@g-marketing-geo"
  - "@g-marketing-reddit"
  - "@g-marketing-hn"
  - "@g-marketing-social"
  - "@g-marketing-status"
  - "marketing"
  - "distribution"
  - "launch"
  - "SEO"
  - "GEO"
  - "growth"
token_budget: medium
subsystem_memberships: [AGENT_ORCHESTRATION]
---

# g-skl-marketing — AI Growth & Distribution System

## The Core Problem This Solves

> **Building is cheap. Distribution is the bottleneck.**

AI coding tools made product creation faster than ever — days instead of months.
But marketing, SEO, community, and content stayed hard and expensive.
A proper marketing team costs $60K–$160K/year. This skill replaces the repetitive,
consistent parts of that work with always-on AI agents.

**Who this is for:**
- Solo founders and vibe coders (built the product, no idea how to get users)
- Early-stage teams (0→1 or 1→10) without a marketing budget
- Indie developers who need consistency without context-switching

---

## Modes

| Mode | Command | What It Does |
|------|---------|--------------|
| `AUDIT` | `@g-marketing-audit` | Full product/site analysis — SEO gaps, messaging, positioning |
| `GEO` | `@g-marketing-geo` | Generative Engine Optimization — get found in ChatGPT, Claude, Perplexity |
| `CONTENT` | `@g-marketing-content` | Blog post generation, evergreen content strategy |
| `REDDIT` | `@g-marketing-reddit` | Find relevant conversations + draft authentic replies |
| `HN` | `@g-marketing-hn` | Hacker News launch post — title, framing, story |
| `SOCIAL` | `@g-marketing-social` | X/Twitter content in brand voice, thread strategies |
| `LAUNCH` | `@g-marketing-launch` | Full launch sequence orchestration |
| `STATUS` | `@g-marketing-status` | Growth dashboard — channels, tasks, wins, next actions |

---

## Quick Reference: Channel Playbook

### SEO Agent
**Goal**: Get pages ranking on traditional search engines.

```
Input needed:
- Product URL or description (from PROJECT.md)
- Target audience

Output:
- Technical SEO audit (meta, headings, structured data, speed)
- Keyword gap analysis (what you should rank for vs. what you do)
- Priority fix list (ranked by impact)
- Content ideas that match search intent
```

**Key principle**: Most founders publish a page, hope for the best, and wonder
why nothing ranks. The fix is systematic: title tags, internal linking, page speed,
and writing content that matches what users actually search for.

---

### GEO Agent (Generative Engine Optimization)
**Goal**: Get discovered inside AI tools — ChatGPT, Claude, Perplexity, Gemini.

More and more users skip Google and ask AI assistants directly. If your product
isn't mentioned in AI-generated answers, you're invisible to this audience.

```
GEO Tactics:
1. Structured, factual content — AI models cite clear, verifiable facts
2. FAQ pages — AI loves Q&A format for synthesis
3. Comparison pages — "X vs Y" often surfaces in AI answers
4. Definition/explainer content — "What is [your category]?" pages
5. Authoritative backlinks — AI models weight highly-cited sources
6. Schema markup — helps AI understand what your product does
7. Use the exact language your users use when asking AI
```

**GEO Audit Checklist:**
- [ ] Does your homepage clearly state what your product does in one sentence?
- [ ] Do you have an FAQ page with questions people would ask an AI?
- [ ] Do you have at least one "comparison" page (your product vs alternatives)?
- [ ] Is your product mentioned on sites that AI models commonly cite?
- [ ] Does your structured data (JSON-LD) match your product category?

---

### Content Agent (Blog / Compound Growth)
**Goal**: Create content that compounds over time — ranks today, brings users for years.

```
Content Strategy Principles:
1. Compound > viral — one ranked post beats 10 viral posts over 12 months
2. Problem-first — write about what your users Google when they have the problem
3. Specificity wins — "how to X for Y" beats "how to X"
4. Long-form with TOC — 1,500+ words, scannable, linked internally
5. Refresh > create — updating a 6-month-old post often beats writing a new one

Content Types (by ROI):
- Tutorial: "How to [solve specific problem]" — high search intent
- Comparison: "[Product A] vs [Product B]" — buyer intent
- List: "Best tools for [use case]" — good for GEO
- Case study: "How [customer] achieved [result]" — social proof + SEO
- Opinion: "[Controversial take] about [industry trend]" — X/LinkedIn fodder
```

**Content Calendar Template:**
```
Week 1: Tutorial post (targets main search query)
Week 2: Comparison/alternative post
Week 3: Short social content batch (10 posts from week 1 post)
Week 4: GEO-optimized FAQ page
Monthly: Refresh one existing post with new data/examples
```

---

### Reddit Agent
**Goal**: Find authentic conversations to participate in — not spam, genuine help.

Reddit users detect fake marketing instantly. The play is to actually help,
while being present where your potential users already are.

```
Reddit Workflow:
1. DISCOVER — find subreddits where your target users gather
   Common: r/entrepreneur, r/SideProject, r/IndieHackers, r/startups,
   r/learnprogramming, r/webdev, r/MachineLearning (category-specific)

2. MONITOR — track keyword mentions for:
   - Your product category ("task management", "AI coding")
   - Your competitors
   - Pain point language ("frustrated with", "looking for a tool to", "any recommendations for")
   - Launch opportunities ("just launched", "show reddit")

3. ENGAGE — respond authentically:
   - Lead with help, not product
   - Only mention your product if DIRECTLY relevant
   - Add value first, mention later (or not at all)
   - "I built X to solve exactly this" is OK. "Check out my product" is not.

4. LAUNCH — r/SideProject, r/IndieHackers launch posts
   Best performing format:
   - Title: "I built [X] because [problem]"
   - Opening: The story of why you built it
   - The product: What it does, simply
   - Traction/proof: Any early users, feedback
   - Ask: What would make this better for you?
```

**Keywords to monitor** (customize per product):
```
- "[category] tool"
- "best [category] for"
- "how to [problem your product solves]"
- "alternatives to [competitor]"
- "[competitor] vs"
- "anyone built a [category]"
```

---

### Hacker News Agent
**Goal**: Write a proper HN post that gets traction, not crickets.

HN is high-leverage for developer/technical products. A good Show HN can bring
thousands of users in 48 hours. But title, framing, and explanation matter enormously.

```
Show HN Formula:
Title: "Show HN: [What it does] ([key differentiator])"
Examples:
  "Show HN: An open-source AI task manager that learns your workflow"
  "Show HN: CLI tool that turns any GitHub repo into a training dataset"
  "Show HN: We replaced our $160K/year marketing team with AI agents"

Body Structure:
1. The problem (1-2 sentences, relatable)
2. Why existing solutions suck (be honest, not disparaging)
3. What you built (clear, specific)
4. Technical decisions worth discussing (HN loves this)
5. What stage you're at (alpha, v1, launched)
6. The ask (feedback, specific questions)

HN Best Practices:
- Post early morning US East Coast (7-9 AM)
- Respond to every comment in the first 2 hours
- Don't ask for upvotes anywhere (instant credibility death)
- Answer technical questions thoroughly — show depth
- "We" not "I" reads as more credible (even if solo)
```

**Tell HN Formula** (when sharing insights, not products):
```
Title: "Tell HN: [Insight or observation]"
- Share something genuinely interesting you learned building
- Don't pitch — let the discussion drive awareness naturally
- Works well after a Show HN as follow-up engagement
```

---

### Social Agent (X / Twitter)
**Goal**: Build a consistent brand voice presence without burning hours daily.

```
Content Pillars (rotate through):
1. Building in public — share progress, mistakes, decisions
2. Hot takes — controversial (but defensible) opinions about your space
3. Tutorials — short, specific how-to content
4. Social proof — user wins, testimonials, milestones
5. Behind the scenes — technical decisions, architecture, process

Thread Templates:
"I [did X]. Here's what happened: [thread]"
"The dirty secret about [common belief in your industry]: [thread]"
"I replaced [expensive thing] with [what you built]. Here's how: [thread]"
"[N] things I wish I knew before [doing what your audience does]: [thread]"

Optimal posting:
- 1 standalone tweet/post daily (take 5 min)
- 1 thread per week (from a blog post or experience)
- Engage with 5-10 replies in your niche per day (takes ~15 min)
```

---

## Launch Sequence (Full Orchestration)

Use `@g-marketing-launch` to run this full sequence:

```
T-2 weeks: Foundation
  [ ] Audit product messaging (clarity, value prop in one sentence)
  [ ] Set up analytics (Plausible, PostHog, or similar)
  [ ] Prepare landing page (headline, benefit bullets, social proof, CTA)
  [ ] Create email capture (waitlist or early access)
  [ ] Write Show HN draft + Reddit post drafts

T-1 week: Tease
  [ ] "Building something to solve X" post (no product reveal)
  [ ] Behind-the-scenes content (screenshot, story)
  [ ] DM 10-20 potential users for feedback/beta

Launch Day:
  [ ] Show HN post (7-9 AM ET)
  [ ] Product Hunt submit (12:01 AM PST — separate campaign)
  [ ] Reddit post (r/SideProject, r/IndieHackers, category-specific)
  [ ] Twitter announcement thread
  [ ] Email early access list

Post-Launch Week:
  [ ] Respond to every HN comment, Reddit reply, tweet
  [ ] Post "Day 1 results" update (transparency = engagement)
  [ ] DM everyone who commented for feedback
  [ ] Write a blog post: "What we learned from our launch"
  [ ] Submit to newsletters in your niche
```

---

## Agent Behavior Instructions

When invoked via a mode, the agent:

1. **READS** `PROJECT.md` to understand the product, mission, and target user
2. **READS** `CONSTRAINTS.md` to understand what cannot be changed
3. **OUTPUTS** the requested artifact (audit, draft, content, etc.)
4. **LOGS** the output to `.gald3r/reports/marketing/YYYY-MM-DD_[mode].md`
5. **OPTIONALLY** creates a follow-up task if the output requires implementation

### AUDIT Mode — Full Execution

```
Step 1: Read PROJECT.md → extract: product name, target user, unique value prop
Step 2: Read PLAN.md → understand current stage (0→1 vs 1→10)
Step 3: Generate:
  - Positioning audit (is the value prop clear in one sentence?)
  - Channel recommendation (which 2-3 channels make sense for this stage?)
  - Quick-win list (5 actions that could move the needle in <1 week)
  - 30-day content plan skeleton
  - GEO readiness score (0-10, with specific fixes)
Step 4: Write to .gald3r/reports/marketing/YYYY-MM-DD_audit.md
Step 5: Offer to create tasks for the top 3 quick-wins
```

---

## Marketing Reports Folder

All marketing outputs go to `.gald3r/reports/marketing/`:
```
.gald3r/reports/marketing/
├── YYYY-MM-DD_audit.md        ← Full marketing audit
├── YYYY-MM-DD_seo.md          ← SEO recommendations
├── YYYY-MM-DD_geo.md          ← GEO audit results
├── YYYY-MM-DD_content_plan.md ← Content calendar
├── YYYY-MM-DD_hn_draft.md     ← Hacker News launch post
├── YYYY-MM-DD_reddit.md       ← Reddit conversations + drafts
└── YYYY-MM-DD_social.md       ← X/Twitter content batch
```

---

## Key Principles

1. **Leverage over perfection** — One ranked blog post is worth 100 unread tweets
2. **Distribution is now the bottleneck** — Always ask: how does this get discovered?
3. **Always-on beats burst** — Consistent daily presence compounds; one big launch fades
4. **Authentic community > broadcast** — Reddit/HN users are smart; help first, promote never
5. **GEO is the new SEO** — If AI tools can't find your product, you're invisible to AI-native users
6. **Measure ruthlessly** — If a channel isn't generating users in 30 days, deprioritize it

---

## Integration with gald3r System

- Reads `PROJECT.md` for product context (no manual input required)
- Creates tasks via `g-skl-tasks` for any action items
- Logs all reports to `.gald3r/reports/marketing/`
- Works alongside `g-skl-ideas` — marketing angles can be captured as ideas
- Compatible with `g-skl-release` — launch sequence links to release tracking

---

## See Also

- `g-skl-ideas` — Capture marketing ideas as they surface
- `g-skl-tasks` — Convert marketing audit items into tracked tasks
- `g-skl-release` — Coordinate with release planning
- `g-skl-recon-url` — Ingest competitor/market research URLs into vault
- `g-skl-recon-yt` — Ingest marketing tutorial videos into vault
