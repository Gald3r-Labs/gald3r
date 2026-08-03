# g-go-go Companion: Provider & Model Routing (T580, BUG-612)

> Extracted verbatim from `commands/g-go-go.md` under T588 (file-size decomposition,
> repo threshold g-rl-00) -- content unchanged, relocated only. Companion:
> `commands/g-go-go.md` (the base command spec -- see its "Provider & Model Routing"
> section for the quick-reference flag summary and a pointer back here for the full
> contract).

---

## Provider & Model Routing (T580, BUG-612 companion)

BUG-612: a Cursor-launched `@g-go-go` with parent model GPT-5.6 Sol used to still spawn the
Claude CLI (`claude --model sonnet ...`) as its coordinator and label worktrees `claude-swarm`,
because the T477/T514 resolver only ever picked a Claude model TIER — it had no concept of a
non-Claude PROVIDER, and `gald3r autopilot loop` exposed no `--provider`/`--model` flag to
override it with. `gald3r go` already had `--model` with `provider:model` semantics
(`gald3r go -h`); `gald3r autopilot loop` did not. Both gaps are closed.

**Flags** (mirrored identically on the standalone `python -m
gald3r_core.coordination.autopilot.outer_loop` entry point):

```
--provider <provider>[:<model>]   # global override, every role that has no role-specific one
--model <model>                   # global model override (composes with --provider)
--coordinator-provider / --coordinator-model   # coordinator role only
--implementer-provider / --implementer-model   # Phase 1 bucket agents only
--reviewer-provider    / --reviewer-model      # Phase 2 reviewer agents only
--coordinator-command <cmd>       # lower-level expert override -- ALWAYS wins (unchanged, T477)
```

Known providers: `claude` (default), `cursor-agent`. Register additional vendors via
`agent_role_routing.register_role_provider()` — the same extension-point shape
`register_coordinator_fatal_sentinels()` already used for vendor-scoped fatal-output detection.

**Deterministic resolution order** (highest first — never blends two competing resolvers,
g-rl-33 Conflict Pattern Gate), resolved INDEPENDENTLY per role (coordinator / implementer /
reviewer) and independently on the PROVIDER axis vs. the MODEL axis (so `--coordinator-model
opus` alone, with no `--coordinator-provider`, correctly keeps whatever provider host mapping
already chose rather than silently forcing `claude`):

1. **Role-specific CLI override** — `--coordinator-model`, `--reviewer-provider`, etc.
2. **Global CLI override** — `--provider` / `--model`.
3. **Invoking host / parent-model mapping** — see the table below.
4. **Task `preferred_model:`** / session **`--mode fast|standard|cheap`** policy — the SAME
   tier system `g-go`/`g-go-code`'s "Model-Tier Selection" section documents; this resolver
   surfaces the raw tier value rather than re-deriving the tier→model table a second time.
5. **Project config / default** — `coordinator_model:` (T477, unchanged) for the coordinator
   role; new `implementer_model:` / `reviewer_model:` AGENT_CONFIG.md keys for the other two.

**Host-native default mapping table:**

| Detected host | Default provider | Default model (when nothing overrides) |
|---|---|---|
| Claude Code (`CLAUDECODE=1`) | `claude` | T477/T514 resolver — `sonnet` unless `GALD3R_GGO_COORDINATOR_MODEL` / `coordinator_model:` overrides |
| Cursor (`CURSOR_CONVERSATION_ID`/`CURSOR_TRANSCRIPT_PATH`) | `cursor-agent` | `gpt-5.6-terra-medium` (BUG-612's owner-confirmed default — applies regardless of which exact Cursor parent model is declared via `GALD3R_GGO_ORCHESTRATOR_MODEL`, not only GPT-5.6 Sol) |
| Unknown (no positive evidence of a non-Claude host) | `claude` | Same as Claude Code — never invents a Cursor mapping without positive evidence |

Cursor does **not** silently launch the Claude CLI just because Claude is the historically
hardcoded default — a detected Cursor host always resolves to `cursor-agent` unless an
explicit override names a different provider.

**Propagation:** the coordinator's resolved target either feeds the SAME
`GALD3R_GGO_COORDINATOR_MODEL` env var the T477 resolver already reads (when the provider stays
`claude` — preserves `--effort` and every other nuance of the existing command builder, no
second competing command-building path) or, for any other provider, becomes the explicit
launch command itself. Implementer/reviewer resolutions are exported as
`GALD3R_GGO_IMPLEMENTER_PROVIDER`/`_MODEL` and `GALD3R_GGO_REVIEWER_PROVIDER`/`_MODEL`, inherited
by the spawned coordinator subprocess — a swarm coordinator dispatching `g-go-code-swarm` /
`g-go-review-swarm` buckets reads these the same way it already reads `--mode`, and passes them
to the Agent-tool `model:` parameter or worktree-session launch when set. The run's `--json`
summary and status-history rows report the ACTUAL resolved `provider`/`model` per role — never a
silently-ignored requested value.

**Validation (AC6):** an unsupported `--provider`/role-specific provider fails fast — refused
before any claim, worktree allocation, or budget consumption; `--coordinator-command` is
unaffected and always still wins.

**Verification scope note:** live end-to-end verification against a real Cursor GPT-5.6 Sol
session's `agent` CLI was not possible from the implementing sandbox (no network access to spawn
or authenticate a live Cursor session). The resolution logic, host-mapping table, and CLI
surface are deterministic and unit/integration-tested (`tests/coordination
/test_coordination_autopilot_agent_role_routing.py`,
`tests/cli/test_orchestration_autopilot_role_routing.py`); the `agent` CLI's `--model`/`-p`/
`--force`/`--output-format` flags were confirmed via live docs fetch (cursor.com/docs/cli/headless)
rather than assumed.
