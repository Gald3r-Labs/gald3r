# Specification — Mode-B Pipeline (`gald3r_agent`) on the Claude Agent SDK

**Status:** specification for handoff. Not yet built.
**Audience:** an implementing agent/engineer with no access to the originating conversation.
**Prereq reading (in this repo):** `strategy/GALD3R_PYTHON_CENTRALIZATION.md` (strategy),
`gald3r-engine/SYSTEMS.md` (what the Mode-A core already does), `gald3r-engine/README.md`,
`strategy/COMPONENT_REGISTRY.md` (the `g-go*` rows + dispositions), and — critically — the gate
definitions in `gald3r/project_template/.claude/rules/g-rl-33-enforcement_catchall.md`
(the `g-go*` gates are specified there in prose; this spec turns them into code).

---

## 0. One-paragraph summary

Build `gald3r_agent` — the **Mode-B harness** that runs the agentic *loop* itself (plan → act →
verify → iterate), as opposed to the Mode-A engine which is a passive tool/state backend that
existing IDE harnesses call. Mode B is the **only** place in gald3r that makes LLM calls. It is built
on the **Claude Agent SDK**, and it reuses the finished Mode-A core unchanged — by connecting the
gald3r **MCP server** (37 deterministic tools) as its toolset and the gald3r **prompt library**
(9 judgment assets) as its reasoning. It ports the `@g-go*` autopilot family from interpreted markdown
prose into real orchestration code with deterministic guardrails. The same core later deploys behind
HTTP as `gald3r_world_tree`; `gald3r_agent` is one caller of it.

---

## 1. Why this exists / Mode A vs Mode B

| | **Mode A (built)** | **Mode B (this spec)** |
|---|---|---|
| What gald3r is | a tool + state backend | the agent that runs the loop |
| Who drives the loop | the IDE harness (Claude Code, Cursor, …) | `gald3r_agent` itself |
| LLM calls | **none** (pure deterministic core) | **yes** — this is the only place |
| Surface | `Gald3r` facade · CLI · 37 MCP tools · 9 prompt assets | the Claude Agent SDK loop |
| Today's analog | `gald3r task new`, `gald3r_task_*` MCP tool | `@g-go`, `@g-go-go` autopilot |

**Invariant that makes this clean:** the Mode-A core already assumes nothing about its caller and
makes no LLM calls. So Mode B is "just another caller" of the same MCP tools that Claude Code calls.
Do **not** add LLM calls to `gald3r-engine/src/gald3r/` — all model interaction lives in the new
`pipeline/` package.

---

## 2. What `@g-go*` does today (the behavior to port)

These are currently `command` + `skill` markdown (disposition `code+prompt` in the registry). Port the
*orchestration* to code; keep the *judgment* steps as prompt-library fetches.

| Command | Behavior |
|---|---|
| `g-go-code` | Take a pending task → lock an implementation plan (`playbook.plan`) → implement → run the AC gate → mark awaiting-verification. |
| `g-go-review` | Adversarial review of a task awaiting verification by a **fresh** reviewer identity (`role.verifier` + `role.code_reviewer`) → PASS (`[✅]`) or FAIL back to `[📋]` with reasons. |
| `g-go` | Phase 1 `g-go-code` → Phase 2 fresh-reviewer `g-go-review` for one task. |
| `g-go-go` | Autopilot: loop `g-go` over the task queue until empty / budget / stop, fire-and-forget. |
| `g-go-*-swarm` | Fan out buckets of independent tasks to parallel sub-agents (SDK subagents), then a coordinator reconciles and does all shared `.gald3r/` writes in one pass. |

The swarm "report-back" contract: bucket agents are **handoff producers** — they return patch
bundles, evidence, changed-file inventories, and proposed status rows; they must **not** write shared
`.gald3r/` indexes, `CHANGELOG.md`, or commits. The coordinator performs all shared writes after
deterministic reconciliation. (Source: g-rl-33 "Swarm Reconciliation Gate".)

---

## 3. Architecture

