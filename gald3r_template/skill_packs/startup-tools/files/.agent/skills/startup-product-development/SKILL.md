---
name: startup-product-development
description: Startup product strategy—MVP, roadmaps, stack choice, QA, build vs buy, PMF across industries.
---

# Startup Product Development Skill

> **Industry-Agnostic Product Strategy & Execution Framework**
> For software, hardware, biotech, consumer products, and B2B services

## Overview

This skill provides comprehensive product development guidance for startups across ALL industries. This is NOT code development (we have SubAgents for that) - this is PRODUCT STRATEGY, roadmap planning, MVP definition, quality assurance frameworks, and revolutionary concept exploration.

**What This Skill Covers**:
- MVP (Minimum Viable Product) definition and scoping
- Product roadmap planning and prioritization
- Technology stack selection by industry
- Industry-specific development processes
- Quality assurance frameworks
- Revolutionary concept exploration
- Build vs buy decisions
- Product-market fit assessment

**Industries Supported**:
- Software/SaaS (web, mobile, cloud, AI/ML)
- Hardware (IoT, electronics, robotics, consumer devices)
- Biotech/Pharma (diagnostics, therapeutics, medical devices)
- Consumer Products (CPG, retail, food & beverage)
- B2B Services (platforms, consulting, enterprise tools)

## When to Use This Skill

### Automatic Triggers
Use this skill automatically when user mentions:
- "product roadmap"
- "MVP" or "minimum viable product"
- "product development plan"
- "technology stack"
- "what should I build first"
- "product-market fit"
- "revolutionary product"
- Industry-specific: "prototype", "clinical trials", "manufacturing"

### Manual Invocation
- User explicitly asks for product development guidance
- User needs help defining MVP scope
- User wants to create a product roadmap
- User needs technology stack recommendations
- User is exploring revolutionary concepts

### NOT for This Skill
- Code implementation (use full-stack-developer, backend-developer, frontend-developer SubAgents)
- Bug fixing (use debugger SubAgent)
- Code review (use code-reviewer SubAgent)
- Infrastructure setup (use devops-engineer SubAgent)

## Core Capabilities

### 1. MVP Definition

**Purpose**: Define the absolute minimum product that delivers core value

**Process**:
1. Identify core problem being solved
2. List essential features (must-have)
3. Distinguish nice-to-have features
4. Define success metrics
5. Estimate timeline and resources

**Anti-Patterns to Avoid**:
- Scope creep (adding "just one more feature")
- Building for scale before validation
- Perfecting UX before testing core value
- Including features for edge cases
- Building full feature set before launch

**Reference**: See `reference/mvp_definition.md`

### 2. Product Roadmap Planning

**Purpose**: Strategic plan from vision to execution

**Framework**: Vision → Strategy → Roadmap → Backlog

**Roadmap Structure**:
- Quarterly themes (Q1-Q4)
- Monthly milestones
- Feature prioritization
- Resource allocation
- Risk mitigation

**Prioritization Methods**:
- **RICE**: Reach × Impact × Confidence ÷ Effort
- **MoSCoW**: Must have, Should have, Could have, Won't have
- **Kano Model**: Basic, Performance, Excitement features
- **Value vs Effort Matrix**: Quick wins, major projects, fill-ins, time sinks

**Reference**: See `reference/product_roadmap_planning.md`

### 3. Technology Stack Selection

**Purpose**: Choose optimal technologies for your industry and scale

**Software/SaaS Stack Decisions**:
- **Frontend**: React, Vue, Angular, Next.js, React Native, Flutter
- **Backend**: Node.js, Python (Django/Flask), Go, Java (Spring), Ruby (Rails)
- **Database**: PostgreSQL, MySQL, MongoDB, DynamoDB, Firebase
- **Hosting**: AWS, GCP, Azure, Vercel, Netlify, Railway
- **Infrastructure**: Docker, Kubernetes, Serverless, Edge computing

