---
subsystem_memberships: [TASK_MANAGEMENT]
---
Pipeline orchestrator — implement then auto-review: $ARGUMENTS

## Mode: PIPELINE (Implement → Auto-Review)

`g-go` is a **two-phase pipeline**. Phase 1 implements tasks; Phase 2 automatically spawns an
independent reviewer agent on the completed work. You get adversarial QA without manually
alternating between sessions.

> **Multi-agent frameworks used (T1094):** `g-go` combines **delegation** (Phase 1 spawns
> implementation work / swarm buckets), **creator–verifier** (Phase 2's fresh independent
> reviewer), and **broadcast** (status/constraints surfaced to sub-agents). `--swarm` adds
> **negotiation** (coordinator-owned reconciliation over shared `.gald3r/` state). See the
> 5-framework taxonomy table in `@g-go-swarm`.

> **Independence guarantee**: The Phase 2 reviewer is a fresh Task subagent. It receives only
> the task IDs and the `g-go-review` protocol — it has **no access** to Phase 1's conversation
> history, reasoning, or implementation decisions. It reads the artifacts on disk cold.

---

## 🚦 Coordinator: Routing-Only Mandate

> **The coordinator never implements. It only routes, observes, and reconciles.**
>
> If the coordinator finds itself about to write production code or do file edits for a task,
> it **MUST STOP** and delegate to `g-go-code` instead. This is the **pure routing orchestrator**
> pattern — the coordinator is traffic control, not implementation. (OpenSwarm F-002, Anthropic
> multi-agent coordination 2026-05-07.)

**Routing decision record** — for each subtask the coordinator logs to the task's Status History:

```
ROUTE: {task_id} → {specialist} ({mode}) — {reason}
```

**Mode choices:**
- **`SendMessage`** (parallel) — independent subtask, no cross-bucket deps; fire-and-forget. Maps to `--swarm` parallel buckets.
- **`Handoff`** (sequential) — full-context transfer required from a prior result; wait for upstream output. Maps to the sequential `g-go-code → g-go-review` pipeline.

**Coordinator-owned writes** — all shared `.gald3r/` write operations (TASKS.md, task files, BUGS.md,
CHANGELOG.md, generated prompts, parity output) are **coordinator-owned steps** performed after
specialist results are collected. They are never delegated to bucket agents or specialist executors.

### Routing Flowchart

```mermaid
graph TD
    C[Coordinator] --> |routes task spec| IA[Implementer Agent]
    C --> |routes task spec| RA[Reviewer Agent]
    IA --> |returns patch bundle| C
    RA --> |returns verdict| C
    C --> |coordinator-owned write| G[.gald3r/ shared state]
    style C fill:#f9f,stroke:#333
    style G fill:#bbf,stroke:#333
```

---

### ⛔ NO-PROMPT RULE — READ AND ENFORCE BEFORE DOING ANYTHING ELSE

**The coordinator MUST NEVER ask the user to confirm a plan, select a scope, choose between options, or approve a proposal.** This command is designed for fire-and-forget operation across multi-window workflows and scheduled automation. The user has already expressed intent by typing the command; they are not watching this session.

The **only** valid reasons to stop mid-run are the explicitly documented **hard-gate failures** listed below (WPAC conflict exit-code `2`, dirty orchestration root outside this run's staging allowlist, manifest / `workspace_repos` resolution error on multi-repo work). Any ambiguity that is NOT one of those hard gates is **resolved silently by the auto-plan rules below** and the run proceeds without comment.

Asking "Go?" or "Confirm?" or "Which tasks?" or "Conservative or expanded?" is a **violation of this rule**. If you find yourself composing a confirmation question, apply the auto-plan instead and start working.

#### Auto-Plan Algorithm (no explicit task IDs in `$ARGUMENTS`)

When `$ARGUMENTS` is empty or contains no task/bug IDs, the coordinator selects the work queue **immediately and silently** using these ordered rules:

1. **Scope filter** — determined by flags AND `.gald3r/config/AGENT_CONFIG.md` `g_go_default_scope` (T532 + controller-default extension):

   **Step 1a — Resolve effective scope** (evaluated in priority order, highest wins):
   | Priority | Condition | Effective scope |
   |---|---|---|
   | 1 | `--local` flag present | **local-only**: current repo tasks only |
   | 2 | `--workspace <id>` or `--workspace <id1,id2>` | **narrow**: only the named manifest member(s) |
   | 3 | `--workspace` (flag, no value) | **all members**: full workspace scan |
   | 4 | *(no flag)* + AGENT_CONFIG `g_go_default_scope: workspace_all` | **all members** (controller-repo default) |
   | 5 | *(no flag)* + AGENT_CONFIG `g_go_default_scope: local_only` or absent | **local-only** (member-repo default) |

   **Step 1b — Apply the resolved scope:**
   - **local-only** — include only items that are **this-repo-scoped**: the task's `workspace_repos` field is absent, empty, or contains only the current repo's own manifest ID. Items whose `workspace_repos` lists other member repos are **deferred** (logged as `Deferred — member-repo scope` in the session summary; no prompt to the user).
   - **workspace scope (all or filtered)** — include items routed to any manifest-declared workspace repository that (a) is in the resolved member set, (b) has `repository.local_path` existing on disk, (c) has `lifecycle_status` permitting work, and (d) has `allowed_write_policy` compatible with the task's `workspace_touch_policy`. Items routing to repos that are missing/planned/unavailable, write-disallowed, or unauthorized are **deferred** with explicit per-repo reasons. The orchestration controller and every selected member repo each get their own per-root clean check, worktree context, and blocker reporting; no per-repo blocker silently affects unrelated repos.

   > **Controller repos** (those with `g_go_default_scope: workspace_all` in AGENT_CONFIG.md) default to workspace-wide scope because they have no code of their own. Use `--local` to explicitly restrict to controller-only tasks, or `--workspace <repo_id>` to narrow to a specific member.
2. **Phase 1 queue** — all `[📋]` / `[ ]` / stale-`[📝]` items that pass the scope filter, ordered Critical → High → Medium → Low. Apply the auto-downgrade rule: if exactly one implementation item passes the filter, downgrade to single-agent `g-go-code` and continue — do not stop.
3. **Phase 2 queue** — all `[🔍]` items that pass the scope filter and are reachable from the Phase 1 checkpoint.
4. **Zero runnable items** — output `[PIPELINE] No runnable items after scope filter. Deferred: {list with reasons}. Nothing to commit.` and exit cleanly. **Do not ask what to do.**

When `$ARGUMENTS` provides explicit task/bug IDs, use those IDs exactly — skip scope filtering. The user's explicit selection is the plan. The `--workspace` flag still affects per-repo clean-check and authorization behavior even with explicit IDs: every repo touched by the explicit task list is gated per-root.

---

## Prompt Template Variables (T1175)

When the `g-go` coordinator dispatches a task to an implementer subagent (`g-go-code`) or to a reviewer subagent (`g-go-review`), the dispatch prompt is **templated**: the coordinator substitutes a fixed set of template variables at runtime before the subagent receives the prompt. This eliminates the "hand-edit the prompt per task" anti-pattern and gives a stable, audit-able dispatch surface.

Supported template variables (resolved at coordinator dispatch time, never inside the bucket agent):

| Variable | Resolved from | Example resolution |
|----------|---------------|-------------------|
| `{{TASK_ID}}` | Numeric ID of the queued task (no `T` prefix) | `1175` |
| `{{TASK_TITLE}}` | `title:` field of the task YAML frontmatter | `the external runner g-go pipeline patterns` |
| `{{SKILL_PATH}}` | Absolute path to the active gald3r skill folder for the dispatch role | `.claude/skills/g-skl-tasks` |
| `{{BRANCH_NAME}}` | Worktree branch from `gald3r_worktree.py -Action Create -Json` output | `gald3r/1175/code/<gald3r_source>/autopilot-iter9` |
| `{{TASK_FILE}}` | Path to the active task file under `.gald3r/tasks/**` | `.gald3r/tasks/open/task1175_external_runner_g_go_pipeline_patterns.md` |
| `{{WORKTREE_PATH}}` | Absolute worktree path from the helper JSON | `<ECOSYSTEM_ROOT>/.gald3r-worktrees/<gald3r_source>/1175-code-autopilot-iter9` |
| `{{MODE}}` | Resolved model tier (`fast` | `standard` | task `preferred_model:` override) | `standard` |
| `{{COORDINATOR_AGENT}}` | Slug of the coordinator agent for audit trail | `autopilot-iter9` |

**Resolution rules:**

1. All `{{VAR}}` tokens are resolved by simple string substitution **before** the prompt is sent to the subagent. The subagent receives a fully-materialized prompt — it never sees an unresolved `{{...}}` token.
2. If a referenced variable cannot be resolved (e.g. `{{TASK_TITLE}}` for a task with no `title:` field), the coordinator logs the failure as `PROMPTARG_FAIL: {{VAR}} unresolved for T{id}` and **defers** the item rather than dispatching with a malformed prompt.
3. Custom dispatch prompts may extend the template set, but the eight variables above are **guaranteed** present in every dispatch and must never be re-purposed for other meanings.
4. Template variable substitution is a coordinator-only operation — bucket agents and reviewer subagents must NOT receive raw template strings to render themselves.

**Why this matters**: a structured templating surface lets the coordinator log exactly which payload each subagent received (audit), lets dispatch prompts evolve without rewriting every bucket call-site, and lets future provider adapters (see "Provider-Agnostic Adapter Pattern" below) translate `{{VAR}}` into provider-specific argument shapes (OpenAI tool args, Anthropic content blocks, etc.) at a single chokepoint.

## Swarm Lifecycle Hooks (T1175)

`g-go --swarm` (and `g-go-code --swarm` / `g-go-review --swarm`) supports **optional** PowerShell lifecycle hook scripts that fire at bucket transition points. Hooks are advisory observation/notification surfaces — they MUST NOT mutate task state, write to shared `.gald3r/` ledgers, or affect coordinator routing decisions. They are intended for logging, metrics, external notifications (Slack/Rally/PagerDuty), and developer-machine status displays.

### Hook contract

The coordinator looks for the following optional PowerShell scripts in the active IDE hooks folder (first match wins across `.claude/hooks/`, `.cursor/hooks/`, `.agent/hooks/`, `.codex/hooks/`, `.copilot/hooks/`, `.opencode/hooks/`):

| Hook script | Fires when | Coordinator-passed arguments |
|-------------|-----------|-----------------------------|
| `g-hk-on-bucket-start.ps1` | Immediately after a bucket worktree is created and just before the bucket agent is spawned | `-BucketId <int> -TaskIds <int[]> -WorktreePath <string> -Branch <string> -Mode <string>` |
| `g-hk-on-bucket-complete.ps1` | After a bucket agent returns its handoff payload (PASS, partial, or with Blockers) and before coordinator reconciliation begins on that bucket | `-BucketId <int> -TaskIds <int[]> -PassCount <int> -BlockedCount <int> -DurationSeconds <int> -Verdict <string>` |
| `g-hk-on-bucket-error.ps1` | When a bucket agent fails to return a parseable payload, times out, or returns an error verdict | `-BucketId <int> -TaskIds <int[]> -ErrorType <string> -ErrorMessage <string>` |

### Coordinator invocation pattern

```powershell
# Pseudo-code the coordinator follows for each hook
$hook = @(
  ".cursor\hooks\g-hk-on-bucket-start.ps1",
  ".claude\hooks\g-hk-on-bucket-start.ps1",
  ".agent\hooks\g-hk-on-bucket-start.ps1",
  ".codex\hooks\g-hk-on-bucket-start.ps1",
  ".copilot\hooks\g-hk-on-bucket-start.ps1",
  ".opencode\hooks\g-hk-on-bucket-start.ps1"
) | Where-Object { Test-Path $_ } | Select-Object -First 1
if ($hook) {
  powershell -NoProfile -ExecutionPolicy Bypass -File $hook `
    -BucketId 1 -TaskIds @(7,9) -WorktreePath "..." -Branch "..." -Mode "fast"
}
```

### Hook rules

- **Optional**: missing hook scripts are NOT an error. The coordinator continues silently when no hook is present.
- **Read-only side effects**: hooks must NOT touch `.gald3r/TASKS.md`, `.gald3r/BUGS.md`, task/bug files, `CHANGELOG.md`, parity output, or git state. They may write to `.gald3r/logs/`, external systems, or stdout for the coordinator session log.
- **Non-blocking**: hooks run with a 30-second timeout (override via `GALD3R_HOOK_TIMEOUT_SECONDS`). If a hook exceeds the timeout or exits non-zero, the coordinator logs `HOOK_FAIL: <script> exit=<n>` to the session summary and continues — a failed hook never blocks bucket progression.
- **Idempotent**: hooks may be invoked more than once per bucket if the coordinator retries (e.g. on transient parse failures). Hook scripts must tolerate replay without producing duplicate side effects on external systems.
- **Documented contract**: the hook script's parameter block MUST match the argument table above; coordinators will pass arguments by name (`-BucketId`, `-TaskIds`, etc.) and ignore additional declared parameters.

### Contract definition only — no example scripts shipped

This command defines the contract. Concrete hook scripts (e.g. "post bucket-complete to Slack", "write a metric to Datadog", "ping Rally with `Rally-Comment`") are NOT shipped in the gald3r template — operators write them per environment. Place hook scripts in the appropriate `<ide>/hooks/` folder using the names above; the coordinator discovers them automatically on the next swarm run.

## Provider-Agnostic Adapter Pattern (T1175)

`g-go` does not own model selection — by design. The gald3r framework is a **prompt orchestrator**: it routes work, partitions buckets, gates safety, and writes shared state, but the actual LLM call is delegated to the host IDE harness (Claude Code, Cursor, Codex, Gemini, OpenCode, Copilot). The provider-agnostic abstraction in gald3r is the `--mode` flag combined with the per-task `preferred_model:` field — see "Model-Tier Selection" below.

**The adapter surface, in concrete terms:**

| Layer | Owner | What it does |
|-------|-------|--------------|
| Tier selection (`fast` / `standard` / `cheap`) | `g-go` / `g-go-code` flag | Provider-agnostic intent: "this task wants a cheap model" or "this task needs a reasoning model". Recorded in Status History as `mode=<tier>`. |
| Per-task override (`preferred_model:`) | Task YAML | Provider-agnostic intent: "this specific task needs Opus" or "this specific task is fine on Haiku", overrides session mode. |
| Tier → concrete model resolution | Host IDE harness | The IDE maps `fast` → `claude-haiku-4-5` (Claude Code), `fast` → `gpt-4o-mini` or `haiku` (Cursor), etc. See the Mode Mapping table in "Model-Tier Selection" below for current resolutions per IDE. |
| API call | Host IDE harness | gald3r never opens an HTTPS connection to a model provider. The IDE owns auth, rate limits, retries, and streaming. |

**Why this matters for adoption**: a future IDE adding gald3r support (e.g. a new local-LLM CLI) does not require any gald3r changes. The new IDE adds its own `--mode` → `model-name` mapping; gald3r continues to emit `mode=<tier>` and `preferred_model:` annotations unchanged. The the external runner adapter pattern is satisfied because the abstraction lives at the tier-of-intent level, not the model-name level.

**Limit**: this is a tier-of-intent abstraction, not a runtime model swap. gald3r cannot fail over from one provider to another mid-task if the IDE-configured model is rate-limited. That is properly an IDE-layer concern. Operators who need cross-provider failover should configure it in the IDE (e.g. Cursor's model-fallback settings) — gald3r will inherit it.

## Iteration and Timeout Limits (T1175)

`g-go` accepts dual stop-conditions in `$ARGUMENTS` that bound the **pipeline** run (both phases combined). **Whichever limit hits first stops new work cleanly**; in-flight items finish, status writes batch, the review-result commit lands, and the pipeline summary is written.

| Flag | Default | Override env var | Behavior |
|------|---------|------------------|----------|
| `--max-iterations N` | `5` | `GALD3R_MAX_ITERATIONS` | Maximum number of items the pipeline will process this session (Phase 1 implementation count). Once N items reach `[🔍]` or Blocked, Phase 1 stops claiming and Phase 2 reviews only those N items. |
| `--timeout-minutes M` | `30` | `GALD3R_TIMEOUT_MINUTES` | Wall-clock budget from pipeline start. When elapsed minutes ≥ M and the current item finishes, Phase 1 stops claiming. If Phase 2 has not yet spawned when the timer expires, it still spawns once on the already-checkpointed items (the user has earned a review pass for the work that completed). |

**Enforcement rules:**

- Limits are checked between items, never preemptively. An in-flight item is never interrupted mid-edit.
- `--max-iterations` counts Phase 1 attempts (PASS + BLOCKED items). It does not separately bound Phase 2 — once Phase 1 stops, Phase 2 reviews whatever made it to `[🔍]`.
- `--timeout-minutes` is wall-clock from pipeline start (NOT from each phase start). A pipeline at minute 28 will not start a new Phase 1 item even if Phase 1 has been the only active phase.
- In `--swarm` mode, limits apply to the coordinator's scheduling: `--max-iterations` caps total items partitioned across all buckets; `--timeout-minutes` is a coordinator-level wall-clock fence.
- Either limit hitting MUST be logged in the Pipeline Session Summary as `Stop reason: queue exhausted | max-iterations (N of N) | timeout-minutes (M elapsed) | hard-gate blocker`.
- Explicit `$ARGUMENTS` flags override env vars; env vars override defaults.

**Why dual limits**: see the matching section in `g-go-code.md` — iteration alone is brittle for tasks of mixed size; wall-clock alone is brittle when many small items finish cleanly. Together they bound both work and time.

## Completion Signal Convention (T1122)

A coordinator or parent orchestrator may need to recognize that a `g-go` /
`g-go-code` / `g-go-review` iteration is finished without polling task files
or waiting for the agent process to exit. To support this, gald3r defines a
single inline completion signal that agents emit in their stdout / response
text when they consider their work for the current iteration done.

### Default signal

```
<gald3r-status>COMPLETE</gald3r-status>
```

This is the canonical default. Parent orchestrators (`g-go --swarm` coordinator,
external `example_agent` daemon, CI runners) scanning agent output SHOULD look
for this exact tag pair.

### Recognition rules

1. **Case-insensitive on both the tag name and the value** — `<gald3r-status>COMPLETE</gald3r-status>`,
   `<GALD3R-STATUS>complete</GALD3R-STATUS>`, and `<Gald3r-Status>Complete</Gald3r-Status>`
   all match.
2. **Whitespace tolerant around the value** — `<gald3r-status>  COMPLETE  </gald3r-status>`
   matches. Whitespace inside the tag name itself does NOT match (the tag is
   a literal token, not XML-with-attributes).
3. **First match wins** — if an iteration emits the signal multiple times
   (e.g., from quoted documentation in a result summary), the first occurrence
   stops the loop. Agents SHOULD only emit the signal once, at the very end of
   their final response.
4. **Quoted / fenced occurrences are still matches** — the scanner does NOT
   try to distinguish between a real signal and an example inside a code
   fence. Agents documenting this convention MUST therefore zero-width-break
   the tag in examples (e.g., `<gald3r-status>` becomes `<gald3r​-status>`
   or `<g-status>` in prose) or place documentation examples outside the
   iteration's primary output channel.
5. **Other emitted values besides `COMPLETE` are advisory** — `BLOCKED`,
   `NEEDS_INPUT`, `FAILED` are reserved for future use. The current scanner
   only short-circuits on `COMPLETE`; the rest log as evaluator notes.

### Agent emission contract

When an agent acting under `g-go`, `g-go-code`, or `g-go-review` has finished
its iteration's work AND has performed coordinator-owned shared writes
(TASKS.md, BUGS.md, review-result commits, etc.), it SHOULD emit the
completion signal as the **final** non-whitespace line of its response, like
so:

```
... last paragraph of work summary ...

