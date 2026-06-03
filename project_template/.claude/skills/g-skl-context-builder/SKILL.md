---
name: g-skl-context-builder
description: Dynamic context assembly from live .gald3r/ state. Builds a token-budgeted agent context block including active tasks, constraints, subsystem specs, and session memory. Use at session start or when handing off between agents in g-go pipelines.
token_budget: medium
subsystem_memberships: [MEMORY_AND_KNOWLEDGE, TASK_MANAGEMENT]
---

# g-skl-context-builder — Dynamic Instruction Assembly

Generates a compact, token-budgeted context block from live `.gald3r/` state rather than relying solely on static SKILL.md injection. The context block is assembled fresh each run from the actual current state of the project.

**When to use this skill:**
- At session start before `g-go-code` or `g-go-review` begins task selection
- When resuming a multi-session task (stale static context is replaced with live state)
- When handing off between agents in a swarm — inject current context into each bucket
- Any time you need to know: "what task am I on, what constraints apply, what subsystems are relevant?"

---

## Operations

### BUILD

Assembles a live context block. Called by `g-go` Step 0 before task selection.

**Inputs (all optional):**
- `task_id` — if provided, builds context specifically for that task
- `token_budget` — max tokens for the context block (default: 800)
- `include_memory` — whether to include last session summary (default: true)

**Assembly Order (priority order for truncation):**

1. **Active Task** (~200 tokens, highest priority)
   - Read `.gald3r/TASKS.md` → find task matching `task_id` or first `[🔄]` / `[📋]` in-progress task
   - Read `.gald3r/tasks/task{id}_*.md` → extract: title, objective, acceptance criteria (abbreviated), subsystems
   - Format: `🎯 Task {id}: {title}\nObjective: {first 100 chars}\nACs: {count} items\nSubsystems: {list}`

2. **Active Constraints** (~150 tokens)
   - Read `.gald3r/CONSTRAINTS.md` → extract active constraint IDs + titles only (one line each)
   - Skip expired/archived constraints
   - Format: `🛡️ Constraints: C-001 (title) | C-002 (title) | ...`

3. **Relevant Subsystem Specs** (~250 tokens)
   - Take `subsystems:` list from the active task
   - For each subsystem, read `.gald3r/subsystems/{name}.md` frontmatter only (skip body)
   - Extract: name, status, dependencies, locations (abbreviated)
   - If no task specified: skip this section

4. **Recent Session Memory** (~200 tokens, lowest priority — truncated first)
   - Try `memory_context` MCP tool (if Docker backend available)
   - Fallback: read last 10 bullet points from `.gald3r/learned-facts.md`
   - Format: `🧠 Recent: {bullet 1} | {bullet 2} | ...`

**Token Budget Enforcement:**
- Each section adds tokens; once budget is reached, drop lower-priority sections
- Never truncate within a constraint (drop the whole constraint entry rather than truncate mid-line)
- Report token estimate in output header

**Output Format:**
```
═══ DYNAMIC CONTEXT (est. {N} tokens) ═══
🎯 Task {id}: {title}
   Objective: {abbreviated}
   ACs: {N} items | Status: {status}
   Subsystems: {comma-separated list}

🛡️ Constraints: {C-IDs with titles, pipe-separated}

📐 Subsystems:
   {name}: {status} | deps: {list} | at: {locations abbreviated}

🧠 Recent: {last session highlights}
═══════════════════════════════════════
```

**Graceful Degradation:**
- `.gald3r/` missing or empty → output: `ℹ️ No .gald3r/ state found — proceeding with static context only`
- No active task → skip task and subsystem sections; include constraints + memory only
- MCP backend unavailable → use file-first fallback for memory

---

### INJECT

Wraps the BUILD output in a format compatible with `memory_context` MCP tool response shape.

```json
{
  "context": "...(assembled context block)...",
  "token_estimate": 742,
  "task_id": "846",
  "generated_at": "2026-05-09T09:25:00Z",
  "fallback_used": false
}
```

---

### STATUS

Reports what live `.gald3r/` state is available for context building:
- Task file count, constraint count, subsystem spec count
- Memory source (MCP or file-only)
- Last successful BUILD timestamp (if tracked in `.gald3r/logs/`)

---

## Integration with g-go-code

`g-go-code` Step 0 calls:
```
@g-context-builder BUILD task_id={claimed_task_id} token_budget=800
```

The output is prepended to the task-implementation prompt before the actual task spec is injected. This ensures the agent starts with current project state, not stale session context.

---

## MCP Compatibility

The INJECT output uses the same schema as `memory_context` MCP tool responses:
- `context` (string) — the assembled block
- `token_estimate` (int) — approximate token count
- `task_id` (string, optional) — task anchor

When the MCP backend is available, `memory_context` handles the assembly and this skill provides the orchestration layer. When offline, this skill produces equivalent output from local files.

---

## Override via Task Frontmatter

Tasks can override the token budget via frontmatter:
```yaml
agent_context_budget: 1200
```
This allows complex tasks (large subsystems, many constraints) to request more context.