**Hardware Stack Decisions**:
- **Microcontrollers**: Arduino, Raspberry Pi, ESP32, STM32
- **Connectivity**: WiFi, Bluetooth, LoRa, Zigbee, Cellular (4G/5G)
- **Sensors**: Temperature, motion, pressure, optical, chemical
- **Power**: Battery (Li-ion, LiPo), solar, USB-C PD, wireless charging
- **Enclosure**: 3D printing, injection molding, CNC machining

**Biotech Stack Decisions**:
- **Lab Equipment**: PCR, sequencing, mass spec, flow cytometry
- **Reagents**: Enzymes, antibodies, cell lines, media
- **Analysis Software**: Bioinformatics pipelines, statistical tools
- **Data Management**: LIMS, ELN, cloud storage, compliance systems

**Decision Framework**:
1. Current requirements
2. Future scalability
3. Team expertise
4. Budget constraints
5. Time to market
6. Ecosystem maturity
7. Community support

**Reference**: See `reference/tech_stack_selection.md`

### 4. Industry-Specific Development

#### Software/SaaS Development

**Methodology**: Agile/Scrum for startups
- 2-week sprints
- Daily standups (async for small teams)
- Sprint planning, review, retrospective
- Continuous integration/deployment (CI/CD)

**Development Phases**:
1. **Planning**: User stories, acceptance criteria
2. **Design**: Wireframes, mockups, prototypes
3. **Development**: Code, test, review
4. **Testing**: Unit, integration, E2E, UAT
5. **Deployment**: Staging → Production
6. **Monitoring**: Analytics, error tracking, performance

**Key Practices**:
- Version control (Git + GitHub/GitLab)
- Code reviews
- Automated testing
- Feature flags
- A/B testing
- Analytics integration

**Reference**: See `reference/software_development_guide.md`

#### Hardware Development

**Development Phases**:
1. **Concept**: Sketches, block diagrams, requirements
2. **Prototype**: Breadboard, proof of concept
3. **Engineering**: Schematic design, PCB layout, firmware
4. **Pre-production**: DFM review, tooling, pilot run
5. **Manufacturing**: Mass production, quality control
6. **Distribution**: Packaging, shipping, support

**Critical Considerations**:
- **PCB Design**: 2-layer vs 4-layer, component placement, signal integrity
- **Enclosure**: CAD design, material selection, IP rating
- **Firmware**: Embedded C/C++, OTA updates, power management
- **Certifications**: FCC (US), CE (EU), UL (safety), IP ratings
- **Supply Chain**: Component sourcing, lead times, alternatives
- **Manufacturing**: Domestic vs overseas, MOQ, cost per unit

**Key Milestones**:
- Breadboard working prototype (Week 4-8)
- PCB Rev 1 (Week 8-12)
- Enclosure CAD complete (Week 12-16)
- Pre-production units (Week 20-24)
- Manufacturing pilot run (Week 28-32)

**Reference**: See `reference/hardware_development_guide.md`

#### Biotech/Pharma Development

**Development Phases**:
1. **Discovery**: Literature review, hypothesis generation
2. **Assay Development**: In vitro testing, validation
3. **Preclinical**: Animal studies, safety testing
4. **Clinical Trials**: Phase I (safety), II (efficacy), III (confirmation)
5. **Regulatory**: FDA submission (510(k), PMA, De Novo, IND, NDA)
6. **Manufacturing**: GMP facility, scale-up, quality systems

**Critical Considerations**:
- **IP Strategy**: Patents on composition, method, use
- **Regulatory Pathway**: 510(k) (Class II), PMA (Class III), De Novo (novel Class II)
- **Clinical Trial Design**: Endpoints, patient population, statistical power
- **GMP Requirements**: Manufacturing processes, quality control, documentation
- **Reimbursement**: CPT codes, payer coverage, health economics

**Timeline Realities**:
- Diagnostics: 3-5 years to market
- Medical devices: 3-7 years to market
- Therapeutics: 8-15 years to market
- Cost: $5M-$50M+ depending on complexity

**Reference**: See `reference/biotech_development_guide.md`

#### Consumer Products Development