```
                 ┌──────────────────────────────────────────────┐
                 │            gald3r_agent  (Mode B)            │
                 │  pipeline/  — the loop, gates, swarm, verify │
                 │                                              │
   Claude Agent  │   ┌── system prompt ◄── gald3r.prompts ─────┐│
   SDK (the loop,│   │   (persona, role.verifier, playbook.*)  ││
   tool-calling, │   │                                         ││
   subagents) ───┼──►│   tools  ◄── gald3r MCP server (stdio) ──┤│  37 deterministic tools
                 │   │            `gald3r mcp`                  ││  (gald3r_task_*, _bug_*, …)
                 │   └─────────────────────────────────────────┘│
                 └───────────────────────┬──────────────────────┘
                                         │ reads/writes ONLY via tools
                                         ▼
                                   .gald3r/  (source of truth)
```

- **The loop** is the Agent SDK's. `pipeline/` supplies: the system prompt (assembled from prompt
  assets), the tool connection (the gald3r MCP server), the per-phase orchestration, and the gates.
- **Tools = the Mode-A MCP server.** Start it with `gald3r mcp` (stdio) or import `tool_impls(g)`
  directly. The agent never hand-edits `.gald3r/`; it calls `gald3r_task_update`, etc. This is how the
  Mode-A guarantees (validation, index regen, PRD/release freeze) are inherited for free.
- **Judgment = the prompt library.** Fetch `role.verifier`, `role.code_reviewer`, `playbook.plan`,
  `persona.norse_pantheon`, etc. via `Gald3r(...).prompts.render(id)` and compose into the SDK system
  prompt / sub-agent briefs. One canonical copy; no inlined prose.

---

## 4. Module layout (proposed)

```
gald3r-engine/src/gald3r/pipeline/        # NEW package — the ONLY place with LLM calls
  __init__.py
  client.py        # SDK client factory: connect gald3r MCP server, set model, system prompt, hooks
  loop.py          # the single-task g-go loop (plan → implement → verify) as code
  go.py            # g-go / g-go-go autopilot: queue iteration, budget, stop conditions
  swarm.py         # bucketing + SDK subagents + coordinator reconciliation (single shared-write pass)
  verify.py        # the verification ladder: evidence checks + fresh-reviewer gate
  gates.py         # deterministic guardrails (see §5) — pure functions over git + .gald3r state
  budget.py        # token/turn budget tracking + the Context Budget Gate
  config.py        # pipeline config (model, max turns, swarm width, dry-run) from .gald3r/config/
  adapters/cli.py extension:  `gald3r go [--task ID] [--auto] [--swarm N] [--dry-run]`
```

Keep `pipeline/` importable without the SDK installed failing the whole package: lazy-import the SDK
inside `client.py` (mirror how `adapters/mcp.py` lazy-imports `mcp`). Add an optional dependency
group: `[project.optional-dependencies] agent = ["claude-agent-sdk>=<pin>"]`.

---

## 5. The gates (turn prose rules into deterministic code)

These are specified in `g-rl-33` and must become **pure, testable functions** in `gates.py` that the
loop calls at the right seam. They run BEFORE/AFTER model turns; they are deterministic (git + file
state), so they are unit-testable without the model.

| Gate | When | Logic (deterministic) |
|---|---|---|
| **PCAC INBOX Gate** | before any claim/implement/review | call `g.workspace.has_conflicts()` (engine already implements this); if conflicts → stop, surface, require resolution. |
| **Housekeeping Commit Gate** | preflight + post-coordinator-write | classify `git status` dirty paths against a safe-`.gald3r/`-coordination allowlist vs. a deny list; auto-commit only the safe set; block on unsafe/mixed. |
| **Clean Controller Gate** | before claims/worktrees/shared writes | orchestration git root must be clean except the run's explicit staging allowlist; else block. |
| **Member touch-set gate (v1/v2)** | before cross-repo writes | extend the clean gate to each repo root resolved from the task's `workspace_repos`/`extended_touch_repos`/subsystem `locations`. |
| **Review Checkpoint Gate** | code→review handoff | implementation creates a checkpoint commit; pass branch/SHA to the reviewer; reviewer works from that checkpoint. |
| **Review Result Commit Gate** | after PASS/FAIL written | reviewer creates a review-result commit (allowlist-staged); blockers limited to conflicts/secrets/hook-fail/unrelated-dirty. |
| **Pre-Reconciliation Clean Gate** | swarm, before coordinator shared writes | re-run `git status` on every touch-set root; fail closed if unrelated dirt appeared during parallel work. |
| **Follow-Up Task Filing Gate** | before writing a run summary | any follow-up item must be a real task file (`gald3r_task_new`) before the summary — no slug-only "T123-followup". |
| **Autonomous Push Gate** | always | never `git push` without explicit user confirmation; offer only in the final summary. |
| **Context Budget Gate** | each turn | if est. context > 80%, stop, summarize (done/verified/remaining), do not silently continue. (See `budget.py`.) |