<gald3r-status>COMPLETE</gald3r-status>
```

Agents MUST NOT emit `COMPLETE` while there is still pending work in the
current iteration's task or while a hard-gate blocker is unresolved.

### `--completion-signal <tag>` override flag (future orchestrator)

A future external orchestrator may want to use a different signal tag (for
example, when integrating with external-runner-style `<promise>COMPLETE</promise>`
pipelines or when one shell wraps multiple gald3r runs in a parent loop that
needs distinct signals per child). The flag is reserved as:

```
--completion-signal <tag-name>
```

Default: `gald3r-status:COMPLETE`. When supplied, the orchestrator scans for
`<{tag-name}>COMPLETE</{tag-name}>` instead. Agents reading this flag MUST
emit the supplied tag instead of the default. The current gald3r implementation
documents the convention only — no PowerShell orchestrator currently parses
this flag, since the "iteration loop" of `g-go` is the agent itself rather
than a wrapping process. The flag becomes load-bearing once `example_agent`
or a external runner takes over the loop role.

### Why a tag, not a file

File-based status polling (writing `.gald3r/iteration_status.json` and having
the parent watch it) is heavier than necessary for in-shell loops, requires
file-locking on Windows, and races with cleanup. An inline stdout tag is
trivially testable (`grep -i '<gald3r-status>COMPLETE</gald3r-status>'`),
needs no filesystem coordination, and survives stdout/stderr redirection
without changing the parent's contract.


## Dynamic Context Expansion in Prompts (T1119)

`g-go` prompt files (and the dispatch prompts generated by the coordinator
for `g-go-code` and `g-go-review`) support an inline shell-expansion
expression: any occurrence of an opening `!\`` (bang-backtick) and a
matching closing `\`` on the same line is treated as a shell command
whose stdout is substituted in place before the agent sees the prompt.

This lets a prompt declare its live context (current TASKS.md head,
recent commits, open PRs, currently-claimed worktrees) without the
coordinator having to know in advance which context the implementer
will need.

### Syntax

```
Current task queue:
!`Get-Content .gald3r/TASKS.md -TotalCount 100`

Recent commits:
!`git log --oneline -10`

Open PRs (GitHub):
!`gh pr list --limit 5 --state open`
```

Each `!\`...\`` expression is replaced by the captured stdout of the
command run with the project root as the working directory.

### Expansion rules

1. **Parallel execution** — every `!\`...\`` in a prompt file runs in
   parallel (PowerShell `Start-Job` / `ForEach-Object -Parallel` on PS
   7+, or `Wait-Job` aggregation on PS 5.1). The orchestrator does not
   serialize expansions and does not depend on declaration order. A
   prompt that requires a specific ordering between two expressions
   must compose them into a single command (`cmd1; cmd2 | ...`) rather
   than relying on left-to-right ordering of the inline tags.
2. **Fast-fail on non-zero exit** — if any expression exits with a
   non-zero exit code, the entire prompt expansion fails fast with
   the error line `Context expansion failed: !\`{command}\` exited
   {exit_code}` and the run is aborted before the agent is invoked.
   This is intentional: a context expansion that errors usually means
   the agent's understanding of the world is now broken.
3. **Escaped backticks pass through literal** — `!!\`literal\`` (double
   bang) is the explicit escape: it produces the literal text
   `!\`literal\`` in the expanded prompt without executing anything.
   Use this when documenting the convention itself or when prose
   genuinely needs the bang-backtick token.
4. **No nested expansion** — the stdout of an expansion is substituted
   verbatim; if it contains a literal `!\`...\``, that nested token is
   NOT re-expanded. Prompts that need recursive expansion must
   construct the second-level expansion in their own command rather
   than embedding it for re-evaluation.
5. **Run as project root** — all expressions run with the project root
   (the directory containing `.gald3r/.identity`) as cwd, with the
   user's normal shell environment. Commands that need a different cwd
   must `cd`-prefix themselves explicitly.
6. **Truncation contract** — expansions are NOT truncated by the
   expander itself. If a command emits 10 MB of output, the agent
   receives 10 MB of context. Prompts SHOULD pipe heavy expansions
   through `Select-Object -First N` or `head -N` to keep the prompt
   shaped to the agent's context window.
7. **Stderr is not substituted** — only stdout is captured. Stderr
   passes through to the orchestrator's own stderr and is logged but
   not interpolated into the prompt.

### `g-go` invocation

Prompt files containing `!\`...\`` expressions are processed by the
coordinator's pre-agent dispatch step before the prompt is handed to
the implementer or reviewer subagent. The orchestrator caches expanded
prompts per iteration so re-invocations within the same iteration do
not re-execute the commands.

The current gald3r implementation documents the convention only — the
expander itself becomes load-bearing when an external runner takes over the prompt
dispatch role. Today, when `g-go` IS the agent, the agent SHOULD
interpret `!\`...\`` expressions itself by running the command via the
shell tool and substituting the output into its own working context.


## Structured Review Verdict (T1120)

