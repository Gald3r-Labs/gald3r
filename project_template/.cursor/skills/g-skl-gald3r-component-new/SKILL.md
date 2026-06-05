---
name: g-skl-gald3r-component-new
description: Scaffold a new gald3r .gald3r_sys component (skill, command, rule, agent, or hook) with correct structure and mandatory subsystem tagging.
subsystem_memberships: [PROJECT_IDENTITY_SETUP]
skill_trust_level: core
---
# g-skl-gald3r-component-new - Scaffold a new gald3r .gald3r_sys component with mandatory tagging

Creates correctly structured, tagged component files for skills, commands, rules, agents,
or hooks within the `.gald3r_sys/` canonical tree. Every scaffold includes the required
`subsystem_memberships:` (Markdown) or `# @subsystems:` (PowerShell) tag so the component
appears in `PRODUCT_SYSTEMS.md` after the next aggregation run.

## Trigger Phrases

Use via commands:
- `@g-skill-new <name> [group]` — scaffold a new skill
- `@g-command-new <name> [group]` — scaffold a new command
- `@g-rule-new <name> [group]` — scaffold a new rule

Or directly: "create a new skill called X", "scaffold a command for Y", "new rule for Z"

## Operations

### Step 1 — Gather required inputs

Before scaffolding, collect:
1. **Component name** (slug, e.g. `g-skl-my-thing`, `g-cmd-my-action`, `g-rl-38-my-rule`)
2. **Component type**: skill | command | rule | agent | hook
3. **Subsystem group** — ask the user or infer from name/description. Valid groups:
   `LOGGING_SYSTEM` | `MEMORY_AND_KNOWLEDGE` | `TASK_MANAGEMENT` | `BUG_AND_QUALITY` |
   `WORKSPACE_COORDINATION` | `PROJECT_IDENTITY_SETUP` | `PLATFORM_INTEGRATION` |
   `AGENT_ORCHESTRATION` | `RELEASE_AND_VERSIONING` | `VAULT_AND_RESEARCH` |
   `UI_AND_OUTPUT` | `SECURITY_AND_COMPLIANCE` | `UNGROUPED`
4. **One-line description** — shown in skill packs, IDE command palettes, and PRODUCT_SYSTEMS.md

If the group is unclear, default to `UNGROUPED` and flag it for follow-up.

### Step 2 — Scaffold using the correct template

Use the template for the chosen component type (see Templates section below).
Write the file to `.gald3r_sys/<type>/<name>/SKILL.md` (skills) or
`.gald3r_sys/<type>/<name>.md` (commands/agents/rules).

### Step 3 — Post-scaffold checklist

After creating the file:
- [ ] Verify `subsystem_memberships:` or `# @subsystems:` is present
- [ ] For skills and commands: remind user to run `platform_parity_sync.ps1 -Sync`
      to propagate to `.cursor/`, `.claude/`, `.agent/`, `.codex/`, `.opencode/`
- [ ] Offer to regenerate `PRODUCT_SYSTEMS.md`:
      `pwsh .gald3r_sys/scripts/aggregate_subsystems.ps1`
- [ ] Offer a CHANGELOG entry (g-rl-26 requires it for user-facing additions)

---

## Templates

### SKILL template

**File path**: `.claude/skills/g-skl-<name>/SKILL.md`
**Naming**: prefix `g-skl-`, kebab-case slug

```markdown
---
subsystem_memberships: [GROUP]
skill_trust_level: core
---
# g-skl-<name> - <One-line description>

<2-3 sentence description of what this skill does and when to use it.>

## Trigger Phrases

<Phrase 1>
<Phrase 2>

## Operations

### <Operation Name>

<Step-by-step instructions for this operation.>

## Related

- Skill: `g-skl-<related-skill>`
- Command: `@g-<related-command>`
- Task: T<NNN>
```

**Required frontmatter fields**:
- `subsystem_memberships: [GROUP]`
- `skill_trust_level: core` (use `community` for third-party / user-contributed)

**Naming conventions**:
- Folder and SKILL.md filename: `g-skl-<verb-noun>/SKILL.md`
- Trigger phrases: listed in skill SKILL.md for IDE command palette discovery
- Max recommended length: 300 lines. If longer — split into sub-skills.

---

### COMMAND template

**File path**: `.claude/commands/g-<verb>-<noun>.md`
**Naming**: prefix `g-`, verb before noun, kebab-case

```markdown
---
subsystem_memberships: [GROUP]
---
# g-<verb>-<noun> - <One-line description>

<2-3 sentence description of what this command does.>

## Usage

\`\`\`
@g-<verb>-<noun> <required-arg> [optional-arg]
\`\`\`

## Steps

1. <Step 1 description>
2. <Step 2 description>
3. <Step 3 description>

## After running

- <What to do next, if anything>

## Related

- Skill: `g-skl-<delegated-skill>` (if this command activates a skill)
- Task: T<NNN>
```

