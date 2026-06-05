---
subsystem_memberships: [AGENT_ORCHESTRATION]
---
# Think in Code — Context Reduction Pattern (g-rl-37)

**Source**: OpenAI context-mode MCP "Think in Code" pattern. Validated on gald3r g-go workflows.

## Rule

When a task requires **3 or more sequential reads, greps, or status checks** on the same or related files, **write a single script** instead of making multiple tool calls.

## Threshold

| Number of planned tool calls | Action |
|------------------------------|--------|
| 1–2 | Normal tool calls are fine |
| 3–9 | Prefer a single script |
| 10+ | **MUST** use a script |

## Why

- 1 script = up to 10 tool calls collapsed to 1 context round-trip
- 65–75% output token reduction for file-read-heavy tasks
- Reduces context window pressure, enabling more tasks per session

## Examples

### ❌ Multiple tool calls (wasteful)
```
read_file("config.py")
grep("OPENAI_KEY", "config.py")
read_file("config.py")  # again, looking for something else
```

### ✅ Single script (preferred)
```python
# Run with shell or Python tool in one call
import re, pathlib
src = pathlib.Path("config.py").read_text()
keys = {m.group(1) for m in re.finditer(r"(\w+_KEY)\s*=", src)}
print("keys:", sorted(keys))
print("lines:", src.count("\n"))
```

## Exemptions

Do NOT collapse to a script when:
- The second tool call depends on runtime output of the first (dynamic path resolution)
- You need an IDE diff/edit tool (not a script)
- The task is a single-file edit (script overhead not worth it)

## Integration with g-go-code

`g-go-code` Step b0 (Impact Scan) and Step c1 (context assembly) check `AGENT_CONFIG.md context_reduction_mode`. When `think_in_code: true`, agents are reminded of this rule before tool planning.
