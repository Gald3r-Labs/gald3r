Start project planning: $ARGUMENTS

## What This Command Does

Guides you through creating a comprehensive project plan using the gald3r planning system.

## Planning Workflow

### 1. Scope Validation (5 Essential Questions)
Before creating any plan, I'll ask:
- **User Context**: Personal use, small team, or broader deployment?
- **Security Requirements**: Minimal, standard, enhanced, or enterprise?
- **Scalability Expectations**: Basic, moderate, high, or enterprise?
- **Feature Complexity**: Minimal, standard, feature-rich, or enterprise?
- **Integration Requirements**: Standalone, basic, standard, or enterprise?

### 2. Create PLAN.md (Product Requirements Document)
I'll generate a comprehensive PRD with:
- Product overview (title, version, summary)
- Goals (business, user, non-goals)
- User personas and roles
- Project phases with task ID ranges
- User experience flows
- Success metrics
- Technical considerations
- Milestones & sequencing
- User stories with acceptance criteria

### 3. Create PROJECT_CONTEXT.md
- Project mission statement
- Current phase and focus
- Success criteria
- Scope boundaries
- Key constraints

### 4. Create SUBSYSTEMS.md
- Component registry
- Subsystem descriptions
- Dependencies between components
- Ownership assignments

### 5. Initial Phase Documents
- Create phase files in `.gald3r/phases/`
- Link phases to PLAN.md
- Set up task ID ranges

## Phase-Based Task Organization
- **Phase 0** (Task IDs: 1-99): Setup & Infrastructure
- **Phase 1** (Task IDs: 100-199): Foundation
- **Phase 2** (Task IDs: 200-299): Core Development
- **Phase N** (Task IDs: N×100 to N×100+99): Custom phases

## Benefits
- ✅ Prevents over-engineering
- ✅ Clarifies scope and boundaries
- ✅ Aligns team on goals
- ✅ Provides clear success metrics
- ✅ Organizes work into logical phases

## For Existing Codebases
If you have existing code, I'll:
- Analyze current file structure
- Extract existing functionality
- Generate documentation from code
- Create phase documents for remaining work

## What I Need From You
- Brief project description
- Primary goals
- Target users
- Key phases (high-level)

Let's build the right thing at the right complexity level!
