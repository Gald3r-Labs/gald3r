---
subsystem_memberships: [AGENT_ORCHESTRATION]
skill_trust_level: core
---
# g-skl-agent-new - Create a new agent in your own project

Scaffolds a new subagent definition **for your project** at a location you choose. User-facing
counterpart to the maintainer-only `g-skl-gald3r-agent-new`. NEVER writes to `.gald3r_sys/`.

## Trigger Phrases
- `@g-agent-new <name>`
- "create an agent for my project", "add a subagent"

## Operations

1. **Ask where it should live** (required):
   - **(a) Platform folder** - e.g. `.cursor/agents/<name>.md`, `.claude/agents/<name>.md`.
     Offer installed platforms.
   - **(b) Repo contents** - a path the user specifies.
2. Collect: **role name**, **trigger phrases**, **owned skills/tools**, **acceptance criteria**.
3. Write the agent definition at the chosen location from this template:

```markdown
---
description: <role in one line>
---
# <Agent Display Name>

## Role
<what this agent does, when it activates, what it owns>

## Trigger Phrases
- "<phrase 1>"

## Tools / Skills
- <skill or tool the agent uses>

## Acceptance Criteria
- [ ] <criterion>
```

4. Keep the agent focused on a single, clear role.
5. Offer a CHANGELOG entry if the project keeps one.

## Related
- Command: `@g-agent-new`
- Maintainer-only (edits gald3r itself): `g-skl-gald3r-agent-new`