The `g-go-review` reviewer subagent emits its PASS/FAIL verdict inside
a single XML tag that the coordinator can parse deterministically.
This replaces fragile string matching on free-form markdown ("did the
reviewer say PASS or FAIL?") with a typed, schema-validated extraction.

### Verdict schema

The reviewer emits exactly one of these tags as the final structured
output of its response:

```xml
<gald3r-verdict>
{
  "status": "PASS",
  "criteria": [
    {"id": "AC1", "result": "pass", "note": "verified by file inspection"},
    {"id": "AC2", "result": "pass", "note": "test output captured"}
  ],
  "evidence": "Re-ran the AC verification commands in a clean checkout; outputs match the implementer's claim.",
  "reviewer_notes": "Optional free-form notes for the coordinator log."
}
</gald3r-verdict>
```

`status` is one of `PASS`, `FAIL`, or `PASS_WITH_NOTES`. The `criteria`
array enumerates each acceptance criterion the reviewer evaluated, with
per-criterion `result` (`pass`, `fail`, `unsure`) and a short `note`.
`evidence` is a single string describing how the reviewer verified the
work. `reviewer_notes` is optional free-form text the coordinator may
surface in its session summary.

### Recognition rules

1. **Exactly one verdict tag per review** — if the reviewer's output
   contains multiple `<gald3r-verdict>` blocks, the orchestrator uses
   the LAST one (so a reviewer who self-corrects mid-response can
   overwrite an earlier draft verdict by emitting a new one at the
   end).
2. **JSON body, no XML attributes** — the tag carries a JSON object
   in its body; XML attributes on the tag are ignored.
3. **Validation is mandatory** — the orchestrator validates the parsed
   JSON against the schema (`status` enum, `criteria` array, required
   string fields). Malformed JSON or a missing required field surfaces
   as `Verdict schema invalid: {error}` and the review FAILS the
   coordinator's structured-extraction gate (the underlying task is
   left at `[🔍]` for re-review, not auto-failed).
4. **Backwards-compatible fallback** — if NO `<gald3r-verdict>` tag is
   present, the orchestrator falls back to legacy text-pattern
   detection: it scans the reviewer's output for "PASS" / "FAIL" /
   "PASS_WITH_NOTES" headings as before. The fallback is documented
   as deprecated and will be removed in a future release once all
   reviewer prompts are updated.

### Reviewer emission contract

When the `g-go-review` reviewer agent finishes evaluating a task or
bucket, it emits the verdict tag as the FINAL structured block of its
response, after the human-readable summary. Example:

```text
... narrative summary of the review ...

<gald3r-verdict>
{
  "status": "FAIL",
  "criteria": [
    {"id": "AC1", "result": "pass",  "note": "files exist, content matches"},
    {"id": "AC2", "result": "fail",  "note": "no test was added for the regression"},
    {"id": "AC3", "result": "unsure", "note": "spec is ambiguous about whether the helper is required"}
  ],
  "evidence": "Ran fast suite (1970 tests) -- 1 regression on test_voxelize_back_compat. Test added in implementer commit covers only the happy path.",
  "reviewer_notes": "Recommend splitting AC2 into AC2a (happy-path test, done) and AC2b (regression test for the back-compat invariant, missing)."
}
</gald3r-verdict>

<gald3r-status>COMPLETE</gald3r-status>
```

(Note: the completion signal and the verdict tag are both emitted at the
end of the response. The verdict tag carries the review outcome; the
completion signal tells a parent orchestrator that the reviewer is done
emitting output. They are independent and serve different purposes.)

### Coordinator extraction

The coordinator's structured-output extraction reads the LAST
`<gald3r-verdict>...</gald3r-verdict>` block from the reviewer's
response, parses the JSON, validates the schema, and writes the
resulting verdict to the Status History of the reviewed task or bug
in the form:

```
| TIMESTAMP | [🔍] | [✅] | reviewer-id | PASS — {evidence summary} |
```

(or `[🔍] -> [📋]` for FAIL, with the FAIL marker and the evidence
summary.)





## Named Workflow Templates (T1121)

gald3r ships five named workflow templates that map almost perfectly to
a clear, named taxonomy. Naming the patterns makes their
intent discoverable and lets users pick the right one with a single
flag instead of memorizing flag combinations.

### Template catalog

| Template name | gald3r equivalent | One-line use case |
|---|---|---|
| `blank` | `g-go --single` (no loop, single iteration) | One-shot task; do it once and stop |
| `simple-loop` | bare `g-go` (default — iterate until done) | Implement one task to `[✅]`, iterating as needed |
| `sequential-reviewer` | `g-go` with `--review` (implement + review each task) | Pair each implementation with an immediate independent review |
| `parallel-planner` | `g-go --swarm` (plan, then branch per task) | Fan out independent tasks across parallel buckets |
| `parallel-planner-with-review` | `g-go --swarm --review` | Parallel fan-out with per-bucket independent review |

The mapping is intentionally a thin alias: every template is a
documented composition of existing flags, NOT new orchestration logic.
This keeps the underlying behavior auditable in terms of the flag
contract while making the pattern discoverable.


### Template definitions

#### `blank` — single-shot, no loop

| Aspect | Value |
|---|---|
| Phases | 1 (implement only) |
| Agent role(s) | Solo implementer |
| Branch strategy | Worktree off current branch; no auto-rebase |
| Review behavior | None (no Phase 2) |
| Ideal use case | "Just do this one thing once" — quick fixes, one-line edits, anything that does not need iteration or review |

Equivalent invocation:

```text
@g-go --single tasks <task-id>
```

#### `simple-loop` — iterate until done

| Aspect | Value |
|---|---|
| Phases | 1 (implementer iterates until `[✅]` or hard-gate) |
| Agent role(s) | Solo implementer with `g-go-code` semantics |
| Branch strategy | Worktree off current branch; coordinator-owned checkpoint commit at end of each iteration |
| Review behavior | None during the loop; a separate `g-go-review` run can be invoked later |
| Ideal use case | Single-task focus session; the implementer is trusted to self-verify |

Equivalent invocation:

```text
@g-go tasks <task-id>
```

(Bare `g-go` is `simple-loop` by default.)

#### `sequential-reviewer` — implement, then review, per task

| Aspect | Value |
|---|---|
| Phases | 2 (Phase 1 implement → Phase 2 fresh-reviewer subagent) |
| Agent role(s) | Implementer (`g-go-code`) + fresh independent Reviewer (`g-go-review`) |
| Branch strategy | Implementer worktree → checkpoint commit → reviewer worktree from that branch/SHA |
| Review behavior | Mandatory; reviewer reads code-on-disk cold, never sees implementer's reasoning history |
| Ideal use case | Default "do it right" mode for any task that ships user-facing behavior |

Equivalent invocation:

```text
@g-go tasks <task-id>            # bare g-go is now also the two-phase default
@g-go --review tasks <task-id>   # explicit form
```

(The two-phase pipeline is the bare-`g-go` default per the existing
`## Mode: PIPELINE` section above; the `--review` flag is the explicit
spelling.)

#### `parallel-planner` — fan out, no review

| Aspect | Value |
|---|---|
| Phases | 1 (coordinator partitions; buckets implement in parallel) |
| Agent role(s) | Coordinator + N parallel implementer buckets |
| Branch strategy | One worktree per bucket off the coordinator's checkpoint; bucket branches are FF-merged at the end of Phase 1 |
| Review behavior | None |
| Ideal use case | Many small independent tasks where the implementer is trusted; max throughput |

Equivalent invocation:

```text
@g-go --swarm tasks <id1> <id2> <id3> ...
```

#### `parallel-planner-with-review` — fan out, then review

| Aspect | Value |
|---|---|
| Phases | 2 (parallel implement → parallel review) |
| Agent role(s) | Coordinator + N implementer buckets + N reviewer buckets |
| Branch strategy | Implementer worktrees per task → checkpoint per task → reviewer worktree per task from that branch/SHA |
| Review behavior | Mandatory and parallel; each reviewer is independent of every implementer's reasoning |
| Ideal use case | Default for any swarm run that ships user-facing behavior; matches `sequential-reviewer`'s correctness bar at swarm scale |

Equivalent invocation:

```text
@g-go --swarm --review tasks <id1> <id2> <id3> ...
```

### `--template <name>` flag

The `--template <name>` flag is an alias for one of the five names
above. It composes with `--workspace`, `--mode`, and any task / bug ID
filter. Examples:

```text
@g-go --template blank tasks T1234              # one-shot, no loop
@g-go --template simple-loop tasks T1234        # iterate until done
@g-go --template sequential-reviewer tasks T1234 # default two-phase
@g-go --template parallel-planner tasks T1234 T1235 T1236
@g-go --template parallel-planner-with-review tasks T1234 T1235 T1236
@g-go --template parallel-planner-with-review --workspace tasks T1234
```

When `--template` is supplied, ANY conflicting flag combination
explicitly errors with `Template conflict: --template <X> implies <Y>;
remove the conflicting flag`. When `--template` is omitted, gald3r
infers the template from the explicit flag combination (bare `g-go` =
`sequential-reviewer`; `g-go --swarm --review` = `parallel-planner-with-review`).

### `--template list` discovery

```text
@g-go --template list
```

Outputs the five template names with one-line descriptions, mapping
to gald3r's existing flag spelling. This is the canonical
discovery surface — it always reflects what is actually implemented.

### Mapping table for existing commands

| Existing command form | Inferred template |
|---|---|
| `@g-go --single tasks T<id>` | `blank` |
| `@g-go tasks T<id>` (single-task) | `simple-loop` when only one item, else `sequential-reviewer` |
| `@g-go --review tasks T<id>` | `sequential-reviewer` |
| `@g-go --swarm tasks <ids>` | `parallel-planner` |
| `@g-go --swarm --review tasks <ids>` | `parallel-planner-with-review` |
| `@g-go-code tasks T<id>` | (lower-level — Phase 1 only of `simple-loop`) |
| `@g-go-review tasks T<id>` | (lower-level — Phase 2 only of `sequential-reviewer`) |

`g-go-code` and `g-go-review` are not templates themselves; they are
the per-phase building blocks. The template names describe *workflows*,
not individual commands.

### Why named templates

- **Discoverability** — `@g-go --template list` is the canonical entry
  point for users who do not yet know which flag combination they want.
- **Documentation consistency** — Skills, READMEs, and CHANGELOG entries
  can now refer to "the `parallel-planner-with-review` template"
  unambiguously instead of "g-go --swarm --review (which is also
  sometimes called swarm-with-review)".
- **Future external runner alignment** — when `example_agent` or a
  external runner takes over orchestration, the
  template names become the stable user-facing surface; the flag
  compositions become implementation detail of the runner.


## Session Capture & Cross-Sandbox Resume (T1124)

When a `g-go` iteration runs inside an agent worktree/sandbox, the full Claude Code
conversation transcript (the session JSONL) can be captured to the host so a later
iteration — or a fresh agent in a different sandbox — resumes the *literal* thread with
`claude --resume`. This is distinct from `memory_capture_session` (semantic summaries
for search); JSONL capture preserves the conversation itself.

### Capture helper

`gald3r_session_capture.py` ships beside `gald3r_worktree.py` in each IDE skill folder
(`.claude/skills/g-skl-git-commit/scripts/`, `.cursor/...`, `.claude/...`).

```powershell
# After an iteration completes in a worktree, capture its session JSONL to the host
.\scripts\gald3r_session_capture.py -Action Capture -Apply `
    -WorktreePath {{WORKTREE_PATH}} -TaskId {{TASK_ID}} -Json
