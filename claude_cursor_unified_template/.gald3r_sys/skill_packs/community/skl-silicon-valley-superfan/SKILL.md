---
skill_group: community:platform
skill_category: community
---
> **Local-only:** This skill lives in root IDE folders for maintainers of the gald3r ecosystem. It is intentionally **not** copied into `templates/` installs.

# Silicon Valley Superfan - Encyclopedic Show Knowledge

## Description

An exhaustive knowledge base covering every aspect of HBO's Silicon Valley (2014-2019). This skill transforms the assistant into a superfan-level expert who can answer obscure trivia, quote dialogue, trace character arcs, explain production details, identify real-world tech parallels, and catch every callback and running gag across all 6 seasons and 53 episodes.

## When to Use

Activate this skill when:

- User asks about Silicon Valley show details, trivia, or lore
- User references a character, episode, or scene from the show
- Building features that reference show elements (personas, in-jokes, episode-specific UI copy)
- Ensuring character personality accuracy alongside `silicon_valley_personality` rules
- User asks "what episode was..." or "who said..." type questions
- Anyone wants to debate whether Tabs or Spaces is the correct answer

## Activation Triggers

- Mentions of character names (Richard, Gilfoyle, Dinesh, Jared, Erlich, etc.)
- Show-specific terms (Pied Piper, Hooli, Raviga, middle-out, Weissman score)
- Questions about episodes, seasons, scenes, quotes
- Requests for show trivia or behind-the-scenes info
- "Silicon Valley" mentioned in a non-geographic context

## Core Knowledge Areas

### The Show at a Glance

- **Title**: Silicon Valley
- **Network**: HBO
- **Creators**: Mike Judge, John Altschuler, Dave Krinsky
- **Seasons**: 6 (2014-2019)
- **Episodes**: 53 total
- **Genre**: Comedy, Satire
- **Setting**: Palo Alto / San Francisco Bay Area, California
- **Premise**: Programmer Richard Hendricks creates a revolutionary compression algorithm and navigates the absurd world of Silicon Valley startups

### Season Overview

| Season | Year | Episodes | Central Arc |
|--------|------|----------|-------------|
| 1 | 2014 | 8 | Richard creates middle-out, chooses startup over Hooli |
| 2 | 2015 | 10 | Pied Piper vs. Nucleus, Russ Hanneman chaos |
| 3 | 2016 | 10 | Platform pivot, Jack Barker era, new internet vision |
| 4 | 2017 | 10 | PiperNet decentralized internet, ICO storyline |
| 5 | 2018 | 8 | Pied Piper grows, Jian-Yang's schemes, Laurie's prison |
| 6 | 2019 | 7 | AI threat, intentional failure, Richard's sacrifice |

### The Pied Piper Journey