**Development Phases**:
1. **Ideation**: Consumer insights, trend analysis
2. **Concept Testing**: Focus groups, surveys, prototypes
3. **Design**: Industrial design, packaging, branding
4. **Sampling**: Prototypes, user testing, iteration
5. **Manufacturing**: Partner selection, quality standards
6. **Launch**: Distribution, marketing, retail placement

**Critical Considerations**:
- **User-Centered Design**: Pain points, desires, behaviors
- **Rapid Prototyping**: 3D printing, mockups, MVP samples
- **Manufacturing Partners**: Alibaba, ThomasNet, local manufacturers
- **Packaging**: Shelf appeal, sustainability, cost
- **Distribution**: DTC (Shopify), Amazon, retail buyers
- **Margins**: 3-5x manufacturing cost for retail

**Key Metrics**:
- Customer acquisition cost (CAC)
- Lifetime value (LTV)
- Conversion rate
- Repeat purchase rate
- Net promoter score (NPS)

### 5. Quality Assurance Frameworks

**Purpose**: Ensure product quality before and after launch

**Testing Strategies by Industry**:

**Software/SaaS**:
- **Unit Tests**: Function/method level (80%+ coverage)
- **Integration Tests**: API endpoints, database interactions
- **E2E Tests**: User workflows (Cypress, Playwright, Selenium)
- **Performance Tests**: Load testing, stress testing
- **Security Tests**: Penetration testing, vulnerability scans
- **User Acceptance Testing (UAT)**: Beta users, feedback loops

**Hardware**:
- **Functional Testing**: Does it work as specified?
- **Environmental Testing**: Temperature, humidity, drop tests
- **Reliability Testing**: MTBF (mean time between failures)
- **Compliance Testing**: FCC, CE, UL, IP ratings
- **Manufacturing Testing**: In-circuit test (ICT), functional test
- **Field Testing**: Beta units with real users

**Biotech**:
- **Analytical Validation**: Sensitivity, specificity, accuracy, precision
- **Clinical Validation**: Clinical trials, real-world evidence
- **Manufacturing Validation**: Process validation, batch consistency
- **Stability Testing**: Shelf life, storage conditions
- **Quality Control**: Every batch, statistical process control
- **Regulatory Compliance**: FDA QSR, ISO 13485

**QA Metrics**:
- Defect density (bugs per 1000 lines of code or per unit)
- Test coverage (% code/features tested)
- Mean time to resolution (MTTR)
- Escaped defects (found in production)
- Customer satisfaction (CSAT, NPS)

**Reference**: See `reference/quality_assurance_frameworks.md`

### 6. Revolutionary Concept Exploration

**Purpose**: Validate and develop breakthrough innovations

**Innovation Frameworks**:

**First Principles Thinking**:
1. Break down problem to fundamental truths
2. Question all assumptions
3. Rebuild solution from ground up
4. Example: SpaceX reusable rockets vs traditional expendable

**Design Thinking Process**:
1. **Empathize**: Deep user understanding
2. **Define**: Problem statement
3. **Ideate**: Brainstorm solutions
4. **Prototype**: Quick mockups
5. **Test**: Validate with users

**TRIZ (Theory of Inventive Problem Solving)**:
- 40 inventive principles
- Contradiction resolution
- Technology evolution trends
- Used by Samsung, Intel, NASA

**Moonshot Validation**:
1. **Technical Feasibility**: Can it be built with existing/near-term tech?
2. **Market Validation**: Do people actually need this?
3. **Business Model**: Can it be profitable/sustainable?
4. **Competitive Moat**: What prevents copying?
5. **Timeline**: Can we build it before someone else?

**Proof of Concept (PoC)**:
- Build minimal technical demonstration
- Validate core hypothesis
- Test with target users
- Measure key metrics
- Decision point: Pivot, persevere, or kill

**Reference**: See `reference/revolutionary_concept_guide.md`

### 7. Build vs Buy Decisions

**Framework**:

**Build When**:
- Core competitive differentiator
- Unique requirements not met by existing solutions
- Long-term cost savings justify upfront investment
- Maintain control over roadmap and data
- No suitable alternatives exist