> Implementation note: the existing PowerShell helpers (`gald3r_housekeeping_commit.ps1`,
> `gald3r_push_gate.ps1`, `gald3r_worktree.ps1`) encode much of this logic already. Port them to
> cross-platform Python in `gates.py` (no PowerShell dependency — the engine is the cross-platform
> story). Use `subprocess` for `git`.

---

## 6. The single-task loop (`loop.py`) — reference flow

```
run_task(task_id, *, dry_run=False):
  1. gates.pcac_inbox(g)                      # block on cross-project conflicts
  2. gates.clean_controller(git_root)         # + member touch-set if workspace_repos present
  3. task = g.tasks.get(task_id); g.tasks.claim(task_id)          # via MCP/facade
  4. plan = sdk_turn(system=prompt('playbook.plan')+persona,      # LOCK_PLAN
                     tools=[gald3r_task_*], goal="lock impl plan for AC", task=task)
     -> write plan into the task file via gald3r_task_update
  5. impl = sdk_loop(system=prompt(role for the work)+persona,    # implement
                     tools=ALL, until="AC met", budget=budget)
        - on stub/TODO  -> gates.todo_completion (file follow-up task)  [g-rl-34]
        - on bug found  -> gates.bug_discovery (file bug)               [g-rl-35]
  6. gates.review_checkpoint(git_root)  -> checkpoint SHA
  7. verdict = verify.review(task, checkpoint_sha)   # FRESH reviewer identity (see §7)
  8. if verdict.passed: g.tasks.update(id, status="completed")  else status="pending" + reasons
  9. gates.review_result_commit(git_root)
 10. gates.follow_up_filing()  ; return RunResult(task, verdict, commits)
```

`sdk_turn` / `sdk_loop` are thin wrappers over the Agent SDK client in `client.py`. `dry_run=True`
must thread through every gate and tool call (no writes, no commits) — required for testing and for
the user's safety expectations.

---

## 7. Verification (`verify.py`) — the adversarial gate

Reuse `prompts/assets/role.verifier.md` (already authored) verbatim as the reviewer system prompt.
Hard rules from that asset, enforced in code:

- **Fresh identity** — the reviewer agent MUST be a different SDK session/subagent than the
  implementer (the asset says "you cannot verify your own work"). Enforce by construction: `verify`
  spawns a new client, never reuses the implementer's.
- **Two-stage gate** — Stage 1 spec-compliance (each AC exactly met) must pass before Stage 2
  code-quality is even assessed. Encode as sequential; Stage-1 fail short-circuits.
- **Evidence standards** — the reviewer demands authentic output (test logs, compile logs) not "looks
  correct". `verify.py` can pre-collect evidence deterministically (run the test command, capture
  output) and hand it to the reviewer, so the model judges real artifacts.
- **FAIL records reasons** — write the failure reason to the task's status history via
  `gald3r_task_update` so the next attempt sees it (`playbook.plan` re-lock uses it).

---

## 8. Swarm (`swarm.py`)

- **Bucketing** — partition independent pending tasks (no shared file/subsystem touch set) into N
  buckets. Dependencies and overlapping `subsystems:`/`workspace_repos:` must NOT be split across
  buckets concurrently.
