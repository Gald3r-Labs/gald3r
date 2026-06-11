---
gald3r_rel_version: "2.0.1"
schema_version: "generic-v1"
---
# AGENT_CONFIG.md — gald3r Agent Configuration

Configuration file for gald3r agent harness behavior. Read by `g-go-code`, `g-go-review`, and the `g-skl-context-builder` at session start.

---

## Version Check

```
disable_version_check: false
version_feed_url: https://api.github.com/repos/gald3r/gald3r/releases/latest
```

Set `disable_version_check: true` for air-gapped environments.

---

## Auto-Triage L0 (T1385)

```
auto_triage_risk_threshold: 2.0
```

Reactive Medic L0 (`g-skl-auto-triage`) only attempts a bounded auto-fix when a non-code bug's
computed `risk_score` is `<= auto_triage_risk_threshold`. Phase 1 default is `2.0` (cautious — only
the lowest-risk schema comments, manifest clarifications, and metadata annotations are auto-fixed).
Anything above the threshold is logged as `needs_attention` / `blocked_by_risk`. Raising this value
expands courage (Phase 2); keep it low for unattended runs.

---

## Active Preset

```
active_preset: preset_implementation
```

Override in task frontmatter via `agent_config_preset:` field.

---

## Harness Tuning

Performance-affecting harness knobs documented and configured here. Research basis: Stanford/Chinha University findings showing a **6× performance gap** between well-tuned and poorly-tuned agent harnesses using the same model, driven by: context window management, tool call ordering, retry logic, temperature per task type, and memory injection timing.

### Knobs Reference

#### Context Window Budget (`context_budget_tokens`)
Maximum tokens allocated for context assembly before the task spec is injected. Larger budgets include more subsystem specs and memory; smaller budgets run faster on simple tasks.

| Task Type | Recommended Budget | Rationale |
|-----------|-------------------|-----------|
| feature / implementation | 800 | Full: task + constraints + subsystems + memory |
| bug_fix | 600 | Focused: task + constraints + error context |
| review / verification | 400 | Lean: task summary + constraints only |
| documentation | 300 | Minimal: task only |
| research / planning | 1200 | Broad: full context + vault memory |

#### Tool Call Ordering Strategy (`tool_call_order`)
Order in which tools are called during task execution. `reads_first` (default) batches all reads before writes; `writes_as_needed` interleaves. `reads_first` is safer for parallel bucket agents.

Options: `reads_first` | `writes_as_needed` | `explicit` (task spec defines order)

#### Retry Count and Backoff (`max_retries`, `retry_backoff_seconds`)
Number of times to retry a failed tool call before surfacing an error. Exponential backoff base is `retry_backoff_seconds`.

| Scenario | Retries | Backoff |
|----------|---------|---------|
| MCP tool call fails | 3 | 2s |
| File write conflict | 2 | 1s |
| Network request | 2 | 3s |

#### Temperature Settings (`temperature_by_task_type`)
LLM temperature per task type. Lower = more deterministic; higher = more creative.

| Task Type | Temperature | Rationale |
|-----------|-------------|-----------|
| bug_fix | 0.1 | Precise, minimal hallucination risk |
| implementation | 0.2 | Reliable code generation |
| review | 0.3 | Consistent quality judgment |
| planning | 0.5 | Exploratory option generation |
| research / documentation | 0.6 | Natural language variety |

#### Memory Injection Timing (`memory_injection_timing`)
When session memory is injected into the context.

Options:
- `session_start` (default) — inject memory once at the beginning of the session
- `per_task` — re-read and inject memory before each task claim
- `disabled` — no memory injection (fastest, use for CI/automated runs)

---

## Presets

### `preset_implementation` (default)
For `g-go-code` coding tasks. Optimized for reliable, low-variance code production.

```yaml
context_budget_tokens: 800
tool_call_order: reads_first
max_retries: 3
retry_backoff_seconds: 2
temperature: 0.2
memory_injection_timing: session_start
include_constraints: true
include_subsystems: true
include_recent_memory: true
include_active_task: true
```

