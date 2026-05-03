# g-skl-constraints

**Skill**: `g-skl-constraints`
**Owner**: File-centric owner of `.gald3r/CONSTRAINTS.md`
**Trigger**: `@g-constraints`, `@g-constraint-add`, `@g-constraint-check`

---

## Operations

### ADD — Create a new constraint

Use when the user wants to add a new architectural rule to the project.

**Steps**:
1. Assign the next sequential C-ID (check the Constraint Index for the highest current ID)
2. Gather the following fields from context or ask the user:
   - **Name**: 2-5 hyphenated words, descriptive
   - **Rationale**: 2-3 sentences explaining the core reason
   - **Applies to**: which files, behaviors, or agents
   - **In practice**: 3-6 specific rules
   - **Violation examples**: 2-4 concrete examples of what NOT to do
   - **Enforcement**: how/when this is checked
   - **Scope**: `local-only` (default) | `inheritable` | `shareable` | `ecosystem-wide` (see Scope Definitions below)
   - *(Optional)* **Expires at**: `YYYY-MM-DD` — date-based auto-expiry
   - *(Optional)* **Resolved when task**: task ID — auto-expires when that task reaches `[✅]`
   - *(Optional)* **Resolved when feature**: feature slug — auto-expires when feature is `shipped`
   - *(Optional)* **Resolved when**: free-text condition (human-reviewed)
   - *(Optional)* **Auto archive**: `true` (default) or `false` — if false, expiry flags but does not auto-archive
3. Add a row to `## Constraint Index`:
   ```
   | C-{ID} | active | {name} | {scope} | {one-line summary} |
   ```
4. Add a full `### C-{ID}: {name}` block in `## Constraint Definitions` following the established format (includes `**Scope**:` field and optional expiry fields)
5. Append an entry to `## Change Log`:
   ```
   | {today} | C-{ID} | Initial constraint created — {name} | user |
   ```
6. Confirm completion: "Constraint C-{ID} ({name}) added. ID it in future task YAMLs as `{slug}`."
7. **Warning**: If `scope: ecosystem-wide` AND expiry fields are set, warn: "Ecosystem-wide constraints are typically permanent. Confirm expiry is intentional."

---

### UPDATE — Modify an existing constraint

Use when an existing constraint needs to change (wording, scope, in-practice rules).

**Steps**:
1. STOP — display the current constraint text verbatim
2. State the proposed change and rationale
3. **WAIT** for explicit user approval. Required phrases: "yes", "approved", "go ahead", "confirmed", "do it"
4. Do NOT proceed on inferred agreement, silence, or conversational context alone
5. After approval: apply the change to both the `## Constraint Index` summary row and the `## Constraint Definitions` block
6. Append an entry to `## Change Log`:
   ```
   | {today} | C-{ID} | {description of change} | user |
   ```

---

### CHECK — Validate current work against active constraints

Use during `g-go-code` AC gate step (b2), or on demand before claiming a task.

**Steps**:
1. Read all rows in `## Constraint Index` where Status = `active`
2. **Expiry evaluation** (runs before violation checks):
   - For each active constraint with expiry fields:
     a. **Date check**: if `**Expires at**:` ≤ today → mark expired
     b. **Task check**: if `**Resolved when task**:` is set → read TASKS.md → if task is `[✅]` → mark expired
     c. **Feature check**: if `**Resolved when feature**:` is set → read FEATURES.md → if feature is `shipped` → mark expired
     d. **Text condition**: `**Resolved when**:` (string only, no task/feature ID) → display for human confirmation
   - When a constraint expires:
     - If `**Auto archive**:` is `true` (or absent): set `**Status**: expired`, move to `## Archived Constraints` section, remove from `## Constraint Index`, append Change Log entry
     - If `**Auto archive**: false`: flag only — `⏰ C-{id} expiry condition met — review and archive manually`
   - Report expired constraints: `⏰ C-{id} "{name}" expired — {reason}`
3. For each remaining active constraint, evaluate: does the current task/implementation potentially violate any rule?
4. Report verdicts:
   - `✅ PASS` — no conflict found
   - `⚠️ POSSIBLE` — implementation touches this area; review carefully
   - `🚫 VIOLATION` — implementation would violate this constraint
5. Any `🚫 VIOLATION` → **block task completion**; return to implementation step
6. Any `⚠️ POSSIBLE` → note it; agent must confirm the concern is addressed before marking `[🔍]`
7. For constraints with `inherited_from:` — note the origin project in the output

**Output format**:
```
EXPIRY CHECK:
  ⏰ C-016 "no-direct-oracle" expired — Task 094 [✅]
  ⏰ C-018 "mobile-view-required" — resolved_when needs human review: "Sprint policy ends"

CONSTRAINT CHECK:
  C-001 [file-first vault] (ecosystem-wide): ✅ PASS
  C-009 [12-target propagation] (local-only): ⚠️ POSSIBLE — skill added to gald3r_template_full; confirm root copies exist
  C-007 [secrets] (inheritable): ✅ PASS
  ...
```