**Buy/Use Third-Party When**:
- Commodity functionality (auth, payments, email)
- Well-established market solutions exist
- Faster time to market critical
- Not core to competitive advantage
- Ongoing maintenance burden too high

**Decision Matrix**:
| Factor | Weight | Build Score | Buy Score |
|--------|--------|-------------|-----------|
| Time to Market | 0.25 | 3/10 | 9/10 |
| Cost (2 years) | 0.20 | 5/10 | 7/10 |
| Competitive Advantage | 0.25 | 9/10 | 2/10 |
| Maintenance Burden | 0.15 | 4/10 | 8/10 |
| Flexibility/Control | 0.15 | 10/10 | 5/10 |
| **Weighted Total** | **1.00** | **6.3/10** | **6.4/10** |

**Common Buy Decisions for Startups**:
- Authentication: Auth0, Firebase Auth, AWS Cognito
- Payments: Stripe, PayPal, Square
- Email: SendGrid, Mailgun, AWS SES
- Analytics: Mixpanel, Amplitude, Google Analytics
- Error Tracking: Sentry, Rollbar, Bugsnag
- Customer Support: Intercom, Zendesk, HubSpot

**Template**: See `templates/build_vs_buy_template.xlsx`

### 8. Product-Market Fit Assessment

**Indicators of Product-Market Fit**:
- Users actively seeking your product (organic demand)
- High retention rates (40%+ monthly retention)
- Word-of-mouth growth (NPS > 50)
- Users upset if product disappeared (Sean Ellis test: >40% "very disappointed")
- Scaling challenges (too much demand)

**Assessment Framework**:
1. **Measure Core Metrics**:
   - Retention cohorts (Day 1, 7, 30, 90)
   - Net Promoter Score (NPS)
   - Customer acquisition cost (CAC) vs Lifetime Value (LTV)
   - Churn rate
   - Organic vs paid growth

2. **Qualitative Signals**:
   - Unsolicited testimonials
   - Press coverage requests
   - Investor inbound interest
   - Competitor reactions

3. **Decision Framework**:
   - **No PMF yet**: Focus on iteration, user interviews, pivots
   - **Early PMF**: Double down on growth, optimize funnel
   - **Strong PMF**: Scale operations, expand team, raise capital

**Reference**: See Research & Validation Skill for detailed market research frameworks

## Available Resources

### Reference Guides (`reference/`)

1. **mvp_definition.md** (~400 lines)
   - What is MVP?
   - How to define scope
   - Common MVP mistakes
   - Success metrics
   - Examples by industry

2. **product_roadmap_planning.md** (~450 lines)
   - Vision → Strategy → Roadmap → Backlog
   - Quarterly planning frameworks
   - Prioritization methods (RICE, MoSCoW, Kano)
   - Stakeholder alignment
   - Roadmap communication

3. **tech_stack_selection.md** (~500 lines)
   - Software/SaaS stack options
   - Hardware stack options
   - Biotech stack options
   - Decision frameworks
   - Migration considerations
   - Cost analysis

4. **software_development_guide.md** (~600 lines)
   - Agile/Scrum for startups
   - Sprint planning and execution
   - CI/CD pipelines
   - Testing strategies
   - Deployment best practices
   - Development tools

5. **hardware_development_guide.md** (~550 lines)
   - Prototyping to manufacturing
   - PCB design principles
   - Enclosure design
   - Supply chain management
   - Regulatory approvals (FCC, CE, UL)
   - Quality control

6. **biotech_development_guide.md** (~600 lines)
   - R&D process
   - Clinical trial design
   - FDA regulatory pathways
   - GMP manufacturing
   - IP strategy
   - Reimbursement strategy

7. **quality_assurance_frameworks.md** (~450 lines)
   - Testing strategies by industry
   - QA processes and metrics
   - Beta testing programs
   - Quality control systems
   - Continuous improvement

8. **revolutionary_concept_guide.md** (~500 lines)
   - First principles thinking
   - Innovation frameworks (Design Thinking, TRIZ)
   - Moonshot validation
   - Technical feasibility assessment
   - Proof of concept development

### Templates (`templates/`)