### `preset_review`
For `g-go-review` verification tasks. Lean context — reviewer should judge independently.

```yaml
context_budget_tokens: 400
tool_call_order: reads_first
max_retries: 2
retry_backoff_seconds: 1
temperature: 0.3
memory_injection_timing: session_start
include_constraints: true
include_subsystems: false
include_recent_memory: false
include_active_task: true
```

### `preset_planning`
For `g-plan`, `g-propose`, and strategic planning sessions. Broad context, higher creativity.

```yaml
context_budget_tokens: 1200
tool_call_order: reads_first
max_retries: 2
retry_backoff_seconds: 2
temperature: 0.5
memory_injection_timing: per_task
include_constraints: true
include_subsystems: true
include_recent_memory: true
include_active_task: false
```

### `preset_research`
For `g-recon-*`, `g-res-*`, and vault ingestion tasks. Maximum context, most natural language variety.

```yaml
context_budget_tokens: 1200
tool_call_order: writes_as_needed
max_retries: 3
retry_backoff_seconds: 3
temperature: 0.6
memory_injection_timing: session_start
include_constraints: false
include_subsystems: false
include_recent_memory: true
include_active_task: false
```

---

## Per-Task Preset Override

Add `agent_config_preset:` to task frontmatter to override the active preset for a specific task:

```yaml
---
id: 846
title: 'Dynamic Instruction Assembly'
agent_config_preset: preset_planning
---
```

Agents read this field before selecting the active preset. Override takes priority over `AGENT_CONFIG.md active_preset`.

---

## g-go-code Integration

`g-go-code` reads this file at Step 0 (before task selection):
1. Read `active_preset` (or task-level `agent_config_preset:` if claiming a specific task)
2. Load the corresponding preset block above
3. Pass `context_budget_tokens` to `g-skl-context-builder BUILD`
4. Apply `temperature`, `max_retries`, and `memory_injection_timing` to the session

---

## g-go Default Scope (`g_go_default_scope`)

Controls the scope a bare `@g-go` / `@g-go --swarm` (no `--local` / `--workspace` flag, no
explicit task IDs) uses when selecting its work queue. Read by the `g-go` / `g-go-swarm`
coordinator at Step 1a of the Auto-Plan scope filter.

```yaml
# g_go_default_scope: local_only   # uncomment + set to workspace_all on controller repos
```

| Value | Bare `@g-go` behavior |
|-------|-----------------------|
| `local_only` (default — also the behavior when the key is **absent**) | Scope to **this repo's** tasks only. Items whose `workspace_repos` names other members are deferred. Safe default for member / leaf repos. |
| `workspace_all` | Scope to **all manifest members** (identical to `@g-go --workspace`). |

**Controller pattern**: Controller repos (e.g. `<gald3r_source>`) have no code of their own — a
bare `@g-go` scoped local-only finds nothing to run. Set `g_go_default_scope: workspace_all`
in those repos so bare `@g-go` scans the whole workspace by default. Flags still override
config every time:

| Flag (highest priority) | Effect, regardless of `g_go_default_scope` |
|-------------------------|--------------------------------------------|
| `--local` | Force local-only (controller-own tasks only) |
| `--workspace <id>` / `--workspace <id1,id2>` | Narrow to the named member(s) |
| `--workspace` (no value) | All members |

See the Step 1a priority table in `g-go.md` / `g-go-swarm.md` for the full resolution order
(`--local` > `--workspace <id>` > `--workspace` > `g_go_default_scope` > local-only default).

---

## Context Reduction Strategy (T872)

Context window efficiency is critical for g-go --swarm performance. Target: 98% reduction for tool output (315KB → ~5KB for typical file reads).

### `context_reduction_mode` Flags

