---
description: "Component creation standards — subsystem tagging required on all .gald3r_sys components"
globs:
alwaysApply: true
subsystem_memberships: [PROJECT_IDENTITY_SETUP]
---

# Component Creation Standards (g-rl-38)

**Fires on every response.** When creating OR editing any component file inside `.gald3r_sys/`,
you MUST include subsystem membership tagging. Creation without tagging is a violation.

---

## Tagging Requirements by File Type

### Markdown components (skills, commands, agents, rules)

Every `.md` file created or modified in:
- `.gald3r_sys/skills/<name>/SKILL.md`
- `.gald3r_sys/commands/*.md`
- `.gald3r_sys/agents/*.md`
- `.gald3r_sys/rules/*.md`

MUST contain a YAML frontmatter block with `subsystem_memberships:`:

```markdown
---
subsystem_memberships: [GROUP_NAME]
---
```

Valid groups (from `PRODUCT_SYSTEMS.md` `defined_groups:`):

| Group | Typical component types |
|---|---|
| `LOGGING_SYSTEM` | Logging hooks, log scripts, diagnostics |
| `MEMORY_AND_KNOWLEDGE` | Memory skills, vault, learn |
| `TASK_MANAGEMENT` | Task skills, commands, agents |
| `BUG_AND_QUALITY` | Bug skills, QA, security scan |
| `WORKSPACE_COORDINATION` | WPAC skills, workspace commands |
| `PROJECT_IDENTITY_SETUP` | Setup skills, constraints, project config |
| `PLATFORM_INTEGRATION` | Platform skills, parity scripts, hooks for IDEs |
| `AGENT_ORCHESTRATION` | Agent hiring, orchestration, g-go pipeline |
| `RELEASE_AND_VERSIONING` | Release, ship, version commands |
| `VAULT_AND_RESEARCH` | Vault, recon, ingest skills |
| `UI_AND_OUTPUT` | HTML/JSON/TOON output skills |
| `SECURITY_AND_COMPLIANCE` | Security scan, compliance, audit |

If unsure: pick the closest group. `UNGROUPED` is valid only for components not yet classified —
it must be followed by a retroactive tagging within the same session.

### PowerShell components (hooks, scripts)

Every `.ps1` file created or modified in:
- `.gald3r_sys/hooks/*.ps1`
- `.gald3r_sys/scripts/*.ps1`

MUST have a `# @subsystems:` comment in the first 15 lines:

```powershell
# g-hk-my-hook.ps1 - Description
# @subsystems: GROUP_NAME
```

---

## Creation Workflow Gates (MANDATORY)

When creating a NEW component file, before writing any content:

1. **Determine the subsystem group** — check `PRODUCT_SYSTEMS.md` `defined_groups:` or use the table above
2. **Include the tag in the template** — do not create the file skeleton without the tag
3. **After creation**: offer to run `aggregate_subsystems.ps1` to update `PRODUCT_SYSTEMS.md`
4. **For skills and commands**: remind user to run `platform_parity_sync.ps1 -Sync` to propagate to all IDE targets

## Quick-reference: use creation commands

| Component type | Correct command |
|---|---|
| New skill | `@g-skill-new` |
| New command | `@g-command-new` |
| New rule | `@g-rule-new` |
| New agent | `@g-agent-hire` (existing, research-gated) |
| New hook | `@g-create-hook` (existing, multi-platform) |

These commands scaffold the correct template with tagging pre-filled.

---

## Enforcement Table

| Rationalization | Reality |
|---|---|
| "I'll add the tag after I write the content" | Add it in the template. The tag is 1 line. |
| "It's a draft/prototype skill" | Draft skills get tagged too. Tag drives PRODUCT_SYSTEMS.md. |
| "I don't know which group" | Pick the closest one and move on. UNGROUPED is a valid temporary value. |
| "The hook is small, no need to tag" | Size is irrelevant. Every script in .gald3r_sys gets tagged. |
| "I'll run aggregate_subsystems.ps1 next session" | Run it before the session ends. It takes 3 seconds. |
