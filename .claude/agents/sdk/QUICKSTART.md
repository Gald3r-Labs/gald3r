# Fallback System Quick Start Guide

Get up and running with the fallback and error handling system in 5 minutes.

---

## Installation

### 1. Install Dependencies

```bash
cd /mnt/c/git/gald3r
pip install -r .claude/agents/sdk/requirements.txt
```

### 2. Verify Installation

```bash
python .claude/agents/sdk/health.py
```

You should see a health check report. Don't worry if SDK shows as "not installed" - that's expected and the fallback system will handle it!

---

## Basic Usage

### Run a Health Check

```python
from health import HealthMonitor

monitor = HealthMonitor()
report = monitor.run_checks()
monitor.print_report(report)
```

**Output**:
```
============================================================
AGENT SDK HEALTH CHECK REPORT
============================================================
Timestamp: 2025-11-01T12:00:00Z
Overall Status: WARNING

Individual Checks:
------------------------------------------------------------
✗ sdk_availability: Anthropic SDK not installed
✗ api_key: ANTHROPIC_API_KEY not set
✓ agent_files: 15 agents available
✓ context_storage: Context storage ready
✓ system_resources: Resources OK
⚠ network_connectivity: Network connection issues

Summary:
------------------------------------------------------------
Total Checks: 6
Healthy: 3
Warning: 1
Critical: 2

Ready for SDK: False
Ready for Prompt-based: True
============================================================
```

This tells you:
- SDK not ready (expected if not installed)
- Prompt-based agents available and working
- System is functional

### Invoke an Agent with Automatic Fallback

```python
from fallback import HybridAgentInvoker

# Initialize invoker
invoker = HybridAgentInvoker()

# Create context
context = {
    "workflow_id": "my-first-workflow",
    "task": "Build user authentication system",
    "requirements": ["JWT tokens", "Password hashing"]
}

# Invoke agent - will automatically use prompt-based if SDK unavailable
result = invoker.invoke(
    agent_name="backend-developer",
    context=context,
    task="Implement login endpoint with JWT authentication"
)

print(result)
```

**What happens**:
1. Tries SDK agent first
2. SDK not installed → fallback to prompt-based
3. Returns result (either way works!)

---

## Common Scenarios

### Scenario 1: SDK Not Installed (Most Common)

**What you'll see**:
```
[FALLBACK] SDK agent failed: No module named 'anthropic'
[FALLBACK] Switching to prompt-based agent...
```

**What happens**: Automatic fallback to `.claude/agents/backend-developer.md`

**Action needed**: None! System works with prompt-based agents.

### Scenario 2: API Key Not Set

**What you'll see**:
```
[FALLBACK] SDK agent failed: api_key is required
[FALLBACK] Switching to prompt-based agent...
```

**What happens**: Immediate fallback (no retry)

**Action needed**: If you want SDK agents, set `ANTHROPIC_API_KEY`:
```bash
export ANTHROPIC_API_KEY=sk-your-key-here
```

### Scenario 3: Network Issues

**What you'll see**:
```
[FALLBACK] SDK agent failed: Network timeout
[FALLBACK] Retry 1/2: network_failure
[FALLBACK] Retry 2/2: network_failure
[FALLBACK] Max retries exceeded, falling back...
```

**What happens**: Retries 2 times, then falls back

**Action needed**: Check internet connection if this happens repeatedly

---

## Running Examples

### Test All Fallback Scenarios

```bash
cd .claude/agents/sdk/examples
python fallback_scenarios.py
```

**Output**:
```
======================================================================
SCENARIO 1: SDK Not Installed
======================================================================
✗ Failure detected: sdk_not_installed
→ Should fallback? True
→ Switching to prompt-based agent...
✓ Fallback successful!

Prompt-based agent invocation:
[FALLBACK MODE - Using prompt-based agent]
Agent: backend-developer
Context file: .claude/agent_context/json/scenario1.json
...
```

### Run Specific Scenario

```bash
# Scenario 1: SDK not installed
python fallback_scenarios.py 1

# Scenario 3: Timeout with retry
python fallback_scenarios.py 3

# Scenario 5: Hybrid workflow
python fallback_scenarios.py 5
```

---

## Checking Statistics

### View Fallback Statistics

```python
from fallback import FallbackHandler

handler = FallbackHandler()

# After some agent invocations...
stats = handler.get_statistics()

print(f"Total invocations: {stats['total_invocations']}")
print(f"SDK success rate: {stats['sdk_success_rate']:.1%}")
print(f"Fallback rate: {stats['fallback_rate']:.1%}")
print(f"\nTop failures:")
for reason, count in stats['failure_reasons'].items():
    print(f"  {reason}: {count}")
```