```yaml
context_reduction_mode:
  think_in_code: true           # g-rl-37 — prefer one script over multiple sequential reads
  graphify_b0_enabled: false    # T874b — opt-in: run g-skl-graphify code-graph query at g-go-code Step b0.2 before implementation
```

| Flag | Default | What it does | Where read |
|------|---------|--------------|------------|
| `think_in_code` | `true` | Reminds agents to collapse 3+ sequential file reads into a single script per g-rl-37 | g-go-code Step b0/c1 context assembly |
| `graphify_b0_enabled` | `false` | When `true`, the coordinator runs a single gitNexus/Graphify/tree-sitter query at Step b0.2 and passes the ≤200-token result block to implementer subagents. When `false`, Step b0.1 (gitnexus_impact) alone gates context. | g-go-code Step b0.2; g-go --swarm coordinator briefing |

`graphify_b0_enabled` ships **off by default** so the b0 path is a no-op for projects without `gitnexus` MCP, `graphify-cli`, or a `.graphify/` index. Operators enable it once a backend is wired and indexed (see g-skl-graphify SETUP).

### "Think in Code" Pattern

**Rule**: Prefer writing a single script over making multiple sequential tool calls.

Instead of:
1. `read_file("config.py")` → scan output
2. `read_file("config.py")` → look for key
3. `grep("OPENAI", "config.py")` → count matches

Write:
```python
# single script that does all three in one execute call
import re
content = open("config.py").read()
keys = [l for l in content.splitlines() if "OPENAI" in l]
print(f"lines_found={len(keys)}\nfirst={keys[0] if keys else 'none'}")
```

**Guidance for agents**:
- 1 script = up to 10 tool calls collapsed to 1 context round-trip
- 65-75% output token reduction for file-read-heavy tasks
- Prefer scripts for: multi-file reads, grep+filter, bulk status checks, format conversions

### context-mode MCP (External Integration)

Context-mode MCP provides:
- 315KB → ~5KB tool output compression via content-addressed truncation
- FTS5/BM25 SQLite session continuity (context survives compaction)
- 14-platform support

**Docker service**: Add to `docker-compose.yml` when ready to activate.

**Setup** (npm-based MCP):
```json
{
  "mcpServers": {
    "context-mode": {
      "command": "npx",
      "args": ["-y", "context-mode"],
      "env": {}
    }
  }
}
```

Add this to `.cursor/mcp.json` under `mcpServers` to enable context compression on Cursor.

### Measured Baselines

| Tool Output Type | Raw Size | Compressed (est.) | Reduction |
|-----------------|----------|-------------------|-----------|
| File read (100KB source) | ~100KB | ~2-5KB | ~97% |
| Directory listing (200 files) | ~12KB | ~0.3KB | ~97% |
| Grep results (50 matches) | ~8KB | ~0.5KB | ~94% |
| Git log (100 commits) | ~15KB | ~0.8KB | ~95% |

Source: context-mode upstream benchmarks (/context-mode README, May 2026).

---

## Model Assignment

Configure which model tier each agent role should use. Set any role to `default` to use the active CLI's configured model for that role.

> Run `@g-status` to see the current model assignment in session context.

| Role | Preferred Model | Fallback | Cost Tier | Notes |
|------|----------------|----------|-----------|-------|
| `code_generation` | claude-opus | claude-sonnet | premium | Senior dev tasks — correctness > cost |
| `code_review` | claude-sonnet | claude-haiku | standard | Review + security analysis |
| `research` | gemini-flash | claude-haiku | cheap | Trend scanning, data gathering |
| `health_check` | claude-haiku | default | cheap | Cron monitoring, quick triage |
| `planning` | claude-opus | claude-sonnet | premium | Architecture and roadmap decisions |

**To use the CLI's default model for all roles**, set every row's preferred_model to `default`.

**Integration with g-go-code / g-go-review**: When a model is specified here (not `default`), the pipeline surfaces a suggestion: _"This task type maps to `code_generation` — consider passing `--model claude-opus` to your CLI."_ Agents do not override the user's model automatically; this is advisory only.