```

What it does:

1. Locates the worktree's session JSONL under the Claude projects dir
   (`$env:CLAUDE_CONFIG_DIR\projects` or `~/.claude/projects`), using Claude's
   path-folder encoding (every non-alphanumeric char in the cwd → `-`).
2. Copies it to `~/.gald3r-sessions/<project_id>/<task_id>/<session_id>.jsonl`
   (root overridable via `$env:GALD3R_SESSIONS_ROOT`).
3. Rewrites embedded worktree paths (`cwd` and file references, both JSON-escaped
   `\\` and raw forms) to the host repo path so resume references real host files.
4. Upserts metadata to `~/.gald3r-sessions/<project_id>/sessions.json`.

Without `-Apply` the helper is a dry-run (`-Action Report`). `-Action List` enumerates
captured sessions; `-Action Resolve -SessionId <id>` prints the JSONL path and the
`claude --resume` command.

### `--resume-session <session_id>` flag

`g-go --resume-session <session_id>` starts the next iteration by reusing a previously
captured session context instead of a cold start:

1. The coordinator runs `gald3r_session_capture.py -Action Resolve -SessionId <id> -Json`
   to obtain the host JSONL path and resume command.
2. The spawned agent is launched with `claude --resume <session_id>` (host cwd), so it
   inherits the full prior conversation thread.
3. If the session id is unknown (no metadata record and no JSONL on disk), the coordinator
   logs `RESUME_MISS: <session_id>` to the session summary and falls back to a normal cold
   iteration — a missing capture never blocks the pipeline.

Capture is **best-effort and non-blocking**: if no session JSONL is found (e.g. the runner
stores transcripts elsewhere), the helper reports `no-session-found` and the pipeline
continues unaffected.


## Shared Sandbox Phase Handoff (`--shared-sandbox`) — T1118

By **default**, `g-go` uses **separate-context handoff**: Phase 1 implements in a `code`
worktree, reconciles the diff into the primary checkout, creates a code-complete checkpoint
commit, and Phase 2 spawns a fresh reviewer that creates its **own** `review` worktree from
that checkpoint commit. This is the proven default and is unchanged — see Phase 1 Completion
and Phase 2 below.

`--shared-sandbox` is an **opt-in** flag that keeps the **same `code` worktree alive across
Phase 1 and Phase 2** instead of spinning up a separate reviewer worktree. This mirrors
a persistent multi-run sandbox: the sandbox is created once, dependencies
are installed once, commits accumulate on a single branch, and a second `run()` (the review
pass) sees the same filesystem/git state without re-cloning.

### Lifecycle contract

| Stage | Default (separate-context) | `--shared-sandbox` |
|-------|----------------------------|--------------------|
| Phase 1 worktree | `code` worktree off current branch | same — `code` worktree off current branch |
| End of Phase 1 | reconcile diff to primary checkout → checkpoint commit on primary | checkpoint commit **on the `code` worktree branch**; no reconcile to primary yet |
| Between phases | `code` worktree may be cleaned up | coordinator runs `-Action Keep` to protect the worktree across the boundary |
| Phase 2 review source | fresh `review` worktree created from checkpoint commit | **reuse the same `code` worktree path/branch, read-only** |
| Phase 2 verdict | review-result commit on primary | review-result commit on primary after coordinator reconciles the (now reviewed) `code` branch |
| Post-PASS | member auto-merge from `code` branch | member auto-merge from the same `code` branch |

The independence guarantee is **preserved**: the Phase 2 reviewer is still a fresh Task
subagent with no Phase 1 conversation history. It reads the code on disk cold. Sharing the
**worktree filesystem** is not sharing the **reasoning context** — the reviewer only inherits
the installed dependencies and accumulated commits, never the implementer's decisions.

### Handoff artifacts (coordinator → reviewer)

Under `--shared-sandbox`, the coordinator passes the shared worktree as the review source
instead of a separate-worktree base. These three fields are the handoff contract:

```
shared_sandbox       = true
implementation_branch = {code worktree branch from Phase 1 -Action Create JSON}
shared_worktree_path  = {worktree_path from Phase 1 -Action Create JSON}
implementation_sha    = {checkpoint commit SHA on that branch}
```

The reviewer receives these in its initial prompt and, per `g-go-review` Step 2b, **reuses the
named worktree read-only** (sets `review_isolation_mode: shared-worktree`) rather than calling
`-Action Create -Role review`.

### Keep / cleanup protection

To stop the normal cleanup pass from reclaiming the shared worktree between phases, the
coordinator stamps it with a keep window immediately after the Phase 1 checkpoint commit:

```powershell
.\scripts\gald3r_worktree.py -Action Keep -TaskId {id} -Role code -Owner {owner} -KeepHours 2 -Json
```

`-Action Keep` writes `phase_handoff: true` and a future `keep_until` (ISO-8601) onto the
worktree's `.gald3r-worktree.json` marker (additive — all existing fields preserved).
`-Action Cleanup` skips any worktree whose `keep_until` is still in the future, so the shared
sandbox survives the Phase 1→2 boundary. Once the keep window elapses (default 2h), or after
Phase 2 reconciliation removes the worktree explicitly via `-Action Remove` / member
auto-merge, the worktree is reclaimable again. `Keep` is idempotent and may be re-stamped to
extend the window for long review passes.

### Flag semantics

- **Default (no flag)**: current separate-context behavior — backwards compatible, unchanged.
- **`--shared-sandbox`**: opt-in single-worktree lifecycle described above. Composes with
  `--swarm` (each bucket's `code` worktree is its own shared sandbox for that bucket's
  reviewer), `--mode`, `--workspace`, and explicit task/bug filters.
- All existing safety gates (Review Checkpoint Gate, Review Result Commit Gate, Clean
  Controller Gate, Pre-Reconciliation Clean Gate, member touch-set gates) apply unchanged. The
  only change is **which worktree the reviewer inspects** and **when the primary-checkout
  reconcile happens** (after review rather than before).

> **Integration test contract (AC5)**: a full `g-go --shared-sandbox tasks T<id>` run must
> demonstrate that Phase 2 sees Phase 1's commits without re-cloning — i.e. the reviewer's
> `review_isolation_mode` is `shared-worktree`, its inspected path equals
> `shared_worktree_path`, and `git log` on that worktree shows the Phase 1 checkpoint commit
> with no intervening `git worktree add`/clone for the review role. The keep-window protection
> is unit-verifiable via `gald3r_worktree.py -Action Keep` followed by `-Action Cleanup
> -StaleHours 0`, which must leave the kept worktree intact.

## Model-Tier Selection (`--mode fast|standard|cheap`)

`g-go` accepts an optional `--mode` flag in `$ARGUMENTS` that selects model-tier policy for
the pipeline. The flag composes with `--swarm`, `--workspace`, and any task/bug filter.

### Mode mapping table

| `--mode` | Tier | Claude model | Cursor model | Use when |
|----------|------|--------------|--------------|----------|
| `fast` (alias `cheap`) | haiku-class | `claude-haiku-4-5` | `gpt-4o-mini` / `haiku` | Simple task batches, cost-sensitive runs, bucket agents on parallel-safe work |
| `standard` (default) | sonnet-class | `claude-sonnet-4-6` | `sonnet-4` | Most pipelines, coordinator role, anything requiring real reasoning |
| (no flag) | inherit | session default | session default | Fall through to the IDE-configured default model |

`cheap` is a strict alias for `fast` (same tier, same model mapping).

### Coordinator vs bucket inheritance (AC4)

`g-go` (and `g-go --swarm`) treats `--mode` differently for the coordinator role and bucket
agents:

- **Coordinator** — always defaults to `standard` regardless of the session `--mode` flag.
  Coordinators route work, plan partitions, perform reconciliation, and write shared
  `.gald3r/` state — these operations require Sonnet-class reasoning. The only way to force
  the coordinator onto a lower tier is to pass `--mode fast` AND set the env override
  `GALD3R_ALLOW_FAST_COORDINATOR=1` (intended for experimental/automated regression suites,
  not production pipelines).
- **Bucket agents (Phase 1 implementers)** — inherit the session `--mode` flag. When the
  session is launched as `@g-go --swarm --mode fast`, every bucket implementer runs in
  `fast` mode (haiku-class). When the session is `@g-go --swarm --mode standard` or
  `@g-go --swarm` with no flag, buckets run `standard`.
- **Phase 2 reviewer** — defaults to `standard` for adversarial review. Override only with
  explicit `--mode fast` on the session AND a per-task `preferred_model:` declaring the
  reviewer tier; otherwise the reviewer agent always runs `standard` to protect the
  independence guarantee.
- **Task YAML `preferred_model:` overrides** — when a queued task sets `preferred_model:`
  (`haiku` | `sonnet` | `opus` | `fast` | `standard`) in its frontmatter, that overrides the
  bucket inheritance for that specific task. Use this to keep one complex task on Opus while
  the rest of the swarm runs on Haiku, or vice versa.

### Status History mode logging (AC5)

When Phase 1 claims a task and moves it to `[🔄]` / `in-progress`, the claim's Status History
row MUST include `mode=<tier>` in the `Message` column (see `g-go-code` for the full row
template). The coordinator records its own routing mode and each bucket agent records its
inherited mode independently. This applies to both single-agent `g-go` and swarm
coordination.

### Budget-aware skill preference (T1172 / T1259)

`g-go --swarm` coordinators (and single-agent `g-go` when context is constrained) SHOULD
read the `token_budget:` frontmatter field on each candidate skill before dispatch and
prefer lower-band skills when available context budget is tight. This is **advisory, not
enforcing** — the coordinator may still pick a `high` or `very_high` skill if it is
genuinely the right tool, but it MUST note the budget tradeoff in its dispatch log.

| Band | Approximate context cost | Coordinator preference |
|------|--------------------------|------------------------|
| `low` | < 5K tokens | Prefer when context > 50% used; safe default |
| `medium` | 5K – 20K tokens | Default working band; use freely under normal load |
| `high` | 20K – 50K tokens | Reserve for pipelines that genuinely need the depth; note the cost |
| `very_high` | > 50K tokens | Only when the task explicitly requires deep ingest or cross-session work |
| unset | unknown | Treat as `medium`; flag the gap via `@g-doctor` (see g-doctor §6) |

**When `token_budget:` is unset**: the coordinator MUST NOT abort dispatch — fall back
to `medium` and log the unset state. `g-doctor` surfaces the gap as a low-severity
quality finding (T1259 AC).

**Composite/orchestrator skills** (`g-go`, `g-mission`, etc.) inherit the maximum band of
their internal invokees. When delegating to a composite skill, budget against its declared
band, not its individual invokees.

**See also**: the authoring guide at `.gald3r_sys/skill_packs/user-skills/skl-skill-create/SKILL.md`
§"`token_budget:` declaration (T1172)" for full band definitions, example skills, and
authoring guidance.

---

### Step 0 — Workspace Member Clean-Status Preflight (T1431, AUTHORITATIVE definition)

**Runs first — before the WPAC inbox gate, task selection, claim, or any worktree creation.**
This is the canonical Step 0 spec; the other `g-go*` commands reference it. Purpose: surface dirty
`autonomous_child` member repos **early** so the user resolves them up front, instead of hitting
the existing Clean Controller Gate / member touch-set block mid-pipeline (post-claim).

**Behavior (read-only — no commits, no writes, no stashes):**

1. If `.gald3r/workspace/workspace_manifest.yaml` is absent, OR no `autonomous_child` members are
   declared → skip Step 0 silently and proceed to the WPAC gate.
2. For each manifest member with `workspace_role: autonomous_child` whose `repository.local_path`
   exists on disk (skip missing paths whose `lifecycle_status` is a planned/bootstrap gap — note
   them), run `git -C <path> status --short`.
   - `controlled_member` repos are marker-only with no active development → skip (or list as
     informational only); never block on them.
3. **Clean path** — all checked members clean → print `Workspace clean -- N members checked` and
   proceed to Step 1 (WPAC gate).
4. **Dirty path** — any member has modified/untracked files → print a compact per-repo status
   table and ask the user to commit/stash before continuing. Do **NOT** auto-commit, do **NOT**
   fail silently:

   ```
   ⚠️  Workspace members have uncommitted changes:
   | repo id            | path                          | modified | untracked |
   |--------------------|-------------------------------|----------|-----------|
   | example_desktop      | <ECOSYSTEM_ROOT>/...throne | 3        | 1         |
   Commit or stash these before continuing, or pass --skip-member-clean-check.
   ```

5. **`--skip-member-clean-check`** flag → bypass Step 0 with a printed warning and proceed
   directly to Step 1.

**Additive, not a replacement:** the Gald3r Housekeeping Commit Gate (controller `.gald3r/`
coordination files) continues to auto-commit safe controller paths exactly as before. Step 0 only
*reports* member status; it never mutates anything. Target: completes in < 2 s for a 5-10 member
ecosystem. Uses the same manifest resolution as the v1 member touch-set gate.

---

### WPAC inbox Gate (Only When WPAC is configured)

Before task claiming, implementation, verification, planning, or swarm partitioning, first determine whether this project is a WPAC participant. WPAC is configured only when `.gald3r/workspace/topology.md` declares at least one parent/child/sibling relationship, or `.gald3r/PROJECT.md` explicitly declares WPAC project linking relationships. A Workspace-Control manifest and local `INBOX.md` alone do not make the project a WPAC group member.

If WPAC is configured, run the re-callable inbox check when the hook exists:

```powershell
$hook = @( ".cursor\hooks\g-hk-wpac-inbox-check.py", ".claude\hooks\g-hk-wpac-inbox-check.py", ".agent\hooks\g-hk-wpac-inbox-check.py", ".codex\hooks\g-hk-wpac-inbox-check.py", ".opencode\hooks\g-hk-wpac-inbox-check.py" ) | Where-Object { Test-Path $_ } | Select-Object -First 1
if ($hook) { powershell -NoProfile -ExecutionPolicy Bypass -File $hook -ProjectRoot . -BlockOnConflict }
```

Installed templates may call the equivalent hook from the active IDE folder. If the check reports `INBOX CONFLICT GATE` or exits with code `2`, stop immediately and run `@g-wpac-read`; do not claim tasks, create worktrees, spawn reviewers, or continue planning until conflicts are resolved. Non-conflict requests, broadcasts, and syncs are advisory and should be surfaced in the session summary. If WPAC is not configured, skip this gate and report `WPAC: not configured / skipped`.


### Gald3r Housekeeping Commit Gate (T531)

<!-- T531-HOUSEKEEPING-GATE -->
After the WPAC gate is skipped or passes and **before** the Clean Controller Gate hard-blocks the run, run the safety classifier helper at the orchestration root:

```powershell
.\scripts\gald3r_housekeeping_commit.py -Mode preflight -Apply -TaskId <id-when-known> -Json
```

Behavior:

- **`clean`** -> continue.
- **`safe-gald3r-housekeeping`** -> the helper stages **only** allowlisted controller `.gald3r/` paths via explicit `git add -- <paths>` (never `git add .`), re-checks for drift, and creates a focused `chore(gald3r): preflight gald3r housekeeping` commit. The run continues automatically.
- **`unsafe-gald3r` / `mixed-dirty` / `conflict` / `drift-detected` / unknown `.gald3r` paths / member-repo `config-fault`** -> the helper exits non-zero, the existing Clean Controller Gate hard-block applies, and the run STOPs with the exact unsafe paths listed.

The helper allowlist covers the safe controller `.gald3r/` coordination surfaces (TASKS.md, BUGS.md, FEATURES.md, PRDS.md, SUBSYSTEMS.md, IDEA_BOARD.md, learned-facts.md, tasks/, bugs/, features/, prds/, subsystems/, reports/, logs/wpac_auto_actions.log, workspace/sent_orders/, workspace/inbox.md). The deny list covers `.identity`, `.user_id`, `.project_id`, `.vault_location`, `vault/`, `config/`, `.gald3r-worktree.json`, secret-named files, and unknown `.gald3r/` paths. Member-repo targets (marker-only `.gald3r/`) are refused -- this gate is **controller-only**.

Re-run the helper in `-Mode post-write -Apply` immediately after coordinator-owned shared `.gald3r` writes (task/bug status writes, review-result writes, sent_orders ledger updates, safe report/log outputs) and before the next major phase so the shared-state dirty window stays short. In `--swarm` flows only the coordinator runs the helper; bucket agents remain handoff producers.
### Clean Controller Gate (before claims, worktrees, reconciliation)

After the WPAC gate is skipped or passes:

1. At the **orchestration git root** (the repo from which you run this command — normally the Workspace-Control owner, e.g. `<gald3r_source>`): run `git status --short`. If anything is listed **outside** this run's explicit coordinator staging allowlist for the active task and bug IDs, **STOP** here. Do not claim tasks or bugs, create or reuse T170 worktrees, partition swarms, or write coordinator-owned updates to `.gald3r/TASKS.md`, `.gald3r/BUGS.md`, other shared `.gald3r` coordination files, `CHANGELOG.md`, generated Copilot prompts, or parity output until unrelated changes are committed, stashed, or moved to a prior focused commit. Preserve any bucket handoff artifacts already produced and list the paths that blocked progress.

2. **`gald3r_worktree.py -AllowDirty`**: do not use this switch for `g-go`, `g-go-code`, `g-go-review`, or any `--swarm` variant **except** when every dirty path is owned exclusively by the active task/bug scope and a `## Status History` row documents that override. Otherwise clean the checkout first. The same **per-root** `-AllowDirty` discipline applies to every repository included in the touch set below when multi-repo work is in scope.