1. **mvp_spec_template.md**
   - MVP feature list with priorities
   - Acceptance criteria
   - Success metrics
   - Timeline estimation

2. **product_roadmap_template.md**
   - Quarterly roadmap structure
   - Feature themes
   - Milestone definitions
   - Resource allocation

3. **tech_stack_decision_matrix.xlsx**
   - Technology comparison spreadsheet
   - Weighted scoring
   - Cost analysis
   - Decision documentation

4. **sprint_planning_template.md**
   - 2-week sprint structure
   - User stories format
   - Sprint goals and commitments
   - Retrospective format

5. **quality_checklist_template.md**
   - Pre-launch QA checklist
   - Testing coverage requirements
   - Release readiness criteria
   - By product type (software, hardware, biotech)

6. **innovation_canvas_template.md**
   - Revolutionary concept exploration
   - Assumption mapping
   - Validation plan
   - Pivot decision framework

7. **build_vs_buy_template.xlsx**
   - Decision matrix with weighted factors
   - Cost analysis (2-year TCO)
   - Risk assessment
   - Vendor comparison

### Industry Examples (`examples/`)

1. **saas_product_roadmap.md**
   - SaaS example: Project management tool
   - MVP → Beta → V1.0 → V2.0
   - Feature prioritization
   - Tech stack decisions

2. **hardware_product_roadmap.md**
   - Hardware example: Smart home device
   - Prototype → Pre-production → Manufacturing
   - Supply chain planning
   - Certification timeline

3. **biotech_product_roadmap.md**
   - Biotech example: Diagnostic test
   - R&D → Validation → Clinical → Regulatory → Launch
   - FDA pathway strategy
   - Reimbursement planning

4. **consumer_app_roadmap.md**
   - Consumer app example: Fitness tracking
   - MVP features
   - User acquisition strategy
   - Monetization roadmap

5. **b2b_service_roadmap.md**
   - B2B service example: Consulting platform
   - Service design
   - Client onboarding
   - Scaling strategy

### Utility Scripts (`scripts/`)

1. **roadmap_generator.py**
   - Generate product roadmap from feature list
   - Quarterly planning output
   - Markdown and PDF export

2. **prioritization_calculator.py**
   - RICE score calculator
   - MoSCoW categorization helper
   - Value vs Effort matrix generator

3. **tech_stack_recommender.py**
   - Technology recommendation engine
   - Based on requirements input
   - Cost and scalability analysis

4. **sprint_planner.py**
   - Generate sprint plans from backlog
   - Velocity tracking
   - Burndown chart generation

## Integration with Other Skills

### Works With:
- **Research & Validation Skill**: Market research informs product decisions
- **VC Fundraising Skill**: Product roadmap critical for pitch deck
- **Patent Filing Skill**: Product features may need IP protection
- **full-stack-developer SubAgent**: Implements software product
- **backend-developer SubAgent**: Builds APIs and services
- **frontend-developer SubAgent**: Creates user interfaces
- **devops-engineer SubAgent**: Sets up infrastructure
- **qa-engineer SubAgent**: Executes testing strategy

### Workflow Example:
1. Use this skill to define MVP and roadmap
2. Use Research & Validation to validate market need
3. Use Patent Filing if innovative features need protection
4. Use full-stack-developer to implement software
5. Use devops-engineer to deploy infrastructure
6. Use qa-engineer to execute testing
7. Use VC Fundraising with completed product roadmap

## Common Workflows

### Workflow 1: Define MVP for New Product

**User Request**: "Help me define MVP for my [industry] product"

**Skill Response**:
1. Ask clarifying questions:
   - What core problem are you solving?
   - Who is your target user?
   - What is the minimum feature set that delivers value?
   - What is your timeline constraint?
   - What resources do you have available?

2. Reference MVP definition guide

3. Generate MVP spec using template

4. Prioritize features using RICE or MoSCoW

5. Output MVP specification document

### Workflow 2: Create Product Roadmap

**User Request**: "I need a product roadmap for the next 12 months"