---

## Provider Fallback Chain (T1087)

Define a cost-ordered list of AI providers per agent role. The agent tries providers in order, falling back when the primary provider hits rate limits, budget exhaustion, or is unavailable.

**Tier values**: `paid-high` > `paid-low` > `free` > `offline`

```yaml
provider_fallback_chain:
  orchestrator:
    - provider: anthropic
      model: claude-opus-4
      tier: paid-high
    - provider: openrouter
      model: google/gemini-pro
      tier: paid-low
    - provider: nvidia-nim
      model: nimitron
      tier: free
  code_generation:
    - provider: anthropic
      model: claude-sonnet-4-5
      tier: paid-low
    - provider: openrouter
      model: deepseek/deepseek-chat
      tier: paid-low
    - provider: nvidia-nim
      model: glm4
      tier: free
  reviewer:
    - provider: anthropic
      model: claude-sonnet-4-5
      tier: paid-low
    - provider: openrouter
      model: google/gemini-flash
      tier: paid-low
    - provider: ollama
      model: qwen2.5
      tier: offline
  qa_engineer:
    - provider: anthropic
      model: claude-haiku-4
      tier: paid-low
    - provider: nvidia-nim
      model: llama3
      tier: free
    - provider: ollama
      model: llama3.2
      tier: offline
  task_manager:
    - provider: anthropic
      model: claude-haiku-4
      tier: paid-low
    - provider: nvidia-nim
      model: llama3
      tier: free
```

**Free/offline providers for zero-cost fallback**:
- `nvidia-nim`: Nvidia's free inference tier — various Llama, Nemo, and GLM4 models
- `openrouter`: Many free-tier models (Google Gemini Flash, some DeepSeek variants)
- `ollama`: Fully offline — requires local installation; model quality depends on hardware

**Cross-reference**: See `## Model Assignment` above for per-role preferred model. `provider_fallback_chain` extends model_assignment with explicit fallback ordering for budget-aware routing.

---

## Skill Capture Hook (T1174)

Opt-in feedback loop that lets `g-hk-agent-complete` stage SKILL.md candidate stubs after every completed session. Filled stubs are surfaced to `IDEA_BOARD.md` by `@g-idea-farm` (Pass 6).

```yaml
skill_capture_hook: false   # set to `true` to enable
```

| Flag | Default | Effect |
|------|---------|--------|
| `skill_capture_hook` | `false` | When `true` and the session ends with `status: completed`, `g-hk-agent-complete` writes a SKILL-candidate stub to `.gald3r/reports/skill_candidates/YYYYMMDD_HHMMSS_session{shortcid}.md`. Filled stubs are promoted to `IDEA_BOARD.md` by `@g-idea-farm`. |

**Flow**:
1. Agent ends session → hook checks this flag → if true, stages a pending stub
2. Next agent session (or human) edits the stub: fills `name`, `when_to_use`, `how_it_works`, `example`, sets `status: filled`
3. `@g-idea-farm` Pass 6 scans the folder; filled stubs become IDEA_BOARD entries with `Category: skill_candidate`
4. Promoted stubs move to `.gald3r/reports/skill_candidates/promoted/`; discarded stubs move to `.../discarded/`
5. From IDEA_BOARD, the user can promote to a real task via `g-skl-ideas` PROMOTE (then scaffold the skill via `@g-create-skill`)

**Disabled by default** so projects opt in only when they want the feedback loop. No stubs are staged while the flag is false or absent.

---

## Notes

- This file is in `.gald3r/config/` alongside `HEARTBEAT.md`, `SPRINT.md`, etc.
- Not committed by default (`.gald3r/` is gitignored in the source repo)
- Safe to customize per-project; upgrades will not overwrite this file
- The `disable_version_check` flag here is the authoritative override for the g-rl-25 Step 1.5 version check
