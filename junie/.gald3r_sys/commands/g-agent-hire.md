---
subsystem_memberships: [AGENT_ORCHESTRATION]
---
# g-agent-hire — Research-gated new agent creation workflow

Adds a new gald3r agent through a four-phase research-gated workflow so
new agents land with quality, uniqueness, and parity baked in — rather
than being added ad hoc with overlap, unclear ownership, or trigger-phrase
collisions.

Inspired by myPKA's Nolan specialist pattern (IDEA-HARVEST-111). The
command is interactive at the REVIEW phase by design — humans approve
the contract before any IDE-target file is written.

## Usage

```
@g-agent-hire "<role description>"
@g-agent-hire "<role description>" --reference <repo-or-url>          # optional: prime research with a specific reference
@g-agent-hire "<role description>" --skill <existing-skill-id>        # optional: pre-declare an owned skill
@g-agent-hire status                                                  # show the current draft state if a hire is in progress
@g-agent-hire cancel                                                  # abort an in-progress hire and discard the draft
```

## Phases

### Phase 1 — RESEARCH

Calls `@g-skl-res-review` (or `@g-res-review`) to analyze 2-3 reference
implementations of the requested agent role.

- Pull candidates from: vault `research/recon/`, prior gald3r harvests
  (IDEA-HARVEST-* in `IDEA_BOARD.md`), and — if `--reference` was passed
  — the user-supplied reference repo or URL.
- Output: a `research_note` summarizing how 2-3 best-in-class
  implementations of this role behave (responsibilities, trigger phrases,
  failure modes, owned tools/skills).
- Surface the research summary inline to the user before moving to DRAFT.
- Hard fail this phase rather than synthesize from memory when no
  reference can be found — the point is to ground the new agent in
  observed practice, not in hallucinated norms.

### Phase 2 — DRAFT

Generates the new agent's contract, following existing gald3r agent
structure (see `.gald3r_sys/agents/g-agnt-*.md` and the AGENTS.md
"Agents" roster). Produces:

1. `.gald3r_sys/agents/g-agnt-<slug>.md` — full agent contract:
   - YAML frontmatter: `name`, `description` (third-person, includes
     trigger phrases), `model`, `tools` (allowed-tools list),
     `disable-model-invocation`
   - Body sections: **Role**, **Use proactively when:**, **Trigger
     phrases**, **Owned skills**, **Boundary**, **Estimated context impact**
2. A delta for the AGENTS.md roster table (new row in the "Agents" or
   platform-equivalent section).
3. A short rationale: which reference implementations from Phase 1
   shaped the draft.

The draft is written to a staging location only:
`.gald3r/reports/agent_drafts/<slug>_YYYYMMDD_HHMMSS.md` — not to any
IDE target directory yet.

### Phase 3 — REVIEW

Presents the draft to the user without writing to any IDE target
directory. The presentation MUST include:

- Role + responsibilities
- Trigger phrases (with a collision check — see Quality Gates below)
- Owned skills / commands the agent will dispatch
- Estimated context impact (in coarse `low` / `medium` / `high` /
  `very_high` bands, mirroring `token_budget:` in SKILL.md frontmatter
  per T1172a)
- Diff summary of what Phase 4 will write to which platform dirs

Pause for explicit user `approve` / `reject` / `revise` input. Capture
the response in the draft file's Status History.

### Phase 4 — HIRE

Only runs after explicit user approval in Phase 3. Actions:

1. Write `g-agnt-<slug>.md` to all active IDE target agent directories
   (per `.gald3r_sys/_platform_capabilities.json` — `.cursor/agents/`,
   `.claude/agents/`, `.codex/agents/`, etc. — where the platform
   supports the `agents/` primitive).
2. Append a new row to the canonical AGENTS.md roster table.
3. Run `custom_scripts/platform_parity_sync.ps1 -Sync` so external template
   member repos pick up the new agent (controller parity is owned by
   gald3r_dev — see CLAUDE.md learned fact #31).
4. Move the staged draft to
   `.gald3r/reports/agent_drafts/hired/<slug>_<ISO>.md` for audit.
5. Append a CHANGELOG.md `[Unreleased]` entry under "Added" describing
   the new agent.

## Quality Gates (enforced before Phase 4)

| Gate | Rule |
|---|---|
| Trigger-phrase uniqueness | The new agent's trigger phrases MUST NOT collide with any existing agent's trigger phrases. Scan all `g-agnt-*.md` files and the AGENTS.md roster. Collisions block the hire — revise or rename. |
| Skill ownership | The new agent MUST reference at least one owned skill (`.gald3r_sys/skills/g-skl-*/` entry). An agent with zero skill ownership is overlap with an existing role — either declare ownership or do not hire. |
| `use proactively when:` present | The agent contract MUST contain a populated `Use proactively when:` section so the model invokes it appropriately. Empty or boilerplate sections block the hire. |
| Description format | `description:` field MUST be third-person and contain trigger terms a model can match against — see [[skl-skill-create]] "Writing Effective Descriptions". |

## Notes

- `@g-skl-agent-creator` is **not** a precondition for this command —
  the skill name appears in T1017's spec but no such skill currently
  ships with gald3r. `@g-agent-hire` itself IS the workflow; future
  refactor may extract reusable phases into a `g-skl-agent-creator`
  skill, in which case this command will delegate. For now: this command
  is self-contained.
- Platform parity is intentional: an agent that exists only in
  `.cursor/` is effectively unhired for users on Claude Code, Codex,
  OpenCode, etc. The default target set is "every platform that supports
  the `agents/` primitive" as declared in
  `.gald3r_sys/_platform_capabilities.json`.
- Estimated context-impact band should be conservative — `medium`
  unless you can demonstrate the agent is reliably `low`. Over-declaring
  causes mild dispatch conservatism; under-declaring causes context
  exhaustion (same contract as `token_budget:` in SKILL.md).

## Subsystem Tagging (g-rl-38 — mandatory)

The agent file written in Phase 4 MUST include `subsystem_memberships: [GROUP]` in its YAML
frontmatter. The REVIEW phase contract template already prompts for this. If a group is not
confirmed during REVIEW, default to `AGENT_ORCHESTRATION` and flag for follow-up.
After Phase 4, offer to regenerate `PRODUCT_SYSTEMS.md`:
`pwsh .gald3r_sys/scripts/aggregate_subsystems.ps1`

## Related

- T1017 — original task spec (IDEA-HARVEST-111, myPKA Nolan specialist
  pattern).
- T1172a — `token_budget:` ordinal bands (re-used here for the
  agent's "Estimated context impact").
- `custom_scripts/platform_parity_sync.ps1` — controller parity machinery
  invoked in Phase 4.
- AGENTS.md "Agents" roster table — canonical source-of-truth for the
  active agent set.