3. **Member touch-set (v1 — `workspace_repos`)** — The orchestration root is **always** gated. When the active task or bug declares **`workspace_repos:`** with manifest `repository.id` entries, extend the gate to each **other** resolved member root (blast radius follows declared cross-repo scope). Read `.gald3r/workspace/workspace_manifest.yaml` when present; map each listed ID (deduplicated) to `repositories[?].local_path`. For each existing path, run `git -C "<path>" rev-parse --show-toplevel` then `git status --short` at that root. Apply the same **explicit coordinator staging allowlist** per root. Skip IDs whose paths are missing while `lifecycle_status` is a planned/bootstrap gap (report only; do not expand the touch set). If the manifest is missing while `workspace_repos` is non-empty, or an ID is unknown under `repositories:`, **STOP** multi-repo coordinator work until manifest or frontmatter is repaired (controller-only queue items whose `workspace_repos` lists only the owner id may proceed once that id resolves).

4. **Touch-set expansion (v2 — optional signals)** — Union extra repository roots into the same per-root checks (still **not** a blanket scan of every manifest member):
   - **`extended_touch_repos:`** — optional task/bug YAML list of additional manifest `repository.id` values beyond `workspace_repos`.
   - **`touch_repos:` (swarm handoffs)** — In `--swarm` runs, when bucket work edits roots not already covered by `workspace_repos` + `extended_touch_repos:`, bucket summaries and the coordinator reconciliation block MUST list those ids under `touch_repos:` so the union is gated before shared writes.
   - **Subsystem `locations:` absolutes** — When the active item declares **`subsystems:`**, read each `.gald3r/subsystems/{name}.md` frontmatter **`locations:`** (all nested strings). For values matching a host **absolute** path (`^[A-Za-z]:[/\\]` on Windows, or POSIX `/` rooted at `/` elsewhere), if the path exists, resolve `git -C <dir> rev-parse --show-toplevel` (use the file's parent directory when the path is a file). Each distinct root **other than** the orchestration root joins the touch set. Relative paths do not expand the set.

### Pre-Reconciliation Clean Gate (before coordinator shared writes)

Also re-run the **Gald3r Housekeeping Commit Gate** with `-Mode post-write -Apply` against the orchestration root immediately after each coordinator-owned shared `.gald3r` write so safe controller coordination state lands in a focused `chore(gald3r): commit g-go coordination state` commit before the next major phase begins.


Immediately before the coordinator merges bucket results into the primary checkout, updates shared `.gald3r` indexes or task/bug files as coordinator-owned writes, touches `CHANGELOG.md`, or creates checkpoint / review-result commits: **re-run** `git status --short` on the **orchestration root and every other repository root in the computed touch set** (steps 1 + 3 + 4). For `--swarm` runs, if unrelated dirty paths appear in **any** of those roots during parallel bucket work, **fail closed** — do not apply those shared writes; keep patches, artifacts, and evidence; report **per-root** blockers using the same blocker family as checkpoint and review-result commits.

## Session-Start: Load Active Goal (Goal-Locked Loop)

> Fires immediately after safety gates pass, before Phase 1 work begins. If no active goal is set, this section is a no-op.

If `.gald3r/config/ACTIVE_GOAL.md` exists:

1. Read the file. Parse its YAML frontmatter (`description`, `linked_task`, `set_at`, `turn_budget`, `turns_consumed`).
2. Inject into working context as the prefix:
   ```
   CURRENT GOAL: <description> (turn <turns_consumed>/<turn_budget>, task T{id})
   ```
3. Increment `turns_consumed` by 1 and write the updated value back to `ACTIVE_GOAL.md`.
4. If `turns_consumed >= turn_budget`:
   - Surface `🎯 Goal turn budget exhausted — pausing for user direction.`
   - Stop the run cleanly. The user must extend the budget (`@g-goal <description>` to reset) or clear the goal (`@g-goal clear`).

If `--with-goal T{id}` was passed in `$ARGUMENTS`:

1. Treat as if `@g-goal --from-task T{id}` were just run: read `.gald3r/tasks/task{id}_*.md` (active or archive), set `ACTIVE_GOAL.md` from the task title, then proceed.
2. Set `linked_task: T{id}` and the description from the task `title:` field. Default `turn_budget: 50`.

If no `ACTIVE_GOAL.md` exists and no `--with-goal` flag is present, proceed without a goal lock (normal operation).

**Goal-aligned AC gate** (Phase 1 implementation only): after each AC-gate iteration in Phase 1, the implementing agent (or per-bucket implementer) self-checks: "Did this action advance `<description>`?" If not, re-anchor on the goal in the next reasoning step. This is a soft drift-correction — not a hard block.

See `g-goal` command (parity across all 6 IDE platforms) for the full goal-locked loop specification.

---

## Phase 1: Implementation

Phase 1 runs the full `g-go-code` protocol. Every completed item is marked `[🔍]`.
During Phase 1, the implementation-only boundary still applies: run smoke/unit readiness checks only, and do not invoke full adversarial review. Only Phase 2 may spawn the independent reviewer.

### Step 0a — Shell Router (T1144, before any tool call)

Before issuing any shell, hook, or git command in this run, **probe once** and lock the shell route for the session. This complements the always-apply rule `g-rl-00-always` §6 ("Shell Context — OS + Shell Probe") and prevents the bash-vs-PowerShell token-waste loop documented in BUG-031 / T1144.

**Probe (one signal, not a diagnostic loop):**

| Signal | Route |
|---|---|
| `$env:OS` contains `Windows`, or `$IsWindows -eq $true`, or harness reports `Shell: PowerShell` | **PowerShell route** — use a `PowerShell` / `Shell` tool when available |
| `uname -s` returns `Linux` / `Darwin`, `$BASH_VERSION` is set, or harness reports `Shell: Bash` | **bash/zsh route** — use the `Bash` tool |

**Lock and route every subsequent invocation through the chosen interpreter.** Do not mix syntaxes inside a single tool call — the tool, not the snippet, picks the parser. If the harness exposes both `Bash` and `PowerShell` tools on Windows, prefer the PowerShell tool for PowerShell snippets.

Concrete syntax differences to keep in mind (mirrors `g-rl-00-always` §6):

- Arrays: `@(...)` (PS) vs `(...)` / `arr=(a b c)` (bash)
- Statement separators: `;` sequential (PS, both); `&&` short-circuit (bash always, PS 7+)
- Env vars: `$env:VAR` (PS) vs `$VAR` / `${VAR}` (bash)
- Paths: `\` (PS, `/` also accepted on Windows) vs `/` (bash)
- File-exists test: `Test-Path $p` (PS) vs `[ -f "$p" ]` (bash)
- Pipeline filters: `Where-Object { ... }` (PS) vs `grep` / `awk` / `xargs` (bash)

**Regression canonical (BUG-031 family)** — the WPAC inbox hook lookup snippet that triggered T1144:

```powershell
$hook = @( ".cursor\hooks\g-hk-wpac-inbox-check.py", ".claude\hooks\g-hk-wpac-inbox-check.py" ) | Where-Object { Test-Path $_ } | Select-Object -First 1
```

This snippet is PowerShell-only — invoking it via `Bash(...)` produces `syntax error near unexpected token '('` (exit 2). That error is a **tool-routing failure**, NOT a real WPAC conflict or hook-missing state. Re-route through PowerShell and the call succeeds; do not enter an error-driven retry loop.

The same router applies to **Phase 2 (review)** below — the reviewer subagent must inherit the route and not re-probe.

---

### 1. Load Context (Before Touching Anything)

Read in this order:
- `.gald3r/PROJECT.md` — mission, goals, ecosystem context
- `.gald3r/PLAN.md` — current milestones
- `.gald3r/BUGS.md` — open bugs (**read before TASKS** — bugs run first)
- `.gald3r/TASKS.md` — master task list
- `.gald3r/CONSTRAINTS.md` — guardrails (if exists)
- `.gald3r/DECISIONS.md` — past decisions (if exists, read-only)
- **Active workflow profile (T1239)** — load once via `load_profile.py` (active
  skill folder; see g-skl-tasks "Reading the active profile"). The resulting
  `task_statuses[]` (each with `id`, `symbol`, `skip_in_pipeline`) is the
  pipeline's source of truth for which statuses are claimable vs. skipped and for
  status-DAG transition order — **not** the hardcoded `[📋]/[🔄]/[🔍]/[✅]`
  strings (AC1). When `.gald3r/config/workflow_profiles/` is absent (pre-T1238
  installs), use the built-in `software_dev` lifecycle so behavior is unchanged.
- `git log --oneline -10` — recent changes

### 2. Build the Work Queue

> **Profile-driven queue (T1239 AC1):** the "claimable" vs. "skip" decisions
> below are derived from the active profile's `task_statuses[]` `skip_in_pipeline`
> flag, and status transitions (`[📋]→[🔄]→[🔍]→[✅]` for `software_dev`) follow
> the profile's `task_statuses[]` declaration order. The symbols shown in this
> section are the `software_dev` defaults; a non-code profile substitutes its own
> (e.g. `content_creation`: claim `[💡] concept`/`[✍️] scripting`, skip
> `[✅] published`). g-go-code and g-go-review inherit this same loaded profile.

**Bugs first (Tier 1), then tasks (Tier 2).**

**Tier 1 — Open bugs:**
- From `BUGS.md` + `bugs/` files; Critical → High → Medium → Low
- Skip bugs with external blockers
- **Skip `[🚨]` bugs** — log in Skipped section

**Tier 2 — Pending tasks:**
- Status `[ ]` (pending), `[📋]` (ready), or stale `[📝]` (speccing claim expired)
- **Skip non-expired `[📝]` speccing claims** — log owner/expiry as "Speccing-In-Progress"
- For stale `[📝]` claims, append a Status History takeover row naming the prior `spec_owner` before proceeding
- **NOT** `[🚨]` — skip entirely
- **Skip `[⏸️]` (paused) tasks** — stored in `tasks/paused/`; must be manually unpaused before g-go picks them up
- **Skip `[🚫]` (cancelled) tasks** — stored in `tasks/cancelled/`; terminal state, never eligible for implementation
- No unmet dependencies, with the rolling-pipeline exception: checkpointed `[🔍]` dependencies count as implementation-satisfied unless the downstream task declares `requires_verified_dependencies: true`; not `ai_safe: false`
- Priority: Critical → High → Medium → Low

Supported `$ARGUMENTS` filters:
- Task IDs: `@g-go tasks 7, 9`
- Bug IDs: `@g-go bugs BUG-003`
- Subsystem: `@g-go subsystem vault-hooks-automation`
- `@g-go bugs-only` / `@g-go tasks-only`

### 2a. Resolve Phase 1 Speccing Claims Before Worktrees

Before Phase 1 worktree allocation, resolve task-spec claims in the primary checkout:
- For a bare `[ ]` task with no complete task file, run `g-skl-tasks` `CLAIM-FOR-SPEC` -> `WRITE-SPEC` -> `PROMOTE-SPEC` first.
- Skip non-expired `[📝]` claims before allocating a coding worktree.
- For expired `[📝]` claims, append a Status History takeover row naming the prior `spec_owner`, then finish/promote the spec before worktree creation.
- Only `[📋]` tasks or stale claims successfully promoted to `[📋]` proceed to Phase 1 coding worktree creation.

### 2b. Harvested Task Pre-Flight Check (T810)

**Applies to any task with `harvested_from:` in its YAML frontmatter.** Runs after speccing claims are resolved, before Phase 1 worktrees are created. Tasks without the field pass silently.

For each queued task that has `harvested_from:` set:

1. **Read subsystem spec** — Find the task's `subsystems:` list. For each subsystem, read `.gald3r/subsystems/{name}.md`. Extract the `locations:` paths and read the key files there. Produce a 3-5 line bullet summary of what is currently implemented.

2. **Scan pending queue** — Search `TASKS.md` for other tasks in status `[📋]` or `[🔄]` that reference the same subsystem(s) in their frontmatter. List: task ID, title, status.

3. **Display context panel:**
   ```
   ⚠️ HARVESTED TASK PRE-FLIGHT
   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
   Task:    T{id} — {title}
   Source:  {harvested_from} (analyzed {harvest_date})
   Type:    {harvest_type}

   Subsystem: {subsystem_name}
   Existing implementation:
     • {bullet 1}
     • {bullet 2}

   Other pending tasks for same subsystem:
     T{n}: "{title}" [{status}]
   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
   ```

4. **Decision gate by `harvest_type`:**
   - `harvest_type: additive` — Display panel, then **proceed automatically.**
   - `harvest_type: replacement` without `harvest_approved: true` — **BLOCK.** Do not proceed to Phase 1. Ask: "This task would replace existing functionality. Confirm to proceed, or `skip` to defer." Log in Skipped section as "Awaiting harvest comparison confirmation."
   - `harvest_type: replacement` with `harvest_approved: true` — Display panel as context, then proceed.
   - No `harvested_from:` field — Pass silently. (Legacy tasks.)

> **`--override-harvest-check` flag** — treats all replacement harvested tasks as approved. Use for batch runs after explicit human review of the harvest intake report.

### 3. Pre-Create Phase 1 Coding Worktrees

After speccing claims are resolved, Phase 1 uses the same isolation contract as `g-go-code`:

```powershell
.\scripts\gald3r_worktree.py -Action Create -TaskId {id} -Role code -Owner {platform_or_agent_slug} -Json
```

Installed templates may call the helper from `g-skl-git-commit/scripts/gald3r_worktree.py` when no root `scripts/` copy exists.

Rules:
- Create/reuse all queued item worktrees before implementation edits or primary-checkout status writes.
- Map helper JSON to claim metadata: `worktree_path` → `worktree_path`, `worktree_branch` → `worktree_branch`, `created_at` → `worktree_created_at`, and `owner` → `worktree_owner`.
- Run Phase 1 implementation inside the worktree root.
- Keep the primary checkout for queue coordination, final batched status writes, and Phase 2 reviewer handoff.
- If the helper refuses because the active checkout is dirty, skip the item unless the task explicitly owns direct-root work and an override is documented.
- Leave failed worktrees intact for inspection; do not delete them during the same pipeline run.

### 4. Implement Each Item

For each item:

**a)** Read the task/bug file — understand objective and acceptance criteria
**b)** If the item is a bare `[ ]` task with no complete spec, run `g-skl-tasks` `CLAIM-FOR-SPEC` → `WRITE-SPEC` → `PROMOTE-SPEC` first; skip non-expired `[📝]` claims. Then create/reuse the coding worktree and implement the solution inside that worktree
**b2) AC gate** — before moving on, walk every `- [ ]` acceptance criterion:
  - Is this criterion satisfied in actual files? → proceed
  - Unmet → return to **(b)**
  - Cannot meet this session → log as Blocker, skip task entirely (no partial `[🔍]`)
  - **Stub/TODO scan**: bare `# TODO`, `pass`, `raise NotImplementedError` → annotate `TODO[TASK-X→TASK-Y]` + create follow-up task (see `g-rl-34`)
  - **Bug-discovery check**: pre-existing bugs → BUG entry + `BUG[BUG-{id}]` comment; current-task bugs → fix inline (see `g-rl-35`)
  - **Constraint check**: any `🚫 VIOLATION` blocks `[🔍]`
  - **Workspace boundary check**: run `g-skl-workspace` ENFORCE_SCOPE before editing and before `[🔍]`; omitted metadata is current-repo-only, unknown manifest repo IDs block, and member repo writes require explicit `workspace_repos`, compatible `workspace_touch_policy`, authorization text, reviewed member git status, and manifest write permission.
**b3) Queue Status History** — collect the row that will be appended before marking `[🔍]`:
  ```
  | YYYY-MM-DD | pending | awaiting-verification | Implementation complete; {1-line summary} |
  ```