**Output**:
```
Total invocations: 50
SDK success rate: 70.0%
Fallback rate: 30.0%

Top failures:
  network_failure: 10
  agent_timeout: 5
```

---

## Logs and Monitoring

### Log Files Location

```
.claude/agents/sdk/logs/
├── fallback.log          # Detailed fallback events
├── metrics.log           # Structured metrics (JSONL)
├── health.log            # Health check results
├── latest_health.json    # Most recent health report
└── health_history.jsonl  # Historical health data
```

### View Recent Fallbacks

```bash
tail -20 .claude/agents/sdk/logs/fallback.log
```

### View Health History

```bash
tail -5 .claude/agents/sdk/logs/health_history.jsonl | jq .
```

---

## Testing

### Run Test Suite

```bash
cd .claude/agents/sdk
pytest tests/test_fallback.py -v
```

**Output**:
```
tests/test_fallback.py::TestFailureDetection::test_sdk_not_installed PASSED
tests/test_fallback.py::TestFailureDetection::test_api_key_missing PASSED
tests/test_fallback.py::TestFallbackDecisions::test_immediate_fallback_sdk_not_installed PASSED
...
========================= 15 passed in 2.5s =========================
```

### Run with Coverage

```bash
pytest tests/test_fallback.py --cov=fallback --cov=health --cov-report=html
```

View coverage report: `open htmlcov/index.html`

---

## Troubleshooting

### "No agents found"

**Problem**: Agent files not detected

**Solution**:
```bash
# Check agent files exist
ls .claude/agents/*.md
ls .claude/agents/prompt-based/*.md

# Run health check
python .claude/agents/sdk/health.py
```

### "Cannot write to context directory"

**Problem**: Permission issues

**Solution**:
```bash
# Check permissions
ls -la .claude/agent_context/

# Create directory if missing
mkdir -p .claude/agent_context/json
chmod 755 .claude/agent_context/json
```

### "High fallback rate"

**Problem**: >30% of invocations falling back

**Solution**:
```python
# Check statistics
from fallback import FallbackHandler
handler = FallbackHandler()
stats = handler.get_statistics()
print(stats['failure_reasons'])

# Most common issue? Fix it:
# - sdk_not_installed → Install SDK
# - api_key_missing → Set API key
# - network_failure → Check internet
```

---

## Next Steps

1. **Read Full Documentation**: [FALLBACK_SYSTEM.md](FALLBACK_SYSTEM.md)
2. **Run Examples**: `python examples/fallback_scenarios.py`
3. **Set Up Monitoring**: Schedule health checks
4. **Configure Alerts**: Alert on repeated failures

---

## FAQ

### Q: Do I need to install the Anthropic SDK?

**A**: No! The system works perfectly with prompt-based agents. SDK is optional and provides additional features.

### Q: What happens if both SDK and prompt-based agents fail?

**A**: Prompt-based agents are highly reliable and should always work. If they fail, check:
- Agent files exist (`.claude/agents/*.md`)
- Context directory is writable
- System resources available

### Q: How do I prefer prompt-based agents (skip SDK)?

**A**:
```python
invoker = HybridAgentInvoker()
result = invoker.invoke(
    agent_name="backend-developer",
    context=context,
    prefer_sdk=False  # Always use prompt-based
)
```

### Q: Can I customize retry logic?

**A**: Yes!
```python
handler = FallbackHandler(
    enable_retry=True,
    max_retries=5,  # Retry 5 times
)
```

### Q: How do I disable fallback (fail fast)?

**A**:
```python
handler = FallbackHandler(
    enable_retry=False  # No retries, immediate failure
)
# Then don't call fallback methods - let exceptions propagate
```

---

## Summary

The fallback system ensures your agent workflows **always work**:

- ✅ SDK unavailable → prompt-based agents
- ✅ Network issues → retry then fallback
- ✅ Agent crashes → retry then fallback
- ✅ Context conversion fails → text-based communication
- ✅ Comprehensive logging and monitoring
- ✅ Zero configuration required (works out of the box)

**Start simple**: Just use `HybridAgentInvoker.invoke()` and the system handles everything!

---

**Questions?** See [FALLBACK_SYSTEM.md](FALLBACK_SYSTEM.md) for complete documentation.