- **Subagents** — use the Agent SDK's subagent capability; each bucket agent gets the implementer
  system prompt + the gald3r tools, scoped to its bucket. Run in isolated git worktrees
  (`gates`/worktree helper) so parallel writes don't collide.
- **Report-back, not write** — bucket agents return structured handoffs (patch bundle, evidence,
  changed-files, proposed status rows, and `touch_repos:` if they edited extra roots). They never
  write shared `.gald3r/` indexes or commit shared state.
- **Coordinator reconciliation** — after `gates.pre_reconciliation_clean()` passes on every touch-set
  root, the coordinator applies handoffs and performs ALL shared writes + commits in one pass.

---

## 9. Claude Agent SDK usage notes

- **Package:** `claude-agent-sdk` (Python). Pin a version in the `agent` optional-dependency group.
- **Client:** use the streaming client for multi-turn control (so gates can run between turns) rather
  than one-shot `query()`. `client.py` owns: model selection, `max_turns`, the system prompt, the MCP
  server connection, and SDK hooks.
- **Tools:** connect the gald3r MCP server as the tool source — either spawn `gald3r mcp` (stdio) as a
  subprocess MCP server, or register `tool_impls(g)` via the SDK's in-process tool mechanism. Prefer
  the in-process path for speed and to avoid a second process; fall back to stdio for parity with how
  other IDEs consume it.
- **System prompt:** assemble from `gald3r.prompts` — `persona.norse_pantheon` (optional, default
  off for cost), plus the role/playbook asset for the active phase. Keep it small; the tools carry the
  capability, the prompt carries the judgment.
- **Permissions / safety:** run tools in the SDK's controlled permission mode; route every git-mutating
  action through `gates.py`, not raw model tool calls. The Autonomous Push Gate is mandatory.
- **Subagents:** use for swarm buckets and for the fresh-reviewer identity.
- **Model:** default to the latest Claude (e.g. an Opus/Sonnet tier per task complexity); make it
  config-driven (`pipeline/config.py`, from `.gald3r/config/AGENT_CONFIG.md`).

---

## 10. Configuration & runtime

