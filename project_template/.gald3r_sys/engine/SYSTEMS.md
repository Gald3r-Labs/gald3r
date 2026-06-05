# gald3r-engine — systems coverage

The **pattern** (established by `tasks`, factored into `systems/_base.py` for folder-backed
systems and `systems/_table.py` for single-file ones): a `systems/<x>.py` module that does
deterministic CRUD over the existing `.gald3r/` markdown, regenerates its index, and is
exposed via the `Gald3r` facade + CLI + MCP, with pytest coverage. Pure Mode-A (no LLM calls).

## ✅ Cloned — all file-backed state systems (9)

| System | Module | `.gald3r/` state | Shape | IDs |
|---|---|---|---|---|
| tasks | `systems/tasks.py` | `TASKS.md` + `tasks/<status>/` | folder + index | int `T{n}` |
| goals | `systems/goals.py` | `PROJECT.md` `## Goals` | single-file section | `G-NN` |
| bugs | `systems/bugs.py` (base) | `BUGS.md` + `bugs/<status>/` | folder + index | `BUG-NNN` |
| features | `systems/features.py` (base) | `FEATURES.md` + `features/` | flat folder + grouped index | `feat-NNN` |
| prds | `systems/prds.py` (base) | `PRDS.md` + `prds/` | flat folder + index, **C-019 freeze** | `PRD-NNN` |
| ideas | `systems/ideas.py` (table) | `IDEA_BOARD.md` | single-file table | `I-NNN` |
| vocab | `systems/vocab.py` (table) | `vocab.md` | single-file table | keyed by abbr |
| constraints | `systems/constraints.py` (table) | `CONSTRAINTS.md` index | single-file table | `C-NNN` |
| subsystems | `systems/subsystems.py` | `SUBSYSTEMS.md` + `subsystems/<name>.md` | name-keyed folder + index | keyed by name |

Each: `Gald3r` facade property, CLI subcommand(s) and/or MCP tools, and tests. **71 tests green** (incl. the prompt layer).
Two reusable bases were factored out so the clones are real clones: `_base.FolderSystem` (bugs/
features/prds/**release**) and `_table` (ideas/vocab/constraints).

## ✅ Larger file-backed systems (3) — bigger than the simple pattern, same Mode-A discipline

These are file-backed but materially larger than the 9 above; each is its own module. They were
built directly from the salvage reviews (`../reviews/`), so each one *encodes* the fix the review
called the system's signature breakage.

| System | Module | `.gald3r/` state | Core deterministic ops | Tier |
|---|---|---|---|---|
| release | `systems/release.py` (base) | `RELEASES.md` + `releases/` | create / `ship` (frozen-on-release, C-019 model) / `roadmap` / `next_target_date` (cadence math) | all |
| vault | `systems/vault.py` | `vault/` notes + `_index.yaml` + `index.md` + `log.md` | `ingest` (route-by-type) / `reindex` / `list` / `lint` — **bakes in `tags:` (D021); migrates `topics:`→`tags:` so the index can't lose the label field again** | all |
| workspace | `systems/workspace.py` | `linking/` (topology + `INBOX.md` + `workspace_manifest.yaml`) | topology r/w · the **INBOX CONFLICT gate** (`has_conflicts`) keyed to the tree that actually exists · the **single manifest VALIDATE** (was "two validators, two contracts") | **controller** |

- **release** reuses `_base.FolderSystem` (it's a folder+index system); vault and workspace are
  standalone because their state shapes (type-routed notes; nested-YAML topology + manifest) don't
  fit the flat-frontmatter base.
- **vault**'s judgment half (entity/concept extraction, classification, LLM enrichment) stays in
  `prompts/` — this module makes **no LLM calls**. The same boundary as everywhere else.
- **workspace** is **controller-tier**: the `Gald3r.workspace` facade property raises
  `PermissionError` below `controller` (it ships dormant in slim/full). Read/validate-heavy — it
  never rewrites the hand-authored manifest YAML. Verified: the **shipped** `workspace_manifest.yaml`
  stub VALIDATEs with **zero errors** through the engine's one contract.

## 🧠 Prompt / judgment layer (`src/gald3r/prompts/`)

The other side of the split: the reusable **LLM reasoning** that can't become deterministic code —
served as a centralized asset library (one canonical copy, not duplicated across `.claude/` +
`.cursor/` + 34 platforms). Same boundary as the rest of the core: it **serves** prompts, it never
**executes** them (no LLM calls), so the Mode-B harness is just another caller.

`PromptLibrary` loads markdown assets with frontmatter (`id`, `kind`, `inputs`, `tier`, `source`
provenance) and `${slot}` substitution; exposed via `Gald3r.prompts`, the `gald3r prompt list|get`
CLI, and 2 MCP tools. **9 seed assets** across every judgment family:

| id | kind | from |
|---|---|---|
| `persona.norse_pantheon` | persona | `rules/gald3r_personality.md` (the 18KB pack, condensed canonical copy) |
| `role.code_reviewer` / `role.qa_engineer` / `role.verifier` | role | the agent role briefs |
| `rubric.swot` | rubric | `g-skl-swot-review` |
| `playbook.plan` / `playbook.design` | playbook | `g-skl-plan` / `g-skl-design` |
| `voice.marketing` | voice | `g-skl-marketing` |
| `rule.code_reusability` | rule | `g-rl-04` |

Each asset is **judgment only** — the deterministic procedure was stripped (it's in `systems/*.py`).
Adding the remaining role briefs follows the identical extraction pattern.

## ✂️ Shim thinning (`../strategy/thin_shims.py`, `../strategy/CONTEXT_THINNING.md`)

The payoff of the engine: the 9 migrated skills' verbose `SKILL.md` procedure is now redundant, so it
was thinned to engine-pointers — **~88.5k tokens saved** across both trees (g-skl-tasks 77KB→1.3KB).
Self-containment preserved: the full procedure is retained in `SKILL.full.md` (reversible, both trees,
frontmatter intact). Layer-0 parity holds.

## ⏭️ NOT clones of this pattern (separate designs — see `../strategy/COMPONENT_REGISTRY.md`)

The remaining registry "systems" are **not** file-backed CRUD and so are not instances of this
pattern. They are tracked with their own Python targets and dispositions:

- **Orchestration / harness** — `pipeline/go.py`, `pipeline/swarm.py`, `pipeline/verify.py`
  (the `@g-go*` autopilot). This is **Mode B**; it drives LLM calls and belongs on the Claude
  Agent SDK. Spec for handoff: `../strategy/MODE_B_PIPELINE_SPEC.md`.
- **Remaining large integration** — `research` (recon ingestion: repo/url/docs/yt/file fetchers
  that *feed* the vault). The vault store itself is now built (above); the recon fetchers are the
  separate follow-on, and several touch the network / external tools.
- **Adapters / config / cross-cutting** — `adapters/ide/`, `adapters/output.py`, `hooks.py`,
  `context.py`, `compliance.py`, `git.py`, `scaffold.py`.

> **Scope statement:** the engine pattern has been cloned to **every file-backed state system**
> (the 9 simple + 3 larger above). The systems listed under "NOT clones" are deliberately different
> kinds of work (LLM-driving harness, prompt/judgment assets, network recon, cross-cutting plumbing)
> and are not in scope for "clone the pattern" — they are separate, individually-tracked builds.
