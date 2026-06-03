---
name: startup-vc-fundraising
description: >
  VC fundraising guidance from pre-seed through Series C+.
  Covers pitch decks, investor targeting, term sheets, cap tables, and due diligence.
skill_group: "startup-tools"
skill_category: "Startup & Business Tools"
---

# VC Fundraising Skill

Guide the user through venture capital fundraising ΓÇö from preparation to close.

## When to Use

Activate when the user:
- Plans or prepares for a fundraising round
- Builds a pitch deck or investor materials
- Researches or targets potential investors
- Negotiates a term sheet or reviews deal terms
- Models cap table dilution or SAFE/convertible notes
- Prepares a data room for due diligence
- Tracks an investor outreach pipeline

## Process

### 1. Assess Stage & Readiness
- Ask which stage: pre-seed, seed, Series A, B, or C+
- Load `reference/fundraising_stages.md` for stage-specific benchmarks
- Compare the user's metrics (ARR, growth, team size) against benchmarks
- Flag gaps and recommend what to fix before fundraising

### 2. Build Pitch Materials
- Load `reference/pitch_deck_guide.md` for the 15-slide framework
- Walk through each slide: problem, solution, market, traction, team, ask
- Review and critique existing decks slide-by-slide
- Help draft the one-pager and executive summary

### 3. Research & Target Investors
- Load `reference/investor_outreach.md` for VC research workflow
- Help build a tiered target list (100+ VCs for seed, 50+ for later rounds)
- Draft warm intro requests and cold outreach emails
- Set up pipeline tracking columns and follow-up cadence

### 4. Negotiate Terms
- Load `reference/term_sheet_guide.md` for term sheet components
- Explain each clause: valuation, liquidation preference, anti-dilution, board seats
- Flag red-flag terms (participating preferred, full ratchet, >60-day no-shop)
- Help compare multiple term sheets with a weighted scorecard

### 5. Model Cap Table & Dilution
- Load `reference/cap_table_management.md` for equity math
- Calculate pre-money/post-money ownership after the round
- Model option pool impact (pre-money vs post-money creation)
- Project founder ownership through future rounds
- Explain SAFE and convertible note conversion mechanics

### 6. Prepare for Due Diligence
- Load `reference/due_diligence_prep.md` for data room checklist
- Help organize documents into standard folders
- Draft customer reference prep materials
- Set response-time SLAs and DD timeline

### 7. Evaluate Valuation
- Load `reference/valuation_methods.md` for valuation frameworks
- Run comparable analysis using recent deals at the same stage
- Apply revenue multiples and discount rates
- Sanity-check the user's target valuation against market data

## Reference Loading

| File | Contains |
|------|----------|
| `reference/fundraising_stages.md` | Stage benchmarks: metrics, dilution, timelines, investor types |
| `reference/pitch_deck_guide.md` | 15-slide framework, design principles, slide-by-slide examples |
| `reference/term_sheet_guide.md` | Term sheet clauses, negotiation priorities, red flags |
| `reference/cap_table_management.md` | Equity types, dilution math, option pools, cap table tools |
| `reference/investor_outreach.md` | VC research, warm intros, cold emails, pipeline tracking |
| `reference/due_diligence_prep.md` | Data room folders, DD checklist, customer references |
| `reference/valuation_methods.md` | Pre/post-money, comparables, revenue multiples, SAFE math |

Load only the references needed for the current step. Do not dump entire files.

## Output Templates

### Investor Target Row
```
| Firm | Partner | Stage | Check Size | Thesis Fit | Tier | Warm Path | Status |
```

### Term Sheet Comparison
```
| Term | Sheet A | Sheet B | Preferred |
|------|---------|---------|-----------|
| Pre-money valuation | | | |
| Liquidation pref | | | |
| Anti-dilution | | | |
| Board seats | | | |
| No-shop period | | | |
```

### Dilution Snapshot
```
Round: [Seed / A / B]
Pre-money: $__M | Investment: $__M | Post-money: $__M
New investor ownership: __%
Founder ownership after: __%
Option pool: __% (pre/post-money)
```

## Integration

- **startup-business-formation**: Legal entity setup before fundraising
- **startup-product-development**: Product milestones that drive fundraising timing
- **patent-filing-ai**: IP story strengthens investor pitch
- **business-operations**: Financial reporting readiness for due diligence
- **g-task-management**: Track fundraising prep as gald3r tasks

## Key Principles

1. **Stage-appropriate** ΓÇö never recommend Series A tactics for a pre-seed founder
2. **Founder-friendly defaults** ΓÇö push for 1x non-participating, broad-based weighted average
3. **Numbers first** ΓÇö quantify everything: metrics, market size, dilution impact
4. **Honest assessment** ΓÇö flag weaknesses early so the user can fix them before pitching
5. **Speed matters** ΓÇö batch meetings, set deadlines, maintain urgency throughout the process