**Skill Response**:
1. Gather roadmap inputs:
   - Vision and strategy
   - Feature backlog
   - Resource constraints
   - Market milestones
   - Competitive pressures

2. Reference roadmap planning guide

3. Use roadmap template

4. Generate quarterly roadmap with:
   - Q1: MVP + Early Adopter Features
   - Q2: Core Feature Expansion
   - Q3: Platform/Scalability
   - Q4: Advanced Features

5. Output roadmap document

### Workflow 3: Technology Stack Selection

**User Request**: "What technology stack should I use for my [type] product?"

**Skill Response**:
1. Gather requirements:
   - Product type (web, mobile, hardware, etc.)
   - Team expertise
   - Scalability needs
   - Budget constraints
   - Time to market

2. Reference tech stack selection guide

3. Use tech stack recommender script

4. Generate comparison matrix

5. Provide recommendation with rationale

### Workflow 4: Revolutionary Concept Validation

**User Request**: "I have a revolutionary idea for [industry], how do I validate it?"

**Skill Response**:
1. Understand the concept and claimed innovation

2. Reference revolutionary concept guide

3. Apply first principles thinking

4. Assess technical feasibility

5. Design proof of concept

6. Define validation experiments

7. Create innovation canvas

8. Output validation plan

## Best Practices

### DO:
- Start with MVP - resist feature creep
- Validate with real users early and often
- Choose technologies team knows (or can learn quickly)
- Prioritize ruthlessly (RICE, MoSCoW)
- Plan in quarterly themes, execute in sprints
- Build quality in from the start
- Document decisions (especially tech stack)
- Iterate based on user feedback
- Focus on product-market fit before scaling

### DON'T:
- Build for scale before validation
- Choose trendy tech without justification
- Skip testing to save time
- Add features without user validation
- Ignore technical debt indefinitely
- Neglect regulatory requirements (hardware, biotech)
- Build commodity features (auth, payments)
- Perfect UI before validating core value
- Commit to long roadmap without flexibility

## Industry-Specific Gotchas

### Software/SaaS
- **Avoid**: Over-engineering for scale on day 1
- **Do**: Use managed services (AWS, Firebase) to move fast
- **Watch out for**: Security vulnerabilities, GDPR compliance

### Hardware
- **Avoid**: Skipping certifications (FCC, CE) until production
- **Do**: Plan for manufacturing from prototype stage
- **Watch out for**: Component lead times (can be 6+ months), supply chain disruptions

### Biotech
- **Avoid**: Underestimating regulatory timeline (add 50%)
- **Do**: Engage FDA early for pre-submission meetings
- **Watch out for**: Clinical trial recruitment, reimbursement pathway

### Consumer Products
- **Avoid**: Assuming "if you build it, they will come"
- **Do**: Validate demand before manufacturing MOQ
- **Watch out for**: Retail margins (need 3-5x manufacturing cost)

## Success Metrics

### Product Development Success Indicators:
- MVP launched within planned timeline (±20%)
- Core features validated with target users
- Product roadmap aligned with business goals
- Technology stack supports current and near-term needs
- Quality metrics meet industry standards
- Product-market fit indicators trending positive

### Process Success Indicators:
- Team aligned on priorities
- Clear decision documentation
- Minimal scope creep
- Predictable development velocity
- Low technical debt accumulation

## Getting Started

### For New Startups:
1. Read `reference/mvp_definition.md`
2. Use `templates/mvp_spec_template.md` to define your MVP
3. Review relevant industry guide (`software_development_guide.md`, `hardware_development_guide.md`, or `biotech_development_guide.md`)
4. Use `templates/product_roadmap_template.md` to plan beyond MVP
5. Reference `examples/` for your industry

### For Existing Products:
1. Assess current product-market fit
2. Review `reference/product_roadmap_planning.md`
3. Use `scripts/prioritization_calculator.py` for feature prioritization
4. Evaluate tech stack against `reference/tech_stack_selection.md`
5. Audit quality processes against `reference/quality_assurance_frameworks.md`

