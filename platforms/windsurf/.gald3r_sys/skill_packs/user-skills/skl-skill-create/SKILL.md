---
skill_group: workflow:ide
skill_category: user-skills
token_budget: low
---
# Creating Skills in Cursor

This skill guides you through creating effective Agent Skills for Cursor. Skills are markdown files that teach the agent how to perform specific tasks: reviewing PRs using team standards, generating commit messages in a preferred format, querying database schemas, or any specialized workflow.

## Before You Begin: Gather Requirements

Before creating a skill, gather essential information from the user about:

1. **Purpose and scope**: What specific task or workflow should this skill help with?
2. **Target location**: Should this be a personal skill (~/.cursor/skills/) or project skill (.cursor/skills/)?
3. **Trigger scenarios**: When should the agent automatically apply this skill?
4. **Key domain knowledge**: What specialized information does the agent need that it wouldn't already know?
5. **Output format preferences**: Are there specific templates, formats, or styles required?
6. **Existing patterns**: Are there existing examples or conventions to follow?
7. **Paid/OAuth service?** Does this skill wrap an API, MCP server, or service that requires authentication or charges per use?
   - **Yes** → the skill MUST include a `## Installation` section following the Skill-as-Installer pattern (see below)
   - **Credit-billed** → the skill MUST also include a Cost Confirmation gate requiring explicit user approval before each billable call

### Verbatim text from the user

If the user includes exact wording to use in the skill, respect it and use it **verbatim** in `SKILL.md` (same words, same order). Do not paraphrase, soften, or expand their copy, and do not add unrequested headings or commentary around it.

### Inferring from Context

If you have previous conversation context, infer the skill from what was discussed. You can create skills based on workflows, patterns, or domain knowledge that emerged in the conversation.

### Gathering Additional Information

If you need clarification, use the AskQuestion tool when available:

```
Example AskQuestion usage:
- "Where should this skill be stored?" with options like ["Personal (~/.cursor/skills/)", "Project (.cursor/skills/)"]
- "Should this skill include executable scripts?" with options like ["Yes", "No"]
```

If the AskQuestion tool is not available, ask these questions conversationally.

---

## Skill File Structure

### Directory Layout

Skills are stored as directories containing a `SKILL.md` file and (for gald3r `g-skl-*` skills) a companion `README.md`:

```
skill-name/
├── SKILL.md              # Required - LLM prompt body (instructions only)
├── README.md             # Required for g-skl-* skills - human-facing docs
├── reference.md          # Optional - detailed documentation
├── examples.md           # Optional - usage examples
└── scripts/              # Optional - utility scripts
    ├── validate.py
    └── helper.sh
```

### Dual-file split (T1044 / IDEA-HARVEST-137)

Every new gald3r `g-skl-*` skill ships **both** files. They have different audiences and content rules:

| File          | Audience    | Content                                                                                             |
|---------------|-------------|-----------------------------------------------------------------------------------------------------|
| `SKILL.md`    | LLM agent   | Pure prompt body — what to do, file ownership, operations, trigger phrases, exact procedural steps. |
| `README.md`   | Human dev   | What it does, when to use it, examples, related skills, GitHub-rendered overview.                   |

**Do not duplicate explanation across both.** A reader of `SKILL.md` already
has the context the LLM needs and never reads README.md; a reader of README.md
is browsing on GitHub and never reads SKILL.md. Splitting reduces SKILL.md
token cost (target ≥15% reduction once full migration completes) and makes the
skill library browsable.

See `docs/SKILLS_DUAL_FILE_RULES.md` for the full content-rules cheat sheet and
the 5 pilot skills (`g-skl-tasks`, `g-skl-bugs`, `g-skl-memory`,
`g-skl-subsystems`, `g-skl-setup`).

### Storage Locations

| Type | Path | Scope |
|------|------|-------|
| Personal | ~/.cursor/skills/skill-name/ | Available across all your projects |
| Project | .cursor/skills/skill-name/ | Shared with anyone using the repository |

