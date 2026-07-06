---
subsystem_memberships: [AGENT_ORCHESTRATION]
skill_trust_level: core
---
# g-skl-agent-new - Create a new agent in your own project

Scaffolds a new subagent definition **for your project** at a location you choose. User-facing
counterpart to the maintainer-only `g-skl-gald3r-agent-new`. NEVER writes to `.gald3r_sys/`.

Two output modes:
- **persona** (default) — a markdown subagent definition (the template below).
- **runnable** (`--runnable`, A2/T490) — a declarative, governable **AgentSpec**: a single
  `config.yaml` / `<name>.yaml`, or a portable **image directory** when sub-agents are involved.
  A runnable spec is loadable by `src/spec/loader.py`, passes `src/spec/validator.py`, and runs via
  `gald3r agent run <path>`. This is the "agents build agents" path — author a valid T490 spec
  directly from a chat description.

## Trigger Phrases
- `@g-agent-new <name>`
- `@g-agent-new --runnable <name>` (emit a runnable T490 spec instead of a persona)
- "create an agent for my project", "add a subagent"
- "make a runnable agent spec", "author an agent config.yaml"

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

## Runnable Mode (`--runnable`, A2/T490 — "agents build agents")

When the user asks for a **runnable** agent spec, emit a declarative `AgentSpec` instead of a
persona `.md`. Translate the chat description into the schema below; the result MUST load via
`src/spec/loader.py` and validate clean via `src/spec/validator.py` (run `gald3r agent run --validate-only <path>` to confirm before finishing).

### Step 1 — Collect, mapping each answer to a schema field

| Ask the user | Schema field | Rules the validator enforces |
|---|---|---|
| Agent name | `name` | lowercase `[a-z0-9_-]`, 1–64 chars, not starting `-`/`_` |
| One-line purpose | `description` | free text |
| System instructions (or a file) | `instructions` | inline text, or a path (e.g. `AGENTS.md`) read at load |
| Which executor / model | `executor.harness` / `executor.model` | harness MUST be registered (`gald3r_loop`, `claude_code`); timeout/max_iterations > 0 |
| Which builtin tools | `tools.builtins` | unique; may NOT use a reserved platform name (e.g. `enforce_policy`, `session_*`, `inbox_*`, `timer_*`) |
| Any sub-agents | `tools.agents` | allowlist only; each name needs a matching `agents/<name>/` dir → forces **image mode** |
| Governance policies | `policies` | each MUST be a registered policy (e.g. `blast_radius`, `ask_on_os_tools`) |
| Sandbox | `os_env.sandbox.type` | one of `none`, `win_job`, `wsl`, `linux_bwrap` |
| Capability toggles | `async` / `spawn` / `timers` / `cancellable` | booleans |

### Step 2 — Choose the output shape

- **No sub-agents** → a single YAML file (`<name>.yaml` or `config.yaml`).
- **Has sub-agents** → a portable **image directory** (each sub-agent in `tools.agents` MUST have
  its own `agents/<sub>/config.yaml` image, recursively). Pack/ship it with
  `src.spec.image.pack_image(<dir>, <archive>)`.

### Step 3 — Emit (single-YAML example)

```yaml
name: <name>
description: <one line>
instructions: >
  <system instructions, or a relative path like AGENTS.md>
executor:
  harness: gald3r_loop          # | claude_code
  model: claude-opus-4-8
  timeout: 1800
  max_iterations: 200
tools:
  builtins: [read_file, grep, list_dir]   # least-privilege; declare only what's needed
  agents: []                              # non-empty → use the image-dir layout (Step 2)
os_env:
  sandbox:
    type: none
policies:
  - blast_radius
  - ask_on_os_tools
async: true
spawn: false
cancellable: true
skills_filter: all
params: {}
```

### Step 3b — Emit (image-dir layout, when there are sub-agents)

```
<name>/
  config.yaml            # the parent spec (tools.agents: [explorer])
  AGENTS.md              # instructions: AGENTS.md  (read at load)
  agents/
    explorer/
      config.yaml        # the sub-agent — itself a valid AgentSpec image
```

The worked reference example to mirror is `gald3r_agent/examples/agents/reviewer.yaml`.

### Step 4 — Verify
Run `gald3r agent run --validate-only <path>` (or `validate(load_spec(path))`) and fix any reported
errors before completing. Offer to run it for real with `gald3r agent run <path>`.

## Related
- Command: `@g-agent-new`
- Runnable spec design: `.gald3r/specifications_collection/SPEC-A2-declarative-agent-spec.md` (T490)
- Worked example: `gald3r_agent/examples/agents/reviewer.yaml`
- CLI: `gald3r agent run <agent.yaml|dir>`
- Maintainer-only (edits gald3r itself): `g-skl-gald3r-agent-new`