### For Revolutionary Concepts:
1. Read `reference/revolutionary_concept_guide.md`
2. Apply first principles thinking
3. Use `templates/innovation_canvas_template.md`
4. Design proof of concept
5. Validate with target users
6. Consider Patent Filing Skill for IP protection

## Troubleshooting

### Problem: MVP keeps growing in scope
**Solution**: Use MoSCoW prioritization - move everything except "Must Have" to post-MVP roadmap

### Problem: Can't decide on technology stack
**Solution**: Use `templates/tech_stack_decision_matrix.xlsx` with weighted criteria, bias toward team expertise

### Problem: Product roadmap too ambitious
**Solution**: Apply RICE scoring, cut bottom 50% of features, focus on quarterly themes

### Problem: How do I know if I have product-market fit?
**Solution**: Measure retention cohorts, NPS, Sean Ellis test (>40% "very disappointed" if product disappeared)

### Problem: Build vs buy decision paralysis
**Solution**: Use `templates/build_vs_buy_template.xlsx`, default to "buy" unless core competitive differentiator

## Examples in Action

### Example 1: SaaS MVP Definition
**User**: "I'm building a project management tool for remote teams"

**Skill Guidance**:
- **MVP Features** (Must Have):
  - User authentication
  - Create/edit projects
  - Create/edit tasks
  - Assign tasks to team members
  - Basic commenting
  - Email notifications
- **Post-MVP** (Should/Could Have):
  - File attachments
  - Time tracking
  - Gantt charts
  - Integrations (Slack, GitHub)
  - Mobile apps
- **Success Metrics**:
  - 100 active teams in 3 months
  - 40%+ D30 retention
  - NPS > 30
- **Timeline**: 8-12 weeks to MVP launch

### Example 2: Hardware Product Roadmap
**User**: "I'm building a smart home security camera"

**Skill Guidance**:
- **Phase 1** (Months 1-3): Breadboard prototype
  - ESP32 + camera module
  - WiFi connectivity
  - Basic motion detection
  - Stream to mobile app
- **Phase 2** (Months 4-6): PCB design + enclosure
  - Custom PCB layout
  - 3D printed enclosure design
  - Improved motion detection algorithm
  - Cloud storage integration
- **Phase 3** (Months 7-9): Pre-production
  - Final PCB revision
  - Injection molded enclosure
  - FCC/CE certification
  - Manufacturing partner selection
- **Phase 4** (Months 10-12): Manufacturing + launch
  - Pilot run (100 units)
  - Beta testing
  - Kickstarter campaign
  - Full production (1000+ units)

### Example 3: Biotech Diagnostic Development
**User**: "I'm developing a rapid diagnostic test for infectious disease"

**Skill Guidance**:
- **Phase 1** (Year 1): Assay Development
  - Literature review
  - Antibody screening
  - Lateral flow prototype
  - Analytical validation (sensitivity, specificity)
- **Phase 2** (Year 2): Clinical Validation
  - Clinical sample collection
  - Validation study (n=200-500)
  - Performance characteristics
  - Manuscript preparation
- **Phase 3** (Year 3): Regulatory + Manufacturing
  - FDA 510(k) submission
  - ISO 13485 certification
  - GMP manufacturing setup
  - Quality systems validation
- **Phase 4** (Year 4): Launch + Commercialization
  - FDA clearance received
  - Manufacturing scale-up
  - Reimbursement strategy
  - Sales and distribution

## Related Skills

- **Research & Validation Skill**: Market research, user interviews, validation studies
- **Patent Filing Skill**: IP protection for innovative product features
- **VC Fundraising Skill**: Pitch deck requires product roadmap
- **Business Planning Skill**: Product strategy informs business model
- **Resource Access Skill**: Infrastructure and tooling for development

## Version History

- **v1.0.0** (2025-11-02): Initial comprehensive product development skill for all industries

---

**Skill Type**: Reference + Templates + Scripts
**Industry Coverage**: Software, Hardware, Biotech, Consumer, B2B
**Use Case**: Product strategy, MVP definition, roadmap planning, technology selection
**Dependencies**: None (standalone skill)
**Integration**: Works with all development SubAgents and startup skills