---

### LIST — Display active constraints at session start

Use at every session start (called by `g-rl-25`) to surface the active constraint summary.

**Output format**:
```
ACTIVE CONSTRAINTS (12):
  C-001 [file-first vault] (ecosystem-wide): Vault works without Docker or MCP
  C-002 [obsidian-markdown] (local-only): Standard MD + [[wikilinks]]; tags: not topics:
  C-003 [path-via-identity] (inheritable): Resolve vault_location from .identity before writes
  ...
Full detail: .gald3r/CONSTRAINTS.md
Shareable constraints: C-001, C-010 (offer to peers on @g-pcac-sync)
Inheritable constraints: C-003, C-007 (auto-offered when spawning children)
```

Show scope in parentheses after the constraint name. If scope is missing from a constraint definition, treat it as `local-only`.

---

## Format Reference

Each constraint definition block follows this template:

```markdown
### C-{ID}: {Name}

**Status**: active | superseded | retired | expired
**Established**: YYYY-MM-DD
**Scope**: local-only | inheritable | shareable | ecosystem-wide
**Rationale**: [2-3 sentences]

**Applies to**: [files, behaviors, agents]

**In practice**:
- [Rule 1]
- [Rule 2]
- [Rule 3]

**Violation examples**:
- [Concrete example of what NOT to do]
- [Concrete example of what NOT to do]

**Enforcement**: [How/when checked — g-go-code AC gate, session start, parity sync, etc.]
```

### Optional Expiry Fields (for temporary constraints)

Add any combination of these after the core fields:

```markdown
**Expires at**: YYYY-MM-DD
**Resolved when task**: {task_id}
**Resolved when feature**: {feature_slug}
**Resolved when**: {free-text condition — human-reviewed}
**Auto archive**: true | false (default: true)
```

- `expires_at` — auto-expires on this date
- `resolved_when_task` — auto-expires when the referenced task reaches `[✅]`
- `resolved_when_feature` — auto-expires when the referenced feature is `shipped`
- `resolved_when` — free-text condition displayed for human confirmation
- `auto_archive` — if `false`, expiry flags but does NOT auto-move to archive section

**Permanent constraints** (C-001 style) should NEVER have expiry fields. Expiry is for temporary policies, migration guards, and sprint-scoped rules only.

### Inherited Constraints

For constraints propagated from a parent/peer project, add:
```markdown
**Scope**: inheritable
**Inherited from**: {parent-slug} (propagated {YYYY-MM-DD})
```
Constraints with `**Inherited from**:` are **read-only** locally. To change them, coordinate via `@g-pcac-sync` with the originating project.

---

## Constraint Scope Definitions

| Scope | Meaning | Propagation |
|-------|---------|-------------|
| `local-only` | Applies only to this project (default) | Never propagated |
| `inheritable` | Parent → children on spawn (opt-in) | Offered at `@g-pcac-spawn` time |
| `shareable` | Any linked project can opt in | Offered via `@g-pcac-sync` |
| `ecosystem-wide` | All topology members should follow | Auto-offered to all linked projects |

**Workflow for propagating constraints:**
- **At spawn**: `g-skl-pcac-spawn` lists parent's `inheritable` + `ecosystem-wide` constraints and asks "Propagate N constraints to child?"
- **At link**: `g-skl-pcac-adopt` / `g-skl-pcac-claim` offers to sync `ecosystem-wide` constraints bidirectionally
- **On update**: when a source constraint changes, owner should run `@g-pcac-sync` to notify peers with copies

**Note**: Scope defaults to `local-only` if the `**Scope**:` field is absent from a constraint definition (backward compatible).

---

## Constraint Naming Convention

New constraint names must:
- Be 2-5 hyphenated words
- Describe what the rule *enforces*, not just what it *is*
- Read naturally as a bullet point in a project README
- Be immediately understood by a developer reading it cold

**Good**: `file-first-vault`, `10-target-propagation`, `schema-before-changes`
**Bad**: `vault`, `parity`, `no-docker`

---

## Notes for Implementers

- CONSTRAINTS.md is loaded at **every session start** — it must remain a single file, fully in-context
- Never split into individual `constraints/` files — the single-file model is intentional (D028)
- The file has five sections: Governance, Constraint Index, Constraint Definitions, Archived Constraints, Change Log — do not add or remove sections
- The Change Log is append-only — the `g-go-review` agent uses it to detect unauthorized constraint changes
- **Constraint states**: `active` → `expired` (auto, via date/task/feature condition) | `deprecated` (manual) | `violated` (temporary flag). Expired constraints move to `## Archived Constraints` section (unless `auto_archive: false`)
- **Expiry is additive** — existing constraints without expiry fields are completely unaffected (backward compatible)