**IMPORTANT**: Never create skills in `~/.cursor/skills-cursor/`. This directory is reserved for Cursor's internal built-in skills and is managed automatically by the system.

### SKILL.md Structure

Every skill requires a `SKILL.md` file with YAML frontmatter and markdown body:

```markdown
---
name: your-skill-name
description: Brief description of what this skill does and when to use it
disable-model-invocation: true
maturity: beta
allowed-tools: [file_read, shell]
requires: []
---

# Your Skill Name

## Instructions
Clear, step-by-step guidance for the agent.

## Examples
Concrete examples of using this skill.
```

Default `disable-model-invocation: true` so the skill only loads when named explicitly. Omit it only when the agent should auto-invoke from ambient context.

### Required Metadata Fields

| Field | Requirements | Purpose |
|-------|--------------|---------|
| `name` | Max 64 chars, lowercase letters/numbers/hyphens only | Unique identifier for the skill |
| `description` | Max 1024 chars, non-empty | Helps agent decide when to apply the skill |

### Optional Capability Fields (T1101)

| Field | Values | Default | Purpose |
|-------|--------|---------|---------|
| `maturity` | `production` \| `beta` \| `experimental` | `beta` | Stability signal for users; `experimental` means API may change |
| `allowed-tools` | list: `shell`, `file_read`, `file_write`, `browser`, `mcp`, `git`, `network`, `editor`, `any` | `any` | Capability boundary — tools this skill is permitted to call |
| `requires` | list: `docker`, `mcp`, `internet`, `browser`, `git`, `uv`, `node` | `[]` | Capabilities that must be available for full function; absent = degrade gracefully with warning |
| `token_budget` (T1172) | `low` \| `medium` \| `high` \| `very_high` | unset | Declared expected context contribution; lets `g-go` coordinators and `g-doctor` reason about cost before dispatching this skill |
| `skill_trust_level` (T1056) | `core` \| `community` \| `local` | unset | Provenance signal — `core` = gald3r-shipped, `community` = third-party/marketplace, `local` = user-authored in this project |

**Maturity guide**:
- `production` — core gald3r primitives (`g-skl-tasks`, `g-skl-bugs`, `g-go*`, `g-skl-git-commit`). Breaking changes go through migration path.
- `beta` — works reliably but API may change (`g-skl-memory`, `g-skl-workspace`, `g-skl-muninn`)
- `experimental` — early-stage or narrow-audience skills; breakage expected (`g-skl-comfyui`, `g-skl-curator`)

**`requires:` degradation contract**: When a required capability is absent, the skill MUST either:
1. Degrade to a file-first fallback and note it in output, OR
2. Surface a clear "Capability absent — enable X to use this skill" message and stop.

### `token_budget:` declaration (T1172)

The optional `token_budget:` frontmatter field declares the skill's expected
context contribution as a coarse ordinal — NOT an exact token count. Use it
so `g-go` coordinators, `g-doctor`, and future swarm dispatchers can make
cost-aware decisions about which skills to invoke before they consume
context.

| Value | Approximate context contribution | Example skills |
|---|---|---|
| `low` | < 5,000 tokens | `g-skl-status`, `g-skl-tasks` CREATE TASK, `g-skl-keep-it-simple`, most one-shot commands |
| `medium` | 5,000 – 20,000 tokens | `g-skl-code-review`, `g-skl-bugs` FIX BUG, `g-skl-git-commit` (with diff), `g-skl-medic` L1 |
| `high` | 20,000 – 50,000 tokens | `g-go` full pipeline, `g-skl-subsystems` full scan, `g-skl-recon-docs` FETCH |
| `very_high` | > 50,000 tokens | `g-skl-res-deep` full harvest, `g-skl-memory` cross-session ingest, multi-repo `g-go --swarm` |