**c)** Validate — lint, test, check files exist
**d)** Record decisions → append to `.gald3r/DECISIONS.md`
**e)** Update subsystem Activity Log for each subsystem in `subsystems:` field
**f)** Queue `[🔍]` (NOT `[✅]`) status for the final Phase 1 batch write; add task ID to `phase1_results`
**g)** Move to next item

### 5. Phase 1 Completion

After all items are processed, reconcile successful worktree diffs into the primary checkout, batch-write task/bug status, then create a code-complete checkpoint commit before reviewer handoff. For each successful worktree, stage only intended files in that worktree with `git add -A -- {paths}`, export `git diff --binary --cached HEAD`, and apply it to the primary checkout with `git apply --3way --index` so new files are included. Never use `git add .` in swarm worktrees. If the patch does not apply cleanly, preserve the worktree and list the item as skipped.

**`--shared-sandbox` variation (T1118)**: when the session is run with `--shared-sandbox`, do **NOT** reconcile the diff into the primary checkout at end of Phase 1. Instead, create the code-complete checkpoint commit **on the `code` worktree branch itself**, then stamp the worktree with a keep window so the cleanup pass cannot reclaim it before Phase 2:

```powershell
.\scripts\gald3r_worktree.py -Action Keep -TaskId {id} -Role code -Owner {owner} -KeepHours 2 -Json
```

Record `shared_sandbox: true`, `shared_worktree_path`, and `implementation_branch` in each `[🔍]` task's metadata so Phase 2 reuses the same worktree read-only. The primary-checkout reconcile is deferred until after Phase 2 review passes (see the "Shared Sandbox Phase Handoff" section above).

```
[PIPELINE] Phase 1 complete
  Implemented → [🔍]: {phase1_results IDs}
  Checkpoint → {branch}@{commit_sha}
  Blocked/Skipped: {list with reasons}
```

**5b. Optional GitHub PR-Open Hook (T1291)** — after the checkpoint commit, run the triple-gated PR-open hook from `g-go-code` section 7b-pr for each task that reached `[🔍]` this session. The gate checks `project_type=software_development`, `github_integration: enabled`, and `github_pr_hooks: enabled` in AGENT_CONFIG.md. Failure does not roll back task state or block Phase 2.

If `phase1_results` is empty → skip Phase 2:
```
[PIPELINE] Phase 1 completed 0 items — Phase 2 skipped. Nothing to review.
```

---

## Phase 2: Auto-Spawn Independent Reviewer

> **Only runs if Phase 1 marked at least 1 item `[🔍]`.**

Phase 2 is a parallel review lane, not a default global pause. In swarm mode, the coordinator should launch review from the checkpoint and then continue Phase 1 rolling implementation waves for newly runnable items whose dependencies are checkpointed at `[🔍]`. Only block the implementation lane for tasks that declare `requires_verified_dependencies: true`, a review failure that invalidates a downstream checkpoint dependency, a WPAC conflict, Workspace-Control preflight denial, or a repository state that prevents a safe checkpoint.

### Spawn

Print the handoff notice:
```
[PIPELINE] Spawning Phase 2 reviewer for: Task {task IDs} / Bug {bug IDs}
[PIPELINE] Reviewer is a fresh agent — no Phase 1 context. Adversarial independence: ✓
```

**Before spawning**, collect branch context from the Phase 1 checkpoint and task files (BUG-095 fix, T1375):
```
implementation_branch = read implementation_branch from [🔍] task files (should all match the checkpoint branch)
implementation_sha    = checkpoint commit SHA from Phase 1 completion block above
```