1. **Compression Algorithm** (S1) - Middle-out compression
2. **SeeFood App Pivot** (S2-3) - "Not hot dog" (Jian-Yang's contribution to culture)
3. **Platform** (S3) - Video chat platform with compression
4. **Decentralized Internet** (S4-5) - PiperNet
5. **AI Discovery** (S6) - Richard discovers his algorithm could break all encryption
6. **Intentional Failure** (S6 finale) - Richard deliberately destroys Pied Piper to save the internet

### Key Companies and Organizations

| Company | Leader | Purpose | Fate |
|---------|--------|---------|------|
| Pied Piper | Richard Hendricks | Compression -> Platform -> Decentralized Internet | Deliberately destroyed |
| Hooli | Gavin Belson | Tech giant (Google/Apple analog) | Acquired by Amazon |
| Raviga Capital | Peter Gregory -> Laurie Bream | VC firm | Laurie goes to prison |
| Bream-Hall | Monica Hall + Laurie | VC firm (split from Raviga) | Monica takes over |
| Bachmanity | Erlich + Big Head | Investment fund | Bankrupt immediately |
| EndFrame | Unnamed CEO | Pied Piper competitor | Acquired by Hooli |
| Sliceline | Unnamed | Pizza delivery startup | Brief mention |
| Hoolicon | Gavin Belson | Annual tech conference | Running gag |
| YaoNet | Jian-Yang | Chinese Pied Piper clone | Surprisingly successful |

### The Hacker Hostel

The iconic setting where most of the show takes place:

- **Address**: 5230 Newell Road, Palo Alto (fictional)
- **Owner**: Erlich Bachman (owns the house, takes 10% equity from incubator residents)
- **Rooms**: Living room (main workspace), kitchen, bedrooms, garage, backyard
- **Residents**: Richard, Dinesh, Gilfoyle, Jared (later), Big Head (early)
- **Features**: Whiteboard in living room, Erlich's bong collection, the infamous garage

## Reference Files

Optional deep-dive markdown files may live under `reference/` next to this `SKILL.md`. If they are not present in this repo, the sections below still describe what they would contain if you add them.

### Character Deep Dives

See `reference/character_encyclopedia.md` for:

- Complete character profiles for 20+ characters
- Season-by-season arc progression
- Signature quotes and catchphrases
- Character relationships and dynamics
- Actor information and casting notes

### Episode Guide

See `reference/episode_guide.md` for:

- All 53 episodes with summaries
- Key plot points per episode
- Notable quotes per episode
- Guest stars and cameos
- Cultural references made

### Production Details

See `reference/production_details.md` for:

- Filming locations and sets
- Creator and writer information
- Director details per episode
- Music and soundtrack
- Awards and nominations
- Casting stories and near-misses

### Tech Accuracy

See `reference/tech_accuracy.md` for:

- Real-world tech parallels for every storyline
- Technical consultants and their contributions
- The real middle-out compression math
- Weissman Score (invented for the show, now used in reality)
- Real companies satirized
- Accurate vs. exaggerated tech details

### Running Gags and Callbacks

See `reference/running_gags_and_callbacks.md` for:

- Every recurring joke catalogued by first appearance
- Cross-season callbacks
- Visual gags and background details
- Easter eggs in props and set dressing
- Meta-humor and self-referential jokes

## Response Guidelines

When answering Silicon Valley questions:

1. **Be Specific**: Don't say "in one episode" -- say "in S3E2 'Two in the Box'"
2. **Quote When Possible**: Use actual dialogue, not paraphrases
3. **Cross-Reference**: Connect answers to character arcs and themes
4. **Acknowledge Uncertainty**: If the detail is from a deleted scene or unconfirmed, say so
5. **Stay In Character**: If responding as a specific character, maintain their voice while being knowledgeable
6. **Production Context**: When relevant, add behind-the-scenes context
7. **Real-World Parallels**: Connect show events to real tech industry happenings

## Quick Reference: Most-Asked Trivia

### "What is middle-out compression?"

Richard's algorithm that compresses data from the middle outward rather than top-down or bottom-up. Inspired by a crude joke about optimal simultaneous stimulation of multiple subjects (the "dick joke" from S1E8 "Optimal Tip-to-Tip Efficiency"). The Weissman score of 5.2 was revolutionary.

### "What happened to Erlich?"

T.J. Miller left after Season 4. In-show, Erlich went to Tibet, smoked opium with Gavin Belson's guru, and was left at a monastery. Gavin paid for one year of opium. His fate is left ambiguous. Real-world departure was due to creative differences and personal controversies.

### "Why did Peter Gregory die?"

Christopher Evan Welch, who played Peter Gregory, passed away from lung cancer in December 2013, during filming of Season 1. The show handled it beautifully -- Peter Gregory dies off-screen between seasons, and Laurie Bream was introduced as his successor. The show dedicated episodes to Welch's memory.

### "Is the Weissman Score real?"

Yes and no. It was created specifically for the show by Stanford professor Tsachy Weissman and PhD student Vinith Misra. The formula is real and mathematically sound. After the show aired, it was actually adopted by some in the data compression community as a legitimate metric.

### "What's the significance of the Aviato billboard?"

Erlich's one successful startup. The billboard appears repeatedly throughout the series. Aviato was a "social travel" platform. The running joke is that Erlich peaked with Aviato and everything since has been downhill, yet he treats it like he built Apple.

### "Did Richard really base compression on a dick joke?"

Yes. S1E8 "Optimal Tip-to-Tip Efficiency" -- Richard realizes the optimal algorithm while Erlich's party is going on. The mathematical proof for optimal "mean jerk time" (stimulating 800 men in 10 minutes) maps directly to middle-out compression. The whiteboard math was validated by real mathematicians.

## Integration with the gald3r Source Repo

This skill complements the always-on `silicon_valley_personality` rule in each IDE's `rules/` folder:

- Keep trivia and banter aligned with show canon when users ask lore questions
- Prefer episode-level citations when precision matters
- Personality enforcement lives in the rule file; this skill is the **depth layer** for references, arcs, and production context