**Why ordinal, not exact**: actual token usage varies per invocation (tools called,
context already loaded, model selected). The declaration is a planning hint,
not a hard contract. Future tooling MAY use it to pre-emptively warn when
the remaining context budget is insufficient for the requested skill, but
the skill is NOT obligated to abort if it exceeds the declared band.

**Authoring guidance**:
- Skills that mostly compose other skills inherit the maximum of their
  invokees — declare the maximum.
- Skills with an INGEST / QUERY split (see "Skill Pattern: Pre-Process-Once
  / Query-Many" below) typically have separate budgets per phase; in that
  case declare the higher one (INGEST) and note the QUERY budget in the
  skill body.
- When unsure, prefer the higher band. Over-declaring causes mild
  conservatism in dispatch; under-declaring causes context exhaustion.

`g-doctor` L1 triage SHOULD flag skills missing `token_budget:` as a low-
severity quality finding (`T1172` follow-up).

`g-go --swarm` skill selection SHOULD prefer `low` / `medium` skills when
available budget is constrained; this is advisory, not enforcing — the
coordinator may still pick a `high` skill if it is genuinely the right
tool, but it MUST note the budget tradeoff in its dispatch log.

### `skill_trust_level:` declaration (T1056)

The optional `skill_trust_level:` frontmatter field declares the skill's
provenance so install flows, `g-skl-setup`, and `g-doctor` can apply
appropriate vetting before the skill is loaded into context or allowed to
fire its tools.

| Value | Meaning | Authoring rule |
|---|---|---|
| `core` | Skill is shipped in `gald3r_template_*` repos or the controller's `.gald3r_sys/`. Maintained by gald3r upstream. | Only set on skills that genuinely live in the canonical template / controller. Never set on user-authored or imported skills. |
| `community` | Skill came from an external pack (marketplace, contributed pack, third-party skill repo). Treat with suspicion until vetted. | Required on any skill added via `g-skill-pack-add` from an external source. |
| `local` | Skill was authored or modified in this project's `.cursor/skills/`, `.claude/skills/`, etc., and is not synced from upstream. | Implicit default for new skills authored in-place; set explicitly when authoring guidance documents need it. |

**Phase 1 enforcement (advisory)**: `g-skl-setup` and `g-skill-pack-add`
SHOULD warn (not block) when installing a skill whose
`skill_trust_level:` is unset or `community`. The warning surfaces:

- The trust level (or `unset`)
- The source the skill came from
- A reminder that the skill's `allowed-tools:` boundary still applies
- The recommendation to inspect the skill's body before its first invocation

**Phase 2 (separate task)**: a future constraint MAY add hard-blocking for
`community` skills until the user explicitly marks them as trusted. That
is out of scope for the initial declaration.

**Authoring guidance**:
- `core` is reserved for skills that ship via the gald3r_template_* repos
  or the controller's `.gald3r_sys/skill_packs/`. Do NOT mark a skill `core`
  just because it works well — the field signals *provenance*, not quality.
- When publishing a skill to a community pack, set
  `skill_trust_level: community` in the upstream copy so downstream
  installers inherit the correct signal.
- `local` is the safe default for one-off project skills.

`g-doctor` L1 triage SHOULD flag skills missing `skill_trust_level:` as a
low-severity quality finding alongside missing `token_budget:` (`T1056`
follow-up, parallel to T1172).

---

## Writing Effective Descriptions

The description is **critical** for skill discovery. The agent uses it to decide when to apply your skill.

### Description Best Practices

1. **Write in third person** (the description is injected into the system prompt):
   - ✅ Good: "Processes Excel files and generates reports"
   - ❌ Avoid: "I can help you process Excel files"
   - ❌ Avoid: "You can use this to process Excel files"

2. **Be specific and include trigger terms**:
   - ✅ Good: "Extract text and tables from PDF files, fill forms, merge documents. Use when working with PDF files or when the user mentions PDFs, forms, or document extraction."
   - ❌ Vague: "Helps with documents"

3. **Include both WHAT and WHEN**:
   - WHAT: What the skill does (specific capabilities)
   - WHEN: When the agent should use it (trigger scenarios)

### Description Examples

```yaml
# PDF Processing
description: Extract text and tables from PDF files, fill forms, merge documents. Use when working with PDF files or when the user mentions PDFs, forms, or document extraction.

# Excel Analysis
description: Analyze Excel spreadsheets, create pivot tables, generate charts. Use when analyzing Excel files, spreadsheets, tabular data, or .xlsx files.

# Git Commit Helper
description: Generate descriptive commit messages by analyzing git diffs. Use when the user asks for help writing commit messages or reviewing staged changes.

# Code Review
description: Review code for quality, security, and best practices following team standards. Use when reviewing pull requests, code changes, or when the user asks for a code review.
```

---

## Core Authoring Principles

### 1. Concise is Key

The context window is shared with conversation history, other skills, and requests. Every token competes for space.

**Default assumption**: The agent is already very smart. Only add context it doesn't already have.

Challenge each piece of information:
- "Does the agent really need this explanation?"
- "Can I assume the agent knows this?"
- "Does this paragraph justify its token cost?"

**Good (concise)**:
```markdown
## Extract PDF text

Use pdfplumber for text extraction:

\`\`\`python
import pdfplumber

with pdfplumber.open("file.pdf") as pdf:
    text = pdf.pages[0].extract_text()
\`\`\`
```

**Bad (verbose)**:
```markdown
## Extract PDF text

PDF (Portable Document Format) files are a common file format that contains
text, images, and other content. To extract text from a PDF, you'll need to
use a library. There are many libraries available for PDF processing, but we
recommend pdfplumber because it's easy to use and handles most cases well...
```

### 2. Keep SKILL.md Under 500 Lines

For optimal performance, the main SKILL.md file should be concise. Use progressive disclosure for detailed content.

### 3. Progressive Disclosure

Put essential information in SKILL.md; detailed reference material in separate files that the agent reads only when needed.

```markdown
# PDF Processing

## Quick start
[Essential instructions here]

## Additional resources
- For complete API details, see [reference.md](reference.md)
- For usage examples, see [examples.md](examples.md)
```

**Keep references one level deep** - link directly from SKILL.md to reference files. Deeply nested references may result in partial reads.

### 4. Set Appropriate Degrees of Freedom

Match specificity to the task's fragility:

| Freedom Level | When to Use | Example |
|---------------|-------------|---------|
| **High** (text instructions) | Multiple valid approaches, context-dependent | Code review guidelines |
| **Medium** (pseudocode/templates) | Preferred pattern with acceptable variation | Report generation |
| **Low** (specific scripts) | Fragile operations, consistency critical | Database migrations |

---

## Skill-as-Installer Pattern (for paid/OAuth services)

When the skill wraps a paid or OAuth-gated service, generate an `## Installation` section using this three-state template:

```markdown
## Installation

Requires [ServiceName] [account / subscription tier].

**Agent-guided setup (runs automatically on first use):**

1. **Configured?** — check `.cursor/mcp.json` (Cursor) or `.mcp.json` (Claude) for `"service-name"` → skip if present
2. **Key found?** — check env `SERVICE_API_KEY` (or `~/.config/service/token`) → write MCP entry, continue
3. **Not set up?** — open `Start-Process "https://service.com/api-keys"` (Win) / `open "..."` (macOS),
   prompt user to paste key, then write entry to `.cursor/mcp.json` / `.mcp.json`

> **Cost gate (credit-billed services only):** before each billable call, quote model + settings,
> estimated cost, current balance, and projected balance after. Wait for explicit "go".
```

**Rules:**
- State 1 check MUST run first — never re-prompt a configured user
- State 3 browser open uses Shell tool (`Start-Process` on Windows, `open` on macOS/Linux)
- Cost gate is non-negotiable for any service that charges per call / per generation

See `higgsfield` skill for the reference implementation.

---

## Common Patterns

### Template Pattern

Provide output format templates:

```markdown
## Report structure

Use this template:

\`\`\`markdown
# [Analysis Title]

## Executive summary
[One-paragraph overview of key findings]

## Key findings
- Finding 1 with supporting data
- Finding 2 with supporting data

## Recommendations
1. Specific actionable recommendation
2. Specific actionable recommendation
\`\`\`
```

### Examples Pattern

For skills where output quality depends on seeing examples:

```markdown
## Commit message format

**Example 1:**
Input: Added user authentication with JWT tokens
Output:
\`\`\`
feat(auth): implement JWT-based authentication

Add login endpoint and token validation middleware
\`\`\`

**Example 2:**
Input: Fixed bug where dates displayed incorrectly
Output:
\`\`\`
fix(reports): correct date formatting in timezone conversion

Use UTC timestamps consistently across report generation
\`\`\`
```

### Workflow Pattern

Break complex operations into clear steps with checklists:

```markdown
## Form filling workflow

Copy this checklist and track progress:

\`\`\`
Task Progress:
- [ ] Step 1: Analyze the form
- [ ] Step 2: Create field mapping
- [ ] Step 3: Validate mapping
- [ ] Step 4: Fill the form
- [ ] Step 5: Verify output
\`\`\`

**Step 1: Analyze the form**
Run: \`python scripts/analyze_form.py input.pdf\`
...
```

### Conditional Workflow Pattern

Guide through decision points:

```markdown
## Document modification workflow

1. Determine the modification type:

   **Creating new content?** → Follow "Creation workflow" below
   **Editing existing content?** → Follow "Editing workflow" below

2. Creation workflow:
   - Use docx-js library
   - Build document from scratch
   ...
```

### Feedback Loop Pattern

For quality-critical tasks, implement validation loops:

```markdown
## Document editing process

1. Make your edits
2. **Validate immediately**: \`python scripts/validate.py output/\`
3. If validation fails:
   - Review the error message
   - Fix the issues
   - Run validation again
4. **Only proceed when validation passes**
```

---

## Utility Scripts

Pre-made scripts offer advantages over generated code:
- More reliable than generated code
- Save tokens (no code in context)
- Save time (no code generation)
- Ensure consistency across uses

```markdown
## Utility scripts

**analyze_form.py**: Extract all form fields from PDF
\`\`\`bash
python scripts/analyze_form.py input.pdf > fields.json
\`\`\`

**validate.py**: Check for errors
\`\`\`bash
python scripts/validate.py fields.json
# Returns: "OK" or lists conflicts
\`\`\`
```

Make clear whether the agent should **execute** the script (most common) or **read** it as reference.

---

## Skill Pattern: Pre-Process-Once / Query-Many (T1169)

When a skill consumes a **large input** (a repository clone, a PDF, a video,
a long document, a vault snapshot, or any source that takes meaningful time
or tokens to ingest), it SHOULD split itself into two phases:

| Phase | What it does | Cost shape |
|---|---|---|
| **INGEST** | Parse, chunk, embed, index the source once. Write the result to a cache file (vault note, `.cache/` JSON, sqlite, etc.) | Expensive but one-time |
| **QUERY** | Read the cache and answer the user's question. Re-ingestion is NOT triggered. | Cheap; can be repeated dozens of times |
| **REINDEX** | Optional explicit refresh. Force re-ingest when the source has changed. | Same cost as INGEST |

### When to apply

Apply this pattern when any of the following is true:

- The source is > ~10k tokens of raw content
- The user is likely to ask multiple follow-up questions from the same source
- Ingestion involves embedding, OCR, transcription, or external API calls
- The same source is consumed across multiple sessions

If a skill only reads a small file once per invocation, the pattern is
unnecessary overhead — apply common sense.

### Cache contract

- **Cache location**: `.gald3r/reports/cache/{skill_slug}/{source_hash}.md`
  (or `.json` if structured). The skill SHOULD declare its cache path in
  its SKILL.md "Files Owned" section.
- **Source hash**: `sha256(source_url_or_path)[:8]` is the canonical
  cache key. Two sources with the same content but different paths get
  separate caches — that is intentional; the path is part of the source
  identity.
- **No MCP dependency**: caches are file-first. A skill that requires
  the MCP backend to be online to read its cache violates the file-
  first fallback principle (`.gald3r/` learned fact #5).
- **REINDEX trigger**: an explicit user invocation (e.g. `@skill-name
  reindex <source>`), a source-changed signal (mtime diff, etag diff,
  git SHA diff), or a maintenance command. INGEST MUST NOT run silently
  during a QUERY.

### Canonical examples in gald3r

- **`g-skl-vault`** — INGEST = parse + chunk + embed a vault note into
  `vault_notes` index. QUERY = `vault_search` / `vault_read`. REINDEX =
  `vault_sync` against a specific note.
- **`g-skl-res-deep`** — INGEST = clone + structural analysis of an
  external repo into a recon report. QUERY = answer follow-up questions
  from the recon report. REINDEX = re-run on a fresh git pull or a
  newer upstream tag.
- **`g-skl-recon-docs`** — INGEST = FETCH + crawl + cache a docs URL
  into `research/platforms/`. QUERY = the revisit-check / staleness
  scan that runs at session start. REINDEX = `REFRESH_STALE` on a
  per-platform basis.

### Anti-pattern

Skills that re-read or re-parse a large source on every invocation
(e.g., re-cloning a repo on every question, re-OCR-ing a PDF on every
follow-up) are violating this pattern. They waste tokens and time and
make every QUERY feel like a fresh ingestion. Refactor them into the
INGEST / QUERY split before shipping.

### Source

T1169 / V31 harvest (Construction Drawings AI workflow `_k1jQBS4Nk8`).

---

## Anti-Patterns to Avoid

### 1. Windows-Style Paths
- ✅ Use: `scripts/helper.py`
- ❌ Avoid: `scripts\helper.py`

### 2. Too Many Options
```markdown
# Bad - confusing
"You can use pypdf, or pdfplumber, or PyMuPDF, or..."

# Good - provide a default with escape hatch
"Use pdfplumber for text extraction.
For scanned PDFs requiring OCR, use pdf2image with pytesseract instead."
```

### 3. Time-Sensitive Information
```markdown
# Bad - will become outdated
"If you're doing this before August 2025, use the old API."

# Good - use an "old patterns" section
## Current method
Use the v2 API endpoint.

## Old patterns (deprecated)
<details>
<summary>Legacy v1 API</summary>
...
</details>
```

### 4. Inconsistent Terminology
Choose one term and use it throughout:
- ✅ Always "API endpoint" (not mixing "URL", "route", "path")
- ✅ Always "field" (not mixing "box", "element", "control")

### 5. Vague Skill Names
- ✅ Good: `processing-pdfs`, `analyzing-spreadsheets`
- ❌ Avoid: `helper`, `utils`, `tools`

---

## Skill Creation Workflow

When helping a user create a skill, follow this process:

### Phase 1: Discovery

Gather information about:
1. The skill's purpose and primary use case
2. Storage location (personal vs project)
3. Trigger scenarios
4. Any specific requirements or constraints
5. Existing examples or patterns to follow

If you have access to the AskQuestion tool, use it for efficient structured gathering. Otherwise, ask conversationally.

### Phase 2: Design

1. Draft the skill name (lowercase, hyphens, max 64 chars)
2. Write a specific, third-person description
3. Outline the main sections needed
4. Identify if supporting files or scripts are needed

### Phase 3: Implementation

1. Create the directory structure
2. Write the SKILL.md file with frontmatter
3. Create any supporting reference files
4. Create any utility scripts if needed

### Phase 4: Verification

1. Verify the SKILL.md is under 500 lines
2. Check that the description is specific and includes trigger terms
3. Ensure consistent terminology throughout
4. Verify all file references are one level deep
5. Test that the skill can be discovered and applied

---

## Complete Example

Here's a complete example of a well-structured skill:

**Directory structure:**
```
code-review/
├── SKILL.md
├── STANDARDS.md
└── examples.md
```

**SKILL.md:**
```markdown
---
name: code-review
description: Review code for quality, security, and maintainability following team standards. Use when reviewing pull requests, examining code changes, or when the user asks for a code review.
---

# Code Review

## Quick Start

When reviewing code:

1. Check for correctness and potential bugs
2. Verify security best practices
3. Assess code readability and maintainability
4. Ensure tests are adequate

## Review Checklist

- [ ] Logic is correct and handles edge cases
- [ ] No security vulnerabilities (SQL injection, XSS, etc.)
- [ ] Code follows project style conventions
- [ ] Functions are appropriately sized and focused
- [ ] Error handling is comprehensive
- [ ] Tests cover the changes

## Providing Feedback

Format feedback as:
- 🔴 **Critical**: Must fix before merge
- 🟡 **Suggestion**: Consider improving
- 🟢 **Nice to have**: Optional enhancement

## Additional Resources

- For detailed coding standards, see [STANDARDS.md](STANDARDS.md)
- For example reviews, see [examples.md](examples.md)
```

---

## Cost-Guard Pattern (T844)

Skills that call paid external APIs (image generation, video generation, LLM inference, third-party services) MUST surface an estimated cost and ask for explicit confirmation before executing. This prevents surprise charges.

### Standard Cost-Guard Template

Inject this block in your SKILL.md for any credit-billed operation:

```markdown
## Cost Confirmation Gate

Before calling [Service], always surface:

> "About to [describe operation] using [Service/Model] — estimated cost: [~N credits / $X].
> Continue? (**y** = proceed · **n** = cancel · **options** = see cheaper alternatives)"

Wait for explicit confirmation. If user says **n** or hesitates → offer the Negotiate-Down flow.
```

### Negotiate-Down Flow

When a user hesitates or declines, offer cheaper alternatives before cancelling:

```markdown
## Cheaper Alternatives

If user is cost-conscious, offer in this order:
1. Lower resolution / shorter duration (e.g., 720p → 480p, 10s → 5s)
2. Cheaper model tier (e.g., standard → fast)
3. Smaller batch size (generate 1 instead of 4)
4. Cached/similar result from last generation

Present: "Here are cheaper options: [list]. Which would you prefer?"
```

### When to Apply This Pattern

- Any MCP tool that charges credits per call (Higgsfield, image gen APIs, video gen, etc.)
- Any LLM inference that costs money per token (non-free tier)
- Any batch operation with per-unit billing
- **Not needed** for free-tier tools, local models, or tools with unlimited subscription plans

### Checklist for Cost-Guarded Skills

- [ ] Cost estimate shown BEFORE the API call
- [ ] Explicit user confirmation required (y/n)
- [ ] Negotiate-down alternatives offered on hesitation
- [ ] Balance/quota check performed when API supports it
- [ ] Cost estimate included in the cancellation message ("Cancelled — no credits used")

---

## Summary Checklist

Before finalizing a skill, verify:

### Core Quality
- [ ] Description is specific and includes key terms
- [ ] Description includes both WHAT and WHEN
- [ ] Written in third person
- [ ] SKILL.md body is under 500 lines
- [ ] Consistent terminology throughout
- [ ] Examples are concrete, not abstract
- [ ] If this skill processes large inputs (repos, PDFs, docs, videos, vault snapshots), does it implement INGEST / QUERY separation per the **Pre-Process-Once / Query-Many** pattern (T1169)?

### Structure
- [ ] File references are one level deep
- [ ] Progressive disclosure used appropriately
- [ ] Workflows have clear steps
- [ ] No time-sensitive information

### If Including Scripts
- [ ] Scripts solve problems rather than punt
- [ ] Required packages are documented
- [ ] Error handling is explicit and helpful
- [ ] No Windows-style paths