Spawn a Task subagent with:
- The full `g-go-review` prompt
- Filter: `tasks {phase1_task_result_ids} bugs {phase1_bug_result_ids}` (omit either clause when empty)
- Coordinator-managed override: "Return PASS/FAIL payloads and Status History rows only. Do not write task/bug files, `TASKS.md`, or `BUGS.md`; the `g-go` coordinator owns final writes."
- **Branch handoff context** (append to the reviewer's initial prompt — enables Branch Pre-Flight Step 0):
  ```
  Review context (from Phase 1 coordinator):
    Implementation branch: {implementation_branch}
    Implementation checkpoint SHA: {implementation_sha}
  The reviewer should use Branch Pre-Flight (Step 0 of g-go-review) to confirm it is on branch {implementation_branch} before scanning the review queue.
  ```
- **Shared-sandbox handoff context (T1118)** — when the session ran with `--shared-sandbox`, also append the shared worktree path so the reviewer reuses it read-only instead of creating a new `review` worktree:
  ```
  Shared sandbox (from Phase 1 coordinator):
    shared_sandbox: true
    shared_worktree_path: {shared_worktree_path}
  Per g-go-review Step 2b, reuse this worktree read-only (review_isolation_mode: shared-worktree). Do NOT create a separate review worktree — the Phase 1 commits and installed dependencies are already present on {implementation_branch} at {shared_worktree_path}.
  ```
  Omit this block entirely when `--shared-sandbox` was not passed (separate-context default).
- No other context from Phase 1

### Reviewer Protocol

The spawned agent runs the standard `g-go-review` protocol:
- Claims each Phase 2 item as `[🕵️]` / `verification-in-progress` before inspection
- Establishes review isolation before inspection:
  - T170 `review` worktree from the Phase 1 checkpoint commit by default
  - Snapshot mode only when the candidate changes are explicitly left uncommitted or cannot be made branch-addressable
- Verifies the selected review source contains the candidate changes; if the candidate diff is dirty or not reachable from the chosen source branch, uses snapshot mode instead of a stale `HEAD` worktree
- Skips non-expired verifier claims and may only take over expired claims with Status History logging
- Reads each task/bug spec and checks ACs or fix criteria against actual files
- PASS → returns PASS payload + verification note
- FAIL → returns FAIL payload + Status History row; stuck-loop check (≥3 FAILs → `[🚨]`)
- **Does NOT write task/bug files, TASKS.md, or BUGS.md** — returns result payload to coordinator

### Coordinator Collects and Finalises

After reviewer completes:
1. Batch-update `TASKS.md` (all PASS → `[✅]`, all FAIL → `[📋]`) in a single write
2. Batch-update `BUGS.md` (all PASS → `[✅]`, all FAIL → `[📋]`) in a single write
3. Create the review-result commit after PASS/FAIL status writes, using explicit path staging only
4. Write Pipeline Session Summary (see format below), including the review-result commit SHA or the explicit non-commit blocker

The coordinator commits the review result by default for PASS, FAIL, and mixed verdicts. Allowed reasons not to commit are limited to unresolved conflicts, failed commit hooks, staged or untracked unrelated changes, detected secrets, dirty generated outputs not owned by review, missing user permission for destructive or out-of-scope changes, or repository state that prevents a safe commit.

**4b. Optional GitHub PR-Close Hook (T1292)** — after the review-result commit, run the triple-gated PR-close hook from `g-go-review` section "Optional GitHub PR-Close Hook" for each reviewed item. The gate checks `project_type=software_development`, `github_integration: enabled`, and `github_pr_hooks: enabled`. PASS items are squash-merged; FAIL items get a failure comment. A hook failure never rolls back the recorded verdict.

### 5. Member Repo Auto-Merge (Post-PASS)

> **Flags** (pass in `$ARGUMENTS` or inherit from `@g-go-go`):
> - `--no-auto-merge` — skip auto-merge and use old `[MERGE-BLOCKED]` behavior for all items
> - `--target-branch <name>` — override merge target (default: `main`; feature-branches-only model, see `g-rl-02`)

After the review-result commit, for every PASS item whose code worktree targets a **member repository** (any `workspace_repos` value that resolves to a repo other than the controller itself), perform the auto-merge step. Default target branch is `main` (feature-branches-only model — NO long-lived `dev` branch; see `g-rl-02-git_workflow`).

**Step 1 — Target branch existence check:**

```powershell
# Determine target branch (default: main; override with --target-branch <name>)
$targetBranch = if ($args -contains "--target-branch") { $args[$args.IndexOf("--target-branch") + 1] } else { "main" }

# Check if target branch exists in member repo
$branchExists = git -C <member_path> branch --list $targetBranch
if (-not $branchExists) {
    $branchExists = git -C <member_path> branch -r --list "origin/$targetBranch"
}
```

**Step 2 — Attempt auto-merge (when `--no-auto-merge` is NOT set AND target branch exists):**

```powershell
.\scripts\gald3r_worktree.py -Action MergeToMain -RepoPath <member_path> -TaskId {id} -Owner {owner} -TargetBranch $targetBranch -Apply -Json
```

The helper:
1. Checks out `$targetBranch` in the member repo
2. Attempts `git merge --ff-only <code_branch>` into `$targetBranch`
3. If FF fails (intervening commits), falls back to `git merge --no-ff -m "merge(T{id}): merge verified implementation into $targetBranch"`
4. On success: removes the code worktree + branch, removes the review worktree + branch, removes worktree folders, and runs `git worktree prune`
5. Returns a structured JSON result: `action` = `merged` | `merge-blocked` | `merge-skipped-dirty` | `skipped`

**Success**: log `[AUTO-MERGED→{targetBranch}] T{id}: ff` (or `no-ff`) in the Pipeline Session Summary.

**Merge blocked (fallback)**: if merge fails (conflict, unrelated history, or `--no-auto-merge` was passed), preserve the branch and log `[MERGE-BLOCKED] T{id}: <reason>` in the Pipeline Session Summary as a human action item. Do not fail the overall run.

**Target branch missing (fallback)**: if the target branch does not exist in the member repo (neither local nor remote), log `[MERGE-BLOCKED] T{id}: target branch '{targetBranch}' not found — create it first` and preserve the branch. This is the expected fallback for newly bootstrapped member repos whose `main` branch has not yet been created.

**Member dirty**: if the member repo has uncommitted changes unrelated to this task at merge time, log `[MERGE-SKIPPED-DIRTY] T{id}: member dirty` and preserve the branch. Do not attempt the merge.

**FAIL items**: do NOT run auto-merge for items that received a FAIL verdict — the code branch must be preserved for re-implementation.

Run auto-merge per PASS item sequentially in dependency order (lowest task ID first) so that each merge advances member `$targetBranch` cleanly for the next FF candidate.

When Phase 2 review and later Phase 1 rolling waves overlap, the coordinator serializes shared writes by checkpoint generation:

1. A review-result write may update only the items reviewed from its named checkpoint and any direct downstream checkpoint consumers it must requeue after FAIL.
2. A rolling implementation wave may write only its own newly implemented items to `[🔍]` and must preserve review-result status changes already committed for earlier checkpoints.
3. If review and implementation finish at the same time, apply the review-result commit first, recompute the queue, then reconcile the implementation wave against the updated primary checkout.
4. Never allow two coordinators to write `.gald3r/TASKS.md`, `.gald3r/BUGS.md`, task/bug files, changelog/docs, generated prompts, or final commits concurrently.

If review FAILs an item that later rolling-wave work consumed, requeue the failed item and mark each dependent consumer as pending rework unless its implementation can be trivially proven independent of the failed behavior. Do not roll back unrelated completed or in-progress waves.

---

## Follow-Up Task Filing Gate (MANDATORY — runs before Pipeline Session Summary)

Before writing the Pipeline Session Summary, the coordinator MUST handle all follow-up items surfaced during the run. **Named-but-not-filed follow-ups are a policy violation** — they silently disappear and require manual rescue later.

1. **Identify ALL follow-up items** surfaced during implementation or review:
   - Reviewer notes flagging deferred sub-features, gaps, or "non-blocking" items
   - Items the implementer found out-of-scope but necessary
   - Stub/TODO items that got `TODO[TASK-X→TASK-Y]` annotations (each Y must be a real file)
   - Anything described as "can be done later", "for tracking", or "named for follow-up"

2. **For each follow-up item, call `g-skl-tasks CREATE TASK`** to create an actual task file with:
   - A proper `title:` describing the work
   - `type: feature | bug_fix | refactor` as appropriate
   - `priority: low` (default; raise only when urgency is clear)
   - An `## Objective` section describing what the follow-up must accomplish
   - `dependencies: [T{originating_task_id}]` linking it to the task that surfaced it
   - Capture the returned `task_id` (e.g. `T1110`) — this is the ONLY valid identifier

3. **Reference actual task IDs** (e.g. `T1110`) in the Pipeline Session Summary — NEVER a slug like `T1043-followup-template-gitignore`. A slug without a real task file is a policy violation equivalent to data loss.

4. **If task creation fails** for any reason: log it as a `BLOCKER` in the Pipeline Session Summary — do NOT silently name-only the follow-up.

> | Rationalization | Reality |
> |---|---|
> | "It's non-blocking, I'll name it for tracking" | Named-only = lost forever. Create the task file or it doesn't exist. |
> | "The user can create it later" | The user has moved on. The pipeline IS the filing point. |
> | "I'm not sure it's needed" | Create with `priority: low`. User can archive it. Costs 30 seconds. |
> | "It's just a minor follow-up" | Minor items get lost too. T1110–T1113 were rescued manually because of this. |

---

## Pipeline Session Summary

```markdown
## Pipeline Session Summary

### Phase 1: Implementation
- Items attempted: {N}
- Completed → [🔍]: Task 7, Task 9, Bug BUG-003
- Blocked/Skipped: Task 10 — {reason}

### Phase 2: Adversarial Review (independent agent)
- Reviewer: 1 fresh Task subagent
- Reviewer had NO Phase 1 context ✓

| Task | Result | Notes |
|------|--------|-------|
| Task 7 | [✅] PASS | all ACs met |
| Task 9 | [✅] PASS | all ACs met |
| BUG-003 | [📋] FAIL | AC-2 not met — {reason} |

### Member Repo Auto-Merges
- {member_repo}: T{id} [AUTO-MERGED→main] (ff)
- {member_repo}: T{id} [AUTO-MERGED→main] (no-ff)
- Blocked (fallback): T{id} — {reason}

### Follow-Up Tasks Filed
- T{id}: {title} — {reason surfaced}
- T{id}: {title} — {reason surfaced}
(none surfaced this run — or list all filed task IDs with titles)

### Final Status
- ✅ Completed (verified): 2
- 📋 Failed (back to pending): 1
- Blocked (not attempted): 1

### Re-implement failed tasks
@g-go tasks {failed_ids}

### Push offer (this section only — never between phases or between tasks)
{N} commits are ready on {branch}. Review changes and push when satisfied:
  git log origin/{branch}..HEAD --oneline
  git push origin {branch}
Want me to push now?
```

**Push offer rules for `g-go`:**
- The push offer appears **once** — in this final status block only
- Do NOT offer push between Phase 1 and Phase 2 (pipeline still running)
- Do NOT offer push after each task commit (loop still running)
- Do NOT offer push at swarm rolling-wave checkpoints (more waves may follow)
- If the user replies "yes" / "go ahead" / "push it": push immediately

---


### WPAC inbox Heartbeats (Swarm / Long Runs)

For swarm mode or any run lasting more than 30 minutes, the coordinator reruns the WPAC inbox check every 30 minutes and once more before the final summary. If a conflict appears mid-run, pause new claims/spawns/reconciliation, preserve worktrees and partial outputs, and require `@g-wpac-read` before continuing.

## Swarm Mode (`--swarm`)

When `$ARGUMENTS` includes `--swarm`, both phases run in swarm mode.

Swarm mode is a rolling pipeline by default. Phase 1 emits checkpoint commits; Phase 2 reviews those checkpoints from fresh `review-swarm` worktrees; Phase 1 then continues with the next runnable wave instead of waiting for every review verdict. `[🔍]` dependencies count as implementation-satisfied for downstream coding unless the downstream task has `requires_verified_dependencies: true`.

### Phase 1 Swarm (g-go-code swarm protocol)

Before partitioning, evaluate Phase 1 swarm eligibility after Workspace-Control preflight. If exactly one runnable item remains and preflight passes, automatically downgrade Phase 1 to the standard single-agent `g-go-code` path and continue the pipeline without asking for confirmation. If preflight fails because a workspace member is unknown, not a git root, or not authorized for the task/bug routing metadata, stop with that blocker; invalid workspace routing is not a swarm/single-agent choice.

**Smart Agent Count:**

| Queue size | Agents |
|-----------|--------|
| 1 | 1 (no swarm — fallback) |
| 2–4 | 2 |
| 5–9 | `ceil(count / 3)` (2–3) |
| 10–14 | 4 |
| 15+ | 5 (hard cap) |

**Conflict-safe partition** (subsystem-boundary):
```
1. For each pair (A, B): CONFLICT if shared subsystem OR A depends_on B OR B depends_on A
2. Greedy assign: item → first bucket with no conflict (open new bucket up to agent_count limit)
3. Tasks touching TASKS.md/BUGS.md directly → single bucket
```

Before spawning implementer agents, skip non-expired `[📝]` speccing claims, log stale `[📝]` takeovers with prior `spec_owner`, then create or reuse one coding worktree per bucket with role `code-swarm` and `-Json`. Pass each bucket's `worktree_path` and `worktree_branch` to its implementer. Implementers run from their assigned worktree and MUST return patch bundles or explicit diffs, generated artifacts, test evidence, changed-file inventories, and proposed Status History rows. Implementers MUST NOT directly write shared `.gald3r/TASKS.md` / `.gald3r/BUGS.md`, task/bug status files, `CHANGELOG.md`, generated Copilot prompts, parity outputs, or commits. They also MUST NOT run `git add .`; explicit path staging only, excluding `.gald3r-worktree.json`, ownership metadata, terminal transcripts, local logs, and other non-deliverables.

The coordinator reconciles bucket outputs one at a time by staging only intended bucket files in the bucket worktree with `git add -A -- {paths}`, exporting `git diff --binary --cached HEAD`, and applying it to the primary checkout with `git apply --3way --index`. Before applying, the coordinator detects overlapping shared-file edits and defers shared surfaces to one final coordinator write. Failed worktrees are preserved for inspection, then the coordinator batch-writes final task/bug status, changelog/docs updates, generated prompt changes, and parity sync output once. The coordinator then creates one code-complete checkpoint commit and passes its branch/SHA to Phase 2 as the default review source. Collect `phase1_results` = union of all reconciled `[🔍]` items.

### Phase 2 Swarm (g-go-review swarm protocol)

Partition mixed `phase1_results` (tasks and bugs) round-robin across M reviewer agents (same count formula).
Coordinator claims each review bucket as `[🕵️]` before spawning reviewers, skips non-expired verifier claims, and establishes one review isolation source per bucket (`review-swarm` worktree or snapshot mode).
Each reviewer produces a result payload only: PASS/FAIL, evidence, proposed Status History rows, and any fix-forward patch if explicitly authorized. Reviewers do not write `TASKS.md`, `BUGS.md`, task/bug files, changelog/docs, generated prompts, parity output, or commits.
Coordinator performs one final shared-write pass for `TASKS.md`, `BUGS.md`, task/bug files, changelog/docs updates, generated prompts, parity sync output, final staging, and the review-result commit. The coordinator commits PASS, FAIL, and mixed review verdicts by default after status writes, unless a narrow non-commit blocker applies.

### Bucket Cancellation Contract (T1123)

The coordinator can abort in-flight bucket agents cleanly — required when a bucket
times out (`--timeout-minutes`), runs rogue, or the WPAC conflict gate fires mid-run.

- When a bucket agent is launched in its worktree, the coordinator records the agent's
  PID via `gald3r_worktree.py -Action Run ... -AgentCommand <agent>` (non-blocking;
  the PID is persisted to that worktree's `.gald3r-worktree.json`).
- **On timeout or conflict-gate abort**, the coordinator calls
  `gald3r_worktree.py -Action CancelAll -TaskId <id> -Reason <why>` to terminate **all**
  active bucket agents owned by that task. A single bucket can be killed with
  `-Action Cancel -TaskId <id> -Role <role> -Owner <owner>`.
- Termination is **graceful first** (window-close / SIGTERM), then a **forced tree-kill**
  after `-GraceSeconds` (default 5).
- **Dirty worktrees are PRESERVED** on cancellation — the coordinator never runs
  `-Action Remove` as part of the cancellation flow, so bucket state is kept for forensics.
- Every cancellation appends a row to `.gald3r/logs/worktree_cancellations.log`
  (`{timestamp} | {task_id} | {worktree_path} | {reason} ({outcome})`).
- Cancellation only stops the subprocess; the coordinator still performs its normal
  reconciliation/clean-gate handling on any partial bucket output.

### Swarm Pipeline Summary

```markdown
## Swarm Pipeline Session Summary

### Phase 1: Swarm Implementation
- Implementers: N
- Partition: subsystem-boundary
- Checkpoint: {branch}@{commit_sha}
| Bucket | Tasks | [🔍] | Blocked |
|--------|-------|------|---------|
| 1 | 7, 9 | 2 | 0 |
| 2 | 10, 11 | 1 | 1 |

### Phase 2: Swarm Review (N fresh agents — no Phase 1 context)
- Reviewers: M
- Partition: round-robin by priority
| Reviewer | Tasks | PASS | FAIL |
|----------|-------|------|------|
| R-1 | 7, 10 | 2 | 0 |
| R-2 | 9 | 0 | 1 |

### Member Repo Auto-Merges
- {member_repo}: T{id} [AUTO-MERGED→main] (ff)
- {member_repo}: T{id} [AUTO-MERGED→main] (no-ff)
- Blocked (fallback): T{id} — {reason}

### Follow-Up Tasks Filed
- T{id}: {title} — {reason surfaced}
(none surfaced this run — or list all filed task IDs with titles)

### Final Status
- ✅ Completed (verified): {N}
- 📋 Failed (back to pending): {M}
- Blocked: {K}
```

---

## Workspace Mode (`--workspace`)

`--workspace` is the **explicit, opt-in** mode that expands queue selection across manifest-declared workspace repositories. It composes with `--swarm`, with task-ID filters, and with bug filters. Bare `/g-go` is unchanged — it remains current-controller-scoped by default. **Bare `/g-go` MUST NEVER scan member repos automatically.** All existing safety gates remain in force.

### When to use

- `/g-go --workspace` — workspace-aware pipeline; runs the full Phase 1 → Phase 2 flow, but selects from items routed across manifest-declared workspace repos.
- `/g-go --swarm --workspace` — workspace-aware swarm; partitions work across buckets respecting per-repo conflict-safety and per-repo touch-set gating.
- Bare `/g-go` and `/g-go --swarm` — unchanged. Member-repo items are deferred with `Deferred — member-repo scope` in the summary.

### Workspace queue selection

When `--workspace` is present, the coordinator:

1. Reads `.gald3r/workspace/workspace_manifest.yaml` (the canonical Workspace-Control registry).
2. Resolves the repository set: orchestration controller (`<gald3r_source>`) plus every entry under `repositories:` whose `local_path` exists on disk and whose `lifecycle_status` permits work (e.g. excluding `planned`/`bootstrap_gap`/`frozen` archives).
3. Filters the queue: each runnable task or bug is included only if every entry in its `workspace_repos:` resolves to a manifest member that is (a) locally available, (b) write-permitted by `allowed_write_policy.write_allowed`, and (c) compatible with the task's `workspace_touch_policy`.
4. Honors all standard ordering rules: Critical → High → Medium → Low, dependencies (with the rolling-pipeline `[🔍]` checkpoint exception unless `requires_verified_dependencies: true`), `[🚨]` skips, stale claim takeovers, WPAC-derived priority floor, and `ai_safe: false` exclusions.
5. Logs per-deferral reasons in the session summary. Reasons include: `member-repo path missing`, `lifecycle_status forbids work`, `write_allowed: false`, `unknown repository.id in workspace_repos`, `workspace_touch_policy mismatch`, and `manifest missing or unparseable`.

### Per-repo clean and touch-set gates

The Clean Controller Gate, Pre-Reconciliation Clean Gate, and Gald3r Housekeeping Commit Gate (T531) apply **per-root** to every repository in the computed touch set:

- The orchestration controller is **always** in the touch set.
- v1: every manifest member listed in any selected task's `workspace_repos:` joins the touch set.
- v2: optional `extended_touch_repos:`, swarm-handoff `touch_repos:`, and absolute paths from subsystem `locations:` may union additional roots into the touch set (per `g-rl-33`).
- Each member root is checked independently with `git -C "<path>" status --short`. Unrelated dirty paths in any per-repo touch set block coordinator-owned writes to that repo only — they do not block unrelated clean repos unless the selected coordinator action requires all selected repos (e.g. a single-task multi-repo reconciliation).
- The **marker-only `.gald3r/` invariant** for `controlled_member` and `migration_source` repositories remains absolute. `--workspace` does NOT relax it. Attempted writes to member `.gald3r/` paths outside the marker allowlist (`.identity`, `PROJECT.md`) MUST be blocked by `g-rl-36` / the guard helper before the edit lands.

### Member-scoped task authorization

A selected task is permitted to edit a member repository only when ALL of the following are true:

1. The member's manifest `repository.id` appears in the task's `workspace_repos:` list.
2. The task's `workspace_touch_policy` is in the manifest entry's `allowed_write_policy.allowed_touch_policies`.
3. The manifest entry's `allowed_write_policy.write_allowed` is `true`.
4. Every dependency, blocker, WPAC inbox, and `[🚨]` check passes for that member root.
5. Per-repo clean check passes (or `-AllowDirty` is documented per-root in the task's `## Status History`).
6. No member `.gald3r/` control-plane path is targeted (marker-only invariant).

If any check fails, the task is deferred (workspace mode never silently degrades authorization).

### Workspace swarm coordination

Under `/g-go --swarm --workspace`:

- Bucket planning includes per-repo conflict-safety: items targeting different members can run in parallel; items sharing a member root must serialize on that root's coordinator-owned writes.
- Bucket worktrees follow `g-rl-02` (branch `gald3r/{task_id}/{role}/{repo_slug}/{owner}-{suffix}`); the `repo_slug` is the manifest `repository.id`.
- Bucket handoff metadata MUST include `touch_repos:` listing every member root the bucket actually edited; the coordinator unions those into its Pre-Reconciliation Clean Gate.
- Bucket agents return patches/artifacts/evidence/proposed-status only. The coordinator owns all shared `.gald3r/`, `CHANGELOG.md`, generated Copilot prompt, parity, and per-repo final-staging writes. `git add .` is forbidden in bucket worktrees; explicit path allowlists only.
- Checkpoint and review-result commits are created **per repository root** with focused messages. No single commit spans multiple repositories.

### Workspace summary output

Both at the periodic 30-minute heartbeats and at the final summary, `--workspace` runs print:

```
[WORKSPACE] Mode: workspace[+swarm]
[WORKSPACE] Manifest: .gald3r/workspace/workspace_manifest.yaml
[WORKSPACE] Considered repos: <gald3r_source>, gald3r_template_*, example_desktop, ...
[WORKSPACE] Skipped repos: example_app (lifecycle: frozen_marker_only), external_repo (write_allowed: false)
[WORKSPACE] Runnable items: {N}    Blocked: {K}    Deferred: {D}
[WORKSPACE] Per-repo blockers: <template_full> (unrelated dirty: .github/...), ...
[WORKSPACE] Next recommended: {command}
```

The summary makes it explicit which repos were considered, which were skipped, which were blocked, and what to run next. `--workspace` runs never finish silently with implicit cross-repo work.

### Marker-only protection (recap)

Member `.gald3r/` may contain ONLY `.identity` and `PROJECT.md`. `g-skl-workspace`, `g-skl-WPAC-spawn`, `g-skl-WPAC-adopt`, `g-skl-setup`, and `gald3r_install` all consult `.claude/skills/g-skl-workspace/scripts/check_member_repo_gald3r_guard.py` before any member `.gald3r/` write. `--workspace` runs do NOT add a bypass; the guard is non-negotiable. Any attempted write to a forbidden member `.gald3r/` path is logged as a blocker and excluded from the run.

---

## Behavioral Rules

| Rule | Why |
|------|-----|
| Phase 1 never marks `[✅]` — only `[🔍]` | Phase 2 reviewer owns `[✅]` |
| Phase 2 reviewer spawned with no Phase 1 context | Adversarial independence guarantee |
| Phase 2 inspects through a review worktree or read-only snapshot | Prevents reviewers from mutating implementation checkouts |
| Coordinator batch-writes TASKS.md and BUGS.md after Phase 2 | Prevents concurrent line-edit conflicts |
| **NEVER ask questions, propose options, or request confirmation** — apply the auto-plan and work | This is fire-and-forget; the user has moved on |
| Skip tasks you can't complete | Maximize total output |
| Respect CONSTRAINTS.md | Never violate project guardrails |
| Abort if destructive (schema drop, data loss) | Safety first — log as blocker |
| Bare `/g-go` is **always** controller-only — never silently scans member repos | Workspace expansion requires explicit `--workspace` opt-in |
| `--workspace` honors per-repo clean gates, marker-only `.gald3r/` invariant, manifest write policy, and `workspace_touch_policy` | A single global flag must not weaken per-repo safety |
| Workspace summary names every considered repo, skipped repo, and per-repo blocker | Multi-repo runs MUST be explicit about scope |
| Workspace checkpoint and review-result commits are **per repository root** | No single commit may span multiple member repositories |

---

## Usage Examples

```
@g-go
@g-go tasks 7, 9, 12
@g-go bugs BUG-003, BUG-007
@g-go subsystem vault-hooks-automation
@g-go bugs-only
@g-go --swarm
@g-go --swarm tasks 7, 9, 10, 11, 12
@g-go --swarm bugs-only
@g-go --workspace
@g-go --workspace tasks 220, 221
@g-go --swarm --workspace
@g-go --swarm --workspace tasks 220, 221, 222
@g-go --mode fast tasks 7, 9
@g-go --mode standard tasks 7, 9
@g-go --swarm --mode fast tasks 7, 9, 10, 11
@g-go --swarm --mode cheap bugs-only
@g-go --max-iterations 3 tasks 7, 9, 10, 11, 12
@g-go --timeout-minutes 15 bugs-only
@g-go --max-iterations 10 --timeout-minutes 60 --swarm
@g-go --swarm --workspace --max-iterations 8 --timeout-minutes 45
```

`--mode fast` / `--mode cheap` route bucket implementers to haiku-class models; the
coordinator stays on sonnet-class for routing and reconciliation. `--mode standard` is the
explicit form of the default. See the "Model-Tier Selection" section above for full
inheritance rules.

`--max-iterations N` (default `5`, env `GALD3R_MAX_ITERATIONS`) and `--timeout-minutes M`
(default `30`, env `GALD3R_TIMEOUT_MINUTES`) bound the pipeline run. Whichever fires first
stops new claims cleanly; in-flight work finishes and the pipeline writes its summary. See
"Iteration and Timeout Limits" above for full semantics.

Swarm lifecycle hooks (`g-hk-on-bucket-start.ps1`, `g-hk-on-bucket-complete.ps1`,
`g-hk-on-bucket-error.ps1`) are discovered automatically when present in `.cursor/hooks/`,
`.claude/hooks/`, `.agent/hooks/`, `.codex/hooks/`, `.copilot/hooks/`, or `.opencode/hooks/`.
Hook scripts are read-only observers (logging, notification, metrics); they MUST NOT mutate
`.gald3r/` state or git state. See "Swarm Lifecycle Hooks" above for the parameter contract.

Dispatch prompts use template variables (`{{TASK_ID}}`, `{{TASK_TITLE}}`, `{{SKILL_PATH}}`,
`{{BRANCH_NAME}}`, `{{TASK_FILE}}`, `{{WORKTREE_PATH}}`, `{{MODE}}`, `{{COORDINATOR_AGENT}}`)
resolved at coordinator-dispatch time. Subagents never see unresolved `{{...}}` tokens. See
"Prompt Template Variables" above.

**For manual control (two separate sessions):**
```
Session 1:  @g-go-code
Session 2 (new agent window):  @g-go-review
```

Let's go.