**Required frontmatter fields**: `subsystem_memberships: [GROUP]`

**Conventions**:
- Thin wrapper preferred: delegate implementation to a skill via "Activates `g-skl-X`"
- Args in angle brackets `<required>`, square brackets `[optional]`
- Max recommended length: 100 lines. Implementation lives in the skill.

---

### RULE template

**File path**: `.claude/rules/g-rl-<NN>-<slug>.md`
**Naming**: sequential rule number (check highest existing NN + 1), kebab-case slug

```markdown
---
description: "<Short description of what this rule enforces>"
globs:
alwaysApply: true
subsystem_memberships: [GROUP]
---

# <Rule Title> (g-rl-NN)

<Opening statement: when this rule fires and what it enforces.>

---

## What It Does

<Core behavior description.>

## Requirements

<Bullet list of mandatory behaviors.>

## Enforcement Table

| Rationalization | Reality |
|---|---|
| "<excuse>" | "<correct behavior>" |
```

**Required frontmatter fields**:
- `description:` — shown in IDE rule browser
- `alwaysApply: true` for ambient rules; `false` for file-pattern rules with `globs:`
- `subsystem_memberships: [GROUP]`

**Conventions**:
- Rule number must be unique. Run `ls .claude/rules/*.md | sort` to find the highest.
- Always-applied rules are injected into every AI context — keep them tight (<80 lines ideal).
- Include an Enforcement Table for common rationalizations.

---

### AGENT template

**File path**: `.claude/agents/g-agnt-<name>.md`
**Naming**: prefix `g-agnt-`, role-descriptive name

```markdown
---
subsystem_memberships: [GROUP]
---
# <Agent Display Name>

## Role

<1-2 sentence description of what this agent does, when it activates, and what it owns.>

## Trigger Phrases

- `"<phrase 1>"`
- `"<phrase 2>"`
- `@g-<command>` invocations

## Owned Skills

- `g-skl-<skill-1>` — <brief description>
- `g-skl-<skill-2>` — <brief description>

## Background

<Context, motivation, design history. What problem does this agent solve?>

## Acceptance Criteria

- [ ] <Criterion 1>
- [ ] <Criterion 2>

## Related

- Task: T<NNN>
- Skill: `g-skl-<related>`
```

**Note**: For new agents, prefer `@g-agent-hire` which runs a 4-phase research-gated
workflow ensuring uniqueness and avoiding overlap with existing agents.

---

### HOOK template

**File path**: `.claude/hooks/g-hk-<name>.ps1`
**Naming**: prefix `g-hk-`, kebab-case slug

```powershell
# g-hk-<name>.ps1 - <One-line description>
# @subsystems: GROUP
# Triggered by: <event name>
#
# <Brief explanation of what this hook checks or does.>
# Contract: reads JSON from stdin (Cursor/Claude hooks), emits { "continue": true|false } on stdout.
# Exit 0 = allow/continue, Exit 2 = block (Cursor) / deny (Claude).

$inputJson = ""
if ([Console]::IsInputRedirected) {
    try { $inputJson = [Console]::In.ReadToEnd() } catch {}
}

try {
    $event = if ($inputJson) { $inputJson | ConvertFrom-Json } else { @{} }

    # TODO: implement hook logic here

    Write-Output '{"continue": true}'
    exit 0
}
catch {
    # Fail open — never block on hook errors
    Write-Output '{"continue": true}'
    exit 0
}
```

**Note**: For new hooks, prefer `@g-create-hook <name> <event>` which scaffolds
the PS1 + companion `.md`, wires `hooks.json` for IDE events, and handles
multi-platform parity automatically.

---

## Post-scaffold: propagate to all platforms

Skills, commands, agents, and rules in `.gald3r_sys/` must be synced to IDE targets:

```powershell
# From <gald3r_source> repo root:
pwsh custom_scripts\platform_parity_sync.ps1 -Sync
```

This copies to `.cursor/`, `.claude/`, `.agent/`, `.codex/`, `.opencode/` as appropriate.

Then regenerate the component map:

```powershell
pwsh gald3r_template\.gald3r_sys\scripts\aggregate_subsystems.ps1
```

## Installing the git pre-commit enforcement hook (one-time per repo clone)

```powershell
# From <gald3r_source> repo root:
git config core.hooksPath .gald3r_sys/git-hooks
```

This wires `g-hk-component-tag-check.ps1` to run before every commit, blocking
any untagged `.gald3r_sys` component from landing.
