---
subsystem_memberships: [AGENT_ORCHESTRATION]
---
# g-agent-new - Scaffold a new agent in YOUR project

Creates a new subagent definition for your own project. You choose where it lives - your AI
platform's agents folder (e.g. `.cursor/agents/`, `.claude/agents/`) or somewhere in your repo's
contents. Never writes to `.gald3r_sys/`.

## Usage

```
@g-agent-new <name>
@g-agent-new "release-reviewer"
```

- `<name>` - role slug for the agent.

## Steps

Activates **g-skl-agent-new**.

1. Ask **where** to create it:
   - **(a) Platform folder** - e.g. `.cursor/agents/<name>.md`, `.claude/agents/<name>.md`.
   - **(b) Repo contents** - a path you specify inside your project.
2. Collect the agent's role, trigger phrases, owned skills/tools, and acceptance criteria.
3. Write the agent definition from the template at the chosen location.
4. Offer a CHANGELOG entry if your project keeps one.

## Related

- Skill: `g-skl-agent-new` (implementation)
- Maintainer-only equivalent (edits gald3r itself): `@g-gald3r-agent-new`