- **Auth:** `ANTHROPIC_API_KEY` (or the SDK's configured auth). `gald3r_agent` is the first component
  that needs a key — the Mode-A core never did. Document this clearly; it's the dividing line.
- **Config file:** `.gald3r/config/AGENT_CONFIG.md` (already referenced by the rules) — model,
  `max_turns`, swarm width, `think_in_code`, budget thresholds, dry-run default.
- **Entry points:** `gald3r go --task T123`, `gald3r go --auto` (g-go-go), `gald3r go --swarm 4`.
  Add under the existing argparse CLI; lazy-import `pipeline` so non-agent installs don't pay for the
  SDK.
- **Where it runs:** local CLI first. Later, the same `pipeline` invoked server-side is the
  `gald3r_world_tree` deployment — keep all I/O behind the `Gald3r` facade so the swap is transport-only.

---

## 11. Acceptance criteria (MVP "done")

1. `gald3r go --task <id> --dry-run` plans + simulates implement + review for one real task against a
   real `.gald3r/`, making **zero** writes, and prints the planned actions + would-be verdict.
2. `gald3r go --task <id>` (live) completes one task end-to-end: locks a plan into the task file,
   implements via tools, produces a checkpoint commit, runs a **fresh-identity** review, writes PASS/
   FAIL via `gald3r_task_update`, and creates a review-result commit — all gate-guarded.
3. Every gate in §5 exists as a unit-tested pure function and is wired into the loop at the right seam.
4. `gald3r go --auto` iterates the queue until empty / budget / stop, never pushes without
   confirmation, and files real follow-up tasks (no slug-only items).
5. `gald3r go --swarm N` runs N buckets in isolated worktrees with report-back; the coordinator does
   the single shared-write pass after the pre-reconciliation clean gate.
6. The Mode-A core (`gald3r-engine/src/gald3r/{config,store,schema,systems,prompts}.py`) is **unchanged**
   and still makes no LLM calls. All model interaction lives in `pipeline/`.

---

## 12. Test plan (testing an LLM-driving harness)

- **Gates:** pure unit tests over fixture git repos + fixture `.gald3r/` (no model). This is the bulk
  of the coverage and must be deterministic.
- **Loop seams:** inject a **fake SDK client** (a stub that returns scripted tool-call sequences) so
  `loop.py`/`go.py`/`swarm.py` are tested without real model calls. Assert the orchestration: correct
  tools called in order, gates fired at the right seams, dry-run writes nothing.
- **Prompt assembly:** assert the system prompt is composed from the right `gald3r.prompts` assets per
  phase (and that persona is off by default).
- **Golden transcripts (optional, gated):** a small set of live, recorded runs behind an env flag /
  marker, not in the default suite (they cost tokens and are nondeterministic).
- **Reuse:** the existing engine suite (`gald3r-engine/tests/`, 71 tests) already covers the tool layer;
  Mode B tests only the orchestration on top.

---

## 13. Risks & open questions

- **In-process vs stdio MCP tools** — decide early (affects `client.py`). In-process is faster; stdio
  matches external-IDE parity. Recommendation: in-process, with a stdio fallback.
- **Cost & reliability** — Mode B is the first token-spending component; the Context Budget Gate and
  `--auto` stop conditions are not optional. Default to dry-run in docs/examples.
- **Worktree story on Windows/macOS/Linux** — the worktree helper is currently PowerShell; port to
  Python `git worktree` via subprocess for the cross-platform promise.
- **SDK version drift** — pin and isolate behind `client.py`; nothing else imports the SDK.
- **Fresh-reviewer enforcement** — must be structural (separate session), not a prompt request.
- **Open:** does `gald3r_agent` ship inside `gald3r-engine` (as the `pipeline/` package + `agent`
  extra) or as a separate distribution? Recommendation: same package, optional `agent` extra, so the
  Mode-A core stays installable without the SDK.

---

## 14. Phased build order

1. **Phase 0 — `client.py` + `config.py`:** connect the gald3r MCP tools + a prompt-assembled system
   prompt; prove a single SDK turn can call `gald3r_task_list` and read it back. No orchestration yet.
2. **Phase 1 — `gates.py`:** port the deterministic gates (start with PCAC inbox [already in the
   engine], clean-controller, housekeeping-commit, push gate). Full unit tests.
3. **Phase 2 — `loop.py` + `verify.py`:** the single-task `g-go` flow with the fresh-reviewer gate,
   behind `--dry-run` first, then live. Meets ACs 1–3.
4. **Phase 3 — `go.py`:** the `g-go-go` autopilot (queue iteration, budget, stop, follow-up filing).
   Meets ACs 4.
5. **Phase 4 — `swarm.py`:** bucketing + subagents + coordinator reconciliation. Meets AC 5.
6. **Phase 5 — thin the `g-go*` shims** (per `strategy/CONTEXT_THINNING.md`) to point at `gald3r go`,
   and re-run `strategy/build_registry.py` to flip the `g-go*` rows to ✅.

---

## Appendix A — engine surfaces Mode B consumes (already built)

- **37 MCP tools** (`gald3r-engine/src/gald3r/adapters/mcp.py`): `gald3r_task_*`, `_goal_*`, `_bug_*`,
  `_feature_*`, `_prd_*`, `_idea_*`, `_vocab_*`, `_constraint_*`, `_subsystem_*`, `_vault_*`,
  `_release_*`, `_workspace_*`, `_prompt_*`.
- **The `Gald3r` facade** (`core.py`): `.tasks .goals .bugs .features .prds .ideas .vocab .constraints
  .subsystems .vault .release .workspace(controller) .prompts`.
- **9 prompt assets** (`prompts/assets/`): `persona.norse_pantheon`, `role.code_reviewer`,
  `role.qa_engineer`, `role.verifier`, `rubric.swot`, `playbook.plan`, `playbook.design`,
  `voice.marketing`, `rule.code_reusability`. Fetch with `g.prompts.render(id)`.
- **The workspace conflict gate** is already deterministic: `g.workspace.has_conflicts()` /
  `g.workspace.conflicts()` — wire it straight into the PCAC INBOX Gate.
